#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from django.db import connection

def verificar_tablas():
    cursor = connection.cursor()
    
    tablas_a_verificar = [
        'venta_produccion',
        'detalle_venta', 
        'pago',
        'venta_recetas'
    ]
    
    for tabla in tablas_a_verificar:
        try:
            cursor.execute(f"SHOW TABLES LIKE '{tabla}'")
            result = cursor.fetchall()
            if result:
                print(f"✓ Tabla '{tabla}' existe")
                # Obtener estructura si existe
                cursor.execute(f"DESCRIBE {tabla}")
                columns = cursor.fetchall()
                print(f"Columnas de {tabla}:")
                for col in columns:
                    print(f"  - {col[0]} ({col[1]})")
                print()
            else:
                print(f"✗ Tabla '{tabla}' NO existe")
        except Exception as e:
            print(f"Error verificando {tabla}: {e}")
    
    cursor.close()

if __name__ == "__main__":
    verificar_tablas()