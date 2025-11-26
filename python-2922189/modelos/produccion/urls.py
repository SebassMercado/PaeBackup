from django.urls import path
from . import views

app_name = 'produccion'

urlpatterns = [
    # Vistas principales
    path('', views.listar_producciones, name='index'),
    path('listar/', views.listar_producciones, name='listar'),
    path('nueva/', views.nueva_produccion, name='nueva'),
    path('<int:produccion_id>/detalle/', views.detalle_produccion, name='detalle'),
    path('eliminar/<int:produccion_id>/', views.eliminar_produccion, name='eliminar'),
    
    # APIs para cambios de estado y gestión
    path('cambiar-estado/<int:produccion_id>/', views.cambiar_estado_produccion, name='cambiar_estado'),
    path('api/cambiar-estado/<int:produccion_id>/', views.api_cambiar_estado_produccion, name='api_cambiar_estado'),
    path('api/fechas/<int:produccion_id>/', views.obtener_fechas_produccion, name='obtener_fechas'),
    path('<int:produccion_id>/recetas/', views.recetas_produccion, name='recetas'),
    
    # APIs para gestión de recetas en producción
    path('api/agregar-receta/<int:produccion_id>/', views.agregar_receta_produccion, name='agregar_receta'),
    path('api/actualizar-cantidad-receta/<int:detalle_id>/', views.actualizar_cantidad_receta, name='actualizar_cantidad'),
    path('api/eliminar-receta/<int:detalle_id>/', views.eliminar_receta_produccion, name='eliminar_receta'),
    path('api/ingredientes-receta/<int:receta_id>/', views.obtener_ingredientes_receta, name='ingredientes_receta'),
    
    # Exportación
    path('exportar-excel/', views.exportar_excel, name='exportar_excel'),
    path('exportar-pdf/', views.exportar_pdf, name='exportar_pdf'),
    path('migrar/', views.migrar_producciones, name='migrar'),
]