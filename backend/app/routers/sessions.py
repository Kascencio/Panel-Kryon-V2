from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import User, Therapy, TherapySession, SessionStatus, CreditLedger, ActivityLog
from ..auth import require_auth

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class StartSessionRequest(BaseModel):
    therapy_id: int
    playlist_id: int | None = None
    duration_planned_sec: int
    color_mode: str | None = None
    arduino_connected: bool = False


class EndSessionRequest(BaseModel):
    status: str = "completed"  # completed, cancelled, paused
    duration_actual_sec: int | None = None


class SessionOut(BaseModel):
    id: int
    therapy_id: int
    therapy_name: str
    started_at: datetime
    ended_at: datetime | None
    duration_planned_sec: int
    duration_actual_sec: int
    status: str
    credits_consumed: int
    
    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def log_activity(
    db: Session,
    user_id: int | None,
    action: str,
    entity_type: str | None = None,
    entity_id: int | None = None,
    description: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
):
    """Registrar actividad en el log."""
    log = ActivityLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(log)


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.post("/start", response_model=SessionOut)
async def start_session(
    form: StartSessionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Iniciar una nueva sesión de terapia."""
    # Verificar terapia existe
    therapy = db.get(Therapy, form.therapy_id)
    if not therapy or not therapy.is_active:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    # Verificar acceso por plan (server-side, para evitar bypass)
    plan_access = None
    if user.user_plan and user.user_plan.plan and user.user_plan.plan.is_active:
        plan_access = user.user_plan.plan.therapies_access

    def _is_allowed_by_plan(access_value: str | None, t: Therapy) -> bool:
        # Admins siempre pueden
        if getattr(user, "role", None) and getattr(user.role, "value", None) in {"admin", "superadmin"}:
            return True

        # Sin plan asignado => básico
        if not access_value:
            return (getattr(t, "access_level", None) or "basic") != "premium"

        v = str(access_value).strip()
        if v in {"all", "premium"}:
            return True
        if v == "basic":
            return (getattr(t, "access_level", None) or "basic") != "premium"

        # Lista de IDs permitidos (JSON)
        if v.startswith("["):
            try:
                allowed_ids = json.loads(v)
                if isinstance(allowed_ids, list):
                    return int(t.id) in {int(x) for x in allowed_ids if str(x).isdigit() or isinstance(x, int)}
            except Exception:
                return True  # fallback: no bloquear por formato inesperado

        # Fallback: no bloquear
        return True

    if not _is_allowed_by_plan(plan_access, therapy):
        raise HTTPException(status_code=403, detail="Terapia no disponible en tu plan")
    
    # Verificar créditos suficientes (1 crédito por sesión)
    if user.credits_balance < 1:
        raise HTTPException(status_code=400, detail="Créditos insuficientes")
    
    # Crear sesión
    session = TherapySession(
        user_id=user.id,
        therapy_id=form.therapy_id,
        playlist_id=form.playlist_id,
        duration_planned_sec=form.duration_planned_sec,
        color_mode_used=form.color_mode or therapy.color_mode,
        arduino_connected=form.arduino_connected,
        status=SessionStatus.started,
    )
    db.add(session)
    
    # Log de actividad
    log_activity(
        db,
        user_id=user.id,
        action="session_start",
        entity_type="therapy",
        entity_id=form.therapy_id,
        description=f"Inició sesión: {therapy.name}",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    
    db.commit()
    db.refresh(session)
    
    return SessionOut(
        id=session.id,
        therapy_id=session.therapy_id,
        therapy_name=therapy.name,
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_planned_sec=session.duration_planned_sec,
        duration_actual_sec=session.duration_actual_sec,
        status=session.status.value,
        credits_consumed=session.credits_consumed,
    )


@router.post("/{session_id}/end", response_model=SessionOut)
async def end_session(
    session_id: int,
    form: EndSessionRequest,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Finalizar una sesión de terapia."""
    session = db.get(TherapySession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if session.user_id != user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta sesión")
    
    if session.status != SessionStatus.started:
        raise HTTPException(status_code=400, detail="La sesión ya fue finalizada")
    
    therapy = db.get(Therapy, session.therapy_id)
    
    # Calcular duración real
    now = datetime.utcnow()
    if form.duration_actual_sec is not None:
        actual_duration = form.duration_actual_sec
    else:
        actual_duration = int((now - session.started_at).total_seconds())
    
    # Actualizar sesión
    session.ended_at = now
    session.duration_actual_sec = actual_duration
    
    # Determinar status
    try:
        session.status = SessionStatus(form.status)
    except ValueError:
        session.status = SessionStatus.completed
    
    # Consumir crédito solo si se completó la sesión
    credits_to_consume = 0
    if session.status == SessionStatus.completed:
        credits_to_consume = 1
        session.credits_consumed = credits_to_consume
        
        # Descontar crédito del usuario
        user.credits_balance -= credits_to_consume
        
        # Registrar en ledger
        ledger = CreditLedger(
            user_id=user.id,
            delta=-credits_to_consume,
            reason=f"Sesión completada: {therapy.name if therapy else 'Terapia'}",
        )
        db.add(ledger)
    
    # Log de actividad
    log_activity(
        db,
        user_id=user.id,
        action=f"session_{form.status}",
        entity_type="session",
        entity_id=session.id,
        description=f"Sesión {form.status}: {therapy.name if therapy else 'Terapia'} ({actual_duration // 60} min)",
        ip_address=request.client.host if request.client else None,
    )
    
    db.commit()
    db.refresh(session)
    
    return SessionOut(
        id=session.id,
        therapy_id=session.therapy_id,
        therapy_name=therapy.name if therapy else "Unknown",
        started_at=session.started_at,
        ended_at=session.ended_at,
        duration_planned_sec=session.duration_planned_sec,
        duration_actual_sec=session.duration_actual_sec,
        status=session.status.value,
        credits_consumed=session.credits_consumed,
    )


@router.get("/my", response_model=list[SessionOut])
async def get_my_sessions(
    limit: int = 20,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Obtener mis sesiones recientes."""
    stmt = (
        select(TherapySession)
        .where(TherapySession.user_id == user.id)
        .order_by(TherapySession.started_at.desc())
        .limit(limit)
    )
    
    sessions = db.execute(stmt).scalars().all()
    
    items = []
    for s in sessions:
        therapy = db.get(Therapy, s.therapy_id)
        items.append(SessionOut(
            id=s.id,
            therapy_id=s.therapy_id,
            therapy_name=therapy.name if therapy else "Unknown",
            started_at=s.started_at,
            ended_at=s.ended_at,
            duration_planned_sec=s.duration_planned_sec,
            duration_actual_sec=s.duration_actual_sec,
            status=s.status.value,
            credits_consumed=s.credits_consumed,
        ))
    
    return items


@router.get("/active")
async def get_active_session(
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Verificar si hay una sesión activa."""
    stmt = (
        select(TherapySession)
        .where(
            TherapySession.user_id == user.id,
            TherapySession.status == SessionStatus.started,
        )
        .order_by(TherapySession.started_at.desc())
        .limit(1)
    )
    
    session = db.execute(stmt).scalar_one_or_none()
    
    if not session:
        return {"active": False}
    
    therapy = db.get(Therapy, session.therapy_id)
    
    return {
        "active": True,
        "session": SessionOut(
            id=session.id,
            therapy_id=session.therapy_id,
            therapy_name=therapy.name if therapy else "Unknown",
            started_at=session.started_at,
            ended_at=session.ended_at,
            duration_planned_sec=session.duration_planned_sec,
            duration_actual_sec=session.duration_actual_sec,
            status=session.status.value,
            credits_consumed=session.credits_consumed,
        )
    }
