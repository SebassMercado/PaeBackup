from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db import models
from .models import Produccion, ProduccionReceta


@admin.register(Produccion)
class ProduccionAdmin(admin.ModelAdmin):
    """
    Administración del modelo Producción
    """
    
    list_display = [
        'id_proc',
        'receta',
        'cantidad',
        'estado',
        'nombre_completo_creador',
        'nombre_completo_asignado',
        'fecha_hora',
        'tiempo_transcurrido',
    ]
    
    list_filter = [
        'estado',
        'fecha_hora',
        'usuario_asignado',
        'receta',
    ]
    
    search_fields = [
        'id_proc',
        'receta__nombre',
        'usuario_creador__nombres',
        'usuario_creador__apellidos',
        'usuario_asignado__nombres',
        'usuario_asignado__apellidos',
    ]
    
    readonly_fields = [
        'fecha_hora',
        'tiempo_transcurrido',
        'tiempo_produccion',
        'costo_estimado',
        'valor_estimado',
        'ganancia_estimada',
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'receta',
                'cantidad',
                'estado',
            )
        }),
        ('Asignación', {
            'fields': (
                'usuario_creador',
                'usuario_asignado',
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_hora',
                'fecha_aceptacion',
                'fecha_finalizacion',
            )
        }),
        ('Información Calculada', {
            'fields': (
                'tiempo_transcurrido',
                'tiempo_produccion',
                'costo_estimado',
                'valor_estimado',
                'ganancia_estimada',
            ),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-fecha_hora']
    
    # Acciones personalizadas
    actions = ['aceptar_producciones', 'marcar_esperando_insumos', 'finalizar_producciones']
    
    def aceptar_producciones(self, request, queryset):
        """Acepta las producciones seleccionadas"""
        count = 0
        for produccion in queryset:
            try:
                if produccion.puede_aceptar:
                    produccion.aceptar_produccion()
                    produccion.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} producciones aceptadas exitosamente.')
    aceptar_producciones.short_description = "Aceptar producciones seleccionadas"
    
    def marcar_esperando_insumos(self, request, queryset):
        """Marca producciones aceptadas como 'Esperando insumos'"""
        count = 0
        for produccion in queryset:
            try:
                if produccion.estado == 'Aceptada':
                    produccion.marcar_esperando_insumos()
                    produccion.save()
                    count += 1
            except ValueError:
                continue
        self.message_user(request, f"{count} producciones marcadas 'Esperando insumos'.")
    marcar_esperando_insumos.short_description = "Marcar como Esperando insumos"

    def finalizar_producciones(self, request, queryset):
        """Finaliza las producciones seleccionadas"""
        count = 0
        for produccion in queryset:
            try:
                if produccion.puede_finalizar:
                    produccion.finalizar_produccion()
                    produccion.save()
                    count += 1
            except ValueError:
                continue
        self.message_user(request, f'{count} producciones finalizadas exitosamente.')
    finalizar_producciones.short_description = "Finalizar producciones seleccionadas"
    
    # Eliminada acción de cancelar (estado no soportado en enum actual)


class ProduccionRecetaInline(admin.TabularInline):
    """
    Inline para mostrar detalles de recetas dentro de la producción
    """
    model = ProduccionReceta
    extra = 1
    readonly_fields = ['valor_total_display', 'disponibilidad_display', 'tiempo_estimado_display']
    fields = ['receta', 'cantidad', 'valor_total_display', 'disponibilidad_display', 'tiempo_estimado_display']
    
    def valor_total_display(self, obj):
        """Muestra el valor total del detalle"""
        if obj.id:
            return obj.valor_total_formateado
        return "$0"
    valor_total_display.short_description = 'Valor Total'
    
    def disponibilidad_display(self, obj):
        """Muestra la disponibilidad de ingredientes"""
        if obj.id:
            if obj.disponibilidad_ingredientes:
                return format_html('<span style="color: green;">✅ Disponible</span>')
            else:
                faltantes = len(obj.ingredientes_faltantes)
                return format_html(
                    '<span style="color: red;">⚠️ Faltan {} ingredientes</span>',
                    faltantes
                )
        return "N/A"
    disponibilidad_display.short_description = 'Disponibilidad'
    
    def tiempo_estimado_display(self, obj):
        """Muestra el tiempo estimado"""
        if obj.id:
            tiempo = obj.tiempo_estimado_total
            if tiempo > 0:
                return f"{tiempo} min"
        return "N/A"
    tiempo_estimado_display.short_description = 'Tiempo Est.'


@admin.register(ProduccionReceta)
class ProduccionRecetaAdmin(admin.ModelAdmin):
    """
    Administración del modelo ProduccionReceta
    """
    
    list_display = [
        'id_detalle',
        'produccion_link',
        'estado_produccion_display',
        'receta_display',
        'cantidad',
        'valor_total_display',
        'disponibilidad_display',
        'margen_display',
        'empleado_asignado'
    ]
    
    list_filter = [
        'produccion__estado',
        'produccion__fecha_hora',
        'receta__nombre',
        'produccion__usuario_asignado',
    ]
    
    search_fields = [
        'produccion__id_proc',
        'receta__nombre',
        'produccion__usuario_asignado__nombres',
        'produccion__usuario_asignado__apellidos',
    ]
    
    date_hierarchy = 'produccion__fecha_hora'
    ordering = ['-produccion__fecha', 'id_detalle']
    
    readonly_fields = [
        'valor_total_produccion',
        'tiempo_estimado_total',
        'costo_ingredientes_total',
        'margen_ganancia_estimado',
        'porcentaje_orden_produccion',
        'disponibilidad_ingredientes',
        'estado_produccion',
        'fecha_produccion',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'produccion',
                'receta',
                'cantidad',
            )
        }),
        ('Valores Calculados', {
            'fields': (
                'valor_total_produccion',
                'costo_ingredientes_total',
                'margen_ganancia_estimado',
                'porcentaje_orden_produccion',
            ),
            'classes': ('collapse',),
        }),
        ('Tiempos y Disponibilidad', {
            'fields': (
                'tiempo_estimado_total',
                'disponibilidad_ingredientes',
            ),
            'classes': ('collapse',),
        }),
        ('Información de Producción', {
            'fields': (
                'estado_produccion',
                'fecha_produccion',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Métodos para mostrar información formateada
    def produccion_link(self, obj):
        """Link a la orden de producción"""
        if obj.produccion:
                        url = reverse('admin:produccion_produccion_change', args=[obj.produccion.id_proc])
                        return format_html('<a href="{}">{}</a>', url, f"Orden #{obj.produccion.id_proc}")
        return "Sin orden"
    produccion_link.short_description = 'Orden'
    
    def estado_produccion_display(self, obj):
        """Muestra el estado de la producción con color"""
        estado = obj.estado_produccion
        color_map = {'Pendiente': 'orange', 'Aceptada': 'blue', 'Finalizada': 'green', 'Esperando insumos': 'purple'}
        color = color_map.get(estado, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, estado
        )
    estado_produccion_display.short_description = 'Estado'
    
    def receta_display(self, obj):
        """Muestra la receta con disponibilidad"""
        nombre = obj.nombre_receta
        if not obj.disponibilidad_ingredientes:
            return format_html(
                '<span style="color: red;">{} ⚠️</span>',
                nombre
            )
        return nombre
    receta_display.short_description = 'Receta'
    
    def valor_total_display(self, obj):
        """Muestra el valor total"""
        return obj.valor_total_formateado
    valor_total_display.short_description = 'Valor Total'
    
    def disponibilidad_display(self, obj):
        """Muestra la disponibilidad con detalles"""
        if obj.disponibilidad_ingredientes:
            return format_html('<span style="color: green;">✅ Disponible</span>')
        else:
            faltantes = obj.ingredientes_faltantes
            if faltantes:
                primer_faltante = faltantes[0]
                tooltip = f"Falta: {primer_faltante['insumo']} ({primer_faltante['faltante']:.2f} {primer_faltante['unidad']})"
                if len(faltantes) > 1:
                    tooltip += f" y {len(faltantes) - 1} más"
                
                return format_html(
                    '<span style="color: red;" title="{}">⚠️ {} faltantes</span>',
                    tooltip, len(faltantes)
                )
            return format_html('<span style="color: red;">⚠️ Sin info</span>')
    disponibilidad_display.short_description = 'Disponibilidad'
    
    def margen_display(self, obj):
        """Muestra el margen de ganancia"""
        margen = obj.margen_ganancia_estimado
        if margen > 0:
            color = 'green' if margen >= 50 else ('orange' if margen >= 25 else 'red')
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, margen
            )
        return "N/A"
    margen_display.short_description = 'Margen'
    
    # Acciones personalizadas
    actions = [
        'verificar_ingredientes',
        'calcular_tiempos_produccion',
        'generar_reporte_costos',
    ]
    
    def verificar_ingredientes(self, request, queryset):
        """Verifica disponibilidad de ingredientes"""
        disponibles = 0
        no_disponibles = 0
        total_faltantes = 0
        
        for detalle in queryset:
            if detalle.disponibilidad_ingredientes:
                disponibles += 1
            else:
                no_disponibles += 1
                total_faltantes += len(detalle.ingredientes_faltantes)
        
        mensaje = f"Verificación: {disponibles} disponibles, {no_disponibles} con faltantes ({total_faltantes} ingredientes faltantes en total)"
        self.message_user(request, mensaje)
    verificar_ingredientes.short_description = "Verificar disponibilidad de ingredientes"
    
    def calcular_tiempos_produccion(self, request, queryset):
        """Calcula tiempos totales de producción"""
        tiempo_total = sum(detalle.tiempo_estimado_total for detalle in queryset)
        cantidad_productos = sum(detalle.cantidad for detalle in queryset)
        
        mensaje = f"Tiempo estimado total: {tiempo_total} minutos para {cantidad_productos} productos"
        self.message_user(request, mensaje)
    calcular_tiempos_produccion.short_description = "Calcular tiempos de producción"
    
    def generar_reporte_costos(self, request, queryset):
        """Genera reporte de costos y márgenes"""
        valor_total = sum(detalle.valor_total_produccion for detalle in queryset)
        costo_total = sum(detalle.costo_ingredientes_total for detalle in queryset)
        
        if valor_total > 0:
            margen_promedio = ((valor_total - costo_total) / valor_total) * 100
            mensaje = f"Reporte: Valor ${valor_total:,.0f}, Costo ${costo_total:,.0f}, Margen {margen_promedio:.1f}%"
        else:
            mensaje = "No hay datos suficientes para calcular costos"
        
        self.message_user(request, mensaje)
    generar_reporte_costos.short_description = "Generar reporte de costos"
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'produccion',
            'produccion__usuario_asignado',
            'receta'
        )


# Actualizar los inlines de ProduccionAdmin
ProduccionAdmin.inlines = [ProduccionRecetaInline]
