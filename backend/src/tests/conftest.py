import os
import django
import pytest

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')
django.setup()

from src.models.perfiles import Perfil
from src.services.patterns import UsuarioFactory


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Enable database access for all pytest tests."""
    pass


@pytest.fixture
def perfiles():
    p_coord, _ = Perfil.objects.get_or_create(id_perfil=1, defaults={'nombre_perfil': Perfil.COORDINADOR})
    p_coach, _ = Perfil.objects.get_or_create(id_perfil=2, defaults={'nombre_perfil': Perfil.ENTRENADOR})
    p_estud, _ = Perfil.objects.get_or_create(id_perfil=3, defaults={'nombre_perfil': Perfil.ESTUDIANTE})
    return {'coordinador': p_coord, 'entrenador': p_coach, 'estudiante': p_estud}


@pytest.fixture
def coordinador_user(perfiles):
    return UsuarioFactory.crear_usuario(
        perfil_nombre=Perfil.COORDINADOR,
        rut='11111111-1',
        nombre='Carlos',
        apellido='Coordinador',
        correo='coord@test.cl',
        clave='Admin2026!#Segura',
    )


@pytest.fixture
def entrenador_user(perfiles):
    return UsuarioFactory.crear_usuario(
        perfil_nombre=Perfil.ENTRENADOR,
        rut='22222222-2',
        nombre='Marcelo',
        apellido='Entrenador',
        correo='coach@test.cl',
        clave='Coach2026!#Segura',
        especialidad='Fútbol y Acondicionamiento',
    )


@pytest.fixture
def entrenador_user_2(perfiles):
    return UsuarioFactory.crear_usuario(
        perfil_nombre=Perfil.ENTRENADOR,
        rut='12345678-5',
        nombre='Jorge',
        apellido='Sampaoli',
        correo='coach2@test.cl',
        clave='Coach2026!#Segura',
        especialidad='Básquetbol',
    )


@pytest.fixture
def estudiante_user(perfiles):
    return UsuarioFactory.crear_usuario(
        perfil_nombre=Perfil.ESTUDIANTE,
        rut='33333333-3',
        nombre='Alexis',
        apellido='Estudiante',
        correo='alumno@test.cl',
        clave='Alumno2026!#Segura',
        matricula='MAT-2026-001',
    )


@pytest.fixture
def estudiante_user_2(perfiles):
    return UsuarioFactory.crear_usuario(
        perfil_nombre=Perfil.ESTUDIANTE,
        rut='18456789-K',
        nombre='Arturo',
        apellido='Estudiante2',
        correo='alumno2@test.cl',
        clave='Alumno2026!#Segura',
        matricula='MAT-2026-002',
    )
