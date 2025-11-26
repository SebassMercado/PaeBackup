from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal


class Venta(models.Model):
    """
    Modelo de Ventas del sistema PAE
    Migrado desde ventas.java
    
    Maneja las ventas de productos tanto directas como por producción.
    Incluye asignación de empleados y seguimiento completo del proceso.
    """
    
    # Opciones para tipo de venta
    TIPO_CHOICES = [
        ('directa', 'Venta Directa'),
        ('pedido', 'Pedido'),
    ]
    
    # Opciones para estado de venta
    ESTADO_CHOICES = [
        ('Pago pendiente', 'Pago Pendiente'),
        ('Procesando', 'Procesando'),
        ('Pago completo', 'Pago Completo'),
        ('Completada', 'Completada'),
    ]
    
    # Campos del modelo (equivalentes a ventas.java)
    id_ven = models.AutoField(
        primary_key=True,
        db_column='id_ven',
        verbose_name='ID Venta'
    )
    
    tipo = models.CharField(
        max_length=20,
        db_column='Tipo',
        choices=TIPO_CHOICES,
        default='directa',
        verbose_name='Tipo de Venta',
        help_text='Tipo de venta realizada'
    )
    
    # Relación con cliente
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.CASCADE,
        db_column='id_Cliente',
        verbose_name='Cliente',
        help_text='Cliente que realiza la compra',
        related_name='ventas'
    )
    
    # Usuario que registra la venta
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        db_column='id_usu',
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario que registra la venta',
        related_name='ventas_registradas'
    )
    
    # Usuario asignado para procesar la venta
    usuario_asignado = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        db_column='id_asignado',
        null=True,
        blank=True,
        verbose_name='Usuario Asignado',
        help_text='Usuario asignado para procesar la venta',
        related_name='ventas_asignadas'
    )
    
    total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Total',
        help_text='Valor total de la venta',
        default=Decimal('0.00')
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='Pago pendiente',
        verbose_name='Estado',
        help_text='Estado actual de la venta'
    )
    
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha',
        help_text='Fecha y hora de la venta'
    )
    
    observaciones = models.TextField(
        blank=True,
        null=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales sobre la venta'
    )
    

    
    class Meta:
        db_table = 'ventas'
        managed = False  # No crear/modificar tabla existente
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']
    
    def __str__(self):
        return f"Venta {self.id_ven} - {self.cliente.nombre} - ${self.total} - {self.estado}"
    
    # 🧍 Propiedades auxiliares (equivalentes a campos auxiliares en Java)
    @property
    def nombre_cliente(self):
        """Nombre del cliente"""
        return self.cliente.nombre if self.cliente else ""
    
    @property
    def nombre_usuario(self):
        """Nombre del usuario que registró la venta"""
        return self.usuario.nombres if self.usuario else ""
    
    @property
    def apellido_usuario(self):
        """Apellido del usuario que registró la venta"""
        return self.usuario.apellidos if self.usuario else ""
    
    @property
    def nombre_asignado(self):
        """Nombre del usuario asignado"""
        return self.usuario_asignado.nombres if self.usuario_asignado else ""
    
    @property
    def apellido_asignado(self):
        """Apellido del usuario asignado"""
        return self.usuario_asignado.apellidos if self.usuario_asignado else ""
    
    @property
    def nombre_completo_usuario(self):
        """Nombre completo del usuario que registró"""
        return f"{self.nombre_usuario} {self.apellido_usuario}".strip()
    
    @property
    def nombre_completo_asignado(self):
        """Nombre completo del usuario asignado"""
        return f"{self.nombre_asignado} {self.apellido_asignado}".strip()
    
    @property
    def total_formateado(self):
        """Total formateado como moneda"""
        return f"${self.total:,.2f}"
    
    @property
    def fecha_formateada(self):
        """Fecha formateada para mostrar"""
        return self.fecha.strftime("%d/%m/%Y %H:%M")
    
    @property
    def tiempo_transcurrido(self):
        """Tiempo transcurrido desde la venta"""
        now = timezone.now()
        delta = now - self.fecha
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    @property
    def status_color(self):
        """Color para mostrar en interfaz según el estado"""
        colors = {
            'Pago pendiente': 'orange',
            'Procesando': 'blue',
            'Pago completo': 'green',
            'Completada': 'darkgreen'
        }
        return colors.get(self.estado, 'gray')
    
    @property
    def requiere_produccion(self):
        """Indica si la venta requiere producción"""
        return self.tipo == 'pedido'
    
    @property
    def tiene_produccion_asociada(self):
        """Indica si tiene una producción asociada"""
        return False  # No production relation in current schema
    
    @property
    def estado_produccion(self):
        """Estado de la producción asociada (si existe)"""
        return None  # No production relation in current schema
    
    @property
    def puede_confirmar(self):
        """Verifica si la venta puede ser confirmada"""
        return self.estado == 'Pago pendiente'
    
    @property
    def puede_preparar(self):
        """Verifica si la venta puede pasar a preparación"""
        return self.estado == 'Pago completo'
    
    @property
    def puede_entregar(self):
        """Verifica si la venta puede ser entregada"""
        return self.estado == 'Procesando'
    
    @property
    def puede_facturar(self):
        """Verifica si la venta puede ser facturada"""
        return self.estado == 'Completada'
    
    @property
    def puede_cancelar(self):
        """Verifica si la venta puede ser cancelada"""
        return self.estado in ['Pago pendiente', 'Procesando']
    
    # 🎯 Métodos de lógica de negocio
    
    def confirmar_venta(self):
        """Confirma la venta"""
        if not self.puede_confirmar:
            raise ValueError(f"No se puede confirmar una venta en estado '{self.estado}'")
        self.estado = 'Procesando'
        # Aceptar producciones asociadas si existen y están Pendientes
        try:
            for vp in getattr(self, 'producciones_asociadas', []).all():
                prod = vp.produccion
                if prod and prod.estado == 'Pendiente':
                    prod.aceptar_produccion()
                    prod.save()
        except Exception as e:
            print(f"[WARN] No se pudieron aceptar producciones asociadas a venta {self.id_ven}: {e}")
    
    def iniciar_preparacion(self):
        """Inicia la preparación de la venta"""
        if not self.puede_preparar:
            raise ValueError(f"No se puede iniciar preparación en estado '{self.estado}'")
        
        self.estado = 'Procesando'
    
    def marcar_lista(self):
        """Marca la venta como lista para entrega"""
        if self.estado != 'Procesando':
            raise ValueError(f"No se puede marcar como lista desde estado '{self.estado}'")
        
        self.estado = 'Pago completo'
    
    def entregar_venta(self):
        """Entrega la venta al cliente"""
        if not self.puede_entregar:
            raise ValueError(f"No se puede entregar una venta en estado '{self.estado}'")
        self.estado = 'Completada'
        # Si al entregar hubiera producciones pendientes de finalizar, intentamos finalizarlas si están Aceptadas/Esperando insumos
        try:
            for vp in getattr(self, 'producciones_asociadas', []).all():
                prod = vp.produccion
                if prod and prod.estado in ['Aceptada', 'Esperando insumos']:
                    prod.finalizar_produccion()
                    prod.save()
        except Exception as e:
            print(f"[WARN] No se pudieron finalizar producciones al entregar venta {self.id_ven}: {e}")
    
    def facturar_venta(self):
        """Factura la venta"""
        if not self.puede_facturar:
            raise ValueError(f"No se puede facturar una venta en estado '{self.estado}'")
        
        # Already in final state
        pass
    
    def cancelar_venta(self, motivo=""):
        """Cancela la venta"""
        if not self.puede_cancelar:
            raise ValueError(f"No se puede cancelar una venta en estado '{self.estado}'")
        
        self.estado = 'Cancelada'
        if motivo:
            self.observaciones = f"{self.observaciones or ''}\nMotivo cancelación: {motivo}".strip()
    

    
    def calcular_total_detalle(self):
        """Calcula el total basado en los detalles de la venta"""
        total = Decimal('0.00')
        for detalle in self.detalles.all():
            total += detalle.subtotal
        return total
    
    def actualizar_total(self):
        """Actualiza el total de la venta basado en los detalles"""
        self.total = self.calcular_total_detalle()
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if self.total < 0:
            raise ValidationError({'total': 'El total no puede ser negativo'})
        
        # Production validation removed for current schema
        
        # Validar que el usuario asignado tenga el rol adecuado
        if self.usuario_asignado and self.usuario_asignado.rol not in ['A', 'EV', 'EP']:
            raise ValidationError({'usuario_asignado': 'El usuario asignado debe ser Admin, Empleado de Ventas o Empleado de Producción'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        self.full_clean()  # Ejecuta validaciones
        super().save(*args, **kwargs)
    
    def recalcular_total(self):
        """Recalcula el total de la venta basado en sus detalles"""
        total_detalles = self.detalles.aggregate(
            total=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        )['total'] or Decimal('0.00')
        
        self.total = total_detalles
        return self.total


class Pago(models.Model):
    """
    Modelo de Pago del sistema PAE
    Migrado desde pago.java
    
    Maneja los pagos asociados a las ventas, permitiendo pagos parciales (abonos)
    o pagos completos. Soporta múltiples pagos por venta para facilitar el flujo de caja.
    """
    
    # Opciones para tipo de pago (solo las que están en la BD)
    TIPO_PAGO_CHOICES = [
        ('abono', 'Abono'),
        ('total', 'Pago total'),
    ]
    
    # Campos del modelo (solo los que existen en la tabla)
    id_pago = models.AutoField(
        primary_key=True,
        db_column='id_pago',
        verbose_name='ID Pago'
    )
    
    fecha_pago = models.DateTimeField(
        default=timezone.now,
        db_column='fecha_pago',
        verbose_name='Fecha de Pago',
        help_text='Fecha y hora en que se realizó el pago'
    )
    
    monto = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        db_column='monto',
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Monto',
        help_text='Monto del pago realizado'
    )
    
    tipo_pago = models.CharField(
        max_length=20,
        db_column='tipo_pago',
        choices=TIPO_PAGO_CHOICES,
        default='abono',
        verbose_name='Tipo de Pago',
        help_text='Indica si es un abono parcial o pago total'
    )
    
    # Relaciones
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.DO_NOTHING,
        db_column='id_ven',
        verbose_name='Venta',
        help_text='Venta a la que pertenece este pago',
        related_name='pagos'
    )
    
    class Meta:
        db_table = 'pago'
        verbose_name = 'Pago'
        verbose_name_plural = 'Pagos'
        ordering = ['-fecha_pago']
        indexes = [
            models.Index(fields=['fecha_pago']),
            models.Index(fields=['venta']),
            models.Index(fields=['tipo_pago']),
            models.Index(fields=['venta', 'fecha_pago']),
        ]
    
    def __str__(self):
        return f"Pago {self.id_pago} - Venta {self.venta.id_ven} - ${self.monto:,.0f} ({self.tipo_pago})"
    
    # Propiedades auxiliares
    @property
    def monto_formateado(self):
        """Monto formateado como moneda"""
        return f"${self.monto:,.0f}"
    
    @property
    def fecha_formateada(self):
        """Fecha formateada para mostrar"""
        return self.fecha_pago.strftime("%d/%m/%Y %H:%M")
    
    @property
    def nombre_cliente(self):
        """Nombre del cliente de la venta"""
        return self.venta.cliente.nombre if self.venta and self.venta.cliente else "Sin cliente"
    
    @property
    def numero_venta(self):
        """Número de la venta asociada"""
        return self.venta.id_ven if self.venta else None
    
    @property
    def total_venta(self):
        """Total de la venta asociada"""
        return self.venta.total if self.venta else Decimal('0.00')
    
    # Métodos de negocio
    @staticmethod
    def calcular_total_pagado_venta(venta):
        """Calcula el total pagado para una venta específica"""
        return Pago.objects.filter(venta=venta).aggregate(
            total=models.Sum('monto')
        )['total'] or Decimal('0.00')
    
    @staticmethod
    def calcular_saldo_pendiente_venta(venta):
        """Calcula el saldo pendiente de una venta"""
        total_pagado = Pago.calcular_total_pagado_venta(venta)
        return max(Decimal('0.00'), venta.total - total_pagado)
    
    @staticmethod
    def crear_pago(venta, monto, tipo_pago='abono'):
        """Crea un nuevo pago con validaciones automáticas"""
        from django.core.exceptions import ValidationError
        
        # Validar saldo disponible
        total_pagado = Pago.calcular_total_pagado_venta(venta)
        saldo_pendiente = venta.total - total_pagado
        
        if monto > saldo_pendiente:
            raise ValidationError(f'El monto ${monto:,.0f} excede el saldo pendiente ${saldo_pendiente:,.0f}')
        
        pago = Pago(
            venta=venta,
            monto=monto,
            tipo_pago=tipo_pago
        )
        
        pago.save()
        return pago
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if self.monto <= 0:
            raise ValidationError({'monto': 'El monto debe ser mayor a cero'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        self.full_clean()
        super().save(*args, **kwargs)


class DetalleVenta(models.Model):
    """
    Modelo de Detalle de Venta del sistema PAE
    Migrado desde DetalleVenta.java
    
    Representa los productos individuales (recetas) incluidos en una venta,
    con sus cantidades y precios. Permite manejar ventas con múltiples productos.
    """
    
    # Campos del modelo (equivalentes a DetalleVenta.java)
    id_detalle = models.AutoField(
        primary_key=True,
        db_column='idDetalle',
        verbose_name='ID Detalle'
    )
    
    nombre_empanada = models.CharField(
        max_length=100,
        verbose_name='Nombre del Producto',
        help_text='Nombre del producto al momento de la venta (histórico)',
        blank=True
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Cantidad de productos vendidos'
    )
    
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio Unitario',
        help_text='Precio por unidad al momento de la venta (histórico)',
        default=Decimal('0.00')
    )
    
    # Relaciones
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.DO_NOTHING,  # No hacer cascade a tabla inexistente
        db_column='id_ven',
        verbose_name='Venta',
        help_text='Venta a la que pertenece este detalle',
        related_name='detalles'
    )
    
    receta = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.CASCADE,
        db_column='id_receta',
        verbose_name='Receta/Producto',
        help_text='Producto vendido',
        related_name='ventas_detalle'
    )
    
    class Meta:
        db_table = 'detalle_venta'
        managed = False  # No crear/modificar tabla inexistente
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Ventas'
        ordering = ['venta', 'id_detalle']
    
    def __str__(self):
        return f"Detalle {self.id_detalle} - Venta {self.venta.id_ven if self.venta else 'N/A'} - {self.nombre_producto_actual} x{self.cantidad}"
    
    # 🧍 Propiedades calculadas
    @property
    def subtotal(self):
        """Calcula el subtotal (cantidad × precio unitario)"""
        return self.cantidad * self.precio_unitario
    
    @property
    def subtotal_formateado(self):
        """Subtotal formateado como moneda"""
        return f"${self.subtotal:,.0f}"
    
    @property
    def precio_unitario_formateado(self):
        """Precio unitario formateado como moneda"""
        return f"${self.precio_unitario:,.0f}"
    
    @property
    def nombre_producto_actual(self):
        """Nombre actual del producto (de la receta)"""
        return self.receta.nombre if self.receta else self.nombre_empanada
    
    @property
    def precio_actual_receta(self):
        """Precio actual de la receta (puede ser diferente al histórico)"""
        return self.receta.precio if self.receta else self.precio_unitario
    
    @property
    def diferencia_precio(self):
        """Diferencia entre precio vendido y precio actual"""
        return self.precio_unitario - self.precio_actual_receta
    
    @property
    def porcentaje_diferencia_precio(self):
        """Porcentaje de diferencia de precio"""
        if self.precio_actual_receta > 0:
            return ((self.precio_unitario - self.precio_actual_receta) / self.precio_actual_receta) * 100
        return Decimal('0.00')
    
    @property
    def categoria_producto(self):
        """Categoría del producto vendido"""
        return getattr(self.receta, 'categoria', 'Sin categoría') if self.receta else 'Sin categoría'
    
    @property
    def disponibilidad_actual(self):
        """Verifica si el producto está disponible actualmente"""
        if not self.receta:
            return False
        return getattr(self.receta, 'esta_disponible', True)
    
    @property
    def porcentaje_venta(self):
        """Porcentaje que representa este detalle del total de la venta"""
        if self.venta and self.venta.total > 0:
            return (self.subtotal / self.venta.total) * 100
        return Decimal('0.00')
    
    @property
    def margen_ganancia_estimado(self):
        """Calcula margen estimado basado en costo de ingredientes"""
        if not self.receta:
            return Decimal('0.00')
        
        # Obtener costo de ingredientes de la receta
        costo_ingredientes = getattr(self.receta, 'costo_total_ingredientes', Decimal('0.00'))
        if costo_ingredientes > 0:
            ganancia = self.precio_unitario - costo_ingredientes
            return (ganancia / self.precio_unitario) * 100
        return Decimal('0.00')
    
    @property
    def resumen_detalle(self):
        """Resumen del detalle para mostrar"""
        return f"{self.nombre_producto_actual} x{self.cantidad} = {self.subtotal_formateado}"
    
    # 🎯 Métodos de negocio
    
    def actualizar_precio_desde_receta(self):
        """Actualiza el precio unitario con el precio actual de la receta"""
        if self.receta and hasattr(self.receta, 'precio'):
            self.precio_unitario = self.receta.precio
            return True
        return False
    
    def actualizar_nombre_desde_receta(self):
        """Actualiza el nombre con el nombre actual de la receta"""
        if self.receta and hasattr(self.receta, 'nombre'):
            self.nombre_empanada = self.receta.nombre
            return True
        return False
    
    def validar_disponibilidad_receta(self):
        """Valida que la receta esté disponible para venta"""
        if not self.receta:
            return False, "No se ha asociado una receta"
        
        if not self.disponibilidad_actual:
            return False, f"El producto '{self.nombre_producto_actual}' no está disponible"
        
        return True, "Producto disponible"
    
    def calcular_costo_total_ingredientes(self):
        """Calcula el costo total de ingredientes para esta cantidad"""
        if not self.receta:
            return Decimal('0.00')
        
        costo_unitario = getattr(self.receta, 'costo_total_ingredientes', Decimal('0.00'))
        return costo_unitario * self.cantidad
    
    def aplicar_descuento_porcentaje(self, porcentaje_descuento):
        """Aplica un descuento porcentual al precio unitario"""
        if 0 <= porcentaje_descuento <= 100:
            descuento = self.precio_unitario * (Decimal(str(porcentaje_descuento)) / 100)
            self.precio_unitario = self.precio_unitario - descuento
            return True
        return False
    
    def aplicar_descuento_monto(self, monto_descuento):
        """Aplica un descuento de monto fijo al precio unitario"""
        if 0 <= monto_descuento <= self.precio_unitario:
            self.precio_unitario = self.precio_unitario - Decimal(str(monto_descuento))
            return True
        return False
    
    # 🎯 Métodos estáticos
    
    @staticmethod
    def crear_detalle_desde_receta(venta, receta, cantidad):
        """Crea un detalle de venta basado en una receta"""
        detalle = DetalleVenta(
            venta=venta,
            receta=receta,
            cantidad=cantidad,
            precio_unitario=getattr(receta, 'precio', Decimal('0.00')),
            nombre_empanada=getattr(receta, 'nombre', 'Sin nombre')
        )
        return detalle
    
    @staticmethod
    def calcular_total_cantidad_venta(venta):
        """Calcula la cantidad total de productos en una venta"""
        return DetalleVenta.objects.filter(venta=venta).aggregate(
            total_cantidad=models.Sum('cantidad')
        )['total_cantidad'] or 0
    
    @staticmethod
    def obtener_productos_mas_vendidos(fecha_inicio=None, fecha_fin=None, limite=10):
        """Obtiene estadísticas de productos más vendidos"""
        queryset = DetalleVenta.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(venta__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(venta__fecha__lte=fecha_fin)
        
        return queryset.values('receta__nombre').annotate(
            total_cantidad=models.Sum('cantidad'),
            total_ventas=models.Count('id_detalle'),
            total_ingresos=models.Sum(models.F('cantidad') * models.F('precio_unitario'))
        ).order_by('-total_cantidad')[:limite]
    
    @staticmethod
    def obtener_ingresos_por_producto(fecha_inicio=None, fecha_fin=None):
        """Obtiene ingresos generados por cada producto"""
        queryset = DetalleVenta.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(venta__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(venta__fecha__lte=fecha_fin)
        
        return queryset.values('receta__nombre', 'receta__id_receta').annotate(
            total_ingresos=models.Sum(models.F('cantidad') * models.F('precio_unitario')),
            total_cantidad=models.Sum('cantidad'),
            precio_promedio=models.Avg('precio_unitario')
        ).order_by('-total_ingresos')
    
    def clean(self):
        """Validaciones adicionales"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        if self.precio_unitario < 0:
            raise ValidationError({'precio_unitario': 'El precio unitario no puede ser negativo'})
        
        # Validar disponibilidad de la receta
        es_valido, mensaje = self.validar_disponibilidad_receta()
        if not es_valido:
            raise ValidationError({'receta': mensaje})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Actualizar nombre y precio desde receta si están vacíos
        if not self.nombre_empanada and self.receta:
            self.actualizar_nombre_desde_receta()
        
        if self.precio_unitario == 0 and self.receta:
            self.actualizar_precio_desde_receta()
        
        # Validar antes de guardar
        self.full_clean()
        
        # Guardar el detalle
        super().save(*args, **kwargs)
        
        # Recalcular total de la venta después de guardar
        if self.venta:
            self.venta.recalcular_total()
            self.venta.save()


class VentaProduccion(models.Model):
    """
    Modelo de Venta-Producción del sistema PAE
    Migrado desde venta_produccion.java
    
    Representa la relación entre una venta y las órdenes de producción necesarias
    para cumplir con esa venta. Conecta el flujo comercial con el productivo.
    """
    
    # Campos del modelo (equivalentes a venta_produccion.java)
    id_ven_prod = models.AutoField(
        primary_key=True,
        db_column='idVenProd',
        verbose_name='ID Venta-Producción'
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Cantidad de productos asociados entre la venta y producción'
    )
    
    # Campos históricos para nombres (como en Java)
    nombre_produccion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre Producción',
        help_text='Nombre descriptivo de la producción (histórico)'
    )
    
    nombre_venta = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Nombre Venta',
        help_text='Nombre descriptivo de la venta (histórico)'
    )
    
    # Relaciones
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.DO_NOTHING,
        db_column='id_venta',
        verbose_name='Venta',
        help_text='Venta asociada',
        related_name='producciones_asociadas'
    )
    
    produccion = models.ForeignKey(
        'produccion.Produccion',
        on_delete=models.DO_NOTHING,
        db_column='id_produccion',
        verbose_name='Producción',
        help_text='Orden de producción asociada',
        related_name='ventas_asociadas'
    )
    
    class Meta:
        db_table = 'venta_produccion'
        verbose_name = 'Venta-Producción'
        verbose_name_plural = 'Ventas-Producciones'
        ordering = ['venta', 'produccion']
        unique_together = [['venta', 'produccion']]  # No duplicar la misma relación
        indexes = [
            models.Index(fields=['venta']),
            models.Index(fields=['produccion']),
            models.Index(fields=['venta', 'produccion']),
        ]
    
    def __str__(self):
        return f"VP-{self.id_ven_prod} | Venta #{self.venta.id_ven if self.venta else 'N/A'} → Prod #{self.produccion.id_proc if self.produccion else 'N/A'} (x{self.cantidad})"
    
    # 🧍 Propiedades auxiliares
    @property
    def numero_venta(self):
        """Número de la venta asociada"""
        return self.venta.id_ven if self.venta else None
    
    @property
    def numero_produccion(self):
        """Número de la producción asociada"""
        return self.produccion.id_proc if self.produccion else None
    
    @property
    def estado_venta(self):
        """Estado actual de la venta"""
        return self.venta.estado if self.venta else "Sin venta"
    
    @property
    def estado_produccion(self):
        """Estado actual de la producción"""
        return self.produccion.estado if self.produccion else "Sin producción"
    
    @property
    def cliente_venta(self):
        """Cliente de la venta asociada"""
        if self.venta and self.venta.cliente:
            return self.venta.cliente.nombre
        return "Sin cliente"
    
    @property
    def empleado_produccion(self):
        """Empleado asignado a la producción"""
        if self.produccion and self.produccion.usuario_asignado:
            return f"{self.produccion.usuario_asignado.nombres} {self.produccion.usuario_asignado.apellidos}"
        return "Sin asignar"
    
    @property
    def fecha_venta(self):
        """Fecha de la venta"""
        return self.venta.fecha if self.venta else None
    
    @property
    def fecha_produccion(self):
        """Fecha de la producción"""
        return self.produccion.fecha_hora if self.produccion else None
    
    @property
    def valor_venta(self):
        """Valor total de la venta"""
        return self.venta.total if self.venta else Decimal('0.00')
    
    @property
    def valor_produccion_estimado(self):
        """Valor estimado de la producción"""
        if self.produccion:
            return self.produccion.calcular_valor_total_detalles()
        return Decimal('0.00')
    
    @property
    def sincronizacion_estados(self):
        """Verifica si los estados están sincronizados correctamente"""
        if not self.venta or not self.produccion:
            return "Datos incompletos"
        
        estado_venta = self.estado_venta
        estado_produccion = self.estado_produccion
        
        # Lógica de sincronización esperada
        if estado_venta == "Confirmada" and estado_produccion in ["Pendiente", "Asignada"]:
            return "Sincronizado"
        elif estado_venta == "En Preparacion" and estado_produccion == "En Proceso":
            return "Sincronizado"
        elif estado_venta == "Lista" and estado_produccion == "Finalizada":
            return "Sincronizado"
        elif estado_venta == "Entregada" and estado_produccion == "Finalizada":
            return "Completado"
        elif estado_venta == "Cancelada" or estado_produccion == "Cancelada":
            return "Cancelado"
        else:
            return "Desincronizado"
    
    @property
    def tiempo_entre_venta_produccion(self):
        """Tiempo transcurrido entre venta y producción"""
        if self.fecha_venta and self.fecha_produccion:
            delta = self.fecha_produccion - self.fecha_venta
            days = delta.days
            hours = delta.seconds // 3600
            
            if days > 0:
                return f"{days} días"
            elif hours > 0:
                return f"{hours} horas"
            else:
                return "Menos de 1 hora"
        return "N/A"
    
    @property
    def progreso_cumplimiento(self):
        """Porcentaje de progreso del cumplimiento venta→producción"""
        estado_prod = self.estado_produccion
        
        estados_progreso = {
            "Pendiente": 10,
            "Asignada": 25,
            "En Proceso": 50,
            "Finalizada": 100,
            "Cancelada": 0
        }
        
        return estados_progreso.get(estado_prod, 0)
    
    @property
    def requiere_atencion(self):
        """Verifica si la relación requiere atención especial"""
        sincro = self.sincronizacion_estados
        if sincro in ["Desincronizado", "Datos incompletos"]:
            return True
        
        # Verificar retrasos
        if self.fecha_venta and self.fecha_produccion:
            delta = timezone.now() - self.fecha_venta
            if delta.days > 2 and self.estado_produccion == "Pendiente":
                return True
        
        return False
    
    @property
    def color_estado(self):
        """Color para mostrar según sincronización"""
        sincro = self.sincronizacion_estados
        colores = {
            "Sincronizado": "green",
            "Completado": "darkgreen",
            "Desincronizado": "red",
            "Cancelado": "gray",
            "Datos incompletos": "orange"
        }
        return colores.get(sincro, "black")
    
    @property
    def resumen_relacion(self):
        """Resumen de la relación para mostrar"""
        return f"Venta #{self.numero_venta} ({self.estado_venta}) → Prod #{self.numero_produccion} ({self.estado_produccion}) | {self.sincronizacion_estados}"
    
    # 🎯 Métodos de negocio
    
    def sincronizar_estados_automatico(self):
        """Sincroniza automáticamente los estados entre venta y producción"""
        if not self.venta or not self.produccion:
            return False, "Datos incompletos"
        
        # Lógica de sincronización automática
        cambios = []
        
        # Si la venta se confirma, asignar la producción
        if self.estado_venta == "Confirmada" and self.estado_produccion == "Pendiente":
            # Aquí se podría implementar auto-asignación
            cambios.append("Producción lista para asignación")
        
        # Si la producción se finaliza, marcar venta como lista
        if self.estado_produccion == "Finalizada" and self.estado_venta == "En Preparacion":
            self.venta.estado = "Lista"
            self.venta.save()
            cambios.append("Venta marcada como Lista")
        
        # Si la venta se cancela, cancelar producción
        if self.estado_venta == "Cancelada" and self.estado_produccion not in ["Finalizada", "Cancelada"]:
            self.produccion.estado = "Cancelada"
            self.produccion.save()
            cambios.append("Producción cancelada")
        
        return True, "; ".join(cambios) if cambios else "Sin cambios necesarios"
    
    def validar_coherencia_cantidad(self):
        """Valida que las cantidades sean coherentes"""
        if not self.venta or not self.produccion:
            return False, "Datos incompletos"
        
        # Obtener cantidades de detalles de venta
        cantidad_venta = DetalleVenta.objects.filter(venta=self.venta).aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
        
        # Obtener cantidades de detalles de producción
        from modelos.produccion.models import ProduccionReceta
        cantidad_produccion = ProduccionReceta.objects.filter(produccion=self.produccion).aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
        
        if self.cantidad != cantidad_venta or self.cantidad != cantidad_produccion:
            return False, f"Inconsistencia: VP={self.cantidad}, Venta={cantidad_venta}, Prod={cantidad_produccion}"
        
        return True, "Cantidades coherentes"
    
    def actualizar_nombres_historicos(self):
        """Actualiza los nombres históricos desde los modelos relacionados"""
        if self.venta:
            self.nombre_venta = f"Venta #{self.venta.id_ven} - {self.cliente_venta}"
        
        if self.produccion:
            self.nombre_produccion = f"Producción #{self.produccion.id_proc} - {self.estado_produccion}"
        
        return True
    
    def calcular_tiempo_cumplimiento(self):
        """Calcula el tiempo total desde venta hasta finalización de producción"""
        if not self.fecha_venta:
            return None
        
        if self.estado_produccion == "Finalizada" and self.produccion.fecha_finalizacion:
            delta = self.produccion.fecha_finalizacion - self.fecha_venta
            return delta
        
        # Si no está finalizada, tiempo actual
        delta = timezone.now() - self.fecha_venta
        return delta
    
    # 🎯 Métodos estáticos
    
    @staticmethod
    def crear_relacion(venta, produccion, cantidad):
        """Crea una nueva relación venta-producción"""
        relacion = VentaProduccion(
            venta=venta,
            produccion=produccion,
            cantidad=cantidad
        )
        
        # Actualizar nombres históricos
        relacion.actualizar_nombres_historicos()
        
        # Validar coherencia
        relacion.save()
        
        # Sincronizar estados inicialmente
        relacion.sincronizar_estados_automatico()
        
        return relacion
    
    @staticmethod
    def obtener_producciones_por_venta(venta):
        """Obtiene todas las producciones asociadas a una venta"""
        return VentaProduccion.objects.filter(venta=venta).select_related('produccion')
    
    @staticmethod
    def obtener_ventas_por_produccion(produccion):
        """Obtiene todas las ventas asociadas a una producción"""
        return VentaProduccion.objects.filter(produccion=produccion).select_related('venta')
    
    @staticmethod
    def obtener_relaciones_desincronizadas():
        """Obtiene relaciones que requieren atención"""
        relaciones = VentaProduccion.objects.all()
        desincronizadas = []
        
        for relacion in relaciones:
            if relacion.requiere_atencion:
                desincronizadas.append(relacion)
        
        return desincronizadas
    
    @staticmethod
    def generar_reporte_sincronizacion(fecha_inicio=None, fecha_fin=None):
        """Genera reporte de sincronización de estados"""
        queryset = VentaProduccion.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(venta__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(venta__fecha__lte=fecha_fin)
        
        reporte = {
            'sincronizados': 0,
            'desincronizados': 0,
            'completados': 0,
            'cancelados': 0,
            'total': queryset.count()
        }
        
        for relacion in queryset:
            sincro = relacion.sincronizacion_estados
            if sincro == "Sincronizado":
                reporte['sincronizados'] += 1
            elif sincro == "Desincronizado":
                reporte['desincronizados'] += 1
            elif sincro == "Completado":
                reporte['completados'] += 1
            elif sincro == "Cancelado":
                reporte['cancelados'] += 1
        
        return reporte
    
    def clean(self):
        """Validaciones adicionales"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        # Validar coherencia de cantidades
        es_valido, mensaje = self.validar_coherencia_cantidad()
        if not es_valido and "Datos incompletos" not in mensaje:
            raise ValidationError({'cantidad': mensaje})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Actualizar nombres históricos
        self.actualizar_nombres_historicos()
        
        # Validar antes de guardar
        self.full_clean()
        
        # Guardar la relación
        super().save(*args, **kwargs)
        
        # Sincronizar estados después de guardar
        self.sincronizar_estados_automatico()


class VentaReceta(models.Model):
    """
    Modelo de Venta-Recetas del sistema PAE
    Migrado desde venta_recetas.java
    
    Representa la relación específica entre ventas y recetas con información
    de trazabilidad adicional. Complementa DetalleVenta con funciones específicas
    de seguimiento y análisis de recetas vendidas.
    """
    
    # Campos del modelo (equivalentes a venta_recetas.java)
    id_venta_receta = models.AutoField(
        primary_key=True,
        db_column='id_venta_receta',
        verbose_name='ID Venta-Receta'
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Cantidad de recetas vendidas'
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Precio',
        help_text='Precio de la receta al momento de la venta',
        default=Decimal('0.00')
    )
    
    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Subtotal',
        help_text='Subtotal calculado (cantidad × precio)',
        default=Decimal('0.00')
    )
    
    # Campos históricos para nombres (como en Java) - DESHABILITADOS (no existen en tabla real)
    # nombre_receta = models.CharField(
    #     max_length=200,
    #     blank=True,
    #     verbose_name='Nombre Receta',
    #     help_text='Nombre de la receta al momento de la venta (histórico)'
    # )
    # 
    # nombre_venta = models.CharField(
    #     max_length=200,
    #     blank=True,
    #     verbose_name='Nombre Venta',
    #     help_text='Identificación de la venta (histórico)'
    # )
    
    # Relaciones
    venta = models.ForeignKey(
        'Venta',
        on_delete=models.CASCADE,
        db_column='id_venta',
        verbose_name='Venta',
        help_text='Venta asociada',
        related_name='recetas_asociadas'
    )
    
    receta = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.DO_NOTHING,
        db_column='id_receta',
        verbose_name='Receta',
        help_text='Receta vendida',
        related_name='ventas_asociadas'
    )
    
    class Meta:
        db_table = 'venta_recetas'
        managed = False  # No crear/modificar tabla existente
        verbose_name = 'Venta-Receta'
        verbose_name_plural = 'Ventas-Recetas'
        ordering = ['venta', 'receta']
    
    def __str__(self):
        return f"VR-{self.id_venta_receta} | Venta #{self.numero_venta} → {self.nombre_receta_actual} x{self.cantidad} = {self.subtotal_formateado}"
    
    # 🧍 Propiedades auxiliares
    @property
    def numero_venta(self):
        """Número de la venta asociada"""
        return self.venta.id_ven if self.venta else None
    
    @property
    def nombre_receta_actual(self):
        """Nombre actual de la receta (prioriza histórico, luego actual)"""
        return self.nombre_receta if self.nombre_receta else (self.receta.nombre if self.receta else "Sin receta")
    
    @property
    def precio_actual_receta(self):
        """Precio actual de la receta"""
        return self.receta.precio if self.receta else Decimal('0.00')
    
    @property
    def subtotal_calculado(self):
        """Subtotal calculado automáticamente"""
        return self.cantidad * self.precio
    
    @property
    def subtotal_formateado(self):
        """Subtotal formateado como moneda"""
        return f"${self.subtotal:,.0f}"
    
    @property
    def precio_formateado(self):
        """Precio formateado como moneda"""
        return f"${self.precio:,.0f}"
    
    @property
    def diferencia_precio_actual(self):
        """Diferencia entre precio vendido y precio actual"""
        return self.precio - self.precio_actual_receta
    
    @property
    def porcentaje_diferencia_precio(self):
        """Porcentaje de diferencia de precio"""
        if self.precio_actual_receta > 0:
            return ((self.precio - self.precio_actual_receta) / self.precio_actual_receta) * 100
        return Decimal('0.00')
    
    @property
    def cliente_venta(self):
        """Cliente de la venta asociada"""
        if self.venta and self.venta.cliente:
            return self.venta.cliente.nombre
        return "Sin cliente"
    
    @property
    def fecha_venta(self):
        """Fecha de la venta"""
        return self.venta.fecha if self.venta else None
    
    @property
    def estado_venta(self):
        """Estado de la venta"""
        return self.venta.estado if self.venta else "Sin estado"
    
    @property
    def categoria_receta(self):
        """Categoría de la receta"""
        return getattr(self.receta, 'categoria', 'Sin categoría') if self.receta else 'Sin categoría'
    
    @property
    def disponibilidad_actual_receta(self):
        """Disponibilidad actual de la receta"""
        if not self.receta:
            return False
        return getattr(self.receta, 'esta_disponible', True)
    
    @property
    def costo_ingredientes_unitario(self):
        """Costo de ingredientes por unidad"""
        if self.receta and hasattr(self.receta, 'costo_total_ingredientes'):
            return getattr(self.receta, 'costo_total_ingredientes', Decimal('0.00'))
        return Decimal('0.00')
    
    @property
    def costo_ingredientes_total(self):
        """Costo total de ingredientes para esta cantidad"""
        return self.costo_ingredientes_unitario * self.cantidad
    
    @property
    def margen_ganancia(self):
        """Margen de ganancia obtenido"""
        if self.subtotal > 0 and self.costo_ingredientes_total > 0:
            ganancia = self.subtotal - self.costo_ingredientes_total
            return (ganancia / self.subtotal) * 100
        return Decimal('0.00')
    
    @property
    def porcentaje_total_venta(self):
        """Porcentaje que representa del total de la venta"""
        if self.venta and self.venta.total > 0:
            return (self.subtotal / self.venta.total) * 100
        return Decimal('0.00')
    
    @property
    def tiempo_desde_venta(self):
        """Tiempo transcurrido desde la venta"""
        if self.fecha_venta:
            delta = timezone.now() - self.fecha_venta
            days = delta.days
            hours = delta.seconds // 3600
            
            if days > 0:
                return f"{days} días"
            elif hours > 0:
                return f"{hours} horas"
            else:
                return "Menos de 1 hora"
        return "N/A"
    
    @property
    def es_precio_promocional(self):
        """Verifica si se vendió con precio promocional"""
        return self.precio < self.precio_actual_receta
    
    @property
    def resumen_venta_receta(self):
        """Resumen de la venta-receta"""
        promocion = " (Promoción)" if self.es_precio_promocional else ""
        return f"{self.nombre_receta_actual} x{self.cantidad} = {self.subtotal_formateado}{promocion}"
    
    # 🎯 Métodos de negocio
    
    def calcular_subtotal_automatico(self):
        """Calcula el subtotal automáticamente"""
        self.subtotal = self.subtotal_calculado
        return self.subtotal
    
    def actualizar_desde_receta(self):
        """Actualiza precio y nombre desde la receta actual"""
        if self.receta:
            self.precio = self.receta.precio
            self.nombre_receta = self.receta.nombre
            self.calcular_subtotal_automatico()
            return True
        return False
    
    def actualizar_nombres_historicos(self):
        """Actualiza los nombres históricos - DESHABILITADO (campos no existen)"""
        # if self.receta:
        #     self.nombre_receta = self.receta.nombre
        # 
        # if self.venta:
        #     self.nombre_venta = f"Venta #{self.venta.id_ven} - {self.cliente_venta}"
        
        return True
    
    def validar_coherencia_precio(self):
        """Valida que el precio sea coherente"""
        if self.precio <= 0:
            return False, "El precio debe ser mayor a cero"
        
        # Verificar si el precio es muy diferente al actual (más del 50% de diferencia)
        if self.precio_actual_receta > 0:
            diferencia_porcentual = abs(self.porcentaje_diferencia_precio)
            if diferencia_porcentual > 50:
                return False, f"Precio muy diferente al actual ({diferencia_porcentual:.1f}% de diferencia)"
        
        return True, "Precio válido"
    
    def aplicar_descuento_porcentual(self, porcentaje):
        """Aplica un descuento porcentual"""
        if 0 <= porcentaje <= 100:
            descuento = self.precio * (Decimal(str(porcentaje)) / 100)
            self.precio = self.precio - descuento
            self.calcular_subtotal_automatico()
            return True, f"Descuento del {porcentaje}% aplicado"
        return False, "Porcentaje de descuento inválido"
    
    def aplicar_precio_promocional(self, nuevo_precio):
        """Aplica un precio promocional"""
        if nuevo_precio > 0 and nuevo_precio <= self.precio_actual_receta:
            self.precio = Decimal(str(nuevo_precio))
            self.calcular_subtotal_automatico()
            return True, f"Precio promocional ${nuevo_precio:,.0f} aplicado"
        return False, "Precio promocional inválido"
    
    # 🎯 Métodos estáticos
    
    @staticmethod
    def crear_desde_detalle_venta(detalle_venta):
        """Crea una VentaReceta desde un DetalleVenta existente"""
        venta_receta = VentaReceta(
            venta=detalle_venta.venta,
            receta=detalle_venta.receta,
            cantidad=detalle_venta.cantidad,
            precio=detalle_venta.precio_unitario,
            nombre_receta=detalle_venta.nombre_empanada
        )
        venta_receta.calcular_subtotal_automatico()
        venta_receta.actualizar_nombres_historicos()
        
        return venta_receta
    
    @staticmethod
    def sincronizar_con_detalles_venta(venta):
        """Sincroniza VentaRecetas con DetalleVenta de una venta"""
        # Eliminar VentaRecetas que no tienen DetalleVenta correspondiente
        detalles_existentes = DetalleVenta.objects.filter(venta=venta).values_list('receta_id', flat=True)
        VentaReceta.objects.filter(venta=venta).exclude(receta_id__in=detalles_existentes).delete()
        
        # Crear/actualizar VentaRecetas desde DetalleVenta
        for detalle in DetalleVenta.objects.filter(venta=venta):
            venta_receta, created = VentaReceta.objects.get_or_create(
                venta=venta,
                receta=detalle.receta,
                defaults={
                    'cantidad': detalle.cantidad,
                    'precio': detalle.precio_unitario,
                    'nombre_receta': detalle.nombre_empanada
                }
            )
            
            if not created:
                # Actualizar si ya existe
                venta_receta.cantidad = detalle.cantidad
                venta_receta.precio = detalle.precio_unitario
                venta_receta.nombre_receta = detalle.nombre_empanada
                venta_receta.calcular_subtotal_automatico()
                venta_receta.save()
        
        return VentaReceta.objects.filter(venta=venta).count()
    
    @staticmethod
    def obtener_recetas_mas_vendidas(fecha_inicio=None, fecha_fin=None, limite=10):
        """Obtiene las recetas más vendidas según VentaRecetas"""
        queryset = VentaReceta.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(venta__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(venta__fecha__lte=fecha_fin)
        
        return queryset.values('receta__nombre', 'receta_id').annotate(
            total_cantidad=models.Sum('cantidad'),
            total_ventas=models.Count('id_venta_receta'),
            total_ingresos=models.Sum('subtotal'),
            precio_promedio=models.Avg('precio')
        ).order_by('-total_cantidad')[:limite]
    
    @staticmethod
    def generar_reporte_margenes(fecha_inicio=None, fecha_fin=None):
        """Genera reporte de márgenes de ganancia"""
        queryset = VentaReceta.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(venta__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(venta__fecha__lte=fecha_fin)
        
        reporte = {
            'total_ventas': queryset.count(),
            'ingresos_totales': queryset.aggregate(total=models.Sum('subtotal'))['total'] or Decimal('0.00'),
            'cantidad_total': queryset.aggregate(total=models.Sum('cantidad'))['total'] or 0,
            'precio_promedio': queryset.aggregate(promedio=models.Avg('precio'))['promedio'] or Decimal('0.00'),
            'recetas_unicas': queryset.values('receta').distinct().count()
        }
        
        return reporte
    
    @staticmethod
    def obtener_precios_historicos_receta(receta):
        """Obtiene historial de precios de una receta específica"""
        return VentaReceta.objects.filter(receta=receta).values(
            'precio', 'venta__fecha'
        ).order_by('-venta__fecha')
    
    def clean(self):
        """Validaciones adicionales"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        # No necesitamos validar precio aquí ya que el MinValueValidator lo hace
        # if self.precio <= Decimal('0'):
        #     raise ValidationError({'precio': 'El precio debe ser mayor a cero'})
        
        # Validar coherencia del precio
        try:
            es_valido, mensaje = self.validar_coherencia_precio()
            if not es_valido:
                raise ValidationError({'precio': mensaje})
        except:
            # Si hay error en validar_coherencia_precio, continuar
            pass
        
        # Validar que el subtotal calculado coincida
        try:
            if abs(self.subtotal - self.subtotal_calculado) > Decimal('0.01'):
                self.subtotal = self.subtotal_calculado
        except:
            # Si hay error calculando subtotal, usar cálculo simple
            self.subtotal = self.cantidad * self.precio
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Calcular subtotal automáticamente
        self.calcular_subtotal_automatico()
        
        # Actualizar nombres históricos si están vacíos - DESHABILITADO (campos no existen)
        # if not self.nombre_receta or not self.nombre_venta:
        #     self.actualizar_nombres_historicos()
        
        # Validar antes de guardar
        self.full_clean()
        
        # Guardar la relación
        super().save(*args, **kwargs)
