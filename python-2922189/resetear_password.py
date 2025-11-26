import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario

print("=" * 70)
print("RESETEANDO CONTRASEÑAS DE TODOS LOS USUARIOS")
print("=" * 70)

# Contraseña por defecto
password_default = '12345'

usuarios = Usuario.objects.all()
for usuario in usuarios:
    usuario.set_password(password_default)
    usuario.save()
    print(f"✅ {usuario.nombres} {usuario.apellidos}")
    print(f"   Correo: {usuario.correo}")
    print(f"   Documento: {usuario.documento}")
    print(f"   Nueva contraseña: {password_default}")
    print()

print("=" * 70)
print(f"COMPLETADO: {usuarios.count()} usuarios actualizados")
print(f"Contraseña para todos: {password_default}")
print("=" * 70)
print("\nPuedes ingresar con:")
print("- Correo o Documento")
print(f"- Contraseña: {password_default}")
