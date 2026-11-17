# SGAD — Sistema de Gestión de Actividades Deportivas

Sistema web completo para la gestión de actividades deportivas universitarias. Permite a coordinadores, entrenadores y estudiantes administrar deportes, horarios, inscripciones y asistencia de manera eficiente y segura.

---

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.11 · Django 4.2 · Django REST Framework |
| **Frontend** | React 18 · React Router 6 · Bootstrap 5 |
| **Base de datos** | SQLite (desarrollo) · Oracle (producción) |
| **Autenticación** | JWT (SimpleJWT) · Argon2 (hashing de contraseñas) |
| **CI/CD** | GitHub Actions |

---

## Requisitos Previos

- **Python** 3.11 o superior
- **Node.js** 18 o superior
- **pip** (incluido con Python)
- **npm** (incluido con Node.js)
- **Oracle Database** (solo para producción, opcional en desarrollo)

---

## Instalación y Configuración

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd proyecto
cp .env.example .env
# Editar .env con los valores apropiados (SECRET_KEY, credenciales de BD, etc.)
```

### 2. Backend (Django)

```bash
cd backend

# Crear y activar entorno virtual
python -m venv venv

# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar migraciones
python manage.py migrate

# Cargar datos iniciales (usuarios, deportes, horarios de ejemplo)
python manage.py seed_data

# Iniciar servidor de desarrollo
python manage.py runserver
```

El backend estará disponible en `http://localhost:8000`.

### 3. Frontend (React)

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

El frontend estará disponible en `http://localhost:3000`.

---

## Ejecución de Tests

### Backend

```bash
cd backend
pytest --cov=src --cov-report=term-missing
```

Se requiere una cobertura mínima del **80 %** para pasar el pipeline de CI.

### Frontend

```bash
cd frontend
npm test -- --watchAll=false --coverage
```

---

## Estructura del Proyecto

```
proyecto/
├── .env.example                  # Variables de entorno de referencia
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml                # Pipeline de CI (GitHub Actions)
├── README.md
├── backend/
│   ├── manage.py                 # Punto de entrada de Django
│   ├── requirements.txt          # Dependencias de Python
│   └── src/
│       ├── config/               # Configuración de Django
│       │   ├── settings.py       # Settings principal
│       │   └── urls.py           # Enrutamiento raíz
│       ├── apps/
│       │   ├── users/            # Autenticación, roles, perfiles
│       │   ├── sports/           # Gestión de deportes y categorías
│       │   ├── schedules/        # Horarios y sesiones
│       │   ├── enrollments/      # Inscripciones de estudiantes
│       │   └── attendance/       # Control de asistencia
│       └── tests/                # Tests unitarios y de integración
└── frontend/
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── components/           # Componentes reutilizables
        ├── pages/                # Vistas por ruta
        ├── services/             # Clientes API (Axios)
        ├── context/              # Contextos de React (Auth, etc.)
        └── utils/                # Helpers y constantes
```

---

## Credenciales por Defecto

Los datos iniciales (`seed_data`) crean los siguientes usuarios de prueba:

| Rol | Usuario | Contraseña |
|-----|---------|------------|
| Coordinador | `coordinador` | `Coord2024!` |
| Entrenador | `entrenador` | `Coach2024!` |
| Estudiante | `estudiante` | `Student2024!` |

> ⚠️ **Importante:** Cambiar estas credenciales de inmediato en entornos de producción.

---

## Características de Seguridad

- **Autenticación JWT** con tokens de acceso (30 min) y refresh (1 día)
- **Hashing Argon2** para contraseñas (resistente a ataques de fuerza bruta)
- **Control de acceso basado en roles (RBAC)**: Coordinador, Entrenador, Estudiante
- **Rate limiting** configurable para endpoints anónimos y autenticados
- **Validación de datos** exhaustiva en serializers y modelos
- **Protección CORS** con orígenes permitidos configurables
- **Cabeceras de seguridad**: `X-Content-Type-Options`, `X-Frame-Options`
- **Auditoría**: registro de eventos de seguridad en archivo dedicado

---

## Arquitectura

```
┌─────────────┐     HTTP/JSON      ┌──────────────────┐     ORM/SQL     ┌────────────┐
│   Frontend  │ ◄────────────────► │     Backend      │ ◄─────────────► │  Base de   │
│  (React 18) │   JWT Auth         │  (Django REST)   │                 │   Datos    │
│  Port 3000  │                    │    Port 8000     │                 │ SQLite /   │
│             │                    │                  │                 │  Oracle    │
└─────────────┘                    └──────────────────┘                 └────────────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │  Middleware   │
                                   │  - CORS      │
                                   │  - JWT Auth   │
                                   │  - Rate Limit │
                                   │  - Audit Log  │
                                   └──────────────┘
```

**Flujo de autenticación:**
1. El cliente envía credenciales a `/api/auth/login/`
2. El backend valida con Argon2 y emite par JWT (access + refresh)
3. El cliente incluye el access token en cabecera `Authorization: Bearer <token>`
4. Los permisos se verifican por rol en cada endpoint protegido

---

## Licencia

Este proyecto es de uso académico. Todos los derechos reservados.
