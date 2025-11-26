from django.contrib import messages
from .models import SystemMessage

class SystemMessageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # Capturar mensajes de Django
        storage = messages.get_messages(request)
        for message in storage:
            level = message.tags if message.tags else 'info'
            SystemMessage.objects.create(
                message=str(message),
                level=level
            )
        
        return response

    def process_exception(self, request, exception):
        # Capturar excepciones no manejadas
        SystemMessage.objects.create(
            message=str(exception),
            level='error'
        )
        return None