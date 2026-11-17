from decimal import Decimal

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from src.models.sesiones import Sesion
from src.models.usuarios import Usuario


class Asistencia(models.Model):
    id_asistencia = models.AutoField(primary_key=True)
    estado_presente = models.BooleanField(default=False)
    puntaje = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        null=True,
        blank=True,
        validators=[
            MinValueValidator(Decimal('1.0')),
            MaxValueValidator(Decimal('7.0')),
        ],
    )
    id_sesion = models.ForeignKey(
        Sesion,
        on_delete=models.CASCADE,
        db_column='id_sesion',
        related_name='asistencias',
    )
    rut_estudiante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='rut_estudiante',
        related_name='asistencias',
    )

    class Meta:
        db_table = 'asistencia'
        verbose_name = 'Asistencia'
        verbose_name_plural = 'Asistencias'
        constraints = [
            models.UniqueConstraint(
                fields=['id_sesion', 'rut_estudiante'],
                name='unique_asistencia',
            ),
        ]

    def __str__(self):
        return f"Asistencia {self.id_asistencia}: {self.rut_estudiante} en sesión {self.id_sesion}"
