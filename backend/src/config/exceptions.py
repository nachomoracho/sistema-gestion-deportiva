import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('security_audit')

SAFE_MESSAGES = {
    400: 'Solicitud inválida. Verifique los datos enviados.',
    401: 'Credenciales inválidas o sesión expirada.',
    403: 'No tiene permisos para acceder a este recurso.',
    404: 'El recurso solicitado no fue encontrado.',
    429: 'Demasiadas solicitudes. Intente nuevamente más tarde.',
}


def custom_exception_handler(exc, context):
    """Custom DRF exception handler that never exposes internal details."""
    response = exception_handler(exc, context)

    if response is not None:
        status_code = response.status_code
        safe_message = SAFE_MESSAGES.get(status_code, 'Error en la solicitud.')

        detalle = None
        if status_code == 400 and isinstance(response.data, dict):
            # Provide field-level validation detail for 400 errors only
            detalle = response.data

        response.data = {
            'error': True,
            'codigo': status_code,
            'mensaje': safe_message,
        }
        if detalle is not None:
            response.data['detalle'] = detalle

        return response

    # Unhandled exception — log and return generic 500
    view = context.get('view', None)
    view_name = view.__class__.__name__ if view else 'Unknown'
    logger.error(
        'Excepción no controlada en %s: %s',
        view_name,
        str(exc),
        exc_info=True,
    )

    return Response(
        {
            'error': True,
            'codigo': 500,
            'mensaje': 'Error interno del servidor. Contacte al administrador.',
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
