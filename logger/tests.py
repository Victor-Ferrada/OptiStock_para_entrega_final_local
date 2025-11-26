from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from .models import SystemMessage
from usuario.models import Usuario
import json

# Tests para el módulo logger: registro de mensajes del sistema, 
# captura de errores, niveles de severidad y filtrado de logs
class LoggerTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False

    def get_status_description(self, status_code):
        """Retorna una descripción amigable del código de estado HTTP"""
        status_descriptions = {
            200: "OK - La solicitud se completó exitosamente",
            400: "Bad Request - La solicitud contiene errores",
            404: "Not Found - Recurso no encontrado",
            500: "Internal Server Error - Error interno del servidor",
        }
        return status_descriptions.get(status_code, f"Código {status_code} - No documentado")

    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*16 + "  TEST DE LOGGER  " + "="*32)
            print("="*65)
            print("="*65)
            # Crear usuario de prueba
            self.usuario = Usuario.objects.create(
                RutUsuua="12345678-9",
                Nombre="Usuario Logger",
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
                Nombre="Usuario Logger",
                ApePa="Test",
                Telefono="123456789"
            )
            self.usuario.set_password("testpass123")
            self.usuario.save()
            self.client = Client()
            self.client.login(username=self.usuario.RutUsuua, password="testpass123")

    def test_crear_mensaje_success(self):
        print("\n" + "="*50)
        print("TEST: CREAR MENSAJE DE ÉXITO")
        print("="*50)
        print("• Creando mensaje de éxito...")
        mensaje = SystemMessage.objects.create(
            message="Operación completada exitosamente",
            level='success',
            app='inventario',
            user=self.usuario
        )
        print("\n✓ Mensaje creado:")
        print(f"  → ID: {mensaje.id}")
        print(f"  → Mensaje: {mensaje.message}")
        print(f"  → Nivel: {mensaje.level}")
        print(f"  → Aplicación: {mensaje.app}")
        print(f"  → Usuario: {mensaje.user.Nombre}")
        print(f"  → Visto: {mensaje.viewed}")
        
        self.assertEqual(mensaje.message, "Operación completada exitosamente")
        self.assertEqual(mensaje.level, 'success')
        self.assertEqual(mensaje.app, 'inventario')
        self.assertFalse(mensaje.viewed)
        print("-"*50)

    def test_crear_mensaje_error(self):
        print("\n" + "="*50)
        print("TEST: CREAR MENSAJE DE ERROR")
        print("="*50)
        print("• Creando mensaje de error...")
        mensaje = SystemMessage.objects.create(
            message="Error al procesar la solicitud",
            level='error',
            app='ventas'
        )
        print("\n✓ Mensaje de error creado:")
        print(f"  → Mensaje: {mensaje.message}")
        print(f"  → Nivel: {mensaje.level}")
        print(f"  → Aplicación: {mensaje.app}")
        
        self.assertEqual(mensaje.level, 'error')
        self.assertEqual(mensaje.app, 'ventas')
        print("-"*50)

    def test_crear_mensaje_warning(self):
        print("\n" + "="*50)
        print("TEST: CREAR MENSAJE DE ADVERTENCIA")
        print("="*50)
        print("• Creando mensaje de advertencia...")
        mensaje = SystemMessage.objects.create(
            message="Stock bajo para el producto X",
            level='warning',
            app='inventario'
        )
        print("\n✓ Mensaje de advertencia creado:")
        print(f"  → Mensaje: {mensaje.message}")
        print(f"  → Nivel: {mensaje.level}")
        
        self.assertEqual(mensaje.level, 'warning')
        print("-"*50)

    def test_crear_mensaje_info(self):
        print("\n" + "="*50)
        print("TEST: CREAR MENSAJE DE INFORMACIÓN")
        print("="*50)
        print("• Creando mensaje de información...")
        mensaje = SystemMessage.objects.create(
            message="Información sobre la operación",
            level='info',
            app='sistema'
        )
        print("\n✓ Mensaje de información creado:")
        print(f"  → Mensaje: {mensaje.message}")
        print(f"  → Nivel: {mensaje.level}")
        
        self.assertEqual(mensaje.level, 'info')
        print("-"*50)

    def test_mensaje_con_ip_address(self):
        print("\n" + "="*50)
        print("TEST: CREAR MENSAJE CON DIRECCIÓN IP")
        print("="*50)
        print("• Creando mensaje con IP address...")
        mensaje = SystemMessage.objects.create(
            message="Acceso desde IP registrada",
            level='info',
            app='usuario',
            ip_address='192.168.1.100'
        )
        print("\n✓ Mensaje creado:")
        print(f"  → Mensaje: {mensaje.message}")
        print(f"  → IP Address: {mensaje.ip_address}")
        
        self.assertEqual(mensaje.ip_address, '192.168.1.100')
        print("-"*50)

    def test_marcar_mensaje_como_visto(self):
        print("\n" + "="*50)
        print("TEST: MARCAR MENSAJE COMO VISTO")
        print("="*50)
        print("• Creando mensaje...")
        mensaje = SystemMessage.objects.create(
            message="Mensaje a marcar como visto",
            level='info',
            app='sistema'
        )
        print(f"  → Mensaje visto inicialmente: {mensaje.viewed}")
        
        print("\n• Marcando como visto...")
        mensaje.viewed = True
        mensaje.save()
        
        print(f"  → Mensaje visto ahora: {mensaje.viewed}")
        self.assertTrue(mensaje.viewed)
        print("-"*50)

    def test_timestamp_automatico(self):
        print("\n" + "="*50)
        print("TEST: TIMESTAMP AUTOMÁTICO")
        print("="*50)
        print("• Creando mensaje...")
        ahora_antes = timezone.now()
        mensaje = SystemMessage.objects.create(
            message="Mensaje con timestamp",
            level='info'
        )
        ahora_despues = timezone.now()
        
        print("\n✓ Timestamp verificado:")
        print(f"  → Hora antes: {ahora_antes}")
        print(f"  → Timestamp del mensaje: {mensaje.timestamp}")
        print(f"  → Hora después: {ahora_despues}")
        print(f"  → ¿Timestamp válido?: {ahora_antes <= mensaje.timestamp <= ahora_despues}")
        
        self.assertGreaterEqual(mensaje.timestamp, ahora_antes)
        self.assertLessEqual(mensaje.timestamp, ahora_despues)
        print("-"*50)

    def test_filtrar_por_nivel(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR MENSAJES POR NIVEL")
        print("="*50)
        print("• Creando mensajes de diferentes niveles...")
        SystemMessage.objects.create(message="Error 1", level='error')
        SystemMessage.objects.create(message="Error 2", level='error')
        SystemMessage.objects.create(message="Éxito 1", level='success')
        SystemMessage.objects.create(message="Advertencia 1", level='warning')
        
        print("\n• Filtrando por nivel 'error'...")
        errores = SystemMessage.objects.filter(level='error')
        print(f"  → Errores encontrados: {errores.count()}")
        
        self.assertEqual(errores.count(), 2)
        print("-"*50)

    def test_filtrar_por_aplicacion(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR MENSAJES POR APLICACIÓN")
        print("="*50)
        print("• Creando mensajes de diferentes aplicaciones...")
        SystemMessage.objects.create(message="Msg Inventario 1", app='inventario')
        SystemMessage.objects.create(message="Msg Inventario 2", app='inventario')
        SystemMessage.objects.create(message="Msg Ventas 1", app='ventas')
        
        print("\n• Filtrando por aplicación 'inventario'...")
        inventario_msgs = SystemMessage.objects.filter(app='inventario')
        print(f"  → Mensajes de inventario: {inventario_msgs.count()}")
        
        self.assertEqual(inventario_msgs.count(), 2)
        print("-"*50)

    def test_filtrar_logs_ultimas_24_horas(self):
        print("\n" + "="*50)
        print("TEST: FILTRAR LOGS DE LAS ÚLTIMAS 24 HORAS")
        print("="*50)
        print("• Creando mensajes con diferentes timestamps...")
        
        # Mensaje de hace 12 horas
        hace_12_horas = timezone.now() - timedelta(hours=12)
        msg_reciente = SystemMessage.objects.create(
            message="Mensaje reciente",
            level='info'
        )
        msg_reciente.timestamp = hace_12_horas
        msg_reciente.save()
        
        # Mensaje de hace 25 horas
        hace_25_horas = timezone.now() - timedelta(hours=25)
        msg_antiguo = SystemMessage.objects.create(
            message="Mensaje antiguo",
            level='info'
        )
        msg_antiguo.timestamp = hace_25_horas
        msg_antiguo.save()
        
        print(f"  → Mensaje reciente: {msg_reciente.message} ({msg_reciente.timestamp})")
        print(f"  → Mensaje antiguo: {msg_antiguo.message} ({msg_antiguo.timestamp})")
        
        print("\n• Filtrando últimas 24 horas...")
        hace_24_horas = timezone.now() - timedelta(hours=24)
        logs_recientes = SystemMessage.objects.filter(timestamp__gte=hace_24_horas)
        print(f"  → Logs en últimas 24 horas: {logs_recientes.count()}")
        
        self.assertEqual(logs_recientes.count(), 1)
        print("-"*50)

    def test_ordenamiento_por_timestamp(self):
        print("\n" + "="*50)
        print("TEST: ORDENAMIENTO POR TIMESTAMP (MÁS RECIENTE PRIMERO)")
        print("="*50)
        print("• Creando varios mensajes con timestamps diferentes...")
        
        # Crear mensajes con timestamps diferentes
        msg1 = SystemMessage.objects.create(message="Primer mensaje", level='info')
        msg1.timestamp = timezone.now() - timedelta(hours=3)
        msg1.save()
        
        msg2 = SystemMessage.objects.create(message="Segundo mensaje", level='info')
        msg2.timestamp = timezone.now() - timedelta(hours=2)
        msg2.save()
        
        msg3 = SystemMessage.objects.create(message="Tercer mensaje", level='info')
        msg3.timestamp = timezone.now() - timedelta(hours=1)
        msg3.save()
        
        print("\n• Obteniendo mensajes ordenados (más reciente primero)...")
        mensajes = SystemMessage.objects.all().order_by('-timestamp')
        print(f"  → Primer mensaje en lista: {mensajes[0].message}")
        print(f"  → Último mensaje en lista: {mensajes[mensajes.count()-1].message}")
        
        self.assertEqual(mensajes[0].message, "Tercer mensaje")
        self.assertEqual(mensajes[mensajes.count()-1].message, "Primer mensaje")
        print("-"*50)

    def test_get_logs_view(self):
        print("\n" + "="*50)
        print("TEST: VISTA GET_LOGS")
        print("="*50)
        print("• Creando mensajes de prueba...")
        
        for i in range(3):
            SystemMessage.objects.create(
                message=f"Log de prueba {i+1}",
                level='info',
                app='sistema'
            )
        
        print("\n• Accediendo a la vista get_logs...")
        response = self.client.get(reverse('logger:get_logs'))
        print(f"  → Status: {self.get_status_description(response.status_code)}")
        
        if response.status_code == 200:
            data = json.loads(response.content)
            logs = data.get('logs', [])
            print(f"  → Logs obtenidos: {len(logs)}")
            for log in logs:
                print(f"    - {log['message']} ({log['level']})")
        
        self.assertEqual(response.status_code, 200)
        print("-"*50)

    def test_colored_message(self):
        print("\n" + "="*50)
        print("TEST: MÉTODO COLORED_MESSAGE")
        print("="*50)
        print("• Creando mensaje con nivel 'success'...")
        
        mensaje = SystemMessage.objects.create(
            message="Mensaje coloreado",
            level='success'
        )
        
        colored = mensaje.colored_message()
        colored_str = str(colored)
        print("\n✓ HTML coloreado generado:")
        print(f"  → Contains 'green' color: {'green' in colored_str}")
        print(f"  → Contains 'color' style: {'color' in colored_str}")
        print(f"  → Contains message: {'Mensaje coloreado' in colored_str}")
        
        # Verificar que el color correcto se aplique según el nivel
        self.assertIn('green', colored_str)  # success = green
        self.assertIn('Mensaje coloreado', colored_str)
        print("-"*50)

    def tearDown(self):
        # Limpieza después de cada prueba
        SystemMessage.objects.all().delete()
        Usuario.objects.all().delete()
