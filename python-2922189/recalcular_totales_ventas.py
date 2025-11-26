#!/usr/bin/env python
"""
Script para recalcular totales de ventas
Este script revisa todas las ventas y recalcula sus totales basado en los registros de VentaReceta
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.ventas.models import Venta, VentaReceta

def recalcular_totales_ventas():
    """Recalcula los totales de todas las ventas basado en sus VentaReceta"""
    
    print("=== RECALCULANDO TOTALES DE VENTAS ===\n")
    
    # Obtener todas las ventas
    ventas = Venta.objects.all().order_by('-id_ven')
    
    ventas_actualizadas = 0
    ventas_sin_cambios = 0
    
    for venta in ventas:
        try:
            # Calcular el total actual basado en VentaReceta
            recetas_venta = VentaReceta.objects.filter(venta=venta)
            total_calculado = Decimal('0.00')
            
            print(f"Venta #{venta.id_ven} - Cliente: {venta.cliente.nombre if venta.cliente else 'Sin cliente'}")
            print(f"  Total actual en BD: ${venta.total}")
            
            if recetas_venta.exists():
                print(f"  Recetas asociadas: {recetas_venta.count()}")
                for vr in recetas_venta:
                    subtotal_calculado = vr.cantidad * vr.precio
                    total_calculado += subtotal_calculado
                    print(f"    - {vr.nombre_receta}: {vr.cantidad} x ${vr.precio} = ${subtotal_calculado}")
                    
                    # Actualizar subtotal si es diferente
                    if vr.subtotal != subtotal_calculado:
                        print(f"      * Actualizando subtotal de ${vr.subtotal} a ${subtotal_calculado}")
                        vr.subtotal = subtotal_calculado
                        vr.save()
            else:
                print("  Sin recetas asociadas")
            
            print(f"  Total calculado: ${total_calculado}")
            
            # Actualizar total de la venta si es diferente
            if venta.total != total_calculado:
                print(f"  *** ACTUALIZANDO TOTAL: ${venta.total} -> ${total_calculado}")
                venta.total = total_calculado
                venta.save()
                ventas_actualizadas += 1
            else:
                print("  Total correcto, no requiere actualización")
                ventas_sin_cambios += 1
                
            print("-" * 50)
            
        except Exception as e:
            print(f"ERROR procesando venta #{venta.id_ven}: {e}")
            print("-" * 50)
            continue
    
    print(f"\n=== RESUMEN ===")
    print(f"Ventas actualizadas: {ventas_actualizadas}")
    print(f"Ventas sin cambios: {ventas_sin_cambios}")
    print(f"Total ventas procesadas: {ventas_actualizadas + ventas_sin_cambios}")

if __name__ == "__main__":
    recalcular_totales_ventas()