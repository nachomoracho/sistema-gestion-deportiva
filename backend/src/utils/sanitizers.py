import re

from rest_framework.exceptions import ValidationError as DRFValidationError

# Pattern to detect dangerous characters for XSS / injection prevention
DANGEROUS_CHARS_PATTERN = re.compile(r'[<>"\'%()&+\\]|\x00')


def sanitize_input(value, field_name='campo'):
    """
    Sanitize a single input value.
    If the value is not a string, return it as-is.
    If dangerous characters are detected, raise a DRF ValidationError.
    Returns the stripped value.
    """
    if not isinstance(value, str):
        return value

    if DANGEROUS_CHARS_PATTERN.search(value):
        raise DRFValidationError({
            field_name: f'El campo {field_name} contiene caracteres no permitidos.',
        })

    return value.strip()


def sanitize_dict(data, exclude_fields=None):
    """
    Sanitize all string values in a dictionary.
    Fields listed in exclude_fields are skipped (e.g., 'clave').
    Returns a new dictionary with sanitized values.
    """
    if exclude_fields is None:
        exclude_fields = set()
    else:
        exclude_fields = set(exclude_fields)

    sanitized = {}
    for key, value in data.items():
        if key in exclude_fields:
            sanitized[key] = value
        elif isinstance(value, str):
            sanitized[key] = sanitize_input(value, field_name=key)
        else:
            sanitized[key] = value

    return sanitized
