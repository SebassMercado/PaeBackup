import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario
from modelos.recetas.models import Receta
from modelos.produccion.models import Produccion
from modelos.ventas.models import Venta

print("=" * 50)
print("VERIFICACIÓN DE DATOS PARA DASHBOARD")
print("=" * 50)

print(f"\n📊 Usuarios activos: {Usuario.objects.filter(estado='A').count()}")
print(f"📜 Recetas totales: {Receta.objects.count()}")
print(f"🏭 Producciones totales: {Produccion.objects.count()}")
print(f"💰 Ventas totales: {Venta.objects.count()}")

print("\n" + "=" * 50)
print("DETALLES DE USUARIOS")
print("=" * 50)

for usuario in Usuario.objects.filter(estado='A')[:5]:
    print(f"- {usuario.nombres} {usuario.apellidos} ({usuario.get_rol_display()}) - {usuario.correo}")

print("\n" + "=" * 50)
print("DETALLES DE RECETAS")
print("=" * 50)

for receta in Receta.objects.all()[:5]:
    print(f"- {receta.nombre} ({receta.estado})")

print("\n✅ Verificación completada")
