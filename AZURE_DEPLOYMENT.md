# Guía de Despliegue en Azure / Azure Deployment Guide

## Español

### Requisitos Previos

1. **Cuenta de Azure**: Necesitas una cuenta de Azure activa (como tu cuenta "Soy Sena")
2. **Azure CLI**: Instalar Azure CLI desde https://docs.microsoft.com/cli/azure/install-azure-cli
3. **Maven**: Instalar Apache Maven 3.6 o superior desde https://maven.apache.org/download.cgi
4. **Java JDK 8**: Instalar Java Development Kit 8

### Pasos para Desplegar en Azure

#### 1. Instalar Azure CLI

```bash
# Para Windows (con PowerShell como administrador)
winget install Microsoft.AzureCLI

# Para macOS
brew update && brew install azure-cli

# Para Linux (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 2. Iniciar Sesión en Azure

```bash
# Iniciar sesión con tu cuenta Soy Sena
az login
```

Esto abrirá una ventana del navegador para que inicies sesión con tus credenciales.

#### 3. Configurar Variables de Entorno

Crea un archivo `.env` en la raíz del proyecto o configura las siguientes variables de entorno:

```bash
# Windows (PowerShell)
$env:AZURE_SUBSCRIPTION_ID="tu-subscription-id"
$env:AZURE_RESOURCE_GROUP="pae-resource-group"
$env:AZURE_APP_NAME="pae-webapp-soysena"
$env:AZURE_REGION="East US"

# Linux/macOS (Bash)
export AZURE_SUBSCRIPTION_ID="tu-subscription-id"
export AZURE_RESOURCE_GROUP="pae-resource-group"
export AZURE_APP_NAME="pae-webapp-soysena"
export AZURE_REGION="East US"
```

**Nota**: Para obtener tu Subscription ID:
```bash
az account list --output table
```

#### 4. Crear Grupo de Recursos (si no existe)

```bash
az group create --name pae-resource-group --location "East US"
```

#### 5. Configurar Base de Datos MySQL en Azure

Azure ofrece Azure Database for MySQL. Para crear una:

```bash
# Crear servidor MySQL
az mysql server create \
  --resource-group pae-resource-group \
  --name pae-mysql-server \
  --location "East US" \
  --admin-user adminpae \
  --admin-password "TuContraseñaSegura123!" \
  --sku-name B_Gen5_1 \
  --version 8.0

# Crear base de datos
az mysql db create \
  --resource-group pae-resource-group \
  --server-name pae-mysql-server \
  --name paedb

# Permitir acceso desde Azure Services
az mysql server firewall-rule create \
  --resource-group pae-resource-group \
  --server-name pae-mysql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 6. Configurar Cadena de Conexión

La cadena de conexión MySQL para Azure será:
```
jdbc:mysql://pae-mysql-server.mysql.database.azure.com:3306/paedb?useSSL=true&requireSSL=false
Usuario: adminpae@pae-mysql-server
Contraseña: TuContraseñaSegura123!
```

**Importante**: Actualiza tu aplicación para usar estas credenciales en producción.

#### 7. Construir el Proyecto con Maven

```bash
# En la raíz del proyecto
mvn clean package
```

Esto creará el archivo `Pae.war` en el directorio `target/`.

#### 8. Desplegar en Azure App Service

Hay dos métodos para desplegar:

**Método 1: Usando Maven Plugin (Recomendado)**

```bash
# Configurar y desplegar
mvn azure-webapp:deploy
```

**Método 2: Usando Azure CLI**

```bash
# Crear Web App
az webapp create \
  --resource-group pae-resource-group \
  --plan pae-app-service-plan \
  --name pae-webapp-soysena \
  --runtime "TOMCAT:9.0-java8"

# Crear App Service Plan (si no existe)
az appservice plan create \
  --name pae-app-service-plan \
  --resource-group pae-resource-group \
  --sku F1 \
  --is-linux

# Desplegar WAR
az webapp deploy \
  --resource-group pae-resource-group \
  --name pae-webapp-soysena \
  --src-path target/Pae.war \
  --type war
```

#### 9. Configurar Variables de Entorno de la Aplicación

```bash
# Configurar la cadena de conexión de la base de datos
az webapp config appsettings set \
  --resource-group pae-resource-group \
  --name pae-webapp-soysena \
  --settings \
    MYSQL_HOST="pae-mysql-server.mysql.database.azure.com" \
    MYSQL_DATABASE="paedb" \
    MYSQL_USER="adminpae@pae-mysql-server" \
    MYSQL_PASSWORD="TuContraseñaSegura123!"
```

#### 10. Verificar el Despliegue

Tu aplicación estará disponible en:
```
https://pae-webapp-soysena.azurewebsites.net
```

Para ver los logs:
```bash
az webapp log tail --resource-group pae-resource-group --name pae-webapp-soysena
```

### Solución de Problemas

1. **Error de memoria**: Aumenta el plan de servicio de aplicaciones
2. **Error de conexión a base de datos**: Verifica las reglas del firewall
3. **Timeout durante el despliegue**: Aumenta el timeout en la configuración de Maven

### Costos

- **Free Tier (F1)**: Gratis, limitado a 60 minutos de CPU por día
- **Basic Tier (B1)**: ~$13/mes, recomendado para producción
- **MySQL Basic**: ~$25/mes para servidor pequeño

---

## English

### Prerequisites

1. **Azure Account**: You need an active Azure account (such as your "Soy Sena" account)
2. **Azure CLI**: Install Azure CLI from https://docs.microsoft.com/cli/azure/install-azure-cli
3. **Maven**: Install Apache Maven 3.6 or higher from https://maven.apache.org/download.cgi
4. **Java JDK 8**: Install Java Development Kit 8

### Steps to Deploy to Azure

#### 1. Install Azure CLI

```bash
# For Windows (with PowerShell as administrator)
winget install Microsoft.AzureCLI

# For macOS
brew update && brew install azure-cli

# For Linux (Ubuntu/Debian)
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

#### 2. Login to Azure

```bash
# Login with your Soy Sena account
az login
```

This will open a browser window for you to sign in with your credentials.

#### 3. Configure Environment Variables

Create a `.env` file in the project root or set the following environment variables:

```bash
# Windows (PowerShell)
$env:AZURE_SUBSCRIPTION_ID="your-subscription-id"
$env:AZURE_RESOURCE_GROUP="pae-resource-group"
$env:AZURE_APP_NAME="pae-webapp-soysena"
$env:AZURE_REGION="East US"

# Linux/macOS (Bash)
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="pae-resource-group"
export AZURE_APP_NAME="pae-webapp-soysena"
export AZURE_REGION="East US"
```

**Note**: To get your Subscription ID:
```bash
az account list --output table
```

#### 4. Create Resource Group (if it doesn't exist)

```bash
az group create --name pae-resource-group --location "East US"
```

#### 5. Configure MySQL Database in Azure

Azure offers Azure Database for MySQL. To create one:

```bash
# Create MySQL server
az mysql server create \
  --resource-group pae-resource-group \
  --name pae-mysql-server \
  --location "East US" \
  --admin-user adminpae \
  --admin-password "YourSecurePassword123!" \
  --sku-name B_Gen5_1 \
  --version 8.0

# Create database
az mysql db create \
  --resource-group pae-resource-group \
  --server-name pae-mysql-server \
  --name paedb

# Allow access from Azure Services
az mysql server firewall-rule create \
  --resource-group pae-resource-group \
  --server-name pae-mysql-server \
  --name AllowAzureServices \
  --start-ip-address 0.0.0.0 \
  --end-ip-address 0.0.0.0
```

#### 6. Configure Connection String

The MySQL connection string for Azure will be:
```
jdbc:mysql://pae-mysql-server.mysql.database.azure.com:3306/paedb?useSSL=true&requireSSL=false
User: adminpae@pae-mysql-server
Password: YourSecurePassword123!
```

**Important**: Update your application to use these credentials in production.

#### 7. Build the Project with Maven

```bash
# At the project root
mvn clean package
```

This will create the `Pae.war` file in the `target/` directory.

#### 8. Deploy to Azure App Service

There are two methods to deploy:

**Method 1: Using Maven Plugin (Recommended)**

```bash
# Configure and deploy
mvn azure-webapp:deploy
```

**Method 2: Using Azure CLI**

```bash
# Create Web App
az webapp create \
  --resource-group pae-resource-group \
  --plan pae-app-service-plan \
  --name pae-webapp-soysena \
  --runtime "TOMCAT:9.0-java8"

# Create App Service Plan (if it doesn't exist)
az appservice plan create \
  --name pae-app-service-plan \
  --resource-group pae-resource-group \
  --sku F1 \
  --is-linux

# Deploy WAR
az webapp deploy \
  --resource-group pae-resource-group \
  --name pae-webapp-soysena \
  --src-path target/Pae.war \
  --type war
```

#### 9. Configure Application Environment Variables

```bash
# Configure database connection string
az webapp config appsettings set \
  --resource-group pae-resource-group \
  --name pae-webapp-soysena \
  --settings \
    MYSQL_HOST="pae-mysql-server.mysql.database.azure.com" \
    MYSQL_DATABASE="paedb" \
    MYSQL_USER="adminpae@pae-mysql-server" \
    MYSQL_PASSWORD="YourSecurePassword123!"
```

#### 10. Verify Deployment

Your application will be available at:
```
https://pae-webapp-soysena.azurewebsites.net
```

To view logs:
```bash
az webapp log tail --resource-group pae-resource-group --name pae-webapp-soysena
```

### Troubleshooting

1. **Memory error**: Increase the app service plan tier
2. **Database connection error**: Verify firewall rules
3. **Deployment timeout**: Increase timeout in Maven configuration

### Costs

- **Free Tier (F1)**: Free, limited to 60 minutes CPU per day
- **Basic Tier (B1)**: ~$13/month, recommended for production
- **MySQL Basic**: ~$25/month for small server

---

## Additional Resources

- [Azure App Service Documentation](https://docs.microsoft.com/azure/app-service/)
- [Azure Database for MySQL](https://docs.microsoft.com/azure/mysql/)
- [Maven Plugin for Azure Web Apps](https://github.com/microsoft/azure-maven-plugins)
