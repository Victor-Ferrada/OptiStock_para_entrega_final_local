from functools import wraps
from .models import SystemMessage

def log_action(app_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            try:
                response = view_func(request, *args, **kwargs)
                
                # Capturar la acción realizada
                action_message = f"Acción realizada en {app_name}: {request.method} {request.path}"
                SystemMessage.objects.create(
                    message=action_message,
                    level='info',
                    app=app_name,
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                return response
                
            except Exception as e:
                # Registrar errores
                error_message = f"Error en {app_name}: {str(e)}"
                SystemMessage.objects.create(
                    message=error_message,
                    level='error',
                    app=app_name,
                    user=request.user if request.user.is_authenticated else None,
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                raise
                
        return wrapper
    return decorator