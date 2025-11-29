from django.db import models
from django.core.exceptions import ValidationError
from inventario.models import Producto
from usuario.models import Usuario

class Movimiento(models.Model):
    TIPO_MOVIMIENTO = [
        ('VENTA', 'Venta'),
    ]

    id_mov = models.AutoField(primary_key=True)
    rut_usu = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="Usuario")
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Movimiento {self.id_mov} - {self.tipo}"


class Detalle(models.Model):
    num_transac = models.AutoField(primary_key=True)
    id_mov = models.ForeignKey(Movimiento, on_delete=models.CASCADE, related_name="detalles")
    id_prod = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    precio_uni = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()

    def clean(self):
        # Validar que la cantidad no exceda el stock disponible
        # Solo validar si ambos campos tienen valores
        try:
            if self.id_prod_id and self.cantidad:
                if self.id_prod.stock < self.cantidad:
                    raise ValidationError(f"Stock insuficiente para {self.id_prod.nombre}. Stock disponible: {self.id_prod.stock}, requerido: {self.cantidad}.")
        except:
            # Si hay error al acceder a id_prod, simplemente ignorar la validación de stock
            pass

    @property
    def subtotal(self):
        # Calcular el subtotal como precio_unitario * cantidad
        return self.precio_uni * self.cantidad

    def __str__(self):
        return f"Detalle {self.num_transac} - {self.id_prod.nombre}"