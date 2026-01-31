# Documentación del proyecto Panel Kryon V2

## 🚀 Inicio Rápido


### Requerimientos del Sistema
#### Requisitos adicionales para Windows

Si usas Windows, antes de instalar las dependencias de Python, asegúrate de tener:

1. **Visual C++ Build Tools**
   - Descarga e instala desde: https://visualstudio.microsoft.com/visual-cpp-build-tools/
   - Durante la instalación, selecciona **"Desarrollo de escritorio con C++"**.
   - Reinicia tu terminal después de instalar.

2. **Rust y Cargo**
   - Descarga e instala desde: https://rustup.rs/
   - Sigue las instrucciones y reinicia tu terminal.

3. **Verifica la instalación:**
   ```powershell
   rustc --version
   cargo --version
   ```
   Si alguno de estos comandos falla, revisa la instalación.

> Estos requisitos son necesarios para compilar extensiones nativas de algunos paquetes de Python (como pydantic-core). Si no los tienes, la instalación de dependencias puede fallar con errores sobre 'link.exe', Visual Studio, Rust o Cargo.

**Software requerido:**
- **Python 3.9+** (para el backend FastAPI)
- **Node.js y npm** (opcional, solo si se desea usar un servidor estático más avanzado)
- **SQLite** (incluido con Python, se usa por defecto) o **PostgreSQL** (opcional, para producción)

**Hardware recomendado:**
- Mínimo 4GB RAM
- 500MB de espacio libre en disco (para code + media)

### Instalación y Configuración

#### 1. Clonar o descargar el repositorio

```bash
cd /ruta/deseada
# Asumiendo que ya tienes el código en /Users/keaf/Downloads/panel-kryon
```


#### 2. Configurar el Backend

**a) Crear entorno virtual:**

**En macOS/Linux:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

**En Windows:**

1. Abre una terminal en la carpeta `backend`:
    ```powershell
    cd backend
    python -m venv venv
    ```

2. Activa el entorno virtual según tu terminal:
    - **PowerShell:**
       ```powershell
       . .\venv\Scripts\Activate.ps1
       ```
    - **CMD (símbolo del sistema):**
       ```cmd
       venv\Scripts\activate.bat
       ```

> Si ves un error de permisos en PowerShell, ejecuta una vez:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Luego, continúa con la instalación de dependencias.

**b) Instalar dependencias:**

**En macOS/Linux:**
```bash
pip install -r requirements.txt
```

**En Windows:**
```powershell
python -m pip install -r requirements.txt
```

**⚠️ Si ves un error como 'link.exe not found', 'error: linker `link.exe` not found', o te pide Visual Studio/Build Tools al instalar dependencias en Windows:**

Algunos paquetes de Python (como pydantic-core) requieren compilar extensiones nativas y necesitan el compilador de C++ de Microsoft (link.exe) instalado y en el PATH.

**Solución:**

1. Descarga e instala los Build Tools de Visual Studio desde:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Durante la instalación, selecciona **"Desarrollo de escritorio con C++"**.
3. Reinicia tu terminal después de instalar.
4. Vuelve a instalar las dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```

Esto es necesario solo si ves errores de compilación relacionados con 'link.exe', Visual Studio, o mensajes que mencionan el compilador de C++.

**⚠️ Si ves un error relacionado con Rust/Cargo o pydantic-core al instalar dependencias en Windows:**

Algunos paquetes de Python (como pydantic-core) requieren compilar extensiones nativas y necesitan que Rust y Cargo estén instalados y en el PATH.

**Solución:**

1. Instala Rust y Cargo desde https://rustup.rs/ (descarga y ejecuta el instalador para Windows, sigue las instrucciones y reinicia la terminal).
2. Verifica la instalación:
   ```powershell
   rustc --version
   cargo --version
   ```
3. Luego vuelve a instalar las dependencias:
   ```powershell
   python -m pip install -r requirements.txt
   ```

Esto es necesario solo si ves errores de compilación relacionados con pydantic-core, maturin, o mensajes que mencionan Rust/Cargo.

**c) Configurar variables de entorno:**

Crear archivo `.env` en la carpeta `backend/`:

```env
# Base de datos (SQLite por defecto)
DATABASE_URL=sqlite:///./app.db

# Seguridad
SECRET_KEY=tu-clave-secreta-super-segura-cambiar-en-produccion
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (para desarrollo local)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Directorio de media
MEDIA_DIR=./media

# Superadmin inicial
INITIAL_SUPERADMIN_EMAIL=admin@panelkryon.com
INITIAL_SUPERADMIN_PASSWORD=admin123
INITIAL_SUPERADMIN_NAME=Super Admin
```

> **⚠️ Importante:** En producción, cambia `SECRET_KEY` y las credenciales del superadmin.

**d) Resetear la base de datos (opcional):**

Para formatear la base de datos y volver a ejecutar el seed inicial:

```bash
cd backend
source venv/bin/activate
python reset_db.py
```

El script eliminará todas las tablas, las recreará y ejecutará el seed inicial (plan básico, superadmin, modos de luz, categorías). 

> **⚠️ Advertencia:** Este comando borra todos los datos existentes. Úsalo solo en desarrollo.

#### 3. Iniciar el Backend

**Opción A: Usando el script de inicio (recomendado):**

```bash
cd backend
chmod +x start.sh  # Solo la primera vez en macOS/Linux
./start.sh
```

El backend estará disponible en `http://127.0.0.1:8000`

**Opción B: Manualmente:**

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 4. Iniciar el Frontend (UI Externa)

**En otra terminal:**

```bash
cd external-ui
python3 -m http.server 5173
```

El frontend estará disponible en `http://localhost:5173`

### Verificación de la Instalación

1. **Backend health check:**
   ```bash
   curl http://127.0.0.1:8000/health
   # Respuesta esperada: {"status": "ok"}
   ```

2. **API docs:**
   Abrir en navegador: `http://127.0.0.1:8000/docs`

3. **Frontend:**
   Abrir en navegador: `http://localhost:5173`

4. **Login admin:**
   - URL: `http://localhost:5173/admin/login.html`
   - Email: `admin@panelkryon.com`
   - Password: `admin123` (usar las credenciales de tu `.env`)

### Flujo de Uso Típico

**Para Administradores:**

1. Acceder a `http://localhost:5173/admin/login.html`
2. Iniciar sesión con credenciales de admin
3. Navegar al dashboard para:
   - Crear terapias
   - Gestionar usuarios
   - Configurar planes
   - Ver analytics
4. Usar botón "Ir a Terapias" para probar la interfaz de usuario

**Para Usuarios:**

1. Acceder a `http://localhost:5173/login.html`
2. Iniciar sesión o registrarse
3. Seleccionar terapia en `selection.html`
4. Iniciar sesión de terapia
5. Controlar reproducción en `session.html`

### Solución de Problemas Comunes

**Error: `ModuleNotFoundError`**
```bash
cd backend
pip install -r requirements.txt
```

**Error: Puerto 8000 o 5173 en uso**
```bash
# Para backend, cambiar puerto:
uvicorn app.main:app --reload --port 8001

# Para frontend, cambiar puerto:
python3 -m http.server 5174
```

**Error: Base de datos bloqueada**
```bash
# Reiniciar el backend
cd backend
./start.sh
```

---

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

#### Soporte Multi-Base de Datos

El sistema soporta **SQLite**, **MySQL** y **PostgreSQL** de forma intercambiable. Solo necesitas cambiar la variable `DATABASE_URL` en el archivo `.env`:

```bash
# SQLite (desarrollo local, sin servidor - RECOMENDADO para desarrollo)
DATABASE_URL=sqlite:///./panel_kryon.db

# MySQL (XAMPP u otro servidor MySQL)
DATABASE_URL=mysql+pymysql://root:@127.0.0.1:3306/panel_kryon?charset=utf8mb4

# PostgreSQL (producción)
DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/panel_kryon
```

**Notas:**
- **SQLite**: Incluido con Python, no requiere instalación adicional. Ideal para desarrollo local.
- **MySQL**: Requiere `PyMySQL` (ya incluido en `requirements.txt`).
- **PostgreSQL**: Requiere `psycopg2-binary` (ya incluido en `requirements.txt`).

Después de cambiar la URL, ejecuta `python reset_db.py` para inicializar la nueva base de datos.

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
