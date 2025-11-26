import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario
from modelos.clientes.models import Cliente
from modelos.insumos.models import Insumo
from modelos.recetas.models import Receta
from modelos.produccion.models import Produccion
from modelos.ventas.models import Venta

print("=" * 70)
print("VERIFICANDO DATOS EN MYSQL")
print("=" * 70)

print(f"\n📊 Resumen de datos importados:")
print(f"   - Usuarios: {Usuario.objects.count()}")
print(f"   - Clientes: {Cliente.objects.count()}")
print(f"   - Insumos: {Insumo.objects.count()}")
print(f"   - Recetas: {Receta.objects.count()}")
print(f"   - Producciones: {Produccion.objects.count()}")
print(f"   - Ventas: {Venta.objects.count()}")

print(f"\n👥 Usuarios activos:")
usuarios = Usuario.objects.filter(estado='A')[:5]
for u in usuarios:
    print(f"   - {u.nombres} {u.apellidos} ({u.correo}) - Rol: {u.get_rol_display_extended}")

print("\n" + "=" * 70)
print("⚠️  IMPORTANTE: Las contraseñas están en MD5/Bcrypt")
print("Necesitas resetearlas para poder ingresar")
print("Ejecuta: python resetear_password.py")
print("=" * 70)
