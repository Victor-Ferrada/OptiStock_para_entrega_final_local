from django import forms
from .models import Movimiento, Producto
from django import forms
from .models import Detalle
from inventario.models import Producto

class MovimientoForm(forms.ModelForm):
    class Meta:
        model = Movimiento
        fields = ['tipo', 'rut_usu']  # Ajusta los campos según tu modelo

class ProductoCantidadForm(forms.Form):
    producto = forms.ModelChoiceField(queryset=Producto.objects.all(), label="Producto")
    cantidad = forms.IntegerField(min_value=1, label="Cantidad")

class DetalleForm(forms.ModelForm):
    class Meta:
        model = Detalle
        fields = ['id_prod', 'cantidad']
        widgets = {
            'id_prod': forms.Select(attrs={'class': 'form-control'}),
            'cantidad': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
        }
    
    def __init__(self, *args, queryset=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Hacer los campos opcionales para permitir filas vacías
        self.fields['id_prod'].required = False
        self.fields['cantidad'].required = False
        
        # Si se proporciona un queryset personalizado, usarlo
        if queryset is not None:
            self.fields['id_prod'].queryset = queryset
    
    def clean(self):
        cleaned_data = super().clean()
        id_prod = cleaned_data.get('id_prod')
        cantidad = cleaned_data.get('cantidad')
        
        # Si ambos están vacíos, es una fila vacía que se ignorará
        if not id_prod and not cantidad:
            return cleaned_data
        
        # Si uno está lleno pero el otro no, mostrar error
        if (id_prod and not cantidad) or (not id_prod and cantidad):
            raise forms.ValidationError("Debe completar tanto el producto como la cantidad.")
        
        return cleaned_data