# external-ui

Maquetas estáticas (solo front-end) en **HTML/CSS/JS** basadas en la UI de la app.  
Objetivo: poder iterar **diseño/UX** de todas las ventanas/páginas (botones, layouts, estados visuales) sin depender todavía de Arduino, autenticación o base de datos.

> Nota: esta carpeta es **estática**. No incluye backend. Para persistencia (BD), usuarios, créditos y subida de audio/video se conectará a una **API Python** (FastAPI) y **MySQL/MariaDB (XAMPP)**.

---

## Cambios y alcance (lo que se hizo aquí)

- Se creó la carpeta `external-ui/` como **UI desacoplada** de Next.js.
- Se agregaron páginas HTML equivalentes a pantallas/ventanas de la app.
- Se centralizó el look en `styles.css` y los comportamientos visuales/mocks en `app.js`.
- Se dejó preparada UI para **reproductor de audio y reproductor de video** (solo presentación; sin pipeline real todavía).
- Se replicó el estilo de **pantalla de carga** (fondo, spinner/glow, progreso simulado, textos y elementos decorativos).
- Se definió flujo de **login de usuario** y **login de admin** con ruta alterna y un **dashboard** (configuración de planes/créditos).
- **Planificado (versión profesional):**
  - **Sincronización real entre ventanas** (principal ↔ panel externo ↔ pantalla extendida) con un bus de eventos.
  - **Conexión real a Arduino** vía **Web Serial API** (como en la primera versión).

---

## Qué se usará (stack)

### Front-end (esta carpeta)
- HTML (páginas)
- CSS (`styles.css`) para estilos compartidos
- JS vanilla (`app.js`) para:
  - navegación simple entre páginas,
  - estados visuales (activos/inactivos),
  - simulación de progreso / loading,
  - comportamiento UI de ejemplo (sin persistencia real).

### Backend (planificado, fuera de esta carpeta)
- **Python (FastAPI)** como API
- **MySQL/MariaDB en XAMPP** como BD local
- Carpeta de media en el proyecto (p.ej. `backend/media/`) para:
  - **audio** subido por el admin/superadmin,
  - **video** subido por el admin/superadmin,
  - metadatos en BD (no guardar BLOB en la BD).

### Integración hardware (front-end)
- **Arduino por Web Serial API** (cliente, directo desde el navegador).
  - Requiere gesto de usuario (click) para `requestPort()`.
  - Recomendado: Chrome/Edge.
  - Se usa en el flujo de sesión/terapia para enviar comandos.

---

## Cómo ver las maquetas

### Opción A: abrir directo
Abrir `external-ui/index.html` en el navegador.

### Opción B: servidor estático (recomendado)
#### Mac
```bash
python3 -m http.server 5173 --directory external-ui
```

#### Windows
```bat
py -m http.server 5173 --directory external-ui
```

Luego abrir: `http://localhost:5173/`

---

## Pantallas (usuario normal) — flujo requerido

**Pantallas del usuario normal:**
1) Pantalla de carga  
2) Login (usuario)  
3) Menú de terapias  
4) Sesión de terapia (audio/video)  
5) Panel de pantalla externa (gestor)  
6) Pantalla extendida (segunda pantalla)

---

## Páginas incluidas / previstas

> Algunas páginas ya existen; otras se agregan como parte del flujo de login y dashboard.

### Usuario normal
- `loading.html` — splash / precarga (progreso simulado)
- `login.html` — login de usuario
- `selection.html` — menú/selección de terapias
- `session.html` — sesión (UI de reproducción audio/video + controles)
- `window-manager.html` — panel de “ventana externa”
- `external-screen.html` — pantalla extendida (segunda pantalla)

### Admin (ruta alterna)
- `admin/login.html` — login de admin/superadmin
- `admin/dashboard.html` — dashboard de administración (planes, créditos, terapias, media)

### Utilidades
- `index.html` — menú (solo para navegación de maquetas)
- `permissions.html` — pantalla/modal de permisos (mock)

---

## Funciones UI (mock) incluidas

> Estas funciones son **de presentación**; no guardan datos reales ni ejecutan Arduino.

- **Loading / precarga**
  - Progreso simulado
  - Textos rotativos/indicadores visuales
  - Animaciones (spinner/glow y elementos decorativos)

- **Login (usuario)**
  - Form: email/usuario + contraseña
  - Estados: cargando / error / éxito (mock)
  - Redirección UI a selección de terapias

- **Login (admin)**
  - Form: usuario + contraseña
  - Redirección UI al dashboard

- **Dashboard (admin/superadmin)**
  - Gestión visual de:
    - créditos por usuario (sumar/restar),
    - planes (crear/editar/activar),
    - asignación de plan a usuario,
    - catálogo de terapias (metadata),
    - subida de **audio** y **video** a terapia (solo UI).

- **Selección de terapias**
  - Layout tipo grid/lista
  - Estados activos/hover
  - Separación por secciones (tabs)

- **Sesión**
  - Contenedor visual para:
    - **Audio player** (botones/estado)
    - **Video player** (área/controls UI)
  - Controles de sesión (iniciar/pausar/detener) a nivel visual

- **Pantalla extendida**
  - Composición “solo visualización” (sin controles)
  - Diseñada para replicar lo que se mostraría en pantalla secundaria

---

## Sincronización real entre ventanas (objetivo)

Se implementará un bus de eventos para sincronizar estado entre:
- **Ventana principal** (sesión/controles),
- **Window Manager** (gestor de pantalla secundaria),
- **Pantalla extendida** (solo visualización).

### Tecnología recomendada
- **BroadcastChannel** como canal principal (simple y estable entre pestañas/ventanas del mismo origen).
- **`window.postMessage`** como fallback cuando aplique (ej. handshake al abrir la ventana, o si se requiere comunicación directa).

### Tipos de eventos (protocolo sugerido)
```text
SESSION_START / SESSION_STOP / SESSION_PAUSE / SESSION_RESUME
THERAPY_SELECTED
PLAYBACK_STATE (audio/video currentTime, isPlaying)
COLOR_MODE_CHANGED
TIMER_UPDATED (remainingSec)
ARDUINO_STATUS (connected, portInfo)
ERROR (code, message)
```

### Diagrama de sincronización (alto nivel)
```text
[Main: session.html]
   │  BroadcastChannel("kryon")
   ├─────────────────────────────────────┐
   │                                     │
[window-manager.html]               [external-screen.html]
(abrir/cerrar/pantalla)             (render visual + estado)
```

> Nota: la pantalla extendida **no debería** tomar decisiones de negocio (créditos, permisos). Solo renderiza el estado sincronizado.

---

## Conexión de Arduino (como primera versión) — objetivo

### Tecnología
- **Web Serial API** desde el navegador:
  - `navigator.serial.requestPort()`
  - `port.open({ baudRate })`
  - `writer.write(...)` para comandos
  - `reader.read()` para feedback/telemetría (si aplica)

### Requisitos y consideraciones
- Requiere **gesto de usuario** (click) para seleccionar el puerto serial.
- Recomendado: **Chrome/Edge**.
- Se recomienda manejar:
  - reconexión/estado,
  - cola de comandos,
  - timeout/reintentos,
  - desconexión limpia al terminar sesión.

### Diagrama Arduino (alto nivel)
```text
session.html (UI)  ── Web Serial API ──>  Arduino (COM/ttyUSB)
   │                                         │
   └─ Sync (BroadcastChannel) ────────────────┘
      (estado/errores a external-screen)
```

> La API Python/BD **no** es necesaria para hablar con Arduino si el control es local vía navegador.
> La BD se usa para usuarios/planes/créditos, terapias, playlist y media.

---

## Diagrama de funcionamiento (actual vs planificado)

### Estado actual (solo estático)
```text
Browser
  │
  ├─ GET /login.html, /selection.html, /session.html, /external-screen.html...
  └─ UI mock (sin BD, sin Arduino, sin auth)
```

### Estado objetivo (versión profesional)
```text
Browser (external-ui o Next)
  │
  ├─ UI Usuario:
  │     loading → login → selección → sesión → window-manager → external-screen
  │
  ├─ UI Admin:
  │     /admin/login → /admin/dashboard
  │
  ├─ Sync Ventanas:
  │     BroadcastChannel/postMessage (estado sesión, playback, color, timers)
  │
  ├─ Arduino:
  │     Web Serial API (conexión + envío de comandos)
  │
  ├─ fetch() a API Python (FastAPI)
  │     ├─ Auth + Roles (superadmin/admin/user)
  │     ├─ Terapias + Playlist (orden, tiempo por item, modo color)
  │     ├─ Créditos + Planes + Alertas (<= 15)
  │     └─ Upload/serving de Audio/Video (carpeta media + metadata en BD)
  │
  └─ MySQL/MariaDB (XAMPP)
        ├─ users, roles
        ├─ plans, user_plans
        ├─ credits_ledger (movimientos)
        ├─ therapies (metadatos + paths audio/video + config arduino)
        └─ playlists (+ items, tiempos, color mode)
```

---

## Diagrama de páginas (navegación)

### Usuario normal
```text
loading.html
  └─ login.html
       └─ selection.html
            └─ session.html
                 ├─ window-manager.html
                 │     └─ external-screen.html
                 └─ external-screen.html
```

### Admin (ruta alterna)
```text
admin/login.html
  └─ admin/dashboard.html
        ├─ Planes (CRUD)
        ├─ Usuarios (roles, asignación plan)
        ├─ Créditos (ajustes, ledger)
        ├─ Terapias (CRUD)
        └─ Media (subir audio/video por terapia)
```

---

## Integración futura (contrato sugerido API)

### Auth
- `POST /api/auth/login` → login usuario/admin (retorna token/sesión)
- `POST /api/auth/logout`
- `GET /api/users/me` → perfil + rol + créditos + plan + flags de alerta

### Bootstrapping (primer inicio del sistema)
- En el **primer arranque** del backend:
  - se crea un **Plan Básico** por defecto (si no existe).
  - opcional: crear `superadmin` inicial (si no existe).

> Implementación sugerida: en `startup` del backend, correr un “seed” idempotente.

### Terapias + Media
- `GET /api/therapies`
- `POST /api/therapies` (admin/superadmin)
- `POST /api/therapies/:id/audio` (admin/superadmin) → guarda archivo en carpeta
- `POST /api/therapies/:id/video` (admin/superadmin) → guarda archivo en carpeta

### Playlist
- `GET /api/playlists`
- `POST /api/playlists` (admin/superadmin)
- `PUT /api/playlists/:id/items` (orden, tiempo por item, modo color)

### Créditos / Planes
- `POST /api/admin/users/:id/credits` (admin/superadmin) → +N/-N con reason
- `GET /api/admin/plans`
- `POST /api/admin/plans`
- `PUT /api/admin/plans/:id`
- `POST /api/admin/users/:id/plan` → asignar plan

Alertas:
- Cuando `credits_balance <= 15` → devolver flag en `/api/users/me` para mostrar aviso en UI.

---

## Notas
- No hay integración con Arduino, audio/video real, ni sincronización real entre ventanas (por ahora) en estas maquetas.
- `python -m http.server` solo sirve archivos; la BD y lógica vivirán en la API Python.
- Web Serial puede requerir condiciones del navegador; validar soporte en el entorno final.
- Si cambias la estructura de carpetas, actualiza las rutas relativas en los HTML.
