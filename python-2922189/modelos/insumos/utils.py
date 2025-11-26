from django.db import connection

def sincronizar_estado_insumo(id_ins):
    """Ajusta el estado del insumo dado según stock_actual vs stock_min.
    Regla: si estado actual es 'Inactivo' se respeta. Si stock_actual < stock_min => 'Stock insuficiente', else 'Activo'."""
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE insumos
            SET estado = CASE
                WHEN estado <> 'Inactivo' AND stock_actual < stock_min THEN 'Stock insuficiente'
                WHEN estado <> 'Inactivo' THEN 'Activo'
                ELSE estado
            END
            WHERE id_ins = %s
        """, [id_ins])


def sincronizar_estado_insumos_multiples(ids):
    """Versión batch para varios insumos."""
    if not ids:
        return 0
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE insumos
            SET estado = CASE
                WHEN estado <> 'Inactivo' AND stock_actual < stock_min THEN 'Stock insuficiente'
                WHEN estado <> 'Inactivo' THEN 'Activo'
                ELSE estado
            END
            WHERE id_ins IN (%s)
        """ % ",".join(str(i) for i in ids))
    return len(ids)
