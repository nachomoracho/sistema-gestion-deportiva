import pytest
from rest_framework.exceptions import ValidationError

from src.models.disciplinas import Disciplina
from src.models.inscripciones import Inscripcion
from src.controllers.serializers import InscripcionSerializer


class TestCuposTransaccional:
    def test_inscripcion_dentro_del_cupo(self, estudiante_user):
        disc = Disciplina.objects.create(nombre="Tenis", cupo_maximo=2)
        serializer = InscripcionSerializer(data={
            'rut_estudiante': estudiante_user.rut,
            'id_disciplina': disc.id_disciplina,
        })
        assert serializer.is_valid(), serializer.errors
        insc = serializer.save()
        assert insc.id_inscripcion is not None
        assert disc.inscripciones.count() == 1

    def test_inscripcion_rechaza_exceder_cupo_maximo(self, estudiante_user, estudiante_user_2):
        disc = Disciplina.objects.create(nombre="Ajedrez", cupo_maximo=1)

        # Inscribe 1st student (uses the 1 available slot)
        Inscripcion.objects.create(rut_estudiante=estudiante_user, id_disciplina=disc)
        assert disc.inscripciones.count() == 1

        # Attempt to inscribe 2nd student
        serializer = InscripcionSerializer(data={
            'rut_estudiante': estudiante_user_2.rut,
            'id_disciplina': disc.id_disciplina,
        })
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "No hay cupos disponibles" in str(exc.value)

    def test_duplicidad_inscripcion_rechazada(self, estudiante_user):
        disc = Disciplina.objects.create(nombre="Rugby", cupo_maximo=30)
        Inscripcion.objects.create(rut_estudiante=estudiante_user, id_disciplina=disc)

        # Attempt to inscribe again
        serializer = InscripcionSerializer(data={
            'rut_estudiante': estudiante_user.rut,
            'id_disciplina': disc.id_disciplina,
        })
        with pytest.raises(ValidationError) as exc:
            serializer.is_valid(raise_exception=True)
        assert "ya se encuentra inscrito" in str(exc.value)
