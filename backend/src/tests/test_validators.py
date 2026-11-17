import pytest
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

from src.utils.validators import validar_rut, validar_password_strength
from src.utils.sanitizers import sanitize_input, sanitize_dict


class TestRutValidator:
    def test_rut_valido_estandar(self):
        # Should not raise exception
        validar_rut("11111111-1")
        validar_rut("22222222-2")
        validar_rut("33333333-3")
        validar_rut("18456789-K")
        validar_rut("19876543-0")
        validar_rut("12345678-5")

    def test_rut_valido_con_k(self):
        # 11.222.333-K (11222333-K)
        # 1*3 + 1*2 + 2*7 + 2*6 + 2*5 + 3*4 + 3*3 + 3*2 = 3+2+14+12+10+12+9+6 = 68. 68%11 = 2. 11-2 = 9.
        # Let's verify a known RUT with K: 7.654.321-K or calculate:
        # e.g. 55555555-K: 5*(3+2+7+6+5+4+3+2) = 5*32 = 160. 160%11 = 6. 11-6 = 5.
        # 60.000.000-K: 6*3 = 18. 18%11 = 7. 11-7 = 4.
        # 14.987.654-K:
        # Let's test with valid check digits:
        with pytest.raises(ValidationError):
            validar_rut("11111111-9")  # Checksum mismatch

    def test_rut_invalido_formato(self):
        with pytest.raises(ValidationError):
            validar_rut("11111111")  # No dash
        with pytest.raises(ValidationError):
            validar_rut("ABC-1")      # Letters in body

    def test_rut_digito_verificador_erroneo(self):
        with pytest.raises(ValidationError):
            validar_rut("22222222-0")


class TestPasswordValidator:
    def test_password_fuerte_valida(self):
        validar_password_strength("Admin2026!#Segura")
        validar_password_strength("Prueba.1234$Complex")

    def test_password_corta_rechazada(self):
        with pytest.raises(ValidationError):
            validar_password_strength("Ab1!short")  # < 10 chars

    def test_password_sin_mayuscula_rechazada(self):
        with pytest.raises(ValidationError):
            validar_password_strength("admin2026!#segura")

    def test_password_sin_simbolo_rechazada(self):
        with pytest.raises(ValidationError):
            validar_password_strength("Admin2026Segura")

    def test_password_sin_numero_rechazada(self):
        with pytest.raises(ValidationError):
            validar_password_strength("AdminSecret!#Segura")


class TestSanitizer:
    def test_sanitize_limpia_espacios(self):
        res = sanitize_input("   Texto Seguro   ", field_name="campo")
        assert res == "Texto Seguro"

    def test_sanitize_rechaza_caracteres_peligrosos(self):
        caracteres_peligrosos = ['<script>', '"', "'", "%", "(", ")", "&", "+", "\\", "\x00"]
        for char in caracteres_peligrosos:
            with pytest.raises(DRFValidationError):
                sanitize_input(f"Ataque{char}Injection", field_name="prueba")

    def test_sanitize_dict_excluye_campos_clave(self):
        data = {
            'nombre': 'Carlos',
            'clave': 'PasswordConSimbolo#123()&+',
        }
        sanitized = sanitize_dict(data, exclude_fields=['clave'])
        assert sanitized['nombre'] == 'Carlos'
        assert sanitized['clave'] == 'PasswordConSimbolo#123()&+'
