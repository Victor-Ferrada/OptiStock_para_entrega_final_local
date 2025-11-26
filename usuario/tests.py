from django.test import TestCase
from django.urls import reverse
from usuario.models import Usuario
#pruebas de login, se prueba el login con credenciales correctas, 
# con contraseña incorrecta, con rut incorrecto, con campos vacíos y la carga de la página de login
class LoginTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_message_shown = False
#setUp se ejecuta antes de cada test y crea un usuario de prueba
    def setUp(self):
        if not self.__class__._setup_message_shown:
            print("\n" + "="*65)
            print("="*65)
            print("="*16 + "  TEST DE LOGIN  " + "="*33)
            print("="*65)
            print("="*65)
            self.credentials = {
                'RutUsuua': '12345678-9',
                'password': 'contraseña123',
                'Nombre': 'Test',
                'ApePa': 'Usuario',
                'Telefono': '123456789'
            }
            usuario = Usuario.objects.create_user(**self.credentials)
            print("✓ Usuario de prueba creado exitosamente")
            print(f"  → RUT: {usuario.RutUsuua}")
            print(f"  → Nombre: {usuario.Nombre} {usuario.ApePa}")
            print("-"*50)
            self.__class__._setup_message_shown = True
        else:
            # Si ya se mostró el mensaje, solo crear el usuario
            self.credentials = {
                'RutUsuua': '12345678-9',
                'password': 'contraseña123',
                'Nombre': 'Test',
                'ApePa': 'Usuario',
                'Telefono': '123456789'
            }
            Usuario.objects.create_user(**self.credentials)
#test_login_valido prueba el login con credenciales correctas
    def test_login_valido(self):
        print("\n" + "="*50)
        print("TEST: LOGIN VÁLIDO")
        print("="*50)
        print("• Intentando login con credenciales correctas...")
        response = self.client.post(reverse('usuario:login'), {
            'RutUsuua': '12345678-9',
            'password': 'contraseña123'
        })
        self.assertRedirects(response, reverse('inventario:base'))
        print("✓ Login exitoso - Usuario redirigido correctamente")
#test_login_invalido_password prueba el login con contraseña incorrecta
    def test_login_invalido_password(self):
        print("\n" + "="*50)
        print("TEST: LOGIN CON CONTRASEÑA INCORRECTA")
        print("="*50)
        print("• Intentando login con contraseña inválida...")
        response = self.client.post(reverse('usuario:login'), {
            'RutUsuua': '12345678-9',
            'password': 'contraseñaincorrecta'
        })
        self.assertContains(response, 'RUT o contraseña inválidos')
        print("✓ Error detectado correctamente - Acceso denegado")
#test_login_invalido_rut prueba el login con rut incorrecto
    def test_login_invalido_rut(self):
        print("\n" + "="*50)
        print("TEST: LOGIN CON RUT INCORRECTO")
        print("="*50)
        print("• Intentando login con RUT inválido...")
        response = self.client.post(reverse('usuario:login'), {
            'RutUsuua': '98765432-1',
            'password': 'contraseña123'
        })
        self.assertContains(response, 'RUT o contraseña inválidos')
        print("✓ Error detectado correctamente - Usuario no encontrado")
#test_campos_vacios prueba el login con campos vacíos
    def test_campos_vacios(self):
        print("\n" + "="*50)
        print("TEST: LOGIN CON CAMPOS VACÍOS")
        print("="*50)
        print("• Intentando login sin datos...")
        response = self.client.post(reverse('usuario:login'), {})
        self.assertEqual(response.status_code, 200)
        print("✓ Formulario vacío manejado correctamente")
#test_acceso_pagina_login prueba la carga de la página de login
    def test_acceso_pagina_login(self):
        print("\n" + "="*50)
        print("TEST: CARGA DE PÁGINA DE LOGIN")
        print("="*50)
        print("• Verificando acceso a la página de login...")
        response = self.client.get(reverse('usuario:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'usuario/login.html')
        print("✓ Página de login carga correctamente")
#tearDown se ejecuta después de cada test y elimina el usuario de prueba
    def tearDown(self):
        # Limpieza después de cada prueba
        Usuario.objects.all().delete()