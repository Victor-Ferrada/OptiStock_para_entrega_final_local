from django.shortcuts import render
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from .models import SystemMessage

# Create your views here.

def get_logs(request):
    # Obtener logs de las últimas 24 horas
    recent_logs = SystemMessage.objects.filter(
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-timestamp')[:50]  # Limitamos a los últimos 50 registros
    
    logs = []
    for log in recent_logs:
        logs.append({
            'message': log.message,
            'timestamp': log.timestamp.strftime('%d/%m/%Y %H:%M:%S'),
            'level': log.level,
            'app': log.app
        })
    
    return JsonResponse({'logs': logs})
