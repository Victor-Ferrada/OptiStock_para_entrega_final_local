from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.forms import modelformset_factory
from django.core.exceptions import ValidationError
from .forms import CompraForm, DetalleCompraForm
from .models import Compra, DetalleCompra
from inventario.models import Producto
from logger.models import SystemMessage
from datetime import datetime
import json
from urllib.parse import urlencode

def registrar_compra(request):
    categoria = request.GET.get('categoria', '')

    # Filtrar productos
    if categoria:
        productos_queryset = Producto.objects.filter(categoria=categoria).order_by('nombre')
    else:
        productos_queryset = Producto.objects.all().order_by('nombre')

    mostrar_mensaje = request.GET.get('ok') == '1'
    error = None
    compra_form = CompraForm(request.POST or None)

    if request.method == "POST":
        try:
            carrito = json.loads(request.POST.get('carrito', '[]'))

            if not carrito:
                error = 'El carrito está vacío'
                raise ValidationError(error)

            if not compra_form.is_valid():
                error = 'Por favor completa los datos del proveedor'
                raise ValidationError(error)

            with transaction.atomic():
                compra = compra_form.save(commit=False)
                compra.rut_usu = request.user
                total = 0
                detalles = []

                for item in carrito:
                    try:
                        producto = Producto.objects.get(id=item['id'])
                        cantidad = item['cantidad']
                        precio_unitario = item['precio_uni']

                        subtotal = precio_unitario * cantidad
                        total += subtotal

                        # Actualizar stock y precio del producto
                        producto.stock += cantidad
                        producto.precio = precio_unitario
                        producto.save()

                        SystemMessage.objects.create(
                            message=f"Stock actualizado para {producto.nombre}. Nuevo stock: {producto.stock}",
                            level='info',
                            app='compras',
                            user=request.user
                        )

                        detalle = DetalleCompra(
                            id_compra=compra,
                            id_prod=producto,
                            cantidad=cantidad,
                            precio_uni=precio_unitario
                        )
                        detalles.append(detalle)

                    except Producto.DoesNotExist:
                        raise ValidationError(f"Producto con ID {item['id']} no encontrado")

                compra.total = total
                compra.save()
                DetalleCompra.objects.bulk_create(detalles)

                SystemMessage.objects.create(
                    message=f"Compra registrado exitosamente. Total: ${total:.2f}",
                    level='info',
                    app='compras',
                    user=request.user
                )

            # PRG: redirigir después de un POST exitoso
            params = {'ok': '1'}
            if categoria:
                params['categoria'] = categoria

            url = request.path
            url_con_params = f"{url}?{urlencode(params)}"
            return redirect(url_con_params)

        except (json.JSONDecodeError, ValidationError) as e:
            error = str(e) if isinstance(e, ValidationError) else 'Error en los datos del carrito'

    return render(request, 'compras/registrar_compra.html', {
        'compra_form': compra_form,
        'mostrar_mensaje': mostrar_mensaje,
        'categoria_seleccionada': categoria,
        'productos_filtrados': productos_queryset,
        'error': error
    })

def lista_compras(request):
    # Obtener mes y año actuales por defecto
    today = datetime.now()
    mes = request.GET.get('mes', str(today.month))
    año = int(request.GET.get('año', today.year))
    
    # Filtrar compras por mes y año
    if mes == 'todos':
        # Mostrar todos los meses del año
        compras = Compra.objects.filter(
            fecha__year=año
        ).order_by('-fecha')
    else:
        # Mostrar solo el mes especificado
        mes = int(mes)
        compras = Compra.objects.filter(
            fecha__month=mes,
            fecha__year=año
        ).order_by('-fecha')
    
    # Verificar y limpiar la variable de sesión
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
    for compra in Compra.objects.values_list('fecha__year', flat=True).distinct():
        años_disponibles.add(compra)
    años_disponibles = sorted(list(años_disponibles), reverse=True)
    # Si no hay años, agregar el año actual
    if not años_disponibles:
        años_disponibles = [today.year]
    
    return render(request, 'compras/lista_compras.html', {
        'compras': compras,
        'mostrar_mensaje': mostrar_mensaje,
        'mes_seleccionado': mes,
        'año_seleccionado': año,
        'meses': meses,
        'años_disponibles': años_disponibles
    })

def detalle_compra(request, id_compra):
    compra = get_object_or_404(Compra, pk=id_compra)
    detalles = compra.detalles.all().select_related('id_prod')
    SystemMessage.objects.create(
        message=f"Usuario {request.user} consultó el detalle de la compra #{id_compra}",
        level='info',
        app='compras',
        user=request.user
    )
    return render(request, 'compras/detalle_compra.html', {
        'compra': compra,
        'detalles': detalles
    })