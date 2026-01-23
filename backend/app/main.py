from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .db import SessionLocal
from .migrations import run_migrations
from .seed import run_seed

from .routers import auth, users, plans, therapies, playlists, sessions, analytics, categories


# ──────────────────────────────────────────────────────────────
# Lifespan (startup/shutdown)
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Iniciando Panel Kryon API...")

    # Migraciones ligeras
    migrations_ok = run_migrations()
    if migrations_ok:
        print("✅ Tablas y migraciones verificadas")
    else:
        print("⚠️  Tablas/migraciones no verificadas (BD no disponible)")

    # Crear carpetas de media
    media_dir = Path(settings.MEDIA_DIR).resolve()
    (media_dir / "audio").mkdir(parents=True, exist_ok=True)
    (media_dir / "video").mkdir(parents=True, exist_ok=True)
    print(f"✅ Carpetas de media: {media_dir}")

    # Seed inicial
    if migrations_ok:
        db = SessionLocal()
        try:
            run_seed(db)
        finally:
            db.close()
    else:
        print("⚠️  Seed omitido (BD no disponible)")

    yield

    # Shutdown
    print("👋 Cerrando Panel Kryon API...")


# ──────────────────────────────────────────────────────────────
# App
# ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Panel Kryon API",
    description="API para el sistema de terapias Cabina AQ",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (media)
media_path = Path(settings.MEDIA_DIR).resolve()
media_path.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(media_path)), name="media")

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(plans.router)
app.include_router(therapies.router)
app.include_router(playlists.router)
app.include_router(sessions.router)
app.include_router(analytics.router)
app.include_router(categories.router)


# Health check
@app.get("/health")
async def health():
    return {"status": "ok", "service": "Panel Kryon API"}


@app.get("/")
async def root():
    return {
        "message": "Panel Kryon API v2.0",
        "docs": "/docs",
        "health": "/health",
    }
