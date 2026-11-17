"""
Script de carga de datos iniciales (Seed Data) para el Sistema de Gestión de Actividades Deportivas (SGAD).

Crea de forma idempotente:
- 3 Perfiles ('COORDINADOR', 'ENTRENADOR', 'ESTUDIANTE')
- 5 Cuentas de prueba listas para usar con contraseñas seguras Argon2id
- 2 Disciplinas deportivas con control de cupos
- 2 Sesiones de entrenamiento
- 3 Inscripciones formales de estudiantes
- Registros de asistencia y notas de rendimiento (disparando el patrón Observer)
"""

import os
import sys
from decimal import Decimal
from datetime import date, time, timedelta

# Configurar entorno Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.settings')

import django
django.setup()

from src.models.perfiles import Perfil
from src.models.usuarios import Usuario
from src.models.disciplinas import Disciplina
from src.models.inscripciones import Inscripcion
from src.models.sesiones import Sesion
from src.models.asistencia import Asistencia
from src.models.notificaciones import Notificacion
from src.services.patterns import UsuarioFactory, evaluacion_subject


def seed():
    print("=" * 60)
    print("INICIANDO CARGA DE DATOS INICIALES (SEED DATA) - SGAD")
    print("=" * 60)

    # 1. Crear Perfiles
    print("\n1. Verificando perfiles del sistema...")
    perfil_coord, _ = Perfil.objects.get_or_create(id_perfil=1, defaults={'nombre_perfil': Perfil.COORDINADOR})
    perfil_coach, _ = Perfil.objects.get_or_create(id_perfil=2, defaults={'nombre_perfil': Perfil.ENTRENADOR})
    perfil_estud, _ = Perfil.objects.get_or_create(id_perfil=3, defaults={'nombre_perfil': Perfil.ESTUDIANTE})
    print("   [OK] Perfiles configurados: COORDINADOR, ENTRENADOR, ESTUDIANTE.")

    # 2. Crear Usuarios mediante UsuarioFactory
    print("\n2. Creando usuarios iniciales mediante UsuarioFactory...")
    usuarios_seed = [
        {
            'perfil': Perfil.COORDINADOR,
            'rut': '11111111-1',
            'nombre': 'Carlos',
            'apellido': 'Valenzuela',
            'correo': 'coordinador@deportes.cl',
            'clave': 'Admin2026!#Segura',
            'especialidad': None,
            'matricula': None,
        },
        {
            'perfil': Perfil.ENTRENADOR,
            'rut': '22222222-2',
            'nombre': 'Marcelo',
            'apellido': 'Bielsa',
            'correo': 'entrenador@deportes.cl',
            'clave': 'Coach2026!#Segura',
            'especialidad': 'Fútbol y Acondicionamiento Físico',
            'matricula': None,
        },
        {
            'perfil': Perfil.ESTUDIANTE,
            'rut': '33333333-3',
            'nombre': 'Alexis',
            'apellido': 'Sánchez',
            'correo': 'estudiante@alumnos.cl',
            'clave': 'Alumno2026!#Segura',
            'especialidad': None,
            'matricula': 'MAT-2026-001',
        },
        {
            'perfil': Perfil.ESTUDIANTE,
            'rut': '18456789-K',
            'nombre': 'Arturo',
            'apellido': 'Vidal',
            'correo': 'arturo@alumnos.cl',
            'clave': 'Alumno2026!#Segura',
            'especialidad': None,
            'matricula': 'MAT-2026-002',
        },
        {
            'perfil': Perfil.ESTUDIANTE,
            'rut': '19876543-0',
            'nombre': 'Claudio',
            'apellido': 'Bravo',
            'correo': 'claudio@alumnos.cl',
            'clave': 'Alumno2026!#Segura',
            'especialidad': None,
            'matricula': 'MAT-2026-003',
        },
    ]

    for u_data in usuarios_seed:
        if not Usuario.objects.filter(rut=u_data['rut']).exists():
            usr = UsuarioFactory.crear_usuario(
                perfil_nombre=u_data['perfil'],
                rut=u_data['rut'],
                nombre=u_data['nombre'],
                apellido=u_data['apellido'],
                correo=u_data['correo'],
                clave=u_data['clave'],
                especialidad=u_data['especialidad'],
                matricula=u_data['matricula'],
                debe_cambiar_clave=False,
            )
            print(f"   [+] Usuario creado: {usr.rut} - {usr.nombre} {usr.apellido} ({u_data['perfil']})")
        else:
            print(f"   [-] Usuario ya existe: {u_data['rut']}")

    # 3. Crear Disciplinas
    print("\n3. Creando catálogo de disciplinas deportivas...")
    disc_futbol, _ = Disciplina.objects.get_or_create(
        nombre='Fútbol Formativo',
        defaults={'cupo_maximo': 20}
    )
    disc_basket, _ = Disciplina.objects.get_or_create(
        nombre='Básquetbol Selección',
        defaults={'cupo_maximo': 15}
    )
    print(f"   [OK] Disciplinas: {disc_futbol.nombre} (Cupos: {disc_futbol.cupo_maximo}), {disc_basket.nombre} (Cupos: {disc_basket.cupo_maximo})")

    # 4. Inscribir Estudiantes
    print("\n4. Registrando inscripciones con validación de cupos...")
    est_alexis = Usuario.objects.get(rut='33333333-3')
    est_arturo = Usuario.objects.get(rut='18456789-K')
    est_claudio = Usuario.objects.get(rut='19876543-0')

    inscripciones_data = [
        (est_alexis, disc_futbol),
        (est_arturo, disc_futbol),
        (est_claudio, disc_futbol),
        (est_claudio, disc_basket),
    ]

    for est, disc in inscripciones_data:
        insc, created = Inscripcion.objects.get_or_create(
            rut_estudiante=est,
            id_disciplina=disc,
        )
        if created:
            print(f"   [+] Inscrito: {est.nombre} {est.apellido} en {disc.nombre}")
        else:
            print(f"   [-] Ya inscrito: {est.nombre} en {disc.nombre}")

    # 5. Crear Sesiones
    print("\n5. Programando sesiones de entrenamiento...")
    coach = Usuario.objects.get(rut='22222222-2')
    hoy = date.today()
    manana = hoy + timedelta(days=1)

    sesion_1, s1_created = Sesion.objects.get_or_create(
        fecha=hoy,
        hora_inicio=time(10, 0),
        id_disciplina=disc_futbol,
        rut_entrenador=coach,
        defaults={'lugar': 'Cancha Sintética Principal - Sector A'}
    )
    sesion_2, s2_created = Sesion.objects.get_or_create(
        fecha=manana,
        hora_inicio=time(15, 30),
        id_disciplina=disc_basket,
        rut_entrenador=coach,
        defaults={'lugar': 'Gimnasio Techado - Tablero 2'}
    )
    print(f"   [OK] Sesiones programadas: Sesión 1 ({sesion_1.id_sesion}) y Sesión 2 ({sesion_2.id_sesion})")

    # 6. Registrar Asistencias y Calificaciones (Disparando Observer)
    print("\n6. Registrando asistencia inicial y evaluando mediante patrón Observer...")
    asistencias_demo = [
        {
            'sesion': sesion_1,
            'estudiante': est_alexis,
            'presente': True,
            'puntaje': Decimal('6.8'),
        },
        {
            'sesion': sesion_1,
            'estudiante': est_arturo,
            'presente': True,
            'puntaje': Decimal('6.2'),
        },
        {
            'sesion': sesion_1,
            'estudiante': est_claudio,
            'presente': False,
            'puntaje': Decimal('1.0'),
        },
    ]

    for item in asistencias_demo:
        asist, created = Asistencia.objects.update_or_create(
            id_sesion=item['sesion'],
            rut_estudiante=item['estudiante'],
            defaults={
                'estado_presente': item['presente'],
                'puntaje': item['puntaje'],
            }
        )
        # Disparo explícito de Observer
        evaluacion_subject.notify(asist)
        print(f"   [+] Asistencia: {item['estudiante'].nombre} -> Presente: {item['presente']}, Nota: {item['puntaje']} (Observer Notificación disparado)")

    print("\n" + "=" * 60)
    print("CARGA DE DATOS COMPLETADA CON ÉXITO")
    print("=" * 60)
    print("\nCUENTAS DISPONIBLES PARA PRUEBAS:")
    print("  • COORDINADOR: RUT 11111111-1  | Clave: Admin2026!#Segura")
    print("  • ENTRENADOR:  RUT 22222222-2  | Clave: Coach2026!#Segura")
    print("  • ESTUDIANTE:   RUT 33333333-3  | Clave: Alumno2026!#Segura")
    print("  • ESTUDIANTE 2: RUT 18456789-K  | Clave: Alumno2026!#Segura")
    print("  • ESTUDIANTE 3: RUT 19876543-0  | Clave: Alumno2026!#Segura")
    print("=" * 60)


if __name__ == '__main__':
    seed()
