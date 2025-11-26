from django.contrib import admin
from .models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ['documento', 'nombres', 'apellidos', 'correo', 'rol', 'estado']
    list_filter = ['rol', 'estado']
    search_fields = ['nombres', 'apellidos', 'correo', 'documento']
    ordering = ['nombres', 'apellidos']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('documento', 'nombres', 'apellidos', 'telefono', 'direccion', 'correo')
        }),
        ('Acceso al Sistema', {
            'fields': ('rol', 'password', 'estado')
        }),
    )
