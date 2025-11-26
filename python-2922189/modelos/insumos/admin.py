from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Insumo, DetalleInsumo, HistorialInsumo


@admin.register(Insumo)
class InsumoAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 
        'unidad_medida', 
        'stock_actual_display', 
        'stock_min', 
        'estado_display',
        'porcentaje_stock_display'
    ]
    list_filter = ['estado', 'unidad_medida']
    search_fields = ['nombre']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información del Insumo', {
            'fields': ('nombre', 'unidad_medida')
        }),
        ('Control de Stock', {
            'fields': ('stock_min', 'stock_actual', 'estado')
        }),
    )
    
    readonly_fields = ['estado']  # El estado se calcula automáticamente
    
    def stock_actual_display(self, obj):
        """Muestra el stock actual con color según el nivel"""
        color = 'red' if obj.necesita_restock else 'green'
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color,
            obj.stock_actual,
            obj.unidad_medida
        )
    stock_actual_display.short_description = 'Stock Actual'
    
    def estado_display(self, obj):
        """Muestra el estado con color"""
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.status_color,
            obj.estado
        )
    estado_display.short_description = 'Estado'
    
    def porcentaje_stock_display(self, obj):
        """Muestra el porcentaje de stock como barra"""
        porcentaje = obj.porcentaje_stock
        color = 'red' if porcentaje < 100 else 'green'
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 3px;">'
            '<div style="width: {}%; background-color: {}; height: 20px; border-radius: 3px; '
            'display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">'
            '{}%</div></div>',
            min(100, porcentaje),
            color,
            round(porcentaje, 1)
        )
    porcentaje_stock_display.short_description = 'Nivel de Stock'
    
    def save_model(self, request, obj, form, change):
        """Override para aplicar lógica de negocio al guardar"""
        obj.recalcular_estado()
        super().save_model(request, obj, form, change)


@admin.register(DetalleInsumo)
class DetalleInsumoAdmin(admin.ModelAdmin):
    list_display = [
        'id_detalle',
        'nombre_insumo_display', 
        'cantidad_display',
        'fecha_ingreso_display',
        'fecha_vencimiento_display', 
        'estado_display',
        'dias_vencimiento_display'
    ]
    list_filter = ['estado', 'id_ins__nombre', 'fecha_vencimiento']
    search_fields = ['id_ins__nombre']
    ordering = ['fecha_vencimiento', '-fecha_ingreso']
    
    fieldsets = (
        ('Información del Lote', {
            'fields': ('id_ins', 'cantidad')
        }),
        ('Fechas', {
            'fields': ('fecha_ingreso', 'fecha_vencimiento')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
    )
    
    readonly_fields = ['fecha_ingreso']
    
    def nombre_insumo_display(self, obj):
        """Muestra el nombre del insumo"""
        return obj.nombre_insumo
    nombre_insumo_display.short_description = 'Insumo'
    
    def cantidad_display(self, obj):
        """Muestra la cantidad con unidad"""
        return f"{obj.cantidad} {obj.unidad_medida}"
    cantidad_display.short_description = 'Cantidad'
    
    def fecha_ingreso_display(self, obj):
        """Muestra la fecha de ingreso formateada"""
        return obj.fecha_ingreso.strftime('%d/%m/%Y %H:%M')
    fecha_ingreso_display.short_description = 'F. Ingreso'
    
    def fecha_vencimiento_display(self, obj):
        """Muestra la fecha de vencimiento con color según proximidad"""
        if not obj.fecha_vencimiento:
            return "No aplica"
        
        color = obj.status_color
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.fecha_vencimiento.strftime('%d/%m/%Y')
        )
    fecha_vencimiento_display.short_description = 'F. Vencimiento'
    
    def estado_display(self, obj):
        """Muestra el estado con color"""
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            obj.status_color,
            obj.estado
        )
    estado_display.short_description = 'Estado'
    
    def dias_vencimiento_display(self, obj):
        """Muestra días para vencer"""
        dias = obj.dias_para_vencer
        if dias is None:
            return "N/A"
        
        if dias < 0:
            return format_html('<span style="color: red;">Vencido hace {} días</span>', abs(dias))
        elif dias == 0:
            return format_html('<span style="color: red; font-weight: bold;">Vence hoy</span>')
        elif dias <= 7:
            return format_html('<span style="color: orange;">Faltan {} días</span>', dias)
        else:
            return format_html('<span style="color: green;">Faltan {} días</span>', dias)
    dias_vencimiento_display.short_description = 'Vencimiento'
    
    def save_model(self, request, obj, form, change):
        """Override para aplicar lógica de negocio al guardar"""
        obj.actualizar_estado_por_vencimiento()
        obj.actualizar_estado_por_cantidad()
        super().save_model(request, obj, form, change)


@admin.register(HistorialInsumo)
class HistorialInsumoAdmin(admin.ModelAdmin):
    list_display = ['id_hist', 'fecha_formateada_display', 'accion_display', 'nombre_insumo', 'cantidad_display', 'stock_display', 'usuario_responsable']
    list_filter = ['accion', 'fecha', 'estado', 'insumo__nombre']
    search_fields = ['insumo__nombre', 'novedad', 'accion']
    date_hierarchy = 'fecha'
    ordering = ['-fecha']
    readonly_fields = ['fecha', 'stock_actual', 'nombre_insumo', 'unidad_medida', 'tiempo_transcurrido', 'tipo_operacion', 'diferencia_stock']
    
    fieldsets = (
        ('Información de la Operación', {
            'fields': ('fecha', 'accion', 'estado', 'novedad')
        }),
        ('Insumo Afectado', {
            'fields': ('insumo', 'detalle_insumo', 'nombre_insumo', 'unidad_medida')
        }),
        ('Cantidades', {
            'fields': ('cantidad', 'stock_actual', 'diferencia_stock')
        }),
        ('Información Adicional', {
            'fields': ('tiempo_transcurrido', 'tipo_operacion'),
            'classes': ('collapse',)
        })
    )
    
    def fecha_formateada_display(self, obj):
        return format_html(
            '<span title="{}">{}</span>',
            obj.fecha_formateada, obj.tiempo_transcurrido
        )
    fecha_formateada_display.short_description = 'Fecha'
    
    def accion_display(self, obj):
        return format_html(
            '<span style="color: {};">{} {}</span>',
            obj.color_accion, obj.icono_accion, obj.accion
        )
    accion_display.short_description = 'Acción'
    
    def cantidad_display(self, obj):
        signo = '+' if obj.diferencia_stock > 0 else ('-' if obj.diferencia_stock < 0 else '')
        color = 'green' if obj.diferencia_stock > 0 else ('red' if obj.diferencia_stock < 0 else 'blue')
        
        return format_html(
            '<span style="color: {};">{}{}</span>',
            color, signo, obj.cantidad_formateada
        )
    cantidad_display.short_description = 'Cantidad'
    
    def stock_display(self, obj):
        return obj.stock_formateado
    stock_display.short_description = 'Stock Resultante'
    
    def usuario_responsable(self, obj):
        # Por ahora retorna información del sistema
        # En el futuro se puede asociar con el usuario que hizo el cambio
        return "Sistema"
    usuario_responsable.short_description = 'Responsable'
    
    actions = ['exportar_historial', 'filtrar_por_periodo', 'generar_reporte_movimientos']
    
    def exportar_historial(self, request, queryset):
        # Placeholder para exportación
        count = queryset.count()
        self.message_user(request, f'Preparando exportación de {count} registros de historial.')
    exportar_historial.short_description = "Exportar historial seleccionado"
    
    def filtrar_por_periodo(self, request, queryset):
        hoy = timezone.now().date()
        ultimo_mes = queryset.filter(fecha__gte=hoy.replace(day=1))
        self.message_user(request, f'{ultimo_mes.count()} registros del último mes.')
    filtrar_por_periodo.short_description = "Filtrar por último mes"
    
    def generar_reporte_movimientos(self, request, queryset):
        ingresos = queryset.filter(accion='Ingreso').count()
        salidas = queryset.filter(accion='Salida').count()
        ajustes = queryset.filter(accion='Ajuste').count()
        self.message_user(request, f'Movimientos: {ingresos} ingresos, {salidas} salidas, {ajustes} ajustes.')
    generar_reporte_movimientos.short_description = "Generar reporte de movimientos"
    
    # Personalizar las acciones que aparecen en el formulario de cambio
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editando un objeto existente
            return self.readonly_fields + ['insumo', 'detalle_insumo', 'accion', 'cantidad']
        return self.readonly_fields
    
    def has_delete_permission(self, request, obj=None):
        # Los registros de historial no se deben eliminar para mantener auditoría
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        # Los registros de historial se crean automáticamente
        return request.user.is_superuser
