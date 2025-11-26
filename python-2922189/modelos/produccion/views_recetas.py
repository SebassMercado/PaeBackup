from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
import json

from .models import Produccion, ProduccionReceta
from modelos.recetas.models import Receta, RecetaInsumo
from modelos.insumos.models import Insumo


# @login_required
def listar_recetas_produccion(request, produccion_id):
    """
    Vista para listar recetas asociadas a una producción
    Equivalente a: produccion_recetasBean.java - init() y cargarRecetasPorProduccion()
    """
    produccion = get_object_or_404(Produccion, id_proc=produccion_id)
    
    # Obtener recetas asociadas a esta producción
    recetas_produccion = ProduccionReceta.objects.filter(
        produccion=produccion
    ).select_related('receta').order_by('id_detalle')
    
    # Obtener todas las recetas activas para agregar nuevas
    recetas_activas = Receta.objects.filter(
        estado='Activa'
    ).order_by('nombre')
    
    # Calcular totales
    total_cantidad = recetas_produccion.aggregate(
        total=Sum('cantidad')
    )['total'] or 0
    
    total_valor = sum(
        detalle.valor_total_produccion 
        for detalle in recetas_produccion
    )
    
    # Información adicional de cada receta
    detalles_recetas = []
    for detalle in recetas_produccion:
        ingredientes_info = obtener_info_ingredientes(detalle)
        
        detalles_recetas.append({
            'detalle': detalle,
            'ingredientes_info': ingredientes_info,
            'tiene_stock': all(ing['suficiente'] for ing in ingredientes_info),
            'ingredientes_faltantes': [ing for ing in ingredientes_info if not ing['suficiente']]
        })
    
    context = {
        'produccion': produccion,
        'recetas_produccion': recetas_produccion,
        'detalles_recetas': detalles_recetas,
        'recetas_activas': recetas_activas,
        'total_cantidad': total_cantidad,
        'total_valor': total_valor,
        'puede_editar': produccion.estado in ['Pendiente', 'Esperando insumos'],
    }
    
    return render(request, 'produccion/recetas.html', context)


@transaction.atomic
def agregar_receta_produccion(request, produccion_id):
    """
    Agrega una receta a una producción
    """
    if request.method == 'POST':
        try:
            produccion = get_object_or_404(Produccion, id_proc=produccion_id)
            
            # Validar que se puede editar
            if produccion.estado not in ['Pendiente', 'Esperando insumos']:
                messages.error(request, 'No se puede editar una producción en este estado')
                return redirect('produccion:recetas', produccion_id=produccion_id)
            
            receta_id = request.POST.get('receta_id')
            cantidad = request.POST.get('cantidad', 1)
            
            # Validaciones
            if not receta_id:
                messages.error(request, 'Debe seleccionar una receta')
                return redirect('produccion:recetas', produccion_id=produccion_id)
            
            try:
                cantidad = int(cantidad)
                if cantidad <= 0:
                    messages.error(request, 'La cantidad debe ser mayor a cero')
                    return redirect('produccion:recetas', produccion_id=produccion_id)
            except (ValueError, TypeError):
                messages.error(request, 'Cantidad inválida')
                return redirect('produccion:recetas', produccion_id=produccion_id)
            
            # Obtener receta
            receta = get_object_or_404(Receta, id_rec=receta_id)
            
            # Verificar que no esté duplicada
            if ProduccionReceta.objects.filter(produccion=produccion, receta=receta).exists():
                messages.error(request, f'La receta "{receta.nombre}" ya está agregada a esta producción')
                return redirect('produccion:recetas', produccion_id=produccion_id)
            
            # Crear detalle
            detalle = ProduccionReceta.objects.create(
                produccion=produccion,
                receta=receta,
                cantidad=cantidad
            )
            
            messages.success(request, f'Receta "{receta.nombre}" agregada correctamente')
            
        except Exception as e:
            messages.error(request, f'Error al agregar receta: {str(e)}')
    
    return redirect('produccion:recetas', produccion_id=produccion_id)


def actualizar_cantidad_receta(request, detalle_id):
    """
    Actualiza la cantidad de una receta en la producción
    """
    if request.method == 'POST':
        try:
            detalle = get_object_or_404(ProduccionReceta, id_detalle=detalle_id)
            
            # Validar que se puede editar
            if detalle.produccion.estado not in ['Pendiente', 'Esperando insumos']:
                return JsonResponse({
                    'success': False,
                    'error': 'No se puede editar una producción en este estado'
                })
            
            nueva_cantidad = request.POST.get('cantidad', 1)
            
            try:
                nueva_cantidad = int(nueva_cantidad)
                if nueva_cantidad <= 0:
                    return JsonResponse({
                        'success': False,
                        'error': 'La cantidad debe ser mayor a cero'
                    })
            except (ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Cantidad inválida'
                })
            
            # Actualizar cantidad
            detalle.cantidad = nueva_cantidad
            detalle.save()
            
            # Validar stock con nueva cantidad
            ingredientes_info = obtener_info_ingredientes(detalle)
            tiene_stock = all(ing['suficiente'] for ing in ingredientes_info)
            
            return JsonResponse({
                'success': True,
                'nueva_cantidad': nueva_cantidad,
                'valor_total': float(detalle.valor_total_produccion),
                'tiene_stock': tiene_stock,
                'mensaje': f'Cantidad actualizada a {nueva_cantidad}'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al actualizar cantidad: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


def eliminar_receta_produccion(request, detalle_id):
    """
    Elimina una receta de la producción
    """
    try:
        detalle = get_object_or_404(ProduccionReceta, id_detalle=detalle_id)
        produccion_id = detalle.produccion.id_proc
        
        # Validar que se puede editar
        if detalle.produccion.estado not in ['Pendiente', 'Esperando insumos']:
            messages.error(request, 'No se puede editar una producción en este estado')
            return redirect('produccion:recetas', produccion_id=produccion_id)
        
        nombre_receta = detalle.nombre_receta
        detalle.delete()
        
        messages.success(request, f'Receta "{nombre_receta}" eliminada de la producción')
        
    except Exception as e:
        messages.error(request, f'Error al eliminar receta: {str(e)}')
        produccion_id = request.GET.get('produccion_id', 1)
    
    return redirect('produccion:recetas', produccion_id=produccion_id)


def obtener_receta_por_produccion(request, produccion_id):
    """
    Obtiene el ID de la receta asociada a una producción
    Equivalente a: produccion_recetasBean.java - obtenerIdRecetaPorProduccion()
    """
    try:
        # Buscar la primera receta asociada a esta producción
        detalle = ProduccionReceta.objects.filter(
            produccion_id=produccion_id
        ).first()
        
        if detalle:
            return JsonResponse({
                'success': True,
                'receta_id': detalle.receta.id_rec,
                'receta_nombre': detalle.nombre_receta,
                'cantidad': detalle.cantidad
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'No se encontró receta asociada a esta producción'
            })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error obteniendo receta: {str(e)}'
        })


# Funciones auxiliares

def obtener_info_ingredientes(detalle_produccion):
    """
    Obtiene información detallada de los ingredientes necesarios
    Equivalente a: produccion_recetasBean.java - getNombreReceta() extendido
    """
    ingredientes_info = []
    
    if detalle_produccion.receta:
        ingredientes = RecetaInsumo.objects.filter(
            receta=detalle_produccion.receta
        ).select_related('insumo')
        
        for ingrediente in ingredientes:
            cantidad_unitaria = ingrediente.cantidad
            cantidad_necesaria = cantidad_unitaria * detalle_produccion.cantidad
            stock_disponible = ingrediente.insumo.stock_actual
            suficiente = stock_disponible >= cantidad_necesaria
            faltante = max(0, cantidad_necesaria - stock_disponible)
            
            ingredientes_info.append({
                'insumo': ingrediente.insumo,
                'cantidad_unitaria': cantidad_unitaria,
                'cantidad_necesaria': cantidad_necesaria,
                'stock_disponible': stock_disponible,
                'suficiente': suficiente,
                'faltante': faltante,
                'unidad': ingrediente.insumo.unidad_medida,
                'porcentaje_stock': (stock_disponible / cantidad_necesaria * 100) if cantidad_necesaria > 0 else 0
            })
    
    return ingredientes_info


def calcular_costo_total_produccion(produccion):
    """
    Calcula el costo total estimado de una producción
    """
    costo_total = Decimal('0.00')
    
    detalles = ProduccionReceta.objects.filter(produccion=produccion)
    
    for detalle in detalles:
        if detalle.receta:
            # Calcular costo basado en ingredientes
            ingredientes = RecetaInsumo.objects.filter(receta=detalle.receta)
            
            for ingrediente in ingredientes:
                cantidad_necesaria = ingrediente.cantidad * detalle.cantidad
                costo_insumo = getattr(ingrediente.insumo, 'precio_promedio', Decimal('0.00'))
                costo_total += cantidad_necesaria * costo_insumo
    
    return costo_total


def validar_disponibilidad_total(produccion):
    """
    Valida la disponibilidad de ingredientes para toda la producción
    """
    detalles = ProduccionReceta.objects.filter(produccion=produccion)
    
    # Consolidar ingredientes necesarios
    ingredientes_consolidados = {}
    
    for detalle in detalles:
        ingredientes = RecetaInsumo.objects.filter(receta=detalle.receta)
        
        for ingrediente in ingredientes:
            insumo_id = ingrediente.insumo.id_ins
            cantidad_necesaria = ingrediente.cantidad * detalle.cantidad
            
            if insumo_id in ingredientes_consolidados:
                ingredientes_consolidados[insumo_id]['cantidad_total'] += cantidad_necesaria
            else:
                ingredientes_consolidados[insumo_id] = {
                    'insumo': ingrediente.insumo,
                    'cantidad_total': cantidad_necesaria,
                    'stock_disponible': ingrediente.insumo.stock_actual
                }
    
    # Verificar disponibilidad
    ingredientes_insuficientes = []
    
    for insumo_id, info in ingredientes_consolidados.items():
        if info['stock_disponible'] < info['cantidad_total']:
            ingredientes_insuficientes.append({
                'insumo': info['insumo'],
                'necesario': info['cantidad_total'],
                'disponible': info['stock_disponible'],
                'faltante': info['cantidad_total'] - info['stock_disponible']
            })
    
    return len(ingredientes_insuficientes) == 0, ingredientes_insuficientes


# APIs para AJAX

def api_info_receta(request, receta_id):
    """
    API para obtener información de una receta
    """
    try:
        receta = get_object_or_404(Receta, id_rec=receta_id)
        
        # Obtener ingredientes
        ingredientes = RecetaInsumo.objects.filter(
            receta=receta
        ).select_related('insumo')
        
        ingredientes_data = []
        for ing in ingredientes:
            ingredientes_data.append({
                'nombre': ing.insumo.nombre,
                'cantidad': float(ing.cantidad),
                'unidad': ing.insumo.unidad_medida,
                'stock_actual': float(ing.insumo.stock_actual)
            })
        
        return JsonResponse({
            'success': True,
            'receta': {
                'id': receta.id_rec,
                'nombre': receta.nombre,
                'precio': float(receta.precio),
                'tiempo_preparacion': getattr(receta, 'tiempo_preparacion', 0),
                'ingredientes': ingredientes_data
            }
        })
    
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error obteniendo información de receta: {str(e)}'
        })


def api_validar_stock_detalle(request):
    """
    API para validar stock de un detalle específico
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            receta_id = data.get('receta_id')
            cantidad = int(data.get('cantidad', 1))
            
            receta = get_object_or_404(Receta, id_rec=receta_id)
            
            # Crear detalle temporal para validar
            detalle_temp = ProduccionReceta(receta=receta, cantidad=cantidad)
            ingredientes_info = obtener_info_ingredientes(detalle_temp)
            
            tiene_stock = all(ing['suficiente'] for ing in ingredientes_info)
            ingredientes_faltantes = [ing for ing in ingredientes_info if not ing['suficiente']]
            
            return JsonResponse({
                'success': True,
                'tiene_stock': tiene_stock,
                'ingredientes_info': [
                    {
                        'nombre': ing['insumo'].nombre,
                        'necesario': float(ing['cantidad_necesaria']),
                        'disponible': float(ing['stock_disponible']),
                        'suficiente': ing['suficiente'],
                        'faltante': float(ing['faltante']),
                        'unidad': ing['unidad']
                    }
                    for ing in ingredientes_info
                ],
                'ingredientes_faltantes_count': len(ingredientes_faltantes)
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error validando stock: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})