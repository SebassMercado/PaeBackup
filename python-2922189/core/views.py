from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from modelos.usuarios.models import Usuario
from modelos.clientes.models import Cliente
from modelos.insumos.models import Insumo
from modelos.recetas.models import Receta
from modelos.produccion.models import Produccion
from modelos.ventas.models import Venta


def login_view(request):
    """Vista de login personalizada usando SOLO tabla usuarios"""
    if request.method == 'POST':
        email_or_document = request.POST.get('correoDoc')
        password = request.POST.get('password')
        
        # Buscar usuario por correo o documento
        try:
            usuario = None
            
            # Determinar si es email o documento
            if '@' in email_or_document:
                # Es un email
                usuario = Usuario.objects.get(
                    correo=email_or_document,
                    estado='A'
                )
            else:
                # Es un documento (número)
                try:
                    documento_num = int(email_or_document)
                    usuario = Usuario.objects.get(
                        documento=documento_num,
                        estado='A'
                    )
                except ValueError:
                    # No es un número válido
                    messages.error(request, 'Formato de documento inválido')
                    return render(request, 'auth/login.html')
            
            if usuario:
                # Verificar contraseña
                if usuario.check_password(password):
                    # Guardar información del usuario en sesión (SIN usar auth_user)
                    request.session['usuario_id'] = usuario.id_usu
                    request.session['usuario_rol'] = usuario.rol
                    request.session['usuario_nombres'] = usuario.nombres
                    request.session['usuario_apellidos'] = usuario.apellidos
                    request.session['usuario_correo'] = usuario.correo
                    request.session['usuario_documento'] = usuario.documento
                    
                    messages.success(request, f'¡Bienvenido {usuario.nombres}!')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Contraseña incorrecta')
            else:
                messages.error(request, 'Usuario no encontrado o inactivo')
                
        except Usuario.DoesNotExist:
            messages.error(request, 'Usuario no encontrado o inactivo')
    
    return render(request, 'auth/login.html')


def logout_view(request):
    """Vista de logout"""
    # Limpiar sesión
    request.session.flush()
    messages.success(request, 'Has cerrado sesión correctamente')
    return redirect('login')


def dashboard_view(request):
    """Vista principal del dashboard"""
    # Verificar sesión
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        messages.error(request, 'Debes iniciar sesión primero')
        return redirect('login')
    
    usuario_rol = request.session.get('usuario_rol')
    
    try:
        usuario = Usuario.objects.get(id_usu=usuario_id, estado='A')
    except Usuario.DoesNotExist:
        request.session.flush()
        messages.error(request, 'Sesión inválida')
        return redirect('login')
    
    # Crear contexto base
    context = {
        'usuario': usuario,
        'usuario_rol': usuario_rol,
    }
    
    # Métricas según el rol
    if usuario_rol == 'A':  # Administrador
        context.update({
            'total_usuarios': Usuario.objects.filter(estado='A').count(),
            'total_producciones': Produccion.objects.count(),
            'total_ventas': Venta.objects.count(),
            # Métricas de insumos
            'insumos_activos': Insumo.objects.filter(estado='Activo').count(),
            'insumos_bajo_stock': Insumo.objects.filter(estado='Stock insuficiente').count(),
            'insumos_inactivos': Insumo.objects.filter(estado='Inactivo').count(),
            
            # Métricas de ventas
            'ventas_pago_pendiente': Venta.objects.filter(estado='Pago pendiente').count(),
            'ventas_pago_completo': Venta.objects.filter(estado='Pago completo').count(),
            'ventas_procesando': Venta.objects.filter(estado='Procesando').count(),
            'ventas_completadas': Venta.objects.filter(estado='Completada').count(),
            
            # Métricas de producción
            'producciones_pendientes': Produccion.objects.filter(estado='Pendiente').count(),
            'producciones_aceptadas': Produccion.objects.filter(estado='Aceptada').count(),
            'producciones_finalizadas': Produccion.objects.filter(estado='Finalizada').count(),
            
            # Métricas de recetas
            'recetas_activas': Receta.objects.filter(estado='Activo').count(),
            'recetas_inactivas': Receta.objects.filter(estado='Inactivo').count(),
            'total_recetas': Receta.objects.count(),
        })
        
        # Calcular porcentaje de recetas inactivas
        if context['total_recetas'] > 0:
            context['porcentaje_inactivas'] = round(
                (context['recetas_inactivas'] / context['total_recetas']) * 100, 1
            )
        else:
            context['porcentaje_inactivas'] = 0
    
    elif usuario_rol == 'EV':  # Empleado de Ventas
        user_ventas = Venta.objects.filter(usuario=usuario)
        context.update({
            'total_ventas_usuario': user_ventas.count(),
            'ventas_pago_pendiente_usuario': user_ventas.filter(estado='Pago pendiente').count(),
            'ventas_pago_completo_usuario': user_ventas.filter(estado='Pago completo').count(),
            'ventas_procesando_usuario': user_ventas.filter(estado='Procesando').count(),
            'ventas_completadas_usuario': user_ventas.filter(estado='Completada').count(),
        })
    
    elif usuario_rol == 'EP':  # Empleado de Producción
        # Producción no tiene campo 'usuario'; usamos 'usuario_asignado' para el empleado asignado
        user_producciones = Produccion.objects.filter(usuario_asignado=usuario)
        context.update({
            'total_producciones_usuario': user_producciones.count(),
            'producciones_pendientes_usuario': user_producciones.filter(estado='Pendiente').count(),
            'producciones_aceptadas_usuario': user_producciones.filter(estado='Aceptada').count(),
            'producciones_finalizadas_usuario': user_producciones.filter(estado='Finalizada').count(),
            # Métricas de insumos (visibles para producción)
            'insumos_activos': Insumo.objects.filter(estado='Activo').count(),
            'insumos_bajo_stock': Insumo.objects.filter(estado='Stock insuficiente').count(),
            'insumos_inactivos': Insumo.objects.filter(estado='Inactivo').count(),
            
            # Métricas de recetas para producción
            'recetas_activas': Receta.objects.filter(estado='Activo').count(),
            'recetas_inactivas': Receta.objects.filter(estado='Inactivo').count(),
            'total_recetas': Receta.objects.count(),
        })
        
        # Calcular porcentaje de recetas inactivas
        if context['total_recetas'] > 0:
            context['porcentaje_inactivas'] = round(
                (context['recetas_inactivas'] / context['total_recetas']) * 100, 1
            )
        else:
            context['porcentaje_inactivas'] = 0
    
    return render(request, 'dashboard/index.html', context)