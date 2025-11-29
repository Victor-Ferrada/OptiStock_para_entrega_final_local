from django import forms
from .models import Compra, DetalleCompra

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor']
        widgets = {
            'proveedor': forms.TextInput(attrs={'class': 'form-control', 'id': 'proveedorInput'}),
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
    
    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer los campos opcionales para permitir filas vacías
        self.fields['id_prod'].required = False
        self.fields['cantidad'].required = False
        self.fields['precio_uni'].required = False
        
        # Si se proporciona un queryset personalizado, usarlo
        if queryset is not None:
            self.fields['id_prod'].queryset = queryset
    
    def clean(self):
        cleaned_data = super().clean()
        id_prod = cleaned_data.get('id_prod')
        cantidad = cleaned_data.get('cantidad')
        precio_uni = cleaned_data.get('precio_uni')
        
        # Si todos están vacíos, es una fila vacía que se ignorará
        if not id_prod and not cantidad and not precio_uni:
            return cleaned_data
        
        # Si alguno está lleno pero no todos, mostrar error
        if (id_prod or cantidad or precio_uni) and not (id_prod and cantidad and precio_uni):
            raise forms.ValidationError("Debe completar producto, cantidad y precio unitario.")
        
        return cleaned_data