# Documentación del proyecto Panel Kryon V2

## 1) Resumen ejecutivo
Panel Kryon V2 es una plataforma para administrar terapias (audio/video), usuarios, créditos y sesiones, con un **backend FastAPI** y una **UI estática desacoplada** para prototipado visual. El backend expone una API REST con autenticación JWT, gestión de planes y créditos, catálogos de terapias, sesiones, analíticas y categorías/modos de luz. La UI externa (carpeta `external-ui/`) ofrece páginas HTML/CSS/JS con interacciones simuladas para flujos de usuario y administración. 【F:backend/app/main.py†L1-L92】【F:backend/app/auth.py†L1-L110】【F:external-ui/README.md†L1-L190】

---

## 2) Arquitectura general

**Componentes principales:**

1) **Backend (FastAPI + SQLAlchemy)**
   - Expone la API y monta recursos estáticos de media (`/media`).
   - Incluye migraciones ligeras en el arranque y un seed inicial (plan básico, superadmin, modos de luz, categorías).
   - Implementa autenticación y autorización por roles. 【F:backend/app/main.py†L1-L92】【F:backend/app/migrations.py†L1-L97】【F:backend/app/seed.py†L1-L95】【F:backend/app/auth.py†L1-L110】

2) **UI externa (HTML/CSS/JS estático)**
   - Maquetas estáticas para navegación y diseño de pantallas sin dependencia del backend.
   - Incluye simulaciones de loading, selección de terapias y control de sesión (mock). 【F:external-ui/README.md†L1-L190】【F:external-ui/app.js†L1-L200】

---

## 3) Estructura del repositorio

```
/ (raíz)
├─ backend/                 # API FastAPI, modelos y migraciones
├─ external-ui/             # UI estática (HTML/CSS/JS)
└─ env.example              # Plantilla de variables de entorno
```

- **`backend/`**: Código del servidor, configuración, modelos, routers y arranque. 【F:backend/app/main.py†L1-L92】
- **`external-ui/`**: Maquetas y flujo visual del sistema, sin persistencia real. 【F:external-ui/README.md†L1-L190】
- **`env.example`**: Variables de entorno de referencia. 【F:env.example†L1-L12】

---

## 4) Backend (FastAPI)

### 4.1 Arranque de la aplicación
El backend usa **FastAPI** con un ciclo de vida (`lifespan`) que:
- Ejecuta migraciones ligeras.
- Crea carpetas de media (`audio`, `video`).
- Ejecuta un seed inicial si la BD está disponible.
- Monta `/media` como archivos estáticos.
- Incluye routers de auth, usuarios, planes, terapias, playlists, sesiones, analítica y categorías. 【F:backend/app/main.py†L1-L92】

**Endpoints base:**
- `/health`: health check.
- `/`: raíz con metadata de la API. 【F:backend/app/main.py†L69-L92】

### 4.2 Configuración
La configuración se basa en `pydantic-settings` y se carga desde `.env` con valores por defecto para:
- `DATABASE_URL`
- `SECRET_KEY`, `ALGORITHM`, expiración del token
- `CORS_ORIGINS`
- `MEDIA_DIR`
- Credenciales iniciales del superadmin 【F:backend/app/config.py†L1-L26】

El repositorio incluye un `env.example` como base para variables de entorno. 【F:env.example†L1-L12】

### 4.3 Base de datos
Se usa **SQLAlchemy** con un `engine` creado desde `DATABASE_URL` y `SessionLocal` como session factory. `get_db()` es la dependencia estándar para inyectar la sesión en los endpoints. 【F:backend/app/db.py†L1-L21】

### 4.4 Modelos (tablas principales)
Los modelos representan el dominio de usuarios, planes, terapias, créditos, sesiones y analítica:

- **Usuarios y roles**: `User`, con `Role` (superadmin/admin/user), balance de créditos y plan asociado. 【F:backend/app/models.py†L10-L46】
- **Planes**: `Plan` y relación `UserPlan`. 【F:backend/app/models.py†L50-L90】
- **Créditos**: `CreditLedger` para registrar movimientos. 【F:backend/app/models.py†L93-L106】
- **Categorías**: `Category` creada por admin. 【F:backend/app/models.py†L110-L125】
- **Modos de luz**: `LightMode` (fijos, no modificables por usuarios). 【F:backend/app/models.py†L129-L146】
- **Terapias**: `Therapy` con duración, intensidad, acceso por plan y rutas de media. 【F:backend/app/models.py†L149-L207】
- **Playlists**: `Playlist` y `PlaylistItem`. 【F:backend/app/models.py†L211-L238】
- **Sesiones**: `TherapySession` con estado, duración y créditos consumidos. 【F:backend/app/models.py†L245-L289】
- **Auditoría**: `ActivityLog` para acciones del sistema. 【F:backend/app/models.py†L292-L315】
- **Estadísticas diarias**: `DailyStats` para agregados. 【F:backend/app/models.py†L318-L345】

### 4.5 Autenticación y autorización
- Hash de contraseña con **bcrypt**.
- JWT con `SECRET_KEY` y expiración por minutos.
- Dependencias para roles: `require_auth`, `require_admin`, `require_superadmin`. 【F:backend/app/auth.py†L1-L110】

### 4.6 Migraciones y seed
- **Migraciones ligeras**: validan tablas y agregan columnas faltantes sin usar Alembic. 【F:backend/app/migrations.py†L1-L97】
- **Seed inicial**: crea plan básico, superadmin, modos de luz y categorías por defecto si no existen. 【F:backend/app/seed.py†L1-L95】

### 4.7 Routers (API)

#### a) Auth (`/api/auth`)
- Login por email/contraseña, login OAuth2 para `/docs`, registro de usuarios y endpoint `/me`. 【F:backend/app/routers/auth.py†L1-L110】

#### b) Usuarios admin (`/api/admin/users`)
- Listado, creación, ajuste de créditos y asignación de planes. 【F:backend/app/routers/users.py†L1-L200】

#### c) Planes (`/api/admin/plans`)
- CRUD de planes, con soft delete. 【F:backend/app/routers/plans.py†L1-L135】

#### d) Terapias (`/api/therapies`)
- Listado público (con auth), CRUD admin y subida de media (audio/video), incluyendo soporte para múltiples duraciones (corto/mediano/largo). 【F:backend/app/routers/therapies.py†L1-L268】

#### e) Playlists (`/api/playlists`)
- CRUD de playlists y manejo de items con reorder, duración override y modo de color override. 【F:backend/app/routers/playlists.py†L1-L280】

#### f) Sesiones (`/api/sessions`)
- Inicio y cierre de sesiones con validaciones de plan y créditos, logging de actividad, y consultas de sesiones activas y recientes. 【F:backend/app/routers/sessions.py†L1-L320】

#### g) Analítica (`/api/analytics`)
- Endpoints para dashboard, uso de terapias, actividad de usuarios y reportes agregados. 【F:backend/app/routers/analytics.py†L1-L200】

#### h) Categorías y modos de luz (`/api/categories`)
- CRUD de categorías (admin) y listado público.
- Modos de luz solo lectura con fallback a defaults si no existen en BD. 【F:backend/app/routers/categories.py†L1-L220】

---

## 5) UI externa (maquetas estáticas)

La carpeta `external-ui/` contiene pantallas HTML/CSS/JS para prototipar la experiencia de usuario sin backend real. Su objetivo es iterar UX/UI sin depender de la base de datos ni hardware. 【F:external-ui/README.md†L1-L40】

### 5.1 Páginas principales
Incluye páginas para el flujo de usuario (loading, login, selección, sesión, pantalla extendida) y para administración (login y dashboard). 【F:external-ui/README.md†L80-L150】

### 5.2 Comportamientos simulados
`app.js` maneja la navegación y la interacción visual (tabs, selección de terapias, loading y timer de sesión en modo mock). 【F:external-ui/app.js†L1-L200】

### 5.3 Cómo ejecutar la UI
Se recomienda levantar un servidor estático, por ejemplo con `python -m http.server`, y abrir `http://localhost:5173/`. 【F:external-ui/README.md†L54-L78】

---

## 6) Manejo de media (audio y video)

- El backend crea la carpeta `MEDIA_DIR` con subcarpetas `audio` y `video`.
- Los endpoints de terapias permiten subir archivos y exponen URLs relativas bajo `/media`. 【F:backend/app/main.py†L30-L64】【F:backend/app/routers/therapies.py†L114-L268】

---

## 7) Configuración y despliegue local (backend)

### 7.1 Requisitos
- Python y dependencias listadas en `backend/requirements.txt`. 【F:backend/requirements.txt†L1-L10】

### 7.2 Variables de entorno
- Crear un `.env` en `backend/` (o en la raíz según convención) con las variables necesarias (`DATABASE_URL`, `SECRET_KEY`, etc.). El backend admite configuración por `.env` vía `config.py`. 【F:backend/app/config.py†L1-L26】
- El archivo `env.example` sirve como guía inicial. 【F:env.example†L1-L12】

### 7.3 Arranque
El script `backend/start.sh` inicia el servidor en el puerto `8000` y utiliza un entorno virtual en `backend/venv/`. 【F:backend/start.sh†L1-L16】

---

## 8) Consideraciones de uso

- **Roles**: las acciones administrativas requieren `admin` o `superadmin`. 【F:backend/app/auth.py†L74-L110】
- **Créditos**: las sesiones completadas consumen créditos y se registran en el ledger. 【F:backend/app/routers/sessions.py†L132-L223】
- **Planes**: la asignación de planes puede agregar créditos automáticamente y define el acceso a terapias. 【F:backend/app/routers/users.py†L70-L190】

---

## 9) Próximos pasos sugeridos (para evolución)

- Integrar la UI externa con los endpoints reales de FastAPI.
- Añadir pruebas automáticas y documentación de API (OpenAPI + ejemplos de uso).
- Completar integración con hardware (Web Serial API) con eventos reales en la UI.

---

## 10) Referencias rápidas

- **API docs**: `/docs` (Swagger UI, al levantar el backend).
- **Health check**: `/health`. 【F:backend/app/main.py†L69-L83】
