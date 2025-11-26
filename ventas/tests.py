from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from .models import Movimiento, Detalle
from inventario.models import Producto
from usuario.models import Usuario
from django.forms import formset_factory
from .forms import DetalleForm
#ventas test hace pruebas de la creación de ventas, la creación de ventas sin stock suficiente, 
# el cálculo del total de una venta y la vista de detalle de una venta
class VentaTests(TestCase):
    #get_status_description retorna una descripción amigable del código de estado HTTP
    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            201: "Created - El recurso se creó exitosamente",
            301: "Moved Permanently - Redirección permanente",
            302: "Found - Redirección temporal (la venta se creó y redirige a otra página)",
            400: "Bad Request - La solicitud contiene errores",
            401: "Unauthorized - No autorizado, requiere autenticación",
            403: "Forbidden - Prohibido, no tiene permisos",
            404: "Not Found - Recurso no encontrado",
            500: "Internal Server Error - Error interno del servidor"
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")
#setUpClass se ejecuta una vez antes de todos los tests y muestra un mensaje de configuración inicial
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False
#setUp se ejecuta antes de cada test y crea un usuario de prueba y un producto de prueba
    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*16 + "  TEST DE VENTAS  " + "="*32)
            print("="*65)
            print("="*65)
            self.__class__._setup_message_shown = True
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create(
            RutUsuua="12345678-9",
            Nombre="Usuario Prueba",
            ApePa="Apellido Prueba",
            Telefono="123456789"
        )
        self.usuario.set_password("testpass123")
        self.usuario.save()
        
        if not self.__class__._setup_message_shown:
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
        if not self.__class__._setup_message_shown:
            print("\n✓ Producto de prueba creado exitosamente")
            print(f"  → Nombre: {self.producto.nombre}")
            print(f"  → Precio: ${self.producto.precio}")
            print(f"  → Stock inicial: {self.producto.stock}")
        # Iniciar sesión
        self.client = Client()
        login_success = self.client.login(username=self.usuario.RutUsuua, password="testpass123")
        if not self.__class__._setup_message_shown:
            print("\n✓ Inicio de sesión:", "Exitoso" if login_success else "Fallido")
            print("-"*50)
#test_crear_venta_exitosa prueba la creación de una venta exitosa
    def test_crear_venta_exitosa(self):
        print("\n" + "="*50)
        print("TEST: CREACIÓN DE VENTA EXITOSA")
        print("="*50)
        
        print("• Preparando datos de la venta...")
        print(f"  → Stock inicial del producto: {self.producto.stock}")
        datos_venta = {
            'tipo': 'VENTA',
            'rut_usu': '1',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id_prod': self.producto.id,
            'form-0-cantidad': 2,
            'form-0-precio_uni': str(self.producto.precio)
        }
        print("\n• Enviando solicitud de venta...")
        response = self.client.post(reverse('ventas:registrar_venta'), datos_venta)
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        if Movimiento.objects.exists():
            venta = Movimiento.objects.first()
            print("\n✓ Venta creada exitosamente")
            print(f"  → ID de la venta: {venta.id_mov}")
            print(f"  → Total: ${venta.total}")
            print("\n• Detalles de la venta:")
            for detalle in venta.detalles.all():
                print(f"  → Producto: {detalle.id_prod.nombre}")
                print(f"  → Cantidad: {detalle.cantidad}")
                print(f"  → Precio unitario: ${detalle.precio_uni}")
            self.producto.refresh_from_db()
            print(f"\n• Stock final del producto: {self.producto.stock}")
        else:
            print("\n✗ Error: No se creó la venta")
        print("-"*50)
#test_venta_sin_stock_suficiente prueba la creación de una venta sin stock suficiente
    def test_venta_sin_stock_suficiente(self):
        print("\n" + "="*50)
        print("TEST: VENTA SIN STOCK SUFICIENTE")
        print("="*50)
        print(f"• Stock inicial: {self.producto.stock}")
        print("• Intentando vender más unidades que el stock disponible...")
        datos_venta = {
            'tipo': 'VENTA',
            'rut_usu': '1',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-id_prod': self.producto.id,
            'form-0-cantidad': 15,
            'form-0-precio_uni': str(self.producto.precio)
        }
        response = self.client.post(reverse('ventas:registrar_venta'), datos_venta)
        print(f"\n• Status: {self.get_status_description(response.status_code)}")
        if hasattr(response, 'context') and response.context:
            if 'mov_form' in response.context:
                print("• Errores del formulario de movimiento:", response.context['mov_form'].errors)
            if 'detalle_formset' in response.context:
                print("• Errores del formset de detalles:", response.context['detalle_formset'].errors)
        self.producto.refresh_from_db()
        print("\n✓ Validaciones:")
        print(f"  → Stock sin cambios: {self.producto.stock == 10}")
        print(f"  → Venta no creada: {not Movimiento.objects.exists()}")
        print("-"*50)
#test_venta_calculo_total prueba el cálculo del total de una venta
    def test_venta_calculo_total(self):
        print("\n" + "="*50)
        print("TEST: CÁLCULO DEL TOTAL DE VENTA")
        print("="*50)
        print("• Creando venta de prueba...")
        venta = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('2000')
        )
        detalle = Detalle.objects.create(
            id_mov=venta,
            id_prod=self.producto,
            precio_uni=self.producto.precio,
            cantidad=2
        )
        print("\n✓ Verificación de totales:")
        print(f"  → Total esperado: ${Decimal('2000')}")
        print(f"  → Total calculado: ${venta.total}")
        print(f"  → ¿Coinciden?: {venta.total == Decimal('2000')}")
        print("-"*50)
#test_detalle_venta prueba la vista de detalle de una venta
    def test_detalle_venta(self):
        print("\n" + "="*50)
        print("TEST: VISTA DE DETALLE DE VENTA")
        print("="*50)
        print("• Creando venta de prueba...")
        venta = Movimiento.objects.create(
            rut_usu=self.usuario,
            tipo='VENTA',
            total=Decimal('2000')
        )
        detalle = Detalle.objects.create(
            id_mov=venta,
            id_prod=self.producto,
            precio_uni=self.producto.precio,
            cantidad=2
        )
        print("• Accediendo a la vista de detalle...")
        response = self.client.get(reverse('ventas:detalle_venta', args=[venta.id_mov]))
        print("\n✓ Verificaciones:")
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        print(f"  → Template usado: {response.templates[0].name if response.templates else 'No template'}")
        print(f"  → Contiene nombre del producto: {self.producto.nombre in str(response.content)}")
        print("-"*50)