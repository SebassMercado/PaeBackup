@echo off
echo ========================================
echo RECREANDO BASE DE DATOS PAE EN MYSQL
echo ========================================
echo.

REM Ruta de MySQL
set MYSQL_PATH=C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe

echo ADVERTENCIA: Esto eliminara la base de datos 'pae' existente
echo y creara una nueva con los datos de pae.sql
echo.
pause

echo.
echo Eliminando base de datos 'pae' existente...
"%MYSQL_PATH%" -u root -e "DROP DATABASE IF EXISTS pae;"

echo Creando nueva base de datos 'pae'...
"%MYSQL_PATH%" -u root -e "CREATE DATABASE pae CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"

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
    echo.
    echo Ahora puedes ejecutar:
    echo   python manage.py migrate
    echo   python resetear_password.py
) else (
    echo.
    echo ERROR EN LA IMPORTACION
    echo Verifica que MySQL este corriendo
)

echo.
pause
