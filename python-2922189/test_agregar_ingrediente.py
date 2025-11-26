#!/usr/bin/env python
"""
Script de debug para probar agregar ingredientes
"""
import os
import sys
import django

# Configurar Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.recetas.models import Receta, RecetaInsumo
from modelos.insumos.models import Insumo
from django.db import connection
from decimal import Decimal

def test_agregar_ingrediente():
    print("🔍 Iniciando test de agregar ingrediente...")
    
    # Listar recetas disponibles
    print("\n📋 Recetas disponibles:")
    recetas = Receta.objects.all()[:5]
    for r in recetas:
        print(f"  - ID: {r.id_rec}, Nombre: {r.nombre}")
    
    # Listar insumos disponibles
    print("\n📦 Insumos disponibles:")
    insumos = Insumo.objects.filter(estado='Activo')[:5]
    for i in insumos:
        print(f"  - ID: {i.id_ins}, Nombre: {i.nombre}, Unidad: {i.unidad_medida}")
    
    if not recetas.exists() or not insumos.exists():
        print("❌ No hay recetas o insumos disponibles")
        return
    
    # Probar inserción directa
    receta = recetas.first()
    insumo = insumos.first()
    cantidad = Decimal('1.50')
    
    print(f"\n🧪 Probando inserción:")
    print(f"  Receta: {receta.nombre} (ID: {receta.id_rec})")
    print(f"  Insumo: {insumo.nombre} (ID: {insumo.id_ins})")
    print(f"  Cantidad: {cantidad}")
    print(f"  Unidad: {insumo.unidad_medida}")
    
    try:
        # Verificar si ya existe
        if RecetaInsumo.objects.filter(receta=receta, insumo=insumo).exists():
            print("⚠️ El ingrediente ya existe, eliminándolo primero...")
            RecetaInsumo.objects.filter(receta=receta, insumo=insumo).delete()
        
        # Inserción con SQL directo
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO receta_insumos (id_rec, id_ins, cantidad, unidad, estado) VALUES (%s, %s, %s, %s, %s)",
                [receta.id_rec, insumo.id_ins, cantidad, insumo.unidad_medida, 'Activo']
            )
        
        print("✅ Inserción exitosa con SQL directo")
        
        # Verificar que se insertó
        ingrediente = RecetaInsumo.objects.filter(receta=receta, insumo=insumo).first()
        if ingrediente:
            print(f"✅ Verificación: {ingrediente}")
        else:
            print("❌ No se encontró el ingrediente insertado")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_agregar_ingrediente()