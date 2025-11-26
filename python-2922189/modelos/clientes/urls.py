from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # Vistas principales
    path('', views.index, name='index'),
    path('listar/', views.listar_clientes, name='listar'),
    path('nuevo/', views.nuevo_cliente, name='nuevo'),
    path('editar/<int:cliente_id>/', views.editar_cliente, name='editar'),
    path('eliminar/<int:cliente_id>/', views.eliminar_cliente, name='eliminar'),
    
    # Importar/Exportar
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('importar-excel/', views.importar_excel, name='importar_excel'),
    
    # AJAX y selección
    path('ajax/buscar/', views.buscar_clientes_ajax, name='buscar_ajax'),
    path('ajax/cargar/', views.cargar_clientes, name='cargar_ajax'),
    path('seleccionar/', views.cargar_clientes, name='seleccionar'),
]