from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal
from .models import ConfiguracionReporte
from inventario.models import Producto
from ventas.models import Movimiento, Detalle as DetalleVenta
from compras.models import Compra, DetalleCompra
from usuario.models import Usuario

# Tests para el módulo reportes: configuración de reportes, generación de reportes,
# filtrado por fechas y formatos de exportación (PDF, Excel)
class ReportesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False

    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            302: "Found - Redirección temporal",
            400: "Bad Request - La solicitud contiene errores",
            404: "Not Found - Recurso no encontrado",
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")

    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*14 + "  TEST DE REPORTES  " + "="*31)
            print("="*65)
            print("="*65)
            # Crear usuario de prueba
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Reportes",
                ApePa="Test",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            print("✓ Usuario de prueba creado exitosamente")
            print(f"  → RUT: {self.usuario.RutUsuua}")
            
            # Crear producto de prueba
            self.producto = Producto.objects.create(
                nombre="Producto Test",
                categoria="Madera",
                precio=Decimal("1000"),
                stock=50
            )
            print("✓ Producto de prueba creado")
            
            # Iniciar sesión
            self.client = Client()
            login_success = self.client.login(username=self.usuario.RutUsuua, password="testpass123")
            print("\n✓ Inicio de sesión:", "Exitoso" if login_success else "Fallido")
            print("-"*50)
            self.__class__._setup_message_shown = True
        else:
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Reportes",
                ApePa="Test",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            self.producto = Producto.objects.create(
                nombre="Producto Test",
                categoria="Madera",
                precio=Decimal("1000"),
                stock=50
            )
            self.client = Client()
            self.client.login(username=self.usuario.RutUsuua, password="testpass123")

    def test_crear_configuracion_reporte(self):
        print("\n" + "="*50)
        print("TEST: CREAR CONFIGURACIÓN DE REPORTE")
        print("="*50)
        print("• Creando configuración de reporte...")
        
        fecha_inicio = date.today() - timedelta(days=30)
        fecha_fin = date.today()
        
        config = ConfiguracionReporte.objects.create(
            nombre="Reporte Mensual",
            incluir_ventas=True,
            incluir_compras=True,
            incluir_inventario=True,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        print("\n✓ Configuración creada:")
        print(f"  → ID: {config.id}")
        print(f"  → Nombre: {config.nombre}")
        print(f"  → Incluir ventas: {config.incluir_ventas}")
        print(f"  → Incluir compras: {config.incluir_compras}")
        print(f"  → Incluir inventario: {config.incluir_inventario}")
        print(f"  → Período: {config.fecha_inicio} a {config.fecha_fin}")
        
        self.assertEqual(config.nombre, "Reporte Mensual")
        self.assertTrue(config.incluir_ventas)
        self.assertTrue(config.incluir_compras)
        print("-"*50)

    def test_configuracion_parcial(self):
        print("\n" + "="*50)
        print("TEST: CONFIGURACIÓN PARCIAL (SOLO VENTAS)")
        print("="*50)
        print("• Creando configuración parcial...")
        
        config = ConfiguracionReporte.objects.create(
            nombre="Reporte de Ventas",
            incluir_ventas=True,
            incluir_compras=False,
            incluir_inventario=False,
            fecha_inicio=date.today() - timedelta(days=7),
            fecha_fin=date.today()
        )
        
        print("\n✓ Configuración parcial creada:")
        print(f"  → Incluir ventas: {config.incluir_ventas}")
        print(f"  → Incluir compras: {config.incluir_compras}")
        print(f"  → Incluir inventario: {config.incluir_inventario}")
        
        self.assertTrue(config.incluir_ventas)
        self.assertFalse(config.incluir_compras)
        print("-"*50)

    def test_str_representation(self):
        print("\n" + "="*50)
        print("TEST: REPRESENTACIÓN EN STRING")
        print("="*50)
        
        config = ConfiguracionReporte.objects.create(
            nombre="Reporte Trimestral",
            incluir_ventas=True,
            incluir_compras=True,
            incluir_inventario=True,
            fecha_inicio=date.today() - timedelta(days=90),
            fecha_fin=date.today()
        )
        
        str_rep = str(config)
        print(f"\n• Representación en string: {str_rep}")
        self.assertEqual(str_rep, "Reporte Trimestral")
        print("-"*50)

    def test_acceso_sin_login(self):
        print("\n" + "="*50)
        print("TEST: ACCESO SIN LOGIN")
        print("="*50)
        print("• Creando cliente sin autenticación...")
        client_sin_login = Client()
        
        print("\n• Intentando acceder a generar_reporte...")
        response = client_sin_login.get(reverse('reportes:generar'))
        
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        # Debería redirigir a login (302) o mostrar acceso denegado
        self.assertIn(response.status_code, [302, 403])
        print("-"*50)

    def test_vista_formulario_reporte(self):
        print("\n" + "="*50)
        print("TEST: VISTA FORMULARIO DE REPORTE")
        print("="*50)
        print("• Accediendo a la vista del formulario...")
        
        response = self.client.get(reverse('reportes:generar'))
        
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        if response.status_code == 200:
            print(f"  → Template usado: {response.templates[0].name if response.templates else 'No template'}")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def test_crear_venta_para_reporte(self):
        print("\n" + "="*50)
        print("TEST: CREAR VENTA PARA REPORTE")
        print("="*50)
        print("• Creando venta...")
        
        venta = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('2000')
        )
        
        DetalleVenta.objects.create(
            id_mov=venta,
            id_prod=self.producto,
            precio_uni=Decimal('1000'),
            cantidad=2
        )
        
        print("\n✓ Venta creada:")
        print(f"  → ID de venta: {venta.id_mov}")
        print(f"  → Total: ${venta.total}")
        print(f"  → Tipo: {venta.tipo}")
        
        self.assertEqual(venta.tipo, 'VENTA')
        self.assertEqual(venta.total, Decimal('2000'))
        print("-"*50)

    def test_crear_compra_para_reporte(self):
        print("\n" + "="*50)
        print("TEST: CREAR COMPRA PARA REPORTE")
        print("="*50)
        print("• Creando compra...")
        
        compra = Compra.objects.create(
            rut_usu=self.usuario,
            proveedor="Proveedor Test",
            total=Decimal('5000')
        )
        
        DetalleCompra.objects.create(
            id_compra=compra,
            id_prod=self.producto,
            precio_uni=Decimal('2500'),
            cantidad=2
        )
        
        print("\n✓ Compra creada:")
        print(f"  → ID de compra: {compra.id_compra}")
        print(f"  → Proveedor: {compra.proveedor}")
        print(f"  → Total: ${compra.total}")
        
        self.assertEqual(compra.proveedor, "Proveedor Test")
        self.assertEqual(compra.total, Decimal('5000'))
        print("-"*50)

    def test_filtro_por_fechas(self):
        print("\n" + "="*50)
        print("TEST: FILTRO POR FECHAS")
        print("="*50)
        print("• Creando ventas con diferentes fechas...")
        
        # Venta reciente
        venta_reciente = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('1000')
        )
        
        # Venta antigua
        venta_antigua = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('500')
        )
        venta_antigua.fecha = timezone.now() - timedelta(days=45)
        venta_antigua.save()
        
        print("\n• Filtrando ventas de los últimos 30 días...")
        fecha_inicio = timezone.now() - timedelta(days=30)
        ventas_recientes = Movimiento.objects.filter(fecha__gte=fecha_inicio)
        
        print(f"  → Ventas en últimos 30 días: {ventas_recientes.count()}")
        self.assertEqual(ventas_recientes.count(), 1)
        print("-"*50)

    def test_generador_reporte_pdf(self):
        print("\n" + "="*50)
        print("TEST: GENERAR REPORTE PDF")
        print("="*50)
        print("• Creando datos para reporte...")
        
        # Crear venta
        venta = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('2000')
        )
        
        print("\n• Generando reporte PDF...")
        fecha_inicio = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(
            reverse('reportes:generar'),
            {
                'formato': 'pdf',
                'tipo': 'ventas',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
        )
        
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print(f"  → Content-Type: {response.get('Content-Type', 'No especificado')}")
        
        if response.status_code == 200:
            print("  ✓ PDF generado exitosamente")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def test_generador_reporte_excel(self):
        print("\n" + "="*50)
        print("TEST: GENERAR REPORTE EXCEL")
        print("="*50)
        print("• Creando datos para reporte...")
        
        # Crear compra
        compra = Compra.objects.create(
            rut_usu=self.usuario,
            proveedor="Proveedor Test",
            total=Decimal('5000')
        )
        
        print("\n• Generando reporte Excel...")
        fecha_inicio = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(
            reverse('reportes:generar'),
            {
                'formato': 'excel',
                'tipo': 'compras',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
        )
        
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print(f"  → Content-Type: {response.get('Content-Type', 'No especificado')}")
        
        if response.status_code == 200:
            print("  ✓ Excel generado exitosamente")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def test_reporte_completo(self):
        print("\n" + "="*50)
        print("TEST: REPORTE COMPLETO")
        print("="*50)
        print("• Preparando datos para reporte completo...")
        
        # Crear venta
        venta = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('2000')
        )
        
        # Crear compra
        compra = Compra.objects.create(
            rut_usu=self.usuario,
            proveedor="Proveedor Test",
            total=Decimal('5000')
        )
        
        print("\n• Generando reporte completo...")
        fecha_inicio = (timezone.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        fecha_fin = timezone.now().strftime('%Y-%m-%d')
        
        response = self.client.get(
            reverse('reportes:generar'),
            {
                'formato': 'pdf',
                'tipo': 'completo',
                'fecha_inicio': fecha_inicio,
                'fecha_fin': fecha_fin
            }
        )
        
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print("  ✓ Reporte completo generado")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def test_producto_bajo_stock(self):
        print("\n" + "="*50)
        print("TEST: PRODUCTO BAJO STOCK EN REPORTE")
        print("="*50)
        print("• Creando producto con stock bajo...")
        
        producto_bajo = Producto.objects.create(
            nombre="Producto Bajo Stock",
            categoria="Madera",
            precio=Decimal("1000"),
            stock=2,
            umbral_stock_invierno=10
        )
        
        print(f"  → Nombre: {producto_bajo.nombre}")
        print(f"  → Stock: {producto_bajo.stock}")
        print(f"  → Umbral: {producto_bajo.umbral_stock_invierno}")
        
        # Verificar que está bajo mínimo
        bajo_minimo = producto_bajo.stock <= producto_bajo.umbral_stock_invierno
        print(f"  → ¿Está bajo mínimo?: {bajo_minimo}")
        
        self.assertTrue(bajo_minimo)
        print("-"*50)

    def tearDown(self):
        # Limpieza después de cada prueba
        ConfiguracionReporte.objects.all().delete()
        Movimiento.objects.all().delete()
        DetalleVenta.objects.all().delete()
        Compra.objects.all().delete()
        DetalleCompra.objects.all().delete()
        Producto.objects.all().delete()
        Usuario.objects.all().delete()
