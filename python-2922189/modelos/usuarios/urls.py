from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Lista principal
    path('', views.index, name='index'),
    
    # CRUD básico
    path('nuevo/', views.nuevo_usuario, name='nuevo'),
    path('editar/<int:id_usuario>/', views.editar_usuario, name='editar'),
    
    # Acciones AJAX
    path('cambiar-estado/<int:id_usuario>/', views.cambiar_estado, name='cambiar_estado'),
    path('eliminar/<int:id_usuario>/', views.eliminar_usuario, name='eliminar'),
    
    # Funciones avanzadas
    path('migrar/', views.migrar_usuarios, name='migrar'),
    path('correos/', views.enviar_correos, name='correos'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    
    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset/confirm/<str:token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('password-reset/verify/', views.password_reset_verify, name='password_reset_verify'),
    path('email-test/', views.email_test, name='email_test'),
]