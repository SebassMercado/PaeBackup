#!/usr/bin/env python3
"""
Script para probar el endpoint de registro de ventas
"""

import os
import sys
import django
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from django.test import Client
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

def test_venta_endpoint():
    print("=== PRUEBA DEL ENDPOINT DE VENTAS ===")
    
    # Crear un cliente de prueba Django
    client = Client()
    
    # Datos de prueba para la venta
    datos_venta = {
        'cliente_id': '1',
        'usuario_id': '1',
        'total': '100.00',
        'detalles_venta': json.dumps([
            {
                'receta_id': 43,
                'cantidad': 2,
                'precio': 50.00
            }
        ])
    }
    
    print("Datos de la venta:", datos_venta)
    
    try:
        # Intentar hacer una petición POST
        print("\n--- Haciendo petición POST ---")
        response = client.post('/ventas/procesar-nueva/', datos_venta)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.items())}")
        
        if hasattr(response, 'content'):
            content = response.content.decode('utf-8')
            print(f"Response Content (primeros 500 chars): {content[:500]}")
        
        if response.status_code == 302:
            print(f"Redirección a: {response.get('Location', 'No especificado')}")
        
        return response
        
    except Exception as e:
        print(f"Error durante la petición: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_venta_get():
    print("\n=== PRUEBA DEL ENDPOINT GET ===")
    
    client = Client()
    
    try:
        response = client.get('/ventas/nueva/')
        print(f"GET Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("La página de nueva venta se carga correctamente")
        else:
            print(f"Error al cargar la página: {response.status_code}")
            
        return response
        
    except Exception as e:
        print(f"Error durante GET: {e}")
        return None

if __name__ == "__main__":
    # Probar GET primero
    test_venta_get()
    
    # Luego probar POST
    test_venta_endpoint()