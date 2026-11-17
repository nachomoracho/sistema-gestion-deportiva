import pytest
from decimal import Decimal
from django.contrib.auth.hashers import check_password

from src.models.perfiles import Perfil
from src.models.disciplinas import Disciplina
from src.models.sesiones import Sesion
from src.models.asistencia import Asistencia
from src.models.notificaciones import Notificacion
from src.services.patterns import (
    ConexionOracleSingleton,
    UsuarioFactory,
    EvaluacionSubject,
    EstudianteNotificacionObserver,
    IntranetAcademicaAdapter,
)


class TestSingletonPattern:
    def test_singleton_misma_instancia(self):
        ConexionOracleSingleton.reset()
        c1 = ConexionOracleSingleton()
        c2 = ConexionOracleSingleton()
        assert c1 is c2

    def test_singleton_inicializacion_parametros(self):
        ConexionOracleSingleton.reset()
        pool = ConexionOracleSingleton()
        pool.initialize(dsn="db.oracle.corp:1521/PROD", user="sec_admin", pool_min=4, pool_max=20)
        assert pool.is_initialized is True
        assert pool.dsn == "db.oracle.corp:1521/PROD"
        assert pool.user == "sec_admin"
        assert pool.pool_min == 4
        assert pool.pool_max == 20

    def test_singleton_consulta_parametrizada(self):
        pool = ConexionOracleSingleton()
        res = pool.ejecutar_consulta_segura("SELECT * FROM usuarios WHERE rut = :1", params=["11111111-1"])
        assert res["status"] == "SUCCESS"
        assert res["params_count"] == 1


class TestFactoryPattern:
    def test_crear_coordinador(self, perfiles):
        user = UsuarioFactory.crear_usuario(
            perfil_nombre=Perfil.COORDINADOR,
            rut="11111111-1",
            nombre="Juan",
            apellido="Perez",
            correo="juan@test.cl",
            clave="Secret2026!#Segura",
        )
        assert user.rut == "11111111-1"
        assert user.id_perfil.nombre_perfil == Perfil.COORDINADOR
        assert check_password("Secret2026!#Segura", user.clave)

    def test_crear_entrenador_requiere_especialidad(self, perfiles):
        with pytest.raises(ValueError, match="especialidad"):
            UsuarioFactory.crear_usuario(
                perfil_nombre=Perfil.ENTRENADOR,
                rut="22222222-2",
                nombre="Entrenador",
                apellido="SinEspecialidad",
                correo="ent@test.cl",
                clave="Coach2026!#Segura",
                especialidad=None,
            )

    def test_crear_estudiante_requiere_matricula(self, perfiles):
        with pytest.raises(ValueError, match="matricula"):
            UsuarioFactory.crear_usuario(
                perfil_nombre=Perfil.ESTUDIANTE,
                rut="33333333-3",
                nombre="Alumno",
                apellido="SinMatricula",
                correo="alum@test.cl",
                clave="Alumno2026!#Segura",
                matricula=None,
            )


class TestObserverPattern:
    def test_observer_crea_notificacion_al_evaluar(self, estudiante_user, entrenador_user):
        disc = Disciplina.objects.create(nombre="Voleibol Test", cupo_maximo=10)
        sesion = Sesion.objects.create(
            fecha="2026-11-20",
            hora_inicio="12:00:00",
            lugar="Gimnasio Central",
            id_disciplina=disc,
            rut_entrenador=entrenador_user,
        )

        asistencia = Asistencia.objects.create(
            id_sesion=sesion,
            rut_estudiante=estudiante_user,
            estado_presente=True,
            puntaje=Decimal("6.5"),
        )

        subject = EvaluacionSubject()
        observer = EstudianteNotificacionObserver()
        subject.attach(observer)

        subject.notify(asistencia)

        # Verify notification was generated for the student (CU08)
        notif = Notificacion.objects.filter(rut_estudiante=estudiante_user).first()
        assert notif is not None
        assert "Voleibol Test" in notif.mensaje
        assert "PRESENTE" in notif.mensaje
        assert "6.5" in notif.mensaje
        assert notif.leida is False


class TestAdapterPattern:
    def test_adapter_esquema_estudiante(self, estudiante_user):
        adapted = IntranetAcademicaAdapter.adaptar_estudiante(estudiante_user)
        assert adapted['schema_version'] == '2.0-ACADEMIC'
        assert adapted['identificacion']['rut'] == estudiante_user.rut
        assert adapted['identificacion']['matricula'] == estudiante_user.matricula
        assert adapted['datos_personales']['email_institucional'] == estudiante_user.correo

    def test_adapter_esquema_asistencia(self, estudiante_user, entrenador_user):
        disc = Disciplina.objects.create(nombre="Natación", cupo_maximo=12)
        sesion = Sesion.objects.create(
            fecha="2026-11-21",
            hora_inicio="16:00:00",
            lugar="Piscina Olímpica",
            id_disciplina=disc,
            rut_entrenador=entrenador_user,
        )
        asist = Asistencia.objects.create(
            id_sesion=sesion,
            rut_estudiante=estudiante_user,
            estado_presente=True,
            puntaje=Decimal("5.8"),
        )

        adapted = IntranetAcademicaAdapter.adaptar_asistencia(asist)
        assert adapted['actividad']['disciplina'] == 'Natación'
        assert adapted['estudiante']['rut'] == estudiante_user.rut
        assert adapted['registro_academico']['asistio'] is True
        assert adapted['registro_academico']['calificacion_rendimiento'] == 5.8
        assert adapted['registro_academico']['condicion'] == 'APROBADO'
