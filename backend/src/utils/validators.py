import re

from django.core.exceptions import ValidationError


def validar_rut(value):
    """
    Validate a Chilean RUT using the Modulo 11 algorithm.
    Accepts format: '12345678-K' or '12345678-0'
    """
    # Clean: strip whitespace, uppercase, remove dots
    cleaned = value.strip().upper().replace('.', '')

    # Validate format
    if not re.match(r'^\d{1,8}-[\dK]$', cleaned):
        raise ValidationError(
            'Formato de RUT inválido. Use el formato 12345678-K.',
            code='invalid_rut_format',
        )

    # Split body and check digit
    body, provided_digit = cleaned.split('-')

    # Modulo 11 calculation
    reversed_body = body[::-1]
    multipliers = [2, 3, 4, 5, 6, 7]
    total = 0
    for i, char in enumerate(reversed_body):
        total += int(char) * multipliers[i % len(multipliers)]

    remainder = total % 11
    result = 11 - remainder

    # Determine expected check digit
    if result == 11:
        expected_digit = '0'
    elif result == 10:
        expected_digit = 'K'
    else:
        expected_digit = str(result)

    # Compare
    if provided_digit != expected_digit:
        raise ValidationError(
            'RUT inválido. El dígito verificador no coincide.',
            code='invalid_rut_checksum',
        )


def validar_password_strength(password):
    """
    Validate password strength requirements.
    - Minimum 10 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    errors = []

    if len(password) < 10:
        errors.append('La contraseña debe tener al menos 10 caracteres.')

    if not re.search(r'[A-Z]', password):
        errors.append('La contraseña debe contener al menos una letra mayúscula.')

    if not re.search(r'[a-z]', password):
        errors.append('La contraseña debe contener al menos una letra minúscula.')

    if not re.search(r'\d', password):
        errors.append('La contraseña debe contener al menos un dígito.')

    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':\"\\|,.<>\/?`~]', password):
        errors.append('La contraseña debe contener al menos un carácter especial.')

    if errors:
        raise ValidationError(errors, code='weak_password')
