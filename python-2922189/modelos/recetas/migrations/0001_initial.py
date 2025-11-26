# Generated manually for recetas app

from django.db import migrations, models
import decimal


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('insumos', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Receta',
            fields=[
                ('id_rec', models.AutoField(db_column='id_rec', primary_key=True, serialize=False, verbose_name='ID Receta')),
                ('nombre', models.CharField(help_text='Nombre del producto o plato', max_length=50, verbose_name='Nombre')),
                ('descripcion', models.TextField(help_text='Descripción detallada del producto', null=True, blank=True, verbose_name='Descripción')),
                ('precio', models.DecimalField(decimal_places=2, default=decimal.Decimal('0.00'), help_text='Precio de venta del producto', max_digits=10, verbose_name='Precio')),
                ('estado', models.CharField(choices=[('Activo', 'Activo'), ('Inactivo', 'Inactivo')], default='Activo', max_length=10, verbose_name='Estado')),
            ],
            options={
                'verbose_name': 'Receta',
                'verbose_name_plural': 'Recetas',
                'db_table': 'recetas',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='RecetaInsumo',
            fields=[
                ('id_rec_ins', models.AutoField(primary_key=True, serialize=False)),
                ('cantidad', models.DecimalField(decimal_places=3, help_text='Cantidad del insumo necesaria para esta receta', max_digits=10, verbose_name='Cantidad')),
                ('unidad', models.CharField(choices=[('g', 'Gramos'), ('kg', 'Kilogramos'), ('ml', 'Mililitros'), ('l', 'Litros'), ('unidad', 'Unidades'), ('cucharada', 'Cucharadas'), ('cucharadita', 'Cucharaditas'), ('taza', 'Tazas'), ('pizca', 'Pizca')], max_length=15, verbose_name='Unidad de medida')),
                ('estado', models.CharField(choices=[('Activo', 'Activo'), ('Agotado', 'Agotado')], default='Activo', max_length=10, verbose_name='Estado')),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creación')),
                ('fecha_modificacion', models.DateTimeField(auto_now=True, verbose_name='Última modificación')),
                ('insumo', models.ForeignKey(db_column='id_ins', on_delete=models.deletion.CASCADE, related_name='recetas_que_usan', to='insumos.insumo', verbose_name='Insumo')),
                ('receta', models.ForeignKey(db_column='id_rec', on_delete=models.deletion.CASCADE, related_name='ingredientes', to='recetas.receta', verbose_name='Receta')),
            ],
            options={
                'verbose_name': 'Ingrediente de Receta',
                'verbose_name_plural': 'Ingredientes de Recetas',
                'db_table': 'receta_insumos',
                'ordering': ['receta__nombre', 'insumo__nombre'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='recetainsumo',
            unique_together={('receta', 'insumo')},
        ),
    ]