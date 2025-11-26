# 📋 Sistema de Migración de Base de Datos PAE

Este sistema te permite exportar e importar la base de datos completa de forma automática.

## ⚡ Uso Rápido (Recomendado)

### **Importar base de datos:**
```bash
# Doble clic en el archivo o ejecuta:
importar_bd.bat
```

### **Exportar/Respaldar base de datos:**
```bash
# Doble clic en el archivo o ejecuta:
exportar_bd.bat
```

---

## 🚀 Scripts Disponibles

### **Scripts Rápidos (.bat) - Windows**

#### **`importar_bd.bat`** ⚡ Más Fácil
Importa la base de datos completa automáticamente.

```bash
# Solo ejecuta (o doble clic):
importar_bd.bat
```

**Hace automáticamente:**
1. ✅ Elimina la BD existente
2. ✅ Crea una BD nueva
3. ✅ Importa `pae.sql`
4. ✅ Sincroniza migraciones Django
5. ✅ Crea tabla de sesiones

---

#### **`exportar_bd.bat`** ⚡ Más Fácil
Exporta/Respalda toda la base de datos.

```bash
# Solo ejecuta (o doble clic):
exportar_bd.bat
```

**Genera:** `backup_pae_YYYYMMDD_HHMM.sql`

---

### **Scripts Python (Avanzados)**

### 1. **Exportar Estructura** (`exportar_estructura.py`)
Exporta solo la estructura de las tablas (CREATE TABLE) sin datos.

```bash
python exportar_estructura.py
```

**Genera:** `estructura_pae_YYYYMMDD_HHMMSS.sql`

---

### 2. **Exportar Datos** (`exportar_datos.py`)
Exporta solo los datos (INSERT INTO) sin la estructura.

```bash
python exportar_datos.py
```

**Genera:** `datos_pae_YYYYMMDD_HHMMSS.sql`

---

### 3. **Importar Base Completa** (`importar_base_completa.py`)
Importa la base de datos completa desde un archivo SQL (estructura + datos).

```bash
python importar_base_completa.py
```

**Requiere:** `pae.sql` (o edita la variable `ARCHIVO_SQL` en el script)

---

## 📦 Flujo de Trabajo Completo

### **Exportar tu base de datos actual:**

```bash
# Opción 1: Exportar estructura y datos por separado
python exportar_estructura.py
python exportar_datos.py

# Opción 2: Exportar todo en un solo archivo con MySQL
mysqldump -u root -h 127.0.0.1 -P 3306 pae > backup_completo.sql
```

### **Importar desde cero:**

```bash
# Edita importar_base_completa.py y cambia ARCHIVO_SQL al archivo deseado
python importar_base_completa.py
```

---

## 🔄 Proceso Automático de Importación

El script `importar_base_completa.py` realiza:

1. ✅ **Elimina** la base de datos existente
2. ✅ **Crea** una base de datos nueva vacía
3. ✅ **Importa** estructura y datos desde el SQL
4. ✅ **Sincroniza** las migraciones de Django (fake)
5. ✅ **Crea** las tablas de Django necesarias (sesiones, auth, etc.)
6. ✅ **Verifica** que todo esté correcto

---

## ⚙️ Configuración

Puedes editar las variables de conexión en cada script:

```python
DB_HOST = "127.0.0.1"
DB_PORT = "3306"
DB_USER = "root"
DB_PASSWORD = ""  # Agrega contraseña si la tienes
DB_NAME = "pae"
```

---

## 📊 Tablas Exportadas (en orden)

El script `exportar_datos.py` exporta las tablas en este orden para respetar las dependencias:

1. **Tablas base:** `usuarios`, `clientes`, `insumos`, `recetas`
2. **Dependencias nivel 1:** `detalle_insumo`, `receta_insumos`, `historial`
3. **Producción:** `produccion`, `produccion_recetas`
4. **Ventas:** `ventas`, `pago`, `venta_produccion`, `venta_recetas`

---

## 🛠️ Solución de Problemas

### Error: "mysqldump no encontrado"
Asegúrate de que MySQL esté instalado y en el PATH del sistema.

### Error: "Access denied"
Verifica usuario y contraseña en las variables de configuración.

### Error: "Table already exists"
El script de importación elimina automáticamente la BD antes de importar.

---

## 💾 Respaldo Manual

Si prefieres usar la línea de comandos directamente:

```bash
# Exportar todo
mysqldump -u root -h 127.0.0.1 -P 3306 pae > backup_completo.sql

# Importar todo
mysql -u root -h 127.0.0.1 -P 3306 -e "DROP DATABASE IF EXISTS pae; CREATE DATABASE pae;"
mysql -u root -h 127.0.0.1 -P 3306 pae < backup_completo.sql
python manage.py migrate --fake
```

---

## 📝 Notas Importantes

- ⚠️ **La importación elimina todos los datos existentes**
- 💾 Siempre haz un respaldo antes de importar
- 🔐 Las contraseñas de usuarios se importan tal cual están en el SQL
- ✅ Después de importar, ejecuta `python resetear_password.py` si es necesario

---

## 🎯 Ejemplo de Uso

```bash
# 1. Hacer respaldo de tu BD actual
python exportar_datos.py

# 2. Importar desde un archivo existente
# (edita importar_base_completa.py: ARCHIVO_SQL = "pae.sql")
python importar_base_completa.py

# 3. Verificar
python manage.py runserver
```

---

**¡Listo!** Ahora puedes exportar e importar tu base de datos con un solo comando. 🚀
