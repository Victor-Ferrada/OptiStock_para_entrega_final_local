from django.urls import path
from . import views

app_name = 'logger'

urlpatterns = [
    path('get-logs/', views.get_logs, name='get_logs'),
] 