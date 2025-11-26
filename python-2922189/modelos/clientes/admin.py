from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'nit', 'telefono', 'correo']
    search_fields = ['nombre', 'nit', 'correo']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información del Cliente', {
            'fields': ('nombre', 'nit')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'correo')
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        # Si está editando (obj existe), hacer el NIT readonly
        if obj:
            return ['nit']
        return []
