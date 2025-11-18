@echo off
REM Script de Despliegue Rápido para Azure
REM Azure Quick Deployment Script

echo === Despliegue de PAE en Azure / PAE Azure Deployment ===
echo.

REM Verificar si Azure CLI está instalado
where az >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Azure CLI no está instalado. Por favor instálalo primero.
    echo Error: Azure CLI is not installed. Please install it first.
    echo Visit: https://docs.microsoft.com/cli/azure/install-azure-cli
    exit /b 1
)

REM Verificar si Maven está instalado
where mvn >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Error: Maven no está instalado. Por favor instálalo primero.
    echo Error: Maven is not installed. Please install it first.
    echo Visit: https://maven.apache.org/download.cgi
    exit /b 1
)

REM Solicitar información de Azure
echo Por favor ingresa la siguiente información:
echo Please enter the following information:
echo.

set /p SUBSCRIPTION_ID="Azure Subscription ID: "
set /p RESOURCE_GROUP="Resource Group Name (default: pae-resource-group): "
if "%RESOURCE_GROUP%"=="" set RESOURCE_GROUP=pae-resource-group

set /p APP_NAME="App Name (default: pae-webapp-soysena): "
if "%APP_NAME%"=="" set APP_NAME=pae-webapp-soysena

set /p REGION="Region (default: East US): "
if "%REGION%"=="" set REGION=East US

echo.
echo === Configuración / Configuration ===
echo Subscription ID: %SUBSCRIPTION_ID%
echo Resource Group: %RESOURCE_GROUP%
echo App Name: %APP_NAME%
echo Region: %REGION%
echo.

set /p CONFIRM="¿Continuar con estos valores? / Continue with these values? (y/n): "
if /i not "%CONFIRM%"=="y" (
    echo Despliegue cancelado / Deployment cancelled
    exit /b 0
)

REM Establecer variables de entorno
set AZURE_SUBSCRIPTION_ID=%SUBSCRIPTION_ID%
set AZURE_RESOURCE_GROUP=%RESOURCE_GROUP%
set AZURE_APP_NAME=%APP_NAME%
set AZURE_REGION=%REGION%

echo.
echo === Paso 1: Iniciar sesión en Azure / Step 1: Login to Azure ===
call az login

echo.
echo === Paso 2: Establecer suscripción / Step 2: Set subscription ===
call az account set --subscription %SUBSCRIPTION_ID%

echo.
echo === Paso 3: Crear grupo de recursos / Step 3: Create resource group ===
call az group create --name %RESOURCE_GROUP% --location "%REGION%"

echo.
echo === Paso 4: Construir proyecto / Step 4: Build project ===
call mvn clean package

echo.
echo === Paso 5: Desplegar en Azure / Step 5: Deploy to Azure ===
call mvn azure-webapp:deploy

echo.
echo === ¡Despliegue Completado! / Deployment Completed! ===
echo.
echo Tu aplicación está disponible en / Your application is available at:
echo https://%APP_NAME%.azurewebsites.net
echo.
echo Para ver los logs / To view logs:
echo az webapp log tail --resource-group %RESOURCE_GROUP% --name %APP_NAME%
