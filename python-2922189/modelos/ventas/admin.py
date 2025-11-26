from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db import models
from .models import Venta, Pago, DetalleVenta, VentaProduccion, VentaReceta


@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    """
    Administración del modelo Venta
    """
    
    list_display = [
        'id_ven',
        'cliente',
        'tipo',
        'total_formateado',
        'estado',
        'nombre_completo_usuario',
        'nombre_completo_asignado',
        'fecha_formateada',
        'tiempo_transcurrido',
    ]
    
    list_filter = [
        'estado',
        'tipo',
        'fecha',
        'usuario_asignado',
        'usuario',
    ]
    
    search_fields = [
        'id_ven',
        'cliente__nombre',
        'cliente__nit',
        'usuario__nombres',
        'usuario__apellidos',
        'usuario_asignado__nombres',
        'usuario_asignado__apellidos',
        'observaciones',
    ]
    
    readonly_fields = [
        'fecha',
        'tiempo_transcurrido',
        'total_formateado',
        'fecha_formateada',
        'estado_produccion',
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': (
                'tipo',
                'cliente',
                'total',
                'estado',
            )
        }),
        ('Asignación', {
            'fields': (
                'usuario',
                'usuario_asignado',
            )
        }),
        ('Producción', {
            'fields': (
                'numero_produccion',
                'estado_produccion',
            ),
            'classes': ('collapse',),
        }),
        ('Fechas y Tiempos', {
            'fields': (
                'fecha',
                'fecha_formateada',
                'tiempo_transcurrido',
            )
        }),
        ('Información Adicional', {
            'fields': (
                'observaciones',
                'total_formateado',
            ),
            'classes': ('collapse',),
        }),
    )
    
    ordering = ['-fecha']
    
    # Acciones personalizadas
    actions = [
        'confirmar_ventas',
        'iniciar_preparacion',
        'marcar_como_lista',
        'entregar_ventas',
        'facturar_ventas',
        'cancelar_ventas'
    ]
    
    def confirmar_ventas(self, request, queryset):
        """Confirma las ventas seleccionadas"""
        count = 0
        for venta in queryset:
            try:
                if venta.puede_confirmar:
                    venta.confirmar_venta()
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas confirmadas exitosamente.')
    confirmar_ventas.short_description = "Confirmar ventas seleccionadas"
    
    def iniciar_preparacion(self, request, queryset):
        """Inicia preparación de las ventas seleccionadas"""
        count = 0
        for venta in queryset:
            try:
                if venta.puede_preparar:
                    venta.iniciar_preparacion()
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas en preparación exitosamente.')
    iniciar_preparacion.short_description = "Iniciar preparación de ventas"
    
    def marcar_como_lista(self, request, queryset):
        """Marca las ventas como listas para entrega"""
        count = 0
        for venta in queryset:
            try:
                if venta.estado == 'En Preparacion':
                    venta.marcar_lista()
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas marcadas como listas.')
    marcar_como_lista.short_description = "Marcar como listas para entrega"
    
    def entregar_ventas(self, request, queryset):
        """Entrega las ventas seleccionadas"""
        count = 0
        for venta in queryset:
            try:
                if venta.puede_entregar:
                    venta.entregar_venta()
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas entregadas exitosamente.')
    entregar_ventas.short_description = "Entregar ventas seleccionadas"
    
    def facturar_ventas(self, request, queryset):
        """Factura las ventas seleccionadas"""
        count = 0
        for venta in queryset:
            try:
                if venta.puede_facturar:
                    venta.facturar_venta()
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas facturadas exitosamente.')
    facturar_ventas.short_description = "Facturar ventas seleccionadas"
    
    def cancelar_ventas(self, request, queryset):
        """Cancela las ventas seleccionadas"""
        count = 0
        for venta in queryset:
            try:
                if venta.puede_cancelar:
                    venta.cancelar_venta("Cancelación masiva desde admin")
                    venta.save()
                    count += 1
            except ValueError:
                continue
        
        self.message_user(request, f'{count} ventas canceladas exitosamente.')
    cancelar_ventas.short_description = "Cancelar ventas seleccionadas"
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'cliente',
            'usuario',
            'usuario_asignado',
            'numero_produccion'
        )


class PagoInline(admin.TabularInline):
    """
    Inline para mostrar pagos dentro de la venta
    """
    model = Pago
    extra = 0
    readonly_fields = ['fecha_pago', 'monto_formateado_display']
    fields = ['fecha_pago', 'monto', 'tipo_pago', 'monto_formateado_display']
    
    def monto_formateado_display(self, obj):
        """Muestra el monto formateado"""
        if obj.id:
            return obj.monto_formateado
        return "$0"
    monto_formateado_display.short_description = 'Monto'


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    """
    Administración del modelo Pago
    """
    
    list_display = [
        'id_pago',
        'venta_link',
        'cliente_display',
        'fecha_formateada_display',
        'monto_display',
        'tipo_pago_display',
    ]
    
    list_filter = [
        'tipo_pago',
        'fecha_pago',
        'venta__estado',
        'venta__tipo',
    ]
    
    search_fields = [
        'id_pago',
        'venta__id_ven',
        'venta__cliente__nombre',
        'venta__cliente__nit',
    ]
    
    date_hierarchy = 'fecha_pago'
    ordering = ['-fecha_pago']
    
    readonly_fields = [
        'fecha_pago',
        'total_venta',
    ]
    
    fieldsets = (
        ('Información del Pago', {
            'fields': (
                'venta',
                'monto',
                'fecha_pago',
            )
        }),
        ('Tipo', {
            'fields': (
                'tipo_pago',
            )
        }),
        ('Cálculos Automáticos', {
            'fields': (
                'total_venta',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Métodos para mostrar información formateada
    def venta_link(self, obj):
        """Link a la venta asociada"""
        if obj.venta:
            url = reverse('admin:ventas_venta_change', args=[obj.venta.id_ven])
            return format_html('<a href="{}">{}</a>', url, f"Venta #{obj.venta.id_ven}")
        return "Sin venta"
    venta_link.short_description = 'Venta'
    
    def cliente_display(self, obj):
        """Muestra el cliente de la venta"""
        return obj.nombre_cliente
    cliente_display.short_description = 'Cliente'
    
    def fecha_formateada_display(self, obj):
        """Muestra la fecha formateada"""
        return obj.fecha_formateada
    fecha_formateada_display.short_description = 'Fecha Pago'
    
    def monto_display(self, obj):
        """Muestra el monto formateado"""
        return obj.monto_formateado
    monto_display.short_description = 'Monto'
    
    def tipo_pago_display(self, obj):
        """Muestra el tipo de pago"""
        return obj.get_tipo_pago_display()
    tipo_pago_display.short_description = 'Tipo'
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'venta',
            'venta__cliente',
            'venta__usuario'
        )


# Registrar el inline en VentaAdmin
VentaAdmin.inlines = [PagoInline]


class DetalleVentaInline(admin.TabularInline):
    """
    Inline para mostrar detalles dentro de la venta
    """
    model = DetalleVenta
    extra = 1
    readonly_fields = ['subtotal_display', 'porcentaje_venta_display', 'precio_actual_display']
    fields = ['receta', 'nombre_empanada', 'cantidad', 'precio_unitario', 'subtotal_display', 'porcentaje_venta_display']
    
    def subtotal_display(self, obj):
        """Muestra el subtotal calculado"""
        if obj.id:
            return obj.subtotal_formateado
        return "$0"
    subtotal_display.short_description = 'Subtotal'
    
    def porcentaje_venta_display(self, obj):
        """Muestra el porcentaje que representa del total"""
        if obj.id and obj.venta:
            return f"{obj.porcentaje_venta:.1f}%"
        return "0%"
    porcentaje_venta_display.short_description = '% Total'
    
    def precio_actual_display(self, obj):
        """Muestra el precio actual de la receta"""
        if obj.receta:
            precio_actual = obj.precio_actual_receta
            diferencia = obj.diferencia_precio
            if diferencia != 0:
                color = 'red' if diferencia > 0 else 'green'
                return format_html(
                    '${:,.0f} <span style="color: {};">({}${:,.0f})</span>',
                    precio_actual, color, '+' if diferencia > 0 else '', diferencia
                )
            return f"${precio_actual:,.0f}"
        return "N/A"
    precio_actual_display.short_description = 'Precio Actual'


@admin.register(DetalleVenta)
class DetalleVentaAdmin(admin.ModelAdmin):
    """
    Administración del modelo DetalleVenta
    """
    
    list_display = [
        'id_detalle',
        'venta_link',
        'cliente_display',
        'producto_display',
        'cantidad',
        'precio_unitario_display',
        'subtotal_display',
        'porcentaje_venta_display',
        'margen_estimado_display'
    ]
    
    list_filter = [
        'venta__fecha',
        'venta__estado',
        'receta__nombre',
        'venta__tipo',
    ]
    
    search_fields = [
        'venta__id_ven',
        'venta__cliente__nombre',
        'receta__nombre',
        'nombre_empanada',
    ]
    
    date_hierarchy = 'venta__fecha'
    ordering = ['-venta__fecha', 'id_detalle']
    
    readonly_fields = [
        'subtotal',
        'porcentaje_venta',
        'precio_actual_receta',
        'diferencia_precio',
        'porcentaje_diferencia_precio',
        'margen_ganancia_estimado',
        'disponibilidad_actual',
    ]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'venta',
                'receta',
                'nombre_empanada',
            )
        }),
        ('Cantidades y Precios', {
            'fields': (
                'cantidad',
                'precio_unitario',
                'subtotal',
            )
        }),
        ('Análisis de Precios', {
            'fields': (
                'precio_actual_receta',
                'diferencia_precio',
                'porcentaje_diferencia_precio',
            ),
            'classes': ('collapse',),
        }),
        ('Estadísticas', {
            'fields': (
                'porcentaje_venta',
                'margen_ganancia_estimado',
                'disponibilidad_actual',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Métodos para mostrar información formateada
    def venta_link(self, obj):
        """Link a la venta asociada"""
        if obj.venta:
            url = reverse('admin:ventas_venta_change', args=[obj.venta.id_ven])
            return format_html('<a href="{}">{}</a>', url, f"Venta #{obj.venta.id_ven}")
        return "Sin venta"
    venta_link.short_description = 'Venta'
    
    def cliente_display(self, obj):
        """Muestra el cliente de la venta"""
        if obj.venta and obj.venta.cliente:
            return obj.venta.cliente.nombre
        return "Sin cliente"
    cliente_display.short_description = 'Cliente'
    
    def producto_display(self, obj):
        """Muestra el producto con disponibilidad"""
        producto = obj.nombre_producto_actual
        if not obj.disponibilidad_actual:
            return format_html(
                '<span style="color: red;">{} ⚠️</span>',
                producto
            )
        return producto
    producto_display.short_description = 'Producto'
    
    def precio_unitario_display(self, obj):
        """Muestra el precio unitario con comparación"""
        precio = obj.precio_unitario_formateado
        diferencia = obj.diferencia_precio
        
        if diferencia != 0:
            color = 'red' if diferencia > 0 else 'green'
            signo = '+' if diferencia > 0 else ''
            return format_html(
                '{} <small style="color: {};">({}${:,.0f})</small>',
                precio, color, signo, diferencia
            )
        return precio
    precio_unitario_display.short_description = 'Precio Unit.'
    
    def subtotal_display(self, obj):
        """Muestra el subtotal"""
        return obj.subtotal_formateado
    subtotal_display.short_description = 'Subtotal'
    
    def porcentaje_venta_display(self, obj):
        """Muestra el porcentaje que representa del total"""
        porcentaje = obj.porcentaje_venta
        return f"{porcentaje:.1f}%"
    porcentaje_venta_display.short_description = '% Venta'
    
    def margen_estimado_display(self, obj):
        """Muestra el margen estimado"""
        margen = obj.margen_ganancia_estimado
        if margen > 0:
            color = 'green' if margen >= 50 else ('orange' if margen >= 25 else 'red')
            return format_html(
                '<span style="color: {};">{:.1f}%</span>',
                color, margen
            )
        return "N/A"
    margen_estimado_display.short_description = 'Margen Est.'
    
    # Acciones personalizadas
    actions = [
        'actualizar_precios_desde_recetas',
        'calcular_ingresos_por_producto',
        'generar_reporte_productos_vendidos',
    ]
    
    def actualizar_precios_desde_recetas(self, request, queryset):
        """Actualiza precios con los precios actuales de las recetas"""
        actualizados = 0
        for detalle in queryset:
            if detalle.actualizar_precio_desde_receta():
                detalle.save()
                actualizados += 1
        
        self.message_user(request, f'{actualizados} precios actualizados desde recetas.')
    actualizar_precios_desde_recetas.short_description = "Actualizar precios desde recetas"
    
    def calcular_ingresos_por_producto(self, request, queryset):
        """Calcula ingresos generados por los productos seleccionados"""
        total_ingresos = queryset.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        )['total'] or 0
        
        cantidad_total = queryset.aggregate(
            cantidad=models.Sum('cantidad')
        )['cantidad'] or 0
        
        productos_unicos = queryset.values('receta__nombre').distinct().count()
        
        self.message_user(
            request,
            f'Ingresos: ${total_ingresos:,.0f} | Cantidad: {cantidad_total} | Productos únicos: {productos_unicos}'
        )
    calcular_ingresos_por_producto.short_description = "Calcular ingresos por producto"
    
    def generar_reporte_productos_vendidos(self, request, queryset):
        """Genera reporte de productos más vendidos en la selección"""
        productos = queryset.values('receta__nombre').annotate(
            cantidad_total=models.Sum('cantidad'),
            ingresos_total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        ).order_by('-cantidad_total')[:5]
        
        top_productos = [
            f"{p['receta__nombre']}: {p['cantidad_total']} unidades (${p['ingresos_total']:,.0f})"
            for p in productos
        ]
        
        self.message_user(
            request,
            f"Top productos: {' | '.join(top_productos)}"
        )
    generar_reporte_productos_vendidos.short_description = "Top productos vendidos"
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'venta',
            'venta__cliente',
            'receta'
        )


# Actualizar los inlines de VentaAdmin para incluir DetalleVenta
VentaAdmin.inlines = [DetalleVentaInline, PagoInline]


class VentaProduccionInline(admin.TabularInline):
    """
    Inline para mostrar producciones asociadas dentro de la venta
    """
    model = VentaProduccion
    extra = 0
    readonly_fields = ['sincronizacion_display', 'progreso_display', 'tiempo_transcurrido_display']
    fields = ['produccion', 'cantidad', 'sincronizacion_display', 'progreso_display', 'tiempo_transcurrido_display']
    
    def sincronizacion_display(self, obj):
        """Muestra el estado de sincronización"""
        if obj.id:
            sincro = obj.sincronizacion_estados
            color = obj.color_estado
            return format_html(
                '<span style="color: {}; font-weight: bold;">{}</span>',
                color, sincro
            )
        return "N/A"
    sincronizacion_display.short_description = 'Sincronización'
    
    def progreso_display(self, obj):
        """Muestra el progreso como barra"""
        if obj.id:
            progreso = obj.progreso_cumplimiento
            color = 'green' if progreso == 100 else ('orange' if progreso >= 50 else 'red')
            return format_html(
                '<div style="width: 80px; background-color: #f0f0f0; border-radius: 3px;">'
                '<div style="width: {}%; background-color: {}; height: 15px; border-radius: 3px; '
                'display: flex; align-items: center; justify-content: center; color: white; font-size: 10px;">'
                '{}%</div></div>',
                progreso, color, progreso
            )
        return "0%"
    progreso_display.short_description = 'Progreso'
    
    def tiempo_transcurrido_display(self, obj):
        """Muestra el tiempo transcurrido"""
        if obj.id:
            return obj.tiempo_entre_venta_produccion
        return "N/A"
    tiempo_transcurrido_display.short_description = 'Tiempo'


@admin.register(VentaProduccion)
class VentaProduccionAdmin(admin.ModelAdmin):
    """
    Administración del modelo VentaProduccion
    """
    
    list_display = [
        'id_ven_prod',
        'venta_link',
        'produccion_link',
        'cliente_display',
        'cantidad',
        'sincronizacion_display',
        'progreso_display',
        'requiere_atencion_display',
        'empleado_produccion'
    ]
    
    list_filter = [
        'venta__estado',
        'produccion__estado',
        'venta__fecha',
        'produccion__fecha_hora',
        'produccion__usuario_asignado',
    ]
    
    search_fields = [
        'venta__id_ven',
        'produccion__id_proc',
        'venta__cliente__nombre',
        'nombre_venta',
        'nombre_produccion',
    ]
    
    date_hierarchy = 'venta__fecha'
    ordering = ['-venta__fecha', 'id_ven_prod']
    
    readonly_fields = [
        'numero_venta',
        'numero_produccion',
        'estado_venta',
        'estado_produccion',
        'sincronizacion_estados',
        'progreso_cumplimiento',
        'tiempo_entre_venta_produccion',
        'requiere_atencion',
        'valor_venta',
        'valor_produccion_estimado',
    ]
    
    fieldsets = (
        ('Relación Principal', {
            'fields': (
                'venta',
                'produccion',
                'cantidad',
            )
        }),
        ('Estados y Sincronización', {
            'fields': (
                'estado_venta',
                'estado_produccion',
                'sincronizacion_estados',
                'progreso_cumplimiento',
            )
        }),
        ('Tiempos y Atención', {
            'fields': (
                'tiempo_entre_venta_produccion',
                'requiere_atencion',
            ),
            'classes': ('collapse',),
        }),
        ('Valores', {
            'fields': (
                'valor_venta',
                'valor_produccion_estimado',
            ),
            'classes': ('collapse',),
        }),
        ('Información Histórica', {
            'fields': (
                'nombre_venta',
                'nombre_produccion',
                'numero_venta',
                'numero_produccion',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Métodos para mostrar información formateada
    def venta_link(self, obj):
        """Link a la venta asociada"""
        if obj.venta:
            url = reverse('admin:ventas_venta_change', args=[obj.venta.id_ven])
            estado_color = {'Pendiente': 'orange', 'Confirmada': 'blue', 'Lista': 'green', 'Entregada': 'darkgreen', 'Cancelada': 'red'}.get(obj.estado_venta, 'black')
            return format_html(
                '<a href="{}">Venta #{}</a> <span style="color: {};">({})</span>',
                url, obj.numero_venta, estado_color, obj.estado_venta
            )
        return "Sin venta"
    venta_link.short_description = 'Venta'
    
    def produccion_link(self, obj):
        """Link a la producción asociada"""
        if obj.produccion:
            url = reverse('admin:produccion_produccion_change', args=[obj.produccion.id_proc])
            estado_color = {'Pendiente': 'orange', 'Aceptada': 'blue', 'Finalizada': 'green', 'Esperando insumos': 'purple'}.get(obj.estado_produccion, 'black')
            return format_html(
                '<a href="{}">Prod #{}</a> <span style="color: {};">({})</span>',
                url, obj.numero_produccion, estado_color, obj.estado_produccion
            )
        return "Sin producción"
    produccion_link.short_description = 'Producción'
    
    def cliente_display(self, obj):
        """Muestra el cliente"""
        return obj.cliente_venta
    cliente_display.short_description = 'Cliente'
    
    def sincronizacion_display(self, obj):
        """Muestra el estado de sincronización con color"""
        sincro = obj.sincronizacion_estados
        color = obj.color_estado
        icon = "⚠️" if obj.requiere_atencion else "✅"
        
        return format_html(
            '{} <span style="color: {}; font-weight: bold;">{}</span>',
            icon, color, sincro
        )
    sincronizacion_display.short_description = 'Sincronización'
    
    def progreso_display(self, obj):
        """Muestra el progreso como barra de progreso"""
        progreso = obj.progreso_cumplimiento
        color = 'green' if progreso == 100 else ('orange' if progreso >= 50 else 'red')
        
        return format_html(
            '<div style="width: 100px; background-color: #f0f0f0; border-radius: 5px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 20px; '
            'display: flex; align-items: center; justify-content: center; '
            'color: white; font-size: 12px; font-weight: bold;">'
            '{}%</div></div>',
            progreso, color, progreso
        )
    progreso_display.short_description = 'Progreso'
    
    def requiere_atencion_display(self, obj):
        """Indica si requiere atención"""
        if obj.requiere_atencion:
            return format_html('<span style="color: red; font-weight: bold;">🚨 SÍ</span>')
        return format_html('<span style="color: green;">✅ No</span>')
    requiere_atencion_display.short_description = 'Requiere Atención'
    
    # Acciones personalizadas
    actions = [
        'sincronizar_estados',
        'identificar_desincronizadas',
        'generar_reporte_cumplimiento',
    ]
    
    def sincronizar_estados(self, request, queryset):
        """Sincroniza automáticamente los estados"""
        sincronizadas = 0
        cambios_totales = []
        
        for relacion in queryset:
            exito, cambios = relacion.sincronizar_estados_automatico()
            if exito and "Sin cambios" not in cambios:
                sincronizadas += 1
                cambios_totales.append(f"VP-{relacion.id_ven_prod}: {cambios}")
        
        mensaje = f"{sincronizadas} relaciones sincronizadas"
        if cambios_totales:
            mensaje += f". Cambios: {'; '.join(cambios_totales[:3])}"
            if len(cambios_totales) > 3:
                mensaje += f" y {len(cambios_totales) - 3} más"
        
        self.message_user(request, mensaje)
    sincronizar_estados.short_description = "Sincronizar estados automáticamente"
    
    def identificar_desincronizadas(self, request, queryset):
        """Identifica relaciones que requieren atención"""
        requieren_atencion = [rel for rel in queryset if rel.requiere_atencion]
        desincronizadas = [rel for rel in queryset if rel.sincronizacion_estados == "Desincronizado"]
        
        mensaje = f"De {queryset.count()}: {len(requieren_atencion)} requieren atención, {len(desincronizadas)} desincronizadas"
        
        if requieren_atencion:
            ejemplos = [f"VP-{rel.id_ven_prod}" for rel in requieren_atencion[:3]]
            mensaje += f". Ejemplos: {', '.join(ejemplos)}"
        
        self.message_user(request, mensaje)
    identificar_desincronizadas.short_description = "Identificar relaciones problemáticas"
    
    def generar_reporte_cumplimiento(self, request, queryset):
        """Genera reporte de cumplimiento"""
        total = queryset.count()
        if total == 0:
            self.message_user(request, "No hay datos para reportar")
            return
        
        # Calcular estadísticas
        completadas = queryset.filter(produccion__estado='Finalizada').count()
        en_proceso = queryset.filter(produccion__estado='En Proceso').count()
        pendientes = queryset.filter(produccion__estado='Pendiente').count()
        canceladas = queryset.filter(produccion__estado='Cancelada').count()
        
        porcentaje_completadas = (completadas / total) * 100
        
        # Calcular tiempo promedio
        tiempos = []
        for rel in queryset:
            tiempo_cumplimiento = rel.calcular_tiempo_cumplimiento()
            if tiempo_cumplimiento:
                tiempos.append(tiempo_cumplimiento.total_seconds() / 3600)  # Convertir a horas
        
        tiempo_promedio = sum(tiempos) / len(tiempos) if tiempos else 0
        
        mensaje = (f"Reporte: {total} relaciones | "
                  f"Completadas: {completadas} ({porcentaje_completadas:.1f}%) | "
                  f"En proceso: {en_proceso} | Pendientes: {pendientes} | Canceladas: {canceladas}")
        
        if tiempo_promedio > 0:
            mensaje += f" | Tiempo prom: {tiempo_promedio:.1f}h"
        
        self.message_user(request, mensaje)
    generar_reporte_cumplimiento.short_description = "Generar reporte de cumplimiento"
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'venta',
            'venta__cliente',
            'produccion',
            'produccion__usuario_asignado'
        )


# Actualizar los inlines de VentaAdmin para incluir VentaProduccion
VentaAdmin.inlines = [DetalleVentaInline, VentaProduccionInline, PagoInline]


class VentaRecetaInline(admin.TabularInline):
    """
    Inline para mostrar recetas asociadas dentro de la venta
    """
    model = VentaReceta
    extra = 0
    readonly_fields = ['subtotal_display', 'margen_display', 'precio_actual_display']
    fields = ['receta', 'cantidad', 'precio', 'subtotal_display', 'margen_display', 'precio_actual_display']
    
    def subtotal_display(self, obj):
        """Muestra el subtotal calculado"""
        if obj.id:
            return obj.subtotal_formateado
        return "$0"
    subtotal_display.short_description = 'Subtotal'
    
    def margen_display(self, obj):
        """Muestra el margen de ganancia"""
        if obj.id:
            margen = obj.margen_ganancia
            if margen > 0:
                color = 'green' if margen >= 50 else ('orange' if margen >= 25 else 'red')
                return format_html(
                    '<span style="color: {};">{:.1f}%</span>',
                    color, margen
                )
        return "N/A"
    margen_display.short_description = 'Margen'
    
    def precio_actual_display(self, obj):
        """Muestra el precio actual vs vendido"""
        if obj.id and obj.receta:
            precio_actual = obj.precio_actual_receta
            diferencia = obj.diferencia_precio_actual
            if abs(diferencia) > 0.01:
                color = 'red' if diferencia > 0 else 'green'
                signo = '+' if diferencia > 0 else ''
                return format_html(
                    '${:,.0f} <span style="color: {};">({}${:,.0f})</span>',
                    precio_actual, color, signo, diferencia
                )
            return f"${precio_actual:,.0f}"
        return "N/A"
    precio_actual_display.short_description = 'Precio Actual'


@admin.register(VentaReceta)
class VentaRecetaAdmin(admin.ModelAdmin):
    """
    Administración del modelo VentaReceta
    """
    
    list_display = [
        'id_venta_receta',
        'venta_link',
        'receta_display',
        'cliente_display',
        'cantidad',
        'precio_display',
        'subtotal_display',
        'margen_display',
        'promocion_display',
        'fecha_venta_display'
    ]
    
    list_filter = [
        'venta__fecha',
        'venta__estado',
        'receta__nombre',
        'venta__cliente',
    ]
    
    search_fields = [
        'venta__id_ven',
        'receta__nombre',
        'nombre_receta',
        'venta__cliente__nombre',
        'nombre_venta',
    ]
    
    date_hierarchy = 'venta__fecha'
    ordering = ['-venta__fecha', 'id_venta_receta']
    
    readonly_fields = [
        'subtotal_calculado',
        'numero_venta',
        'nombre_receta_actual',
        'precio_actual_receta',
        'diferencia_precio_actual',
        'porcentaje_diferencia_precio',
        'margen_ganancia',
        'porcentaje_total_venta',
        'tiempo_desde_venta',
        'es_precio_promocional',
        'costo_ingredientes_total',
    ]
    
    fieldsets = (
        ('Relación Principal', {
            'fields': (
                'venta',
                'receta',
                'cantidad',
                'precio',
            )
        }),
        ('Cálculos Automáticos', {
            'fields': (
                'subtotal',
                'subtotal_calculado',
                'margen_ganancia',
                'porcentaje_total_venta',
            )
        }),
        ('Análisis de Precios', {
            'fields': (
                'precio_actual_receta',
                'diferencia_precio_actual',
                'porcentaje_diferencia_precio',
                'es_precio_promocional',
            ),
            'classes': ('collapse',),
        }),
        ('Costos y Márgenes', {
            'fields': (
                'costo_ingredientes_total',
            ),
            'classes': ('collapse',),
        }),
        ('Información Histórica', {
            'fields': (
                'nombre_receta',
                'nombre_venta',
                'nombre_receta_actual',
                'numero_venta',
            ),
            'classes': ('collapse',),
        }),
        ('Información Temporal', {
            'fields': (
                'tiempo_desde_venta',
            ),
            'classes': ('collapse',),
        }),
    )
    
    # Métodos para mostrar información formateada
    def venta_link(self, obj):
        """Link a la venta asociada"""
        if obj.venta:
            url = reverse('admin:ventas_venta_change', args=[obj.venta.id_ven])
            return format_html(
                '<a href="{}">Venta #{}</a> <span style="color: gray;">({}) </span>',
                url, obj.numero_venta, obj.estado_venta
            )
        return "Sin venta"
    venta_link.short_description = 'Venta'
    
    def receta_display(self, obj):
        """Muestra la receta con disponibilidad"""
        nombre = obj.nombre_receta_actual
        if not obj.disponibilidad_actual_receta:
            return format_html('<span style="color: red;">{} ⚠️</span>', nombre)
        return nombre
    receta_display.short_description = 'Receta'
    
    def cliente_display(self, obj):
        """Muestra el cliente"""
        return obj.cliente_venta
    cliente_display.short_description = 'Cliente'
    
    def precio_display(self, obj):
        """Muestra el precio con comparación"""
        precio = obj.precio_formateado
        diferencia = obj.diferencia_precio_actual
        
        if abs(diferencia) > 0.01:
            color = 'red' if diferencia > 0 else 'green'
            signo = '+' if diferencia > 0 else ''
            return format_html(
                '{} <small style="color: {};">({}${:,.0f})</small>',
                precio, color, signo, diferencia
            )
        return precio
    precio_display.short_description = 'Precio'
    
    def subtotal_display(self, obj):
        """Muestra el subtotal"""
        return obj.subtotal_formateado
    subtotal_display.short_description = 'Subtotal'
    
    def margen_display(self, obj):
        """Muestra el margen de ganancia con color"""
        margen = obj.margen_ganancia
        if margen > 0:
            color = 'green' if margen >= 50 else ('orange' if margen >= 25 else 'red')
            return format_html(
                '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
                color, margen
            )
        return "N/A"
    margen_display.short_description = 'Margen'
    
    def promocion_display(self, obj):
        """Indica si es precio promocional"""
        if obj.es_precio_promocional:
            descuento = abs(obj.porcentaje_diferencia_precio)
            return format_html(
                '<span style="color: green; font-weight: bold;">🏷️ {:.1f}%</span>',
                descuento
            )
        return ""
    promocion_display.short_description = 'Promoción'
    
    def fecha_venta_display(self, obj):
        """Muestra la fecha con tiempo transcurrido"""
        if obj.fecha_venta:
            return format_html(
                '<span title="{}">{}</span>',
                obj.tiempo_desde_venta,
                obj.fecha_venta.strftime('%d/%m/%Y %H:%M')
            )
        return "N/A"
    fecha_venta_display.short_description = 'Fecha Venta'
    
    # Acciones personalizadas
    actions = [
        'sincronizar_con_detalles',
        'actualizar_precios_actuales',
        'generar_reporte_margenes',
        'identificar_precios_promocionales',
    ]
    
    def sincronizar_con_detalles(self, request, queryset):
        """Sincroniza con DetalleVenta correspondientes"""
        ventas_unicas = queryset.values_list('venta', flat=True).distinct()
        total_sincronizadas = 0
        
        for venta_id in ventas_unicas:
            from .models import Venta
            venta = Venta.objects.get(id_ven=venta_id)
            cantidad = VentaReceta.sincronizar_con_detalles_venta(venta)
            total_sincronizadas += cantidad
        
        self.message_user(request, f'Sincronizadas {total_sincronizadas} relaciones venta-receta')
    sincronizar_con_detalles.short_description = "Sincronizar con detalles de venta"
    
    def actualizar_precios_actuales(self, request, queryset):
        """Actualiza precios con los precios actuales de las recetas"""
        actualizadas = 0
        for venta_receta in queryset:
            precio_anterior = venta_receta.precio
            if venta_receta.actualizar_desde_receta():
                if precio_anterior != venta_receta.precio:
                    venta_receta.save()
                    actualizadas += 1
        
        self.message_user(request, f'{actualizadas} precios actualizados desde recetas')
    actualizar_precios_actuales.short_description = "Actualizar precios desde recetas"
    
    def generar_reporte_margenes(self, request, queryset):
        """Genera reporte de márgenes"""
        total_ingresos = queryset.aggregate(total=models.Sum('subtotal'))['total'] or 0
        cantidad_total = queryset.aggregate(cantidad=models.Sum('cantidad'))['cantidad'] or 0
        
        # Calcular margen promedio
        margenes = [vr.margen_ganancia for vr in queryset if vr.margen_ganancia > 0]
        margen_promedio = sum(margenes) / len(margenes) if margenes else 0
        
        precio_promedio = queryset.aggregate(precio=models.Avg('precio'))['precio'] or 0
        
        mensaje = (f"Reporte: {queryset.count()} ventas-receta | "
                  f"Ingresos: ${total_ingresos:,.0f} | "
                  f"Cantidad: {cantidad_total} | "
                  f"Margen prom: {margen_promedio:.1f}% | "
                  f"Precio prom: ${precio_promedio:,.0f}")
        
        self.message_user(request, mensaje)
    generar_reporte_margenes.short_description = "Generar reporte de márgenes"
    
    def identificar_precios_promocionales(self, request, queryset):
        """Identifica ventas con precios promocionales"""
        promocionales = [vr for vr in queryset if vr.es_precio_promocional]
        
        if promocionales:
            descuento_promedio = sum(abs(vr.porcentaje_diferencia_precio) for vr in promocionales) / len(promocionales)
            self.message_user(
                request,
                f'{len(promocionales)} ventas con precio promocional (descuento prom: {descuento_promedio:.1f}%)'
            )
        else:
            self.message_user(request, 'No se encontraron ventas con precios promocionales')
    identificar_precios_promocionales.short_description = "Identificar precios promocionales"
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        return super().get_queryset(request).select_related(
            'venta',
            'venta__cliente',
            'receta'
        )


# Actualizar los inlines de VentaAdmin para incluir todas las relaciones
VentaAdmin.inlines = [DetalleVentaInline, VentaRecetaInline, VentaProduccionInline, PagoInline]
