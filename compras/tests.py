from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from .models import Compra, DetalleCompra
from inventario.models import Producto
from usuario.models import Usuario
#esto hace pruebas de la creación de compras, la vista de detalle de una compra, 
# la vista de lista de compras y la validación de datos de compra
class CompraTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False
        cls._auth_message_shown = False
#método que retorna una descripción amigable del código de estado HTTP
    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            302: "Found - Redirección temporal (la compra se creó y redirige a otra página)",
            400: "Bad Request - La solicitud contiene errores",
            404: "Not Found - Recurso no encontrado",
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")
#setUpClass se ejecuta una vez antes de todos los tests y muestra un mensaje de configuración inicial
    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*14 + "  TEST DE COMPRAS  " + "="*33)
            print("="*65)
            print("="*65)
            # Crear usuario de prueba
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Prueba",
                ApePa="Apellido Prueba",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            print("✓ Usuario de prueba creado exitosamente")
            print(f"  → RUT: {self.usuario.RutUsuua}")
            print(f"  → Nombre: {self.usuario.Nombre} {self.usuario.ApePa}")
            # Crear producto de prueba
            self.producto = Producto.objects.create(
                nombre="Producto Prueba",
                categoria="Madera",
                precio=Decimal("1000"),
                stock=10
            )
            print("\n✓ Producto de prueba creado exitosamente")
            print(f"  → Nombre: {self.producto.nombre}")
            print(f"  → Precio: ${self.producto.precio}")
            print(f"  → Stock inicial: {self.producto.stock}")
            # Iniciar sesión
            self.client = Client()
            login_success = self.client.login(username=self.usuario.RutUsuua, password="testpass123")
            print("\n✓ Inicio de sesión:", "Exitoso" if login_success else "Fallido")
            print("-"*50)
            self.__class__._setup_message_shown = True
        else:
            # Si ya se mostró el mensaje, solo crear las instancias sin mostrar mensajes
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Prueba",
                ApePa="Apellido Prueba",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            self.producto = Producto.objects.create(
                nombre="Producto Prueba",
                categoria="Madera",
                precio=Decimal("1000"),
                stock=10
            )
            self.client = Client()
            self.client.login(username=self.usuario.RutUsuua, password="testpass123")
#test_crear_compra_exitosa prueba la creación de una compra exitosa
    def test_crear_compra_exitosa(self):
        print("\n" + "="*50)
        print("TEST: CREACIÓN DE COMPRA EXITOSA")
        print("="*50)
        print("• Preparando datos de la compra...")
        datos_compra = {
            'rut_usu': self.usuario.id,
            'proveedor': 'Proveedor Test',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id_prod': self.producto.id,
            'form-0-cantidad': 5,
            'form-0-precio_uni': '1500'
        }
        stock_inicial = self.producto.stock
        print(f"• Stock inicial del producto: {stock_inicial}")
        response = self.client.post(reverse('compras:registrar_compra'), datos_compra)
        print(f"• Status: {self.get_status_description(response.status_code)}")
        self.producto.refresh_from_db()
        print(f"• Stock final del producto: {self.producto.stock}")
        if Compra.objects.exists():
            compra = Compra.objects.first()
            print("\n✓ Compra creada exitosamente")
            print(f"  → ID de la compra: {compra.id_compra}")
            print(f"  → Total: ${compra.total}")
            print(f"  → Proveedor: {compra.proveedor}")
            # Verificaciones
            self.assertEqual(response.status_code, 302)
            self.assertEqual(self.producto.stock, stock_inicial + 5)
            self.assertEqual(compra.total, Decimal('7500'))
        else:
            self.fail("La compra no fue creada")
#test_detalle_compra prueba la vista de detalle de una compra
    def test_detalle_compra(self):
        print("\n" + "="*50)
        print("TEST: VISTA DE DETALLE DE COMPRA")
        print("="*50)
        # Crear una compra de prueba
        compra = Compra.objects.create(
            rut_usu=self.usuario,
            proveedor="Proveedor Test",
            total=Decimal("7500")
        )
        # Crear detalle de compra
        DetalleCompra.objects.create(
            id_compra=compra,
            id_prod=self.producto,
            precio_uni=Decimal("1500"),
            cantidad=5
        )
        print("• Accediendo a la vista de detalle...")
        response = self.client.get(reverse('compras:detalle_compra', args=[compra.id_compra]))
        print("\n✓ Verificaciones:")
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print(f"  → Template usado: {response.templates[0].name if response.templates else 'No template'}")
        print(f"  → Contiene nombre del producto: {self.producto.nombre in str(response.content)}")
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compras/detalle_compra.html')
        self.assertContains(response, self.producto.nombre)
#test_lista_compras prueba la vista de lista de compras
    def test_lista_compras(self):
        print("\n" + "="*50)
        print("TEST: VISTA DE LISTA DE COMPRAS")
        print("="*50)
        # Crear algunas compras de prueba
        compras_creadas = []
        for i in range(3):
            compra = Compra.objects.create(
                rut_usu=self.usuario,
                proveedor=f"Proveedor Test {i+1}",
                total=Decimal(f"{(i+1)*1000}.00")
            )
            compras_creadas.append(compra)
        print("• Accediendo a la vista de lista de compras...")
        response = self.client.get(reverse('compras:lista_compras'))
        print("\n✓ Verificaciones:")
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print(f"  → Número de compras listadas: {len(response.context['compras'])}")
        print(f"  → Template usado: {response.templates[0].name if response.templates else 'No template'}")
        # Verificaciones
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'compras/lista_compras.html')
        self.assertEqual(len(response.context['compras']), 3)
#test_validacion_compra prueba la validación de datos de compra
    def test_validacion_compra(self):
        print("\n" + "="*50)
        print("TEST: VALIDACIÓN DE DATOS DE COMPRA")
        print("="*50)
        # Intentar crear una compra sin productos
        datos_compra = {
            'rut_usu': self.usuario.id,
            'proveedor': 'Proveedor Test',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id_prod': '',
            'form-0-cantidad': '',
            'form-0-precio_uni': ''
        }
        print("• Intentando crear compra sin productos...")
        response = self.client.post(reverse('compras:registrar_compra'), datos_compra)
        print("\n✓ Verificaciones:")
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print("  → ¿Se evitó la creación de la compra?: {}", not Compra.objects.exists())
        # Verificaciones
        self.assertEqual(response.status_code, 200)  # Debería volver al formulario
        self.assertFalse(Compra.objects.exists())  # No debería crear la compra
#tearDownClass se ejecuta una vez después de todos los tests y muestra un mensaje de limpieza final
    def tearDown(self):
        # Limpieza después de cada prueba
        Compra.objects.all().delete()
        DetalleCompra.objects.all().delete()
        Producto.objects.all().delete()
        Usuario.objects.all().delete()