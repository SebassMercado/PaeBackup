"""
Script para exportar la estructura actual de la base de datos
Genera un archivo SQL con solo la estructura (CREATE TABLE)
"""
import os
import subprocess
from datetime import datetime

print("=" * 80)
print("EXPORTANDO ESTRUCTURA DE LA BASE DE DATOS")
print("=" * 80)

# Configuración
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "pae"

# Nombre del archivo de salida
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"estructura_pae_{timestamp}.sql"

print(f"\n📋 Exportando estructura de la base de datos '{DB_NAME}'...")
print(f"📁 Archivo de salida: {output_file}")

# Comando mysqldump para exportar solo la estructura
cmd = [
    "mysqldump",
    "-h", DB_HOST,
    "-P", DB_PORT,
    "-u", DB_USER,
    "--no-data",  # Solo estructura, sin datos
    "--skip-comments",
    "--skip-add-drop-table",
    DB_NAME
]

try:
    # Ejecutar mysqldump
    with open(output_file, 'w', encoding='utf-8') as f:
        result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    
    if result.returncode == 0:
        print(f"✅ Estructura exportada exitosamente a: {output_file}")
        
        # Mostrar estadísticas
        with open(output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            table_count = content.count("CREATE TABLE")
            print(f"\n📊 Estadísticas:")
            print(f"   - Tablas encontradas: {table_count}")
            print(f"   - Tamaño del archivo: {os.path.getsize(output_file)} bytes")
    else:
        print(f"❌ Error al exportar: {result.stderr}")

except FileNotFoundError:
    print("❌ Error: mysqldump no encontrado. Asegúrate de tener MySQL instalado y en el PATH")
except Exception as e:
    print(f"❌ Error inesperado: {e}")

print("\n" + "=" * 80)
