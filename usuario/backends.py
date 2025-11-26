from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import Usuario

class RutUsuuaBackend:
    _auth_message_shown = False  # Variable de clase para controlar los mensajes

    def authenticate(self, request, username=None, password=None):
        try:
            if not RutUsuuaBackend._auth_message_shown:
                print("RutUsuuaBackend: Buscando usuario con RutUsuua:", username)
            user = Usuario.objects.get(RutUsuua=username)
            if user.check_password(password):
                if not RutUsuuaBackend._auth_message_shown:
                    print("RutUsuuaBackend: Contraseña correcta")
                    RutUsuuaBackend._auth_message_shown = True
                return user
            return None
        except Usuario.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None