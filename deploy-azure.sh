#!/bin/bash

# Script de Despliegue Rápido para Azure
# Azure Quick Deployment Script

echo "=== Despliegue de PAE en Azure / PAE Azure Deployment ==="
echo ""

# Verificar si Azure CLI está instalado
if ! command -v az &> /dev/null
then
    echo "Error: Azure CLI no está instalado. Por favor instálalo primero."
    echo "Error: Azure CLI is not installed. Please install it first."
    echo "Visit: https://docs.microsoft.com/cli/azure/install-azure-cli"
    exit 1
fi

# Verificar si Maven está instalado
if ! command -v mvn &> /dev/null
then
    echo "Error: Maven no está instalado. Por favor instálalo primero."
    echo "Error: Maven is not installed. Please install it first."
    echo "Visit: https://maven.apache.org/download.cgi"
    exit 1
fi

# Solicitar información de Azure
echo "Por favor ingresa la siguiente información:"
echo "Please enter the following information:"
echo ""

read -p "Azure Subscription ID: " SUBSCRIPTION_ID
read -p "Resource Group Name (default: pae-resource-group): " RESOURCE_GROUP
RESOURCE_GROUP=${RESOURCE_GROUP:-pae-resource-group}

read -p "App Name (default: pae-webapp-soysena): " APP_NAME
APP_NAME=${APP_NAME:-pae-webapp-soysena}

read -p "Region (default: East US): " REGION
REGION=${REGION:-East US}

echo ""
echo "=== Configuración / Configuration ==="
echo "Subscription ID: $SUBSCRIPTION_ID"
echo "Resource Group: $RESOURCE_GROUP"
echo "App Name: $APP_NAME"
echo "Region: $REGION"
echo ""

read -p "¿Continuar con estos valores? / Continue with these values? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Despliegue cancelado / Deployment cancelled"
    exit 0
fi

# Establecer variables de entorno
export AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
export AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
export AZURE_APP_NAME=$APP_NAME
export AZURE_REGION=$REGION

echo ""
echo "=== Paso 1: Iniciar sesión en Azure / Step 1: Login to Azure ==="
az login

echo ""
echo "=== Paso 2: Establecer suscripción / Step 2: Set subscription ==="
az account set --subscription $SUBSCRIPTION_ID

echo ""
echo "=== Paso 3: Crear grupo de recursos / Step 3: Create resource group ==="
az group create --name $RESOURCE_GROUP --location "$REGION"

echo ""
echo "=== Paso 4: Construir proyecto / Step 4: Build project ==="
mvn clean package

echo ""
echo "=== Paso 5: Desplegar en Azure / Step 5: Deploy to Azure ==="
mvn azure-webapp:deploy

echo ""
echo "=== ¡Despliegue Completado! / Deployment Completed! ==="
echo ""
echo "Tu aplicación está disponible en / Your application is available at:"
echo "https://$APP_NAME.azurewebsites.net"
echo ""
echo "Para ver los logs / To view logs:"
echo "az webapp log tail --resource-group $RESOURCE_GROUP --name $APP_NAME"
