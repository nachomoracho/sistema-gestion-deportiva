import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from src.models.usuarios import Usuario


class JWTAuthenticationBackend(BaseAuthentication):
    """
    Custom JWT Authentication Backend.
    Parses 'Authorization: Bearer <token>', verifies cryptographic signature (HS256),
    and sets request.user as the authenticated Usuario instance.
    """

    def authenticate(self, request):
        auth = get_authorization_header(request).split()

        if not auth or auth[0].lower() != b'bearer':
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Token no proporcionado.')
        elif len(auth) > 2:
            raise AuthenticationFailed('Encabezado de autorización malformado.')

        token = auth[1].decode('utf-8')
        return self.authenticate_credentials(token)

    def authenticate_credentials(self, token):
        try:
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=['HS256'],
                options={'verify_exp': True},
            )
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('La sesión ha expirado. Inicie sesión nuevamente.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token de autenticación inválido o manipulado.')

        rut = payload.get('rut')
        if not rut:
            raise AuthenticationFailed('El token no contiene un identificador de usuario válido.')

        try:
            usuario = Usuario.objects.select_related('id_perfil').get(rut=rut)
        except Usuario.DoesNotExist:
            raise AuthenticationFailed('Usuario no encontrado o dado de baja.')

        return (usuario, token)
