from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q, Sum, Count, Avg, F, Min, Max
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.db import transaction
from decimal import Decimal
import json
from datetime import datetime, date

from .models import Venta, Pago, VentaReceta, VentaProduccion
# DetalleVenta deshabilitado - tabla no existe
from modelos.clientes.models import Cliente
from modelos.usuarios.models import Usuario
from modelos.recetas.models import Receta, RecetaInsumo
from modelos.produccion.models import Produccion


# @login_required  # Temporalmente comentado para pruebas
def listar_ventas(request):
    """
    Vista principal para listar ventas con filtros avanzados
    Equivalente a: ventasBean.java - filtrarVentas()
    """
    # Obtener parámetros de filtro
    filtro_id = request.GET.get('filtro_id')
    filtro_tipo = request.GET.get('filtro_tipo')
    filtro_cliente = request.GET.get('filtro_cliente')
    filtro_usuario = request.GET.get('filtro_usuario')
    filtro_asignado = request.GET.get('filtro_asignado')
    filtro_estado = request.GET.get('filtro_estado')
    filtro_total_min = request.GET.get('filtro_total_min')
    filtro_total_max = request.GET.get('filtro_total_max')
    filtro_fecha_desde = request.GET.get('filtro_fecha_desde')
    filtro_fecha_hasta = request.GET.get('filtro_fecha_hasta')
    
    # Construir queryset base - temporalmente vacío para pruebas
    try:
        ventas = Venta.objects.all().select_related(
            'cliente', 'usuario', 'usuario_asignado'
        )
    except:
        # Si hay problemas con la base de datos, mostrar lista vacía
        ventas = Venta.objects.none()
    
    # Aplicar filtros
    if filtro_id:
        try:
            ventas = ventas.filter(id_ven=int(filtro_id))
        except ValueError:
            pass
    
    if filtro_tipo:
        ventas = ventas.filter(tipo__icontains=filtro_tipo)
    
    if filtro_cliente:
        ventas = ventas.filter(
            Q(cliente__nombre__icontains=filtro_cliente) |
            Q(cliente__apellidos__icontains=filtro_cliente) |
            Q(cliente__nit__icontains=filtro_cliente)
        )
    
    if filtro_usuario:
        ventas = ventas.filter(
            Q(usuario__nombres__icontains=filtro_usuario) |
            Q(usuario__apellidos__icontains=filtro_usuario)
        )
    
    if filtro_asignado:
        ventas = ventas.filter(
            Q(usuario_asignado__nombres__icontains=filtro_asignado) |
            Q(usuario_asignado__apellidos__icontains=filtro_asignado)
        )
    
    if filtro_estado:
        ventas = ventas.filter(estado__icontains=filtro_estado)
    
    if filtro_total_min:
        try:
            ventas = ventas.filter(total__gte=Decimal(filtro_total_min))
        except (ValueError, TypeError):
            pass
    
    if filtro_total_max:
        try:
            ventas = ventas.filter(total__lte=Decimal(filtro_total_max))
        except (ValueError, TypeError):
            pass
    
    if filtro_fecha_desde:
        try:
            fecha_desde = datetime.strptime(filtro_fecha_desde, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date__gte=fecha_desde)
        except ValueError:
            pass
    
    if filtro_fecha_hasta:
        try:
            fecha_hasta = datetime.strptime(filtro_fecha_hasta, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__date__lte=fecha_hasta)
        except ValueError:
            pass
    
    # Ordenar por fecha descendente
    ventas = ventas.order_by('-fecha')
    
    # Calcular estadísticas
    estadisticas = ventas.aggregate(
        total_ventas=Count('id_ven'),
        total_ingresos=Sum('total'),
        promedio_venta=Avg('total'),
    )

    # Ventas en estados ya avanzados (Procesando, Pago completo, Completada)
    ventas_buenas = ventas.filter(estado__in=['Procesando', 'Pago completo', 'Completada'])
    ventas_buenas_count = ventas_buenas.count()
    top_ventas = ventas_buenas.order_by('-total')[:4]
    # Conteos individuales por estado solicitados
    count_procesando = ventas.filter(estado='Procesando').count()
    count_pago_completo = ventas.filter(estado='Pago completo').count()
    count_completada = ventas.filter(estado='Completada').count()
    
    # Paginación
    paginator = Paginator(ventas, 20)
    page_number = request.GET.get('page')
    ventas_paginadas = paginator.get_page(page_number)
    
    # Obtener listas para filtros - temporalmente vacías para pruebas
    try:
        clientes = Cliente.objects.all().order_by('nombre')
        usuarios = Usuario.objects.filter(estado='A').order_by('nombres')
        usuarios_ventas = usuarios.filter(rol__in=['A', 'EV'])
        usuarios_asignados = usuarios.filter(rol__in=['A', 'EV', 'EP'])
    except:
        # Si hay problemas con la base de datos, usar listas vacías
        clientes = []
        usuarios = []
        usuarios_ventas = []
        usuarios_asignados = []
    
    context = {
        'ventas': ventas_paginadas,
        'estadisticas': estadisticas,
        'ventas_buenas_count': ventas_buenas_count,
        'top_ventas': top_ventas,
        'count_procesando': count_procesando,
        'count_pago_completo': count_pago_completo,
        'count_completada': count_completada,
        'clientes': clientes,
        'usuarios': usuarios_ventas,
        'usuarios_asignados': usuarios_asignados,
        # Mantener filtros en el contexto para el formulario
        'filtros': {
            'filtro_id': filtro_id,
            'filtro_tipo': filtro_tipo,
            'filtro_cliente': filtro_cliente,
            'filtro_usuario': filtro_usuario,
            'filtro_asignado': filtro_asignado,
            'filtro_estado': filtro_estado,
            'filtro_total_min': filtro_total_min,
            'filtro_total_max': filtro_total_max,
            'filtro_fecha_desde': filtro_fecha_desde,
            'filtro_fecha_hasta': filtro_fecha_hasta,
        }
    }
    
    return render(request, 'ventas/index.html', context)


# @login_required  # Temporalmente comentado para pruebas
def nueva_venta(request):
    """
    Vista para crear una nueva venta
    """
    if request.method == 'POST':
        return procesar_nueva_venta(request)
    
    # Obtener datos necesarios para el formulario
    clientes = Cliente.objects.all().order_by('nombre')
    # Empleados activos con conteo de producciones aceptadas / esperando insumos (no finalizadas)
    usuarios_ep = Usuario.objects.filter(estado='A', rol='EP').annotate(
        producciones_activas=Count(
            'producciones_asignadas',
            filter=Q(producciones_asignadas__estado__in=['Aceptada', 'Esperando insumos'])
        )
    )
    empleado_auto = usuarios_ep.order_by('producciones_activas', 'id_usu').first()
    empleado_auto_id = empleado_auto.id_usu if empleado_auto else None
    recetas = Receta.objects.filter(estado='Activo').order_by('nombre')

    context = {
        'clientes': clientes,
        'usuarios_ep': usuarios_ep.order_by('nombres'),
        'empleado_auto_id': empleado_auto_id,
        'recetas': recetas,
        'usuario_actual': request.user,
    }
    
    return render(request, 'ventas/nueva.html', context)


@transaction.atomic
def procesar_nueva_venta(request):
    """
    Procesa la creación de una nueva venta
    Equivalente a: ventasBean.java - guardarVenta()
    """
    if request.method != 'POST':
        return redirect('ventas:nueva')
    
    try:
        # Obtener datos del formulario
        cliente_id = request.POST.get('cliente_id') or request.POST.get('id_cliente')
        usuario_asignado_id = request.POST.get('usuario_id') or request.POST.get('id_asignado')
        observaciones = request.POST.get('observaciones', '')
        nuevo_cliente = request.POST.get('nuevo_cliente')
        
        if not request.POST:
            print("ERROR: No hay datos POST")
            messages.error(request, 'No se recibieron datos del formulario')
            return redirect('ventas:nueva')
        
        print("PASO 2: Procesando cliente...")
        
        # Manejar cliente nuevo o existente
        if nuevo_cliente:
            print("DEBUG - Creando nuevo cliente...")
            # Crear nuevo cliente
            cliente_nombre = request.POST.get('cliente_nombre')
            cliente_telefono = request.POST.get('cliente_telefono', '')
            cliente_correo = request.POST.get('cliente_correo', '')
            cliente_nit = request.POST.get('cliente_nit')
            
            print(f"DEBUG - Datos nuevo cliente: nombre={cliente_nombre}, nit={cliente_nit}")
            
            if not cliente_nombre or not cliente_nit:
                print("ERROR - Faltan datos del nuevo cliente")
                messages.error(request, 'Nombre y NIT son obligatorios para el nuevo cliente')
                return redirect('ventas:nueva')
            
            # Verificar que no exista un cliente con el mismo NIT
            if Cliente.objects.filter(nit=cliente_nit).exists():
                messages.error(request, f'Ya existe un cliente con el NIT {cliente_nit}')
                return redirect('ventas:nueva')
            
            # Crear el cliente
            try:
                cliente = Cliente.objects.create(
                    nombre=cliente_nombre,
                    telefono=cliente_telefono or '0000000000',
                    correo=cliente_correo or 'cliente@ejemplo.com',
                    nit=cliente_nit
                )
            except Exception as e:
                messages.error(request, f'Error al crear el cliente: {str(e)}')
                return redirect('ventas:nueva')
        else:
            print("DEBUG - Validando cliente existente...")
            # Validar cliente existente
            if not cliente_id:
                print("ERROR - No se seleccionó cliente")
                messages.error(request, 'Debe seleccionar un cliente existente')
                return redirect('ventas:nueva')
            
            try:
                cliente = Cliente.objects.get(id_Cliente=cliente_id)
                print(f"DEBUG - Cliente encontrado: {cliente.nombre} (ID: {cliente.id_Cliente})")
            except Cliente.DoesNotExist:
                print(f"ERROR - Cliente {cliente_id} no existe")
                messages.error(request, f'El cliente con ID {cliente_id} no existe')
                return redirect('ventas:nueva')
            except Exception as e:
                print(f"ERROR - Error al buscar cliente: {e}")
                messages.error(request, f'Error al buscar cliente: {str(e)}')
                return redirect('ventas:nueva')
        
        print("PASO 3: Validando usuario asignado...")
        
        # Validar / auto-asignar usuario de producción
        if not usuario_asignado_id:
            print("INFO - No se seleccionó usuario asignado, aplicando auto-asignación...")
            auto_qs = Usuario.objects.filter(estado='A', rol='EP').annotate(
                producciones_activas=Count(
                    'producciones_asignadas',
                    filter=Q(producciones_asignadas__estado__in=['Aceptada', 'Esperando insumos'])
                )
            ).order_by('producciones_activas', 'id_usu')
            usuario_asignado = auto_qs.first()
            if not usuario_asignado:
                messages.error(request, 'No hay empleados de producción activos disponibles')
                return redirect('ventas:nueva')
            messages.info(request, f'Empleado asignado automáticamente: {usuario_asignado.nombres} {usuario_asignado.apellidos}')
            print(f"DEBUG - Auto-asignado empleado: {usuario_asignado.id_usu}")
        else:
            try:
                usuario_asignado = get_object_or_404(Usuario, id_usu=usuario_asignado_id)
                print(f"DEBUG - Usuario asignado: {usuario_asignado.nombres} (ID: {usuario_asignado.id_usu})")
            except Exception as e:
                print(f"ERROR - Error al buscar usuario asignado: {e}")
                messages.error(request, f'Error al buscar usuario asignado: {str(e)}')
                return redirect('ventas:nueva')
        
        # Obtener usuario actual de la sesión
        usuario_actual_id = request.session.get('usuario_id')
        print(f"DEBUG - Session usuario_id: {usuario_actual_id}")
        print(f"DEBUG - Session keys: {list(request.session.keys())}")
        
        if not usuario_actual_id:
            # Temporal: usar el primer usuario administrativo disponible
            try:
                usuario_actual = Usuario.objects.filter(estado='A').first()
                if not usuario_actual:
                    messages.error(request, 'No hay usuarios activos en el sistema')
                    return redirect('ventas:nueva')
                print(f"DEBUG - Usando usuario temporal: {usuario_actual.id_usu}")
                messages.warning(request, f'Usando usuario temporal: {usuario_actual.nombres}')
            except Exception as e:
                messages.error(request, f'Error al obtener usuario: {str(e)}')
                return redirect('ventas:nueva')
        else:
            try:
                usuario_actual = get_object_or_404(Usuario, id_usu=usuario_actual_id)
            except Exception as e:
                messages.error(request, f'Usuario de sesión no válido: {str(e)}')
                return redirect('ventas:nueva')
        
        print("PASO 4: Creando la venta...")
        print(f"DEBUG - Cliente: {cliente}")
        print(f"DEBUG - Usuario actual: {usuario_actual}")
        print(f"DEBUG - Usuario asignado: {usuario_asignado}")
        print(f"DEBUG - Observaciones: {observaciones}")
        
        # Crear la venta
        try:
            venta = Venta.objects.create(
                cliente=cliente,
                usuario=usuario_actual,  # Usuario que registra
                usuario_asignado=usuario_asignado,
                estado='Pago pendiente',
                fecha=timezone.now(),
                observaciones=observaciones,
                total=Decimal('0.00')
            )
            print(f"DEBUG - Venta creada exitosamente con ID: {venta.id_ven}")
        except Exception as e:
            print(f"ERROR - Error al crear venta: {e}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            messages.error(request, f'Error al crear la venta: {str(e)}')
            return redirect('ventas:nueva')
        
        print("PASO 5: Procesando detalles de venta...")
        
        # Procesar detalles de venta desde la tabla temporal en JavaScript
        detalles_json = request.POST.get('detalles_venta', '[]')
        print(f"DEBUG - JSON detalles recibido: {detalles_json}")
        
        try:
            detalles = json.loads(detalles_json)
            print(f"DEBUG - Detalles parseados: {detalles}")
        except json.JSONDecodeError as e:
            print(f"ERROR - Error al parsear JSON: {e}")
            detalles = []
        
        total_venta = Decimal('0.00')
        print(f"DEBUG - Número de detalles a procesar: {len(detalles)}")
        
        for detalle_data in detalles:
            receta_id = detalle_data.get('receta_id')
            cantidad = int(detalle_data.get('cantidad', 0))
            precio_unitario = Decimal(str(detalle_data.get('precio_unitario') or detalle_data.get('precio', '0.00')))
            print(f"DEBUG - Precio extraído: {precio_unitario} de datos: {detalle_data}")
            
            if receta_id and cantidad > 0:
                receta = get_object_or_404(Receta, id_rec=receta_id)
                
                # Calcular subtotal
                subtotal = cantidad * precio_unitario
                
                # Crear entrada en VentaReceta para trazabilidad
                VentaReceta.objects.create(
                    venta=venta,
                    receta=receta,
                    cantidad=cantidad,
                    precio=precio_unitario,
                    subtotal=subtotal
                )
                
                # Sumar al total de la venta
                total_venta += subtotal
        
        # Actualizar total de la venta
        venta.total = total_venta
        venta.save()
        
        # Si el total es 0, mostrar advertencia
        if total_venta == 0:
            messages.warning(request, 'La venta fue creada sin productos. Recuerde agregar productos.')
        
        print("PASO 6: Finalizando proceso...")
        print(f"SUCCESS - Venta creada exitosamente: ID={venta.id_ven}, Total=${total_venta}")
        print(f"SUCCESS - Detalles procesados: {len(detalles)}")
        print(f"SUCCESS - Cliente: {cliente.nombre}, Usuario: {usuario_actual.nombres}")
        print("="*50)
        print("PROCESO COMPLETADO EXITOSAMENTE")
        print("="*50)
        
        messages.success(request, f'¡Venta #{venta.id_ven} registrada exitosamente! Total: ${total_venta}')
        # Temporal: redirect a la lista de ventas en lugar del detalle
        return redirect('ventas:listar')
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR COMPLETO: {error_details}")
        messages.error(request, f'Error al crear la venta: {str(e)}')
        messages.error(request, 'Revise la consola para más detalles del error')
        return redirect('ventas:nueva')


# @login_required  # Temporalmente comentado para pruebas
def detalle_venta(request, venta_id):
    """
    Vista para mostrar el detalle completo de una venta
    Equivalente a: ventasBean.java - verDetalleVenta()
    """
    venta = get_object_or_404(Venta, id_ven=venta_id)
    
    # Obtener recetas asociadas a la venta (VentaReceta)
    recetas_venta = venta.recetas_asociadas.select_related('receta').all()
    
    # Obtener pagos de la venta
    pagos = Pago.objects.filter(venta=venta).order_by('-fecha_pago')
    
    # Calcular información de pagos
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    saldo_pendiente = venta.total - total_pagado
    
    # Obtener producciones asociadas (si aplica)
    # producciones = VentaProduccion.objects.filter(venta=venta).select_related('produccion')
    producciones = []  # Temporalmente deshabilitado
    
    # Obtener historial de cambios de estado (si existe un modelo de auditoría)
    # historial_estados = []  # Implementar si se requiere
    
    context = {
        'venta': venta,
        'recetas_venta': recetas_venta,
        'pagos': pagos,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'producciones': producciones,
        'puede_editar': venta.estado in ['Pendiente', 'Confirmada'],
        'puede_confirmar': venta.puede_confirmar,
        'puede_cancelar': venta.puede_cancelar,
        # 'historial_estados': historial_estados,
    }
    
    return render(request, 'ventas/detalle.html', context)


# @login_required  # Temporalmente comentado para pruebas
def editar_venta(request, venta_id):
    """
    Vista para editar una venta existente
    Equivalente a: ventasBean.java - prepararEdicion()
    """
    venta = get_object_or_404(Venta, id_ven=venta_id)
    
    # Verificar que la venta se puede editar
    if venta.estado not in ['Pendiente', 'Confirmada']:
        messages.error(request, f'No se puede editar una venta en estado "{venta.estado}"')
        return redirect('ventas:detalle', venta_id=venta.id_ven)
    
    if request.method == 'POST':
        return procesar_edicion_venta(request, venta)
    
    # Obtener datos actuales - DESHABILITADO (tabla no existe)
    # detalles = DetalleVenta.objects.filter(venta=venta).select_related('receta')
    detalles = []  # Lista vacía temporal
    
    # Obtener listas para el formulario
    clientes = Cliente.objects.filter(estado='Activo').order_by('nombre')
    usuarios_asignados = Usuario.objects.filter(
        estado='Activo', 
        rol__in=['A', 'EV', 'EP']
    ).order_by('nombres')
    recetas = Receta.objects.filter(estado='Activo').order_by('nombre')
    
    context = {
        'venta': venta,
        'detalles': detalles,
        'clientes': clientes,
        'usuarios_asignados': usuarios_asignados,
        'recetas': recetas,
        'editando': True,
    }
    
    return render(request, 'ventas/editar.html', context)


@transaction.atomic
def procesar_edicion_venta(request, venta):
    """
    Procesa la edición de una venta
    Equivalente a: ventasBean.java - actualizarVenta()
    """
    try:
        # Guardar valores originales para validación
        cliente_original = venta.cliente
        usuario_asignado_original = venta.usuario_asignado
        
        # Obtener nuevos datos
        tipo = request.POST.get('tipo', venta.tipo)
        cliente_id = request.POST.get('cliente_id')
        usuario_asignado_id = request.POST.get('usuario_asignado_id')
        observaciones = request.POST.get('observaciones', venta.observaciones)
        
        # Actualizar campos básicos
        venta.tipo = tipo
        venta.observaciones = observaciones
        
        # Actualizar cliente si cambió
        if cliente_id and int(cliente_id) != venta.cliente.id_cli:
            venta.cliente = get_object_or_404(Cliente, id_cli=cliente_id)
        
        # Actualizar usuario asignado si cambió
        if usuario_asignado_id and int(usuario_asignado_id) != venta.usuario_asignado.id_usu:
            venta.usuario_asignado = get_object_or_404(Usuario, id_usu=usuario_asignado_id)
        
        # Procesar cambios en detalles
        detalles_json = request.POST.get('detalles_venta', '[]')
        try:
            nuevos_detalles = json.loads(detalles_json)
        except json.JSONDecodeError:
            nuevos_detalles = []
        
        # Eliminar detalles existentes para reemplazarlos - DESHABILITADO (tabla no existe)
        # DetalleVenta.objects.filter(venta=venta).delete()
        # VentaReceta.objects.filter(venta=venta).delete()
        
        total_venta = Decimal('0.00')
        
        # Crear nuevos detalles
        for detalle_data in nuevos_detalles:
            receta_id = detalle_data.get('receta_id')
            cantidad = int(detalle_data.get('cantidad', 0))
            precio_unitario = Decimal(str(detalle_data.get('precio_unitario', '0.00')))
            
            if receta_id and cantidad > 0:
                receta = get_object_or_404(Receta, id_rec=receta_id)
                
                # Crear detalle de venta - DESHABILITADO (tabla no existe)
                # detalle = DetalleVenta.objects.create(
                #     venta=venta,
                #     receta=receta,
                #     cantidad=cantidad,
                #     precio_unitario=precio_unitario,
                #     nombre_empanada=receta.nombre
                # )
                pass  # Temporal
                
                # Crear entrada en VentaReceta
                VentaReceta.objects.create(
                    venta=venta,
                    receta=receta,
                    cantidad=cantidad,
                    precio=precio_unitario,
                    nombre_receta=receta.nombre
                )
                
                total_venta += detalle.subtotal
        
        # Actualizar total
        venta.total = total_venta
        venta.save()
        
        messages.success(request, f'Venta #{venta.id_ven} actualizada exitosamente')
        return redirect('ventas:detalle', venta_id=venta.id_ven)
        
    except Exception as e:
        messages.error(request, f'Error al actualizar la venta: {str(e)}')
        return redirect('ventas:editar', venta_id=venta.id_ven)


# @login_required  # Temporalmente comentado para pruebas
@require_http_methods(["POST"])
def cambiar_estado_venta(request, venta_id):
    """
    Cambia el estado de una venta
    Equivalente a: ventasBean.java - métodos específicos de estado
    """
    venta = get_object_or_404(Venta, id_ven=venta_id)
    nuevo_estado = request.POST.get('estado')
    motivo = request.POST.get('motivo', '')
    
    try:
        estado_anterior = venta.estado
        
        if nuevo_estado == 'Confirmada' and venta.puede_confirmar:
            venta.confirmar_venta()
            mensaje = f'Venta #{venta.id_ven} confirmada'
            
        elif nuevo_estado == 'En Preparacion' and venta.puede_preparar:
            venta.iniciar_preparacion()
            mensaje = f'Venta #{venta.id_ven} en preparación'
            
        elif nuevo_estado == 'Lista' and venta.estado == 'En Preparacion':
            venta.marcar_lista()
            mensaje = f'Venta #{venta.id_ven} lista para entrega'
            
        elif nuevo_estado == 'Entregada' and venta.puede_entregar:
            venta.entregar_venta()
            mensaje = f'Venta #{venta.id_ven} entregada'
            
        elif nuevo_estado == 'Cancelada' and venta.puede_cancelar:
            venta.cancelar_venta(motivo)
            mensaje = f'Venta #{venta.id_ven} cancelada'
            
        else:
            raise ValueError(f'No se puede cambiar de "{estado_anterior}" a "{nuevo_estado}"')
        
        venta.save()
        
        # Si es AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'mensaje': mensaje,
                'nuevo_estado': venta.estado,
                'color': venta.status_color
            })
        else:
            messages.success(request, mensaje)
            return redirect('ventas:detalle', venta_id=venta.id_ven)
            
    except Exception as e:
        error_msg = f'Error al cambiar estado: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('ventas:detalle', venta_id=venta.id_ven)


# @login_required  # Temporalmente comentado para pruebas
def gestionar_pagos(request, venta_id):
    """
    Vista para gestionar pagos de una venta
    Equivalente a: pagoBean.java - cargarPagosPorId()
    """
    venta = get_object_or_404(Venta, id_ven=venta_id)
    
    # Obtener pagos existentes
    pagos = Pago.objects.filter(venta=venta).order_by('-fecha_pago')
    
    # Obtener recetas de la venta
    recetas_venta = VentaReceta.objects.filter(venta=venta).select_related('receta')

    # === Calcular insumos totales usados por la venta ===
    # Para cada receta vendida, multiplicamos la cantidad de cada ingrediente por la cantidad vendida

    
    # Calcular totales
    total_pagado = pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    saldo_pendiente = venta.total - total_pagado
    
    # Calcular porcentajes
    porcentaje_pagado = (total_pagado / venta.total * 100) if venta.total > 0 else 0
    porcentaje_pendiente = 100 - porcentaje_pagado
    
    context = {
        'venta': venta,
        'pagos': pagos,
        'recetas_venta': recetas_venta,
        'total_pagado': total_pagado,
        'saldo_pendiente': saldo_pendiente,
        'porcentaje_pagado': porcentaje_pagado,
        'porcentaje_pendiente': porcentaje_pendiente,
        'puede_pagar': saldo_pendiente > 0,
    }
    
    return render(request, 'ventas/pagos.html', context)


@transaction.atomic
def procesar_pago(request, venta):
    """
    Procesa un nuevo pago para la venta
    """
    try:
        monto = Decimal(request.POST.get('monto', '0.00'))
        # tipo_pago se asigna automáticamente
        if monto <= 0:
            raise ValueError('El monto debe ser mayor a cero')

        # Verificar saldo disponible
        total_pagado = Pago.calcular_total_pagado_venta(venta)
        saldo_pendiente = venta.total - total_pagado

        if monto > saldo_pendiente:
            raise ValueError(f'El monto ${monto:,.0f} excede el saldo pendiente ${saldo_pendiente:,.0f}')

        # Asignar tipo_pago automáticamente
        if monto < saldo_pendiente:
            tipo_pago = 'abono'  # Abono Parcial
        else:
            tipo_pago = 'total'  # Pago Total

        # Crear el pago
        pago = Pago.crear_pago(
            venta=venta,
            monto=monto,
            tipo_pago=tipo_pago
        )

        mensaje = f'Pago de ${monto:,.0f} registrado exitosamente'

        # Verificar si la venta queda completamente pagada
        nuevo_saldo = saldo_pendiente - monto
        from .utils import actualizar_estado_venta_por_pagos
        actualizar_estado_venta_por_pagos(venta)
        if nuevo_saldo <= 0:
            mensaje += '. Venta completamente pagada.'
            # 🔹 Generar producción automáticamente si pago está completo
            try:
                from .utils import generar_produccion_desde_venta
                produccion = generar_produccion_desde_venta(venta)
                if produccion:
                    mensaje += f' Producción #{produccion["id_produccion"]} generada automáticamente.'
                else:
                    mensaje += ' (Producción ya existía para esta venta)'
            except Exception as e:
                print(f"⚠️ Error al generar producción: {e}")
                # No interrumpimos el proceso de pago por este error
                pass

        messages.success(request, mensaje)

        # Si es AJAX, devolver JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'mensaje': mensaje,
                'nuevo_saldo': float(nuevo_saldo),
                'pago_id': pago.id_pago
            })

        return redirect('ventas:pagos', venta_id=venta.id_ven)

    except Exception as e:
        error_msg = f'Error al procesar el pago: {str(e)}'

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': error_msg})
        else:
            messages.error(request, error_msg)
            return redirect('ventas:pagos', venta_id=venta.id_ven)


@transaction.atomic
def registrar_pago(request, venta_id):
    """
    Registra un nuevo pago para una venta
    Equivalente a: pagoBean.java - registrarPago()
    """
    if request.method != 'POST':
        return redirect('ventas:pagos', venta_id=venta_id)

    print(f"[DEBUG] Entrando a registrar_pago para venta_id={venta_id}")
    venta = get_object_or_404(Venta, id_ven=venta_id)
    return procesar_pago(request, venta)


@transaction.atomic
def eliminar_pago(request, pago_id):
    """
    Elimina un pago registrado
    Equivalente a: pagoBean.java - eliminarPago()
    """
    if request.method != 'POST':
        messages.error(request, 'Método no permitido')
        return redirect('ventas:index')
    
    pago = get_object_or_404(Pago, id_pago=pago_id)
    venta_id = pago.venta.id_ven
    
    print(f"[DEBUG] Entrando a procesar_pago para venta_id={venta.id_ven}")
    try:
        monto = pago.monto
        pago.delete()
        
        # Recalcular estado de la venta usando la función centralizada
        venta = Venta.objects.get(id_ven=venta_id)
        from .utils import actualizar_estado_venta_por_pagos, generar_produccion_desde_venta
        print(f"[DEBUG] Llamando a actualizar_estado_venta_por_pagos para venta_id={venta.id_ven}")
        nuevo_estado = actualizar_estado_venta_por_pagos(venta)
        # Si el estado es Procesando y no existe producción, generar producción explícitamente
        if nuevo_estado == 'Procesando':
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM venta_produccion WHERE id_venta = %s", [venta.id_ven])
                if cursor.fetchone()[0] == 0:
                    print(f"[DEBUG] Llamando a generar_produccion_desde_venta desde procesar_pago para venta_id={venta.id_ven}")
                    generar_produccion_desde_venta(venta)
        messages.success(request, f'Pago de ${monto:,.0f} eliminado correctamente. Estado actualizado.')
        
    except Exception as e:
        messages.error(request, f'Error al eliminar el pago: {str(e)}')
    
    return redirect('ventas:pagos', venta_id=venta_id)


# @login_required  # Temporalmente comentado para pruebas
def eliminar_venta(request, venta_id):
    """
    Elimina una venta con confirmación
    """
    venta = get_object_or_404(Venta, id_ven=venta_id)
    
    if request.method == 'POST':
        # Verificar si es una petición AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                # Verificar que la venta se pueda eliminar
                if venta.estado not in ['Pago pendiente', 'Pendiente']:
                    return JsonResponse({
                        'success': False, 
                        'error': f'No se puede eliminar una venta en estado "{venta.estado}"'
                    })
                
                venta_numero = venta.id_ven
                cliente_nombre = venta.cliente.nombre
                venta.delete()
                
                return JsonResponse({
                    'success': True, 
                    'message': f'Venta #{venta_numero} del cliente {cliente_nombre} eliminada exitosamente'
                })
                
            except Exception as e:
                return JsonResponse({
                    'success': False, 
                    'error': f'Error al eliminar la venta: {str(e)}'
                })
        else:
            # Manejo tradicional (no AJAX)
            try:
                if venta.estado not in ['Pago pendiente', 'Pendiente']:
                    messages.error(request, f'No se puede eliminar una venta en estado "{venta.estado}"')
                    return redirect('ventas:detalle', venta_id=venta.id_ven)
                
                venta_numero = venta.id_ven
                venta.delete()
                messages.success(request, f'Venta #{venta_numero} eliminada exitosamente')
                return redirect('ventas:index')
            except Exception as e:
                messages.error(request, f'Error al eliminar la venta: {str(e)}')
                return redirect('ventas:detalle', venta_id=venta.id_ven)
    
    return render(request, 'ventas/confirmar_eliminar.html', {'venta': venta})


# @login_required  # Temporalmente comentado para pruebas
def reportes_ventas(request):
    """
    Vista para mostrar reportes y estadísticas de ventas
    """
    # Obtener rango de fechas (por defecto último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin.replace(day=1)  # Primer día del mes actual
    
    if request.GET.get('fecha_inicio'):
        try:
            fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    if request.GET.get('fecha_fin'):
        try:
            fecha_fin = datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Filtrar ventas por rango de fechas
    ventas = Venta.objects.filter(
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    )
    
    # Estadísticas generales
    estadisticas = ventas.aggregate(
        total_ventas=Count('id_ven'),
        total_ingresos=Sum('total'),
        promedio_venta=Avg('total'),
        venta_minima=Min('total'),
        venta_maxima=Max('total')
    )
    
    # Ventas por estado
    ventas_por_estado = ventas.values('estado').annotate(
        cantidad=Count('id_ven'),
        total=Sum('total')
    ).order_by('-cantidad')
    
    # Ventas por tipo
    ventas_por_tipo = ventas.values('tipo').annotate(
        cantidad=Count('id_ven'),
        total=Sum('total')
    ).order_by('-cantidad')
    
    # Clientes con más compras
    top_clientes = ventas.values(
        'cliente__nombre', 'cliente__id_cli'
    ).annotate(
        cantidad_compras=Count('id_ven'),
        total_comprado=Sum('total')
    ).order_by('-total_comprado')[:10]
    
    # Empleados con más ventas
    top_empleados = ventas.values(
        'usuario__nombres', 'usuario__apellidos'
    ).annotate(
        cantidad_ventas=Count('id_ven'),
        total_vendido=Sum('total')
    ).order_by('-cantidad_ventas')[:10]
    
    # Productos más vendidos - DESHABILITADO (tabla no existe)
    # productos_vendidos = DetalleVenta.obtener_productos_mas_vendidos(
    #     fecha_inicio=fecha_inicio, 
    #     fecha_fin=fecha_fin,
    #     limite=10
    # )
    productos_vendidos = []  # Lista vacía temporal
    
    # Método de pago más usado
    metodos_pago = Pago.obtener_pagos_por_metodo(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )
    
    context = {
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estadisticas': estadisticas,
        'ventas_por_estado': ventas_por_estado,
        'ventas_por_tipo': ventas_por_tipo,
        'top_clientes': top_clientes,
        'top_empleados': top_empleados,
        'productos_vendidos': productos_vendidos,
        'metodos_pago': metodos_pago,
    }
    
    return render(request, 'ventas/reportes.html', context)


# === Vistas stub agregadas para botones del header (PDF, Correos, Migrar) ===
def exportar_pdf(request):
    """Generación de reporte PDF de ventas (stub). Reemplazar con lógica real."""
    return HttpResponse("Generación de Reporte PDF de Ventas - (pendiente de implementación)")


def correos_ventas(request):
    """Pantalla para envío masivo de correos relacionados con ventas (stub)."""
    return HttpResponse("Enviar Correos de Ventas - (pendiente de implementación)")


def migrar_ventas(request):
    """Herramienta de migración/importación/exportación de datos de ventas (stub)."""
    return HttpResponse("Migrar Datos de Ventas - (pendiente de implementación)")


# 🎯 Vistas AJAX para funcionalidades dinámicas

# @login_required  # Temporalmente comentado para pruebas
def buscar_clientes_ajax(request):
    """
    Búsqueda de clientes para autocompletado
    """
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        clientes = Cliente.objects.filter(
            Q(nombre__icontains=query) |
            Q(nit__icontains=query) |
            Q(telefono__icontains=query) |
            Q(correo__icontains=query)
        ).order_by('nombre')[:10]

        resultados = [
            {
                'id': c.id_Cliente,
                'nombre': c.nombre,
                'nit': c.nit,
                'telefono': c.telefono,
                'correo': c.correo
            } for c in clientes
        ]

        return JsonResponse({'clientes': resultados})
    
    return JsonResponse({'clientes': []})


# @login_required  # Temporalmente comentado para pruebas
def buscar_recetas_ajax(request):
    """
    Búsqueda de recetas para agregar a la venta
    """
    query = request.GET.get('q', '')
    
    if len(query) >= 2:
        recetas = Receta.objects.filter(
            Q(nombre__icontains=query) |
            Q(descripcion__icontains=query),
            estado='Activo'
        )[:10]
        
        resultados = []
        for receta in recetas:
            resultados.append({
                'id': receta.id_rec,
                'nombre': receta.nombre,
                'precio': float(receta.precio),
                'descripcion': receta.descripcion or '',
                'disponible': receta.esta_disponible if hasattr(receta, 'esta_disponible') else True
            })
        
        return JsonResponse({'recetas': resultados})
    
    return JsonResponse({'recetas': []})


# @login_required  # Temporalmente comentado para pruebas
def obtener_precio_receta(request, receta_id):
    """
    Obtiene el precio actual de una receta
    """
    try:
        receta = get_object_or_404(Receta, id_rec=receta_id)
        return JsonResponse({
            'success': True,
            'precio': float(receta.precio),
            'nombre': receta.nombre,
            'disponible': getattr(receta, 'esta_disponible', True)
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


# @login_required  # Temporalmente comentado para pruebas
def dashboard_ventas(request):
    """
    Dashboard principal de ventas con métricas en tiempo real
    """
    hoy = timezone.now().date()
    
    # Métricas del día
    ventas_hoy = Venta.objects.filter(fecha__date=hoy)
    metricas_hoy = ventas_hoy.aggregate(
        cantidad=Count('id_ven'),
        total=Sum('total')
    )
    
    # Métricas del mes
    primer_dia_mes = hoy.replace(day=1)
    ventas_mes = Venta.objects.filter(fecha__date__gte=primer_dia_mes)
    metricas_mes = ventas_mes.aggregate(
        cantidad=Count('id_ven'),
        total=Sum('total')
    )
    
    # Ventas pendientes
    ventas_pendientes = Venta.objects.filter(estado='Pendiente').count()
    ventas_preparacion = Venta.objects.filter(estado='En Preparacion').count()
    
    # Últimas ventas
    ultimas_ventas = Venta.objects.select_related('cliente', 'usuario').order_by('-fecha')[:5]
    
    # Productos más vendidos hoy - DESHABILITADO (tabla no existe)
    # productos_hoy = DetalleVenta.obtener_productos_mas_vendidos(
    #     fecha_inicio=hoy,
    #     fecha_fin=hoy,
    #     limite=5
    # )
    productos_hoy = []  # Lista vacía temporal
    
    context = {
        'metricas_hoy': metricas_hoy,
        'metricas_mes': metricas_mes,
        'ventas_pendientes': ventas_pendientes,
        'ventas_preparacion': ventas_preparacion,
        'ultimas_ventas': ultimas_ventas,
        'productos_hoy': productos_hoy,
    }
    
    return render(request, 'ventas/dashboard.html', context)


# 🎯 Vista especial para índice - redirige a listar_ventas
def index(request):
    """
    Vista índice que redirige a la lista de ventas
    """
    return listar_ventas(request)
