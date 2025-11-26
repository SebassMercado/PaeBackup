import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

# Importar el modelo
from modelos.usuarios.models import Usuario

try:
    # Probar conexión
    count = Usuario.objects.count()
    print(f"✅ Conexión exitosa!")
    print(f"📊 Total usuarios en la BD: {count}")
    
    # Mostrar algunos usuarios
    if count > 0:
        usuarios = Usuario.objects.all()[:5]
        print("\n👥 Primeros 5 usuarios:")
        for u in usuarios:
            print(f"  - {u.nombre_completo} ({u.get_rol_display_extended}) - {u.correo}")
    
except Exception as e:
    print(f"❌ Error: {e}")