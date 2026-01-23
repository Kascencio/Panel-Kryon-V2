"""
Seed inicial: crea Plan Básico, Superadmin y LightModes si no existen.
Se ejecuta en el startup de la aplicación (idempotente).
"""

from sqlalchemy.orm import Session
from sqlalchemy import select

from .config import settings
from .models import Plan, User, Role, LightMode, Category
from .auth import get_password_hash


def run_seed(db: Session) -> None:
    """Ejecutar seed idempotente."""

    # ─────────────────────────────────────────────────────────
    # Plan Básico
    # ─────────────────────────────────────────────────────────
    basic_plan = db.execute(select(Plan).where(Plan.name == "Plan Básico")).scalar_one_or_none()
    if not basic_plan:
        basic_plan = Plan(
            name="Plan Básico",
            description="Plan inicial con acceso básico al sistema.",
            credits_included=10,
            therapies_access="all",
            price=0,
            is_active=True,
        )
        db.add(basic_plan)
        db.commit()
        print("✅ Seed: Plan Básico creado")
    else:
        print("ℹ️  Seed: Plan Básico ya existe")

    # ─────────────────────────────────────────────────────────
    # Superadmin
    # ─────────────────────────────────────────────────────────
    superadmin = db.execute(
        select(User).where(User.email == settings.SUPERADMIN_EMAIL)
    ).scalar_one_or_none()

    if not superadmin:
        superadmin = User(
            email=settings.SUPERADMIN_EMAIL,
            password_hash=get_password_hash(settings.SUPERADMIN_PASSWORD),
            name="Superadmin",
            role=Role.superadmin,
            credits_balance=9999,
            is_active=True,
        )
        db.add(superadmin)
        db.commit()
        print(f"✅ Seed: Superadmin creado ({settings.SUPERADMIN_EMAIL})")
    else:
        print(f"ℹ️  Seed: Superadmin ya existe ({settings.SUPERADMIN_EMAIL})")

    # ─────────────────────────────────────────────────────────
    # Modos de Luz (fijos, no modificables por usuarios)
    # ─────────────────────────────────────────────────────────
    existing_modes = db.execute(select(LightMode)).scalars().all()
    if not existing_modes:
        light_modes = [
            LightMode(name="general", display_name="Patrón Complejo", description="11 patrones variables", esp32_command="general", color="#06b6d4", icon="🔄"),
            LightMode(name="intermitente", display_name="Intermitente", description="Cambio rápido 500ms", esp32_command="intermitente", color="#f59e0b", icon="⚡"),
            LightMode(name="pausado", display_name="Pausado", description="Cambio lento 1.5s", esp32_command="pausado", color="#8b5cf6", icon="⏸️"),
            LightMode(name="cascada", display_name="Cascada", description="Efecto cascada", esp32_command="cascada", color="#10b981", icon="🌊"),
            LightMode(name="cascrev", display_name="Cascada Reversa", description="Cascada invertida", esp32_command="cascrev", color="#182521", icon="🌊"),
            LightMode(name="rojo", display_name="Solo Rojo", description="Rojo sólido", esp32_command="rojo", color="#ef4444", icon="🔴"),
            LightMode(name="verde", display_name="Solo Verde", description="Verde sólido", esp32_command="verde", color="#22c55e", icon="🟢"),
            LightMode(name="azul", display_name="Solo Azul", description="Azul sólido", esp32_command="azul", color="#3b82f6", icon="🔵"),
            LightMode(name="blanco", display_name="Solo Blanco", description="Blanco sólido", esp32_command="blanco", color="#ffffff", icon="⚪"),
        ]
        db.add_all(light_modes)
        db.commit()
        print("✅ Seed: Modos de luz creados (9 modos)")
    else:
        print(f"ℹ️  Seed: Modos de luz ya existen ({len(existing_modes)} modos)")

    # ─────────────────────────────────────────────────────────
    # Categorías por defecto
    # ─────────────────────────────────────────────────────────
    existing_categories = db.execute(select(Category)).scalars().all()
    if not existing_categories:
        default_categories = [
            Category(name="Relajación", description="Terapias para reducir estrés y ansiedad", color="#14b8a6", icon="💆"),
            Category(name="Meditación", description="Sesiones de meditación guiada", color="#8b5cf6", icon="🧘"),
            Category(name="Energía", description="Terapias para aumentar energía y vitalidad", color="#f59e0b", icon="⚡"),
            Category(name="Sueño", description="Mejora del descanso y calidad de sueño", color="#3b82f6", icon="😴"),
            Category(name="Autismo", description="Terapias especializadas para autismo", color="#22c55e", icon="🧩"),
            Category(name="Frecuencias", description="Terapias basadas en frecuencias específicas", color="#ec4899", icon="🎵"),
        ]
        db.add_all(default_categories)
        db.commit()
        print("✅ Seed: Categorías por defecto creadas (6 categorías)")
    else:
        print(f"ℹ️  Seed: Categorías ya existen ({len(existing_categories)} categorías)")
