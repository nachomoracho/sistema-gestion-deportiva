from django.db import models


class AuditoriaLog(models.Model):
    id_log = models.AutoField(primary_key=True)
    rut_actor = models.CharField(max_length=12)
    accion = models.CharField(max_length=200)
    endpoint = models.CharField(max_length=500, blank=True, default='')
    codigo_http = models.IntegerField()
    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'auditoria_logs'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        ordering = ['-fecha_evento']

    def __str__(self):
        return f"[{self.fecha_evento}] {self.rut_actor}: {self.accion} ({self.codigo_http})"
