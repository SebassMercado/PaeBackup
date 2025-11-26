from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal


class Produccion(models.Model):
    """
    Modelo de Producción del sistema PAE
    Migrado desde produccion.java
    
    Maneja las órdenes de producción de productos/recetas en la panadería.
    Incluye workflow completo: creación -> asignación -> aceptación -> finalización
    """
    
    # Opciones para estado de producción
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aceptada', 'Aceptada'),
        ('Esperando insumos', 'Esperando insumos'),
        ('Finalizada', 'Finalizada'),
    ]
    
    # Campos del modelo (equivalentes a produccion.java)
    id_proc = models.AutoField(
        primary_key=True,
        db_column='id_proc',
        verbose_name='ID Producción'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='Pendiente',
        verbose_name='Estado',
        help_text='Estado actual de la orden de producción'
    )
    
    fecha_hora = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha y Hora de Creación',
        help_text='Cuando se creó la orden de producción'
    )
    
    fecha_aceptacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Aceptación',
        help_text='Cuando el empleado aceptó la orden'
    )
    
    fecha_finalizacion = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Finalización',
        help_text='Cuando se completó la producción'
    )
    
    # Relaciones con otros modelos
    receta = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.CASCADE,
        db_column='idReceta',
        verbose_name='Receta',
        help_text='Producto/receta a producir',
        related_name='producciones'
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Cantidad',
        help_text='Cantidad de productos a producir',
        default=Decimal('1.00')
    )
    
    # Usuario que crea la producción (Admin o Empleado Ventas)
    usuario_creador = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        db_column='id_usu',
        verbose_name='Usuario Creador',
        help_text='Usuario que creó la orden de producción',
        related_name='producciones_creadas'
    )
    
    # Usuario asignado para ejecutar la producción (Empleado Producción)
    usuario_asignado = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        db_column='id_asignado',
        verbose_name='Usuario Asignado',
        help_text='Empleado de producción asignado',
        related_name='producciones_asignadas',
        limit_choices_to={'rol': 'EP'}  # Solo empleados de producción
    )

    observacion = models.TextField(
        db_column='observacion',
        null=True,
        blank=True,
        verbose_name='Observación',
        help_text='Observación registrada al finalizar la producción'
    )
    
    class Meta:
        db_table = 'produccion'
        verbose_name = 'Producción'
        verbose_name_plural = 'Producciones'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_hora']),
            models.Index(fields=['usuario_asignado', 'estado']),
            models.Index(fields=['receta']),
        ]
    
    def __str__(self):
        return f"Producción {self.id_proc} - {self.receta.nombre} ({self.cantidad}) - {self.estado}"
    
    # 🧍 Propiedades auxiliares (equivalentes a campos auxiliares en Java)
    @property
    def nombre_usuario(self):
        """Nombre del usuario que creó la producción"""
        return self.usuario_creador.nombres if self.usuario_creador else ""
    
    @property
    def apellido_usuario(self):
        """Apellido del usuario que creó la producción"""
        return self.usuario_creador.apellidos if self.usuario_creador else ""
    
    @property
    def nombre_asignado(self):
        """Nombre del empleado asignado"""
        return self.usuario_asignado.nombres if self.usuario_asignado else ""
    
    @property
    def apellido_asignado(self):
        """Apellido del empleado asignado"""
        return self.usuario_asignado.apellidos if self.usuario_asignado else ""
    
    @property
    def nombre_completo_creador(self):
        """Nombre completo del usuario creador"""
        return f"{self.nombre_usuario} {self.apellido_usuario}".strip()
    
    @property
    def nombre_completo_asignado(self):
        """Nombre completo del empleado asignado"""
        return f"{self.nombre_asignado} {self.apellido_asignado}".strip()
    
    @property
    def nombre_receta(self):
        """Nombre de la receta a producir"""
        return self.receta.nombre if self.receta else "Sin receta"
    
    @property
    def tiempo_transcurrido(self):
        """Tiempo transcurrido desde la creación"""
        now = timezone.now()
        delta = now - self.fecha_hora
        
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
    def tiempo_produccion(self):
        """Tiempo que tomó la producción (si está finalizada)"""
        if self.fecha_finalizacion and self.fecha_aceptacion:
            delta = self.fecha_finalizacion - self.fecha_aceptacion
            hours = delta.seconds // 3600
            minutes = (delta.seconds % 3600) // 60
            return f"{delta.days}d {hours}h {minutes}m" if delta.days > 0 else f"{hours}h {minutes}m"
        return None
    
    @property
    def status_color(self):
        """Color para mostrar en interfaz según el estado"""
        colors = {
            'Pendiente': 'orange',
            'Aceptada': 'blue',
            'Esperando insumos': 'purple',
            'Finalizada': 'green',
        }
        return colors.get(self.estado, 'gray')
    
    @property
    def puede_aceptar(self):
        """Verifica si la producción puede ser aceptada"""
        return self.estado == 'Pendiente'
    
    @property
    def puede_finalizar(self):
        """Verifica si la producción puede ser finalizada"""
        return self.estado in ['Aceptada', 'Esperando insumos']
    
    @property
    def puede_cancelar(self):
        """Verifica si la producción puede ser cancelada (solo mientras no esté finalizada)"""
        return self.estado in ['Pendiente', 'Aceptada', 'Esperando insumos']
    
    @property
    def costo_estimado(self):
        """Calcula el costo estimado de producción basado en la receta"""
        if self.receta:
            costo_receta = self.receta.costo_total
            return costo_receta * self.cantidad
        return Decimal('0.00')
    
    @property
    def valor_estimado(self):
        """Calcula el valor estimado del producto terminado"""
        if self.receta:
            precio_receta = self.receta.precio
            return precio_receta * self.cantidad
        return Decimal('0.00')
    
    @property
    def ganancia_estimada(self):
        """Calcula la ganancia estimada"""
        return self.valor_estimado - self.costo_estimado
    
    # 🎯 Métodos de lógica de negocio
    
    def asignar_empleado(self, empleado):
        """Asigna un empleado de producción a la orden (no cambia estado)"""
        if empleado.rol != 'EP':
            raise ValueError("Solo se puede asignar empleados de producción")
        if self.estado != 'Pendiente':
            raise ValueError("Solo se puede asignar empleado cuando está 'Pendiente'")
        self.usuario_asignado = empleado
    
    def aceptar_produccion(self):
        """Acepta la producción (pasa a 'Aceptada')"""
        if not self.puede_aceptar:
            raise ValueError(f"No se puede aceptar en estado '{self.estado}'")
        self.fecha_aceptacion = timezone.now()
        self.estado = 'Aceptada'

    def marcar_esperando_insumos(self):
        """Marca la producción como esperando insumos"""
        if self.estado != 'Aceptada':
            raise ValueError("Solo se puede pasar a 'Esperando insumos' desde 'Aceptada'")
        self.estado = 'Esperando insumos'
    
    def finalizar_produccion(self, observacion=None, descontar_insumos=False):
        """Finaliza la producción. Permite guardar observación y descontar insumos.
        descontar_insumos: bool (se usa en lógica externa; aquí solo registra observación)."""
        if not self.puede_finalizar:
            raise ValueError(f"No se puede finalizar en estado '{self.estado}'")
        self.estado = 'Finalizada'
        self.fecha_finalizacion = timezone.now()
        if observacion:
            self.observacion = (observacion or '').strip()[:2000]
    
    def cancelar_produccion(self, motivo=""):
        """Cancela la producción (se fuerza estado 'Pendiente' → no implementado en enum, se deja sin efecto)"""
        if not self.puede_cancelar:
            raise ValueError(f"No se puede cancelar en estado '{self.estado}'")
        # Como no existe 'Cancelada' en enum actual, se podría optar por revertir a 'Pendiente' o lanzar excepción.
        self.estado = 'Pendiente'
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        if self.fecha_aceptacion and self.fecha_aceptacion < self.fecha_hora:
            raise ValidationError({'fecha_aceptacion': 'La fecha de aceptación no puede ser anterior a la creación'})
        
        if self.fecha_finalizacion and self.fecha_aceptacion and self.fecha_finalizacion < self.fecha_aceptacion:
            raise ValidationError({'fecha_finalizacion': 'La fecha de finalización no puede ser anterior a la aceptación'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        self.full_clean()  # Ejecuta validaciones
        super().save(*args, **kwargs)
    
    def calcular_valor_total_detalles(self):
        """Calcula el valor total de todos los detalles de esta producción"""
        total = Decimal('0.00')
        for detalle in self.detalles_recetas.all():
            total += detalle.valor_total_produccion
        return total


class ProduccionReceta(models.Model):
    """
    Modelo de Producción-Recetas del sistema PAE
    Migrado desde produccion_recetas.java
    
    Representa la relación entre una orden de producción y las recetas que se van a producir,
    incluyendo las cantidades específicas de cada producto a elaborar.
    """
    
    # Campos del modelo (equivalentes a produccion_recetas.java)
    id_detalle = models.AutoField(
        primary_key=True,
        db_column='id_detalle',
        verbose_name='ID Detalle'
    )
    
    cantidad = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad',
        help_text='Cantidad de productos a producir'
    )
    
    # Relaciones
    produccion = models.ForeignKey(
        'Produccion',
        on_delete=models.CASCADE,
        db_column='id_produccion',
        verbose_name='Orden de Producción',
        help_text='Orden de producción a la que pertenece este detalle',
        related_name='detalles_recetas'
    )
    
    receta = models.ForeignKey(
        'recetas.Receta',
        on_delete=models.CASCADE,
        db_column='id_rec',
        verbose_name='Receta/Producto',
        help_text='Receta/producto a producir',
        related_name='detalles_produccion'
    )
    
    class Meta:
        db_table = 'produccion_recetas'
        verbose_name = 'Detalle de Producción'
        verbose_name_plural = 'Detalles de Producción'
        ordering = ['produccion', 'id_detalle']
        unique_together = [['produccion', 'receta']]  # No duplicar recetas en la misma orden
        indexes = [
            models.Index(fields=['produccion']),
            models.Index(fields=['receta']),
            models.Index(fields=['produccion', 'receta']),
        ]
    
    def __str__(self):
        return f"Detalle {self.id_detalle} - Orden {self.produccion.id_proc if self.produccion else 'N/A'} - {self.nombre_receta} x{self.cantidad}"
    
    # 🧍 Propiedades auxiliares
    @property
    def nombre_receta(self):
        """Nombre de la receta a producir"""
        return self.receta.nombre if self.receta else "Sin receta"
    
    @property
    def precio_unitario_receta(self):
        """Precio unitario de la receta"""
        return self.receta.precio if self.receta else Decimal('0.00')
    
    @property
    def valor_total_produccion(self):
        """Valor total de este detalle de producción"""
        return self.cantidad * self.precio_unitario_receta
    
    @property
    def valor_total_formateado(self):
        """Valor total formateado como moneda"""
        return f"${self.valor_total_produccion:,.0f}"
    
    @property
    def estado_produccion(self):
        """Estado de la orden de producción"""
        return self.produccion.estado if self.produccion else "Sin estado"
    
    @property
    def fecha_produccion(self):
        """Fecha de la orden de producción"""
        return self.produccion.fecha_hora if self.produccion else None
    
    @property
    def empleado_asignado(self):
        """Empleado asignado a la producción"""
        if self.produccion and self.produccion.usuario_asignado:
            return f"{self.produccion.usuario_asignado.nombres} {self.produccion.usuario_asignado.apellidos}"
        return "Sin asignar"
    
    @property
    def tiempo_estimado_total(self):
        """Tiempo estimado total para producir esta cantidad"""
        if self.receta and hasattr(self.receta, 'tiempo_preparacion'):
            tiempo_unitario = getattr(self.receta, 'tiempo_preparacion', 0)
            return tiempo_unitario * self.cantidad
        return 0
    
    @property
    def costo_ingredientes_total(self):
        """Costo total de ingredientes para esta cantidad"""
        if self.receta and hasattr(self.receta, 'costo_total_ingredientes'):
            costo_unitario = getattr(self.receta, 'costo_total_ingredientes', Decimal('0.00'))
            return costo_unitario * self.cantidad
        return Decimal('0.00')
    
    @property
    def margen_ganancia_estimado(self):
        """Margen de ganancia estimado"""
        if self.valor_total_produccion > 0 and self.costo_ingredientes_total > 0:
            ganancia = self.valor_total_produccion - self.costo_ingredientes_total
            return (ganancia / self.valor_total_produccion) * 100
        return Decimal('0.00')
    
    @property
    def porcentaje_orden_produccion(self):
        """Porcentaje que representa este detalle del total de la orden"""
        if self.produccion:
            total_orden = self.produccion.calcular_valor_total_detalles()
            if total_orden > 0:
                return (self.valor_total_produccion / total_orden) * 100
        return Decimal('0.00')
    
    @property
    def disponibilidad_ingredientes(self):
        """Verifica si hay ingredientes suficientes"""
        if not self.receta:
            return False
        
        # Verificar cada ingrediente de la receta
        from modelos.recetas.models import RecetaInsumo
        ingredientes = RecetaInsumo.objects.filter(receta=self.receta)
        
        for ingrediente in ingredientes:
            cantidad_necesaria = ingrediente.cantidad * self.cantidad
            stock_disponible = ingrediente.insumo.stock_actual
            
            if stock_disponible < cantidad_necesaria:
                return False
        
        return True
    
    @property
    def ingredientes_faltantes(self):
        """Lista de ingredientes que faltan"""
        if not self.receta:
            return []
        
        faltantes = []
        from modelos.recetas.models import RecetaInsumo
        ingredientes = RecetaInsumo.objects.filter(receta=self.receta)
        
        for ingrediente in ingredientes:
            cantidad_necesaria = ingrediente.cantidad * self.cantidad
            stock_disponible = ingrediente.insumo.stock_actual
            
            if stock_disponible < cantidad_necesaria:
                faltante = cantidad_necesaria - stock_disponible
                faltantes.append({
                    'insumo': ingrediente.insumo.nombre,
                    'necesario': cantidad_necesaria,
                    'disponible': stock_disponible,
                    'faltante': faltante,
                    'unidad': ingrediente.insumo.unidad_medida
                })
        
        return faltantes
    
    @property
    def resumen_detalle(self):
        """Resumen del detalle para mostrar"""
        estado_icon = "✅" if self.disponibilidad_ingredientes else "⚠️"
        return f"{estado_icon} {self.nombre_receta} x{self.cantidad} = {self.valor_total_formateado}"
    
    # 🎯 Métodos de negocio
    
    def validar_disponibilidad_receta(self):
        """Valida que la receta esté disponible"""
        if not self.receta:
            return False, "No se ha asociado una receta"
        
        if not getattr(self.receta, 'esta_disponible', True):
            return False, f"La receta '{self.nombre_receta}' no está disponible"
        
        return True, "Receta disponible"
    
    def validar_ingredientes_disponibles(self):
        """Valida que haya ingredientes suficientes"""
        if not self.disponibilidad_ingredientes:
            faltantes = self.ingredientes_faltantes
            if faltantes:
                mensaje = "Ingredientes insuficientes: "
                detalles = [f"{f['insumo']}: faltan {f['faltante']:.2f} {f['unidad']}" for f in faltantes[:3]]
                mensaje += ", ".join(detalles)
                if len(faltantes) > 3:
                    mensaje += f" y {len(faltantes) - 3} más"
                return False, mensaje
        
        return True, "Ingredientes disponibles"
    
    def calcular_tiempo_produccion(self):
        """Calcula el tiempo estimado de producción"""
        return self.tiempo_estimado_total
    
    def reservar_ingredientes(self):
        """Reserva los ingredientes necesarios para la producción"""
        if not self.disponibilidad_ingredientes:
            return False, "No hay ingredientes suficientes"
        
        from modelos.recetas.models import RecetaInsumo
        ingredientes = RecetaInsumo.objects.filter(receta=self.receta)
        reservados = []
        
        try:
            for ingrediente in ingredientes:
                cantidad_necesaria = ingrediente.cantidad * self.cantidad
                # Aquí se podría implementar lógica de reserva real
                reservados.append({
                    'insumo': ingrediente.insumo,
                    'cantidad_reservada': cantidad_necesaria
                })
            
            return True, f"Reservados {len(reservados)} ingredientes"
        
        except Exception as e:
            return False, f"Error al reservar ingredientes: {str(e)}"
    
    def liberar_ingredientes(self):
        """Libera los ingredientes reservados"""
        # Implementar lógica de liberación de reservas
        return True
    
    # 🎯 Métodos estáticos
    
    @staticmethod
    def crear_detalle(produccion, receta, cantidad):
        """Crea un nuevo detalle de producción con validaciones"""
        detalle = ProduccionReceta(
            produccion=produccion,
            receta=receta,
            cantidad=cantidad
        )
        
        # Validar receta disponible
        es_valido, mensaje = detalle.validar_disponibilidad_receta()
        if not es_valido:
            raise ValidationError(mensaje)
        
        # Validar ingredientes
        es_valido, mensaje = detalle.validar_ingredientes_disponibles()
        if not es_valido:
            raise ValidationError(mensaje)
        
        detalle.save()
        return detalle
    
    @staticmethod
    def calcular_total_cantidad_orden(produccion):
        """Calcula la cantidad total de productos en una orden"""
        return ProduccionReceta.objects.filter(produccion=produccion).aggregate(
            total=models.Sum('cantidad')
        )['total'] or 0
    
    @staticmethod
    def calcular_valor_total_orden(produccion):
        """Calcula el valor total de una orden de producción"""
        detalles = ProduccionReceta.objects.filter(produccion=produccion)
        return sum(detalle.valor_total_produccion for detalle in detalles)
    
    @staticmethod
    def obtener_recetas_mas_producidas(fecha_inicio=None, fecha_fin=None, limite=10):
        """Obtiene las recetas más producidas en un período"""
        queryset = ProduccionReceta.objects.all()
        
        if fecha_inicio:
            queryset = queryset.filter(produccion__fecha__gte=fecha_inicio)
        if fecha_fin:
            queryset = queryset.filter(produccion__fecha__lte=fecha_fin)
        
        return queryset.values('receta__nombre').annotate(
            total_cantidad=models.Sum('cantidad'),
            total_ordenes=models.Count('id_detalle'),
            valor_total=models.Sum(models.F('cantidad') * models.F('receta__precio'))
        ).order_by('-total_cantidad')[:limite]
    
    @staticmethod
    def verificar_capacidad_produccion(fecha_produccion, recetas_cantidades):
        """Verifica si hay capacidad para producir una lista de recetas"""
        # Implementar lógica de verificación de capacidad
        # Por ahora retorna True, pero se puede expandir
        return True, "Capacidad disponible"
    
    def clean(self):
        """Validaciones adicionales"""
        if self.cantidad <= 0:
            raise ValidationError({'cantidad': 'La cantidad debe ser mayor a cero'})
        
        # Validar disponibilidad de receta
        es_valido, mensaje = self.validar_disponibilidad_receta()
        if not es_valido:
            raise ValidationError({'receta': mensaje})
        
        # Opcional: Validar ingredientes (se puede deshabilitar para permitir producciones futuras)
        # es_valido, mensaje = self.validar_ingredientes_disponibles()
        # if not es_valido:
        #     raise ValidationError({'cantidad': mensaje})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Validar antes de guardar
        self.full_clean()
        
        # Guardar el detalle
        super().save(*args, **kwargs)
        
        # Recalcular totales de la orden de producción
        if self.produccion:
            # Se puede implementar recálculo automático aquí
            pass
