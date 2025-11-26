from django.db import models
from django.utils.html import format_html

class SystemMessage(models.Model):
    LEVEL_CHOICES = [
        ('success', 'Éxito'),
        ('error', 'Error'),
        ('warning', 'Advertencia'),
        ('info', 'Información')
    ]

    APP_CHOICES = [
        ('inventario', 'Inventario'),
        ('ventas', 'Ventas'),
        ('compras', 'Compras'),
        ('usuario', 'Usuario'),
        ('sistema', 'Sistema')
    ]

    message = models.TextField(verbose_name="Mensaje")
    level = models.CharField(
        max_length=20, 
        choices=LEVEL_CHOICES, 
        default='info',
        verbose_name="Nivel"
    )
    app = models.CharField(
        max_length=20,
        choices=APP_CHOICES,
        default='sistema',
        verbose_name="Aplicación"
    )
    user = models.ForeignKey(
        'usuario.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario"
    )
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    viewed = models.BooleanField(default=False, verbose_name="Visto")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Mensaje del Sistema"
        verbose_name_plural = "Mensajes del Sistema"
        ordering = ['-timestamp']

    def colored_message(self):
        colors = {
            'success': 'green',
            'error': 'red',
            'warning': 'orange',
            'info': 'blue'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[self.level],
            self.message
        )
    colored_message.short_description = "Mensaje"