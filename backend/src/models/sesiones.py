from django.db import models

from src.models.disciplinas import Disciplina
from src.models.usuarios import Usuario


class Sesion(models.Model):
    id_sesion = models.AutoField(primary_key=True)
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    lugar = models.CharField(max_length=200)
    id_disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        db_column='id_disciplina',
        related_name='sesiones',
    )
    rut_entrenador = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='rut_entrenador',
        related_name='sesiones_asignadas',
    )

    class Meta:
        db_table = 'sesiones'
        verbose_name = 'Sesión'
        verbose_name_plural = 'Sesiones'

    def __str__(self):
        return f"Sesión {self.id_sesion}: {self.fecha} - {self.id_disciplina}"
