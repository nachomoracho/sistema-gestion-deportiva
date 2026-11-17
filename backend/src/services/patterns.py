"""
Design patterns for the SGAD project.

1. Singleton  — ConexionOracleSingleton
2. Factory    — UsuarioFactory
3. Observer   — EvaluacionSubject / EstudianteNotificacionObserver
4. Adapter    — IntranetAcademicaAdapter
"""

import threading
from abc import ABC, abstractmethod
from decimal import Decimal
from django.contrib.auth.hashers import make_password


# ---------------------------------------------------------------------------
# 1. Singleton — ConexionOracleSingleton
# ---------------------------------------------------------------------------

class ConexionOracleSingleton:
    """
    Thread-safe Singleton for managing Oracle SQL connection and pool parameters.
    Ensures a single connection pool configuration exists across the application lifecycle.
    """

    _instance = None
    _lock = threading.Lock()
    _is_initialized = False

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, dsn="localhost:1521/XEPDB1", user="app_user", password="secret_password", pool_min=2, pool_max=10):
        """Initialize connection pool parameters."""
        with self._lock:
            self._dsn = dsn
            self._user = user
            self._password = password
            self._pool_min = pool_min
            self._pool_max = pool_max
            ConexionOracleSingleton._is_initialized = True

    @property
    def dsn(self):
        return getattr(self, '_dsn', 'localhost:1521/XEPDB1')

    @property
    def user(self):
        return getattr(self, '_user', 'app_user')

    @property
    def pool_min(self):
        return getattr(self, '_pool_min', 2)

    @property
    def pool_max(self):
        return getattr(self, '_pool_max', 10)

    @property
    def is_initialized(self):
        return ConexionOracleSingleton._is_initialized

    def ejecutar_consulta_segura(self, sql, params=None):
        """
        Simulates executing a parameterized query through the Oracle pool.
        Guarantees parameterized input to prevent SQL injection (OWASP A03 / ISO 27002 8.28).
        """
        if params is None:
            params = []
        return {
            "status": "SUCCESS",
            "sql": sql,
            "params_count": len(params),
            "engine": "Oracle SQL Database Pool",
        }

    @classmethod
    def reset(cls):
        """Reset the singleton instance for testing purposes."""
        with cls._lock:
            cls._instance = None
            cls._is_initialized = False


# ---------------------------------------------------------------------------
# 2. Factory — UsuarioFactory
# ---------------------------------------------------------------------------

class UsuarioFactory:
    """
    Factory for polymorphic creation of users according to profile:
    - COORDINADOR
    - ENTRENADOR (requires 'especialidad')
    - ESTUDIANTE  (requires 'matricula')
    Applies Argon2id password hashing and Modulo 11 RUT validation.
    """

    @staticmethod
    def crear_usuario(
        perfil_nombre,
        rut,
        nombre,
        apellido,
        correo,
        clave,
        especialidad=None,
        matricula=None,
        debe_cambiar_clave=False,
    ):
        """
        Create and persist a new Usuario entity with domain invariants enforced.
        """
        from src.models.perfiles import Perfil
        from src.models.usuarios import Usuario
        from src.utils.validators import validar_rut, validar_password_strength

        # 1. Validate RUT format & Modulo 11 check digit
        validar_rut(rut)

        # 2. Validate password complexity (OWASP A02 / ISO 27002 8.5)
        validar_password_strength(clave)

        # 3. Retrieve Profile
        perfil_nombre_clean = str(perfil_nombre).strip().upper()
        try:
            perfil = Perfil.objects.get(nombre_perfil=perfil_nombre_clean)
        except Perfil.DoesNotExist:
            raise ValueError(f"Perfil '{perfil_nombre}' no existe en el sistema.")

        # 4. Enforce role-specific attributes
        if perfil_nombre_clean == Perfil.ENTRENADOR and not especialidad:
            raise ValueError("El campo 'especialidad' es obligatorio para el perfil ENTRENADOR.")
        if perfil_nombre_clean == Perfil.ESTUDIANTE and not matricula:
            raise ValueError("El campo 'matricula' es obligatorio para el perfil ESTUDIANTE.")

        # 5. Hash password with Argon2id
        clave_hash = make_password(clave, hasher='argon2')

        # 6. Instantiate and save Usuario
        usuario = Usuario(
            rut=rut.strip().upper(),
            id_perfil=perfil,
            nombre=nombre.strip(),
            apellido=apellido.strip(),
            correo=correo.strip().lower(),
            clave=clave_hash,
            especialidad=especialidad.strip() if especialidad else None,
            matricula=matricula.strip().upper() if matricula else None,
            debe_cambiar_clave=debe_cambiar_clave,
        )
        usuario.full_clean()
        usuario.save()

        return usuario


# ---------------------------------------------------------------------------
# 3. Observer — EvaluacionSubject / EstudianteNotificacionObserver
# ---------------------------------------------------------------------------

class ObserverBase(ABC):
    """Abstract base class for observers."""

    @abstractmethod
    def update(self, asistencia):
        """Method called when the observed subject emits an event."""
        pass


class EstudianteNotificacionObserver(ObserverBase):
    """
    Observer that automatically creates a Notification (CU08)
    whenever attendance or performance score is recorded/updated (CU03/CU05).
    """

    def update(self, asistencia):
        from src.models.notificaciones import Notificacion

        estado = "PRESENTE" if asistencia.estado_presente else "AUSENTE"
        calificacion = f"{asistencia.puntaje:.1f}" if asistencia.puntaje is not None else "Sin evaluación"
        
        sesion = asistencia.id_sesion
        disciplina_nombre = sesion.id_disciplina.nombre if sesion and sesion.id_disciplina else "Disciplina deportiva"
        fecha_str = str(sesion.fecha) if sesion else "fecha reciente"

        mensaje = (
            f"Evaluación registrada en {disciplina_nombre} ({fecha_str}): "
            f"Asistencia: {estado} | Puntaje de rendimiento: {calificacion}."
        )

        notificacion = Notificacion.objects.create(
            rut_estudiante=asistencia.rut_estudiante,
            mensaje=mensaje,
            leida=False,
        )
        return notificacion


class EvaluacionSubject:
    """Subject that maintains registered observers and notifies them on events."""

    def __init__(self):
        self._observers = []

    def attach(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        try:
            self._observers.remove(observer)
        except ValueError:
            pass

    def notify(self, asistencia):
        results = []
        for observer in self._observers:
            res = observer.update(asistencia)
            results.append(res)
        return results


# Global subject pre-wired with default observer
evaluacion_subject = EvaluacionSubject()
evaluacion_subject.attach(EstudianteNotificacionObserver())


# ---------------------------------------------------------------------------
# 4. Adapter — IntranetAcademicaAdapter
# ---------------------------------------------------------------------------

class IntranetAcademicaAdapter:
    """
    Adapter pattern to transform internal SGAD models (Estudiante, Asistencia)
    into an interoperable JSON schema compliant with external Institutional Academic Intranets.
    """

    @staticmethod
    def adaptar_estudiante(usuario):
        """Adapt internal Usuario to academic student schema."""
        return {
            'schema_version': '2.0-ACADEMIC',
            'sistema_origen': 'SGAD-DEPORTES',
            'tipo_registro': 'ALUMNO_REGULAR',
            'identificacion': {
                'rut': usuario.rut,
                'matricula': usuario.matricula,
            },
            'datos_personales': {
                'nombre_completo': f"{usuario.nombre} {usuario.apellido}",
                'email_institucional': usuario.correo,
            },
            'perfil_academico': {
                'rol': usuario.id_perfil.nombre_perfil if usuario.id_perfil else 'ESTUDIANTE',
                'estado': 'ACTIVO',
            },
        }

    @staticmethod
    def adaptar_asistencia(asistencia):
        """Adapt internal Asistencia to academic performance schema."""
        sesion = asistencia.id_sesion
        return {
            'id_registro_deportivo': asistencia.id_asistencia,
            'actividad': {
                'id_sesion': sesion.id_sesion if sesion else None,
                'fecha': str(sesion.fecha) if sesion else None,
                'disciplina': sesion.id_disciplina.nombre if sesion and sesion.id_disciplina else None,
                'lugar': sesion.lugar if sesion else None,
            },
            'estudiante': {
                'rut': asistencia.rut_estudiante.rut if asistencia.rut_estudiante else None,
                'nombre': f"{asistencia.rut_estudiante.nombre} {asistencia.rut_estudiante.apellido}" if asistencia.rut_estudiante else None,
            },
            'registro_academico': {
                'asistio': asistencia.estado_presente,
                'calificacion_rendimiento': float(asistencia.puntaje) if asistencia.puntaje is not None else None,
                'escala_evaluacion': '1.0-7.0 (Reglamento Académico)',
                'condicion': 'APROBADO' if (asistencia.puntaje and asistencia.puntaje >= Decimal('4.0')) else 'PENDIENTE',
            },
        }

    @staticmethod
    def adaptar_reporte_completo(estudiante, asistencias):
        """Adapt a student with all their attendance records into full academic dossier."""
        return {
            'estudiante': IntranetAcademicaAdapter.adaptar_estudiante(estudiante),
            'historial_asistencias': [
                IntranetAcademicaAdapter.adaptar_asistencia(a) for a in asistencias
            ],
            'total_sesiones_computadas': len(asistencias),
        }
