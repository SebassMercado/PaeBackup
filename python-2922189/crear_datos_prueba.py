"""
Script para crear datos de prueba en el sistema PAE
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario

# Crear usuario administrador de prueba
usuario_admin = Usuario.objects.create(
    documento=12345678,
    nombres='Admin',
    apellidos='Sistema',
    telefono=3001234567,
    direccion='Calle 123 #45-67',
    correo='admin@pae.com',
    rol='A',
    estado='A',
    password='123456'
)

print(f"✅ Usuario administrador creado:")
print(f"   - Correo: admin@pae.com")
print(f"   - Contraseña: 123456")
print(f"   - Rol: Administrador")

# Crear usuario empleado de ventas
usuario_ventas = Usuario.objects.create(
    documento=87654321,
    nombres='Empleado',
    apellidos='Ventas',
    telefono=3007654321,
    direccion='Carrera 456 #78-90',
    correo='ventas@pae.com',
    rol='EV',
    estado='A',
    password='123456'
)

print(f"✅ Usuario empleado de ventas creado:")
print(f"   - Correo: ventas@pae.com")
print(f"   - Contraseña: 123456")
print(f"   - Rol: Empleado Ventas")

# Crear usuario empleado de producción
usuario_produccion = Usuario.objects.create(
    documento=11223344,
    nombres='Empleado',
    apellidos='Producción',
    telefono=3001122334,
    direccion='Avenida 789 #12-34',
    correo='produccion@pae.com',
    rol='EP',
    estado='A',
    password='123456'
)

print(f"✅ Usuario empleado de producción creado:")
print(f"   - Correo: produccion@pae.com")
print(f"   - Contraseña: 123456")
print(f"   - Rol: Empleado Producción")

print(f"\n🎉 ¡Datos de prueba creados exitosamente!")
print(f"Ahora puedes probar el sistema con cualquiera de estos usuarios.")