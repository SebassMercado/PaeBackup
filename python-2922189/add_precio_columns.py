#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from django.db import connection

def agregar_columnas_precio():
    """Agregar columnas de precio a la tabla detalle_insumo"""
    with connection.cursor() as cursor:
        try:
            # Verificar si las columnas ya existen
            cursor.execute("""
                SELECT COLUMN_NAME 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = 'pae' 
                AND TABLE_NAME = 'detalle_insumo' 
                AND COLUMN_NAME IN ('precio_unitario', 'precio_total')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            if 'precio_unitario' not in existing_columns:
                print("Agregando columna precio_unitario...")
                cursor.execute("""
                    ALTER TABLE detalle_insumo 
                    ADD COLUMN precio_unitario DECIMAL(10,2) DEFAULT 0.00 NOT NULL 
                    AFTER fecha_vencimiento
                """)
                print("✅ Columna precio_unitario agregada")
            else:
                print("✅ Columna precio_unitario ya existe")
            
            if 'precio_total' not in existing_columns:
                print("Agregando columna precio_total...")
                cursor.execute("""
                    ALTER TABLE detalle_insumo 
                    ADD COLUMN precio_total DECIMAL(10,2) DEFAULT 0.00 NOT NULL 
                    AFTER precio_unitario
                """)
                print("✅ Columna precio_total agregada")
            else:
                print("✅ Columna precio_total ya existe")
                
            print("\n🎉 Columnas de precio agregadas exitosamente!")
            
        except Exception as e:
            print(f"❌ Error al agregar columnas: {e}")

if __name__ == "__main__":
    agregar_columnas_precio()