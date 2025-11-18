# PAE Backup - Sistema de Gestión PAE

## Descripción / Description

**Español**: Sistema web de gestión PAE desarrollado con JavaEE, JSF y PrimeFaces.

**English**: PAE management web system developed with JavaEE, JSF and PrimeFaces.

## Tecnologías / Technologies

- Java 8
- JavaEE 7
- JSF (JavaServer Faces)
- PrimeFaces 8.0
- MySQL 8.0
- JasperReports
- Apache POI

## Despliegue en Azure / Azure Deployment

Este proyecto incluye configuración completa para desplegar en Microsoft Azure usando tu cuenta "Soy Sena".

This project includes complete configuration to deploy to Microsoft Azure using your "Soy Sena" account.

### Despliegue Rápido / Quick Deployment

**Windows:**
```cmd
deploy-azure.bat
```

**Linux/macOS:**
```bash
./deploy-azure.sh
```

### Documentación Completa / Complete Documentation

Para instrucciones detalladas de despliegue, consulta:

For detailed deployment instructions, see:

📘 [AZURE_DEPLOYMENT.md](AZURE_DEPLOYMENT.md)

## Estructura del Proyecto / Project Structure

```
PaeBackup/
├── Pae/                    # Aplicación principal / Main application
│   ├── src/               # Código fuente / Source code
│   ├── web/               # Recursos web / Web resources
│   └── lib/               # Librerías / Libraries
├── pom.xml                # Configuración Maven / Maven configuration
├── deploy-azure.sh        # Script de despliegue Linux/Mac
├── deploy-azure.bat       # Script de despliegue Windows
└── AZURE_DEPLOYMENT.md    # Guía de despliegue Azure
```

## Desarrollo Local / Local Development

### Requisitos / Requirements

- NetBeans IDE 8.2 o superior
- GlassFish Server 4.x o Payara Server
- MySQL 8.0
- Java JDK 8

### Configuración / Setup

1. Clonar el repositorio / Clone the repository
2. Importar el proyecto en NetBeans / Import project in NetBeans
3. Configurar la base de datos MySQL / Configure MySQL database
4. Ejecutar el proyecto / Run the project

## Licencia / License

Este proyecto es privado y pertenece a su respectivo propietario.

This project is private and belongs to its respective owner.
