from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from src.models.disciplinas import Disciplina
from src.models.inscripciones import Inscripcion
from src.models.sesiones import Sesion
from src.models.asistencia import Asistencia
from src.models.notificaciones import Notificacion
from src.services.auth_service import AuthService


class TestIntegrationFlowCU01ToCU08:
    def test_flujo_completo_ciclo_deportivo(self, coordinador_user, entrenador_user, estudiante_user):
        # 1. CU04: Autenticación de Coordinador
        auth_coord = AuthService.authenticate(coordinador_user.rut, "Admin2026!#Segura")
        client_coord = APIClient()
        client_coord.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_coord['access']}")

        # 2. CU01: Crear Disciplina
        res_disc = client_coord.post('/api/disciplinas/', {
            'nombre': 'Atletismo E2E',
            'cupo_maximo': 25,
        }, format='json')
        assert res_disc.status_code == status.HTTP_201_CREATED
        id_disciplina = res_disc.data['id_disciplina']

        # 3. CU02: Inscribir Estudiante
        res_insc = client_coord.post('/api/inscripciones/', {
            'rut_estudiante': estudiante_user.rut,
            'id_disciplina': id_disciplina,
        }, format='json')
        assert res_insc.status_code == status.HTTP_201_CREATED

        # 4. Programar Sesión asignada al Entrenador
        res_ses = client_coord.post('/api/sesiones/', {
            'fecha': '2026-11-30',
            'hora_inicio': '08:30:00',
            'lugar': 'Pista Atlética 1',
            'id_disciplina': id_disciplina,
            'rut_entrenador': entrenador_user.rut,
        }, format='json')
        assert res_ses.status_code == status.HTTP_201_CREATED
        id_sesion = res_ses.data['id_sesion']

        # 5. CU04: Autenticación de Entrenador
        auth_coach = AuthService.authenticate(entrenador_user.rut, "Coach2026!#Segura")
        client_coach = APIClient()
        client_coach.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_coach['access']}")

        # Consultar nómina de la sesión (Mobile-friendly)
        res_nomina = client_coach.get(f'/api/sesiones/{id_sesion}/nomina_estudiantes/')
        assert res_nomina.status_code == status.HTTP_200_OK
        assert len(res_nomina.data['estudiantes']) == 1
        assert res_nomina.data['estudiantes'][0]['rut'] == estudiante_user.rut

        # 6. CU03 & CU05: Registrar Asistencia y Evaluación (Bulk)
        res_bulk = client_coach.post('/api/asistencia/bulk_guardar/', {
            'id_sesion': id_sesion,
            'asistencias': [
                {
                    'rut_estudiante': estudiante_user.rut,
                    'estado_presente': True,
                    'puntaje': 6.7,
                }
            ]
        }, format='json')
        assert res_bulk.status_code == status.HTTP_200_OK
        assert res_bulk.data['total_procesados'] == 1

        # 7. CU08: Verificar disparo automático del patrón Observer
        notificaciones = Notificacion.objects.filter(rut_estudiante=estudiante_user)
        assert notificaciones.exists()
        notif = notificaciones.first()
        assert "Atletismo E2E" in notif.mensaje
        assert "6.7" in notif.mensaje

        # 8. CU04, CU06 & CU07: Autenticación y Consulta Portal Estudiante
        auth_estud = AuthService.authenticate(estudiante_user.rut, "Alumno2026!#Segura")
        client_estud = APIClient()
        client_estud.credentials(HTTP_AUTHORIZATION=f"Bearer {auth_estud['access']}")

        res_portal = client_estud.get('/api/estudiantes/mi-portal/')
        assert res_portal.status_code == status.HTTP_200_OK
        metricas = res_portal.data['metricas']
        assert metricas['total_sesiones'] == 1
        assert metricas['total_presente'] == 1
        assert metricas['porcentaje_asistencia'] == 100.0
        assert metricas['alerta_riesgo'] is False
        assert metricas['promedio_rendimiento'] == 6.7

        # 9. RF05: Consulta y Exportación CSV por Coordinador
        res_rep = client_coord.get(f'/api/reportes/?id_disciplina={id_disciplina}')
        assert res_rep.status_code == status.HTTP_200_OK
        assert res_rep.data['resumen']['total_registros'] == 1
        assert res_rep.data['resumen']['porcentaje_asistencia'] == 100.0

        res_csv = client_coord.get(f'/api/reportes/?id_disciplina={id_disciplina}&export=csv')
        assert res_csv.status_code == status.HTTP_200_OK
        assert res_csv['Content-Type'].startswith('text/csv')
        assert 'Atletismo E2E' in res_csv.content.decode('utf-8')
