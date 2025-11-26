from django.urls import path
from . import views

app_name = 'recetas'

urlpatterns = [
    # CRUD básico de recetas
    path('', views.listar_recetas, name='index'),
    path('crear/', views.crear_receta, name='crear'),
    path('editar/<int:id_rec>/', views.editar_receta, name='editar'),
    path('eliminar/<int:id_rec>/', views.eliminar_receta, name='eliminar'),
    path('detalle/<int:id_rec>/', views.detalle_receta, name='detalle'),
    
    # Gestión de estado
    path('cambiar-estado/<int:id_rec>/', views.cambiar_estado, name='cambiar_estado'),
    
    # Búsqueda y filtros
    path('buscar/', views.buscar_recetas, name='buscar'),
    
    # Exportar e importar
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('exportar-pdf/<int:id_rec>/', views.exportar_pdf_receta, name='exportar_pdf_receta'),
    path('migrar-excel/', views.migrar_excel, name='migrar_excel'),
    path('duplicar/<int:id_rec>/', views.duplicar_receta, name='duplicar'),
    
    # Gestión de ingredientes
    path('<int:id_rec>/ingredientes/', views.listar_ingredientes, name='ingredientes'),
    path('<int:id_rec>/ingredientes/agregar/', views.agregar_ingrediente, name='agregar_ingrediente'),
    path('<int:id_rec>/ingredientes/<int:id_rec_ins>/editar/', views.editar_ingrediente, name='editar_ingrediente'),
    path('<int:id_rec>/ingredientes/<int:id_rec_ins>/eliminar/', views.eliminar_ingrediente, name='eliminar_ingrediente'),
    path('<int:id_rec>/ingredientes/sincronizar/', views.sincronizar_estados, name='sincronizar_estados'),
    
    # AJAX endpoints
    path('ingrediente/<int:id_rec_ins>/', views.obtener_ingrediente, name='obtener_ingrediente'),
    path('ingrediente/<int:id_rec_ins>/datos/', views.obtener_datos_ingrediente, name='obtener_datos_ingrediente'),
    path('ingrediente/<int:id_rec_ins>/eliminar/', views.eliminar_ingrediente_ajax, name='eliminar_ingrediente_ajax'),
    path('ajax/unidad/', views.actualizar_unidad_ajax, name='actualizar_unidad'),
    path('ajax/verificar/<int:id_rec>/', views.verificar_disponibilidad_receta, name='verificar_disponibilidad'),
    
    # Redirecciones de conveniencia
    path('gestionar-ingredientes/<int:id_rec>/', views.gestionar_ingredientes, name='gestionar_ingredientes'),
    
    # Sincronización y mantenimiento
    path('sincronizar-todas/', views.sincronizar_todas_recetas, name='sincronizar_todas'),
    path('reporte-disponibilidad/', views.reporte_disponibilidad, name='reporte_disponibilidad'),
]