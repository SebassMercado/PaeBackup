from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Count, Sum, F
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
import openpyxl
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import io
from datetime import datetime

from .models import Receta, RecetaInsumo
from modelos.insumos.models import Insumo
from .utils import actualizar_todos_los_estados_ingredientes, obtener_estadisticas_disponibilidad


def actualizar_estados_ingredientes():
    """
    Función para actualizar automáticamente los estados de todos los ingredientes
    basándose en el stock de los insumos
    """
    return actualizar_todos_los_estados_ingredientes()


# ==================== LISTAR RECETAS ====================
def listar_recetas(request):
    """
    Equivalente a: listar() en recetasBean.java
    Lista todas las recetas con filtros y paginación
    """
    # Actualizar estados de todas las recetas antes de listar
    for receta in Receta.objects.all():
        if receta.verificar_y_actualizar_estado():
            receta.save()
    
    # Obtener parámetros de filtro
    busqueda = request.GET.get('busqueda', '')
    estado_filtro = request.GET.get('estado', '')
    precio_min = request.GET.get('precio_min', '')
    precio_max = request.GET.get('precio_max', '')
    
    # Query base
    recetas = Receta.objects.all()
    
    # Aplicar filtros
    if busqueda:
        recetas = recetas.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    
    if estado_filtro:
        recetas = recetas.filter(estado=estado_filtro)
    
    if precio_min:
        try:
            recetas = recetas.filter(precio__gte=Decimal(precio_min))
        except:
            pass
    
    if precio_max:
        try:
            recetas = recetas.filter(precio__lte=Decimal(precio_max))
        except:
            pass
    
    # Estadísticas
    total_recetas = recetas.count()
    recetas_activas = recetas.filter(estado='Activo').count()
    recetas_inactivas = recetas.filter(estado='Inactivo').count()
    
    # Ordenar por nombre
    recetas = recetas.order_by('nombre')
    
    # Paginación
    paginator = Paginator(recetas, 12)  # 12 recetas por página
    page = request.GET.get('page')
    
    try:
        recetas_paginadas = paginator.page(page)
    except PageNotAnInteger:
        recetas_paginadas = paginator.page(1)
    except EmptyPage:
        recetas_paginadas = paginator.page(paginator.num_pages)
    
    contexto = {
        'recetas': recetas_paginadas,
        'total_recetas': total_recetas,
        'recetas_activas': recetas_activas,
        'recetas_inactivas': recetas_inactivas,
        'busqueda': busqueda,
        'estado_filtro': estado_filtro,
        'precio_min': precio_min,
        'precio_max': precio_max,
    }
    
    return render(request, 'recetas/index.html', contexto)


# ==================== CREAR RECETA ====================
def crear_receta(request):
    """
    Crea una nueva receta - Versión simplificada
    """
    # Primero limpiar TODOS los mensajes existentes sin importar el método
    from django.contrib.messages.storage.fallback import FallbackStorage
    from django.contrib.messages.api import get_messages
    
    # Forzar limpieza completa de mensajes
    try:
        # Método 1: Usar get_messages y consumir todos
        storage = get_messages(request)
        list(storage)  # Consume todos los mensajes
        
        # Método 2: Limpiar directamente el storage
        if hasattr(request, '_messages'):
            request._messages._queued_messages = []
            request._messages.used = True
            
        # Método 3: Limpiar desde la sesión
        if 'messages' in request.session:
            del request.session['messages']
            
    except Exception:
        pass  # Ignorar errores de limpieza
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            precio = Decimal(request.POST.get('precio', '0'))
            estado = request.POST.get('estado', 'Activo')
            
            # Validaciones básicas
            if not nombre:
                messages.error(request, "El nombre de la receta es obligatorio")
                return render(request, 'recetas/crear.html', {'titulo': 'Nueva Receta', 'accion': 'Crear'})
            
            if Receta.objects.filter(nombre__iexact=nombre).exists():
                messages.error(request, "Ya existe una receta con ese nombre")
                return render(request, 'recetas/crear.html', {'titulo': 'Nueva Receta', 'accion': 'Crear'})
            
            if precio <= 0:
                messages.error(request, "El precio debe ser mayor que cero")
                return render(request, 'recetas/crear.html', {'titulo': 'Nueva Receta', 'accion': 'Crear'})
            
            # Crear la receta
            receta = Receta.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                estado=estado
            )
            
            messages.success(request, f"Receta '{receta.nombre}' creada correctamente")
            return redirect('recetas:index')
            
        except Exception as e:
            messages.error(request, f"Error al crear la receta: {str(e)}")
            return render(request, 'recetas/crear.html', {'titulo': 'Nueva Receta', 'accion': 'Crear'})
    
    # GET: Formulario limpio sin mensajes
    return render(request, 'recetas/crear.html', {
        'titulo': 'Nueva Receta',
        'accion': 'Crear'
    })


# ==================== EDITAR RECETA ====================
def editar_receta(request, id_rec):
    """
    Equivalente a: actualizar() en recetasBean.java
    Edita una receta existente
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre', '').strip()
            descripcion = request.POST.get('descripcion', '').strip()
            precio = Decimal(request.POST.get('precio', '0'))
            estado = request.POST.get('estado', 'Activo')
            
            # Validaciones
            if not nombre:
                messages.error(request, "El nombre de la receta es obligatorio")
                return redirect('recetas:editar', id_rec=id_rec)
            
            # Validación de duplicado (excluir la receta actual)
            if Receta.objects.filter(nombre__iexact=nombre).exclude(id_rec=id_rec).exists():
                messages.error(request, "Ya existe otra receta con ese nombre")
                return redirect('recetas:editar', id_rec=id_rec)
            
            # Validación de precio
            if precio <= 0:
                messages.error(request, "El precio debe ser mayor que cero")
                return redirect('recetas:editar', id_rec=id_rec)
            
            # Actualizar la receta
            receta.nombre = nombre
            receta.descripcion = descripcion
            receta.precio = precio
            receta.estado = estado
            receta.save()
            
            messages.success(
                request, 
                f"✅ Receta '{receta.nombre}' actualizada correctamente"
            )
            return redirect('recetas:index')
            
        except Exception as e:
            messages.error(request, f"Error al actualizar la receta: {str(e)}")
            return redirect('recetas:editar', id_rec=id_rec)
    
    # GET: Mostrar formulario con datos
    contexto = {
        'receta': receta,
        'titulo': f'Editar: {receta.nombre}',
        'accion': 'Actualizar'
    }
    
    return render(request, 'recetas/editar.html', contexto)


# ==================== ELIMINAR RECETA ====================
def eliminar_receta(request, id_rec):
    """
    Equivalente a: eliminar() en recetasBean.java
    Elimina una receta (con confirmación)
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    if request.method == 'POST':
        nombre = receta.nombre
        
        # Verificar si tiene ingredientes asociados
        ingredientes_count = RecetaInsumo.objects.filter(receta=receta).count()
        
        if ingredientes_count > 0:
            messages.warning(
                request,
                f"⚠️ La receta '{nombre}' tiene {ingredientes_count} ingredientes. "
                f"Se eliminarán también los ingredientes asociados."
            )
        
        try:
            receta.delete()
            messages.success(request, f"✅ Receta '{nombre}' eliminada correctamente")
        except Exception as e:
            messages.error(request, f"Error al eliminar la receta: {str(e)}")
    
    return redirect('recetas:index')


# ==================== DETALLE DE RECETA ====================
def detalle_receta(request, id_rec):
    """
    Muestra el detalle completo de una receta con sus ingredientes
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    # Verificar y actualizar el estado de la receta basado en sus insumos
    if receta.verificar_y_actualizar_estado():
        receta.save()
    
    # Obtener ingredientes de la receta
    ingredientes = RecetaInsumo.objects.filter(
        receta=receta
    ).select_related('insumo').order_by('insumo__nombre')
    
    # Calcular estadísticas
    total_ingredientes = ingredientes.count()
    ingredientes_disponibles = ingredientes.filter(estado='Activo').count()
    ingredientes_agotados = ingredientes.filter(estado='Agotado').count()
    
    # Verificar si se puede producir
    puede_producir, motivo = receta.puede_producirse()
    
    contexto = {
        'receta': receta,
        'ingredientes': ingredientes,
        'total_ingredientes': total_ingredientes,
        'ingredientes_disponibles': ingredientes_disponibles,
        'ingredientes_agotados': ingredientes_agotados,
        'puede_producir': puede_producir,
        'motivo': motivo,
        'costo_produccion': receta.costo_produccion,
        'margen_ganancia': receta.margen_ganancia,
    }
    
    return render(request, 'recetas/detalle.html', contexto)


# ==================== BUSCAR RECETAS ====================
def buscar_recetas(request):
    """
    Equivalente a: buscarPorNombre() en recetasBean.java
    Búsqueda AJAX de recetas
    """
    nombre = request.GET.get('nombre', '').strip()
    
    if not nombre:
        return JsonResponse({'recetas': []})
    
    recetas = Receta.objects.filter(
        nombre__icontains=nombre
    )[:10]  # Limitar a 10 resultados
    
    resultados = []
    for receta in recetas:
        resultados.append({
            'id': receta.id_rec,
            'nombre': receta.nombre,
            'descripcion': receta.descripcion or '',
            'precio': float(receta.precio),
            'precio_formateado': receta.precio_formateado,
            'estado': receta.estado,
            'puede_producir': receta.puede_producirse()[0]
        })
    
    return JsonResponse({'recetas': resultados})


# ==================== EXPORTAR PDF ====================
def exportar_pdf(request):
    """
    Equivalente a: exportarPDF() en recetasBean.java
    Genera reporte PDF de recetas usando ReportLab
    """
    try:
        # Crear respuesta HTTP para PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="Recetas.pdf"'
        
        # Crear documento PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        
        # Estilos
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Centrado
        )
        
        # Contenido del PDF
        contenido = []
        
        # Título
        titulo = Paragraph("Reporte de Recetas - Sistema PAE", title_style)
        contenido.append(titulo)
        contenido.append(Spacer(1, 20))
        
        # Fecha
        fecha = Paragraph(
            f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles['Normal']
        )
        contenido.append(fecha)
        contenido.append(Spacer(1, 20))
        
        # Obtener recetas
        recetas = Receta.objects.all().order_by('nombre')
        
        # Crear tabla
        datos_tabla = [['Nombre', 'Descripción', 'Precio', 'Estado', 'Costo', 'Margen']]
        
        for receta in recetas:
            datos_tabla.append([
                receta.nombre[:30],  # Limitar longitud
                (receta.descripcion or '')[:40],
                receta.precio_formateado,
                receta.estado,
                f"${receta.costo_produccion:,.0f}",
                f"{receta.margen_ganancia:.1f}%"
            ])
        
        # Crear tabla
        tabla = Table(datos_tabla, colWidths=[2*inch, 2.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        
        contenido.append(tabla)
        
        # Estadísticas
        contenido.append(Spacer(1, 20))
        estadisticas = Paragraph(
            f"<b>Total de recetas:</b> {recetas.count()} | "
            f"<b>Activas:</b> {recetas.filter(estado='Activo').count()} | "
            f"<b>Inactivas:</b> {recetas.filter(estado='Inactivo').count()}",
            styles['Normal']
        )
        contenido.append(estadisticas)
        
        # Generar PDF
        doc.build(contenido)
        
        # Obtener contenido del buffer
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
        
    except Exception as e:
        messages.error(request, f"Error generando reporte PDF: {str(e)}")
        return redirect('recetas:index')


# ==================== MIGRAR DESDE EXCEL ====================
def migrar_excel(request):
    """
    Equivalente a: migrar() en recetasBean.java
    Importa recetas desde archivo Excel
    """
    if request.method == 'POST' and request.FILES.get('excel'):
        try:
            archivo = request.FILES['excel']
            
            # Verificar extensión
            if not archivo.name.endswith(('.xlsx', '.xls')):
                messages.error(request, "Por favor sube un archivo Excel válido (.xlsx o .xls)")
                return redirect('recetas:index')
            
            # Leer archivo Excel
            workbook = openpyxl.load_workbook(archivo)
            worksheet = workbook.active
            
            recetas_creadas = 0
            errores = []
            
            # Saltar la primera fila (encabezados)
            for row_num, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
                try:
                    if not row[0]:  # Si no hay nombre, saltar fila
                        continue
                    
                    nombre = str(row[0]).strip()
                    descripcion = str(row[1]).strip() if row[1] else ''
                    precio = Decimal(str(row[2])) if row[2] and str(row[2]).replace('.', '').isdigit() else Decimal('0.00')
                    
                    # Validaciones
                    if not nombre:
                        errores.append(f"Fila {row_num}: Nombre vacío")
                        continue
                    
                    if precio <= 0:
                        errores.append(f"Fila {row_num}: Precio inválido ({precio})")
                        precio = Decimal('0.00')
                    
                    # Verificar si ya existe
                    if Receta.objects.filter(nombre__iexact=nombre).exists():
                        errores.append(f"Fila {row_num}: Receta '{nombre}' ya existe")
                        continue
                    
                    # Crear receta
                    Receta.objects.create(
                        nombre=nombre,
                        descripcion=descripcion,
                        precio=precio,
                        estado='Activo'
                    )
                    
                    recetas_creadas += 1
                    
                except Exception as e:
                    errores.append(f"Fila {row_num}: Error procesando - {str(e)}")
            
            # Mensajes de resultado
            if recetas_creadas > 0:
                messages.success(
                    request, 
                    f"✅ {recetas_creadas} recetas importadas correctamente"
                )
            
            if errores:
                mensaje_errores = "Errores encontrados:\n" + "\n".join(errores[:10])
                if len(errores) > 10:
                    mensaje_errores += f"\n... y {len(errores) - 10} errores más"
                messages.warning(request, mensaje_errores)
            
        except Exception as e:
            messages.error(request, f"Error procesando archivo Excel: {str(e)}")
    
    return redirect('recetas:index')


# ==================== CAMBIAR ESTADO ====================
def cambiar_estado(request, id_rec):
    """
    Cambia el estado de una receta (Activo/Inactivo)
    """
    if request.method == 'POST':
        receta = get_object_or_404(Receta, id_rec=id_rec)
        
        nuevo_estado = 'Inactivo' if receta.estado == 'Activo' else 'Activo'
        receta.estado = nuevo_estado
        receta.save()
        
        messages.success(
            request,
            f"Estado de '{receta.nombre}' cambiado a {nuevo_estado}"
        )
    
    return redirect('recetas:index')


# ==================== GESTIONAR INGREDIENTES ====================
def gestionar_ingredientes(request, id_rec):
    """
    Equivalente a: irAGestionarInsumos() en recetasBean.java
    Redirige a la gestión de ingredientes de una receta específica
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    # Guardar receta en sesión para usar en receta_insumos
    request.session['receta_seleccionada'] = {
        'id': receta.id_rec,
        'nombre': receta.nombre
    }
    
    return redirect('recetas:ingredientes', id_rec=id_rec)


# ==================== GESTIÓN DE INGREDIENTES ====================

def listar_ingredientes(request, id_rec):
    """
    Equivalente a: listar() en receta_insumosBean.java
    Lista ingredientes de una receta específica
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    # Sincronizar estados (equivalente a sincronizarEstadosPorInsumo)
    ingredientes = RecetaInsumo.objects.filter(receta=receta).select_related('insumo')
    
    for ingrediente in ingredientes:
        ingrediente.verificar_disponibilidad()
        ingrediente.save()
    
    # Obtener ingredientes actualizados
    ingredientes = RecetaInsumo.objects.filter(
        receta=receta
    ).select_related('insumo').order_by('insumo__nombre')
    
    # Estadísticas
    total_ingredientes = ingredientes.count()
    ingredientes_activos = ingredientes.filter(estado='Activo').count()
    ingredientes_agotados = ingredientes.filter(estado='Agotado').count()
    
    # Obtener lista de insumos disponibles para agregar
    insumos_disponibles = Insumo.objects.filter(
        estado='Activo'
    ).exclude(
        id_ins__in=ingredientes.values_list('insumo__id_ins', flat=True)
    ).order_by('nombre')
    
    contexto = {
        'receta': receta,
        'ingredientes': ingredientes,
        'total_ingredientes': total_ingredientes,
        'ingredientes_activos': ingredientes_activos,
        'ingredientes_agotados': ingredientes_agotados,
        'insumos_disponibles': insumos_disponibles,
        'costo_total': receta.costo_produccion,
        'margen_ganancia': receta.margen_ganancia,
    }
    
    return render(request, 'recetas/ingredientes.html', contexto)


def agregar_ingrediente(request, id_rec):
    """
    Equivalente a: agregar() en receta_insumosBean.java
    Agrega un ingrediente a una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    if request.method == 'POST':
        try:
            # DEBUG: Mostrar todos los datos recibidos
            print(f"\n=== DEBUG AGREGAR INGREDIENTE ===")
            print(f"Receta ID: {id_rec}")
            print(f"Método: {request.method}")
            print(f"POST data completo: {dict(request.POST)}")
            print(f"Headers: {dict(request.headers)}")
            
            # Obtener datos del formulario con validación
            # Como hay múltiples campos insumo_id, obtener todos los valores y filtrar
            insumo_ids = request.POST.getlist('insumo_id')
            print(f"Todos los insumo_id recibidos: {insumo_ids}")
            
            # Filtrar valores vacíos y tomar el primero válido
            insumo_id_raw = ''
            for id_val in insumo_ids:
                if id_val and id_val.strip():
                    insumo_id_raw = id_val.strip()
                    break
            
            cantidad_raw = request.POST.get('cantidad', '')
            
            print(f"insumo_id_raw final: '{insumo_id_raw}' (tipo: {type(insumo_id_raw)})")
            print(f"cantidad_raw: '{cantidad_raw}' (tipo: {type(cantidad_raw)})")
            
            # Validar que no estén vacíos
            if not insumo_id_raw or insumo_id_raw.strip() == '':
                error_msg = "Debe seleccionar un insumo válido"
                print(f"❌ ERROR: {error_msg}")
                print(f"insumo_id_raw está vacío después del filtrado")
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            if not cantidad_raw or cantidad_raw.strip() == '':
                error_msg = "Debe ingresar una cantidad válida"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            # Convertir a tipos correctos
            id_ins = int(insumo_id_raw)
            cantidad = Decimal(cantidad_raw)
            
            # Validaciones de valores
            if id_ins <= 0:
                error_msg = "Debe seleccionar un insumo"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            if cantidad <= 0:
                error_msg = "La cantidad debe ser mayor que cero"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            from modelos.insumos.models import Insumo
            insumo = get_object_or_404(Insumo, id_ins=id_ins)
            
            # Verificar si ya existe la relación
            if RecetaInsumo.objects.filter(receta=receta, insumo=insumo).exists():
                error_msg = f"El insumo '{insumo.nombre}' ya está asignado a esta receta"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.warning(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            # Crear el ingrediente usando SQL directo
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO receta_insumos (id_rec, id_ins, cantidad, unidad, estado) VALUES (%s, %s, %s, %s, %s)",
                    [receta.id_rec, insumo.id_ins, cantidad, insumo.unidad_medida, 'Activo']
                )
            
            # Si es una petición AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f"Ingrediente '{insumo.nombre}' agregado correctamente"
                })
            
            messages.success(
                request,
                f"✅ Ingrediente '{insumo.nombre}' agregado correctamente"
            )
            
        except Exception as e:
            # Si es una petición AJAX, retornar error JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': f"Error al agregar ingrediente: {str(e)}"
                })
            messages.error(request, f"Error al agregar ingrediente: {str(e)}")
    
    return redirect('recetas:ingredientes', id_rec=id_rec)


def editar_ingrediente(request, id_rec, id_rec_ins):
    """
    Equivalente a: actualizar() en receta_insumosBean.java
    Edita un ingrediente de una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    ingrediente = get_object_or_404(RecetaInsumo, id_rec_ins=id_rec_ins, receta=receta)
    
    if request.method == 'POST':
        try:
            # Obtener datos del formulario con los nombres correctos
            cantidad_raw = request.POST.get('cantidad', '')
            
            # Validar que no esté vacío
            if not cantidad_raw or cantidad_raw.strip() == '':
                error_msg = "Debe ingresar una cantidad válida"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            cantidad = Decimal(cantidad_raw)
            
            # Validaciones de valores
            if cantidad <= 0:
                error_msg = "La cantidad debe ser mayor que cero"
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    from django.http import JsonResponse
                    return JsonResponse({'success': False, 'error': error_msg})
                messages.error(request, error_msg)
                return redirect('recetas:ingredientes', id_rec=id_rec)
            
            # Actualizar ingrediente usando SQL directo para consistencia
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(
                    "UPDATE receta_insumos SET cantidad = %s, unidad = %s WHERE id_rec_ins = %s",
                    [cantidad, ingrediente.insumo.unidad_medida, id_rec_ins]
                )
            
            # Si es petición AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f"Ingrediente '{ingrediente.insumo.nombre}' actualizado correctamente"
                })
            
            messages.success(
                request,
                f"✅ Ingrediente '{ingrediente.insumo.nombre}' actualizado correctamente"
            )
            
        except Exception as e:
            # Si es petición AJAX, retornar error JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': f"Error al actualizar ingrediente: {str(e)}"
                })
            messages.error(request, f"Error al actualizar ingrediente: {str(e)}")
    
    return redirect('recetas:ingredientes', id_rec=id_rec)


def eliminar_ingrediente(request, id_rec, id_rec_ins):
    """
    Equivalente a: eliminar() en receta_insumosBean.java
    Elimina un ingrediente de una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    ingrediente = get_object_or_404(RecetaInsumo, id_rec_ins=id_rec_ins, receta=receta)
    
    if request.method == 'POST':
        nombre_insumo = ingrediente.insumo.nombre
        
        try:
            ingrediente.delete()
            
            # Si es petición AJAX, retornar JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': True,
                    'message': f"Ingrediente '{nombre_insumo}' eliminado correctamente"
                })
            
            messages.success(
                request,
                f"✅ Ingrediente '{nombre_insumo}' eliminado correctamente"
            )
        except Exception as e:
            # Si es petición AJAX, retornar error JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({
                    'success': False,
                    'error': f"Error al eliminar ingrediente: {str(e)}"
                })
            messages.error(request, f"Error al eliminar ingrediente: {str(e)}")
    
    return redirect('recetas:ingredientes', id_rec=id_rec)


def obtener_ingrediente(request, id_rec_ins):
    """
    AJAX: Obtiene datos de un ingrediente para edición
    """
    try:
        ingrediente = get_object_or_404(RecetaInsumo, id_rec_ins=id_rec_ins)
        
        datos = {
            'success': True,
            'id_rec_ins': ingrediente.id_rec_ins,
            'insumo_id': ingrediente.insumo.id_ins,
            'nombre_insumo': ingrediente.insumo.nombre,
            'cantidad': float(ingrediente.cantidad),
            'unidad': ingrediente.insumo.unidad_medida,
        }
        
        return JsonResponse(datos)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def actualizar_unidad_ajax(request):
    """
    Equivalente a: actualizarUnidad() en receta_insumosBean.java
    AJAX: Actualiza la unidad de medida al seleccionar un insumo
    """
    if request.method == 'GET':
        id_ins = request.GET.get('id_ins', 0)
        
        try:
            id_ins = int(id_ins)
            if id_ins > 0:
                insumo = get_object_or_404(Insumo, id_ins=id_ins)
                return JsonResponse({
                    'unidad': insumo.unidad_medida,
                    'nombre': insumo.nombre,
                    'stock_actual': float(insumo.stock_actual),
                    'precio_unitario': float(insumo.precio_unitario) if hasattr(insumo, 'precio_unitario') else 0.0
                })
            else:
                return JsonResponse({'unidad': ''})
                
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)


def sincronizar_estados(request, id_rec):
    """
    Equivalente a: sincronizarEstadosPorInsumo() en receta_insumosBean.java
    Sincroniza los estados de todos los ingredientes de una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    ingredientes = RecetaInsumo.objects.filter(receta=receta)
    actualizados = 0
    
    for ingrediente in ingredientes:
        estado_anterior = ingrediente.estado
        ingrediente.verificar_disponibilidad()
        
        if estado_anterior != ingrediente.estado:
            ingrediente.save()
            actualizados += 1
    
    if actualizados > 0:
        messages.info(
            request,
            f"🔄 {actualizados} ingredientes actualizaron su estado"
        )
    else:
        messages.info(request, "✅ Todos los estados están sincronizados")
    
    return redirect('recetas:ingredientes', id_rec=id_rec)


def verificar_disponibilidad_receta(request, id_rec):
    """
    AJAX: Verifica si una receta puede producirse
    """
    try:
        receta = get_object_or_404(Receta, id_rec=id_rec)
        puede_producir, motivo = receta.puede_producirse()
        
        # Obtener detalles de disponibilidad por ingrediente
        ingredientes_estado = []
        for ingrediente in receta.ingredientes.all():
            ingredientes_estado.append({
                'nombre': ingrediente.insumo.nombre,
                'cantidad_necesaria': float(ingrediente.cantidad),
                'stock_disponible': float(ingrediente.insumo.stock_actual),
                'disponible': ingrediente.disponible,
                'porcentaje': ingrediente.porcentaje_disponible
            })
        
        return JsonResponse({
            'puede_producir': puede_producir,
            'motivo': motivo,
            'costo_produccion': float(receta.costo_produccion),
            'margen_ganancia': float(receta.margen_ganancia),
            'ingredientes': ingredientes_estado
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ==================== VISTAS ADICIONALES ====================

def detalle_receta(request, id_rec):
    """
    Muestra los detalles completos de una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    ingredientes = receta.ingredientes.select_related('insumo')
    
    # Calcular estadísticas básicas
    costo_produccion = receta.costo_produccion
    
    context = {
        'receta': receta,
        'ingredientes': ingredientes,
        'costo_produccion': costo_produccion,
    }
    
    return render(request, 'recetas/detalle.html', context)


def gestionar_ingredientes(request, id_rec):
    """
    Vista para gestionar los ingredientes de una receta
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    
    # Actualizar estados de ingredientes automáticamente
    try:
        actualizados = actualizar_estados_ingredientes()
        if actualizados > 0:
            print(f"Se actualizaron {actualizados} estados de ingredientes")
    except Exception as e:
        print(f"Error actualizando estados: {e}")
    
    ingredientes = receta.ingredientes.select_related('insumo')
    insumos_disponibles = Insumo.objects.filter(estado='Activo').order_by('nombre')
    
    # DEBUG: Mostrar insumos disponibles
    print(f"\n=== DEBUG INGREDIENTES VIEW ===")
    print(f"Receta: {receta.nombre}")
    print(f"Total insumos disponibles: {insumos_disponibles.count()}")
    for insumo in insumos_disponibles[:5]:  # Mostrar solo los primeros 5
        print(f"  - {insumo.nombre} (ID: {insumo.id_ins}, Estado: {insumo.estado})")
    if insumos_disponibles.count() > 5:
        print(f"  ... y {insumos_disponibles.count() - 5} más")
    
    # Calcular estadísticas básicas
    costo_total = sum(ing.costo_total for ing in ingredientes)
    
    # Verificar disponibilidad de la receta
    puede_producirse, razon = receta.puede_producirse()
    
    context = {
        'receta': receta,
        'ingredientes': ingredientes,
        'insumos_disponibles': insumos_disponibles,
        'costo_total': costo_total,
        'puede_producirse': puede_producirse,
        'razon_no_disponible': razon if not puede_producirse else None,
    }
    
    return render(request, 'recetas/ingredientes.html', context)


def duplicar_receta(request, id_rec):
    """
    Duplica una receta existente
    """
    receta_original = get_object_or_404(Receta, id_rec=id_rec)
    
    try:
        # Crear nueva receta
        nueva_receta = Receta.objects.create(
            nombre=f"{receta_original.nombre} (Copia)",
            descripcion=receta_original.descripcion,
            precio=receta_original.precio,
            estado='Inactivo'  # Nueva receta inicia inactiva
        )
        
        # Duplicar ingredientes
        for ingrediente in receta_original.ingredientes.all():
            RecetaInsumo.objects.create(
                receta=nueva_receta,
                insumo=ingrediente.insumo,
                cantidad=ingrediente.cantidad
            )
        
        messages.success(request, f'Receta "{nueva_receta.nombre}" duplicada exitosamente.')
        return redirect('recetas:editar', id_rec=nueva_receta.id_rec)
        
    except Exception as e:
        messages.error(request, f'Error al duplicar la receta: {str(e)}')
        return redirect('recetas:detalle', id_rec=id_rec)


def exportar_pdf_receta(request, id_rec):
    """
    Exporta una receta individual a PDF
    """
    receta = get_object_or_404(Receta, id_rec=id_rec)
    ingredientes = receta.ingredientes.select_related('insumo')
    
    # Crear respuesta HTTP
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receta_{receta.nombre.replace(" ", "_")}.pdf"'
    
    # Crear documento PDF
    doc = SimpleDocTemplate(response, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    story.append(Paragraph(f"Receta: {receta.nombre}", title_style))
    story.append(Spacer(1, 20))
    
    # Información básica
    info_data = [
        ["Información General", ""],
        ["Nombre:", receta.nombre],
        ["Descripción:", receta.descripcion or "Sin descripción"],
        ["Precio de Venta:", f"${receta.precio}"],
        ["Estado:", receta.estado],
        ["Fecha Creación:", receta.fecha_creacion.strftime("%d/%m/%Y")],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 30))
    
    # Ingredientes
    if ingredientes:
        story.append(Paragraph("Ingredientes", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        # Tabla de ingredientes
        ingredientes_data = [["Insumo", "Cantidad", "Unidad", "Precio Unit.", "Costo Total"]]
        
        costo_total = Decimal('0')
        for ing in ingredientes:
            ingredientes_data.append([
                ing.insumo.nombre,
                f"{ing.cantidad}",
                ing.insumo.unidad_medida,
                f"${ing.insumo.precio_unitario}",
                f"${ing.costo_total}"
            ])
            costo_total += ing.costo_total
        
        # Fila de total
        ingredientes_data.append(["", "", "", "TOTAL:", f"${costo_total}"])
        
        ingredientes_table = Table(ingredientes_data)
        ingredientes_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(ingredientes_table)
        story.append(Spacer(1, 20))
        
        # Análisis financiero
        ganancia = receta.precio - costo_total
        margen = (ganancia / receta.precio * 100) if receta.precio > 0 else 0
        
        story.append(Paragraph("Análisis Financiero", styles['Heading2']))
        story.append(Spacer(1, 12))
        
        financiero_data = [
            ["Concepto", "Valor"],
            ["Precio de Venta", f"${receta.precio}"],
            ["Costo de Producción", f"${costo_total}"],
            ["Ganancia Neta", f"${ganancia}"],
            ["Margen de Ganancia", f"{margen:.1f}%"],
        ]
        
        financiero_table = Table(financiero_data, colWidths=[3*inch, 2*inch])
        financiero_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(financiero_table)
    
    # Generar PDF
    doc.build(story)
    return response


def obtener_datos_ingrediente(request, id_rec_ins):
    """
    AJAX: Obtiene los datos de un ingrediente específico para edición
    """
    try:
        ingrediente = get_object_or_404(RecetaInsumo, id_rec_ins=id_rec_ins)
        
        return JsonResponse({
            'success': True,
            'insumo_id': ingrediente.insumo.id_ins,
            'cantidad': float(ingrediente.cantidad),
            'insumo_nombre': ingrediente.insumo.nombre,
            'precio_unitario': float(ingrediente.insumo.precio_unitario),
            'unidad_medida': ingrediente.insumo.unidad_medida,
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


def eliminar_ingrediente_ajax(request, id_rec_ins):
    """
    AJAX: Elimina un ingrediente de una receta
    """
    if request.method == 'POST':
        try:
            ingrediente = get_object_or_404(RecetaInsumo, id_rec_ins=id_rec_ins)
            ingrediente.delete()
            
            return JsonResponse({
                'success': True,
                'message': 'Ingrediente eliminado exitosamente'
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ==================== SINCRONIZACIÓN Y MANTENIMIENTO ====================

def sincronizar_todas_recetas(request):
    """
    Sincroniza el estado de todas las recetas con sus insumos
    """
    if request.method == 'POST':
        try:
            from .utils import sincronizar_todas_las_recetas
            resultado = sincronizar_todas_las_recetas()
            
            mensaje = f"✅ Sincronización completada:\n"
            mensaje += f"• {resultado['ingredientes_actualizados']} ingredientes actualizados\n"
            mensaje += f"• {resultado['recetas_desactivadas']} recetas desactivadas\n"
            mensaje += f"• {resultado['recetas_reactivadas']} recetas reactivadas"
            
            if resultado['recetas_desactivadas'] > 0:
                mensaje += f"\n\n🔴 Recetas desactivadas: {', '.join(resultado['recetas_desactivadas_nombres'])}"
            
            if resultado['recetas_reactivadas'] > 0:
                mensaje += f"\n\n🟢 Recetas reactivadas: {', '.join(resultado['recetas_reactivadas_nombres'])}"
            
            messages.success(request, mensaje)
            
        except Exception as e:
            messages.error(request, f"❌ Error durante la sincronización: {str(e)}")
    
    return redirect('recetas:index')


def reporte_disponibilidad(request):
    """
    Genera un reporte de disponibilidad de recetas
    """
    try:
        from .utils import generar_reporte_recetas_afectadas
        reporte = generar_reporte_recetas_afectadas()
        
        context = {
            'reporte': reporte,
            'fecha_reporte': datetime.now()
        }
        
        return render(request, 'recetas/reporte_disponibilidad.html', context)
        
    except Exception as e:
        messages.error(request, f"❌ Error generando el reporte: {str(e)}")
        return redirect('recetas:index')
