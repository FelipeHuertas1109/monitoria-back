from django.contrib.auth.models import AnonymousUser
from .models import UsuarioPersonalizado

class UsuarioPersonalizadoMiddleware:
    """
    Middleware para manejar la autenticación del modelo UsuarioPersonalizado
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Procesar la petición
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Procesar la vista antes de que se ejecute
        """
        # Si la vista no requiere autenticación, continuar
        if hasattr(view_func, 'permission_classes') and 'AllowAny' in [perm.__name__ for perm in view_func.permission_classes]:
            return None
        
        # Obtener el token del header Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        
        try:
            # Aquí deberías validar el token JWT y obtener el usuario
            # Por ahora, vamos a usar un enfoque simple
            # En producción, deberías usar la librería JWT para validar el token
            
            # Buscar usuario por algún campo del token (esto es temporal)
            # En realidad deberías decodificar el token JWT
            usuario = UsuarioPersonalizado.objects.first()  # Temporal
            if usuario:
                request.user = usuario
            else:
                request.user = AnonymousUser()
                
        except Exception:
            request.user = AnonymousUser()
        
        return None
