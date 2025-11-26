"""
Utilidades para el módulo de ventas
"""
from django.db import transaction
from decimal import Decimal

from .models import Venta, VentaReceta, VentaProduccion
from modelos.produccion.models import Produccion, ProduccionReceta


@transaction.atomic
def generar_produccion_desde_venta(venta):
    """
    Genera una orden de producción automáticamente cuando una venta está completamente pagada
    Usa consultas SQL directas para adaptarse a la estructura existente
    
    Args:
        venta: Instancia de Venta que está completamente pagada
    
    Returns:
        dict: Información de la producción creada o None si ya existe
    """
    from django.db import connection
    from datetime import datetime
    
    print(f"[DEBUG] >>>>> ENTRANDO A generar_produccion_desde_venta para venta ID: {venta.id_ven}")
    print(f"🧩 Iniciando generación de producción para venta ID: {venta.id_ven}")

    from .models import VentaReceta  # asegurar disponibilidad del modelo

    try:
        with connection.cursor() as cursor:
            # Verificar si ya existe producción asociada
            cursor.execute("SELECT COUNT(*) FROM venta_produccion WHERE id_venta = %s", [venta.id_ven])
            if cursor.fetchone()[0] > 0:
                print("⚠️ Ya existe una producción para esta venta. No se generará otra.")
                return None

            estado = 'Pendiente'
            fecha_creacion = datetime.now()
            id_usu = getattr(getattr(venta, 'usuario', None), 'id_usu', 1)
            id_asignado = getattr(getattr(venta, 'usuario_asignado', None), 'id_usu', None)

            # Crear producción
            cursor.execute("""
                INSERT INTO produccion (estado, fecha_hora, id_usu, id_asignado)
                VALUES (%s, %s, %s, %s)
            """, [estado, fecha_creacion, id_usu, id_asignado])

            # Obtener ID de producción (MySQL/SQLite compatible)
            try:
                produccion_id = cursor.lastrowid
            except Exception:
                cursor.execute("SELECT LAST_INSERT_ID()")
                produccion_id = cursor.fetchone()[0]

            print(f"✅ Producción creada con ID: {produccion_id}")

            recetas_venta = VentaReceta.objects.filter(venta=venta)
            print(f"🍳 Recetas encontradas en la venta: {recetas_venta.count()}")

            for vr in recetas_venta:
                cantidad = getattr(vr, 'cantidad', 1)
                # Insert relación venta_produccion
                try:
                    cursor.execute(
                        """
                        INSERT INTO venta_produccion (id_venta, id_produccion, cantidad)
                        VALUES (%s, %s, %s)
                        """,
                        [venta.id_ven, produccion_id, cantidad]
                    )
                    print(f"🔗 venta_produccion insertada venta={venta.id_ven} produccion={produccion_id} cantidad={cantidad}")
                except Exception as e:
                    print(f"❌ Error insertando en venta_produccion (puede existir ya): {e}")

                # Insert en produccion_recetas (si existe la tabla)
                try:
                    cursor.execute(
                        """
                        INSERT INTO produccion_recetas (id_produccion, id_rec, cantidad)
                        VALUES (%s, %s, %s)
                        """,
                        [produccion_id, vr.receta.id_rec, cantidad]
                    )
                    print(f"✅ produccion_recetas: produccion={produccion_id} receta={vr.receta.id_rec} cantidad={cantidad}")
                except Exception as e:
                    print(f"⚠️ No se pudo insertar en produccion_recetas (verificar existencia de tabla): {e}")

            print(f"🎯 Generación de producción completada para venta ID: {venta.id_ven}")
            return {
                'id_produccion': produccion_id,
                'estado': estado,
                'fecha_creacion': fecha_creacion
            }
    except Exception as e:
        print(f"❌ Error al generar producción desde venta: {e}")
        return None


def actualizar_estado_venta_por_pagos(venta):
    """
    Actualiza el estado de una venta basado en el total de pagos recibidos
    
    Args:
        venta: Instancia de Venta
    """
    from .models import Pago
    
    total_pagado = Pago.calcular_total_pagado_venta(venta)
    print(f"[DEBUG] total_pagado: {total_pagado}, venta.total: {venta.total}, estado actual: {venta.estado}")

    if total_pagado <= 0:
        nuevo_estado = 'Pago pendiente'
    elif total_pagado < venta.total:
        nuevo_estado = 'Procesando'
    else:  # total_pagado >= venta.total
        nuevo_estado = 'Pago completo'

    print(f"[DEBUG] nuevo_estado calculado: {nuevo_estado}")

    # Forzar update SQL directo por managed=False
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("UPDATE ventas SET estado = %s WHERE id_ven = %s", [nuevo_estado, venta.id_ven])
        print(f"[DEBUG] UPDATE ventas SET estado = {nuevo_estado} WHERE id_ven = {venta.id_ven}")
    venta.estado = nuevo_estado
    print(f"[DEBUG] Estado en objeto venta después del update: {venta.estado}")

    # Si ahora está en Pago completo y requiere producción, generar automáticamente (idempotente)
    if nuevo_estado == 'Pago completo' and getattr(venta, 'tipo', None) == 'pedido':
        try:
            from .utils import generar_produccion_desde_venta  # self-import safe
            generar_produccion_desde_venta(venta)
        except Exception as e:
            print(f"[ERROR] No se pudo generar producción automática para venta {venta.id_ven}: {e}")

    return nuevo_estado


def sincronizar_ventas_con_producciones_finalizadas():
    """Sincroniza ventas que tienen producciones finalizadas pero quedaron en 'Pago completo'.

    Regla: Si existe al menos una producción asociada (venta_produccion) en estado Finalizada
    y la venta está en 'Pago completo', cambiar a 'Completada'.

    Retorna dict con métricas del proceso.
    """
    from django.db import connection
    actualizadas = []
    total_afectadas = 0
    try:
        with connection.cursor() as cursor:
            # Obtener ventas candidatas
            cursor.execute("""
                SELECT DISTINCT v.id_ven
                FROM ventas v
                JOIN venta_produccion vp ON v.id_ven = vp.id_venta
                JOIN produccion p ON vp.id_produccion = p.id_proc
                WHERE p.estado = 'Finalizada' AND v.estado = 'Pago completo'
            """)
            rows = cursor.fetchall()
            ids = [r[0] for r in rows]
            total_afectadas = len(ids)
            for vid in ids:
                try:
                    cursor.execute("UPDATE ventas SET estado='Completada' WHERE id_ven=%s", [vid])
                    actualizadas.append(vid)
                except Exception as e:
                    print(f"[WARN] No se pudo actualizar venta {vid}: {e}")
    except Exception as e:
        print(f"[ERROR] sincronizando ventas: {e}")
    return {
        'total_candidatas': total_afectadas,
        'actualizadas': actualizadas,
        'total_actualizadas': len(actualizadas)
    }


if __name__ == '__main__':
    # Permite ejecutar este archivo directamente si se configura DJANGO_SETTINGS_MODULE.
    resultado = sincronizar_ventas_con_producciones_finalizadas()
    print("Sincronización completada:", resultado)
