from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q, Sum
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from decimal import Decimal
from datetime import datetime
import openpyxl
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .models import Insumo, DetalleInsumo, HistorialInsumo


def actualizar_recetas_por_insumo(insumo):
    """
    Actualiza el estado de todas las recetas que usan un insumo específico
    """
    try:
        from modelos.recetas.models import Receta
        recetas_actualizadas = Receta.actualizar_estados_por_insumo(insumo)
        
        if recetas_actualizadas:
            nombres_recetas = [receta.nombre for receta in recetas_actualizadas]
            print(f"🔄 RECETAS ACTUALIZADAS por cambio en {insumo.nombre}: {nombres_recetas}")
        
        return recetas_actualizadas
        
    except ImportError:
        print(f"⚠️ No se pudo importar el modelo de Recetas")
        return []
    except Exception as e:
        print(f"❌ Error actualizando recetas por insumo {insumo.nombre}: {e}")
        return []


def actualizar_lotes_vencidos_sistema():
    """
    Función utilitaria para actualizar todos los lotes vencidos del sistema
    """
    from datetime import date
    
    # Buscar todos los lotes activos con fecha vencida
    lotes_vencidos = DetalleInsumo.objects.filter(
        estado='Activo',
        fecha_vencimiento__lt=date.today()
    )
    
    print(f"DEBUG: Encontrados {lotes_vencidos.count()} lotes vencidos en todo el sistema")
    
    insumos_afectados = {}
    
    # Procesar cada lote vencido
    for lote in lotes_vencidos:
        insumo = lote.id_ins
        
        # Acumular stock a restar por insumo
        if insumo.id_ins not in insumos_afectados:
            insumos_afectados[insumo.id_ins] = {
                'insumo': insumo,
                'stock_a_restar': Decimal('0.00'),
                'lotes_actualizados': 0
            }
        
        insumos_afectados[insumo.id_ins]['stock_a_restar'] += lote.cantidad
        insumos_afectados[insumo.id_ins]['lotes_actualizados'] += 1
        
        # Actualizar el lote
        lote.estado = 'Vencido'
        lote.save()
        
        print(f"DEBUG: Lote {lote.id_detalle} actualizado a Vencido - Fecha: {lote.fecha_vencimiento}")
    
    # Recalcular stock de cada insumo afectado basado SOLO en lotes activos
    for data in insumos_afectados.values():
        insumo = data['insumo']
        lotes_count = data['lotes_actualizados']
        
        # Calcular stock real sumando SOLO lotes activos
        stock_real = DetalleInsumo.objects.filter(
            id_ins=insumo,
            estado='Activo'
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0.00')
        
        stock_anterior = insumo.stock_actual
        insumo.stock_actual = stock_real
        insumo.recalcular_estado()
        insumo.save()
        
        print(f"DEBUG: Insumo {insumo.nombre} - Stock anterior: {stock_anterior}, Stock recalculado: {stock_real}, {lotes_count} lotes actualizados")
        
        # Actualizar recetas que usan este insumo
        actualizar_recetas_por_insumo(insumo)
    
    return len(insumos_afectados), lotes_vencidos.count()


def recalcular_stock_todos_insumos():
    """
    Recalcula el stock de todos los insumos basado SOLO en lotes activos
    """
    insumos = Insumo.objects.all()
    insumos_actualizados = 0
    
    for insumo in insumos:
        # Calcular stock real sumando SOLO lotes activos
        stock_real = DetalleInsumo.objects.filter(
            id_ins=insumo,
            estado='Activo'
        ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0.00')
        
        if insumo.stock_actual != stock_real:
            stock_anterior = insumo.stock_actual
            insumo.stock_actual = stock_real
            insumo.recalcular_estado()
            insumo.save()
            insumos_actualizados += 1
            
            print(f"DEBUG: Insumo {insumo.nombre} - Stock corregido: {stock_anterior} → {stock_real}")
    
    return insumos_actualizados


# ==================== LISTAR INSUMOS ====================
def listar_insumos(request):
    """
    Equivalente a: listar() en InsumosBean.java
    Muestra todos los insumos y actualiza sus estados según stock
    """
    try:
        # Traer todos los insumos inicialmente
        insumos = Insumo.objects.all().order_by('nombre')
        
        # Actualizar stock y estado según los lotes activos
        for insumo in insumos:
            # Calcular stock real usando solo lotes activos
            stock_real = DetalleInsumo.objects.filter(
                id_ins=insumo,
                estado='Activo'
            ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0.00')
            
            # Actualizar stock actual
            if insumo.stock_actual != stock_real:
                insumo.stock_actual = stock_real
                insumo.recalcular_estado()
                insumo.save()
        
        # Refrescar la lista después de actualizar
        insumos = Insumo.objects.all().order_by('nombre')

        # Filtro: solo productos que requieren lote (categorías obligatorias)
        categorias_con_lote = [
            'Enlatados', 'Envasados', 'Lácteos', 'Carnes', 'Bebidas',
            'Congelados', 'Panadería industrial', 'Salsas'
        ]
        solo_lote = request.GET.get('solo_lote') == '1'
        if solo_lote:
            insumos = insumos.filter(categoria__in=categorias_con_lote)
        
        # Calcular estadísticas
        total_insumos = insumos.count()
        insumos_activos = insumos.filter(estado='Activo').count()
        insumos_bajo_stock = insumos.filter(estado='Stock insuficiente').count()
        insumos_vencidos = insumos.filter(estado='Insumo vencido').count()
        
        # Alertas de stock bajo removidas (ya no se muestran mensajes individuales)
        
        # Paginación
        paginator = Paginator(insumos, 10)  # 10 insumos por página
        page = request.GET.get('page')
        
        try:
            insumos_paginados = paginator.page(page)
        except PageNotAnInteger:
            insumos_paginados = paginator.page(1)
        except EmptyPage:
            insumos_paginados = paginator.page(paginator.num_pages)
        
        contexto = {
            'insumos': insumos_paginados,
            'total_insumos': total_insumos,
            'insumos_activos': insumos_activos,
            'insumos_bajo_stock': insumos_bajo_stock,
            'insumos_vencidos': insumos_vencidos,
            'solo_lote': solo_lote,
            'categorias_con_lote': categorias_con_lote,
        }
        
        return render(request, 'insumos/index.html', contexto)
        
    except Exception as e:
        messages.error(request, f"Error al listar insumos: {str(e)}")
        return render(request, 'insumos/index.html', {'insumos': []})


# ==================== CREAR/AGREGAR INSUMO ====================
def crear_insumo(request):
    """
    Equivalente a: agregar() en InsumosBean.java
    Crea un nuevo insumo o actualiza si ya existe
    """
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip().title()
            unidad_medida = request.POST.get('unidad_medida', 'kg')
            stock_min = Decimal(request.POST.get('stock_min', '0'))
            stock_actual = Decimal('0')  # Stock inicial ya no se ingresa manualmente
            categoria = request.POST.get('categoria', 'Granel')
            
            # Validaciones
            if not nombre:
                messages.error(request, "El nombre del insumo es obligatorio")
                return redirect('insumos:index')
            
            # Verificar si ya existe
            insumo_existente = Insumo.objects.filter(nombre__iexact=nombre).first()
            
            if insumo_existente:
                # Solo actualizar categoría si cambió; no tocar stock por creación duplicada
                if insumo_existente.categoria != categoria:
                    insumo_existente.categoria = categoria
                    insumo_existente.save()
                    messages.info(request, f"ℹ️ Categoría de '{nombre}' actualizada a {categoria}")
                else:
                    messages.info(request, f"ℹ️ El insumo '{nombre}' ya existe. Use 'Agregar Stock' o lotes para incrementar.")
            else:
                # Crear nuevo insumo
                nuevo_insumo = Insumo.objects.create(
                    nombre=nombre,
                    unidad_medida=unidad_medida,
                    stock_min=stock_min,
                    stock_actual=stock_actual,
                    estado='Activo',
                    categoria=categoria
                )
                nuevo_insumo.recalcular_estado()
                nuevo_insumo.save()
                
                messages.success(request, f"✅ Insumo '{nombre}' creado correctamente")
            
            return redirect('insumos:index')
            
        except Exception as e:
            messages.error(request, f"Error al crear insumo: {str(e)}")
            return redirect('insumos:index')
    
    # GET: Mostrar formulario
    contexto = {
        'unidades_medida': Insumo.UNIDAD_CHOICES,
        'categorias': Insumo.CATEGORIA_CHOICES,
    }
    return render(request, 'insumos/crear.html', contexto)


# ==================== EDITAR INSUMO ====================
def editar_insumo(request, id_ins):
    """
    Equivalente a: editar() y actualizar() en InsumosBean.java
    Edita un insumo existente
    """
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    if request.method == 'POST':
        try:
            insumo.nombre = request.POST.get('nombre', '').strip().title()
            insumo.unidad_medida = request.POST.get('unidad_medida', 'kg')
            insumo.stock_min = Decimal(request.POST.get('stock_min', '0'))
            # stock_actual ya no se edita desde este formulario; se mantiene valor existente
            insumo.categoria = request.POST.get('categoria', insumo.categoria)
            
            insumo.recalcular_estado()
            insumo.save()
            
            messages.success(request, f"✅ Insumo '{insumo.nombre}' actualizado correctamente")
            return redirect('insumos:index')
            
        except Exception as e:
            messages.error(request, f"Error al actualizar: {str(e)}")
    
    contexto = {
        'insumo': insumo,
        'unidades_medida': Insumo.UNIDAD_CHOICES,
        'categorias': Insumo.CATEGORIA_CHOICES,
    }
    return render(request, 'insumos/editar.html', contexto)


# ==================== ELIMINAR INSUMO ====================
def eliminar_insumo(request, id_ins):
    """
    Equivalente a: eliminar() en InsumosBean.java
    Elimina un insumo
    """
    if request.method == 'POST':
        try:
            insumo = get_object_or_404(Insumo, id_ins=id_ins)
            nombre = insumo.nombre
            insumo.delete()
            
            messages.success(request, f"✅ Insumo '{nombre}' eliminado correctamente")
        except Exception as e:
            messages.error(request, f"Error al eliminar: {str(e)}")
    
    return redirect('insumos:index')


# ==================== AGREGAR STOCK (INGRESO) ====================
def agregar_stock(request, id_ins):
    """
    Nueva funcionalidad: Agregar stock a un insumo existente
    Crea un registro de ingreso en el historial
    """
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    if request.method == 'POST':
        try:
            cantidad = Decimal(request.POST.get('cantidad', '0'))
            fecha_vencimiento = request.POST.get('fecha_vencimiento', None)
            novedad = request.POST.get('novedad', f'Ingreso de {cantidad} {insumo.unidad_medida}')
            
            if cantidad <= 0:
                messages.error(request, "La cantidad debe ser mayor a cero")
                return redirect('insumos:detalle', id_ins=id_ins)
            
            # Crear detalle de insumo (lote)
            detalle = DetalleInsumo.objects.create(
                id_ins=insumo,
                cantidad=cantidad,
                fecha_vencimiento=fecha_vencimiento if fecha_vencimiento else None,
                estado='Activo'
            )
            
            # Actualizar stock del insumo
            insumo.agregar_stock(cantidad)
            insumo.save()
            
            # Registrar en historial
            HistorialInsumo.registrar_ingreso(
                insumo=insumo,
                cantidad=cantidad,
                detalle=detalle,
                novedad=novedad
            )
            
            messages.success(
                request,
                f"✅ Agregado {cantidad} {insumo.unidad_medida} de '{insumo.nombre}'"
            )
            return redirect('insumos:index')
            
        except Exception as e:
            messages.error(request, f"Error al agregar stock: {str(e)}")
    
    contexto = {
        'insumo': insumo,
    }
    return render(request, 'insumos/agregar_stock.html', contexto)


# ==================== REGISTRAR SALIDA ====================
def registrar_salida(request, id_ins):
    """
    Nueva funcionalidad: Registrar salida de stock
    """
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    if request.method == 'POST':
        try:
            cantidad = Decimal(request.POST.get('cantidad', '0'))
            motivo = request.POST.get('motivo', 'Salida por producción')
            
            if cantidad <= 0:
                messages.error(request, "La cantidad debe ser mayor a cero")
                return redirect('insumos:index')
            
            if cantidad > insumo.stock_actual:
                messages.error(
                    request,
                    f"Stock insuficiente. Disponible: {insumo.stock_actual} {insumo.unidad_medida}"
                )
                return redirect('insumos:index')
            
            # Reducir stock
            insumo.reducir_stock(cantidad)
            insumo.save()
            
            # Registrar en historial
            HistorialInsumo.registrar_salida(
                insumo=insumo,
                cantidad=cantidad,
                novedad=motivo
            )
            
            messages.success(
                request,
                f"✅ Salida registrada: {cantidad} {insumo.unidad_medida} de '{insumo.nombre}'"
            )
            
        except Exception as e:
            messages.error(request, f"Error al registrar salida: {str(e)}")
    
    return redirect('insumos:index')


# ==================== VER HISTORIAL ====================
def ver_historial(request, id_ins=None):
    """
    Muestra el historial de movimientos de insumos
    """
    if id_ins:
        insumo = get_object_or_404(Insumo, id_ins=id_ins)
        historial = HistorialInsumo.objects.filter(insumo=insumo).order_by('-fecha')
        titulo = f"Historial de {insumo.nombre}"
    else:
        historial = HistorialInsumo.objects.all().order_by('-fecha')
        titulo = "Historial de todos los insumos"
        insumo = None
    
    contexto = {
        'historial': historial[:100],  # Últimos 100 registros
        'insumo': insumo,
        'titulo': titulo,
    }
    return render(request, 'insumos/historial.html', contexto)


# ==================== MIGRAR DESDE EXCEL ====================
def migrar_excel(request):
    """
    Equivalente a: migrar() en InsumosBean.java
    Importa insumos desde un archivo Excel
    """
    if request.method == 'POST' and request.FILES.get('excel'):
        try:
            archivo_excel = request.FILES['excel']
            wb = openpyxl.load_workbook(archivo_excel)
            hoja = wb.active
            
            contador = 0
            for fila in hoja.iter_rows(min_row=2, values_only=True):  # Saltar encabezado
                if not fila[0]:  # Si no hay nombre, saltar
                    continue
                
                nombre = str(fila[0]).strip().title()
                unidad_medida = str(fila[1] if fila[1] else 'kg')
                stock_min = Decimal(str(fila[2] if fila[2] else 0))
                stock_actual = Decimal(str(fila[3] if fila[3] else 0))
                
                # Crear o actualizar
                insumo, created = Insumo.objects.get_or_create(
                    nombre=nombre,
                    defaults={
                        'unidad_medida': unidad_medida,
                        'stock_min': stock_min,
                        'stock_actual': stock_actual,
                        'estado': 'Activo'
                    }
                )
                
                if not created:
                    insumo.stock_actual += stock_actual
                    insumo.save()
                
                contador += 1
            
            messages.success(request, f"✅ {contador} insumos migrados correctamente")
            
        except Exception as e:
            messages.error(request, f"Error al migrar: {str(e)}")
    
    return redirect('insumos:index')


# ==================== EXPORTAR PDF ====================
def exportar_pdf(request):
    """
    Equivalente a: exportarPDF() en InsumosBean.java
    Genera un PDF con la lista de insumos
    """
    try:
        # Crear respuesta HTTP
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Insumos.pdf"'
        
        # Crear documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            'Titulo',
            parent=estilos['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Título
        titulo = Paragraph("LISTADO DE INSUMOS", estilo_titulo)
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3 * inch))
        
        # Datos de la tabla
        datos = [['ID', 'Nombre', 'Unidad', 'Stock Mín.', 'Stock Actual', 'Estado']]
        
        insumos = Insumo.objects.all().order_by('nombre')
        for insumo in insumos:
            datos.append([
                str(insumo.id_ins),
                insumo.nombre,
                insumo.get_unidad_medida_display(),
                str(insumo.stock_min),
                str(insumo.stock_actual),
                insumo.estado
            ])
        
        # Crear tabla
        tabla = Table(datos, colWidths=[0.6*inch, 2.5*inch, 0.8*inch, 1*inch, 1*inch, 1.3*inch])
        
        # Estilo de la tabla
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elementos.append(tabla)
        
        # Construir PDF
        doc.build(elementos)
        
        # Obtener contenido del buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar PDF: {str(e)}")
        return redirect('insumos:index')


# ==================== ALERTAS DE STOCK ====================
def alertas_stock(request):
    """
    Muestra insumos con stock bajo o agotados
    """
    insumos_bajo_stock = Insumo.objects.filter(estado='Stock insuficiente').order_by('nombre')
    insumos_agotados = Insumo.objects.filter(stock_actual=0).order_by('nombre')
    
    contexto = {
        'insumos_bajo_stock': insumos_bajo_stock,
        'insumos_agotados': insumos_agotados,
    }
    return render(request, 'insumos/alertas.html', contexto)


# ==================== DETALLE DE INSUMO ====================
def detalle_insumo(request, id_ins):
    """
    Equivalente a: cargarLotesPorInsumo() en DetalleInsumoBean.java
    Muestra detalle completo de un insumo con sus lotes y historial
    """
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    # PRIMERO: Actualizar automáticamente todos los lotes vencidos
    from datetime import date
    lotes_para_actualizar = DetalleInsumo.objects.filter(
        id_ins=insumo,
        estado='Activo',
        fecha_vencimiento__lt=date.today()
    )
    
    if lotes_para_actualizar.exists():
        print(f"DEBUG: Encontrados {lotes_para_actualizar.count()} lotes activos con fecha vencida")
        
        # Actualizar cada lote vencido
        stock_a_restar = Decimal('0.00')
        for lote in lotes_para_actualizar:
            print(f"DEBUG: Actualizando lote {lote.id_detalle} - Fecha: {lote.fecha_vencimiento}, Cantidad: {lote.cantidad}")
            stock_a_restar += lote.cantidad
            lote.estado = 'Vencido'
            lote.save()
            
            # Registrar en historial
            try:
                HistorialInsumo.objects.create(
                    insumo=insumo,
                    accion='Vencimiento',
                    cantidad=int(lote.cantidad),
                    novedad=f'Lote vencido automáticamente - Fecha vencimiento: {lote.fecha_vencimiento}',
                    estado='Vencido',
                    stock_actual=int(insumo.stock_actual - stock_a_restar),
                    id_detalle=lote.id_detalle
                )
            except:
                pass
        
        # Recalcular stock del insumo basado SOLO en lotes activos
        if stock_a_restar > 0:
            # Calcular stock real sumando SOLO lotes activos
            stock_real = DetalleInsumo.objects.filter(
                id_ins=insumo,
                estado='Activo'
            ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0.00')
            
            stock_anterior = insumo.stock_actual
            insumo.stock_actual = stock_real
            insumo.recalcular_estado()
            insumo.save()
            
            print(f"DEBUG: Stock recalculado - Anterior: {stock_anterior}, Actual: {stock_real} (solo lotes activos)")
            
            # Actualizar recetas que usan este insumo
            recetas_actualizadas = actualizar_recetas_por_insumo(insumo)
            
            # Mostrar mensaje al usuario
            mensaje_base = f"ℹ️ Se actualizaron automáticamente {lotes_para_actualizar.count()} lotes vencidos. Stock recalculado: {stock_real} {insumo.unidad_medida} (solo lotes activos)"
            if recetas_actualizadas:
                mensaje_base += f". {len(recetas_actualizadas)} recetas afectadas"
            
            messages.info(request, mensaje_base)
    
    # Obtener lotes activos y vencidos (equivalente a listarPorInsumoYEstado)
    lotes = DetalleInsumo.objects.filter(
        id_ins=insumo,
        estado__in=['Activo', 'Vencido']
    ).order_by('-fecha_ingreso')
    
    print(f"DEBUG: Insumo {insumo.nombre} tiene {lotes.count()} lotes")
    
    # Separar lotes por estado
    lotes_activos = lotes.filter(estado='Activo')
    lotes_vencidos = lotes.filter(estado='Vencido')
    
    # Obtener historial reciente (si existe la tabla)
    try:
        historial = HistorialInsumo.objects.filter(insumo=insumo).order_by('-fecha')[:20]
    except:
        historial = []
    
    # Paginación de lotes
    paginator = Paginator(lotes, 10)
    page = request.GET.get('page')
    
    try:
        lotes_paginados = paginator.page(page)
    except PageNotAnInteger:
        lotes_paginados = paginator.page(1)
    except EmptyPage:
        lotes_paginados = paginator.page(paginator.num_pages)
    
    contexto = {
        'insumo': insumo,
        'lotes': lotes_paginados,
        'lotes_activos': lotes_activos,
        'lotes_vencidos': lotes_vencidos,
        # Historial enriquecido para mostrar stock antes/después y delta sin cambiar el modelo/DB
        'historiales': historial,
        'historiales_enriquecidos': [
            {
                'obj': h,
                'accion': h.accion,
                'fecha': h.fecha,
                'lote_id': h.id_detalle,
                'cantidad': h.cantidad,
                'stock_despues': h.stock_actual,
                # Stock antes y delta calculados según tipo de acción actual
                'stock_antes': (
                    (h.stock_actual - h.cantidad) if h.accion in ['Entrada'] else
                    (h.stock_actual + h.cantidad) if h.accion in ['Salida','Merma','Vencimiento'] else
                    None
                ),
                'delta_signo': (
                    '+' if h.accion in ['Entrada'] else
                    '-' if h.accion in ['Salida','Merma','Vencimiento'] else
                    '±'
                ),
                'delta_valor': (
                    h.cantidad if h.accion in ['Entrada','Salida','Merma','Vencimiento'] else h.cantidad
                ),
                'novedad': h.novedad,
            }
            for h in historial
        ],
        'total_lotes': lotes.count(),
    }
    return render(request, 'insumos/detalle.html', contexto)


# ==================== AGREGAR LOTE ====================
def agregar_lote(request, id_ins):
    """
    Equivalente a: agregar() en DetalleInsumoBean.java
    Agrega un nuevo lote a un insumo
    """
    print(f"DEBUG: ¡¡¡ENTRANDO A AGREGAR_LOTE!!! id_ins={id_ins}, method={request.method}")
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    if request.method == 'POST':
        print(f"DEBUG: Iniciando agregar_lote para {insumo.nombre}")
        print(f"DEBUG: Datos POST: {request.POST}")
        
        try:
            cantidad = Decimal(request.POST.get('cantidad', '0'))
            fecha_vencimiento_str = request.POST.get('fecha_vencimiento')
            estado = request.POST.get('estado', 'Activo')
            
            # Convertir string de fecha a objeto date
            from datetime import datetime
            fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, '%Y-%m-%d').date() if fecha_vencimiento_str else None
            
            print(f"DEBUG: cantidad={cantidad}, fecha_vencimiento={fecha_vencimiento}, estado={estado}")
            
            # Validaciones
            if cantidad <= 0:
                print(f"DEBUG: Error - Cantidad inválida: {cantidad}")
                messages.error(request, "La cantidad debe ser mayor a cero")
                return redirect('insumos:detalle', id_ins=id_ins)
            
            # Validar fecha de vencimiento SOLO si la categoría requiere lote
            if insumo.requiere_lote and not fecha_vencimiento_str:
                print(f"DEBUG: Error - Fecha de vencimiento vacía y categoría requiere lote")
                messages.error(request, "La fecha de vencimiento es obligatoria para esta categoría")
                return redirect('insumos:detalle', id_ins=id_ins)

            # Si no requiere lote, ignorar cualquier fecha vacía
            if not insumo.requiere_lote:
                fecha_vencimiento = None
            
            # Crear el lote
            detalle = DetalleInsumo.objects.create(
                id_ins=insumo,
                cantidad=cantidad,
                fecha_vencimiento=fecha_vencimiento,
                estado=estado
            )
            
            print(f"DEBUG: Lote creado - ID: {detalle.id_detalle}, Cantidad: {cantidad}, Estado: {estado}")
            
            # Actualizar stock del insumo si el lote está activo
            if estado == 'Activo':
                insumo.stock_actual += cantidad
                insumo.recalcular_estado()
                insumo.save()
            
            # Registrar en historial (si es posible)
            try:
                HistorialInsumo.objects.create(
                    insumo=insumo,
                    accion='Entrada',
                    cantidad=int(cantidad),
                    novedad=f'Se agregó lote de {cantidad} unidades',
                    estado='Ingreso de lote',
                    stock_actual=int(insumo.stock_actual),
                    id_detalle=detalle.id_detalle
                )
            except:
                pass  # Si no existe la tabla historial, continuar sin error
            
            messages.success(
                request,
                f"✅ Lote agregado correctamente. Stock actual: {insumo.stock_actual} {insumo.unidad_medida}"
            )
            
        except Exception as e:
            print(f"DEBUG: EXCEPCIÓN en agregar_lote: {str(e)}")
            print(f"DEBUG: Tipo de excepción: {type(e)}")
            messages.error(request, f"Error al agregar lote: {str(e)}")
    else:
        print(f"DEBUG: Método no es POST, es: {request.method}")
    
    return redirect('insumos:detalle', id_ins=id_ins)


# ==================== EDITAR LOTE ====================
def editar_lote(request, id_ins):
    """
    Equivalente a: actualizar() en DetalleInsumoBean.java
    Edita un lote existente con motivo
    """
    print(f"🔵 DEBUG: Entrada a editar_lote - id_ins={id_ins}, method={request.method}")
    
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    print(f"🔵 DEBUG: Insumo encontrado: {insumo.nombre}")
    
    if request.method == 'POST':
        print(f"🔵 DEBUG: Método POST detectado")
        print(f"🔵 DEBUG: Datos POST recibidos: {dict(request.POST)}")
        try:
            lote_id = request.POST.get('lote_id')
            cantidad_str = request.POST.get('cantidad', '0')
            fecha_vencimiento = request.POST.get('fecha_vencimiento')
            estado = request.POST.get('estado', 'Activo')
            motivo_edicion = request.POST.get('motivo_edicion', '').strip()
            
            print(f"🔵 DEBUG: Valores extraídos del POST:")
            print(f"  - lote_id: '{lote_id}'")
            print(f"  - cantidad_str: '{cantidad_str}'")
            print(f"  - fecha_vencimiento: '{fecha_vencimiento}'")
            print(f"  - estado: '{estado}'")
            print(f"  - motivo_edicion: '{motivo_edicion}'")
            
            try:
                cantidad = Decimal(cantidad_str)
                print(f"🔵 DEBUG: Cantidad convertida a Decimal: {cantidad}")
            except Exception as e:
                print(f"❌ DEBUG: Error convirtiendo cantidad a Decimal: {e}")
                cantidad = Decimal('0')
            
            # Obtener el lote a editar PRIMERO
            print(f"🔵 DEBUG: Buscando lote con id_detalle={lote_id}")
            lote = get_object_or_404(DetalleInsumo, id_detalle=lote_id, id_ins=insumo)
            print(f"🔵 DEBUG: Lote encontrado: {lote}")
            
            # Usar la cantidad original del lote (no permitir cambios)
            cantidad_anterior = lote.cantidad
            cantidad = cantidad_anterior  # Mantener cantidad original
            print(f"🔵 DEBUG: Cantidad original del lote: {cantidad}")
            
            # Validaciones
            print(f"🔵 DEBUG: Iniciando validaciones...")
            
            if not motivo_edicion:
                print(f"❌ DEBUG: Falta motivo de edición")
                messages.error(request, "Debe ingresar un motivo de edición")
                return redirect('insumos:detalle', id_ins=id_ins)
            print(f"✅ DEBUG: Motivo de edición válido")
            
            if insumo.requiere_lote:
                if not fecha_vencimiento:
                    print(f"❌ DEBUG: Falta fecha de vencimiento (categoría requiere)")
                    messages.error(request, "La fecha de vencimiento es obligatoria para esta categoría")
                    return redirect('insumos:detalle', id_ins=id_ins)
                print(f"✅ DEBUG: Fecha de vencimiento válida")
            else:
                # Categoría sin lote: ignorar fecha enviada y forzar None
                fecha_vencimiento = None
                estado = 'Activo'
            estado_anterior = lote.estado
            
            # Convertir string de fecha a objeto date
            from datetime import datetime, date
            if isinstance(fecha_vencimiento, str):
                fecha_vencimiento = datetime.strptime(fecha_vencimiento, '%Y-%m-%d').date()
            
            # Lógica automática de estado basada en fecha de vencimiento
            if fecha_vencimiento and fecha_vencimiento < date.today():
                estado = 'Vencido'
                print(f"DEBUG: Fecha {fecha_vencimiento} ya pasó, cambiando estado a Vencido")
            elif estado == 'Vencido' and fecha_vencimiento and fecha_vencimiento >= date.today():
                estado = 'Activo'
                print(f"DEBUG: Fecha {fecha_vencimiento} es futura, cambiando estado a Activo")
            
            # Actualizar datos del lote (cantidad no cambia)
            lote.fecha_vencimiento = fecha_vencimiento  # Será None para categorías sin lote
            lote.estado = estado
            
            lote.save()
            
            print(f"DEBUG: Lote actualizado - Estado anterior: {estado_anterior}, Estado nuevo: {estado}, Cantidad: {cantidad}")
            
            # Recalcular stock completo basado SOLO en lotes activos (cantidad nunca cambia, solo estado)
            stock_real = DetalleInsumo.objects.filter(
                id_ins=insumo,
                estado='Activo'
            ).aggregate(total=Sum('cantidad'))['total'] or Decimal('0.00')
            
            stock_anterior = insumo.stock_actual
            insumo.stock_actual = stock_real
            insumo.recalcular_estado()
            insumo.save()
            
            print(f"DEBUG: Stock recalculado completamente - Anterior: {stock_anterior}, Actual: {stock_real} (solo lotes activos)")
            
            # Actualizar recetas que usan este insumo
            recetas_actualizadas = actualizar_recetas_por_insumo(insumo)
            if recetas_actualizadas:
                messages.info(request, 
                    f"ℹ️ Se actualizaron {len(recetas_actualizadas)} recetas que usan este insumo"
                )
            
            # Mensaje especial si se cambió automáticamente el estado
            if estado != request.POST.get('estado'):
                messages.info(request, f"ℹ️ Estado actualizado automáticamente a '{estado}' basado en la fecha de vencimiento")
            
            # Registrar en historial (si es posible)
            try:
                HistorialInsumo.objects.create(
                    insumo=insumo,
                    accion='Edición',
                    cantidad=int(cantidad),
                    novedad=motivo_edicion,
                    estado='Edición',
                    stock_actual=int(insumo.stock_actual),
                    id_detalle=lote.id_detalle
                )
            except:
                pass  # Si no existe la tabla historial, continuar sin error
            
            print(f"✅ DEBUG: Lote actualizado exitosamente")
            messages.success(request, "✅ Lote actualizado correctamente")
            
        except Exception as e:
            print(f"❌ DEBUG: Excepción en editar_lote: {str(e)}")
            print(f"❌ DEBUG: Tipo de excepción: {type(e)}")
            import traceback
            print(f"❌ DEBUG: Traceback completo: {traceback.format_exc()}")
            messages.error(request, f"Error al actualizar lote: {str(e)}")
    else:
        print(f"🔵 DEBUG: Método no es POST, es: {request.method}")
    
    print(f"🔵 DEBUG: Redirigiendo a detalle de insumo {id_ins}")
    return redirect('insumos:detalle', id_ins=id_ins)


# ==================== ELIMINAR LOTE ====================
def eliminar_lote(request, id_ins):
    """
    Equivalente a: eliminarConMotivo() en DetalleInsumoBean.java
    Elimina un lote con motivo (marca como eliminado)
    """
    insumo = get_object_or_404(Insumo, id_ins=id_ins)
    
    if request.method == 'POST':
        try:
            lote_id = request.POST.get('lote_id')
            motivo_eliminacion = request.POST.get('motivo_eliminacion', '').strip()
            
            # Validaciones
            if not motivo_eliminacion:
                messages.error(request, "Debe ingresar un motivo de eliminación")
                return redirect('insumos:detalle', id_ins=id_ins)
            
            # Obtener el lote a eliminar
            lote = get_object_or_404(DetalleInsumo, id_detalle=lote_id, id_ins=insumo)
            estado_anterior = lote.estado
            cantidad_lote = lote.cantidad
            
            # Marcar como eliminado
            lote.estado = 'Eliminado'
            lote.save()
            
            # Si el lote estaba activo, descontar del stock
            if estado_anterior == 'Activo':
                insumo.stock_actual -= cantidad_lote
                if insumo.stock_actual < 0:
                    insumo.stock_actual = Decimal('0.00')
                insumo.recalcular_estado()
                insumo.save()
            
            # Determinar estado para historial
            estado_historial = 'Eliminado'
            if estado_anterior == 'Vencido':
                estado_historial = 'Vencimiento'
            
            # Registrar en historial (si es posible)
            try:
                HistorialInsumo.objects.create(
                    insumo=insumo,
                    accion='Salida',
                    cantidad=int(cantidad_lote),
                    novedad=motivo_eliminacion,
                    estado=estado_historial,
                    stock_actual=int(insumo.stock_actual),
                    id_detalle=lote.id_detalle
                )
            except:
                pass  # Si no existe la tabla historial, continuar sin error
            
            messages.warning(
                request,
                f"⚠️ Lote eliminado correctamente. Stock descontado: {cantidad_lote} {insumo.unidad_medida}"
            )
            
        except Exception as e:
            messages.error(request, f"Error al eliminar lote: {str(e)}")
    
    return redirect('insumos:detalle', id_ins=id_ins)


# ==================== CORREGIR LOTES VENCIDOS ====================
def corregir_lotes_vencidos(request):
    """
    Ejecuta corrección masiva de lotes vencidos en todo el sistema
    """
    if request.method == 'POST':
        try:
            # Paso 1: Corregir lotes vencidos
            insumos_afectados, lotes_corregidos = actualizar_lotes_vencidos_sistema()
            
            # Paso 2: Recalcular stock de todos los insumos (por seguridad)
            insumos_stock_corregidos = recalcular_stock_todos_insumos()
            
            if lotes_corregidos > 0 or insumos_stock_corregidos > 0:
                mensaje = f"✅ Corrección completada:\n"
                if lotes_corregidos > 0:
                    mensaje += f"• {lotes_corregidos} lotes vencidos actualizados\n"
                if insumos_stock_corregidos > 0:
                    mensaje += f"• {insumos_stock_corregidos} insumos con stock recalculado\n"
                mensaje += "• Stock basado solo en lotes activos"
                
                messages.success(request, mensaje)
            else:
                messages.info(request, "ℹ️ No se encontraron correcciones necesarias")
                
        except Exception as e:
            messages.error(request, f"❌ Error durante la corrección: {str(e)}")
    
    return redirect('insumos:index')


# ==================== OBTENER DATOS DE LOTE (AJAX) ====================
def obtener_lote(request, lote_id):
    """
    API para obtener datos de un lote específico (para modal de edición)
    """
    try:
        lote = get_object_or_404(DetalleInsumo, id_detalle=lote_id)
        
        datos = {
            'id_detalle': lote.id_detalle,
            'cantidad': float(lote.cantidad),
            'fecha_vencimiento': lote.fecha_vencimiento.strftime('%Y-%m-%d') if lote.fecha_vencimiento else '',
            'estado': lote.estado
        }
        
        return JsonResponse(datos)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==================== EXPORTAR LOTES PDF ====================
def exportar_lotes_pdf(request, id_ins):
    """
    Genera PDF con los lotes de un insumo específico
    """
    try:
        insumo = get_object_or_404(Insumo, id_ins=id_ins)
        lotes = DetalleInsumo.objects.filter(
            id_ins=insumo,
            estado__in=['Activo', 'Vencido']
        ).order_by('-fecha_ingreso')
        
        # Crear respuesta HTTP
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="Lotes_{insumo.nombre}.pdf"'
        
        # Crear documento PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elementos = []
        
        # Estilos
        estilos = getSampleStyleSheet()
        estilo_titulo = ParagraphStyle(
            'Titulo',
            parent=estilos['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Título
        titulo = Paragraph(f"LOTES DE INSUMO: {insumo.nombre.upper()}", estilo_titulo)
        elementos.append(titulo)
        elementos.append(Spacer(1, 0.3 * inch))
        
        # Información del insumo
        info = Paragraph(
            f"<b>Stock Actual:</b> {insumo.stock_actual} {insumo.get_unidad_medida_display()} | "
            f"<b>Estado:</b> {insumo.estado}",
            estilos['Normal']
        )
        elementos.append(info)
        elementos.append(Spacer(1, 0.2 * inch))
        
        # Datos de la tabla
        datos = [['ID', 'Insumo', 'Cantidad', 'F. Ingreso', 'F. Vencimiento', 'Estado']]
        
        for lote in lotes:
            datos.append([
                str(lote.id_detalle),
                insumo.nombre,
                str(lote.cantidad),
                lote.fecha_ingreso.strftime('%d/%m/%Y %H:%M') if lote.fecha_ingreso else 'N/A',
                lote.fecha_vencimiento.strftime('%d/%m/%Y') if lote.fecha_vencimiento else 'N/A',
                lote.estado
            ])
        
        # Crear tabla
        tabla = Table(datos, colWidths=[0.7*inch, 1.5*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.8*inch])
        
        # Estilo de la tabla
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        elementos.append(tabla)
        
        # Construir PDF
        doc.build(elementos)
        
        # Obtener contenido del buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error al generar PDF: {str(e)}")
        return redirect('insumos:detalle', id_ins=id_ins)


# ==================== STUB: ENVIAR CORREOS INSUMOS ====================
def correos_insumos(request):
    """Stub para acción de 'Enviar Correos' en encabezado unificado.
    En el futuro aquí se podría implementar:
    - Envío de alertas de stock bajo a administradores
    - Reportes periódicos de insumos vencidos
    - Resumen semanal de movimientos
    Por ahora solo muestra un mensaje informativo y redirige al índice."""
    messages.info(request, "ℹ️ Módulo 'Enviar Correos' de Insumos aún no implementado.")
    return redirect('insumos:index')
