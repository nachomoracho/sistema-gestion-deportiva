from django.urls import path, include
from rest_framework.routers import DefaultRouter

from src.controllers.views import (
    LoginView,
    LogoutView,
    ChangePasswordView,
    MeView,
    PerfilViewSet,
    UsuarioViewSet,
    DisciplinaViewSet,
    InscripcionViewSet,
    SesionViewSet,
    AsistenciaViewSet,
    NotificacionViewSet,
    ReportesAvanzadosView,
    PortalEstudianteView,
    IntranetAdapterSyncView,
)

router = DefaultRouter()
router.register(r'perfiles', PerfilViewSet, basename='perfil')
router.register(r'usuarios', UsuarioViewSet, basename='usuario')
router.register(r'disciplinas', DisciplinaViewSet, basename='disciplina')
router.register(r'inscripciones', InscripcionViewSet, basename='inscripcion')
router.register(r'sesiones', SesionViewSet, basename='sesion')
router.register(r'asistencia', AsistenciaViewSet, basename='asistencia')
router.register(r'notificaciones', NotificacionViewSet, basename='notificacion')

urlpatterns = [
    # Auth endpoints
    path('auth/login/', LoginView.as_view(), name='auth-login'),
    path('auth/logout/', LogoutView.as_view(), name='auth-logout'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('auth/me/', MeView.as_view(), name='auth-me'),

    # Specialized Views
    path('reportes/', ReportesAvanzadosView.as_view(), name='reportes-avanzados'),
    path('estudiantes/mi-portal/', PortalEstudianteView.as_view(), name='portal-estudiante'),
    path('adapter/sync-intranet/', IntranetAdapterSyncView.as_view(), name='adapter-sync-intranet'),

    # Router endpoints
    path('', include(router.urls)),
]
