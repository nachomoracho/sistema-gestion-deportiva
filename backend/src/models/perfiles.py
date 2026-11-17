from django.db import models


class Perfil(models.Model):
    COORDINADOR = 'COORDINADOR'
    ENTRENADOR = 'ENTRENADOR'
    ESTUDIANTE = 'ESTUDIANTE'
    PERFIL_CHOICES = [
        (COORDINADOR, 'Coordinador'),
        (ENTRENADOR, 'Entrenador'),
        (ESTUDIANTE, 'Estudiante'),
    ]

    id_perfil = models.AutoField(primary_key=True)
    nombre_perfil = models.CharField(max_length=20, unique=True, choices=PERFIL_CHOICES)

    class Meta:
        db_table = 'perfiles'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'

    def __str__(self):
        return self.nombre_perfil
