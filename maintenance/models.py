from django.db import models

class Mantenimiento(models.Model):
    TIPO_CHOICES = [
        ('CORRECTIVO', 'Correctivo'),
        ('PREVENTIVO', 'Preventivo'),
        ('ADAPTATIVO', 'Adaptativo'),
        ('PERFECTIVO', 'Perfectivo')
    ]
    
    tipo = models.CharField(
        max_length=20, 
        choices=TIPO_CHOICES,
        verbose_name="Tipo de mantenimiento"
    )
    descripcion = models.TextField(
        verbose_name="Descripción"
    )
    fecha = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de registro"
    )
    modulo_afectado = models.CharField(
        max_length=100,
        verbose_name="Módulo afectado"
    )
    acciones_realizadas = models.TextField(
        verbose_name="Acciones realizadas"
    )
    estado = models.CharField(
        max_length=20,
        choices=[
            ('PENDIENTE', 'Pendiente'),
            ('EN_PROCESO', 'En Proceso'),
            ('COMPLETADO', 'Completado')
        ],
        default='PENDIENTE',
        verbose_name="Estado"
    )

    class Meta:
        verbose_name = "Mantenimiento"
        verbose_name_plural = "Mantenimientos"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.modulo_afectado} ({self.fecha.strftime('%d/%m/%Y')})"