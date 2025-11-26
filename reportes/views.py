from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta
from django.db.models import Sum, Count, F
from django.utils import timezone
from django.conf import settings
import xlsxwriter
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
import pytz

from ventas.models import Movimiento, Detalle
from compras.models import Compra, DetalleCompra
from inventario.models import Producto

@login_required
def generar_reporte(request):
    # Si es una petición GET sin parámetros, mostrar el formulario
    if not request.GET.get('formato'):
        return render(request, 'reportes/generar_reporte.html')

    # Si hay parámetros, generar el reporte
    try:
        # Configurar zona horaria de Chile
        chile_tz = pytz.timezone('America/Santiago')
        
        # Convertir fechas
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        
        if fecha_inicio:
            # Convertir a datetime y agregar hora inicial del día
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d')
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0)
            fecha_inicio = chile_tz.localize(fecha_inicio)
        else:
            # Usar fecha actual menos 30 días
            fecha_inicio = timezone.localtime(timezone.now(), timezone=chile_tz) - timedelta(days=30)
            fecha_inicio = fecha_inicio.replace(hour=0, minute=0, second=0)

        if fecha_fin:
            # Convertir a datetime y agregar hora final del día
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d')
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
            fecha_fin = chile_tz.localize(fecha_fin)
        else:
            # Usar fecha actual
            fecha_fin = timezone.localtime(timezone.now(), timezone=chile_tz)
            fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)

        tipo_reporte = request.GET.get('tipo', 'completo')
        formato = request.GET.get('formato', 'pdf')

        # Datos base
        data = {
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'tipo_reporte': tipo_reporte
        }

        # Agregar datos según el tipo de reporte
        if tipo_reporte in ['completo', 'ventas']:
            data.update({
                'ventas': Movimiento.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(
                    total_ventas=Sum('total'),
                    num_ventas=Count('id_mov')
                ),
                'detalles_ventas': Detalle.objects.filter(
                    id_mov__fecha__range=[fecha_inicio, fecha_fin]
                ).select_related('id_mov', 'id_prod').values(
                    'id_mov__fecha',
                    'id_prod__nombre',
                    'cantidad',
                    'precio_uni'
                ).annotate(
                    fecha=F('id_mov__fecha'),
                    producto=F('id_prod__nombre'),
                    subtotal=F('precio_uni') * F('cantidad')
                )
            })

        if tipo_reporte in ['completo', 'compras']:
            data.update({
                'compras': Compra.objects.filter(
                    fecha__range=[fecha_inicio, fecha_fin]
                ).aggregate(
                    total_compras=Sum('total'),
                    num_compras=Count('id_compra')
                ),
                'detalles_compras': DetalleCompra.objects.filter(
                    id_compra__fecha__range=[fecha_inicio, fecha_fin]
                ).select_related('id_compra', 'id_prod').values(
                    'id_compra__fecha',
                    'id_prod__nombre',
                    'cantidad',
                    'precio_uni',
                    'id_compra__proveedor'
                ).annotate(
                    fecha=F('id_compra__fecha'),
                    producto=F('id_prod__nombre'),
                    proveedor=F('id_compra__proveedor'),
                    subtotal=F('precio_uni') * F('cantidad')
                )
            })

        if tipo_reporte in ['completo', 'productos_bajo_stock']:
            data.update({
                'productos': Producto.objects.filter(
                    stock__lte=F('umbral_stock_invierno')
                ).values(
                    'nombre', 
                    'stock', 
                    'precio',
                    'umbral_stock_invierno'
                ).order_by('stock')
            })

        if formato == 'excel':
            return generar_excel(data)
        else:
            return generar_pdf(data)

    except Exception as e:
        return render(request, 'reportes/generar_reporte.html', {
            'error': f'Error al generar el reporte: {str(e)}'
        })

def generar_excel(data):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    
    # Formatos
    titulo_formato = workbook.add_format({
        'bold': True,
        'font_size': 14,
        'align': 'center',
        'bg_color': '#4B5563',
        'font_color': 'white'
    })
    
    header_formato = workbook.add_format({
        'bold': True,
        'bg_color': '#9CA3AF',
        'font_color': 'white',
        'border': 1
    })
    
    celda_formato = workbook.add_format({
        'border': 1
    })
    
    numero_formato = workbook.add_format({
        'border': 1,
        'num_format': '$#,##0'
    })

    # Ventas
    if data['tipo_reporte'] in ['completo', 'ventas'] and 'ventas' in data:
        worksheet_ventas = workbook.add_worksheet("Ventas")
        worksheet_ventas.merge_range('A1:E1', 'Reporte de Ventas', titulo_formato)
        worksheet_ventas.write('A3', 'Total de Ventas', header_formato)
        worksheet_ventas.write('B3', data['ventas']['total_ventas'] or 0, numero_formato)
        worksheet_ventas.write('A4', 'Número de Ventas', header_formato)
        worksheet_ventas.write('B4', data['ventas']['num_ventas'] or 0, celda_formato)
        
        # Detalle de Ventas
        if data['detalles_ventas']:
            headers = ['Fecha', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']
            for col, header in enumerate(headers):
                worksheet_ventas.write(5, col, header, header_formato)
            
            row = 6
            for detalle in data['detalles_ventas']:
                worksheet_ventas.write(row, 0, detalle['fecha'].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M"), celda_formato)
                worksheet_ventas.write(row, 1, detalle['producto'], celda_formato)
                worksheet_ventas.write(row, 2, detalle['cantidad'], celda_formato)
                worksheet_ventas.write(row, 3, detalle['precio_uni'], numero_formato)
                worksheet_ventas.write(row, 4, detalle['subtotal'], numero_formato)
                row += 1
            
            worksheet_ventas.set_column('A:A', 15)
            worksheet_ventas.set_column('B:B', 30)
            worksheet_ventas.set_column('C:E', 15)

    # Compras
    if data['tipo_reporte'] in ['completo', 'compras'] and 'compras' in data:
        worksheet_compras = workbook.add_worksheet("Compras")
        worksheet_compras.merge_range('A1:F1', 'Reporte de Compras', titulo_formato)
        worksheet_compras.write('A3', 'Total de Compras', header_formato)
        worksheet_compras.write('B3', data['compras']['total_compras'] or 0, numero_formato)
        worksheet_compras.write('A4', 'Número de Compras', header_formato)
        worksheet_compras.write('B4', data['compras']['num_compras'] or 0, celda_formato)
        
        # Detalle de Compras
        if data['detalles_compras']:
            headers = ['Fecha', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Proveedor']
            for col, header in enumerate(headers):
                worksheet_compras.write(5, col, header, header_formato)
            
            row = 6
            for detalle in data['detalles_compras']:
                worksheet_compras.write(row, 0, detalle['fecha'].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M"), celda_formato)
                worksheet_compras.write(row, 1, detalle['producto'], celda_formato)
                worksheet_compras.write(row, 2, detalle['cantidad'], celda_formato)
                worksheet_compras.write(row, 3, detalle['precio_uni'], numero_formato)
                worksheet_compras.write(row, 4, detalle['subtotal'], numero_formato)
                worksheet_compras.write(row, 5, detalle['proveedor'], celda_formato)
                row += 1
            
            worksheet_compras.set_column('A:A', 15)
            worksheet_compras.set_column('B:B', 30)
            worksheet_compras.set_column('C:E', 15)
            worksheet_compras.set_column('F:F', 20)

    # Productos Bajo Stock
    if data['tipo_reporte'] in ['completo', 'productos_bajo_stock'] and 'productos' in data:
        worksheet_productos = workbook.add_worksheet("Productos Bajo Stock")
        worksheet_productos.merge_range('A1:D1', 'Productos Bajo Stock Mínimo', titulo_formato)
        
        headers = ['Nombre', 'Stock Actual', 'Stock Mínimo', 'Precio']
        for col, header in enumerate(headers):
            worksheet_productos.write(2, col, header, header_formato)
        
        row = 3
        for producto in data['productos']:
            worksheet_productos.write(row, 0, producto['nombre'], celda_formato)
            worksheet_productos.write(row, 1, producto['stock'], celda_formato)
            worksheet_productos.write(row, 2, producto['umbral_stock_invierno'], celda_formato)
            worksheet_productos.write(row, 3, producto['precio'], numero_formato)
            row += 1
        
        worksheet_productos.set_column('A:A', 30)
        worksheet_productos.set_column('B:D', 15)

    workbook.close()
    output.seek(0)

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=reporte.xlsx'
    return response

def generar_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Título y tipo de reporte
    if data['tipo_reporte'] == 'completo':
        elements.append(Paragraph('Reporte General', styles['Title']))
    elif data['tipo_reporte'] == 'ventas':
        elements.append(Paragraph('Reporte de Ventas', styles['Title']))
    elif data['tipo_reporte'] == 'compras':
        elements.append(Paragraph('Reporte de Compras', styles['Title']))
    elif data['tipo_reporte'] == 'productos_bajo_stock':
        elements.append(Paragraph('Reporte de Productos Bajo Stock', styles['Title']))

    # Fechas (excepto para reporte de productos bajo stock)
    if data['tipo_reporte'] != 'productos_bajo_stock':
        elements.append(Paragraph(
            f'Período: {data["fecha_inicio"].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M")} - '
            f'{data["fecha_fin"].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M")}',
            styles['Normal']
        ))
    elements.append(Paragraph('<br/>', styles['Normal']))
    
    # Sección de Ventas
    if data['tipo_reporte'] in ['completo', 'ventas'] and 'ventas' in data:
        elements.append(Paragraph('Resumen de Ventas', styles['Heading1']))
        ventas_data = [
            ['Total de Ventas', f"${data['ventas']['total_ventas'] or 0:,.0f}"],
            ['Número de Ventas', str(data['ventas']['num_ventas'] or 0)]
        ]
        ventas_table = Table(ventas_data, colWidths=[300, 200])
        ventas_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(ventas_table)
        elements.append(Paragraph('<br/>', styles['Normal']))

        # Detalle de Ventas
        elements.append(Paragraph('Detalle de Ventas', styles['Heading2']))
        if data['detalles_ventas']:
            ventas_headers = ['Fecha', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']
            detalles_ventas_data = [ventas_headers]
            for detalle in data['detalles_ventas']:
                detalles_ventas_data.append([
                    detalle['fecha'].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M"),
                    detalle['producto'],
                    str(detalle['cantidad']),
                    f"${detalle['precio_uni']:,.0f}",
                    f"${detalle['subtotal']:,.0f}"
                ])
            detalles_ventas_table = Table(detalles_ventas_data, colWidths=[80, 200, 70, 70, 80])
            detalles_ventas_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT')
            ]))
            elements.append(detalles_ventas_table)
        else:
            elements.append(Paragraph('No hay ventas en este período', styles['Normal']))
        elements.append(Paragraph('<br/><br/>', styles['Normal']))
    
    # Sección de Compras
    if data['tipo_reporte'] in ['completo', 'compras'] and 'compras' in data:
        elements.append(Paragraph('Resumen de Compras', styles['Heading1']))
        compras_data = [
            ['Total de Compras', f"${data['compras']['total_compras'] or 0:,.0f}"],
            ['Número de Compras', str(data['compras']['num_compras'] or 0)]
        ]
        compras_table = Table(compras_data, colWidths=[300, 200])
        compras_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(compras_table)
        elements.append(Paragraph('<br/>', styles['Normal']))

        # Detalle de Compras
        elements.append(Paragraph('Detalle de Compras', styles['Heading2']))
        if data['detalles_compras']:
            compras_headers = ['Fecha', 'Producto', 'Cantidad', 'Precio Unit.', 'Subtotal', 'Proveedor']
            detalles_compras_data = [compras_headers]
            for detalle in data['detalles_compras']:
                detalles_compras_data.append([
                    detalle['fecha'].astimezone(pytz.timezone("America/Santiago")).strftime("%d/%m/%Y %H:%M"),
                    detalle['producto'],
                    str(detalle['cantidad']),
                    f"${detalle['precio_uni']:,.0f}",
                    f"${detalle['subtotal']:,.0f}",
                    detalle['proveedor']
                ])
            detalles_compras_table = Table(detalles_compras_data, colWidths=[80, 150, 70, 70, 80, 100])
            detalles_compras_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT')
            ]))
            elements.append(detalles_compras_table)
        else:
            elements.append(Paragraph('No hay compras en este período', styles['Normal']))
        elements.append(Paragraph('<br/><br/>', styles['Normal']))

    # Sección de Productos Bajo Stock
    if data['tipo_reporte'] in ['completo', 'productos_bajo_stock'] and 'productos' in data:
        elements.append(Paragraph('Productos Bajo Stock Mínimo', styles['Heading1']))
        if data['productos']:
            productos_headers = ['Nombre', 'Stock Actual', 'Stock Mínimo', 'Precio']
            productos_data = [productos_headers]
            for producto in data['productos']:
                productos_data.append([
                    producto['nombre'],
                    str(producto['stock']),
                    str(producto['umbral_stock_invierno']),
                    f"${producto['precio']:,.0f}"
                ])
            productos_table = Table(productos_data, colWidths=[200, 100, 100, 100])
            productos_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'RIGHT')
            ]))
            elements.append(productos_table)
        else:
            elements.append(Paragraph('No hay productos bajo stock mínimo', styles['Normal']))

    # Construir el PDF
    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=reporte.pdf'
    response.write(pdf)
    return response