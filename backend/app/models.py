import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────
class Role(str, enum.Enum):
    superadmin = "superadmin"
    admin = "admin"
    user = "user"


# ──────────────────────────────────────────────────────────────
# Users
# ──────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.user)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    credits_balance: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    user_plan: Mapped[Optional["UserPlan"]] = relationship(back_populates="user", uselist=False)
    credit_ledger: Mapped[list["CreditLedger"]] = relationship(back_populates="user")


# ──────────────────────────────────────────────────────────────
# Plans
# ──────────────────────────────────────────────────────────────
class Plan(Base):
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    credits_included: Mapped[int] = mapped_column(Integer, default=0)
    # "all" = acceso a todas, o JSON array de IDs: "[1,2,3]"
    therapies_access: Mapped[str] = mapped_column(String(500), default="all")
    price: Mapped[int] = mapped_column(Integer, default=0)  # en centavos o unidad mínima
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    user_plans: Mapped[list["UserPlan"]] = relationship(back_populates="plan")


class UserPlan(Base):
    __tablename__ = "user_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"), index=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship(back_populates="user_plan")
    plan: Mapped["Plan"] = relationship(back_populates="user_plans")


# ──────────────────────────────────────────────────────────────
# Credits
# ──────────────────────────────────────────────────────────────
class CreditLedger(Base):
    __tablename__ = "credit_ledger"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    delta: Mapped[int] = mapped_column(Integer)  # +N o -N
    reason: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="credit_ledger")


# ──────────────────────────────────────────────────────────────
# Categories (creadas por admin)
# ──────────────────────────────────────────────────────────────
class Category(Base):
    """Categorías de terapias (pueden ser creadas en admin panel)."""
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(String(20), default="#6366f1")
    icon: Mapped[str] = mapped_column(String(10), default="🌀")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────
# Light Modes (fijos, no modificables por usuarios)
# ──────────────────────────────────────────────────────────────
class LightMode(Base):
    """
    Modos de luz disponibles para ESP32.
    NO modificables por usuario, solo admin puede ver/editar.
    """
    __tablename__ = "light_modes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    esp32_command: Mapped[str] = mapped_column(String(50))  # Comando real para ESP32
    color: Mapped[str] = mapped_column(String(20), default="#06b6d4")
    icon: Mapped[str] = mapped_column(String(10), default="🔄")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


# ──────────────────────────────────────────────────────────────
# Therapies
# ──────────────────────────────────────────────────────────────
class Therapy(Base):
    __tablename__ = "therapies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Duración default y modo de luz default
    default_duration_sec: Mapped[int] = mapped_column(Integer, default=600)
    color_mode: Mapped[str] = mapped_column(String(50), default="general")
    default_intensity: Mapped[int] = mapped_column(Integer, default=50)  # 0-100

    # Tipo de media elegido (audio/video/both)
    # Nota: también puede inferirse por archivos cargados, pero este campo guarda la intención.
    media_type: Mapped[str] = mapped_column(String(10), default="audio")

    # Acceso por plan: basic|premium
    access_level: Mapped[str] = mapped_column(String(10), default="basic")

    # Media para distintos tiempos (paths relativos a MEDIA_DIR)
    # Corto: 0-5 min (max 300 seg)
    # Mediano: 6-20 min (max 1200 seg)  
    # Largo: 21 min - 3 hrs (max 10800 seg)
    audio_corto_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_mediano_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    audio_largo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Duraciones máximas por tipo (en segundos)
    duration_corto_sec: Mapped[int] = mapped_column(Integer, default=300)     # 5 min
    duration_mediano_sec: Mapped[int] = mapped_column(Integer, default=1200)  # 20 min
    duration_largo_sec: Mapped[int] = mapped_column(Integer, default=10800)   # 3 hrs
    
    # Legacy: audio_path se mantiene para compatibilidad (equivale a corto)
    audio_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Etiquetas personalizadas para duraciones (JSON: {"corto": "Track 1", "mediano": "Track 2"})
    duration_labels: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Config Arduino (JSON string)
    arduino_config: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────
# Playlists
# ──────────────────────────────────────────────────────────────
class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    items: Mapped[list["PlaylistItem"]] = relationship(back_populates="playlist", order_by="PlaylistItem.order")
    creator: Mapped["User"] = relationship(foreign_keys=[created_by])


class PlaylistItem(Base):
    __tablename__ = "playlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id"), index=True)
    therapy_id: Mapped[int] = mapped_column(ForeignKey("therapies.id"), index=True)
    order: Mapped[int] = mapped_column(Integer, default=0)
    duration_override: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    color_mode_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    playlist: Mapped["Playlist"] = relationship(back_populates="items")
    therapy: Mapped["Therapy"] = relationship()


# ──────────────────────────────────────────────────────────────
# Sessions (Tracking de uso de terapias)
# ──────────────────────────────────────────────────────────────
class SessionStatus(str, enum.Enum):
    started = "started"
    completed = "completed"
    cancelled = "cancelled"
    paused = "paused"


class TherapySession(Base):
    """Registro de cada sesión de terapia realizada."""
    __tablename__ = "therapy_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    therapy_id: Mapped[int] = mapped_column(ForeignKey("therapies.id"), index=True)
    playlist_id: Mapped[Optional[int]] = mapped_column(ForeignKey("playlists.id"), nullable=True, index=True)
    
    # Timing
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    duration_planned_sec: Mapped[int] = mapped_column(Integer, default=0)
    duration_actual_sec: Mapped[int] = mapped_column(Integer, default=0)
    
    # Status
    status: Mapped[SessionStatus] = mapped_column(Enum(SessionStatus), default=SessionStatus.started)
    
    # Créditos consumidos en esta sesión
    credits_consumed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Configuración usada
    color_mode_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    arduino_connected: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Metadatos adicionales (JSON)
    extra_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relaciones
    user: Mapped["User"] = relationship()
    therapy: Mapped["Therapy"] = relationship()


class ActivityLog(Base):
    """Log de actividades del sistema para auditoría."""
    __tablename__ = "activity_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    
    # Tipo de acción
    action: Mapped[str] = mapped_column(String(100), index=True)  # login, logout, session_start, credit_add, etc.
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # user, therapy, session, etc.
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Detalles
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    # Relaciones
    user: Mapped[Optional["User"]] = relationship()


class DailyStats(Base):
    """Estadísticas diarias pre-calculadas para reportes rápidos."""
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[datetime] = mapped_column(DateTime, unique=True, index=True)
    
    # Contadores
    total_sessions: Mapped[int] = mapped_column(Integer, default=0)
    completed_sessions: Mapped[int] = mapped_column(Integer, default=0)
    cancelled_sessions: Mapped[int] = mapped_column(Integer, default=0)
    
    total_duration_min: Mapped[int] = mapped_column(Integer, default=0)
    total_credits_consumed: Mapped[int] = mapped_column(Integer, default=0)
    total_credits_added: Mapped[int] = mapped_column(Integer, default=0)
    
    unique_users: Mapped[int] = mapped_column(Integer, default=0)
    new_users: Mapped[int] = mapped_column(Integer, default=0)
    
    # Top terapia del día
    top_therapy_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    top_therapy_count: Mapped[int] = mapped_column(Integer, default=0)
