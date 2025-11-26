#!/usr/bin/env python
"""
Script de prueba para simular la creación de una venta
"""

import os
import sys
import django
from decimal import Decimal
import json

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.ventas.models import Venta, VentaReceta
from modelos.clientes.models import Cliente
from modelos.usuarios.models import Usuario
from modelos.recetas.models import Receta
from django.utils import timezone

def crear_venta_prueba():
    """Crear una venta de prueba para verificar que todo funcione"""
    
    print("=== CREANDO VENTA DE PRUEBA ===")
    
    # Obtener datos necesarios
    cliente = Cliente.objects.first()
    usuario = Usuario.objects.first()
    receta = Receta.objects.first()
    
    if not cliente:
        print("ERROR: No hay clientes en la base de datos")
        return
    
    if not usuario:
        print("ERROR: No hay usuarios en la base de datos")
        return
        
    if not receta:
        print("ERROR: No hay recetas en la base de datos")
        return
    
    print(f"Cliente: {cliente.nombre}")
    print(f"Usuario: {usuario.nombre}")
    print(f"Receta: {receta.nombre} - Precio: ${receta.precio}")
    
    # Simular datos del carrito como llegarían desde JavaScript
    detalles_carrito = [
        {
            "receta_id": str(receta.id_rec),
            "cantidad": 3,
            "precio_unitario": float(receta.precio),
            "nombre": receta.nombre
        }
    ]
    
    print(f"Carrito simulado: {detalles_carrito}")
    
    try:
        # Crear la venta
        venta = Venta.objects.create(
            cliente=cliente,
            usuario=usuario,
            usuario_asignado=usuario,
            estado='Pago pendiente',
            fecha=timezone.now(),
            observaciones='Venta de prueba creada por script',
            total=Decimal('0.00')
        )
        
        print(f"Venta creada con ID: {venta.id_ven}")
        
        # Procesar detalles del carrito
        total_venta = Decimal('0.00')
        
        for detalle_data in detalles_carrito:
            receta_id = detalle_data.get('receta_id')
            cantidad = int(detalle_data.get('cantidad', 0))
            precio_unitario = Decimal(str(detalle_data.get('precio_unitario', '0.00')))
            
            if receta_id and cantidad > 0:
                receta_obj = Receta.objects.get(id_rec=receta_id)
                
                # Calcular subtotal
                subtotal = cantidad * precio_unitario
                
                print(f"Creando VentaReceta: {receta_obj.nombre} x {cantidad} = ${subtotal}")
                
                # Crear entrada en VentaReceta
                venta_receta = VentaReceta.objects.create(
                    venta=venta,
                    receta=receta_obj,
                    cantidad=cantidad,
                    precio=precio_unitario,
                    subtotal=subtotal,
                    nombre_receta=receta_obj.nombre
                )
                
                print(f"VentaReceta creada con ID: {venta_receta.id_venta_receta}")
                
                # Sumar al total de la venta
                total_venta += subtotal
        
        # Actualizar total de la venta
        venta.total = total_venta
        venta.save()
        
        print(f"Total de la venta actualizado: ${total_venta}")
        print("✓ Venta de prueba creada exitosamente")
        
        return venta.id_ven
        
    except Exception as e:
        print(f"ERROR creando venta de prueba: {e}")
        return None

def verificar_venta(venta_id):
    """Verificar que la venta se creó correctamente"""
    
    print(f"\n=== VERIFICANDO VENTA #{venta_id} ===")
    
    try:
        venta = Venta.objects.get(id_ven=venta_id)
        print(f"Venta encontrada: #{venta.id_ven}")
        print(f"Cliente: {venta.cliente.nombre}")
        print(f"Total: ${venta.total}")
        
        # Verificar VentaReceta
        recetas_venta = VentaReceta.objects.filter(venta=venta)
        print(f"Recetas asociadas: {recetas_venta.count()}")
        
        for vr in recetas_venta:
            print(f"  - {vr.nombre_receta}: {vr.cantidad} x ${vr.precio} = ${vr.subtotal}")
        
        print("✓ Verificación completada")
        
    except Exception as e:
        print(f"ERROR verificando venta: {e}")

if __name__ == "__main__":
    venta_id = crear_venta_prueba()
    if venta_id:
        verificar_venta(venta_id)