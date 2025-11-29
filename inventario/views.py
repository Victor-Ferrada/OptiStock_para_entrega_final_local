# inventario/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction  # Añade esta importación
from django.utils.timezone import now  # Añade esta importación
from .models import Producto, MovimientoStock
from .forms import ProductoForm, MovimientoStockForm, SeteoStockForm  # Añade SeteoStockForm aquí
from .forms import UmbralStockForm
from django.forms import modelformset_factory


def base_view(request):
    return render(request, 'inventario/index.html')

# 1. Registrar un producto
def registrar_producto(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.umbral_stock_invierno = 10
            producto.umbral_stock_verano = 5
            producto.save()
            
            # Mensaje más simple
            request.session['mensaje_exito'] = 'Producto creado con éxito'
            messages.success(request, 'Producto creado con éxito')
            
            return redirect('inventario:lista_productos')
        else:
            messages.error(request, 'Por favor, corrija los errores en el formulario.')
    else:
        form = ProductoForm()
    return render(request, 'inventario/registrar_producto.html', {'form': form})


# 2. Actualizar stock
def seleccionar_producto_actualizar(request):
    productos = Producto.objects.all()

    # Filtros opcionales
    categoria = request.GET.get('categoria')
    nombre = request.GET.get('nombre')
    cepillado = request.GET.get('cepillado')

    if categoria:
        productos = productos.filter(categoria=categoria)
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if cepillado:
        productos = productos.filter(cepillado=(cepillado == 'true'))

    return render(request, 'inventario/seleccionar_producto_actualizar.html', {'productos': productos})



def actualizar_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if request.method == 'POST':
        form = SeteoStockForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Guardamos el stock anterior para el registro
                    stock_anterior = producto.stock
                    nuevo_stock = form.cleaned_data['nuevo_stock']
                    
                    # Creamos un registro del cambio
                    MovimientoStock.objects.create(
                        producto=producto,
                        cantidad=nuevo_stock - stock_anterior,  # La diferencia como movimiento
                        fecha=now()
                    )
                    
                    # Actualizamos el stock
                    producto.stock = nuevo_stock
                    producto.save()
                    
                    messages.success(
                        request, 
                        f'Stock actualizado correctamente. '
                        f'Stock anterior: {stock_anterior}, '
                        f'Nuevo stock: {nuevo_stock}'
                    )
                    return redirect('inventario:seleccionar-producto-actualizar')
                    
            except Exception as e:
                messages.error(request, f'Error al actualizar el stock: {str(e)}')
    else:
        form = SeteoStockForm(initial={'nuevo_stock': producto.stock})

    return render(request, 'inventario/actualizar_stock.html', {
        'form': form, 
        'producto': producto
    })

    # Actualizar el formulario con información del stock actual
    form.fields['cantidad'].widget.attrs.update({
        'placeholder': f'Stock actual: {producto.stock}',
        'class': 'form-control'
    })
    form.fields['cantidad'].label = 'Cantidad a modificar (use números negativos para disminuir)'

    context = {
        'form': form,
        'producto': producto
    }

    return render(request, 'inventario/actualizar_stock.html', context)


# 3. Generar alerta de stock.
def generar_alerta_stock(request):
    from django.utils import timezone

    # Determinar el mes actual
    mes_actual = timezone.now().month

    # Chile, simplificado a 2 estaciones:
    # Verano = dic–may   (verano + otoño)
    # Invierno = jun–nov (invierno + primavera)
    meses_verano = [12, 1, 2, 3, 4, 5]     # Diciembre → Mayo
    meses_invierno = [6, 7, 8, 9, 10, 11]  # Junio → Noviembre

    # Estación actual como texto
    if mes_actual in meses_verano:
        estacion_actual = 'Verano'
    else:
        estacion_actual = 'Invierno'

    productos_bajo_stock = []

    for producto in Producto.objects.all():
        # Elegir el umbral correcto según la estación
        if mes_actual in meses_verano:
            umbral = producto.umbral_stock_verano
        else:
            umbral = producto.umbral_stock_invierno

        # Si no hay umbral configurado, se ignora ese producto
        if not umbral or umbral <= 0:
            continue

        # Porcentaje de stock respecto al umbral
        #   ratio = 1.0  → 100% del umbral
        #   ratio = 0.5  →  50% del umbral
        ratio = producto.stock / umbral

        # Solo mostramos productos cuyo stock está en o por debajo de 105% del umbral
        # (pre-alerta para avisar que se está acercando).
        if ratio <= 1.05:
            # 4 niveles:
            #  > 75% a 105%  → gris       (row-normal)
            #  > 50% a 75%   → naranjo    (row-warning)
            #  > 25% a 50%   → rojo       (row-low)
            #  ≤ 25%         → rojo fuerte(row-critical)
            if ratio > 0.75:
                nivel = 'normal'
                css_class = 'row-normal'
            elif ratio > 0.5:
                nivel = 'advertencia'
                css_class = 'row-warning'
            elif ratio > 0.25:
                nivel = 'bajo'
                css_class = 'row-low'
            else:
                nivel = 'critico'
                css_class = 'row-critical'

            productos_bajo_stock.append({
                'producto': producto,
                'stock_actual': producto.stock,
                'umbral': umbral,
                'umbral_invierno': producto.umbral_stock_invierno,
                'umbral_verano': producto.umbral_stock_verano,
                'ratio': round(ratio * 100, 1),  # porcentaje para mostrar si quieres
                'nivel': nivel,
                'css_class': css_class,
            })

    # Ordenar por % del umbral (más crítico primero)
    productos_bajo_stock.sort(key=lambda x: x['ratio'])


    context = {
        'productos_bajo_stock': productos_bajo_stock,
        'total_alertas': len(productos_bajo_stock),
        'estacion_actual': estacion_actual,
    }

    return render(request, 'inventario/alerta_stock.html', context)

# 4. Editar umbrales de stock.
def editar_umbrales_stock(request):
    productos = Producto.objects.all()
    
    # Filtros
    categoria = request.GET.get('categoria')
    nombre = request.GET.get('nombre')

    if categoria:
        productos = productos.filter(categoria=categoria)
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    
    if request.method == 'POST':
        alguno_guardado = False
        for producto in productos:
            form = UmbralStockForm(request.POST, instance=producto, prefix=str(producto.id))
            if form.is_valid():
                form.save()
                alguno_guardado = True
            else:
                messages.error(request, "Error al guardar los umbrales")
                return redirect('inventario:editar-umbrales-de-stock')
        
        if alguno_guardado:
            # Usar variable de sesión
            request.session['mostrar_mensaje'] = True
        
        return redirect('inventario:editar-umbrales-de-stock')
    
    # Verificar y limpiar la variable de sesión
    mostrar_mensaje = request.session.pop('mostrar_mensaje', False)
    
    formset = [UmbralStockForm(instance=producto, prefix=str(producto.id)) for producto in productos]
    
    return render(request, 'inventario/editar_umbrales_stock.html', {
        'formset': formset,
        'productos': productos,
        'mostrar_mensaje': mostrar_mensaje
    })


# 4. Registrar procesos adicionales (cepillado).
def seleccionar_producto_para_cepillar(request):
    productos = Producto.objects.filter(categoria='Madera')
    categoria = request.GET.get('categoria', '')
    nombre = request.GET.get('nombre', '')

    if categoria:
        productos = productos.filter(categoria=categoria)
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)

    # Obtener mensaje de la sesión
    mensaje_exito = request.session.pop('mensaje_exito', None)
    if mensaje_exito:
        messages.success(request, mensaje_exito)

    return render(request, 'inventario/selectar_producto_para_cepillar.html', {
        'productos': productos,
        'mensaje_exito': mensaje_exito
    })

def registrar_proceso_cepillado(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        cantidad_cepillar = int(request.POST.get('cantidad', 0))
        stock_original = producto.stock
        
        if cantidad_cepillar <= 0:
            messages.error(request, 'La cantidad debe ser mayor a 0.')
        elif cantidad_cepillar > stock_original:
            messages.error(request, f'No hay suficiente stock. Solo hay {stock_original} disponibles.')
        else:
            nuevo_stock_original = stock_original - cantidad_cepillar
            producto.stock = nuevo_stock_original
            
            if nuevo_stock_original == 0:
                producto.cepillado = True
            
            producto.save()
            
            nombre_cepillado = f"{producto.nombre} CEPI"
            
            producto_cepillado, creado = Producto.objects.get_or_create(
                nombre=nombre_cepillado,
                categoria=producto.categoria,
                cepillado=True,
                defaults={
                    'stock': 0,
                    'precio': producto.precio + 3000,
                    'largo': producto.largo,
                    'ancho': producto.ancho,
                    'alto': producto.alto
                }
            )
            
            producto_cepillado.stock += cantidad_cepillar
            producto_cepillado.save()
            
            request.session['mensaje_exito'] = f'Se han cepillado {cantidad_cepillar} unidades exitosamente'
            messages.success(request, f'Se han cepillado {cantidad_cepillar} unidades exitosamente')
            
            return redirect('inventario:selectar_producto_para_cepillar')
    
    return render(request, 'inventario/registrar_proceso_cepillado.html', {'producto': producto})



# 5. Visualizar y filtrar productos.

def lista_productos(request):
    productos = Producto.objects.all()
    
    # Recuperar mensaje de la sesión
    mensaje_exito = request.session.pop('mensaje_exito', None)
    if mensaje_exito:
        messages.success(request, mensaje_exito)
    
    # Filtros
    categoria = request.GET.get('categoria')
    nombre = request.GET.get('nombre')
    cepillado = request.GET.get('cepillado')

    if categoria:
        productos = productos.filter(categoria=categoria)
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)
    if cepillado:
        productos = productos.filter(cepillado=(cepillado == 'true'))

    return render(request, 'inventario/lista_productos.html', {'productos': productos})


# 6. Registrar productos especiales.

def registrar_producto_especial(request):
    if request.method == 'POST':
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            if producto.categoria != 'Especial':
                messages.error(request, 'Solo se pueden registrar productos especiales en esta funcionalidad.')
            else:
                producto.especial = True
                producto.save()
                messages.success(request, 'Producto especial registrado con éxito.')
                return redirect('inventario:lista_productos')
    else:
        form = ProductoForm()
    return render(request, 'inventario/registrar_producto_especial.html', {'form': form})



