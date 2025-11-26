from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from modelos.recetas.models import Receta, RecetaInsumo

def ingredientes_receta_ajax(request, receta_id):
    """
    Devuelve los ingredientes (insumos) de una receta en formato JSON para el modal de detalle de venta.
    """
    receta = get_object_or_404(Receta, id_rec=receta_id)
    ingredientes = RecetaInsumo.objects.filter(receta=receta).select_related('insumo')
    data = []
    for ing in ingredientes:
        data.append({
            'nombre': ing.insumo.nombre,
            'cantidad': float(ing.cantidad),
            'unidad': ing.get_unidad_display(),
            'estado': ing.estado,
        })
    return JsonResponse({'ingredientes': data, 'receta': receta.nombre})
