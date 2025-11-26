from django.conf import settings
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin


class NoCacheAndSessionAuthMiddleware(MiddlewareMixin):
    """
    - Evita que páginas protegidas se muestren desde caché del navegador (back).
    - Enforcea sesión propia basada en request.session['usuario_id'].
    """

    EXCLUDED_PREFIXES = (
        '/login',
        '/logout',
        '/static/',
        '/media/',
        '/admin',
    )

    def process_request(self, request):
        path = request.path or '/'

        # Permitir rutas excluidas y archivos estáticos
        for pref in self.EXCLUDED_PREFIXES:
            if path.startswith(pref):
                return None

        # Requerir sesión para vistas protegidas (todo excepto lo excluido)
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            # Solo redirigir para peticiones GET normales (no assets)
            if request.method in ('GET', 'HEAD'):
                messages.error(request, 'Debes iniciar sesión')
                return redirect(settings.LOGIN_URL)
        return None

    def process_response(self, request, response):
        path = getattr(request, 'path', '/')
        # No cache para páginas protegidas y dashboard, etc.
        should_nocache = True
        for pref in self.EXCLUDED_PREFIXES:
            if path.startswith(pref):
                should_nocache = False
                break
        # Evita marcarlos en archivos estáticos
        if should_nocache:
            response['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        return response
