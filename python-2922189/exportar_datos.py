"""
Script para exportar solo los DATOS de la base de datos
Genera un archivo SQL con solo los INSERT statements
"""
import os
import subprocess
from datetime import datetime

print("=" * 80)
print("EXPORTANDO DATOS DE LA BASE DE DATOS")
print("=" * 80)

# Configuración
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASSWORD = ""
DB_NAME = "pae"

# Tablas a exportar (en orden de dependencias)
TABLAS_EXPORTAR = [
    # Tablas base sin dependencias
    "usuarios",
    "clientes",
    "insumos",
    "recetas",
    
    # Tablas con dependencias de primer nivel
    "detalle_insumo",
    "receta_insumos",
    "historial",
    
    # Tablas de producción
    "produccion",
    "produccion_recetas",
    
    # Tablas de ventas
    "ventas",
    "pago",
    "venta_produccion",
    "venta_recetas",
]

# Nombre del archivo de salida
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = f"datos_pae_{timestamp}.sql"

print(f"\n📋 Exportando datos de la base de datos '{DB_NAME}'...")
print(f"📁 Archivo de salida: {output_file}")

total_registros = 0

with open(output_file, 'w', encoding='utf-8') as f:
    # Escribir encabezado
    f.write(f"-- Datos de la base de datos PAE\n")
    f.write(f"-- Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"-- Base de datos: {DB_NAME}\n\n")
    f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
    
    # Exportar cada tabla
    for tabla in TABLAS_EXPORTAR:
        print(f"\n📦 Exportando tabla: {tabla}")
        
        cmd = [
            "mysqldump",
            "-h", DB_HOST,
            "-P", DB_PORT,
            "-u", DB_USER,
            "--no-create-info",  # Solo datos, sin CREATE TABLE
            "--skip-comments",
            "--compact",
            "--complete-insert",  # INSERT con nombres de columnas
            DB_NAME,
            tabla
        ]
        
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                datos = result.stdout
                if datos.strip():
                    # Contar registros
                    registros = datos.count("INSERT INTO")
                    total_registros += registros
                    
                    # Escribir al archivo
                    f.write(f"-- Tabla: {tabla} ({registros} registros)\n")
                    f.write(datos)
                    f.write("\n\n")
                    
                    print(f"   ✅ {registros} registros exportados")
                else:
                    print(f"   ⚠️  Tabla vacía, omitida")
            else:
                print(f"   ❌ Error: {result.stderr}")
        
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    # Escribir pie
    f.write("SET FOREIGN_KEY_CHECKS=1;\n")

print("\n" + "=" * 80)
print("✅ EXPORTACIÓN COMPLETADA")
print("=" * 80)
print(f"\n📊 Resumen:")
print(f"   - Archivo: {output_file}")
print(f"   - Tablas exportadas: {len(TABLAS_EXPORTAR)}")
print(f"   - Total registros: {total_registros}")
print(f"   - Tamaño: {os.path.getsize(output_file)} bytes")
print("\n")
