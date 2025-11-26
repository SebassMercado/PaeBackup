from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mass_mail, send_mail, EmailMessage
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import IntegrityError, transaction
from django.core.paginator import Paginator
import pandas as pd
import json
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime

from .models import Usuario, PasswordResetToken
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
import secrets
from datetime import timedelta


# Vista principal - Lista de usuarios
def index(request):
    """Lista todos los usuarios con paginación"""
    usuarios_list = Usuario.objects.all().order_by('nombres', 'apellidos')
    
    # Paginación
    paginator = Paginator(usuarios_list, 10)  # 10 usuarios por página
    page_number = request.GET.get('page')
    usuarios = paginator.get_page(page_number)
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios_list.count(),
        'usuarios_activos': usuarios_list.filter(estado='A').count(),
        'usuarios_inactivos': usuarios_list.filter(estado='I').count(),
    }
    
    return render(request, 'usuarios/index.html', context)


# Crear nuevo usuario
def nuevo_usuario(request):
    """Crear un nuevo usuario"""
    if request.method == 'POST':
        try:
            # Validar datos
            documento = request.POST.get('documento')
            nombres = request.POST.get('nombres')
            apellidos = request.POST.get('apellidos')
            telefono = request.POST.get('telefono')
            direccion = request.POST.get('direccion')
            correo = request.POST.get('correo')
            password = request.POST.get('password')
            rol = request.POST.get('rol')
            
            # Validaciones
            if not all([documento, nombres, apellidos, telefono, direccion, correo, password, rol]):
                messages.error(request, 'Todos los campos son obligatorios')
                return render(request, 'usuarios/nuevo_usuario.html')
            
            # Validar email
            try:
                validate_email(correo)
            except ValidationError:
                messages.error(request, 'El correo electrónico no es válido')
                return render(request, 'usuarios/nuevo_usuario.html')
            
            # Crear usuario
            with transaction.atomic():
                usuario = Usuario(
                    documento=int(documento),
                    nombres=nombres,
                    apellidos=apellidos,
                    telefono=int(telefono),
                    direccion=direccion,
                    correo=correo,
                    rol=rol,
                    estado='A'
                )
                usuario.set_password(password)  # Encriptar contraseña
                usuario.save()
            
            messages.success(request, f'Usuario {nombres} {apellidos} creado exitosamente')
            return redirect('usuarios:index')
            
        except IntegrityError as e:
            if 'documento' in str(e):
                messages.error(request, 'Ya existe un usuario con ese documento')
            elif 'correo' in str(e):
                messages.error(request, 'Ya existe un usuario con ese correo electrónico')
            else:
                messages.error(request, 'Error al crear el usuario')
        except ValueError:
            messages.error(request, 'Documento y teléfono deben ser números válidos')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
    
    return render(request, 'usuarios/nuevo_usuario.html')


# Editar usuario
def editar_usuario(request, id_usuario):
    """Editar un usuario existente"""
    usuario = get_object_or_404(Usuario, id_usu=id_usuario)
    
    if request.method == 'POST':
        try:
            # Actualizar datos
            usuario.documento = int(request.POST.get('documento'))
            usuario.nombres = request.POST.get('nombres')
            usuario.apellidos = request.POST.get('apellidos')
            usuario.telefono = int(request.POST.get('telefono'))
            usuario.direccion = request.POST.get('direccion')
            usuario.correo = request.POST.get('correo')
            usuario.rol = request.POST.get('rol')
            
            # Solo cambiar contraseña si se proporciona
            password = request.POST.get('password')
            if password and password.strip():
                usuario.set_password(password)
            
            # Validar email
            try:
                validate_email(usuario.correo)
            except ValidationError:
                messages.error(request, 'El correo electrónico no es válido')
                return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})
            
            usuario.save()
            messages.success(request, f'Usuario {usuario.nombres} {usuario.apellidos} actualizado exitosamente')
            return redirect('usuarios:index')
            
        except IntegrityError as e:
            if 'documento' in str(e):
                messages.error(request, 'Ya existe un usuario con ese documento')
            elif 'correo' in str(e):
                messages.error(request, 'Ya existe un usuario con ese correo electrónico')
            else:
                messages.error(request, 'Error al actualizar el usuario')
        except ValueError:
            messages.error(request, 'Documento y teléfono deben ser números válidos')
        except Exception as e:
            messages.error(request, f'Error inesperado: {str(e)}')
    
    return render(request, 'usuarios/editar_usuario.html', {'usuario': usuario})


# Cambiar estado del usuario (AJAX)
@require_POST
def cambiar_estado(request, id_usuario):
    """Cambiar estado activo/inactivo de un usuario"""
    try:
        usuario = get_object_or_404(Usuario, id_usu=id_usuario)
        nuevo_estado = 'I' if usuario.estado == 'A' else 'A'
        usuario.estado = nuevo_estado
        usuario.save()
        
        estado_texto = 'Activado' if nuevo_estado == 'A' else 'Desactivado'
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {estado_texto} exitosamente',
            'nuevo_estado': nuevo_estado,
            'estado_texto': 'Activo' if nuevo_estado == 'A' else 'Inactivo'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar estado: {str(e)}'
        })


# Eliminar usuario
@require_POST
def eliminar_usuario(request, id_usuario):
    """Eliminar un usuario"""
    try:
        usuario = get_object_or_404(Usuario, id_usu=id_usuario)
        nombre_completo = f"{usuario.nombres} {usuario.apellidos}"
        usuario.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Usuario {nombre_completo} eliminado exitosamente'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al eliminar usuario: {str(e)}'
        })


# Migrar usuarios desde Excel
def migrar_usuarios(request):
    """Migrar usuarios desde archivo Excel"""
    if request.method == 'POST' and request.FILES.get('excel_file'):
        try:
            excel_file = request.FILES['excel_file']
            
            # Verificar que sea un archivo Excel
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, 'El archivo debe ser un Excel (.xlsx o .xls)')
                return render(request, 'usuarios/migrar.html')
            
            # Leer Excel
            df = pd.read_excel(excel_file)
            
            # Validar columnas requeridas
            columnas_requeridas = ['documento', 'nombres', 'apellidos', 'telefono', 'direccion', 'correo', 'rol', 'password']
            if not all(col in df.columns for col in columnas_requeridas):
                messages.error(request, f'El archivo debe contener las columnas: {", ".join(columnas_requeridas)}')
                return render(request, 'usuarios/migrar.html')
            
            usuarios_creados = 0
            errores = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Validar email
                        validate_email(row['correo'])
                        
                        # Crear usuario
                        usuario = Usuario(
                            documento=int(row['documento']),
                            nombres=row['nombres'],
                            apellidos=row['apellidos'],
                            telefono=int(row['telefono']),
                            direccion=row['direccion'],
                            correo=row['correo'],
                            rol=row['rol'],
                            estado='A'
                        )
                        usuario.set_password(str(row['password']))
                        usuario.save()
                        usuarios_creados += 1
                        
                    except Exception as e:
                        errores.append(f"Fila {index + 2}: {str(e)}")
            
            if usuarios_creados > 0:
                messages.success(request, f'Se migraron {usuarios_creados} usuarios exitosamente')
            
            if errores:
                messages.warning(request, f'Errores encontrados: {"; ".join(errores[:5])}')  # Solo mostrar primeros 5 errores
                
        except Exception as e:
            messages.error(request, f'Error al procesar archivo: {str(e)}')
    
    return render(request, 'usuarios/migrar.html')


# Enviar correos
def enviar_correos(request):
    """Enviar correos masivos a usuarios"""
    usuarios_list = Usuario.objects.filter(estado='A').order_by('nombres')
    
    if request.method == 'POST':
        try:
            destinatarios = request.POST.getlist('destinatarios')
            asunto = request.POST.get('asunto')
            mensaje = request.POST.get('mensaje')
            
            if not destinatarios:
                messages.error(request, 'Debe seleccionar al menos un destinatario')
                return render(request, 'usuarios/correos.html', {'usuarios': usuarios_list})
            
            if not asunto or not mensaje:
                messages.error(request, 'Asunto y mensaje son obligatorios')
                return render(request, 'usuarios/correos.html', {'usuarios': usuarios_list})
            
            # Preparar correos
            correos = []
            for correo in destinatarios:
                correos.append((
                    asunto,
                    mensaje,
                    settings.DEFAULT_FROM_EMAIL,
                    [correo]
                ))
            
            # Enviar correos
            enviados = send_mass_mail(correos, fail_silently=False)
            
            messages.success(request, f'Se enviaron {enviados} correos exitosamente')
            return redirect('usuarios:index')
            
        except Exception as e:
            messages.error(request, f'Error al enviar correos: {str(e)}')
    
    context = {
        'usuarios': usuarios_list
    }
    return render(request, 'usuarios/correos.html', context)


# Exportar PDF
def exportar_pdf(request):
    """Exportar lista de usuarios a PDF"""
    try:
        # Crear buffer
        buffer = BytesIO()
        
        # Crear documento PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elementos = []
        
        # Estilos
        styles = getSampleStyleSheet()
        titulo_style = styles['Title']
        normal_style = styles['Normal']
        
        # Título
        titulo = Paragraph("<b>Reporte de Usuarios - PAE</b>", titulo_style)
        elementos.append(titulo)
        elementos.append(Spacer(1, 20))
        
        # Fecha
        fecha = Paragraph(f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", normal_style)
        elementos.append(fecha)
        elementos.append(Spacer(1, 20))
        
        # Obtener usuarios
        usuarios = Usuario.objects.all().order_by('nombres', 'apellidos')
        
        # Datos para la tabla
        data = [['ID', 'Documento', 'Nombres', 'Apellidos', 'Teléfono', 'Correo', 'Rol', 'Estado']]
        
        for usuario in usuarios:
            data.append([
                str(usuario.id_usu),
                str(usuario.documento),
                usuario.nombres[:15],  # Truncar nombres largos
                usuario.apellidos[:15],
                str(usuario.telefono),
                usuario.correo[:20],
                usuario.get_rol_display(),
                'Activo' if usuario.estado == 'A' else 'Inactivo'
            ])
        
        # Crear tabla
        tabla = Table(data)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elementos.append(tabla)
        
        # Construir PDF
        doc.build(elementos)
        
        # Preparar respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        
        return response
        
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('usuarios:index')


# ===== Recuperación de contraseña =====
def password_reset_request(request):
    """Formulario para solicitar recuperación de contraseña"""
    if request.method == 'POST':
        identificador = request.POST.get('correoDocumento', '').strip()
        if not identificador:
            messages.error(request, 'Debe ingresar correo o documento')
            return render(request, 'usuarios/password_reset_request.html')

        # Buscar usuario por correo o documento
        usuario = None
        try:
            if '@' in identificador:
                usuario = Usuario.objects.get(correo=identificador, estado='A')
            else:
                usuario = Usuario.objects.get(documento=int(identificador), estado='A')
        except (Usuario.DoesNotExist, ValueError):
            usuario = None

        if not usuario:
            messages.error(request, 'No se encontró un usuario activo con esos datos')
            return render(request, 'usuarios/password_reset_request.html')

        # Generar token y código
        token = secrets.token_urlsafe(48)
        codigo = f"{secrets.randbelow(1000000):06d}"
        PasswordResetToken.objects.create(usuario=usuario, token=token, codigo=codigo)
        reset_url = request.build_absolute_uri(reverse('usuarios:password_reset_confirm', args=[token]))

        asunto = 'Recuperación de contraseña PAE'
        texto_plano = (
            f'Hola {usuario.nombres},\n\n'
            f'Solicitaste recuperar tu contraseña. Usa el código y/o el enlace:\n\n'
            f'Código: {codigo}\n'
            f'Enlace: {reset_url}\n\n'
            f'Expira en {settings.PASSWORD_RESET_TOKEN_EXP_MINUTES} minutos.'
        )
        html_body = f"""
        <html><body style='font-family:Poppins,Arial,sans-serif;'>
        <h2 style='color:#b71c1c;margin-bottom:8px;'>Recuperación de contraseña</h2>
        <p>Hola <strong>{usuario.nombres}</strong>, solicitaste recuperar tu contraseña.</p>
        <p><strong>Código:</strong> <span style='font-size:18px;letter-spacing:2px;'>{codigo}</span></p>
        <p><a href='{reset_url}' style='display:inline-block;padding:10px 16px;background:#b71c1c;color:#fff;text-decoration:none;border-radius:8px;'>Restablecer con enlace</a></p>
        <p style='font-size:12px;color:#666;'>Expira en {settings.PASSWORD_RESET_TOKEN_EXP_MINUTES} minutos. Ignora este mensaje si no lo solicitaste.</p>
        </body></html>
        """

        envio_exitoso = False
        errores_envio = []

        # Intento 1: send_mail (texto plano)
        try:
            sent = send_mail(asunto, texto_plano, settings.DEFAULT_FROM_EMAIL, [usuario.correo], fail_silently=False)
            if sent:
                envio_exitoso = True
        except Exception as e:
            errores_envio.append(f'send_mail: {e}')

        # Intento 2: send_mass_mail si anterior falla
        if not envio_exitoso:
            try:
                sent2 = send_mass_mail(((asunto, texto_plano, settings.DEFAULT_FROM_EMAIL, [usuario.correo]),), fail_silently=False)
                if sent2:
                    envio_exitoso = True
            except Exception as e:
                errores_envio.append(f'send_mass_mail: {e}')

        # Intento 3: EmailMessage con HTML
        if not envio_exitoso:
            try:
                msg = EmailMessage(asunto, texto_plano, settings.DEFAULT_FROM_EMAIL, [usuario.correo])
                msg.content_subtype = 'plain'
                msg.attach_alternative(html_body, 'text/html')
                msg.send(fail_silently=False)
                envio_exitoso = True
            except Exception as e:
                errores_envio.append(f'EmailMessage: {e}')

        if envio_exitoso:
            messages.success(request, 'Se envió un correo con instrucciones (código y enlace).')
        else:
            if settings.DEBUG:
                messages.error(request, 'Fallo envío correo. Revisa configuración SMTP.')
                messages.warning(request, f'Errores: {" | ".join(errores_envio)}')
                messages.warning(request, f'Código temporal: {codigo}')
                messages.warning(request, f'Enlace directo: {reset_url}')
            else:
                messages.error(request, 'No fue posible enviar el correo. Contacta al administrador.')

        return render(request, 'usuarios/password_reset_request.html')

    return render(request, 'usuarios/password_reset_request.html')


def password_reset_confirm(request, token):
    """Formulario para establecer nueva contraseña usando token"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token, usado=False)
    except PasswordResetToken.DoesNotExist:
        messages.error(request, 'Token inválido o usado')
        return render(request, 'usuarios/password_reset_confirm.html', {'invalid': True})

    # Verificar expiración
    exp_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXP_MINUTES', 60)
    if timezone.now() > reset_token.creado + timedelta(minutes=exp_minutes):
        messages.error(request, 'El token ha expirado, solicita uno nuevo')
        return render(request, 'usuarios/password_reset_confirm.html', {'expired': True})

    if request.method == 'POST':
        nueva = request.POST.get('password')
        repetir = request.POST.get('password2')
        if not nueva or not repetir:
            messages.error(request, 'Todos los campos son obligatorios')
        elif nueva != repetir:
            messages.error(request, 'Las contraseñas no coinciden')
        elif len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener mínimo 6 caracteres')
        else:
            usuario = reset_token.usuario
            usuario.set_password(nueva)
            usuario.save(update_fields=['password'])
            reset_token.marcar_usado()
            messages.success(request, 'Contraseña actualizada. Ya puedes iniciar sesión.')
            return redirect('login')

    return render(request, 'usuarios/password_reset_confirm.html', {'token': token})


def password_reset_verify(request):
    """Verificar código y establecer nueva contraseña sin usar enlace"""
    if request.method == 'POST':
        identificador = request.POST.get('correoDocumento', '').strip()
        codigo = request.POST.get('codigo', '').strip()
        nueva = request.POST.get('password')
        repetir = request.POST.get('password2')
        if not all([identificador, codigo, nueva, repetir]):
            messages.error(request, 'Todos los campos son obligatorios')
            return render(request, 'usuarios/password_reset_verify.html')
        if nueva != repetir:
            messages.error(request, 'Las contraseñas no coinciden')
            return render(request, 'usuarios/password_reset_verify.html')
        if len(nueva) < 6:
            messages.error(request, 'La contraseña debe tener mínimo 6 caracteres')
            return render(request, 'usuarios/password_reset_verify.html')
        # Buscar usuario
        try:
            if '@' in identificador:
                usuario = Usuario.objects.get(correo=identificador, estado='A')
            else:
                usuario = Usuario.objects.get(documento=int(identificador), estado='A')
        except (Usuario.DoesNotExist, ValueError):
            messages.error(request, 'Usuario no encontrado')
            return render(request, 'usuarios/password_reset_verify.html')
        # Buscar token más reciente con ese código
        exp_minutes = getattr(settings, 'PASSWORD_RESET_TOKEN_EXP_MINUTES', 60)
        limite = timezone.now() - timedelta(minutes=exp_minutes)
        try:
            reset_token = PasswordResetToken.objects.filter(usuario=usuario, codigo=codigo, usado=False, creado__gte=limite).latest('creado')
        except PasswordResetToken.DoesNotExist:
            messages.error(request, 'Código inválido o expirado')
            return render(request, 'usuarios/password_reset_verify.html')
        usuario.set_password(nueva)
        usuario.save(update_fields=['password'])
        reset_token.marcar_usado()
        messages.success(request, 'Contraseña actualizada. Ingresa con tu nueva contraseña.')
        return redirect('login')
    return render(request, 'usuarios/password_reset_verify.html')


def email_test(request):
    """Vista de diagnóstico para probar envío de correo (solo DEBUG)."""
    if not settings.DEBUG:
        return JsonResponse({'error': 'No disponible en producción'}, status=403)
    correo = request.GET.get('to') or settings.EMAIL_HOST_USER
    try:
        sent = send_mail('Test PAE', 'Correo de prueba de configuración SMTP', settings.DEFAULT_FROM_EMAIL, [correo], fail_silently=False)
        return JsonResponse({'status': 'ok', 'sent': sent, 'to': correo})
    except Exception as e:
        return JsonResponse({'status': 'error', 'error': str(e), 'host': settings.EMAIL_HOST, 'user': settings.EMAIL_HOST_USER})
