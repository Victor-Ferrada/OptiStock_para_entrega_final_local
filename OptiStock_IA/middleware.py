from django.shortcuts import redirect
from django.contrib import messages

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # URLs que no requieren autenticación
        public_urls = [
            '/usuario/login/',
            '/static/',
            '/media/',
            '/admin/login/',
            '/admin/'
        ]
        
        # Verificar si la URL actual está en las URLs públicas
        is_public_url = any(request.path.startswith(url) for url in public_urls)
        
        if not request.user.is_authenticated and not is_public_url:
            messages.error(request, 'Es necesario iniciar sesión para acceder a esta página.')
            return redirect('usuario:login')
            
        response = self.get_response(request)
        return response