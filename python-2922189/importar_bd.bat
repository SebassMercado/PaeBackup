@echo off
REM Script para importar la base de datos completa
REM Uso: importar_bd.bat

echo ================================================================================
echo IMPORTACION RAPIDA DE BASE DE DATOS PAE
echo ================================================================================
echo.

REM Verificar que existe pae.sql
if not exist "pae.sql" (
    echo [ERROR] No se encontro el archivo pae.sql
    echo.
    echo Coloca el archivo pae.sql en esta carpeta y vuelve a intentar.
    pause
    exit /b 1
)

echo [1/3] Recreando base de datos...
mysql -u root -h 127.0.0.1 -P 3306 -e "DROP DATABASE IF EXISTS pae; CREATE DATABASE pae CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

if errorlevel 1 (
    echo [ERROR] No se pudo recrear la base de datos
    pause
    exit /b 1
)

echo [OK] Base de datos recreada
echo.

echo [2/3] Importando estructura y datos desde pae.sql...
mysql -u root -h 127.0.0.1 -P 3306 pae < pae.sql 2>&1

if errorlevel 1 (
    echo [ERROR] No se pudo importar el archivo SQL
    pause
    exit /b 1
)

echo [OK] Datos importados
echo.

echo [3/3] Sincronizando migraciones de Django...
python manage.py migrate --fake 2>&1 | findstr /V "Applying"

if errorlevel 1 (
    echo [ERROR] No se pudieron sincronizar las migraciones
    pause
    exit /b 1
)

echo [OK] Migraciones sincronizadas
echo.

REM Crear tabla de sesiones
mysql -u root -h 127.0.0.1 -P 3306 pae -e "CREATE TABLE IF NOT EXISTS django_session (session_key varchar(40) NOT NULL PRIMARY KEY, session_data longtext NOT NULL, expire_date datetime(6) NOT NULL, KEY django_session_expire_date_a5c62663 (expire_date));" 2>nul

echo ================================================================================
echo IMPORTACION COMPLETADA EXITOSAMENTE
echo ================================================================================
echo.
echo Tu base de datos esta lista para usar.
echo.
echo Para iniciar el servidor:
echo   python manage.py runserver
echo.
pause
