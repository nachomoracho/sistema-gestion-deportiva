from django.core.exceptions import ValidationError
from django.db import models

from src.models.perfiles import Perfil
from src.utils.validators import validar_rut


class Usuario(models.Model):
    rut = models.CharField(
        max_length=12,
        primary_key=True,
        validators=[validar_rut],
    )
    id_perfil = models.ForeignKey(
        Perfil,
        on_delete=models.CASCADE,
        db_column='id_perfil',
    )
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.EmailField(unique=True)
    clave = models.CharField(max_length=255)  # Argon2id hash
    especialidad = models.CharField(max_length=100, null=True, blank=True)
    matricula = models.CharField(max_length=20, unique=True, null=True, blank=True)
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)
    debe_cambiar_clave = models.BooleanField(default=False)

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def clean(self):
        super().clean()
        nombre_perfil = None
        if hasattr(self, 'id_perfil') and self.id_perfil:
            nombre_perfil = self.id_perfil.nombre_perfil

        if nombre_perfil == Perfil.ENTRENADOR and not self.especialidad:
            raise ValidationError({
                'especialidad': 'La especialidad es obligatoria para el perfil Entrenador.',
            })
        if nombre_perfil == Perfil.ESTUDIANTE and not self.matricula:
            raise ValidationError({
                'matricula': 'La matrícula es obligatoria para el perfil Estudiante.',
            })

    @property
    def is_authenticated(self):
        """Always return True for authenticated Usuario instances."""
        return True

    @property
    def is_anonymous(self):
        """Always return False for Usuario instances."""
        return False

    @property
    def is_active(self):
        """Account is active if not blocked permanently."""
        return True

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.rut})"
