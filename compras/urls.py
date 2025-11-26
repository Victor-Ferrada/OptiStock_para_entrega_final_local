from django.urls import path
from . import views

app_name = 'compras'

urlpatterns = [
    path('registrar/', views.registrar_compra, name='registrar_compra'),
    path('lista/', views.lista_compras, name='lista_compras'),
    path('detalle/<int:id_compra>/', views.detalle_compra, name='detalle_compra'),
] 