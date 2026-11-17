from django.core.validators import MinValueValidator
from django.db import models


class Disciplina(models.Model):
    id_disciplina = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100, unique=True)
    cupo_maximo = models.PositiveIntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'disciplinas'
        verbose_name = 'Disciplina'
        verbose_name_plural = 'Disciplinas'

    def __str__(self):
        return self.nombre
