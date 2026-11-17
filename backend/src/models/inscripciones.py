from django.db import models

from src.models.disciplinas import Disciplina
from src.models.usuarios import Usuario


class Inscripcion(models.Model):
    id_inscripcion = models.AutoField(primary_key=True)
    rut_estudiante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='rut_estudiante',
        related_name='inscripciones',
    )
    id_disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='id_disciplina',
        related_name='inscripciones',
    )
    fecha_inscripcion = models.DateField(auto_now_add=True)

    class Meta:
        db_table = 'inscripciones'
        verbose_name = 'Inscripción'
        verbose_name_plural = 'Inscripciones'
        constraints = [
            models.UniqueConstraint(
                fields=['rut_estudiante', 'id_disciplina'],
                name='unique_inscripcion',
            ),
        ]

    def __str__(self):
        return f"Inscripción {self.id_inscripcion}: {self.rut_estudiante} -> {self.id_disciplina}"
