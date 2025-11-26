from django.contrib import admin
from .models import Mantenimiento

@admin.register(Mantenimiento)
class MantenimientoAdmin(admin.ModelAdmin):
    list_display = ['tipo', 'modulo_afectado', 'fecha', 'estado']
    list_filter = ['tipo', 'estado', 'fecha']
    search_fields = ['descripcion', 'modulo_afectado']
    readonly_fields = ['fecha']
    
    fieldsets = (
        ('Información General', {
            'fields': ('tipo', 'modulo_afectado', 'estado')
        }),
        ('Detalles', {
            'fields': ('descripcion', 'acciones_realizadas')
        }),
        ('Información Temporal', {
            'fields': ('fecha',),
            'classes': ('collapse',)
        })
    )

    actions = ['marcar_como_completado', 'marcar_en_proceso']

    def marcar_como_completado(self, request, queryset):
        queryset.update(estado='COMPLETADO')
    marcar_como_completado.short_description = "Marcar como completados"

    def marcar_en_proceso(self, request, queryset):
        queryset.update(estado='EN_PROCESO')
    marcar_en_proceso.short_description = "Marcar como en proceso"