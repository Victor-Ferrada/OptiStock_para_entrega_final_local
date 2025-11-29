import json
from urllib.parse import urlencode


from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.db import transaction
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from django.contrib import messages
from django.db.models import Q

from .forms import MovimientoForm, DetalleForm
from .models import Movimiento, Detalle
from inventario.models import Producto
from logger.models import SystemMessage
from datetime import datetime



def lista_ventas(request):
    # Obtener mes y año actuales por defecto
    today = datetime.now()
    mes = request.GET.get('mes', str(today.month))
    año = int(request.GET.get('año', today.year))
    
    # Filtrar ventas por mes y año
    if mes == 'todos':
        # Mostrar todos los meses del año
        ventas = Movimiento.objects.filter(
            tipo='VENTA',
            fecha__year=año
        ).order_by('-fecha')
    else:
        # Mostrar solo el mes especificado
        mes = int(mes)
        ventas = Movimiento.objects.filter(
            tipo='VENTA',
            fecha__month=mes,
            fecha__year=año
        ).order_by('-fecha')
    
    mostrar_mensaje = request.session.pop('mostrar_mensaje', False)
    
    # Generar opciones de meses y años
    meses = [
        ('todos', 'Todos los meses'),
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    
    # Obtener años disponibles en la base de datos
    años_disponibles = set()
    for venta in Movimiento.objects.filter(tipo='VENTA').values_list('fecha__year', flat=True).distinct():
        años_disponibles.add(venta)
    años_disponibles = sorted(list(años_disponibles), reverse=True)
    # Si no hay años, agregar el año actual
    if not años_disponibles:
        años_disponibles = [today.year]
    
    return render(request, 'ventas/lista_ventas.html', {
        'ventas': ventas,
        'mostrar_mensaje': mostrar_mensaje,
        'mes_seleccionado': mes,
        'año_seleccionado': año,
        'meses': meses,
        'años_disponibles': años_disponibles
    })

def detalle_venta(request, id_mov):
    venta = get_object_or_404(Movimiento, pk=id_mov, tipo='VENTA')
    detalles = venta.detalles.all().select_related('id_prod')
    SystemMessage.objects.create(
        message=f"Usuario {request.user} consultó el detalle de la venta #{id_mov}",
        level='info',
        app='ventas',
        user=request.user
    )
    return render(request, 'ventas/detalle_venta.html', {
        'venta': venta,
        'detalles': detalles
    })

def registrar_venta(request):
    # Obtener filtro de categoría desde la URL (?categoria=...)
    categoria = request.GET.get('categoria', '')

    # Filtrar productos
    if categoria:
        productos_queryset = Producto.objects.filter(categoria=categoria).order_by('nombre')
    else:
        productos_queryset = Producto.objects.all().order_by('nombre')

    # Si viene ?ok=1 en la URL, mostramos el mensaje de éxito
    mostrar_mensaje = request.GET.get('ok') == '1'
    error = None

    if request.method == "POST":
        try:
            carrito = json.loads(request.POST.get('carrito', '[]'))

            if not carrito:
                error = 'El carrito está vacío'
                raise ValidationError(error)

            with transaction.atomic():
                movimiento = Movimiento()
                movimiento.tipo = 'VENTA'
                movimiento.rut_usu = request.user
                total = 0
                detalles = []

                for item in carrito:
                    try:
                        producto = Producto.objects.get(id=item['id'])
                        cantidad = item['cantidad']
                        precio_unitario = item['precio_uni']

                        if producto.stock < cantidad:
                            error_msg = (
                                f"Stock insuficiente para {producto.nombre}. "
                                f"Stock disponible: {producto.stock}, requerido: {cantidad}."
                            )
                            SystemMessage.objects.create(
                                message=error_msg,
                                level='error',
                                app='ventas',
                                user=request.user
                            )
                            raise ValidationError(error_msg)

                        subtotal = precio_unitario * cantidad
                        total += subtotal

                        producto.stock -= cantidad
                        producto.save()

                        SystemMessage.objects.create(
                            message=f"Stock actualizado para {producto.nombre}. Nuevo stock: {producto.stock}",
                            level='info',
                            app='ventas',
                            user=request.user
                        )

                        detalle = Detalle(
                            id_mov=movimiento,
                            id_prod=producto,
                            cantidad=cantidad,
                            precio_uni=precio_unitario
                        )
                        detalles.append(detalle)

                    except Producto.DoesNotExist:
                        raise ValidationError(f"Producto con ID {item['id']} no encontrado")

                movimiento.total = total
                movimiento.save()
                Detalle.objects.bulk_create(detalles)

                SystemMessage.objects.create(
                    message=f"Venta registrada exitosamente. Total: ${total:.2f}",
                    level='info',
                    app='ventas',
                    user=request.user
                )

            # 🔴 PRG: redirigir después de un POST exitoso, SIN usar reverse
            params = {'ok': '1'}
            if categoria:
                params['categoria'] = categoria

            url = request.path  # /ventas/registrar/
            url_con_params = f"{url}?{urlencode(params)}"

            return redirect(url_con_params)

        except (json.JSONDecodeError, ValidationError) as e:
            # Si hay error, NO redirigimos, solo mostramos el error en el mismo render
            error = str(e) if isinstance(e, ValidationError) else 'Error en los datos del carrito'

    return render(request, 'ventas/registrar_venta.html', {
        'mostrar_mensaje': mostrar_mensaje,
        'categoria_seleccionada': categoria,
        'productos_filtrados': productos_queryset,
        'error': error
    })
