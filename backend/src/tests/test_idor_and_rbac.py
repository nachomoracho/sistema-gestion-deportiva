import pytest
from rest_framework.test import APIClient
from rest_framework import status

from src.models.disciplinas import Disciplina
from src.models.sesiones import Sesion
from src.models.notificaciones import Notificacion
from src.services.auth_service import AuthService


class TestRbacAndIdor:
    def test_estudiante_no_puede_crear_disciplina_403(self, estudiante_user):
        client = APIClient()
        auth = AuthService.authenticate("33333333-3", "Alumno2026!#Segura")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth['access']}")

        response = client.post('/api/disciplinas/', {
            'nombre': 'Natación Ilegal',
            'cupo_maximo': 20,
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_entrenador_no_puede_registrar_asistencia_en_sesion_ajena_idor(self, entrenador_user, entrenador_user_2, estudiante_user):
        disc = Disciplina.objects.create(nombre="Crossfit", cupo_maximo=15)
        # Session assigned to coach 1
        sesion_coach_1 = Sesion.objects.create(
            fecha="2026-11-25",
            hora_inicio="09:00:00",
            lugar="Sala B",
            id_disciplina=disc,
            rut_entrenador=entrenador_user,
        )

        # Login as coach 2
        client = APIClient()
        auth = AuthService.authenticate(entrenador_user_2.rut, "Coach2026!#Segura")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth['access']}")

        # Coach 2 tries to submit bulk attendance on Coach 1's session
        response = client.post('/api/asistencia/bulk_guardar/', {
            'id_sesion': sesion_coach_1.id_sesion,
            'asistencias': [
                {
                    'rut_estudiante': estudiante_user.rut,
                    'estado_presente': True,
                    'puntaje': 7.0,
                }
            ]
        }, format='json')

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "No tiene autorización" in response.data['mensaje']

    def test_estudiante_solo_ve_sus_propias_notificaciones(self, estudiante_user, estudiante_user_2):
        # Create notification for student 2
        Notificacion.objects.create(
            rut_estudiante=estudiante_user_2,
            mensaje="Mensaje privado para estudiante 2",
        )

        client = APIClient()
        auth = AuthService.authenticate(estudiante_user.rut, "Alumno2026!#Segura")
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {auth['access']}")

        response = client.get('/api/notificaciones/')
        assert response.status_code == status.HTTP_200_OK
        # Student 1 must see 0 notifications
        assert len(response.data.get('results', response.data)) == 0
