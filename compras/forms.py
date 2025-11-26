from django import forms
from .models import Compra, DetalleCompra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['rut_usu', 'proveedor']
        widgets = {
            'rut_usu': forms.Select(attrs={'class': 'form-control'}),
            'proveedor': forms.TextInput(attrs={'class': 'form-control'}),
        }

class DetalleCompraForm(forms.ModelForm):
    class Meta:
        model = DetalleCompra
        fields = ['id_prod', 'cantidad', 'precio_uni']
        widgets = {
            'id_prod': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'precio_uni': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
        }