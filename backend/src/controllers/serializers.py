from decimal import Decimal
from django.db import transaction
from rest_framework import serializers

from src.models.perfiles import Perfil
from src.models.usuarios import Usuario
from src.models.disciplinas import Disciplina
from src.models.inscripciones import Inscripcion
from src.models.sesiones import Sesion
from src.models.asistencia import Asistencia
from src.models.notificaciones import Notificacion
from src.models.auditoria import AuditoriaLog
from src.services.patterns import UsuarioFactory, evaluacion_subject
from src.utils.sanitizers import sanitize_input
from src.utils.validators import validar_rut, validar_password_strength


# ---------------------------------------------------------------------------
# Auth Serializers
# ---------------------------------------------------------------------------

class LoginSerializer(serializers.Serializer):
    rut_o_correo = serializers.CharField(required=True, max_length=150)
    clave = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_rut_o_correo(self, value):
        return sanitize_input(value, field_name='rut_o_correo')

    def validate(self, attrs):
        if not attrs.get('rut_o_correo') or not attrs.get('clave'):
            raise serializers.ValidationError('Debe proporcionar identificación y contraseña.')
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    clave_actual = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    clave_nueva = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_clave_nueva(self, value):
        validar_password_strength(value)
        return value


# ---------------------------------------------------------------------------
# Perfil Serializer
# ---------------------------------------------------------------------------

class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = ['id_perfil', 'nombre_perfil']


# ---------------------------------------------------------------------------
# Usuario Serializer
# ---------------------------------------------------------------------------

class UsuarioSerializer(serializers.ModelSerializer):
    perfil_nombre = serializers.CharField(source='id_perfil.nombre_perfil', read_only=True)
    clave = serializers.CharField(write_only=True, required=False, style={'input_type': 'password'})

    class Meta:
        model = Usuario
        fields = [
            'rut', 'id_perfil', 'perfil_nombre', 'nombre', 'apellido', 'correo',
            'clave', 'especialidad', 'matricula', 'intentos_fallidos',
            'bloqueado_hasta', 'debe_cambiar_clave'
        ]
        read_only_fields = ['intentos_fallidos', 'bloqueado_hasta']

    def validate_rut(self, value):
        cleaned = sanitize_input(value, field_name='rut')
        validar_rut(cleaned)
        return cleaned.upper()

    def validate_nombre(self, value):
        return sanitize_input(value, field_name='nombre')

    def validate_apellido(self, value):
        return sanitize_input(value, field_name='apellido')

    def validate_especialidad(self, value):
        if value:
            return sanitize_input(value, field_name='especialidad')
        return value

    def validate_matricula(self, value):
        if value:
            return sanitize_input(value, field_name='matricula')
        return value

    def create(self, validated_data):
        clave = validated_data.pop('clave', 'Temporal2026!#Segura')
        perfil = validated_data.pop('id_perfil')
        
        # Polymorphic creation through UsuarioFactory pattern
        usuario = UsuarioFactory.crear_usuario(
            perfil_nombre=perfil.nombre_perfil,
            rut=validated_data.get('rut'),
            nombre=validated_data.get('nombre'),
            apellido=validated_data.get('apellido'),
            correo=validated_data.get('correo'),
            clave=clave,
            especialidad=validated_data.get('especialidad'),
            matricula=validated_data.get('matricula'),
            debe_cambiar_clave=validated_data.get('debe_cambiar_clave', True),
        )
        return usuario


# ---------------------------------------------------------------------------
# Disciplina Serializer
# ---------------------------------------------------------------------------

class DisciplinaSerializer(serializers.ModelSerializer):
    cupos_ocupados = serializers.SerializerMethodField()
    cupos_disponibles = serializers.SerializerMethodField()

    class Meta:
        model = Disciplina
        fields = ['id_disciplina', 'nombre', 'cupo_maximo', 'cupos_ocupados', 'cupos_disponibles']

    def validate_nombre(self, value):
        return sanitize_input(value, field_name='nombre')

    def validate_cupo_maximo(self, value):
        if value <= 0:
            raise serializers.ValidationError('El cupo máximo debe ser mayor que cero.')
        if value > 500:
            raise serializers.ValidationError('El cupo máximo no puede exceder 500.')
        return value

    def get_cupos_ocupados(self, obj):
        return obj.inscripciones.count()

    def get_cupos_disponibles(self, obj):
        return max(0, obj.cupo_maximo - obj.inscripciones.count())


# ---------------------------------------------------------------------------
# Inscripcion Serializer
# ---------------------------------------------------------------------------

class InscripcionSerializer(serializers.ModelSerializer):
    estudiante_detalle = serializers.SerializerMethodField()
    disciplina_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Inscripcion
        fields = ['id_inscripcion', 'rut_estudiante', 'id_disciplina', 'fecha_inscripcion', 'estudiante_detalle', 'disciplina_detalle']
        read_only_fields = ['id_inscripcion', 'fecha_inscripcion']

    def get_estudiante_detalle(self, obj):
        est = obj.rut_estudiante
        return {
            'rut': est.rut,
            'nombre_completo': f"{est.nombre} {est.apellido}",
            'matricula': est.matricula,
            'correo': est.correo,
        }

    def get_disciplina_detalle(self, obj):
        disc = obj.id_disciplina
        return {
            'id_disciplina': disc.id_disciplina,
            'nombre': disc.nombre,
            'cupo_maximo': disc.cupo_maximo,
        }

    def validate(self, attrs):
        rut_estudiante = attrs.get('rut_estudiante')
        id_disciplina = attrs.get('id_disciplina')

        # 1. Enforce student role
        if rut_estudiante.id_perfil.nombre_perfil != Perfil.ESTUDIANTE:
            raise serializers.ValidationError({'rut_estudiante': 'Solo usuarios con perfil ESTUDIANTE pueden ser inscritos.'})

        # 2. Check duplicate enrollment
        if Inscripcion.objects.filter(rut_estudiante=rut_estudiante, id_disciplina=id_disciplina).exists():
            raise serializers.ValidationError({'non_field_errors': ['El estudiante ya se encuentra inscrito en esta disciplina.']})

        # 3. Transactional atomic cupo check (CU02 / RNF02)
        with transaction.atomic():
            disciplina_locked = Disciplina.objects.select_for_update().get(pk=id_disciplina.pk)
            total_inscritos = Inscripcion.objects.filter(id_disciplina=disciplina_locked).count()
            if total_inscritos >= disciplina_locked.cupo_maximo:
                raise serializers.ValidationError({
                    'id_disciplina': f"No hay cupos disponibles en '{disciplina_locked.nombre}'. Cupo máximo: {disciplina_locked.cupo_maximo} alcanzado."
                })

        return attrs


# ---------------------------------------------------------------------------
# Sesion Serializer
# ---------------------------------------------------------------------------

class SesionSerializer(serializers.ModelSerializer):
    disciplina_nombre = serializers.CharField(source='id_disciplina.nombre', read_only=True)
    entrenador_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Sesion
        fields = ['id_sesion', 'fecha', 'hora_inicio', 'lugar', 'id_disciplina', 'rut_entrenador', 'disciplina_nombre', 'entrenador_nombre']

    def get_entrenador_nombre(self, obj):
        return f"{obj.rut_entrenador.nombre} {obj.rut_entrenador.apellido} ({obj.rut_entrenador.especialidad or 'Sin especialidad'})"

    def validate_lugar(self, value):
        return sanitize_input(value, field_name='lugar')

    def validate_rut_entrenador(self, value):
        if value.id_perfil.nombre_perfil != Perfil.ENTRENADOR:
            raise serializers.ValidationError('El usuario asignado debe tener perfil ENTRENADOR.')
        return value


# ---------------------------------------------------------------------------
# Asistencia Serializer
# ---------------------------------------------------------------------------

class AsistenciaSerializer(serializers.ModelSerializer):
    estudiante_nombre = serializers.SerializerMethodField()
    disciplina_nombre = serializers.CharField(source='id_sesion.id_disciplina.nombre', read_only=True)
    fecha_sesion = serializers.DateField(source='id_sesion.fecha', read_only=True)

    class Meta:
        model = Asistencia
        fields = [
            'id_asistencia', 'id_sesion', 'rut_estudiante', 'estado_presente',
            'puntaje', 'estudiante_nombre', 'disciplina_nombre', 'fecha_sesion'
        ]

    def get_estudiante_nombre(self, obj):
        return f"{obj.rut_estudiante.nombre} {obj.rut_estudiante.apellido}"

    def validate_puntaje(self, value):
        if value is not None:
            if value < Decimal('1.0') or value > Decimal('7.0'):
                raise serializers.ValidationError('El puntaje debe estar comprendido entre 1.0 y 7.0.')
        return value

    def save(self, **kwargs):
        # Save attendance record
        instance = super().save(**kwargs)

        # Trigger Observer pattern (CU08 - EstudianteNotificacionObserver)
        try:
            evaluacion_subject.notify(instance)
        except Exception:
            pass  # Fail-safe, attendance was persisted

        return instance


class AsistenciaBulkItemSerializer(serializers.Serializer):
    rut_estudiante = serializers.CharField(max_length=12)
    estado_presente = serializers.BooleanField(default=False)
    puntaje = serializers.DecimalField(max_digits=3, decimal_places=1, required=False, allow_null=True)

    def validate_puntaje(self, value):
        if value is not None:
            if value < Decimal('1.0') or value > Decimal('7.0'):
                raise serializers.ValidationError('Puntaje debe estar entre 1.0 y 7.0.')
        return value


class AsistenciaBulkSerializer(serializers.Serializer):
    id_sesion = serializers.IntegerField()
    asistencias = AsistenciaBulkItemSerializer(many=True)


# ---------------------------------------------------------------------------
# Notificacion Serializer
# ---------------------------------------------------------------------------

class NotificacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacion
        fields = ['id_notificacion', 'rut_estudiante', 'mensaje', 'leida', 'fecha_creacion']
        read_only_fields = ['id_notificacion', 'fecha_creacion']


# ---------------------------------------------------------------------------
# AuditoriaLog Serializer
# ---------------------------------------------------------------------------

class AuditoriaLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditoriaLog
        fields = ['id_log', 'rut_actor', 'accion', 'endpoint', 'codigo_http', 'fecha_evento']
        read_only_fields = ['id_log', 'fecha_evento']
