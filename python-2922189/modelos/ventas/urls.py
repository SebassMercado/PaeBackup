from django.urls import path
from . import views
from . import ajax

app_name = 'ventas'

urlpatterns = [
    # Vistas principales
    path('', views.index, name='index'),
    path('listar/', views.listar_ventas, name='listar'),
    path('nueva/', views.nueva_venta, name='nueva'),
    path('procesar-nueva/', views.procesar_nueva_venta, name='procesar_nueva_venta'),
    path('detalle/<int:venta_id>/', views.detalle_venta, name='detalle'),
    path('editar/<int:venta_id>/', views.editar_venta, name='editar'),
    path('eliminar/<int:venta_id>/', views.eliminar_venta, name='eliminar'),
    
    # Gestión de estados
    path('cambiar-estado/<int:venta_id>/', views.cambiar_estado_venta, name='cambiar_estado'),
    
    # Gestión de pagos
    path('pagos/<int:venta_id>/', views.gestionar_pagos, name='pagos'),
    path('pagos/<int:venta_id>/registrar/', views.registrar_pago, name='registrar_pago'),
    path('pagos/<int:pago_id>/eliminar/', views.eliminar_pago, name='eliminar_pago'),
    
    # Reportes y dashboard
    path('reportes/', views.reportes_ventas, name='reportes'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('correos/', views.correos_ventas, name='correos'),
    path('migrar/', views.migrar_ventas, name='migrar'),
    path('dashboard/', views.dashboard_ventas, name='dashboard'),
    
    # Vistas AJAX
    path('ajax/buscar-clientes/', views.buscar_clientes_ajax, name='buscar_clientes_ajax'),
    path('ajax/buscar-recetas/', views.buscar_recetas_ajax, name='buscar_recetas_ajax'),
    path('ajax/precio-receta/<int:receta_id>/', views.obtener_precio_receta, name='precio_receta'),
    path('ajax/ingredientes-receta/<int:receta_id>/', ajax.ingredientes_receta_ajax, name='ingredientes_receta_ajax'),
]