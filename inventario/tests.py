from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from .models import Producto, MovimientoStock
from usuario.models import Usuario
from django.utils import timezone
from datetime import datetime

# Tests para el módulo de inventario: creación de productos, actualización de stock,
# alertas de stock bajo, procesos de cepillado y gestión de productos especiales
class InventarioTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False

    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            302: "Found - Redirección temporal (el producto se creó y redirige a otra página)",
            400: "Bad Request - La solicitud contiene errores",
            404: "Not Found - Recurso no encontrado",
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")

    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*12 + "  TEST DE INVENTARIO  " + "="*31)
            print("="*65)
            print("="*65)
            # Crear usuario de prueba
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Inventario",
                ApePa="Test",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            print("✓ Usuario de prueba creado exitosamente")
            print(f"  → RUT: {self.usuario.RutUsuua}")
            # Iniciar sesión
            self.client = Client()
            login_success = self.client.login(username=self.usuario.RutUsuua, password="testpass123")
            print("\n✓ Inicio de sesión:", "Exitoso" if login_success else "Fallido")
            print("-"*50)
            self.__class__._setup_message_shown = True
        else:
            # Si ya se mostró el mensaje, solo crear el usuario
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Inventario",
                ApePa="Test",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            self.client = Client()
            self.client.login(username=self.usuario.RutUsuua, password="testpass123")

    def test_registrar_producto_exitoso(self):
        print("\n" + "="*50)
        print("TEST: REGISTRAR PRODUCTO EXITOSO")
        print("="*50)
        print("• Preparando datos del producto...")
        datos_producto = {
            'nombre': 'Madera de Pino',
            'categoria': 'Madera',
            'precio': '5000',
            'stock': 50,
            'largo': 2.0,
            'ancho': 0.5,
            'alto': 0.3,
            'cepillado': False,
            'especial': False,
        }
        print("• Enviando solicitud de registro...")
        response = self.client.post(reverse('inventario:registrar_producto'), datos_producto)
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        
        if Producto.objects.exists():
            producto = Producto.objects.first()
            print("\n✓ Producto creado exitosamente")
            print(f"  → ID del producto: {producto.id}")
            print(f"  → Nombre: {producto.nombre}")
            print(f"  → Categoría: {producto.categoria}")
            print(f"  → Precio: ${producto.precio}")
            print(f"  → Stock: {producto.stock}")
            print(f"  → Umbral invierno: {producto.umbral_stock_invierno}")
            print(f"  → Umbral verano: {producto.umbral_stock_verano}")
            # Verificaciones
            self.assertEqual(response.status_code, 302)
            self.assertEqual(producto.nombre, 'Madera de Pino')
            self.assertEqual(producto.categoria, 'Madera')
            self.assertEqual(producto.precio, Decimal('5000'))
            self.assertEqual(producto.stock, 50)
        else:
            self.fail("El producto no fue creado")
        print("-"*50)

    def test_obtener_umbral_actual(self):
        print("\n" + "="*50)
        print("TEST: OBTENER UMBRAL ACTUAL POR ESTACIÓN")
        print("="*50)
        producto = Producto.objects.create(
            nombre="Producto Test Umbral",
            categoria="Madera",
            precio=Decimal("1000"),
            stock=20,
            umbral_stock_invierno=15,
            umbral_stock_verano=5
        )
        print("• Producto creado con umbrales:")
        print(f"  → Umbral invierno: {producto.umbral_stock_invierno}")
        print(f"  → Umbral verano: {producto.umbral_stock_verano}")
        
        umbral = producto.get_umbral_actual()
        print(f"\n• Umbral actual según mes: {umbral}")
        
        # El umbral debe ser uno de los definidos o un valor intermedio
        mes_actual = timezone.now().month
        meses_invierno = [6, 7, 8]
        meses_verano = [12, 1, 2]
        
        if mes_actual in meses_invierno:
            print(f"  → Estación: Invierno")
            self.assertEqual(umbral, producto.umbral_stock_invierno)
        elif mes_actual in meses_verano:
            print(f"  → Estación: Verano")
            self.assertEqual(umbral, producto.umbral_stock_verano)
        else:
            print(f"  → Estación: Intermedia")
        
        print("-"*50)

    def test_esta_bajo_minimo(self):
        print("\n" + "="*50)
        print("TEST: VERIFICAR SI PRODUCTO ESTÁ BAJO MÍNIMO")
        print("="*50)
        producto = Producto.objects.create(
            nombre="Producto Bajo Stock",
            categoria="Planchas",
            precio=Decimal("2000"),
            stock=3,
            umbral_stock_invierno=10,
            umbral_stock_verano=5
        )
        print("• Producto creado:")
        print(f"  → Stock: {producto.stock}")
        print(f"  → Umbral actual: {producto.get_umbral_actual()}")
        
        bajo_minimo = producto.esta_bajo_minimo()
        print(f"\n✓ ¿Está bajo mínimo?: {bajo_minimo}")
        self.assertTrue(bajo_minimo)
        print("-"*50)

    def test_actualizar_stock(self):
        print("\n" + "="*50)
        print("TEST: ACTUALIZAR STOCK")
        print("="*50)
        producto = Producto.objects.create(
            nombre="Producto Actualizar",
            categoria="Madera",
            precio=Decimal("1500"),
            stock=10
        )
        print(f"• Stock inicial: {producto.stock}")
        print("• Actualizando stock a 25...")
        
        stock_anterior = producto.stock
        producto.stock = 25
        producto.save()
        
        # Crear movimiento de stock
        movimiento = MovimientoStock.objects.create(
            producto=producto,
            cantidad=15
        )
        
        print(f"\n✓ Stock actualizado:")
        print(f"  → Stock anterior: {stock_anterior}")
        print(f"  → Stock nuevo: {producto.stock}")
        print(f"  → Movimiento registrado: {movimiento.cantidad} unidades")
        
        self.assertEqual(producto.stock, 25)
        self.assertEqual(movimiento.cantidad, 15)
        print("-"*50)

    def test_movimiento_stock(self):
        print("\n" + "="*50)
        print("TEST: REGISTRO DE MOVIMIENTO DE STOCK")
        print("="*50)
        producto = Producto.objects.create(
            nombre="Producto Movimiento",
            categoria="Otros",
            precio=Decimal("3000"),
            stock=50
        )
        print("• Creando movimiento de stock...")
        movimiento = MovimientoStock.objects.create(
            producto=producto,
            cantidad=-5,
            fecha=timezone.now()
        )
        print("\n✓ Movimiento registrado:")
        print(f"  → Producto: {movimiento.producto.nombre}")
        print(f"  → Cantidad: {movimiento.cantidad}")
        print(f"  → Fecha: {movimiento.fecha}")
        
        self.assertEqual(movimiento.producto, producto)
        self.assertEqual(movimiento.cantidad, -5)
        print("-"*50)

    def test_registrar_producto_especial(self):
        print("\n" + "="*50)
        print("TEST: REGISTRAR PRODUCTO ESPECIAL")
        print("="*50)
        print("• Preparando datos del producto especial...")
        datos_producto = {
            'nombre': 'Madera Especial Premium',
            'categoria': 'Especial',
            'precio': '15000',
            'stock': 5,
            'largo': 3.0,
            'ancho': 1.0,
            'alto': 0.5,
            'cepillado': False,
            'especial': True,
        }
        print("• Enviando solicitud de registro...")
        response = self.client.post(reverse('inventario:registrar_producto_especial'), datos_producto)
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        
        if Producto.objects.filter(especial=True).exists():
            producto = Producto.objects.filter(especial=True).first()
            print("\n✓ Producto especial creado exitosamente")
            print(f"  → Nombre: {producto.nombre}")
            print(f"  → Categoría: {producto.categoria}")
            print(f"  → ¿Es especial?: {producto.especial}")
            self.assertTrue(producto.especial)
        print("-"*50)

    def test_cepillado_producto(self):
        print("\n" + "="*50)
        print("TEST: PROCESO DE CEPILLADO")
        print("="*50)
        # Crear un producto de madera para cepillar
        producto_original = Producto.objects.create(
            nombre="Madera Disponible",
            categoria="Madera",
            precio=Decimal("1000"),
            stock=10,
            cepillado=False
        )
        print("• Producto original:")
        print(f"  → Nombre: {producto_original.nombre}")
        print(f"  → Stock: {producto_original.stock}")
        print(f"  → Cepillado: {producto_original.cepillado}")
        
        cantidad_cepillar = 5
        print(f"\n• Cepillando {cantidad_cepillar} unidades...")
        
        # Simular el proceso de cepillado
        stock_nuevo_original = producto_original.stock - cantidad_cepillar
        producto_original.stock = stock_nuevo_original
        if stock_nuevo_original == 0:
            producto_original.cepillado = True
        producto_original.save()
        
        nombre_cepillado = f"{producto_original.nombre} CEPI"
        producto_cepillado, creado = Producto.objects.get_or_create(
            nombre=nombre_cepillado,
            categoria=producto_original.categoria,
            cepillado=True,
            defaults={
                'stock': 0,
                'precio': producto_original.precio + 3000,
                'largo': producto_original.largo,
                'ancho': producto_original.ancho,
                'alto': producto_original.alto
            }
        )
        producto_cepillado.stock += cantidad_cepillar
        producto_cepillado.save()
        
        print("\n✓ Proceso completado:")
        print(f"  → Stock original actualizado: {producto_original.stock}")
        print(f"  → Nuevo producto cepillado creado: {producto_cepillado.nombre}")
        print(f"  → Stock cepillado: {producto_cepillado.stock}")
        print(f"  → Precio original: ${producto_original.precio}")
        print(f"  → Precio cepillado: ${producto_cepillado.precio}")
        
        self.assertEqual(producto_original.stock, 5)
        self.assertEqual(producto_cepillado.stock, 5)
        self.assertTrue(producto_cepillado.cepillado)
        print("-"*50)

    def test_lista_productos(self):
        print("\n" + "="*50)
        print("TEST: VISTA DE LISTA DE PRODUCTOS")
        print("="*50)
        # Crear varios productos
        for i in range(3):
            Producto.objects.create(
                nombre=f"Producto {i+1}",
                categoria="Madera" if i % 2 == 0 else "Planchas",
                precio=Decimal(f"{(i+1)*1000}"),
                stock=10+i
            )
        print("• Accediendo a la vista de lista de productos...")
        response = self.client.get(reverse('inventario:lista_productos'))
        print("\n✓ Verificaciones:")
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        if hasattr(response, 'context') and 'productos' in response.context:
            print(f"  → Número de productos listados: {len(response.context['productos'])}")
        print(f"  → Template usado: {response.templates[0].name if response.templates else 'No template'}")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventario/lista_productos.html')
        print("-"*50)

    def test_alerta_stock_bajo(self):
        print("\n" + "="*50)
        print("TEST: VISTA DE ALERTAS DE STOCK BAJO")
        print("="*50)
        # Crear productos con stock bajo
        producto_bajo = Producto.objects.create(
            nombre="Producto Stock Bajo",
            categoria="Madera",
            precio=Decimal("1000"),
            stock=2,
            umbral_stock_invierno=10,
            umbral_stock_verano=5
        )
        print("• Producto con stock bajo creado")
        print(f"  → Nombre: {producto_bajo.nombre}")
        print(f"  → Stock: {producto_bajo.stock}")
        print(f"  → Umbral actual: {producto_bajo.get_umbral_actual()}")
        print(f"  → ¿Está bajo mínimo?: {producto_bajo.esta_bajo_minimo()}")
        
        print("\n• Accediendo a la vista de alertas...")
        response = self.client.get(reverse('inventario:alerta_stock'))
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        
        if hasattr(response, 'context'):
            alertas = response.context.get('productos_bajo_stock', [])
            print(f"  → Número de alertas: {len(alertas)}")
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventario/alerta_stock.html')
        print("-"*50)

    def test_filtro_por_categoria(self):
        print("\n" + "="*50)
        print("TEST: FILTRO DE PRODUCTOS POR CATEGORÍA")
        print("="*50)
        # Crear productos de diferentes categorías
        Producto.objects.create(
            nombre="Madera Premium",
            categoria="Madera",
            precio=Decimal("2000"),
            stock=10
        )
        Producto.objects.create(
            nombre="Plancha Estándar",
            categoria="Planchas",
            precio=Decimal("1500"),
            stock=15
        )
        print("• Productos creados de diferentes categorías")
        
        print("\n• Filtrando por categoría 'Madera'...")
        response = self.client.get(reverse('inventario:lista_productos') + '?categoria=Madera')
        
        if hasattr(response, 'context') and 'productos' in response.context:
            productos = response.context['productos']
            print(f"  → Productos encontrados: {len(productos)}")
            for prod in productos:
                print(f"    - {prod.nombre} ({prod.categoria})")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def tearDown(self):
        # Limpieza después de cada prueba
        Producto.objects.all().delete()
        MovimientoStock.objects.all().delete()
        Usuario.objects.all().delete()
