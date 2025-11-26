#!/usr/bin/env python3
"""
Script para limpiar debugging del archivo views.py
"""

import re

def limpiar_debugging():
    archivo = "c:/Users/sebas/OneDrive/Documentos/python-2922189/modelos/ventas/views.py"
    
    with open(archivo, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Quitar todas las líneas de print con DEBUG, PASO, SUCCESS, ERROR, etc.
    patrones = [
        r'^\s*print\(.*DEBUG.*\)\s*\n',
        r'^\s*print\(.*PASO.*\)\s*\n', 
        r'^\s*print\(.*SUCCESS.*\)\s*\n',
        r'^\s*print\(.*ERROR.*\)\s*\n',
        r'^\s*print\(f.*DEBUG.*\)\s*\n',
        r'^\s*print\(f.*PASO.*\)\s*\n',
        r'^\s*print\(f.*SUCCESS.*\)\s*\n',
        r'^\s*print\(f.*ERROR.*\)\s*\n',
        r'^\s*print\("=".*\)\s*\n',
        r'^\s*print\(.*INICIANDO.*\)\s*\n'
    ]
    
    for patron in patrones:
        contenido = re.sub(patron, '', contenido, flags=re.MULTILINE)
    
    # Limpiar líneas vacías múltiples
    contenido = re.sub(r'\n\s*\n\s*\n', '\n\n', contenido)
    
    with open(archivo, 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("Debugging limpiado del archivo views.py")

if __name__ == "__main__":
    limpiar_debugging()