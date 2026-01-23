from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..config import settings
from ..db import get_db
from ..models import User, Therapy
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/api/therapies", tags=["therapies"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class TherapyOut(BaseModel):
    id: int
    name: str
    description: str | None
    category: str | None

    # Acceso por plan: basic|premium
    access_level: str
    default_duration_sec: int
    color_mode: str
    default_intensity: int

    # Tipo de media guardado (audio/video/both)
    media_type: str
    
    # URLs para cada tiempo
    audio_corto_url: str | None
    audio_mediano_url: str | None
    audio_largo_url: str | None
    audio_url: str | None  # Legacy (equivale a corto)
    video_url: str | None
    
    # Duraciones máximas por tipo (opcionales, con defaults)
    duration_corto_sec: int | None = 300      # 5 min default
    duration_mediano_sec: int | None = 1200   # 20 min default
    duration_largo_sec: int | None = 10800    # 3 hrs default
    
    # Etiquetas personalizadas
    duration_labels: str | None
    
    arduino_config: str | None
    is_active: bool

    class Config:
        from_attributes = True


class CreateTherapyRequest(BaseModel):
    name: str
    description: str | None = None
    category: str | None = None
    access_level: str = "basic"
    default_duration_sec: int = 600
    color_mode: str = "general"
    default_intensity: int = 50
    media_type: str = "audio"
    duration_corto_sec: int = 300
    duration_mediano_sec: int = 1200
    duration_largo_sec: int = 10800
    duration_labels: str | None = None
    arduino_config: str | None = None


class UpdateTherapyRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    access_level: str | None = None
    default_duration_sec: int | None = None
    color_mode: str | None = None
    default_intensity: int | None = None
    media_type: str | None = None
    duration_corto_sec: int | None = None
    duration_mediano_sec: int | None = None
    duration_largo_sec: int | None = None
    duration_labels: str | None = None
    arduino_config: str | None = None
    is_active: bool | None = None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def get_audio_url(path: str | None) -> str | None:
    if not path:
        return None
    return f"/media/audio/{Path(path).name}"


def therapy_to_out(t: Therapy) -> TherapyOut:
    # Legacy audio_url uses audio_corto_path or audio_path
    audio_url = get_audio_url(t.audio_corto_path) or get_audio_url(t.audio_path)
    video_url = f"/media/video/{Path(t.video_path).name}" if t.video_path else None
    
    return TherapyOut(
        id=t.id,
        name=t.name,
        description=t.description,
        category=t.category,
        access_level=getattr(t, "access_level", None) or "basic",
        default_duration_sec=t.default_duration_sec,
        color_mode=t.color_mode,
        default_intensity=getattr(t, 'default_intensity', None) or 50,
        media_type=getattr(t, 'media_type', None) or "audio",
        audio_corto_url=get_audio_url(getattr(t, 'audio_corto_path', None)),
        audio_mediano_url=get_audio_url(getattr(t, 'audio_mediano_path', None)),
        audio_largo_url=get_audio_url(getattr(t, 'audio_largo_path', None)),
        audio_url=audio_url,
        video_url=video_url,
        duration_corto_sec=getattr(t, 'duration_corto_sec', None) or 300,
        duration_mediano_sec=getattr(t, 'duration_mediano_sec', None) or 1200,
        duration_largo_sec=getattr(t, 'duration_largo_sec', None) or 10800,
        duration_labels=getattr(t, 'duration_labels', None),
        arduino_config=t.arduino_config,
        is_active=t.is_active,
    )


# ──────────────────────────────────────────────────────────────
# Endpoints públicos (requiere auth)
# ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[TherapyOut])
async def list_therapies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Listar terapias activas."""
    rows = db.execute(select(Therapy).where(Therapy.is_active == True)).scalars().all()
    return [therapy_to_out(t) for t in rows]


@router.get("/{therapy_id}", response_model=TherapyOut)
async def get_therapy(
    therapy_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Obtener una terapia por ID."""
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")
    return therapy_to_out(therapy)


# ──────────────────────────────────────────────────────────────
# Endpoints admin
# ──────────────────────────────────────────────────────────────
@router.post("", response_model=TherapyOut)
async def create_therapy(
    form: CreateTherapyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Crear nueva terapia."""
    therapy = Therapy(
        name=form.name,
        description=form.description,
        category=form.category,
        access_level=form.access_level,
        default_duration_sec=form.default_duration_sec,
        color_mode=form.color_mode,
        media_type=form.media_type,
        arduino_config=form.arduino_config,
    )
    db.add(therapy)
    db.commit()
    db.refresh(therapy)
    return therapy_to_out(therapy)


@router.put("/{therapy_id}", response_model=TherapyOut)
async def update_therapy(
    therapy_id: int,
    form: UpdateTherapyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Actualizar terapia."""
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    if form.name is not None:
        therapy.name = form.name
    if form.description is not None:
        therapy.description = form.description
    if form.category is not None:
        therapy.category = form.category
    if form.access_level is not None:
        therapy.access_level = form.access_level
    if form.default_duration_sec is not None:
        therapy.default_duration_sec = form.default_duration_sec
    if form.color_mode is not None:
        therapy.color_mode = form.color_mode
    if form.default_intensity is not None:
        therapy.default_intensity = form.default_intensity
    if form.media_type is not None:
        therapy.media_type = form.media_type
    if form.duration_corto_sec is not None:
        therapy.duration_corto_sec = form.duration_corto_sec
    if form.duration_mediano_sec is not None:
        therapy.duration_mediano_sec = form.duration_mediano_sec
    if form.duration_largo_sec is not None:
        therapy.duration_largo_sec = form.duration_largo_sec
    if form.duration_labels is not None:
        therapy.duration_labels = form.duration_labels
    if form.arduino_config is not None:
        therapy.arduino_config = form.arduino_config
    if form.is_active is not None:
        therapy.is_active = form.is_active

    db.commit()
    db.refresh(therapy)
    return therapy_to_out(therapy)


@router.delete("/{therapy_id}")
async def delete_therapy(
    therapy_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Eliminar terapia (soft delete)."""
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    therapy.is_active = False
    db.commit()
    return {"ok": True, "message": "Terapia desactivada"}


# ──────────────────────────────────────────────────────────────
# Upload media
# ──────────────────────────────────────────────────────────────
ALLOWED_AUDIO = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
ALLOWED_VIDEO = {".mp4", ".webm", ".mov", ".avi", ".mkv"}


def _compute_media_type(t: Therapy) -> str:
    has_audio = bool(
        getattr(t, "audio_corto_path", None)
        or getattr(t, "audio_mediano_path", None)
        or getattr(t, "audio_largo_path", None)
        or getattr(t, "audio_path", None)
    )
    has_video = bool(getattr(t, "video_path", None))
    if has_audio and has_video:
        return "both"
    if has_video:
        return "video"
    if has_audio:
        return "audio"
    return getattr(t, "media_type", None) or "audio"


@router.post("/{therapy_id}/audio")
async def upload_audio(
    therapy_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Subir audio para una terapia (legacy - usa audio_corto_path)."""
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Permitidos: {ALLOWED_AUDIO}")

    media_dir = Path(settings.MEDIA_DIR).resolve() / "audio"
    media_dir.mkdir(parents=True, exist_ok=True)

    target = media_dir / f"therapy_{therapy_id}{ext}"
    content = await file.read()
    target.write_bytes(content)

    therapy.audio_path = str(target)
    therapy.audio_corto_path = str(target)  # También guarda en audio_corto
    therapy.media_type = _compute_media_type(therapy)
    db.commit()

    return {"ok": True, "audio_url": f"/media/audio/{target.name}"}


@router.post("/{therapy_id}/audio/{duration_type}")
async def upload_audio_by_duration(
    therapy_id: int,
    duration_type: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Subir audio para una terapia según tipo de duración (corto, mediano, largo)."""
    if duration_type not in ["corto", "mediano", "largo"]:
        raise HTTPException(status_code=400, detail="Tipo de duración inválido. Usar: corto, mediano, largo")
    
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Permitidos: {ALLOWED_AUDIO}")

    media_dir = Path(settings.MEDIA_DIR).resolve() / "audio"
    media_dir.mkdir(parents=True, exist_ok=True)

    # Nombre único por terapia y tipo de duración
    target = media_dir / f"therapy_{therapy_id}_{duration_type}{ext}"
    content = await file.read()
    target.write_bytes(content)

    # Guardar en el campo correspondiente
    if duration_type == "corto":
        therapy.audio_corto_path = str(target)
        therapy.audio_path = str(target)  # También actualiza el legacy
    elif duration_type == "mediano":
        therapy.audio_mediano_path = str(target)
    elif duration_type == "largo":
        therapy.audio_largo_path = str(target)

    therapy.media_type = _compute_media_type(therapy)
    
    db.commit()

    return {"ok": True, "audio_url": f"/media/audio/{target.name}", "duration_type": duration_type}


@router.post("/{therapy_id}/video")
async def upload_video(
    therapy_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Subir video para una terapia."""
    therapy = db.get(Therapy, therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Nombre de archivo requerido")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_VIDEO:
        raise HTTPException(status_code=400, detail=f"Formato no soportado. Permitidos: {ALLOWED_VIDEO}")

    media_dir = Path(settings.MEDIA_DIR).resolve() / "video"
    media_dir.mkdir(parents=True, exist_ok=True)

    target = media_dir / f"therapy_{therapy_id}{ext}"
    content = await file.read()
    target.write_bytes(content)

    therapy.video_path = str(target)
    therapy.media_type = _compute_media_type(therapy)
    db.commit()

    return {"ok": True, "video_url": f"/media/video/{target.name}"}
