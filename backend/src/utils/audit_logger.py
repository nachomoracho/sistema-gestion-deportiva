import logging
import re

from src.models.auditoria import AuditoriaLog

logger = logging.getLogger('security_audit')

# Keys whose values should be masked
SENSITIVE_KEYS = re.compile(r'(password|clave|token|secret)', re.IGNORECASE)

# Pattern to find sensitive values in strings (e.g., "password=abc123")
SENSITIVE_VALUE_PATTERN = re.compile(
    r'(password|clave|token|secret)\s*[=:]\s*\S+',
    re.IGNORECASE,
)


def mask_sensitive_data(data):
    """
    Mask sensitive data in strings or dictionaries.
    - For strings: regex-mask password/clave/token/secret values.
    - For dicts: mask values of sensitive keys.
    """
    if isinstance(data, str):
        return SENSITIVE_VALUE_PATTERN.sub(
            lambda m: f"{m.group(1)}=***MASKED***", data,
        )

    if isinstance(data, dict):
        masked = {}
        for key, value in data.items():
            if SENSITIVE_KEYS.search(str(key)):
                masked[key] = '***MASKED***'
            elif isinstance(value, dict):
                masked[key] = mask_sensitive_data(value)
            elif isinstance(value, str):
                masked[key] = mask_sensitive_data(value)
            else:
                masked[key] = value
        return masked

    return data


def log_audit_event(rut_actor, accion, endpoint='', codigo_http=200, extra_data=None):
    """
    Log an audit event to the database and to the security_audit logger.
    Sensitive data is always masked before logging.
    """
    # Create the database record
    AuditoriaLog.objects.create(
        rut_actor=rut_actor,
        accion=accion,
        endpoint=endpoint,
        codigo_http=codigo_http,
    )

    # Prepare log message
    log_message = (
        f"AUDIT | Actor: {rut_actor} | Acción: {mask_sensitive_data(accion)} | "
        f"Endpoint: {endpoint} | HTTP: {codigo_http}"
    )

    if extra_data:
        masked_extra = mask_sensitive_data(extra_data)
        log_message += f" | Extra: {masked_extra}"

    # Log at appropriate level
    if codigo_http >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)
