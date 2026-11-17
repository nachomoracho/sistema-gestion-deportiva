"""
Authentication service for the SGAD project.

Provides secure login, brute-force protection (lockout after 5 failed attempts for 15 min),
Argon2id password hashing, and token issuance with custom claims.
"""

import logging
from datetime import timedelta
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from src.utils.audit_logger import log_audit_event
from src.utils.validators import validar_password_strength

logger = logging.getLogger('security_audit')

LOCKOUT_DURATION_MINUTES = 15
MAX_FAILED_ATTEMPTS = 5


class AuthenticationError(Exception):
    """Raised when authentication credentials are invalid."""
    pass


class AccountLockedError(Exception):
    """Raised when account is locked due to excessive failed attempts."""
    pass


class AuthService:
    """Service handling user authentication and credential security lifecycle."""

    @staticmethod
    def authenticate(rut_or_email, clave, request_ip=None, endpoint='/api/auth/login/'):
        """
        Authenticate a user by RUT or Email and password.
        
        Enforces:
        - Input presence
        - Account lockout verification
        - Failed attempts incrementation
        - Argon2id hash verification
        - Audit trail logging
        - JWT generation with role claims
        """
        from src.models.usuarios import Usuario

        identifier = str(rut_or_email).strip()
        cleaned_rut = identifier.upper().replace('.', '')

        # Lookup by RUT or Email
        usuario = None
        if '@' in identifier:
            usuario = Usuario.objects.select_related('id_perfil').filter(correo__iexact=identifier).first()
        else:
            usuario = Usuario.objects.select_related('id_perfil').filter(rut=cleaned_rut).first()

        if not usuario:
            log_audit_event(
                rut_actor=cleaned_rut or 'DESCONOCIDO',
                accion='AUTENTICACION_FALLIDA_USUARIO_INEXISTENTE',
                endpoint=endpoint,
                codigo_http=401,
                extra_data={'ip': request_ip, 'identificador': identifier}
            )
            raise AuthenticationError('Credenciales inválidas.')

        # Check account lockout
        now = timezone.now()
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta > now:
            remaining_seconds = int((usuario.bloqueado_hasta - now).total_seconds())
            remaining_minutes = max(1, (remaining_seconds + 59) // 60)
            log_audit_event(
                rut_actor=usuario.rut,
                accion='INTENTO_EN_CUENTA_BLOQUEADA',
                endpoint=endpoint,
                codigo_http=403,
                extra_data={'ip': request_ip, 'minutos_restantes': remaining_minutes}
            )
            raise AccountLockedError(
                f'Cuenta bloqueada por seguridad. Intente nuevamente en {remaining_minutes} minuto(s).'
            )

        # Clear expired lockout if timestamp passed
        if usuario.bloqueado_hasta and usuario.bloqueado_hasta <= now:
            usuario.bloqueado_hasta = None
            usuario.intentos_fallidos = 0
            usuario.save(update_fields=['bloqueado_hasta', 'intentos_fallidos'])

        # Verify password hash
        if not check_password(clave, usuario.clave):
            usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1

            if usuario.intentos_fallidos >= MAX_FAILED_ATTEMPTS:
                usuario.bloqueado_hasta = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                usuario.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])
                log_audit_event(
                    rut_actor=usuario.rut,
                    accion='CUENTA_BLOQUEADA_POR_FUERZA_BRUTA',
                    endpoint=endpoint,
                    codigo_http=403,
                    extra_data={'ip': request_ip, 'intentos': usuario.intentos_fallidos}
                )
                raise AccountLockedError(
                    f'Cuenta bloqueada por {LOCKOUT_DURATION_MINUTES} minutos tras {MAX_FAILED_ATTEMPTS} intentos fallidos.'
                )

            remaining = MAX_FAILED_ATTEMPTS - usuario.intentos_fallidos
            usuario.save(update_fields=['intentos_fallidos'])
            log_audit_event(
                rut_actor=usuario.rut,
                accion='AUTENTICACION_PASSWORD_INCORRECTA',
                endpoint=endpoint,
                codigo_http=401,
                extra_data={'ip': request_ip, 'intentos_fallidos': usuario.intentos_fallidos}
            )
            raise AuthenticationError(f'Credenciales inválidas. Intentos restantes: {remaining}.')

        # Authentication Successful - Reset counters
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save(update_fields=['intentos_fallidos', 'bloqueado_hasta'])

        # Generate JWT tokens with custom claims
        refresh = RefreshToken()
        refresh['rut'] = usuario.rut
        refresh['perfil'] = usuario.id_perfil.nombre_perfil if usuario.id_perfil else None
        refresh['nombre'] = f"{usuario.nombre} {usuario.apellido}"
        refresh['correo'] = usuario.correo
        refresh['debe_cambiar_clave'] = usuario.debe_cambiar_clave

        log_audit_event(
            rut_actor=usuario.rut,
            accion='AUTENTICACION_EXITOSA',
            endpoint=endpoint,
            codigo_http=200,
            extra_data={'ip': request_ip}
        )

        return {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'usuario': {
                'rut': usuario.rut,
                'nombre': usuario.nombre,
                'apellido': usuario.apellido,
                'correo': usuario.correo,
                'perfil': usuario.id_perfil.nombre_perfil if usuario.id_perfil else None,
                'especialidad': usuario.especialidad,
                'matricula': usuario.matricula,
                'debe_cambiar_clave': usuario.debe_cambiar_clave,
            },
        }

    @staticmethod
    def change_password(rut, clave_actual, clave_nueva, request_ip=None):
        """
        Change password after verifying the current one and meeting strength rules.
        """
        from src.models.usuarios import Usuario

        try:
            usuario = Usuario.objects.get(rut=rut)
        except Usuario.DoesNotExist:
            raise AuthenticationError('Usuario no encontrado.')

        if not check_password(clave_actual, usuario.clave):
            log_audit_event(
                rut_actor=rut,
                accion='CAMBIO_CLAVE_ACTUAL_INCORRECTA',
                endpoint='/api/auth/change-password/',
                codigo_http=400,
                extra_data={'ip': request_ip}
            )
            raise AuthenticationError('La contraseña actual es incorrecta.')

        # Validate password strength
        validar_password_strength(clave_nueva)

        # Hash with Argon2id
        usuario.clave = make_password(clave_nueva, hasher='argon2')
        usuario.debe_cambiar_clave = False
        usuario.save(update_fields=['clave', 'debe_cambiar_clave'])

        log_audit_event(
            rut_actor=rut,
            accion='CAMBIO_CLAVE_EXITOSO',
            endpoint='/api/auth/change-password/',
            codigo_http=200,
            extra_data={'ip': request_ip}
        )

        return True
