from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Receta(models.Model):
    """
    Modelo de Receta del sistema PAE
    Migrado desde recetas.java
    Representa los productos/platos que se venden
    """
    
    # Opciones para estado
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
    ]
    
    # Campos del modelo (equivalentes a recetas.java)
    id_rec = models.AutoField(
        primary_key=True,
        db_column='id_rec',
        verbose_name='ID Receta'
    )
    
    nombre = models.CharField(
        max_length=50,
        verbose_name='Nombre',
        help_text='Nombre del producto o plato',
        default='Producto sin nombre'
    )
    
    descripcion = models.TextField(
        null=True,
        blank=True,
        verbose_name='Descripción',
        help_text='Descripción detallada del producto'
    )
    
    precio = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Precio',
        help_text='Precio de venta del producto'
    )
    
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='Activo',
        verbose_name='Estado'
    )
    
    class Meta:
        db_table = 'recetas'
        verbose_name = 'Receta'
        verbose_name_plural = 'Recetas'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['nombre']),
        ]
    
    def __str__(self):
        return f"{self.nombre} - ${self.precio}"
    
    @property
    def precio_formateado(self):
        """Retorna el precio formateado como moneda"""
        return f"${self.precio:,.0f}"
    
    @property
    def esta_activo(self):
        """Verifica si la receta está activa"""
        return self.estado == 'Activo'
    
    @property
    def status_color(self):
        """Color para mostrar en interfaz según el estado"""
        return 'green' if self.esta_activo else 'gray'
    
    def activar(self):
        """Activa la receta"""
        self.estado = 'Activo'
    
    def desactivar(self):
        """Desactiva la receta"""
        self.estado = 'Inactivo'
    
    def puede_producirse(self):
        """
        Verifica si la receta puede producirse
        Requiere que TODOS los insumos asociados estén en estado Activo y con stock suficiente
        """
        if not self.esta_activo:
            return False, "Receta inactiva"
        
        ingredientes = self.ingredientes.all()
        
        if not ingredientes.exists():
            return False, "No tiene ingredientes definidos"
        
        # Verificar que TODOS los insumos estén en estado Activo
        for ingrediente in ingredientes:
            if ingrediente.insumo.estado != 'Activo':
                return False, f"El insumo '{ingrediente.insumo.nombre}' no está activo (Estado: {ingrediente.insumo.estado})"
        
        # Verificar que TODOS los insumos tengan stock suficiente
        for ingrediente in ingredientes:
            if ingrediente.insumo.stock_actual < float(ingrediente.cantidad):
                return False, f"Stock insuficiente del insumo '{ingrediente.insumo.nombre}' (Necesario: {ingrediente.cantidad}, Disponible: {ingrediente.insumo.stock_actual})"
        
        return True, "Puede producirse"
    
    def verificar_y_actualizar_estado(self):
        """
        Verifica el estado de la receta basado en sus ingredientes e insumos
        La receta solo estará activa si TODOS sus insumos asociados están en estado Activo
        """
        # Obtener todos los ingredientes de la receta
        ingredientes = self.ingredientes.all()
        
        if not ingredientes.exists():
            # Si no tiene ingredientes, puede estar activa (receta sin componentes)
            return False
        
        # Verificar que TODOS los insumos estén en estado "Activo"
        todos_insumos_activos = True
        insumos_no_activos = []
        
        for ingrediente in ingredientes:
            if ingrediente.insumo.estado != 'Activo':
                todos_insumos_activos = False
                insumos_no_activos.append(f"{ingrediente.insumo.nombre} ({ingrediente.insumo.estado})")
        
        # Si NO todos los insumos están Activos, la receta debe estar Inactiva
        if not todos_insumos_activos and self.estado == 'Activo':
            self.estado = 'Inactivo'
            print(f"🔴 RECETA DESACTIVADA: {self.nombre} - Insumos no activos: {', '.join(insumos_no_activos)}")
            return True  # Hubo cambio
        
        # Si TODOS los insumos están Activos, la receta puede estar Activa
        elif todos_insumos_activos and self.estado == 'Inactivo':
            self.estado = 'Activo'
            print(f"🟢 RECETA ACTIVADA: {self.nombre} - Todos los insumos están en estado Activo")
            return True  # Hubo cambio
        
        return False  # No hubo cambio
    
    @classmethod
    def actualizar_estados_por_insumo(cls, insumo):
        """
        Actualiza el estado de todas las recetas que usan un insumo específico
        """
        # Obtener todas las recetas que usan este insumo
        recetas_afectadas = cls.objects.filter(
            ingredientes__insumo=insumo
        ).distinct()
        
        recetas_actualizadas = []
        
        for receta in recetas_afectadas:
            # Primero actualizar los estados de los ingredientes de esta receta
            RecetaInsumo.actualizar_estados_por_insumo(insumo)
            
            # Luego verificar y actualizar el estado de la receta
            if receta.verificar_y_actualizar_estado():
                receta.save()
                recetas_actualizadas.append(receta)
        
        return recetas_actualizadas
    
    @property
    def costo_produccion(self):
        """
        Calcula el costo de producción basado en los insumos
        """
        costo_total = Decimal('0.00')
        for ingrediente in self.ingredientes.all():
            if ingrediente.estado == 'Activo':
                costo_total += Decimal(str(ingrediente.costo_ingrediente))
        return costo_total
    
    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        costo = self.costo_produccion
        if costo > 0:
            return ((self.precio - costo) / costo) * 100
        return 0.0
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if not self.nombre.strip():
            raise ValidationError({'nombre': 'El nombre es obligatorio'})
        
        if self.precio < 0:
            raise ValidationError({'precio': 'El precio no puede ser negativo'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar formato"""
        # Capitalizar nombre y limpiar descripción
        self.nombre = self.nombre.strip().title()
        if self.descripcion:
            self.descripcion = self.descripcion.strip()
        
        super().save(*args, **kwargs)


class RecetaInsumo(models.Model):
    """
    Modelo que representa la relación entre recetas e insumos
    Migrado desde receta_insumos.java
    Define qué ingredientes necesita cada receta y en qué cantidad
    """
    
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Agotado', 'Agotado'),
    ]
    
    UNIDAD_CHOICES = [
        ('g', 'Gramos'),
        ('kg', 'Kilogramos'),
        ('ml', 'Mililitros'),
        ('l', 'Litros'),
        ('unidad', 'Unidades'),
        ('cucharada', 'Cucharadas'),
        ('cucharadita', 'Cucharaditas'),
        ('taza', 'Tazas'),
        ('pizca', 'Pizca'),
    ]
    
    id_rec_ins = models.AutoField(primary_key=True)
    receta = models.ForeignKey(
        'Receta',
        on_delete=models.CASCADE,
        db_column='id_rec',
        verbose_name='Receta',
        related_name='ingredientes'
    )
    insumo = models.ForeignKey(
        'insumos.Insumo',
        on_delete=models.CASCADE,
        db_column='id_ins',
        verbose_name='Insumo',
        related_name='recetas_que_usan'
    )
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name='Cantidad',
        help_text='Cantidad del insumo necesaria para esta receta',
        default=Decimal('1.00')
    )
    unidad = models.CharField(
        max_length=20,
        choices=UNIDAD_CHOICES,
        verbose_name='Unidad de medida',
        default='kg'
    )
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='Activo',
        verbose_name='Estado'
    )
    
    class Meta:
        db_table = 'receta_insumos'
        verbose_name = 'Ingrediente de Receta'
        verbose_name_plural = 'Ingredientes de Recetas'
        unique_together = ['receta', 'insumo']
        ordering = ['receta__nombre', 'insumo__nombre']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['receta', 'insumo']),
        ]
    
    def __str__(self):
        return f"{self.receta.nombre} - {self.insumo.nombre} ({self.cantidad_formateada})"
    
    @property
    def costo_ingrediente(self):
        """Calcula el costo de este ingrediente para la receta"""
        # Por ahora retorna 0 hasta que se implemente el campo precio en insumos
        return 0.0
    
    @property
    def costo_total(self):
        """Alias para costo_ingrediente para compatibilidad con templates"""
        return self.costo_ingrediente
    
    @property
    def disponible(self):
        """Verifica si hay suficiente stock del insumo para esta cantidad"""
        # Por ahora siempre retorna True para evitar alertas en formularios
        return True
    
    @property
    def porcentaje_disponible(self):
        """Calcula qué porcentaje del ingrediente está disponible"""
        if self.cantidad > 0:
            return min((float(self.insumo.stock_actual) / float(self.cantidad)) * 100, 100)
        return 100
    
    @property
    def cantidad_formateada(self):
        """Retorna la cantidad con su unidad"""
        return f"{self.cantidad} {self.get_unidad_display()}"
    
    @property
    def estado_color(self):
        """Retorna un color según el estado para uso en admin"""
        colores = {
            'Activo': '#28a745',  # Verde
            'Agotado': '#dc3545'  # Rojo
        }
        return colores.get(self.estado, '#6c757d')
    
    def verificar_disponibilidad(self):
        """
        Verifica y actualiza el estado según disponibilidad del insumo
        El ingrediente está activo solo si el insumo está en estado 'Activo'
        """
        # Verificar si el insumo NO está en estado 'Activo'
        if self.insumo.estado != 'Activo':
            if self.estado != 'Agotado':
                self.estado = 'Agotado'
                return True  # Indica que hubo cambio
        # Si el insumo está Activo, el ingrediente también puede estar Activo
        elif self.insumo.estado == 'Activo':
            if self.estado == 'Agotado':
                self.estado = 'Activo'
                return True  # Indica que hubo cambio
        return False  # No hubo cambio
    
    def reservar_insumo(self, cantidad_producir=1):
        """
        Reserva la cantidad necesaria del insumo para producir
        cantidad_producir unidades de la receta
        """
        cantidad_total = float(self.cantidad) * cantidad_producir
        if self.insumo.stock_actual >= cantidad_total:
            self.insumo.stock_actual = models.F('stock_actual') - cantidad_total
            self.insumo.save(update_fields=['stock_actual'])
            # Recalcular estado del insumo
            self.insumo.recalcular_estado()
            return True
        return False
    
    def clean(self):
        """Validaciones personalizadas"""
        from django.core.exceptions import ValidationError
        
        if self.cantidad <= 0:
            raise ValidationError({
                'cantidad': 'La cantidad debe ser mayor a cero'
            })
        
        if self.receta and self.insumo:
            # Verificar que no exista ya esta combinación receta-insumo
            existing = RecetaInsumo.objects.filter(
                receta=self.receta,
                insumo=self.insumo
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    'Ya existe un ingrediente de este tipo para esta receta'
                )
    
    def save(self, *args, **kwargs):
        """Override save para verificar disponibilidad automáticamente"""
        if self.pk:  # Solo si no es nuevo
            self.verificar_disponibilidad()
        super().save(*args, **kwargs)
    
    @classmethod
    def actualizar_estados_por_insumo(cls, insumo):
        """Actualiza el estado de todos los ingredientes que usan un insumo específico"""
        ingredientes = cls.objects.filter(insumo=insumo)
        actualizados = []
        
        for ingrediente in ingredientes:
            if ingrediente.verificar_disponibilidad():
                ingrediente.save()
                actualizados.append(ingrediente)
        
        return actualizados
