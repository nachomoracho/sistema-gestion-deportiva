import pytest
from src.services.auth_service import AuthService, AuthenticationError, AccountLockedError
from src.models.usuarios import Usuario


class TestAuthService:
    def test_login_exitoso(self, coordinador_user):
        res = AuthService.authenticate("11111111-1", "Admin2026!#Segura")
        assert "access" in res
        assert "refresh" in res
        assert res["usuario"]["rut"] == "11111111-1"
        assert res["usuario"]["perfil"] == "COORDINADOR"

    def test_login_con_correo(self, coordinador_user):
        res = AuthService.authenticate("coord@test.cl", "Admin2026!#Segura")
        assert res["usuario"]["rut"] == "11111111-1"

    def test_login_password_incorrecta_incrementa_intentos(self, coordinador_user):
        with pytest.raises(AuthenticationError, match="Intentos restantes"):
            AuthService.authenticate("11111111-1", "WrongPassword!#123")

        u = Usuario.objects.get(rut="11111111-1")
        assert u.intentos_fallidos == 1

    def test_bloqueo_cuenta_tras_5_intentos_fallidos(self, coordinador_user):
        for _ in range(4):
            with pytest.raises(AuthenticationError):
                AuthService.authenticate("11111111-1", "BadPass1234!#")

        # 5th attempt must trigger AccountLockedError
        with pytest.raises(AccountLockedError, match="Cuenta bloqueada por 15 minutos"):
            AuthService.authenticate("11111111-1", "BadPass1234!#")

        u = Usuario.objects.get(rut="11111111-1")
        assert u.intentos_fallidos >= 5
        assert u.bloqueado_hasta is not None

        # Subsequent attempt even with correct password is blocked
        with pytest.raises(AccountLockedError):
            AuthService.authenticate("11111111-1", "Admin2026!#Segura")

    def test_cambio_clave_exitoso(self, coordinador_user):
        success = AuthService.change_password(
            rut="11111111-1",
            clave_actual="Admin2026!#Segura",
            clave_nueva="NuevaClave2026!#Fuerte",
        )
        assert success is True

        # Now authenticate with the new password
        res = AuthService.authenticate("11111111-1", "NuevaClave2026!#Fuerte")
        assert res["usuario"]["rut"] == "11111111-1"

    def test_cambio_clave_actual_invalida(self, coordinador_user):
        with pytest.raises(AuthenticationError, match="actual es incorrecta"):
            AuthService.change_password(
                rut="11111111-1",
                clave_actual="ClaveErronea123!#",
                clave_nueva="NuevaClave2026!#Fuerte",
            )
