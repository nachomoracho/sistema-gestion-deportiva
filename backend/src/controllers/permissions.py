from rest_framework import permissions


class IsCoordinador(permissions.BasePermission):
    """Allows access only to users with the COORDINADOR role."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.id_perfil and
            request.user.id_perfil.nombre_perfil == 'COORDINADOR'
        )


class IsEntrenador(permissions.BasePermission):
    """Allows access only to users with the ENTRENADOR role."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.id_perfil and
            request.user.id_perfil.nombre_perfil == 'ENTRENADOR'
        )


class IsEstudiante(permissions.BasePermission):
    """Allows access only to users with the ESTUDIANTE role."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.id_perfil and
            request.user.id_perfil.nombre_perfil == 'ESTUDIANTE'
        )


class IsCoordinadorOrEntrenador(permissions.BasePermission):
    """Allows access to either COORDINADOR or ENTRENADOR roles."""

    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.id_perfil and
            request.user.id_perfil.nombre_perfil in ['COORDINADOR', 'ENTRENADOR']
        )


class IsOwnerOrAssignedStaff(permissions.BasePermission):
    """
    Object-level permission to prevent IDOR (Insecure Direct Object Reference)
    as mandated by ISO/IEC 27002 Control 8.3, OWASP A01, and Ley N° 21.459 Art. 2°.
    """

    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        rol = request.user.id_perfil.nombre_perfil if request.user.id_perfil else None

        # Coordinador has organizational clearance
        if rol == 'COORDINADOR':
            return True

        # Check for Asistencia object
        if hasattr(obj, 'rut_estudiante') and hasattr(obj, 'id_sesion'):
            if rol == 'ESTUDIANTE':
                # Student can only read their own attendance
                return request.method in permissions.SAFE_METHODS and obj.rut_estudiante_id == request.user.rut
            if rol == 'ENTRENADOR':
                # Trainer can only manage sessions assigned to them
                return obj.id_sesion.rut_entrenador_id == request.user.rut

        # Check for Sesion object
        if hasattr(obj, 'rut_entrenador') and hasattr(obj, 'id_disciplina'):
            if rol == 'ENTRENADOR':
                return obj.rut_entrenador_id == request.user.rut
            if rol == 'ESTUDIANTE':
                # Safe read only
                return request.method in permissions.SAFE_METHODS

        # Check for Notificacion object
        if hasattr(obj, 'rut_estudiante') and hasattr(obj, 'mensaje'):
            return obj.rut_estudiante_id == request.user.rut

        # Check for Inscripcion object
        if hasattr(obj, 'rut_estudiante') and hasattr(obj, 'id_disciplina'):
            if rol == 'ESTUDIANTE':
                return request.method in permissions.SAFE_METHODS and obj.rut_estudiante_id == request.user.rut

        # Check for Usuario object
        if hasattr(obj, 'rut') and hasattr(obj, 'id_perfil'):
            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.rut == request.user.rut

        return False
