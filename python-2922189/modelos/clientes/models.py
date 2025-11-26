from django.db import models
from django.core.validators import RegexValidator


class Cliente(models.Model):
    """
    Modelo de Cliente del sistema PAE
    Migrado desde clientes.java
    """
    
    # Campos del modelo (equivalentes a clientes.java)
    id_Cliente = models.AutoField(
        primary_key=True,
        db_column='id_Cliente',
        verbose_name='ID Cliente'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre completo del cliente o empresa'
    )
    
    nit = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='NIT',
        help_text='NIT, RUC o documento de identificación'
    )
    
    telefono = models.CharField(
        max_length=20,
        unique=True,
        verbose_name='Teléfono',
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message="El teléfono debe tener entre 9 y 15 dígitos."
            )
        ]
    )
    
    correo = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name='Correo Electrónico',
        default='cliente@ejemplo.com'
    )
    
    class Meta:
        db_table = 'clientes'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']
    
    def __str__(self):
        return f"{self.nombre} ({self.nit})"
    
    @property
    def telefono_formateado(self):
        """Retorna el teléfono formateado"""
        if len(self.telefono) == 10:
            return f"{self.telefono[:3]}-{self.telefono[3:6]}-{self.telefono[6:]}"
        return self.telefono
    
    def clean(self):
        """Validaciones adicionales"""
        from django.core.exceptions import ValidationError
        
        # Validar que el NIT no esté vacío
        if not self.nit.strip():
            raise ValidationError({'nit': 'El NIT es obligatorio'})
        
        # Validar formato de correo
        if '@' not in self.correo:
            raise ValidationError({'correo': 'Debe ser un correo válido'})
    
    def save(self, *args, **kwargs):
        """Override del save para validaciones"""
        self.nombre = self.nombre.strip().title()
        self.nit = self.nit.strip().upper()
        self.correo = self.correo.strip().lower()
        super().save(*args, **kwargs)
