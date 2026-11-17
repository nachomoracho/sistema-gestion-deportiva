import jwt
from django.conf import settings
from src.utils.audit_logger import log_audit_event


class SecurityHeadersMiddleware:
    """Middleware that injects defense-in-depth security headers into all responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # OWASP recommended headers
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "connect-src 'self' http://localhost:8000 http://127.0.0.1:8000; "
            "frame-ancestors 'none'"
        )
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        response['Pragma'] = 'no-cache'

        return response


class AuditLoggingMiddleware:
    """Middleware that logs 401 Unauthorized and 403 Forbidden events into the audit trail."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            rut = None
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ', 1)[1]
                try:
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=['HS256'],
                        options={'verify_exp': False},
                    )
                    rut = payload.get('rut')
                except Exception:
                    pass

            if response.status_code == 403:
                log_audit_event(
                    rut_actor=rut or 'ANONYMOUS',
                    accion='ACCESO_DENEGADO_403',
                    endpoint=request.path,
                    codigo_http=403,
                    extra_data={
                        'ip': self._get_client_ip(request),
                        'metodo': request.method,
                    }
                )
            elif response.status_code == 401:
                log_audit_event(
                    rut_actor=rut or 'ANONYMOUS',
                    accion='AUTENTICACION_REQUERIDA_401',
                    endpoint=request.path,
                    codigo_http=401,
                    extra_data={
                        'ip': self._get_client_ip(request),
                        'metodo': request.method,
                    }
                )
        except Exception:
            # Never fail the response due to audit errors
            pass

        return response

    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')
