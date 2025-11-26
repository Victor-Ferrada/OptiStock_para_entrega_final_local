from django.db import models
from inventario.models import Producto
from usuario.models import Usuario

class Compra(models.Model):
    id_compra = models.AutoField(primary_key=True)
    rut_usu = models.ForeignKey(Usuario, on_delete=models.CASCADE, verbose_name="Usuario")
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    proveedor = models.CharField(max_length=100)

    def __str__(self):
        return f"Compra {self.id_compra} - {self.fecha}"

class DetalleCompra(models.Model):
    num_transac = models.AutoField(primary_key=True)
    id_compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name="detalles")
    id_prod = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    precio_uni = models.DecimalField(max_digits=10, decimal_places=2)
    cantidad = models.PositiveIntegerField()

    @property
    def subtotal(self):
        return self.precio_uni * self.cantidad

    def __str__(self):
        return f"Detalle {self.num_transac} - {self.id_prod.nombre}"