from django.urls import path
from . import views

app_name = 'insumos'

urlpatterns = [
    # Listar insumos
    path('', views.listar_insumos, name='index'),
    
    # CRUD básico
    path('crear/', views.crear_insumo, name='crear'),
    path('editar/<int:id_ins>/', views.editar_insumo, name='editar'),
    path('eliminar/<int:id_ins>/', views.eliminar_insumo, name='eliminar'),
    path('detalle/<int:id_ins>/', views.detalle_insumo, name='detalle'),
    
    # Gestión de stock
    path('agregar-stock/<int:id_ins>/', views.agregar_stock, name='agregar_stock'),
    path('registrar-salida/<int:id_ins>/', views.registrar_salida, name='registrar_salida'),
    
    # Historial y alertas
    path('historial/', views.ver_historial, name='historial'),
    path('historial/<int:id_ins>/', views.ver_historial, name='historial_insumo'),
    path('alertas/', views.alertas_stock, name='alertas'),
    
    # Gestión de lotes
    path('agregar-lote/<int:id_ins>/', views.agregar_lote, name='agregar_lote'),
    path('editar-lote/<int:id_ins>/', views.editar_lote, name='editar_lote'),
    path('eliminar-lote/<int:id_ins>/', views.eliminar_lote, name='eliminar_lote'),
    path('lote/<int:lote_id>/', views.obtener_lote, name='obtener_lote'),
    path('exportar-lotes-pdf/<int:id_ins>/', views.exportar_lotes_pdf, name='exportar_lotes_pdf'),
    
    # Importar/Exportar
    path('migrar-excel/', views.migrar_excel, name='migrar_excel'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('correos/', views.correos_insumos, name='correos_insumos'),
    
    # Mantenimiento
    path('corregir-vencidos/', views.corregir_lotes_vencidos, name='corregir_vencidos'),
]
