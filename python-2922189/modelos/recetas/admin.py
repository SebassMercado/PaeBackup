from django.contrib import admin
from django.utils.html import format_html
from .models import Receta, RecetaInsumo


class RecetaInsumoInline(admin.TabularInline):
    """Inline para gestionar ingredientes desde la receta"""
    model = RecetaInsumo
    extra = 1
    fields = ['insumo', 'cantidad', 'unidad', 'estado']
    readonly_fields = []
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('insumo')


@admin.register(Receta)
class RecetaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre',
        'descripcion_corta',
        'precio_display',
        'estado_display',
        'costo_display',
        'margen_display',
        'ingredientes_count'
    ]
    list_filter = ['estado']
    search_fields = ['nombre', 'descripcion']
    ordering = ['nombre']
    inlines = [RecetaInsumoInline]
    
    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Precio y Estado', {
            'fields': ('precio', 'estado')
        }),
        ('Información Calculada', {
            'fields': ('costo_readonly', 'margen_readonly'),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['costo_readonly', 'margen_readonly']
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('ingredientes__insumo')
    
    def descripcion_corta(self, obj):
        """Muestra una descripción recortada"""
        if obj.descripcion:
            return obj.descripcion[:50] + "..." if len(obj.descripcion) > 50 else obj.descripcion
        return "Sin descripción"
    descripcion_corta.short_description = 'Descripción'
    
    def precio_display(self, obj):
        """Muestra el precio formateado"""
        return format_html(
            '<span style="color: green; font-weight: bold;">{}</span>',
            obj.precio_formateado
        )
    precio_display.short_description = 'Precio'
    
    def estado_display(self, obj):
        """Muestra el estado con color"""
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.status_color,
            obj.estado
        )
    estado_display.short_description = 'Estado'
    
    def costo_display(self, obj):
        """Muestra el costo de producción"""
        costo = obj.costo_produccion
        return format_html(
            '<span style="color: orange; font-weight: bold;">${:.2f}</span>',
            costo
        )
    costo_display.short_description = 'Costo'
    
    def margen_display(self, obj):
        """Muestra el margen de ganancia"""
        margen = obj.margen_ganancia
        color = 'green' if margen > 30 else 'orange' if margen > 10 else 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            margen
        )
    margen_display.short_description = 'Margen'
    
    def ingredientes_count(self, obj):
        """Muestra la cantidad de ingredientes"""
        count = obj.ingredientes.count()
        return format_html(
            '<span style="color: blue;">{} ingrediente{}</span>',
            count,
            's' if count != 1 else ''
        )
    ingredientes_count.short_description = 'Ingredientes'
    
    def costo_readonly(self, obj):
        """Campo de solo lectura para mostrar costo"""
        return f"${obj.costo_produccion:.2f}"
    costo_readonly.short_description = 'Costo de Producción'
    
    def margen_readonly(self, obj):
        """Campo de solo lectura para mostrar margen"""
        return f"{obj.margen_ganancia:.1f}%"
    margen_readonly.short_description = 'Margen de Ganancia'
    
    actions = ['activar_recetas', 'desactivar_recetas', 'calcular_costos']
    
    def activar_recetas(self, request, queryset):
        """Acción para activar recetas seleccionadas"""
        updated = queryset.update(estado='Activo')
        self.message_user(
            request,
            f'{updated} receta(s) fueron activadas exitosamente.'
        )
    activar_recetas.short_description = "Activar recetas seleccionadas"
    
    def desactivar_recetas(self, request, queryset):
        """Acción para desactivar recetas seleccionadas"""
        updated = queryset.update(estado='Inactivo')
        self.message_user(
            request,
            f'{updated} receta(s) fueron desactivadas exitosamente.'
        )
    desactivar_recetas.short_description = "Desactivar recetas seleccionadas"
    
    def calcular_costos(self, request, queryset):
        """Acción para recalcular costos de las recetas"""
        count = 0
        for receta in queryset:
            # El costo se calcula automáticamente en la propiedad
            costo = receta.costo_produccion
            count += 1
        
        self.message_user(
            request,
            f'Costos recalculados para {count} receta(s).'
        )
    calcular_costos.short_description = "Recalcular costos"


@admin.register(RecetaInsumo)
class RecetaInsumoAdmin(admin.ModelAdmin):
    list_display = [
        'receta',
        'insumo',
        'cantidad_formateada',
        'costo_display',
        'disponible_display',
        'estado_display'
    ]
    list_filter = ['estado', 'unidad', 'receta__estado']
    search_fields = ['receta__nombre', 'insumo__nombre']
    ordering = ['receta__nombre', 'insumo__nombre']
    
    fieldsets = (
        ('Relación', {
            'fields': ('receta', 'insumo')
        }),
        ('Cantidad y Medida', {
            'fields': ('cantidad', 'unidad')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('receta', 'insumo')
    
    def costo_display(self, obj):
        """Muestra el costo del ingrediente"""
        return format_html(
            '<span style="color: orange;">${:.2f}</span>',
            obj.costo_ingrediente
        )
    costo_display.short_description = 'Costo'
    
    def disponible_display(self, obj):
        """Muestra si el ingrediente está disponible"""
        if obj.disponible:
            return format_html(
                '<span style="color: green;">✓ Disponible</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Insuficiente</span>'
            )
    disponible_display.short_description = 'Disponibilidad'
    
    def estado_display(self, obj):
        """Muestra el estado con color"""
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.estado_color,
            obj.estado
        )
    estado_display.short_description = 'Estado'
    
    actions = ['verificar_disponibilidad', 'activar_ingredientes']
    
    def verificar_disponibilidad(self, request, queryset):
        """Verifica y actualiza la disponibilidad de los ingredientes"""
        count = 0
        for ingrediente in queryset:
            ingrediente.verificar_disponibilidad()
            ingrediente.save()
            count += 1
        
        self.message_user(
            request,
            f'Disponibilidad verificada para {count} ingrediente(s).'
        )
    verificar_disponibilidad.short_description = "Verificar disponibilidad"
    
    def activar_ingredientes(self, request, queryset):
        """Activa ingredientes seleccionados"""
        updated = queryset.update(estado='Activo')
        self.message_user(
            request,
            f'{updated} ingrediente(s) fueron activados.'
        )
    activar_ingredientes.short_description = "Activar ingredientes"
