import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from django.contrib.sessions.models import Session

# Eliminar todas las sesiones activas
Session.objects.all().delete()
print("✅ Todas las sesiones han sido eliminadas")
print("Ahora debes cerrar el navegador y volver a abrir para que te pida login")
