"""
Script maestro para importar la base de datos completa
Recrea la BD desde cero con estructura y datos
"""
import os
import django
import subprocess
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from django.core.management import call_command

# Configuración
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "pae"
ARCHIVO_SQL = "pae.sql"  # Cambia esto al archivo que quieras importar

print("=" * 80)
print("IMPORTACIÓN COMPLETA DE BASE DE DATOS PAE")
print("=" * 80)

def ejecutar_mysql(comando, usar_db=True):
    """Ejecuta un comando MySQL"""
    cmd = ["mysql", "-u", DB_USER, "-h", DB_HOST, "-P", DB_PORT]
    if usar_db:
        cmd.append(DB_NAME)
    cmd.extend(["-e", comando])
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout, result.stderr

def importar_sql_file(archivo):
    """Importa un archivo SQL completo"""
    if not os.path.exists(archivo):
        print(f"❌ Error: Archivo '{archivo}' no encontrado")
        return False
    
    cmd = f'cmd /c "mysql -u {DB_USER} -h {DB_HOST} -P {DB_PORT} {DB_NAME} < {archivo} 2>&1"'
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.returncode == 0

# PASO 1: Eliminar y recrear la base de datos
print("\n🗑️  PASO 1: Recreando base de datos...")
exito, stdout, stderr = ejecutar_mysql(
    f"DROP DATABASE IF EXISTS {DB_NAME}; CREATE DATABASE {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
    usar_db=False
)

if exito:
    print("   ✅ Base de datos recreada")
else:
    print(f"   ❌ Error: {stderr}")
    sys.exit(1)

# PASO 2: Importar estructura y datos desde SQL
print(f"\n📥 PASO 2: Importando archivo SQL '{ARCHIVO_SQL}'...")

if importar_sql_file(ARCHIVO_SQL):
    print("   ✅ Datos importados desde SQL")
    
    # Mostrar estadísticas
    exito, stdout, stderr = ejecutar_mysql("""
        SELECT 'Usuarios:' AS Tabla, COUNT(*) AS Total FROM usuarios
        UNION SELECT 'Clientes:', COUNT(*) FROM clientes
        UNION SELECT 'Insumos:', COUNT(*) FROM insumos
        UNION SELECT 'Recetas:', COUNT(*) FROM recetas
        UNION SELECT 'Ventas:', COUNT(*) FROM ventas
        UNION SELECT 'Producción:', COUNT(*) FROM produccion;
    """)
    
    if exito:
        print("\n   📊 Datos importados:")
        print("   " + stdout.replace("\n", "\n   "))
else:
    print("   ❌ Error al importar SQL")
    sys.exit(1)

# PASO 3: Ejecutar migraciones de Django (fake)
print("\n🔧 PASO 3: Sincronizando migraciones de Django...")

try:
    # Primero las migraciones normales (tablas de Django)
    call_command('migrate', '--fake-initial', verbosity=0)
    
    # Luego marcar como fake las migraciones de nuestras apps
    apps_pae = ['clientes', 'insumos', 'recetas', 'usuarios', 'produccion', 'ventas']
    for app in apps_pae:
        call_command('migrate', app, '--fake', verbosity=0)
    
    print("   ✅ Migraciones sincronizadas")
    
except Exception as e:
    print(f"   ❌ Error en migraciones: {e}")
    sys.exit(1)

# PASO 4: Crear tabla de sesiones si no existe
print("\n📋 PASO 4: Verificando tabla de sesiones...")

exito, stdout, stderr = ejecutar_mysql("""
    CREATE TABLE IF NOT EXISTS django_session (
        session_key varchar(40) NOT NULL PRIMARY KEY,
        session_data longtext NOT NULL,
        expire_date datetime(6) NOT NULL,
        KEY django_session_expire_date_a5c62663 (expire_date)
    );
""")

if exito:
    print("   ✅ Tabla de sesiones lista")
else:
    print(f"   ⚠️  Advertencia: {stderr}")

# PASO 5: Verificación final
print("\n✅ PASO 5: Verificación final...")

exito, stdout, stderr = ejecutar_mysql("SHOW TABLES;")

if exito:
    tablas = stdout.strip().split('\n')[1:]  # Omitir encabezado
    print(f"   ✅ Total de tablas: {len(tablas)}")
else:
    print(f"   ❌ Error: {stderr}")

print("\n" + "=" * 80)
print("✅ IMPORTACIÓN COMPLETADA EXITOSAMENTE")
print("=" * 80)
print("\n💡 Tu base de datos está lista para usar")
print("   Ejecuta: python manage.py runserver\n")
