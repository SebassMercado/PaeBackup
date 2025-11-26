#!/usr/bin/env python
"""
Script para corregir inconsistencias en la base de datos PAE
Aplica las correcciones necesarias usando Django ORM
"""

import os
import sys
import django
from decimal import Decimal
from datetime import date, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

from modelos.usuarios.models import Usuario
from modelos.clientes.models import Cliente
from modelos.insumos.models import Insumo, DetalleInsumo, HistorialInsumo
from modelos.recetas.models import Receta, RecetaInsumo
from modelos.produccion.models import Produccion
from modelos.ventas.models import Venta, DetalleVenta, VentaReceta

def corregir_base_datos():
    """Aplica todas las correcciones necesarias a la base de datos"""
    
    print("🔧 Iniciando corrección de base de datos...")
    
    # 1. Corregir NITs temporales
    print("\n📋 Corrigiendo NITs temporales...")
    nits_mapping = {
        'TEMP-1': '900123456-7',
        'TEMP-2': '900234567-8', 
        'TEMP-3': '79123456-5',
        'TEMP-4': '52987654-3',
        'TEMP-5': '18456789-2',
        'TEMP-8': '900345678-9',
        'TEMP-9': '71234567-6',
        'TEMP-10': '900456789-0',
    }
    
    for temp_nit, real_nit in nits_mapping.items():
        try:
            cliente = Cliente.objects.get(nit=temp_nit)
            cliente.nit = real_nit
            cliente.save()
            print(f"   ✅ Cliente {cliente.nombre}: {temp_nit} → {real_nit}")
        except Cliente.DoesNotExist:
            print(f"   ⚠️  Cliente con NIT {temp_nit} no encontrado")
        except Exception as e:
            print(f"   ❌ Error corrigiendo {temp_nit}: {e}")
    
    # 2. Corregir correos inválidos
    print("\n📧 Corrigiendo correos inválidos...")
    try:
        cliente = Cliente.objects.get(correo='chatopneai')
        cliente.correo = 'chatgpt@openai.com'
        cliente.save()
        print("   ✅ Correo corregido: chatopneai → chatgpt@openai.com")
    except Cliente.DoesNotExist:
        print("   ⚠️  Cliente con correo inválido no encontrado")
    except Exception as e:
        print(f"   ❌ Error corrigiendo correo: {e}")
    
    # 3. Corregir fechas de vencimiento inconsistentes
    print("\n📅 Corrigiendo fechas de vencimiento...")
    detalles_inconsistentes = DetalleInsumo.objects.filter(
        fecha_vencimiento__lt=models.F('fecha_ingreso')
    )
    
    for detalle in detalles_inconsistentes:
        detalle.fecha_vencimiento = detalle.fecha_ingreso.date() + timedelta(days=30)
        detalle.save()
        print(f"   ✅ Fecha corregida para detalle {detalle.id}")
    
    # 4. Recalcular stocks actuales
    print("\n📊 Recalculando stocks actuales...")
    for insumo in Insumo.objects.all():
        stock_actual = DetalleInsumo.objects.filter(
            insumo=insumo,
            estado='Activo'
        ).aggregate(
            total=models.Sum('cantidad')
        )['total'] or Decimal('0.00')
        
        insumo.stock_actual = stock_actual
        
        # Actualizar estado basado en stock
        if stock_actual <= insumo.stock_min:
            insumo.estado = 'Stock insuficiente'
        else:
            insumo.estado = 'Activo'
            
        insumo.save()
        print(f"   ✅ {insumo.nombre}: Stock actualizado a {stock_actual}")
    
    # 5. Corregir estados de detalles de insumo
    print("\n🏷️  Corrigiendo estados de detalles...")
    
    # Marcar como agotado si cantidad es 0
    DetalleInsumo.objects.filter(
        cantidad=0,
        estado='Activo'
    ).update(estado='Agotado')
    
    # Marcar como vencido si la fecha ya pasó
    DetalleInsumo.objects.filter(
        fecha_vencimiento__lt=date.today(),
        estado='Activo'
    ).update(estado='Vencido')
    
    print("   ✅ Estados de detalles actualizados")
    
    # 6. Recalcular subtotales en VentaReceta
    print("\n💰 Recalculando subtotales...")
    for venta_receta in VentaReceta.objects.all():
        subtotal_calculado = venta_receta.cantidad * venta_receta.precio_unitario
        if venta_receta.subtotal != subtotal_calculado:
            venta_receta.subtotal = subtotal_calculado
            venta_receta.save()
            print(f"   ✅ Subtotal corregido para venta {venta_receta.id}")
    
    # 7. Recalcular totales de ventas
    print("\n💵 Recalculando totales de ventas...")
    for venta in Venta.objects.all():
        total_calculado = VentaReceta.objects.filter(
            venta=venta
        ).aggregate(
            total=models.Sum('subtotal')
        )['total'] or Decimal('0.00')
        
        if venta.total != total_calculado:
            venta.total = total_calculado
            venta.save()
            print(f"   ✅ Total corregido para venta {venta.id}: {total_calculado}")
    
    # 8. Corregir estados de receta_insumos
    print("\n🍳 Actualizando estados de ingredientes en recetas...")
    for receta_insumo in RecetaInsumo.objects.all():
        if receta_insumo.insumo.estado == 'Stock insuficiente':
            receta_insumo.estado = 'Agotado'
        else:
            receta_insumo.estado = 'Activo'
        receta_insumo.save()
    
    print("   ✅ Estados de ingredientes actualizados")
    
    # 9. Limpiar teléfonos vacíos en usuarios
    print("\n📱 Corrigiendo teléfonos en usuarios...")
    usuarios_sin_telefono = Usuario.objects.filter(telefono=0)
    for usuario in usuarios_sin_telefono:
        usuario.telefono = '3001234567'
        usuario.save()
        print(f"   ✅ Teléfono corregido para usuario {usuario.nombres}")
    
    print("\n🎉 ¡Corrección de base de datos completada!")
    
    # Resumen final
    print("\n📈 RESUMEN:")
    print(f"   • Clientes: {Cliente.objects.count()}")
    print(f"   • Insumos: {Insumo.objects.count()}")
    print(f"   • Recetas: {Receta.objects.count()}")
    print(f"   • Ventas: {Venta.objects.count()}")
    print(f"   • Usuarios: {Usuario.objects.count()}")
    
    print(f"\n   • Insumos con stock suficiente: {Insumo.objects.filter(estado='Activo').count()}")
    print(f"   • Insumos con stock insuficiente: {Insumo.objects.filter(estado='Stock insuficiente').count()}")
    print(f"   • Detalles activos: {DetalleInsumo.objects.filter(estado='Activo').count()}")
    print(f"   • Detalles vencidos: {DetalleInsumo.objects.filter(estado='Vencido').count()}")
    
def verificar_integridad():
    """Verifica la integridad de los datos después de la corrección"""
    print("\n🔍 VERIFICACIÓN DE INTEGRIDAD:")
    
    # Verificar NITs válidos
    nits_temporales = Cliente.objects.filter(nit__startswith='TEMP-').count()
    print(f"   • NITs temporales restantes: {nits_temporales}")
    
    # Verificar stocks negativos
    stocks_negativos = Insumo.objects.filter(stock_actual__lt=0).count()
    print(f"   • Stocks negativos: {stocks_negativos}")
    
    # Verificar fechas inconsistentes
    fechas_inconsistentes = DetalleInsumo.objects.filter(
        fecha_vencimiento__lt=models.F('fecha_ingreso')
    ).count()
    print(f"   • Fechas de vencimiento inconsistentes: {fechas_inconsistentes}")
    
    # Verificar totales de venta
    ventas_con_total_incorrecto = 0
    for venta in Venta.objects.all():
        total_calculado = VentaReceta.objects.filter(
            venta=venta
        ).aggregate(
            total=models.Sum('subtotal')
        )['total'] or Decimal('0.00')
        
        if venta.total != total_calculado:
            ventas_con_total_incorrecto += 1
    
    print(f"   • Ventas con total incorrecto: {ventas_con_total_incorrecto}")
    
    if (nits_temporales == 0 and stocks_negativos == 0 and 
        fechas_inconsistentes == 0 and ventas_con_total_incorrecto == 0):
        print("\n✅ TODOS LOS PROBLEMAS HAN SIDO CORREGIDOS")
    else:
        print("\n⚠️  ALGUNOS PROBLEMAS REQUIEREN ATENCIÓN MANUAL")

if __name__ == "__main__":
    try:
        # Importar models aquí para evitar errores de importación circular
        from django.db import models
        
        corregir_base_datos()
        verificar_integridad()
        
    except Exception as e:
        print(f"❌ Error durante la corrección: {e}")
        sys.exit(1)