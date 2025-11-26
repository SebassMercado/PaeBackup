# Generated manually for usuarios app

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Usuario',
            fields=[
                ('id_usuario', models.AutoField(db_column='id_usuario', primary_key=True, serialize=False, verbose_name='ID Usuario')),
                ('nombre', models.CharField(help_text='Nombre completo del usuario', max_length=50, verbose_name='Nombre')),
                ('cedula', models.CharField(help_text='Número de cédula único', max_length=20, unique=True, verbose_name='Cédula')),
                ('telefono', models.CharField(blank=True, help_text='Número de teléfono de contacto', max_length=15, null=True, verbose_name='Teléfono')),
                ('direccion', models.TextField(blank=True, help_text='Dirección de residencia', null=True, verbose_name='Dirección')),
                ('email', models.EmailField(blank=True, help_text='Correo electrónico', max_length=100, null=True, unique=True, verbose_name='Email')),
                ('usuario', models.CharField(help_text='Nombre de usuario único', max_length=30, unique=True, verbose_name='Usuario')),
                ('clave', models.CharField(help_text='Contraseña cifrada', max_length=128, verbose_name='Contraseña')),
                ('rol', models.CharField(choices=[('A', 'Administrador'), ('EP', 'Empleado Producción'), ('EV', 'Empleado Ventas')], default='EV', help_text='Rol del usuario en el sistema', max_length=2, verbose_name='Rol')),
                ('activo', models.BooleanField(default=True, help_text='Si el usuario está activo en el sistema', verbose_name='Activo')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('ultima_conexion', models.DateTimeField(blank=True, null=True, verbose_name='Última conexión')),
            ],
            options={
                'verbose_name': 'Usuario',
                'verbose_name_plural': 'Usuarios',
                'db_table': 'usuarios',
                'ordering': ['nombre'],
            },
        ),
    ]