from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def pagina_inicio(request):
    if request.user.is_authenticated:
        return redirect('inventario:base')
    return redirect('usuario:login')  # Cambiado para usar el namespace

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', pagina_inicio, name='pagina_inicio'),
    path('inventario/', include('inventario.urls', namespace='inventario')),
    path('usuario/', include('usuario.urls', namespace='usuario')),
    path('ventas/', include('ventas.urls', namespace='ventas')),
    path('compras/', include('compras.urls', namespace='compras')),
    path('logger/', include('logger.urls')),
    path('reportes/', include('reportes.urls')),
]