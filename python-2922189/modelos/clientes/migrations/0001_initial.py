# Generated manually for clientes app

from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id_cli', models.AutoField(db_column='id_cli', primary_key=True, serialize=False, verbose_name='ID Cliente')),
                ('nombre', models.CharField(help_text='Nombre completo del cliente', max_length=50, verbose_name='Nombre')),
                ('nit', models.CharField(help_text='NIT del cliente', max_length=15, unique=True, verbose_name='NIT')),
                ('direccion', models.TextField(blank=True, help_text='Dirección del cliente', null=True, verbose_name='Dirección')),
                ('telefono', models.CharField(blank=True, help_text='Número de teléfono', max_length=15, null=True, verbose_name='Teléfono')),
                ('email', models.EmailField(blank=True, help_text='Correo electrónico', max_length=100, null=True, verbose_name='Email')),
                ('fecha_registro', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de registro')),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'db_table': 'clientes',
                'ordering': ['nombre'],
            },
        ),
    ]