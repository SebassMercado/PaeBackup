@echo off
echo ========================================
echo IMPORTANDO BASE DE DATOS PAE A MYSQL
echo ========================================
echo.

REM Ruta de MySQL en XAMPP (ajustar si es diferente)
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe

REM Verificar si MySQL existe
if not exist "%MYSQL_PATH%" (
    echo ERROR: No se encontro MySQL en %MYSQL_PATH%
    echo Por favor, ajusta la ruta de MySQL en este script.
    pause
    exit /b 1
)

echo Creando base de datos 'pae'...
"%MYSQL_PATH%" -u root -e "CREATE DATABASE IF NOT EXISTS pae CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

echo Importando datos desde pae.sql...
"%MYSQL_PATH%" -u root pae < pae.sql

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo IMPORTACION COMPLETADA EXITOSAMENTE
    echo ========================================
    echo.
    echo Base de datos: pae
    echo Usuario: root
    echo Password: [vacio]
    echo Host: 127.0.0.1
    echo Puerto: 3306
) else (
    echo.
    echo ERROR EN LA IMPORTACION
    echo Verifica que XAMPP este corriendo y MySQL este activo
)

echo.
pause
