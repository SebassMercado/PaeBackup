# Generated manually for insumos app

from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Insumo',
            fields=[
                ('id_ins', models.AutoField(db_column='id_ins', primary_key=True, serialize=False, verbose_name='ID Insumo')),
                ('nombre', models.CharField(help_text='Nombre del insumo', max_length=50, verbose_name='Nombre')),
                ('descripcion', models.TextField(help_text='Descripción detallada del insumo', null=True, blank=True, verbose_name='Descripción')),
                ('precio_unitario', models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), help_text='Precio por unidad', max_digits=10, verbose_name='Precio Unitario')),
                ('stock_actual', models.DecimalField(decimal_places=3, default=decimal.Decimal('0.000'), help_text='Cantidad disponible en inventario', max_digits=10, verbose_name='Stock Actual')),
                ('stock_minimo', models.DecimalField(decimal_places=3, default=decimal.Decimal('0.000'), help_text='Cantidad mínima antes de agotarse', max_digits=10, verbose_name='Stock Mínimo')),
                ('unidad_medida', models.CharField(choices=[('g', 'Gramos'), ('kg', 'Kilogramos'), ('ml', 'Mililitros'), ('l', 'Litros'), ('unidad', 'Unidades'), ('lb', 'Libras'), ('oz', 'Onzas')], help_text='Unidad en la que se mide este insumo', max_length=10, verbose_name='Unidad de Medida')),
                ('estado', models.CharField(choices=[('Disponible', 'Disponible'), ('Agotado', 'Agotado'), ('Descontinuado', 'Descontinuado')], default='Disponible', max_length=15, verbose_name='Estado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Última modificación')),
            ],
            options={
                'verbose_name': 'Insumo',
                'verbose_name_plural': 'Insumos',
                'db_table': 'insumos',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='DetalleInsumo',
            fields=[
                ('id_det_ins', models.AutoField(db_column='id_det_ins', primary_key=True, serialize=False, verbose_name='ID Detalle')),
                ('numero_lote', models.CharField(help_text='Número de lote del insumo', max_length=20, verbose_name='Número de Lote')),
                ('fecha_vencimiento', models.DateField(help_text='Fecha de vencimiento del lote', null=True, blank=True, verbose_name='Fecha de Vencimiento')),
                ('cantidad_lote', models.DecimalField(decimal_places=3, help_text='Cantidad en este lote', max_digits=10, verbose_name='Cantidad del Lote')),
                ('cantidad_actual', models.DecimalField(decimal_places=3, help_text='Cantidad restante en el lote', max_digits=10, verbose_name='Cantidad Actual')),
                ('precio_compra', models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), help_text='Precio de compra de este lote', max_digits=10, verbose_name='Precio de Compra')),
                ('estado', models.CharField(choices=[('Disponible', 'Disponible'), ('Agotado', 'Agotado'), ('Vencido', 'Vencido')], default='Disponible', max_length=15, verbose_name='Estado')),
                ('fecha_ingreso', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de ingreso')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Última modificación')),
                ('insumo', models.ForeignKey(db_column='id_ins', on_delete=models.deletion.CASCADE, related_name='lotes', to='insumos.insumo', verbose_name='Insumo')),
            ],
            options={
                'verbose_name': 'Detalle de Insumo',
                'verbose_name_plural': 'Detalles de Insumos',
                'db_table': 'detalle_insumos',
                'ordering': ['insumo__nombre', 'fecha_vencimiento'],
            },
        ),
    ]