from django.db import models

class ConfiguracionReporte(models.Model):
    nombre = models.CharField(max_length=100)
    incluir_ventas = models.BooleanField(default=True)
    incluir_compras = models.BooleanField(default=True)
    incluir_inventario = models.BooleanField(default=True)
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField()
    
    def __str__(self):
        return self.nombre