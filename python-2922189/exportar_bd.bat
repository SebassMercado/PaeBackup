@echo off
REM Script rapido para exportar un respaldo completo de la base de datos
REM Uso: exportar_bd.bat

echo ================================================================================
echo EXPORTACION RAPIDA DE BASE DE DATOS PAE
echo ================================================================================
echo.

REM Generar nombre con fecha y hora
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a%%b)
set datetime=%mydate%_%mytime%
set filename=backup_pae_%datetime%.sql

echo Exportando base de datos a: %filename%
echo.

mysqldump -u root -h 127.0.0.1 -P 3306 pae > %filename%

if errorlevel 1 (
    echo [ERROR] No se pudo exportar la base de datos
    pause
    exit /b 1
)

echo.
echo ================================================================================
echo EXPORTACION COMPLETADA
echo ================================================================================
echo.
echo Archivo generado: %filename%

REM Mostrar tamaño del archivo
for %%A in (%filename%) do echo Tamaño: %%~zA bytes

echo.
pause
