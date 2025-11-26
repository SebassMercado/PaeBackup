import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario
from modelos.clientes.models import Cliente
from modelos.insumos.models import Insumo, DetalleInsumo, HistorialInsumo
from modelos.recetas.models import Receta, RecetaInsumo
from modelos.produccion.models import Produccion, ProduccionReceta
from modelos.ventas.models import Venta, Pago, DetalleVenta, VentaProduccion, VentaReceta

print("=" * 70)
print("LIMPIANDO BASE DE DATOS")
print("=" * 70)

# Eliminar en orden inverso para evitar errores de FK
print("\n🗑️  Eliminando Ventas y relaciones...")
VentaReceta.objects.all().delete()
VentaProduccion.objects.all().delete()
DetalleVenta.objects.all().delete()
Pago.objects.all().delete()
Venta.objects.all().delete()

print("🗑️  Eliminando Producciones y relaciones...")
ProduccionReceta.objects.all().delete()
Produccion.objects.all().delete()

print("🗑️  Eliminando Recetas y relaciones...")
RecetaInsumo.objects.all().delete()
Receta.objects.all().delete()

print("🗑️  Eliminando Insumos y relaciones...")
HistorialInsumo.objects.all().delete()
DetalleInsumo.objects.all().delete()
Insumo.objects.all().delete()

print("🗑️  Eliminando Clientes...")
Cliente.objects.all().delete()

print("🗑️  Eliminando Usuarios...")
Usuario.objects.all().delete()

print("\n" + "=" * 70)
print("✅ BASE DE DATOS LIMPIADA COMPLETAMENTE")
print("=" * 70)
print("\nAhora puedes importar los datos del archivo SQL")
