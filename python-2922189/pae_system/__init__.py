# Configuración automática de PyMySQL para equipos de desarrollo
import os

# Solo importar PyMySQL si se va a usar MySQL
use_mysql = os.getenv('USE_MYSQL', 'False').lower() == 'true'

if use_mysql:
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        # Si PyMySQL no está instalado, continuar sin errores  cd "C:\Users\esteb\OneDrive\Documents\Phyton Pae\python-2922189"; python manage.py runserver
        pass
