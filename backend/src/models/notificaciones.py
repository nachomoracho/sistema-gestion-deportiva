from django.db import models

from src.models.usuarios import Usuario


class Notificacion(models.Model):
    id_notificacion = models.AutoField(primary_key=True)
    rut_estudiante = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        db_column='rut_estudiante',
        related_name='notificaciones',
    )
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notificaciones'
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Notificación {self.id_notificacion} para {self.rut_estudiante}"
