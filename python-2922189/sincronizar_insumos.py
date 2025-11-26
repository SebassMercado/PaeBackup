import os
import django
from django.db import connection

# Asegura el settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pae_system.settings')
django.setup()

def sincronizar_estados_insumos(dry_run=False):
    """Sincroniza el campo estado de la tabla insumos según reglas:
    - Si estado = 'Inactivo' se respeta (no se cambia)
    - Si stock_actual < stock_min => 'Stock insuficiente'
    - Else => 'Activo'
    Retorna resumen con conteos.
    """
    with connection.cursor() as cursor:
        # Obtener datos actuales
        cursor.execute("SELECT id_ins, stock_actual, stock_min, estado FROM insumos")
        rows = cursor.fetchall()

    cambios = []
    for id_ins, stock_actual, stock_min, estado in rows:
        nuevo = estado
        try:
            sa = float(stock_actual or 0)
            sm = float(stock_min or 0)
        except Exception:
            sa = 0.0
            sm = 0.0
        if estado == 'Inactivo':
            continue  # respetar inactivos
        if sa < sm:
            nuevo = 'Stock insuficiente'
        else:
            nuevo = 'Activo'
        if nuevo != estado:
            cambios.append((nuevo, id_ins))

    if not dry_run and cambios:
        with connection.cursor() as cursor:
            cursor.executemany("UPDATE insumos SET estado=%s WHERE id_ins=%s", cambios)

    return {
        'total_insumos': len(rows),
        'cambios_aplicados': 0 if dry_run else len(cambios),
        'cambios_potenciales': len(cambios),
        'dry_run': dry_run,
    }

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Sincronizar estado de insumos según stock mínimo.')
    parser.add_argument('--dry-run', action='store_true', help='Solo mostrar cambios potenciales sin aplicar.')
    args = parser.parse_args()
    resumen = sincronizar_estados_insumos(dry_run=args.dry_run)
    print(resumen)
