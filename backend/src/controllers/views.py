import csv
from decimal import Decimal
from django.db import transaction
from django.db.models import Avg, Count, Q
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from src.controllers.permissions import (
    IsCoordinador,
    IsEntrenador,
    IsEstudiante,
    IsCoordinadorOrEntrenador,
    IsOwnerOrAssignedStaff,
)
from src.controllers.serializers import (
    LoginSerializer,
    ChangePasswordSerializer,
    PerfilSerializer,
    UsuarioSerializer,
    DisciplinaSerializer,
    InscripcionSerializer,
    SesionSerializer,
    AsistenciaSerializer,
    AsistenciaBulkSerializer,
    NotificacionSerializer,
    AuditoriaLogSerializer,
)
from src.models.perfiles import Perfil
from src.models.usuarios import Usuario
from src.models.disciplinas import Disciplina
from src.models.inscripciones import Inscripcion
from src.models.sesiones import Sesion
from src.models.asistencia import Asistencia
from src.models.notificaciones import Notificacion
from src.models.auditoria import AuditoriaLog
from src.services.auth_service import AuthService, AuthenticationError, AccountLockedError
from src.services.patterns import evaluacion_subject, IntranetAcademicaAdapter
from src.utils.audit_logger import log_audit_event


# ---------------------------------------------------------------------------
# Auth Views
# ---------------------------------------------------------------------------

class LoginView(APIView):
    """
    Public login endpoint with brute-force protection and rate throttling.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rut_o_correo = serializer.validated_data['rut_o_correo']
        clave = serializer.validated_data['clave']
        client_ip = request.META.get('REMOTE_ADDR', '')

        try:
            auth_data = AuthService.authenticate(
                rut_or_email=rut_o_correo,
                clave=clave,
                request_ip=client_ip,
                endpoint=request.path,
            )
            return Response(auth_data, status=status.HTTP_200_OK)
        except AccountLockedError as e:
            return Response(
                {'error': True, 'codigo': 403, 'mensaje': str(e)},
                status=status.HTTP_403_FORBIDDEN,
            )
        except AuthenticationError as e:
            return Response(
                {'error': True, 'codigo': 401, 'mensaje': str(e)},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    """
    Secure logout endpoint. Logs event and instructs client to clear token.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        log_audit_event(
            rut_actor=request.user.rut,
            accion='CIERRE_DE_SESION_LOGOUT',
            endpoint=request.path,
            codigo_http=200,
        )
        return Response(
            {'mensaje': 'Sesión cerrada exitosamente.'},
            status=status.HTTP_200_OK,
        )


class ChangePasswordView(APIView):
    """
    Mandatory or voluntary password change endpoint.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clave_actual = serializer.validated_data['clave_actual']
        clave_nueva = serializer.validated_data['clave_nueva']

        try:
            AuthService.change_password(
                rut=request.user.rut,
                clave_actual=clave_actual,
                clave_nueva=clave_nueva,
                request_ip=request.META.get('REMOTE_ADDR', ''),
            )
            return Response(
                {'mensaje': 'Contraseña actualizada correctamente.'},
                status=status.HTTP_200_OK,
            )
        except AuthenticationError as e:
            return Response(
                {'error': True, 'codigo': 400, 'mensaje': str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class MeView(APIView):
    """
    Returns current authenticated user info.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Perfiles ViewSet (Dynamic Dropdown Support)
# ---------------------------------------------------------------------------

class PerfilViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Perfil.objects.all().order_by('id_perfil')
    serializer_class = PerfilSerializer
    permission_classes = [permissions.IsAuthenticated]


# ---------------------------------------------------------------------------
# Usuarios ViewSet (RBAC + Anti-IDOR)
# ---------------------------------------------------------------------------

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related('id_perfil').all().order_by('apellido', 'nombre')
    serializer_class = UsuarioSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedStaff]

    def get_queryset(self):
        user = self.request.user
        rol = user.id_perfil.nombre_perfil if user.id_perfil else None

        if rol == 'COORDINADOR':
            qs = Usuario.objects.select_related('id_perfil').all()
            perfil_filter = self.request.query_params.get('perfil')
            if perfil_filter:
                qs = qs.filter(id_perfil__nombre_perfil=perfil_filter.upper())
            return qs.order_by('apellido', 'nombre')

        if rol == 'ENTRENADOR':
            # Trainer can view students enrolled in their disciplines
            disciplina_ids = Sesion.objects.filter(rut_entrenador=user).values_list('id_disciplina', flat=True)
            estudiante_ruts = Inscripcion.objects.filter(id_disciplina__in=disciplina_ids).values_list('rut_estudiante', flat=True)
            return Usuario.objects.filter(Q(rut=user.rut) | Q(rut__in=estudiante_ruts)).distinct()

        # Student only sees self
        return Usuario.objects.filter(rut=user.rut)

    def create(self, request, *args, **kwargs):
        # Only Coordinador can create new users directly
        if not (request.user.id_perfil and request.user.id_perfil.nombre_perfil == 'COORDINADOR'):
            return Response(
                {'error': True, 'codigo': 403, 'mensaje': 'Solo el Coordinador puede registrar nuevos usuarios.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)


# ---------------------------------------------------------------------------
# Disciplinas ViewSet (RF02 / CU01)
# ---------------------------------------------------------------------------

class DisciplinaViewSet(viewsets.ModelViewSet):
    queryset = Disciplina.objects.all().order_by('nombre')
    serializer_class = DisciplinaSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCoordinador()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        disciplina = serializer.save()
        log_audit_event(
            rut_actor=self.request.user.rut,
            accion=f"CREAR_DISCIPLINA: {disciplina.nombre} (Cupo: {disciplina.cupo_maximo})",
            endpoint=self.request.path,
            codigo_http=201,
        )


# ---------------------------------------------------------------------------
# Inscripciones ViewSet (RF02 / CU02 / Anti-IDOR)
# ---------------------------------------------------------------------------

class InscripcionViewSet(viewsets.ModelViewSet):
    queryset = Inscripcion.objects.select_related('rut_estudiante', 'id_disciplina').all().order_by('-fecha_inscripcion')
    serializer_class = InscripcionSerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [permissions.IsAuthenticated(), IsCoordinador()]
        return [permissions.IsAuthenticated(), IsOwnerOrAssignedStaff()]

    def get_queryset(self):
        user = self.request.user
        rol = user.id_perfil.nombre_perfil if user.id_perfil else None

        if rol == 'COORDINADOR':
            qs = Inscripcion.objects.select_related('rut_estudiante', 'id_disciplina').all()
            disciplina_id = self.request.query_params.get('disciplina')
            if disciplina_id:
                qs = qs.filter(id_disciplina_id=disciplina_id)
            return qs.order_by('-fecha_inscripcion')

        if rol == 'ENTRENADOR':
            # Coach can see enrollments for their sessions
            disciplinas = Sesion.objects.filter(rut_entrenador=user).values_list('id_disciplina', flat=True)
            return Inscripcion.objects.filter(id_disciplina__in=disciplinas).select_related('rut_estudiante', 'id_disciplina')

        # Estudiante only sees their own
        return Inscripcion.objects.filter(rut_estudiante=user).select_related('rut_estudiante', 'id_disciplina')

    def perform_create(self, serializer):
        inscripcion = serializer.save()
        log_audit_event(
            rut_actor=self.request.user.rut,
            accion=f"INSCRIBIR_ESTUDIANTE: {inscripcion.rut_estudiante_id} en disciplina {inscripcion.id_disciplina.nombre}",
            endpoint=self.request.path,
            codigo_http=201,
        )


# ---------------------------------------------------------------------------
# Sesiones ViewSet (Anti-IDOR)
# ---------------------------------------------------------------------------

class SesionViewSet(viewsets.ModelViewSet):
    queryset = Sesion.objects.select_related('id_disciplina', 'rut_entrenador').all().order_by('fecha', 'hora_inicio')
    serializer_class = SesionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [permissions.IsAuthenticated(), IsCoordinadorOrEntrenador()]
        return [permissions.IsAuthenticated(), IsOwnerOrAssignedStaff()]

    def get_queryset(self):
        user = self.request.user
        rol = user.id_perfil.nombre_perfil if user.id_perfil else None

        if rol == 'COORDINADOR':
            return Sesion.objects.select_related('id_disciplina', 'rut_entrenador').all().order_by('fecha', 'hora_inicio')

        if rol == 'ENTRENADOR':
            return Sesion.objects.filter(rut_entrenador=user).select_related('id_disciplina', 'rut_entrenador').order_by('fecha', 'hora_inicio')

        # Estudiante: only sessions for disciplines the student is enrolled in
        disciplinas_inscritas = Inscripcion.objects.filter(rut_estudiante=user).values_list('id_disciplina', flat=True)
        return Sesion.objects.filter(id_disciplina__in=disciplinas_inscritas).select_related('id_disciplina', 'rut_entrenador').order_by('fecha', 'hora_inicio')

    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated, IsCoordinadorOrEntrenador])
    def nomina_estudiantes(self, request, pk=None):
        """
        Returns the student roster for this session's discipline, along with any existing attendance record.
        Optimized for the mobile coach panel.
        """
        sesion = self.get_object()

        # Enforce Anti-IDOR for Coach: must be assigned coach
        if request.user.id_perfil.nombre_perfil == 'ENTRENADOR' and sesion.rut_entrenador_id != request.user.rut:
            return Response(
                {'error': True, 'codigo': 403, 'mensaje': 'No tiene autorización sobre sesiones de otro docente.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        inscripciones = Inscripcion.objects.filter(id_disciplina=sesion.id_disciplina).select_related('rut_estudiante')
        asistencias_map = {
            a.rut_estudiante_id: a
            for a in Asistencia.objects.filter(id_sesion=sesion)
        }

        nomina = []
        for insc in inscripciones:
            est = insc.rut_estudiante
            asist = asistencias_map.get(est.rut)
            nomina.append({
                'rut': est.rut,
                'nombre_completo': f"{est.nombre} {est.apellido}",
                'matricula': est.matricula,
                'correo': est.correo,
                'estado_presente': asist.estado_presente if asist else False,
                'puntaje': float(asist.puntaje) if (asist and asist.puntaje is not None) else None,
                'id_asistencia': asist.id_asistencia if asist else None,
            })

        return Response({
            'sesion': SesionSerializer(sesion).data,
            'estudiantes': nomina,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Asistencia ViewSet (RF03 / CU03 / CU05 / CU08 Observer / Anti-IDOR)
# ---------------------------------------------------------------------------

class AsistenciaViewSet(viewsets.ModelViewSet):
    queryset = Asistencia.objects.select_related('id_sesion', 'rut_estudiante', 'id_sesion__id_disciplina').all()
    serializer_class = AsistenciaSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'bulk_guardar']:
            return [permissions.IsAuthenticated(), IsCoordinadorOrEntrenador()]
        return [permissions.IsAuthenticated(), IsOwnerOrAssignedStaff()]

    def get_queryset(self):
        user = self.request.user
        rol = user.id_perfil.nombre_perfil if user.id_perfil else None

        if rol == 'COORDINADOR':
            return Asistencia.objects.select_related('id_sesion', 'rut_estudiante', 'id_sesion__id_disciplina').all()

        if rol == 'ENTRENADOR':
            return Asistencia.objects.filter(id_sesion__rut_entrenador=user).select_related('id_sesion', 'rut_estudiante', 'id_sesion__id_disciplina')

        # Estudiante can only view their own attendance
        return Asistencia.objects.filter(rut_estudiante=user).select_related('id_sesion', 'rut_estudiante', 'id_sesion__id_disciplina').order_by('-id_sesion__fecha')

    def perform_create(self, serializer):
        sesion = serializer.validated_data['id_sesion']
        # Anti-IDOR check: trainer must own the session
        if self.request.user.id_perfil.nombre_perfil == 'ENTRENADOR' and sesion.rut_entrenador_id != self.request.user.rut:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No puede registrar asistencia en sesiones asignadas a otro entrenador.')

        asistencia = serializer.save()
        log_audit_event(
            rut_actor=self.request.user.rut,
            accion=f"REGISTRO_ASISTENCIA: Estudiante {asistencia.rut_estudiante_id} en sesión {asistencia.id_sesion_id} (Presente: {asistencia.estado_presente}, Nota: {asistencia.puntaje})",
            endpoint=self.request.path,
            codigo_http=201,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        if self.request.user.id_perfil.nombre_perfil == 'ENTRENADOR' and instance.id_sesion.rut_entrenador_id != self.request.user.rut:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('No puede modificar asistencia en sesiones asignadas a otro entrenador.')

        asistencia = serializer.save()
        log_audit_event(
            rut_actor=self.request.user.rut,
            accion=f"MODIFICACION_ASISTENCIA: ID {asistencia.id_asistencia} Estudiante {asistencia.rut_estudiante_id} (Presente: {asistencia.estado_presente}, Nota: {asistencia.puntaje})",
            endpoint=self.request.path,
            codigo_http=200,
        )

    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCoordinadorOrEntrenador])
    def bulk_guardar(self, request):
        """
        Batch-save attendance and scores for a session in a single transactional request.
        Dispatches the Observer pattern for all updated records.
        """
        serializer = AsistenciaBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        id_sesion = serializer.validated_data['id_sesion']
        try:
            sesion = Sesion.objects.select_related('id_disciplina', 'rut_entrenador').get(pk=id_sesion)
        except Sesion.DoesNotExist:
            return Response({'error': True, 'codigo': 404, 'mensaje': 'Sesión no encontrada.'}, status=status.HTTP_404_NOT_FOUND)

        # Anti-IDOR check
        if request.user.id_perfil.nombre_perfil == 'ENTRENADOR' and sesion.rut_entrenador_id != request.user.rut:
            log_audit_event(
                rut_actor=request.user.rut,
                accion=f"INTENTO_IDOR_BULK_ASISTENCIA en sesión {id_sesion}",
                endpoint=request.path,
                codigo_http=403,
            )
            return Response(
                {'error': True, 'codigo': 403, 'mensaje': 'No tiene autorización para registrar asistencia en sesiones de otro docente.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        items = serializer.validated_data['asistencias']
        actualizados = 0

        with transaction.atomic():
            for item in items:
                rut_est = item['rut_estudiante']
                try:
                    estudiante = Usuario.objects.get(rut=rut_est)
                except Usuario.DoesNotExist:
                    continue

                asistencia, created = Asistencia.objects.update_or_create(
                    id_sesion=sesion,
                    rut_estudiante=estudiante,
                    defaults={
                        'estado_presente': item.get('estado_presente', False),
                        'puntaje': item.get('puntaje'),
                    }
                )
                actualizados += 1

                # Disparar Observer (CU08)
                evaluacion_subject.notify(asistencia)

        log_audit_event(
            rut_actor=request.user.rut,
            accion=f"BULK_REGISTRO_ASISTENCIA: Sesión {id_sesion}, {actualizados} alumnos procesados",
            endpoint=request.path,
            codigo_http=200,
        )

        return Response({
            'mensaje': f'Asistencias y evaluaciones registradas exitosamente ({actualizados} estudiantes).',
            'id_sesion': id_sesion,
            'total_procesados': actualizados,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Notificaciones ViewSet (CU08 / Observer / Anti-IDOR)
# ---------------------------------------------------------------------------

class NotificacionViewSet(viewsets.ModelViewSet):
    serializer_class = NotificacionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAssignedStaff]

    def get_queryset(self):
        # Student strictly sees their own notifications
        return Notificacion.objects.filter(rut_estudiante=self.request.user).order_by('-fecha_creacion')

    @action(detail=True, methods=['post'])
    def marcar_leida(self, request, pk=None):
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save(update_fields=['leida'])
        return Response({'mensaje': 'Notificación marcada como leída.'}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def marcar_todas_leidas(self, request):
        actualizadas = Notificacion.objects.filter(rut_estudiante=request.user, leida=False).update(leida=True)
        return Response({'mensaje': f'{actualizadas} notificaciones marcadas como leídas.'}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Reportería Avanzada View (RF05 / Coordinador)
# ---------------------------------------------------------------------------

class ReportesAvanzadosView(APIView):
    """
    Advanced reporting engine with cross filters and CSV export.
    Restricted to COORDINADOR role.
    """
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]

    def get(self, request):
        rut_estudiante = request.query_params.get('rut_estudiante', '').strip().upper()
        id_disciplina = request.query_params.get('id_disciplina', '').strip()
        rut_entrenador = request.query_params.get('rut_entrenador', '').strip().upper()
        export_format = request.query_params.get('export', '').strip().lower()

        # Build filtered queryset for Asistencia
        qs = Asistencia.objects.select_related(
            'rut_estudiante', 'id_sesion', 'id_sesion__id_disciplina', 'id_sesion__rut_entrenador'
        ).all()

        if rut_estudiante:
            qs = qs.filter(rut_estudiante__rut=rut_estudiante)
        if id_disciplina and id_disciplina.isdigit():
            qs = qs.filter(id_sesion__id_disciplina_id=int(id_disciplina))
        if rut_entrenador:
            qs = qs.filter(id_sesion__rut_entrenador__rut=rut_entrenador)

        # Handle CSV Export
        if export_format == 'csv':
            response = HttpResponse(content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="reporte_deportivo_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
            
            # UTF-8 BOM for Microsoft Excel compatibility
            response.write('\ufeff')
            writer = csv.writer(response)
            writer.writerow([
                'ID Asistencia', 'RUT Estudiante', 'Nombre Estudiante',
                'Disciplina', 'Fecha Sesión', 'Lugar', 'Entrenador',
                'Asistencia (Presente)', 'Puntaje Rendimiento'
            ])

            for row in qs:
                writer.writerow([
                    row.id_asistencia,
                    row.rut_estudiante.rut,
                    f"{row.rut_estudiante.nombre} {row.rut_estudiante.apellido}",
                    row.id_sesion.id_disciplina.nombre,
                    str(row.id_sesion.fecha),
                    row.id_sesion.lugar,
                    f"{row.id_sesion.rut_entrenador.nombre} {row.id_sesion.rut_entrenador.apellido}",
                    'SÍ' if row.estado_presente else 'NO',
                    f"{row.puntaje:.1f}" if row.puntaje is not None else 'N/A',
                ])

            log_audit_event(
                rut_actor=request.user.rut,
                accion='EXPORTAR_REPORTE_CSV',
                endpoint=request.path,
                codigo_http=200,
            )
            return response

        # Aggregate metrics
        total_registros = qs.count()
        total_presentes = qs.filter(estado_presente=True).count()
        porcentaje_asistencia = round((total_presentes / total_registros * 100), 1) if total_registros > 0 else 0.0
        promedio_puntaje = qs.filter(puntaje__isnull=False).aggregate(Avg('puntaje'))['puntaje__avg']
        promedio_puntaje = round(float(promedio_puntaje), 2) if promedio_puntaje else 0.0

        detalle = []
        for a in qs[:100]:  # Limit 100 for responsive web UI
            detalle.append({
                'id_asistencia': a.id_asistencia,
                'rut_estudiante': a.rut_estudiante.rut,
                'estudiante_nombre': f"{a.rut_estudiante.nombre} {a.rut_estudiante.apellido}",
                'disciplina': a.id_sesion.id_disciplina.nombre,
                'fecha': str(a.id_sesion.fecha),
                'entrenador': f"{a.id_sesion.rut_entrenador.nombre} {a.id_sesion.rut_entrenador.apellido}",
                'estado_presente': a.estado_presente,
                'puntaje': float(a.puntaje) if a.puntaje is not None else None,
            })

        return Response({
            'resumen': {
                'total_registros': total_registros,
                'total_presentes': total_presentes,
                'total_ausentes': total_registros - total_presentes,
                'porcentaje_asistencia': porcentaje_asistencia,
                'promedio_puntaje': promedio_puntaje,
            },
            'registros': detalle,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Portal Estudiante View (RF04 / CU06 / CU07)
# ---------------------------------------------------------------------------

class PortalEstudianteView(APIView):
    """
    Consolidates data for Student Dashboard:
    - Enrolled disciplines
    - Upcoming sessions
    - Attendance history and accumulated percentage with chromatic status
    - Average score
    """
    permission_classes = [permissions.IsAuthenticated, IsEstudiante]

    def get(self, request):
        estudiante = request.user

        inscripciones = Inscripcion.objects.filter(rut_estudiante=estudiante).select_related('id_disciplina')
        disciplinas = [
            {
                'id_disciplina': i.id_disciplina.id_disciplina,
                'nombre': i.id_disciplina.nombre,
                'fecha_inscripcion': str(i.fecha_inscripcion),
            }
            for i in inscripciones
        ]
        disciplina_ids = [i.id_disciplina_id for i in inscripciones]

        # Upcoming sessions
        sesiones = Sesion.objects.filter(id_disciplina__in=disciplina_ids).select_related('id_disciplina', 'rut_entrenador').order_by('fecha', 'hora_inicio')[:10]
        sesiones_data = [
            {
                'id_sesion': s.id_sesion,
                'disciplina': s.id_disciplina.nombre,
                'fecha': str(s.fecha),
                'hora_inicio': str(s.hora_inicio),
                'lugar': s.lugar,
                'entrenador': f"{s.rut_entrenador.nombre} {s.rut_entrenador.apellido}",
            }
            for s in sesiones
        ]

        # Attendance history
        asistencias = Asistencia.objects.filter(rut_estudiante=estudiante).select_related('id_sesion', 'id_sesion__id_disciplina').order_by('-id_sesion__fecha')
        total_sesiones = asistencias.count()
        total_presente = asistencias.filter(estado_presente=True).count()
        porcentaje_asistencia = round((total_presente / total_sesiones * 100), 1) if total_sesiones > 0 else 100.0
        
        # Risk evaluation (< 75% critical academic risk)
        alerta_riesgo = porcentaje_asistencia < 75.0

        promedio_eval = asistencias.filter(puntaje__isnull=False).aggregate(Avg('puntaje'))['puntaje__avg']
        promedio_rendimiento = round(float(promedio_eval), 1) if promedio_eval else 0.0

        historial = [
            {
                'id_asistencia': a.id_asistencia,
                'disciplina': a.id_sesion.id_disciplina.nombre,
                'fecha': str(a.id_sesion.fecha),
                'estado_presente': a.estado_presente,
                'puntaje': float(a.puntaje) if a.puntaje is not None else None,
            }
            for a in asistencias
        ]

        # Unread notifications count
        notificaciones_pendientes = Notificacion.objects.filter(rut_estudiante=estudiante, leida=False).count()

        return Response({
            'estudiante': {
                'rut': estudiante.rut,
                'nombre_completo': f"{estudiante.nombre} {estudiante.apellido}",
                'matricula': estudiante.matricula,
                'correo': estudiante.correo,
            },
            'metricas': {
                'total_sesiones': total_sesiones,
                'total_presente': total_presente,
                'porcentaje_asistencia': porcentaje_asistencia,
                'alerta_riesgo': alerta_riesgo,
                'promedio_rendimiento': promedio_rendimiento,
                'notificaciones_pendientes': notificaciones_pendientes,
            },
            'disciplinas': disciplinas,
            'proximas_sesiones': sesiones_data,
            'historial_asistencia': historial,
        }, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Adapter Sync View (IntranetAcademicaAdapter Integration)
# ---------------------------------------------------------------------------

class IntranetAdapterSyncView(APIView):
    """
    Demonstrates the Adapter Pattern (IntranetAcademicaAdapter).
    Transforms local SGAD models into the target institutional JSON academic schema.
    Returns status 'EN_DESARROLLO' with adapted payload for future external API synchronization.
    """
    permission_classes = [permissions.IsAuthenticated, IsCoordinador]

    def post(self, request):
        rut_estudiante = request.data.get('rut_estudiante')
        if not rut_estudiante:
            # Pick first available student
            estudiante = Usuario.objects.filter(id_perfil__nombre_perfil='ESTUDIANTE').first()
        else:
            estudiante = Usuario.objects.filter(rut=rut_estudiante).first()

        if not estudiante:
            return Response(
                {'error': True, 'codigo': 404, 'mensaje': 'Estudiante no encontrado para sincronización.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        asistencias = Asistencia.objects.filter(rut_estudiante=estudiante).select_related('id_sesion', 'id_sesion__id_disciplina')
        payload_adaptado = IntranetAcademicaAdapter.adaptar_reporte_completo(estudiante, list(asistencias))

        log_audit_event(
            rut_actor=request.user.rut,
            accion=f"ADAPTER_SINCRONIZACION_INTRANET: Estudiante {estudiante.rut}",
            endpoint=request.path,
            codigo_http=200,
        )

        return Response({
            'status': 'EN_DESARROLLO',
            'mensaje': 'Esquema de integración académica generado exitosamente mediante IntranetAcademicaAdapter.',
            'servicio_destino': 'https://intranet.institucion.edu/api/v2/deportes/sync',
            'payload_interoperable': payload_adaptado,
        }, status=status.HTTP_200_OK)
