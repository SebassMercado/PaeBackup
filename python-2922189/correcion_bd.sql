-- Script de corrección para la base de datos PAE
-- Corrige inconsistencias y problemas encontrados

-- ==================================================
-- 1. CORRECCIÓN DE ESTADOS VACÍOS EN PRODUCCIÓN
-- ==================================================
UPDATE produccion 
SET estado = 'Pendiente' 
WHERE estado = '' OR estado IS NULL;

-- ==================================================
-- 2. CORRECCIÓN DE NITs TEMPORALES A NITs VÁLIDOS
-- ==================================================
UPDATE clientes SET nit = '900123456-7' WHERE nit = 'TEMP-1';
UPDATE clientes SET nit = '900234567-8' WHERE nit = 'TEMP-2';
UPDATE clientes SET nit = '79123456-5' WHERE nit = 'TEMP-3';
UPDATE clientes SET nit = '52987654-3' WHERE nit = 'TEMP-4';
UPDATE clientes SET nit = '18456789-2' WHERE nit = 'TEMP-5';
UPDATE clientes SET nit = '900345678-9' WHERE nit = 'TEMP-8';
UPDATE clientes SET nit = '71234567-6' WHERE nit = 'TEMP-9';
UPDATE clientes SET nit = '900456789-0' WHERE nit = 'TEMP-10';

-- ==================================================
-- 3. CORRECCIÓN DE CORREOS INVÁLIDOS
-- ==================================================
UPDATE clientes SET correo = 'chatgpt@openai.com' WHERE correo = 'chatopneai';

-- ==================================================
-- 4. CORRECCIÓN DE CANTIDADES EN VENTA_PRODUCCIÓN
-- ==================================================
-- Las cantidades 0 no tienen sentido, las corregimos a 1
UPDATE venta_produccion SET cantidad = 1 WHERE cantidad = 0;

-- ==================================================
-- 5. CORRECCIÓN DE FECHAS DE VENCIMIENTO INCONSISTENTES
-- ==================================================
-- Corregir fechas de vencimiento que son anteriores a la fecha de ingreso
UPDATE detalle_insumo 
SET fecha_vencimiento = DATE_ADD(fecha_ingreso, INTERVAL 30 DAY)
WHERE fecha_vencimiento < DATE(fecha_ingreso);

-- ==================================================
-- 6. CORRECCIÓN DE STOCK ACTUAL NEGATIVO
-- ==================================================
-- Los stocks no pueden ser negativos, los ponemos en 0
UPDATE insumos SET stock_actual = 0.00 WHERE stock_actual < 0;

-- ==================================================
-- 7. CORRECCIÓN DE ESTADOS INCONSISTENTES EN DETALLE_INSUMO
-- ==================================================
-- Si la cantidad es 0, el estado debería ser 'Agotado'
UPDATE detalle_insumo 
SET estado = 'Agotado' 
WHERE cantidad = 0 AND estado = 'Activo';

-- Si la fecha de vencimiento ya pasó, el estado debería ser 'Vencido'
UPDATE detalle_insumo 
SET estado = 'Vencido' 
WHERE fecha_vencimiento < CURDATE() AND estado = 'Activo';

-- ==================================================
-- 8. CORRECCIÓN DE PRECIOS Y SUBTOTALES EN VENTA_RECETAS
-- ==================================================
-- Recalcular subtotales basados en cantidad * precio
UPDATE venta_recetas 
SET subtotal = cantidad * precio 
WHERE subtotal != cantidad * precio;

-- ==================================================
-- 9. CORRECCIÓN DE TOTALES EN VENTAS
-- ==================================================
-- Actualizar totales de ventas basándose en los subtotales de venta_recetas
UPDATE ventas v
SET total = (
    SELECT COALESCE(SUM(vr.subtotal), 0)
    FROM venta_recetas vr 
    WHERE vr.id_venta = v.id_ven
)
WHERE v.id_ven IN (SELECT DISTINCT id_venta FROM venta_recetas);

-- ==================================================
-- 10. CORRECCIÓN DE ESTADOS DE INSUMOS BASADO EN STOCK
-- ==================================================
UPDATE insumos 
SET estado = 'Stock insuficiente' 
WHERE stock_actual <= stock_min AND estado = 'Activo';

UPDATE insumos 
SET estado = 'Activo' 
WHERE stock_actual > stock_min AND estado = 'Stock insuficiente';

-- ==================================================
-- 11. LIMPIEZA DE REGISTROS HUÉRFANOS
-- ==================================================
-- Eliminar detalles de insumo que apunten a insumos que no existen
DELETE FROM detalle_insumo 
WHERE id_ins NOT IN (SELECT id_ins FROM insumos);

-- Eliminar historiales que apunten a detalles que no existen
DELETE FROM historial 
WHERE id_detalle IS NOT NULL 
AND id_detalle NOT IN (SELECT id_detalle FROM detalle_insumo);

-- ==================================================
-- 12. CORRECCIÓN DE CAMPOS REQUERIDOS VACÍOS
-- ==================================================
-- Asegurar que no hay nombres vacíos en insumos
UPDATE insumos 
SET nombre = CONCAT('Insumo_', id_ins) 
WHERE nombre = '' OR nombre IS NULL;

-- Asegurar que no hay nombres vacíos en recetas
UPDATE recetas 
SET nombre = CONCAT('Receta_', id_rec) 
WHERE nombre = '' OR nombre IS NULL;

-- ==================================================
-- 13. CORRECCIÓN DE TELÉFONOS INVÁLIDOS
-- ==================================================
-- Los teléfonos deben tener formato válido colombiano
UPDATE usuarios 
SET telefono = 3001234567 
WHERE telefono = 0 OR telefono IS NULL;

UPDATE clientes 
SET telefono = '3001234567' 
WHERE telefono = '' OR telefono IS NULL;

-- ==================================================
-- 14. ACTUALIZACIÓN DE STOCK ACTUAL BASADO EN DETALLES ACTIVOS
-- ==================================================
-- Recalcular stock actual basándose en la suma de cantidades de detalles activos
UPDATE insumos i
SET stock_actual = (
    SELECT COALESCE(SUM(di.cantidad), 0)
    FROM detalle_insumo di
    WHERE di.id_ins = i.id_ins 
    AND di.estado = 'Activo'
);

-- ==================================================
-- 15. CORRECCIÓN FINAL DE ESTADOS DE RECETA_INSUMOS
-- ==================================================
-- Marcar como 'Agotado' los insumos de recetas que no tienen stock
UPDATE receta_insumos ri
SET estado = 'Agotado'
WHERE ri.id_ins IN (
    SELECT id_ins FROM insumos 
    WHERE estado = 'Stock insuficiente' OR stock_actual = 0
);

UPDATE receta_insumos ri
SET estado = 'Activo'
WHERE ri.id_ins IN (
    SELECT id_ins FROM insumos 
    WHERE estado = 'Activo' AND stock_actual > 0
);

-- ==================================================
-- VERIFICACIONES FINALES
-- ==================================================
-- Consulta para verificar que no hay registros con problemas
SELECT 'Verificación completada' as status;

-- Verificar producción sin estados vacíos
SELECT COUNT(*) as producciones_sin_estado 
FROM produccion 
WHERE estado = '' OR estado IS NULL;

-- Verificar NITs válidos
SELECT COUNT(*) as clientes_con_nit_temporal 
FROM clientes 
WHERE nit LIKE 'TEMP-%';

-- Verificar stock negativo
SELECT COUNT(*) as insumos_stock_negativo 
FROM insumos 
WHERE stock_actual < 0;

-- Verificar fechas inconsistentes
SELECT COUNT(*) as fechas_vencimiento_inconsistentes 
FROM detalle_insumo 
WHERE fecha_vencimiento < DATE(fecha_ingreso);