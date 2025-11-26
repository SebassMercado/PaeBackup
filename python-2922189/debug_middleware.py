"""
Middleware para debugging de requests
"""
from django.utils import timezone

class RequestDebugMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log de la request entrante
        print(f"🔥 REQUEST: {request.method} {request.path} - {timezone.now()}")
        if request.method == 'POST':
            print(f"🔥 POST DATA: {dict(request.POST)}")
        
        response = self.get_response(request)
        
        # Log de la response
        print(f"🔥 RESPONSE: {response.status_code} - {request.path}")
        
        return response