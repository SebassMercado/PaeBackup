"""
Utilidades para el módulo de recetas
"""

from django.db import transaction
from .models import RecetaInsumo


def actualizar_estados_ingredientes_por_insumo(insumo):
    """
    Actualiza automáticamente el estado de todos los ingredientes 
    que usan un insumo específico cuando este cambia de estado
    """
    ingredientes_actualizados = []
    
    try:
        with transaction.atomic():
            # Obtener todos los ingredientes que usan este insumo
            ingredientes = RecetaInsumo.objects.filter(insumo=insumo).select_related('receta')
            
            for ingrediente in ingredientes:
                estado_anterior = ingrediente.estado
                
                # Verificar y actualizar disponibilidad
                if ingrediente.verificar_disponibilidad():
                    ingrediente.save()
                    ingredientes_actualizados.append({
                        'ingrediente': ingrediente,
                        'estado_anterior': estado_anterior,
                        'estado_nuevo': ingrediente.estado,
                        'receta': ingrediente.receta.nombre
                    })
                    
                    print(f"Ingrediente actualizado: {ingrediente.insumo.nombre} en receta "
                          f"'{ingrediente.receta.nombre}': {estado_anterior} -> {ingrediente.estado}")
    
    except Exception as e:
        print(f"Error actualizando ingredientes para insumo {insumo.nombre}: {e}")
    
    return ingredientes_actualizados


def verificar_disponibilidad_recetas():
    """
    Verifica la disponibilidad de todas las recetas 
    basándose en el estado de sus ingredientes
    """
    from .models import Receta
    
    recetas_procesadas = []
    
    try:
        recetas = Receta.objects.filter(estado='Activo').prefetch_related('ingredientes__insumo')
        
        for receta in recetas:
            puede_producirse, razon = receta.puede_producirse()
            
            recetas_procesadas.append({
                'receta': receta.nombre,
                'puede_producirse': puede_producirse,
                'razon': razon,
                'ingredientes_agotados': receta.ingredientes.filter(estado='Agotado').count()
            })
    
    except Exception as e:
        print(f"Error verificando disponibilidad de recetas: {e}")
    
    return recetas_procesadas


def actualizar_todos_los_estados_ingredientes():
    """
    Actualiza el estado de TODOS los ingredientes del sistema
    basándose en el estado actual de sus insumos
    """
    ingredientes_actualizados = 0
    
    try:
        with transaction.atomic():
            # Obtener todos los ingredientes
            ingredientes = RecetaInsumo.objects.select_related('insumo', 'receta').all()
            
            for ingrediente in ingredientes:
                estado_anterior = ingrediente.estado
                
                # Verificar disponibilidad y actualizar si es necesario
                if ingrediente.verificar_disponibilidad():
                    ingrediente.save()
                    ingredientes_actualizados += 1
                    
                    print(f"Ingrediente {ingrediente.insumo.nombre} en receta "
                          f"{ingrediente.receta.nombre}: {estado_anterior} -> {ingrediente.estado}")
        
        print(f"Actualización completa: {ingredientes_actualizados} ingredientes actualizados")
    
    except Exception as e:
        print(f"Error en actualización masiva de ingredientes: {e}")
    
    return ingredientes_actualizados


def obtener_estadisticas_disponibilidad():
    """
    Obtiene estadísticas generales sobre disponibilidad de recetas e ingredientes
    """
    from .models import Receta
    
    try:
        # Estadísticas de recetas
        total_recetas = Receta.objects.filter(estado='Activo').count()
        recetas_disponibles = 0
        recetas_no_disponibles = 0
        
        for receta in Receta.objects.filter(estado='Activo'):
            puede_producirse, _ = receta.puede_producirse()
            if puede_producirse:
                recetas_disponibles += 1
            else:
                recetas_no_disponibles += 1
        
        # Estadísticas de ingredientes
        total_ingredientes = RecetaInsumo.objects.count()
        ingredientes_activos = RecetaInsumo.objects.filter(estado='Activo').count()
        ingredientes_agotados = RecetaInsumo.objects.filter(estado='Agotado').count()
        
        return {
            'recetas': {
                'total': total_recetas,
                'disponibles': recetas_disponibles,
                'no_disponibles': recetas_no_disponibles,
                'porcentaje_disponibles': (recetas_disponibles / total_recetas * 100) if total_recetas > 0 else 0
            },
            'ingredientes': {
                'total': total_ingredientes,
                'activos': ingredientes_activos,
                'agotados': ingredientes_agotados,
                'porcentaje_activos': (ingredientes_activos / total_ingredientes * 100) if total_ingredientes > 0 else 0
            }
        }
    
    except Exception as e:
        print(f"Error obteniendo estadísticas: {e}")
        return None


def sincronizar_todas_las_recetas():
    """
    Sincroniza el estado de todas las recetas con el estado de sus insumos
    Útil para ejecutar después de cambios masivos en insumos
    """
    from .models import Receta, RecetaInsumo
    
    # Estadísticas
    recetas_desactivadas = []
    recetas_reactivadas = []
    ingredientes_actualizados = []
    
    print("🔄 Iniciando sincronización completa de recetas...")
    
    # Paso 1: Actualizar todos los ingredientes basado en el estado de sus insumos
    print("📋 Paso 1: Actualizando estados de ingredientes...")
    
    with transaction.atomic():
        for ingrediente in RecetaInsumo.objects.select_related('insumo', 'receta').all():
            if ingrediente.verificar_disponibilidad():
                ingrediente.save()
                ingredientes_actualizados.append(ingrediente)
                print(f"  ✅ Ingrediente actualizado: {ingrediente.insumo.nombre} en {ingrediente.receta.nombre} → {ingrediente.estado}")
    
    # Paso 2: Actualizar todas las recetas basado en sus ingredientes
    print("🍽️ Paso 2: Actualizando estados de recetas...")
    
    with transaction.atomic():
        for receta in Receta.objects.prefetch_related('ingredientes').all():
            estado_anterior = receta.estado
            
            if receta.verificar_y_actualizar_estado():
                receta.save()
                
                if estado_anterior == 'Activo' and receta.estado == 'Inactivo':
                    recetas_desactivadas.append(receta)
                    print(f"  🔴 Receta desactivada: {receta.nombre}")
                elif estado_anterior == 'Inactivo' and receta.estado == 'Activo':
                    recetas_reactivadas.append(receta)
                    print(f"  🟢 Receta reactivada: {receta.nombre}")
    
    # Resumen
    print("\n📊 RESUMEN DE SINCRONIZACIÓN:")
    print(f"  • Ingredientes actualizados: {len(ingredientes_actualizados)}")
    print(f"  • Recetas desactivadas: {len(recetas_desactivadas)}")
    print(f"  • Recetas reactivadas: {len(recetas_reactivadas)}")
    
    return {
        'ingredientes_actualizados': len(ingredientes_actualizados),
        'recetas_desactivadas': len(recetas_desactivadas),
        'recetas_reactivadas': len(recetas_reactivadas),
        'recetas_desactivadas_nombres': [r.nombre for r in recetas_desactivadas],
        'recetas_reactivadas_nombres': [r.nombre for r in recetas_reactivadas]
    }


def generar_reporte_recetas_afectadas():
    """
    Genera un reporte de las recetas afectadas por insumos agotados
    """
    from .models import Receta
    
    reporte = {
        'recetas_inactivas_por_insumos': [],
        'recetas_activas_con_problemas': [],
        'insumos_criticos': set(),
        'estadisticas': {}
    }
    
    try:
        # Recetas inactivas por falta de insumos
        for receta in Receta.objects.filter(estado='Inactivo').prefetch_related('ingredientes__insumo'):
            ingredientes_agotados = receta.ingredientes.filter(estado='Agotado')
            
            if ingredientes_agotados.exists():
                nombres_insumos = [ing.insumo.nombre for ing in ingredientes_agotados]
                reporte['recetas_inactivas_por_insumos'].append({
                    'nombre': receta.nombre,
                    'precio': receta.precio,
                    'insumos_agotados': nombres_insumos
                })
                reporte['insumos_criticos'].update(nombres_insumos)
        
        # Recetas activas con problemas (no deberían existir si el sistema funciona bien)
        for receta in Receta.objects.filter(estado='Activo').prefetch_related('ingredientes__insumo'):
            puede_producir, mensaje = receta.puede_producirse()
            
            if not puede_producir:
                ingredientes_agotados = receta.ingredientes.filter(estado='Agotado')
                nombres_insumos = [ing.insumo.nombre for ing in ingredientes_agotados]
                
                reporte['recetas_activas_con_problemas'].append({
                    'nombre': receta.nombre,
                    'precio': receta.precio,
                    'problema': mensaje,
                    'insumos_agotados': nombres_insumos
                })
                reporte['insumos_criticos'].update(nombres_insumos)
        
        # Estadísticas
        total_recetas = Receta.objects.count()
        reporte['estadisticas'] = {
            'total_recetas': total_recetas,
            'recetas_inactivas_por_insumos': len(reporte['recetas_inactivas_por_insumos']),
            'recetas_activas_con_problemas': len(reporte['recetas_activas_con_problemas']),
            'insumos_criticos': len(reporte['insumos_criticos']),
            'porcentaje_afectadas': ((len(reporte['recetas_inactivas_por_insumos']) + 
                                    len(reporte['recetas_activas_con_problemas'])) / total_recetas * 100) if total_recetas > 0 else 0
        }
        
        reporte['insumos_criticos'] = list(reporte['insumos_criticos'])
        
    except Exception as e:
        print(f"Error generando reporte de recetas afectadas: {e}")
    
    return reporte