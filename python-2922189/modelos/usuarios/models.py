from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    """
    Modelo de Usuario del sistema PAE
    Migrado desde usuarios.java
    """
    
    # Opciones para roles
    ROL_CHOICES = [
        ('A', 'Administrador'),
        ('EP', 'Empleado Producción'),
        ('EV', 'Empleado Ventas'),
    ]
    
    # Opciones para estado
    ESTADO_CHOICES = [
        ('A', 'Activo'),
        ('I', 'Inactivo'),
    ]
    
    # Campos del modelo (equivalentes a usuarios.java)
    id_usu = models.AutoField(
        primary_key=True,
        db_column='id_usu',
        verbose_name='ID Usuario'
    )
    
    documento = models.IntegerField(
        unique=True,
        null=True,  # Temporalmente nullable para migraciones
        blank=True,
        verbose_name='Documento',
        help_text='Número de identificación (Cédula, TI, etc.)'
    )
    
    nombres = models.CharField(
        max_length=50,
        verbose_name='Nombres',
        help_text='Nombres completos del usuario',
        default='Sin nombre'
    )
    
    apellidos = models.CharField(
        max_length=50,
        verbose_name='Apellidos',
        help_text='Apellidos completos del usuario',
        default='Sin apellido'
    )
    
    telefono = models.BigIntegerField(
        verbose_name='Teléfono',
        default=0
    )
    
    direccion = models.CharField(
        max_length=100,
        verbose_name='Dirección',
        default='Sin dirección'
    )
    
    correo = models.EmailField(
        max_length=100,
        unique=True,
        verbose_name='Correo Electrónico',
        default='usuario@ejemplo.com'
    )
    
    rol = models.CharField(
        max_length=2,
        choices=ROL_CHOICES,
        verbose_name='Rol',
        help_text='Rol del usuario en el sistema',
        default='EV'
    )
    
    password = models.CharField(
        max_length=256,
        verbose_name='Contraseña',
        default='sin_password'
    )
    
    estado = models.CharField(
        max_length=1,
        choices=ESTADO_CHOICES,
        default='A',
        verbose_name='Estado'
    )
    
    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['nombres', 'apellidos']
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
    def set_password(self, raw_password):
        """Encripta y guarda la contraseña"""
        self.password = make_password(raw_password)
    
    def check_password(self, raw_password):
        """Verifica si la contraseña es correcta"""
        return check_password(raw_password, self.password)
    
    @property
    def get_rol_display_extended(self):
        """Retorna el nombre completo del rol"""
        rol_map = {
            'A': 'Administrador',
            'EP': 'Empleado de Producción',
            'EV': 'Empleado de Ventas'
        }
        return rol_map.get(self.rol, 'Sin definir')
    
    @property
    def nombre_completo(self):
        """Retorna el nombre completo del usuario"""
        return f"{self.nombres} {self.apellidos}"
    
    @property
    def is_active(self):
        """Verifica si el usuario está activo"""
        return self.estado == 'A'
    
    def save(self, *args, **kwargs):
        """Override del save para validaciones adicionales"""
        # Si es un nuevo usuario y no hay password hasheado, lo encriptamos
        if not self.pk and not self.password.startswith('pbkdf2_'):
            self.set_password(self.password)
        super().save(*args, **kwargs)


class PasswordResetToken(models.Model):
    """Token de recuperación de contraseña asociado a Usuario"""
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='reset_tokens')
    token = models.CharField(max_length=128, unique=True, db_index=True)
    creado = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)
    codigo = models.CharField(max_length=6, db_index=True, help_text='Código corto de verificación')

    class Meta:
        db_table = 'usuarios_password_reset_tokens'
        ordering = ['-creado']

    def __str__(self):
        return f"ResetToken({self.usuario.correo})"

    def marcar_usado(self):
        self.usado = True
        self.save(update_fields=['usado'])
