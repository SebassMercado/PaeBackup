"""
Script para probar la actualización automática de estados de recetas
basado en el estado de los insumos asociados
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.recetas.models import Receta, RecetaInsumo
from modelos.insumos.models import Insumo

def mostrar_estado_receta(receta):
    """Muestra el estado actual de una receta y sus insumos"""
    print(f"\n{'='*80}")
    print(f"RECETA: {receta.nombre} - Estado: {receta.estado}")
    print(f"{'='*80}")
    
    ingredientes = receta.ingredientes.all()
    if not ingredientes.exists():
        print("  ⚠️  No tiene ingredientes")
        return
    
    for ing in ingredientes:
        print(f"  📦 {ing.insumo.nombre}")
        print(f"     - Estado Insumo: {ing.insumo.estado}")
        print(f"     - Stock: {ing.insumo.stock_actual} / Min: {ing.insumo.stock_min}")
        print(f"     - Cantidad necesaria: {ing.cantidad}")
        print(f"     - Estado Ingrediente: {ing.estado}")

def test_estados_recetas():
    """Prueba la actualización de estados de recetas"""
    print("\n" + "="*80)
    print("TEST: Actualización automática de estados de recetas")
    print("="*80)
    
    # Obtener todas las recetas
    recetas = Receta.objects.all()
    
    if not recetas.exists():
        print("\n⚠️  No hay recetas en la base de datos")
        return
    
    print(f"\n📊 Total de recetas: {recetas.count()}")
    print(f"   - Activas: {recetas.filter(estado='Activo').count()}")
    print(f"   - Inactivas: {recetas.filter(estado='Inactivo').count()}")
    
    # Mostrar estado actual de cada receta
    print("\n" + "="*80)
    print("ESTADO ACTUAL DE LAS RECETAS")
    print("="*80)
    
    for receta in recetas:
        mostrar_estado_receta(receta)
    
    # Actualizar estados
    print("\n" + "="*80)
    print("ACTUALIZANDO ESTADOS...")
    print("="*80)
    
    recetas_actualizadas = 0
    for receta in recetas:
        if receta.verificar_y_actualizar_estado():
            receta.save()
            recetas_actualizadas += 1
            print(f"✅ {receta.nombre} - Estado actualizado a: {receta.estado}")
        else:
            print(f"ℹ️  {receta.nombre} - Sin cambios (Estado: {receta.estado})")
    
    print(f"\n📊 Recetas actualizadas: {recetas_actualizadas}")
    
    # Mostrar estado final
    print("\n" + "="*80)
    print("ESTADO FINAL DE LAS RECETAS")
    print("="*80)
    
    recetas = Receta.objects.all()
    print(f"\n📊 Total de recetas: {recetas.count()}")
    print(f"   - Activas: {recetas.filter(estado='Activo').count()}")
    print(f"   - Inactivas: {recetas.filter(estado='Inactivo').count()}")
    
    for receta in recetas:
        puede_producir, razon = receta.puede_producirse()
        simbolo = "✅" if puede_producir else "❌"
        print(f"{simbolo} {receta.nombre} - Estado: {receta.estado} - {razon}")

def test_caso_especifico():
    """Prueba un caso específico de actualización"""
    print("\n" + "="*80)
    print("TEST CASO ESPECÍFICO: Cambiar estado de insumo y verificar recetas")
    print("="*80)
    
    # Buscar un insumo activo que esté en alguna receta
    insumos = Insumo.objects.filter(estado='Activo', recetas_que_usan__isnull=False).distinct()
    
    if not insumos.exists():
        print("\n⚠️  No hay insumos activos en recetas")
        return
    
    insumo = insumos.first()
    print(f"\n📦 Insumo seleccionado: {insumo.nombre} (Estado: {insumo.estado})")
    
    # Mostrar recetas que usan este insumo
    recetas_afectadas = Receta.objects.filter(ingredientes__insumo=insumo).distinct()
    print(f"📋 Recetas que usan este insumo: {recetas_afectadas.count()}")
    
    for receta in recetas_afectadas:
        print(f"   - {receta.nombre} (Estado: {receta.estado})")
    
    # Simular cambio de estado del insumo
    estado_original = insumo.estado
    print(f"\n🔄 Cambiando estado de '{insumo.nombre}' de '{estado_original}' a 'Inactivo'...")
    insumo.estado = 'Inactivo'
    insumo.save()
    
    # Verificar actualización de recetas
    print("\n📊 Verificando actualización de recetas...")
    recetas_actualizadas = Receta.actualizar_estados_por_insumo(insumo)
    
    if recetas_actualizadas:
        print(f"✅ {len(recetas_actualizadas)} recetas actualizadas:")
        for receta in recetas_actualizadas:
            print(f"   - {receta.nombre} -> Estado: {receta.estado}")
    else:
        print("ℹ️  No se actualizaron recetas")
    
    # Restaurar estado original
    print(f"\n🔄 Restaurando estado original de '{insumo.nombre}'...")
    insumo.estado = estado_original
    insumo.save()
    
    # Verificar nueva actualización
    recetas_actualizadas = Receta.actualizar_estados_por_insumo(insumo)
    
    if recetas_actualizadas:
        print(f"✅ {len(recetas_actualizadas)} recetas restauradas:")
        for receta in recetas_actualizadas:
            print(f"   - {receta.nombre} -> Estado: {receta.estado}")

if __name__ == "__main__":
    try:
        print("\n🚀 Iniciando pruebas de estados de recetas...")
        
        # Test 1: Actualizar todas las recetas
        test_estados_recetas()
        
        # Test 2: Caso específico
        test_caso_especifico()
        
        print("\n✅ Pruebas completadas exitosamente")
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
