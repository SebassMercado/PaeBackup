"""
URL configuration for pae_system project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.shortcuts import redirect
from core.views import login_view, logout_view, dashboard_view

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Autenticación
    path('', lambda request: redirect('/dashboard/', permanent=False)),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # URLs de módulos (se crearán gradualmente)
    path('usuarios/', include('modelos.usuarios.urls'), name='usuarios'),
    path('clientes/', include('modelos.clientes.urls'), name='clientes'),
    path('insumos/', include('modelos.insumos.urls'), name='insumos'),
    path('recetas/', include('modelos.recetas.urls'), name='recetas'),
    path('produccion/', include('modelos.produccion.urls'), name='produccion'),
    path('ventas/', include('modelos.ventas.urls'), name='ventas'),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
