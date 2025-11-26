from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from datetime import date


class Insumo(models.Model):
    """
    Modelo de Insumo del sistema PAE
    Migrado desde insumos.java
    """
    
    # Opciones para estado
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Inactivo', 'Inactivo'),
        ('Stock insuficiente', 'Stock insuficiente'),
    ]
    
    # Opciones comunes para unidades de medida
    UNIDAD_CHOICES = [
        ('kg', 'Kilogramos'),
        ('g', 'Gramos'),
        ('ml', 'Mililitros'),
        ('l', 'Litros'),
        ('unidad', 'Unidades'),
        ('lb', 'Libras'),
        ('oz', 'Onzas'),
    ]

    # Categorías para lógica de lote / vencimiento
    CATEGORIA_CHOICES = [
        # Con lote obligatorio
        ('Enlatados', 'Enlatados'),
        ('Envasados', 'Envasados'),
        ('Lácteos', 'Lácteos'),
        ('Carnes', 'Carnes'),
        ('Bebidas', 'Bebidas'),
        ('Congelados', 'Congelados'),
        ('Panadería industrial', 'Panadería industrial'),
        ('Salsas', 'Salsas'),
        # Sin lote obligatorio
        ('Frutas', 'Frutas'),
        ('Verduras', 'Verduras'),
        ('Granel', 'Granel'),
        ('Panadería artesanal', 'Panadería artesanal'),
    ]
    
    # Campos del modelo (equivalentes a insumos.java)
    id_ins = models.AutoField(
        primary_key=True,
        db_column='id_ins',
        verbose_name='ID Insumo'
    )
    
    nombre = models.CharField(
        max_length=45,
        verbose_name='Nombre',
        help_text='Nombre del insumo',
        default='Insumo sin nombre'
    )
    
    unidad_medida = models.CharField(
        max_length=10,
        choices=UNIDAD_CHOICES,
        verbose_name='Unidad de Medida',
        default='kg'
    )
    
    stock_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Stock Mínimo',
        help_text='Cantidad mínima requerida en inventario',
        default=Decimal('1.00')
    )
    
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Stock Actual',
        help_text='Cantidad actual en inventario'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='Activo',
        verbose_name='Estado'
    )

    categoria = models.CharField(
        max_length=30,
        choices=CATEGORIA_CHOICES,
        default='Granel',
        verbose_name='Categoría',
        help_text='Categoría del insumo para lógica de lotes/vencimiento'
    )
    
    class Meta:
        db_table = 'insumos'
        verbose_name = 'Insumo'
        verbose_name_plural = 'Insumos'
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['nombre']),
            models.Index(fields=['categoria']),
        ]
    
    def __str__(self):
        return f"{self.nombre} ({self.stock_actual}/{self.stock_min} {self.unidad_medida})"
    
    def recalcular_estado(self):
        """
        Lógica de negocio migrada desde insumos.java
        Recalcula el estado basado en el stock actual vs mínimo
        """
        if self.stock_actual < self.stock_min:
            self.estado = "Stock insuficiente"
        elif self.estado != "Inactivo":  # Solo actualiza si no está manualmente inactivo
            self.estado = "Activo"

    @property
    def requiere_lote(self):
        """Indica si según la categoría debe manejar lotes con vencimiento"""
        return self.categoria in [
            'Enlatados', 'Envasados', 'Lácteos', 'Carnes', 'Bebidas',
            'Congelados', 'Panadería industrial', 'Salsas'
        ]

    @property
    def requiere_vencimiento(self):
        """Alias semántico de requiere_lote para vistas que hablen de vencimiento"""
        return self.requiere_lote
    
    @property
    def necesita_restock(self):
        """Indica si el insumo necesita ser reabastecido"""
        return self.stock_actual < self.stock_min
    
    @property
    def porcentaje_stock(self):
        """Calcula el porcentaje de stock actual vs mínimo"""
        if self.stock_min > 0:
            return (float(self.stock_actual) / float(self.stock_min)) * 100
        return 100.0
    
    @property
    def stock_faltante(self):
        """Calcula cuánto stock falta para llegar al mínimo"""
        if self.necesita_restock:
            return self.stock_min - self.stock_actual
        return Decimal('0.00')
    
    @property
    def status_color(self):
        """Retorna un color para mostrar en interfaz según el estado"""
        colors = {
            'Activo': 'green',
            'Inactivo': 'gray',
            'Stock insuficiente': 'red'
        }
        return colors.get(self.estado, 'gray')
    
    def agregar_stock(self, cantidad):
        """Agrega stock y recalcula el estado"""
        if cantidad > 0:
            self.stock_actual += Decimal(str(cantidad))
            self.recalcular_estado()
    
    def reducir_stock(self, cantidad):
        """Reduce stock y recalcula el estado"""
        if cantidad > 0 and self.stock_actual >= Decimal(str(cantidad)):
            self.stock_actual -= Decimal(str(cantidad))
            self.recalcular_estado()
            return True
        return False
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if self.stock_min < 0:
            raise ValidationError({'stock_min': 'El stock mínimo no puede ser negativo'})
        
        if self.stock_actual < 0:
            raise ValidationError({'stock_actual': 'El stock actual no puede ser negativo'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Guardar estado anterior para comparar
        estado_anterior = None
        stock_anterior = None
        
        if self.pk:  # Si ya existe
            try:
                insumo_anterior = Insumo.objects.get(pk=self.pk)
                estado_anterior = insumo_anterior.estado
                stock_anterior = insumo_anterior.stock_actual
            except Insumo.DoesNotExist:
                pass
        
        # Capitalizar nombre
        self.nombre = self.nombre.strip().title()
        
        # Recalcular estado antes de guardar
        self.recalcular_estado()
        
        super().save(*args, **kwargs)
        
        # Si cambió el estado o el stock, actualizar recetas relacionadas
        if (estado_anterior != self.estado or 
            (stock_anterior is not None and stock_anterior != self.stock_actual)):
            self._actualizar_recetas_relacionadas()
    
    def _actualizar_recetas_relacionadas(self):
        """Actualiza las recetas que usan este insumo cuando cambia su estado o stock"""
        try:
            from modelos.recetas.models import Receta
            recetas_actualizadas = Receta.actualizar_estados_por_insumo(self)
            
            if recetas_actualizadas:
                nombres_recetas = [receta.nombre for receta in recetas_actualizadas]
                print(f"🔄 RECETAS ACTUALIZADAS automáticamente por cambio en {self.nombre}: {nombres_recetas}")
                
        except ImportError:
            print(f"⚠️ No se pudo importar el modelo de Recetas")
        except Exception as e:
            print(f"❌ Error actualizando recetas relacionadas con {self.nombre}: {e}")


class DetalleInsumo(models.Model):
    """
    Modelo de Detalle de Insumo (Lotes) del sistema PAE
    Migrado desde detalle_insumo.java
    """
    
    # Opciones para estado del lote
    ESTADO_CHOICES = [
        ('Activo', 'Activo'),
        ('Vencido', 'Vencido'),
        ('Agotado', 'Agotado'),
        ('Eliminado', 'Eliminado'),
    ]
    
    # Campos del modelo (equivalentes a detalle_insumo.java)
    id_detalle = models.AutoField(
        primary_key=True,
        db_column='id_detalle',
        verbose_name='ID Detalle'
    )
    
    # Relación con Insumo
    id_ins = models.ForeignKey(
        'Insumo',
        on_delete=models.CASCADE,
        db_column='id_ins',
        verbose_name='Insumo',
        help_text='Insumo al que pertenece este lote'
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cantidad',
        help_text='Cantidad del lote',
        default=Decimal('1.00')
    )
    
    fecha_ingreso = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Ingreso',
        help_text='Fecha y hora de ingreso del lote'
    )
    
    fecha_vencimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name='Fecha de Vencimiento',
        help_text='Fecha de vencimiento del lote (opcional)'
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='Activo',
        verbose_name='Estado'
    )
    
    class Meta:
        db_table = 'detalle_insumo'
        verbose_name = 'Detalle de Insumo'
        verbose_name_plural = 'Detalles de Insumos'
        ordering = ['fecha_vencimiento', '-fecha_ingreso']
        indexes = [
            models.Index(fields=['estado']),
            models.Index(fields=['fecha_vencimiento']),
            models.Index(fields=['id_ins', 'estado']),
        ]
    
    def __str__(self):
        return f"{self.nombre_insumo} - Lote {self.id_detalle} ({self.cantidad})"
    
    @property
    def nombre_insumo(self):
        """Campo auxiliar: nombre del insumo (equivalente a nombre_insumo en Java)"""
        return self.id_ins.nombre if self.id_ins else "Sin insumo"
    
    @property
    def unidad_medida(self):
        """Obtiene la unidad de medida del insumo relacionado"""
        return self.id_ins.unidad_medida if self.id_ins else ""
    
    @property
    def esta_vencido(self):
        """Verifica si el lote está vencido"""
        if self.fecha_vencimiento:
            return date.today() > self.fecha_vencimiento
        return False
    
    @property
    def dias_para_vencer(self):
        """Calcula días restantes para vencer (negativo si ya venció)"""
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - date.today()
            return delta.days
        return None
    
    @property
    def esta_por_vencer(self, dias_alerta=7):
        """Verifica si está por vencer en los próximos N días"""
        dias = self.dias_para_vencer
        return dias is not None and 0 <= dias <= dias_alerta
    
    @property
    def status_color(self):
        """Color para mostrar en interfaz según estado y vencimiento"""
        if self.estado == 'Vencido' or self.esta_vencido:
            return 'red'
        elif self.estado == 'Agotado':
            return 'orange'
        elif self.estado == 'Eliminado':
            return 'gray'
        elif self.esta_por_vencer:
            return 'yellow'
        else:
            return 'green'
    
    def actualizar_estado_por_vencimiento(self):
        """Actualiza el estado si el lote está vencido"""
        if self.esta_vencido and self.estado == 'Activo':
            self.estado = 'Vencido'
    
    def actualizar_estado_por_cantidad(self):
        """Actualiza el estado si la cantidad llega a cero"""
        if self.cantidad <= 0 and self.estado == 'Activo':
            self.estado = 'Agotado'
    
    def usar_cantidad(self, cantidad_a_usar):
        """Reduce la cantidad del lote y actualiza estado si es necesario"""
        if cantidad_a_usar > 0 and self.cantidad >= cantidad_a_usar:
            self.cantidad -= cantidad_a_usar
            self.actualizar_estado_por_cantidad()
            return True
        return False
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar lógica de negocio"""
        # Actualizar estados automáticamente
        self.actualizar_estado_por_vencimiento()
        self.actualizar_estado_por_cantidad()
        
        super().save(*args, **kwargs)


class HistorialInsumo(models.Model):
    """
    Modelo de Historial de Insumos del sistema PAE
    Migrado desde historial.java
    
    Registra todas las operaciones realizadas sobre los insumos para auditoría
    y trazabilidad completa del inventario.
    """
    
    # Opciones para tipo de acción
    ACCION_CHOICES = [
        ('Entrada', 'Entrada'),
        ('Salida', 'Salida'),
        ('Edición', 'Edición'),
        ('Ingreso', 'Ingreso de Mercancía'),
        ('Ajuste', 'Ajuste de Inventario'),
        ('Vencimiento', 'Producto Vencido'),
        ('Merma', 'Merma o Pérdida'),
        ('Devolución', 'Devolución'),
        ('Transferencia', 'Transferencia'),
        ('Creación', 'Creación de Insumo'),
        ('Actualización', 'Actualización de Datos'),
    ]
    
    # Campos del modelo (equivalentes a historial.java)
    id_hist = models.AutoField(
        primary_key=True,
        db_column='idHist',
        verbose_name='ID Historial'
    )
    
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha',
        help_text='Fecha y hora de la operación'
    )
    
    accion = models.CharField(
        max_length=20,
        choices=ACCION_CHOICES,
        verbose_name='Acción',
        help_text='Tipo de operación realizada'
    )
    
    estado = models.CharField(
        max_length=20,
        verbose_name='Estado',
        help_text='Estado del insumo después de la operación',
        default='Activo'
    )
    
    cantidad = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Cantidad',
        help_text='Cantidad involucrada en la operación',
        default=Decimal('0.00')
    )
    
    stock_actual = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name='Stock Actual',
        help_text='Stock total después de la operación',
        default=Decimal('0.00')
    )
    
    novedad = models.TextField(
        blank=True,
        null=True,
        verbose_name='Novedad',
        help_text='Descripción detallada de la operación o novedad'
    )
    
    # Relaciones
    insumo = models.ForeignKey(
        'Insumo',
        on_delete=models.CASCADE,
        db_column='id_ins',
        verbose_name='Insumo',
        help_text='Insumo afectado por la operación',
        related_name='historial'
    )
    
    # Campo para ID del detalle (lote) - para compatibilidad con Java Bean
    id_detalle = models.IntegerField(
        null=True,
        blank=True,
        verbose_name='ID Detalle',
        help_text='ID del lote específico afectado'
    )
    
    class Meta:
        db_table = 'historial'
        verbose_name = 'Historial de Insumo'
        verbose_name_plural = 'Historiales de Insumos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['fecha']),
            models.Index(fields=['accion']),
            models.Index(fields=['insumo']),
            models.Index(fields=['insumo', 'fecha']),
            models.Index(fields=['id_detalle']),
        ]
    
    def __str__(self):
        return f"Historial {self.id_hist} - {self.nombre_insumo} - {self.accion} ({self.cantidad})"
    
    # 🧍 Propiedades auxiliares (equivalente a nombre_insumo en Java)
    @property
    def nombre_insumo(self):
        """Nombre del insumo afectado"""
        return self.insumo.nombre if self.insumo else "Sin insumo"
    
    @property
    def unidad_medida(self):
        """Unidad de medida del insumo"""
        return self.insumo.unidad_medida if self.insumo else ""
    
    @property
    def cantidad_formateada(self):
        """Cantidad con unidad de medida"""
        return f"{self.cantidad} {self.unidad_medida}"
    
    @property
    def stock_formateado(self):
        """Stock con unidad de medida"""
        return f"{self.stock_actual} {self.unidad_medida}"
    
    @property
    def fecha_formateada(self):
        """Fecha formateada para mostrar"""
        return self.fecha.strftime("%d/%m/%Y %H:%M:%S")
    
    @property
    def tiempo_transcurrido(self):
        """Tiempo transcurrido desde la operación"""
        now = timezone.now()
        delta = now - self.fecha
        
        days = delta.days
        hours = delta.seconds // 3600
        minutes = (delta.seconds % 3600) // 60
        
        if days > 0:
            return f"Hace {days}d {hours}h"
        elif hours > 0:
            return f"Hace {hours}h {minutes}m"
        else:
            return f"Hace {minutes}m"
    
    @property
    def diferencia_stock(self):
        """Calcula la diferencia en stock por esta operación"""
        if self.accion in ['Ingreso', 'Devolución']:
            return self.cantidad
        elif self.accion in ['Salida', 'Merma', 'Vencimiento']:
            return -self.cantidad
        else:
            return Decimal('0.00')
    
    @property
    def tipo_operacion(self):
        """Categoriza el tipo de operación"""
        if self.accion in ['Ingreso', 'Devolución']:
            return 'Entrada'
        elif self.accion in ['Salida', 'Merma', 'Vencimiento']:
            return 'Salida'
        elif self.accion in ['Ajuste', 'Transferencia']:
            return 'Ajuste'
        else:
            return 'Información'
    
    @property
    def icono_accion(self):
        """Icono para mostrar según el tipo de acción"""
        iconos = {
            'Ingreso': '📦',
            'Salida': '🏭',
            'Ajuste': '⚖️',
            'Vencimiento': '⚠️',
            'Merma': '📉',
            'Devolución': '↩️',
            'Transferencia': '🔄',
            'Creación': '✨',
            'Actualización': '📝',
        }
        return iconos.get(self.accion, '📋')
    
    @property
    def color_accion(self):
        """Color para mostrar según el tipo de acción"""
        colores = {
            'Ingreso': 'green',
            'Salida': 'blue',
            'Ajuste': 'orange',
            'Vencimiento': 'red',
            'Merma': 'red',
            'Devolución': 'purple',
            'Transferencia': 'teal',
            'Creación': 'darkgreen',
            'Actualización': 'gray',
        }
        return colores.get(self.accion, 'black')
    
    @property
    def nombre_lote(self):
        """Nombre del lote si aplica"""
        if self.id_detalle:
            return f"Lote {self.id_detalle}"
        return "General"
    
    @property
    def resumen_operacion(self):
        """Resumen de la operación para mostrar"""
        operacion = f"{self.accion}: {self.cantidad_formateada}"
        if self.novedad:
            operacion += f" - {self.novedad[:50]}{'...' if len(self.novedad) > 50 else ''}"
        return operacion
    
    # 🎯 Métodos estáticos para crear historiales
    
    @staticmethod
    def registrar_ingreso(insumo, cantidad, detalle=None, novedad=""):
        return HistorialInsumo.objects.create(
            accion='Entrada',
            insumo=insumo,
            id_detalle=detalle.id_detalle if detalle else None,
            cantidad=cantidad,
            stock_actual=insumo.stock_actual,
            estado=insumo.estado,
            novedad=novedad or f"Entrada de {cantidad} {insumo.unidad_medida} de {insumo.nombre}"
        )
    
    @staticmethod
    def registrar_salida(insumo, cantidad, detalle=None, novedad=""):
        return HistorialInsumo.objects.create(
            accion='Salida',
            insumo=insumo,
            id_detalle=detalle.id_detalle if detalle else None,
            cantidad=cantidad,
            stock_actual=insumo.stock_actual,
            estado=insumo.estado,
            novedad=novedad or f"Salida de {cantidad} {insumo.unidad_medida}"
        )
    
    @staticmethod
    def registrar_ajuste(insumo, cantidad_anterior, cantidad_nueva, motivo=""):
        diferencia = cantidad_nueva - cantidad_anterior
        return HistorialInsumo.objects.create(
            accion='Edición',
            insumo=insumo,
            cantidad=abs(diferencia),
            stock_actual=insumo.stock_actual,
            estado=insumo.estado,
            novedad=f"Edición: {cantidad_anterior} → {cantidad_nueva}. {motivo}"
        )
    
    @staticmethod
    def registrar_vencimiento(insumo, cantidad, detalle=None):
        return HistorialInsumo.objects.create(
            accion='Edición',
            insumo=insumo,
            id_detalle=detalle.id_detalle if detalle else None,
            cantidad=cantidad,
            stock_actual=insumo.stock_actual,
            estado='Vencimiento',
            novedad=f"Vencimiento lote {detalle.id_detalle if detalle else 'General'}"
        )
    
    @staticmethod
    def registrar_merma(insumo, cantidad, motivo=""):
        return HistorialInsumo.objects.create(
            accion='Salida',
            insumo=insumo,
            cantidad=cantidad,
            stock_actual=insumo.stock_actual,
            estado=insumo.estado,
            novedad=f"Merma. {motivo}"
        )

    @staticmethod
    def registrar_movimiento(insumo, tipo, cantidad, estado="", novedad="", detalle=None):
        tipo_norm = tipo.capitalize()
        if tipo_norm not in ['Entrada','Salida','Edición']:
            tipo_norm = 'Edición'
        return HistorialInsumo.objects.create(
            accion=tipo_norm,
            insumo=insumo,
            id_detalle=detalle.id_detalle if detalle else None,
            cantidad=cantidad,
            stock_actual=insumo.stock_actual,
            estado=estado or insumo.estado,
            novedad=novedad[:100] if novedad else f"{tipo_norm} de {cantidad} {insumo.unidad_medida}"
        )
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        if self.cantidad < 0:
            raise ValidationError({'cantidad': 'La cantidad no puede ser negativa'})
        
        if self.stock_actual < 0:
            raise ValidationError({'stock_actual': 'El stock actual no puede ser negativo'})
    
    def save(self, *args, **kwargs):
        """Override del save para aplicar validaciones"""
        self.full_clean()
        super().save(*args, **kwargs)
