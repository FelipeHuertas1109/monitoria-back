from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import UsuarioPersonalizado

class UsuarioPersonalizadoBackend(BaseBackend):
    """
    Backend de autenticación personalizado para UsuarioPersonalizado
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            usuario = UsuarioPersonalizado.objects.get(username=username)
            if usuario.check_password(password) and usuario.is_active:
                return usuario
        except UsuarioPersonalizado.DoesNotExist:
            return None
        return None
    
    def get_user(self, user_id):
        try:
            return UsuarioPersonalizado.objects.get(pk=user_id)
        except UsuarioPersonalizado.DoesNotExist:
            return None
