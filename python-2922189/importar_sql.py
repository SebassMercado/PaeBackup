import os
import django
import re
from datetime import datetime
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario
from modelos.clientes.models import Cliente
from modelos.insumos.models import Insumo, DetalleInsumo, HistorialInsumo
from modelos.recetas.models import Receta, RecetaInsumo
from modelos.produccion.models import Produccion, ProduccionReceta
from modelos.ventas.models import Venta, Pago, VentaProduccion, VentaReceta

print("=" * 80)
print("IMPORTANDO DATOS DESDE pae.sql")
print("=" * 80)

# Leer el archivo SQL
with open('pae.sql', 'r', encoding='utf-8') as f:
    sql_content = f.read()

# Función para extraer datos de INSERT INTO
def extract_insert_data(table_name, sql_content):
    pattern = rf"INSERT INTO `{table_name}` \([^)]+\) VALUES\s*([\s\S]+?);"
    match = re.search(pattern, sql_content)
    if match:
        values_str = match.group(1)
        # Extraer cada fila de valores
        rows_pattern = r'\(([^)]+)\)'
        rows = re.findall(rows_pattern, values_str)
        return rows
    return []

# 1. LIMPIAR TODA LA BASE DE DATOS
print("\n🗑️  PASO 1: Limpiando base de datos...")
VentaReceta.objects.all().delete()
VentaProduccion.objects.all().delete()
Pago.objects.all().delete()
Venta.objects.all().delete()
ProduccionReceta.objects.all().delete()
Produccion.objects.all().delete()
RecetaInsumo.objects.all().delete()
Receta.objects.all().delete()
HistorialInsumo.objects.all().delete()
DetalleInsumo.objects.all().delete()
Insumo.objects.all().delete()
Cliente.objects.all().delete()
Usuario.objects.all().delete()
print("✅ Base de datos limpiada")

# 2. IMPORTAR USUARIOS
print("\n📥 PASO 2: Importando usuarios...")
usuarios_data = extract_insert_data('usuarios', sql_content)
for row in usuarios_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 10:
        usuario = Usuario(
            id_usu=int(values[0]),
            documento=int(values[1]) if values[1] != 'NULL' else None,
            nombres=values[2],
            apellidos=values[3],
            telefono=int(values[4]) if values[4].isdigit() else 0,
            direccion=values[5],
            correo=values[6],
            rol=values[7],
            estado=values[8],
            password=values[9]
        )
        usuario.save(update_fields=None)  # Evitar re-hashear
print(f"✅ {Usuario.objects.count()} usuarios importados")

# 3. IMPORTAR CLIENTES
print("\n📥 PASO 3: Importando clientes...")
clientes_data = extract_insert_data('clientes', sql_content)
for row in clientes_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 5:
        Cliente.objects.create(
            id_Cliente=int(values[0]),
            nombre=values[1],
            nit=values[2],
            telefono=values[3],
            correo=values[4]
        )
print(f"✅ {Cliente.objects.count()} clientes importados")

# 4. IMPORTAR INSUMOS
print("\n📥 PASO 4: Importando insumos...")
insumos_data = extract_insert_data('insumos', sql_content)
for row in insumos_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 6:
        Insumo.objects.create(
            id_ins=int(values[0]),
            nombre=values[1],
            unidad_medida=values[2],
            stock_min=Decimal(values[3]),
            stock_actual=Decimal(values[4]),
            estado=values[5]
        )
print(f"✅ {Insumo.objects.count()} insumos importados")

# 5. IMPORTAR RECETAS
print("\n📥 PASO 5: Importando recetas...")
recetas_data = extract_insert_data('recetas', sql_content)
for row in recetas_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 5:
        Receta.objects.create(
            id_rec=int(values[0]),
            nombre=values[1],
            descripcion=values[2] if values[2] != 'NULL' else '',
            precio=Decimal(values[3]),
            estado=values[4]
        )
print(f"✅ {Receta.objects.count()} recetas importadas")

# 6. IMPORTAR DETALLE INSUMO
print("\n📥 PASO 6: Importando detalle de insumos...")
detalle_data = extract_insert_data('detalle_insumo', sql_content)
for row in detalle_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 6:
        try:
            insumo = Insumo.objects.get(id_ins=int(values[1]))
            DetalleInsumo.objects.create(
                id_detalle=int(values[0]),
                id_ins=insumo,
                cantidad=Decimal(values[2]),
                fecha_ingreso=values[3] if values[3] != 'NULL' else None,
                fecha_vencimiento=values[4] if values[4] != 'NULL' else None,
                estado=values[5]
            )
        except Exception as e:
            print(f"⚠️  Error importando detalle {values[0]}: {e}")
print(f"✅ {DetalleInsumo.objects.count()} detalles de insumo importados")

# 7. IMPORTAR RECETA INSUMOS
print("\n📥 PASO 7: Importando receta-insumos...")
receta_insumos_data = extract_insert_data('receta_insumos', sql_content)
for row in receta_insumos_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 6:
        try:
            receta = Receta.objects.get(id_rec=int(values[1]))
            insumo = Insumo.objects.get(id_ins=int(values[2]))
            RecetaInsumo.objects.create(
                id_rec_ins=int(values[0]),
                id_rec=receta,
                id_ins=insumo,
                cantidad=Decimal(values[3]),
                unidad=values[4],
                estado=values[5]
            )
        except Exception as e:
            print(f"⚠️  Error importando receta-insumo {values[0]}: {e}")
print(f"✅ {RecetaInsumo.objects.count()} relaciones receta-insumo importadas")

# 8. IMPORTAR HISTORIAL INSUMO
print("\n📥 PASO 8: Importando historial de insumos...")
historial_data = extract_insert_data('historial', sql_content)
for row in historial_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 9:
        try:
            insumo = Insumo.objects.get(id_ins=int(values[7]))
            detalle = DetalleInsumo.objects.get(id_detalle=int(values[8])) if values[8] != 'NULL' else None
            HistorialInsumo.objects.create(
                idHist=int(values[0]),
                fecha=values[1],
                accion=values[2],
                estado=values[3],
                cantidad=Decimal(values[4]),
                stock_actual=Decimal(values[5]),
                novedad=values[6] if values[6] != 'NULL' else '',
                id_ins=insumo,
                id_detalle=detalle
            )
        except Exception as e:
            print(f"⚠️  Error importando historial {values[0]}: {e}")
print(f"✅ {HistorialInsumo.objects.count()} registros de historial importados")

# 9. IMPORTAR PRODUCCIÓN
print("\n📥 PASO 9: Importando producción...")
produccion_data = extract_insert_data('produccion', sql_content)
for row in produccion_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 7:
        try:
            usuario = Usuario.objects.get(id_usu=int(values[5]))
            asignado = Usuario.objects.get(id_usu=int(values[6])) if values[6] != 'NULL' else None
            Produccion.objects.create(
                id_proc=int(values[0]),
                estado=values[1],
                fecha_hora=values[2],
                fecha_aceptacion=values[3] if values[3] != 'NULL' else None,
                fecha_finalizacion=values[4] if values[4] != 'NULL' else None,
                id_usu=usuario,
                id_asignado=asignado
            )
        except Exception as e:
            print(f"⚠️  Error importando producción {values[0]}: {e}")
print(f"✅ {Produccion.objects.count()} producciones importadas")

# 10. IMPORTAR PRODUCCIÓN RECETAS
print("\n📥 PASO 10: Importando producción-recetas...")
produccion_recetas_data = extract_insert_data('produccion_recetas', sql_content)
for row in produccion_recetas_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 4:
        try:
            produccion = Produccion.objects.get(id_proc=int(values[1]))
            receta = Receta.objects.get(id_rec=int(values[2]))
            ProduccionReceta.objects.create(
                id_detalle=int(values[0]),
                id_produccion=produccion,
                id_rec=receta,
                cantidad=int(values[3])
            )
        except Exception as e:
            print(f"⚠️  Error importando producción-receta {values[0]}: {e}")
print(f"✅ {ProduccionReceta.objects.count()} relaciones producción-receta importadas")

# 11. IMPORTAR VENTAS
print("\n📥 PASO 11: Importando ventas...")
ventas_data = extract_insert_data('ventas', sql_content)
for row in ventas_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 9:
        try:
            usuario = Usuario.objects.get(id_usu=int(values[3]))
            asignado = Usuario.objects.get(id_usu=int(values[4])) if values[4] != 'NULL' else None
            cliente = Cliente.objects.get(id_Cliente=int(values[5]))
            Venta.objects.create(
                id_ven=int(values[0]),
                Tipo=values[1],
                fecha=values[2],
                id_usu=usuario,
                id_asignado=asignado,
                id_Cliente=cliente,
                total=Decimal(values[6]),
                estado=values[7],
                observaciones=values[8] if values[8] != 'NULL' else ''
            )
        except Exception as e:
            print(f"⚠️  Error importando venta {values[0]}: {e}")
print(f"✅ {Venta.objects.count()} ventas importadas")

# 12. IMPORTAR PAGOS
print("\n📥 PASO 12: Importando pagos...")
pagos_data = extract_insert_data('pago', sql_content)
for row in pagos_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 5:
        try:
            venta = Venta.objects.get(id_ven=int(values[1]))
            Pago.objects.create(
                id_pago=int(values[0]),
                id_ven=venta,
                fecha_pago=values[2],
                monto=Decimal(values[3]),
                tipo_pago=values[4]
            )
        except Exception as e:
            print(f"⚠️  Error importando pago {values[0]}: {e}")
print(f"✅ {Pago.objects.count()} pagos importados")

# 13. IMPORTAR VENTA PRODUCCIÓN
print("\n📥 PASO 13: Importando venta-producción...")
venta_prod_data = extract_insert_data('venta_produccion', sql_content)
for row in venta_prod_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 4:
        try:
            venta = Venta.objects.get(id_ven=int(values[1]))
            produccion = Produccion.objects.get(id_proc=int(values[2]))
            VentaProduccion.objects.create(
                id_ven_prod=int(values[0]),
                id_venta=venta,
                id_produccion=produccion,
                cantidad=int(values[3])
            )
        except Exception as e:
            print(f"⚠️  Error importando venta-producción {values[0]}: {e}")
print(f"✅ {VentaProduccion.objects.count()} relaciones venta-producción importadas")

# 14. IMPORTAR VENTA RECETAS
print("\n📥 PASO 14: Importando venta-recetas...")
venta_recetas_data = extract_insert_data('venta_recetas', sql_content)
for row in venta_recetas_data:
    values = [v.strip().strip("'") for v in row.split(',')]
    if len(values) >= 6:
        try:
            venta = Venta.objects.get(id_ven=int(values[1]))
            receta = Receta.objects.get(id_rec=int(values[2]))
            VentaReceta.objects.create(
                id_venta_receta=int(values[0]),
                id_venta=venta,
                id_receta=receta,
                cantidad=int(values[3]),
                precio=Decimal(values[4]),
                subtotal=Decimal(values[5])
            )
        except Exception as e:
            print(f"⚠️  Error importando venta-receta {values[0]}: {e}")
print(f"✅ {VentaReceta.objects.count()} relaciones venta-receta importadas")

print("\n" + "=" * 80)
print("✅ IMPORTACIÓN COMPLETADA - TODAS LAS TABLAS")
print("=" * 80)
print(f"\n📊 Resumen completo:")
print(f"   - Usuarios: {Usuario.objects.count()}")
print(f"   - Clientes: {Cliente.objects.count()}")
print(f"   - Insumos: {Insumo.objects.count()}")
print(f"   - Detalles de Insumo: {DetalleInsumo.objects.count()}")
print(f"   - Historial de Insumos: {HistorialInsumo.objects.count()}")
print(f"   - Recetas: {Receta.objects.count()}")
print(f"   - Receta-Insumos: {RecetaInsumo.objects.count()}")
print(f"   - Producción: {Produccion.objects.count()}")
print(f"   - Producción-Recetas: {ProduccionReceta.objects.count()}")
print(f"   - Ventas: {Venta.objects.count()}")
print(f"   - Pagos: {Pago.objects.count()}")
print(f"   - Venta-Producción: {VentaProduccion.objects.count()}")
print(f"   - Venta-Recetas: {VentaReceta.objects.count()}")
print("\n⚠️  Nota: Las contraseñas de los usuarios del SQL pueden estar en texto plano.")
print("   Ejecuta 'python resetear_password.py' para establecer contraseñas conocidas.")
