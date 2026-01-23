from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from ..db import get_db
from ..models import User, Playlist, PlaylistItem, Therapy
from ..auth import require_auth, require_admin

router = APIRouter(prefix="/api/playlists", tags=["playlists"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class PlaylistItemOut(BaseModel):
    id: int
    therapy_id: int
    therapy_name: str
    order: int
    duration_override: int | None
    color_mode_override: str | None


class PlaylistOut(BaseModel):
    id: int
    name: str
    created_by: int
    created_by_name: str | None
    items_count: int
    total_duration_min: int
    items: list[PlaylistItemOut] = []


class CreatePlaylistRequest(BaseModel):
    name: str


class UpdatePlaylistRequest(BaseModel):
    name: str | None = None


class AddItemRequest(BaseModel):
    therapy_id: int
    duration_override: int | None = None
    color_mode_override: str | None = None


class UpdateItemRequest(BaseModel):
    order: int | None = None
    duration_override: int | None = None
    color_mode_override: str | None = None


class ReorderItemsRequest(BaseModel):
    item_ids: list[int]


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def playlist_to_out(playlist: Playlist, include_items: bool = False) -> PlaylistOut:
    """Convertir Playlist a PlaylistOut."""
    creator = playlist.creator if hasattr(playlist, 'creator') else None
    
    items_out = []
    total_duration = 0
    
    for item in playlist.items:
        therapy = item.therapy
        duration = item.duration_override or therapy.default_duration_sec
        total_duration += duration
        
        if include_items:
            items_out.append(PlaylistItemOut(
                id=item.id,
                therapy_id=item.therapy_id,
                therapy_name=therapy.name,
                order=item.order,
                duration_override=item.duration_override,
                color_mode_override=item.color_mode_override,
            ))
    
    return PlaylistOut(
        id=playlist.id,
        name=playlist.name,
        created_by=playlist.created_by,
        created_by_name=creator.name if creator else None,
        items_count=len(playlist.items),
        total_duration_min=total_duration // 60,
        items=items_out if include_items else [],
    )


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[PlaylistOut])
async def list_playlists(db: Session = Depends(get_db), user: User = Depends(require_auth)):
    """Listar todas las playlists."""
    stmt = (
        select(Playlist)
        .options(
            joinedload(Playlist.items).joinedload(PlaylistItem.therapy),
        )
        .order_by(Playlist.created_at.desc())
    )
    playlists = db.execute(stmt).unique().scalars().all()
    return [playlist_to_out(p) for p in playlists]


@router.get("/{playlist_id}", response_model=PlaylistOut)
async def get_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Obtener una playlist con sus items."""
    stmt = (
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(
            joinedload(Playlist.items).joinedload(PlaylistItem.therapy),
        )
    )
    playlist = db.execute(stmt).unique().scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    return playlist_to_out(playlist, include_items=True)


@router.post("", response_model=PlaylistOut)
async def create_playlist(
    form: CreatePlaylistRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Crear nueva playlist."""
    playlist = Playlist(
        name=form.name,
        created_by=user.id,
    )
    db.add(playlist)
    db.commit()
    db.refresh(playlist)
    
    return PlaylistOut(
        id=playlist.id,
        name=playlist.name,
        created_by=playlist.created_by,
        created_by_name=user.name,
        items_count=0,
        total_duration_min=0,
        items=[],
    )


@router.put("/{playlist_id}", response_model=PlaylistOut)
async def update_playlist(
    playlist_id: int,
    form: UpdatePlaylistRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Actualizar playlist."""
    stmt = (
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(joinedload(Playlist.items).joinedload(PlaylistItem.therapy))
    )
    playlist = db.execute(stmt).unique().scalar_one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    
    if form.name is not None:
        playlist.name = form.name
    
    db.commit()
    db.refresh(playlist)
    return playlist_to_out(playlist, include_items=True)


@router.delete("/{playlist_id}")
async def delete_playlist(
    playlist_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Eliminar playlist."""
    playlist = db.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    
    # Eliminar items primero
    for item in playlist.items:
        db.delete(item)
    
    db.delete(playlist)
    db.commit()
    return {"ok": True, "message": "Playlist eliminada"}


# ──────────────────────────────────────────────────────────────
# Items endpoints
# ──────────────────────────────────────────────────────────────
@router.post("/{playlist_id}/items", response_model=PlaylistItemOut)
async def add_item(
    playlist_id: int,
    form: AddItemRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Agregar terapia a playlist."""
    playlist = db.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    
    therapy = db.get(Therapy, form.therapy_id)
    if not therapy:
        raise HTTPException(status_code=404, detail="Terapia no encontrada")
    
    # Obtener el orden máximo actual
    max_order = max([item.order for item in playlist.items], default=-1)
    
    item = PlaylistItem(
        playlist_id=playlist_id,
        therapy_id=form.therapy_id,
        order=max_order + 1,
        duration_override=form.duration_override,
        color_mode_override=form.color_mode_override,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return PlaylistItemOut(
        id=item.id,
        therapy_id=item.therapy_id,
        therapy_name=therapy.name,
        order=item.order,
        duration_override=item.duration_override,
        color_mode_override=item.color_mode_override,
    )


@router.put("/{playlist_id}/items/{item_id}", response_model=PlaylistItemOut)
async def update_item(
    playlist_id: int,
    item_id: int,
    form: UpdateItemRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Actualizar item de playlist."""
    item = db.get(PlaylistItem, item_id)
    if not item or item.playlist_id != playlist_id:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    if form.order is not None:
        item.order = form.order
    if form.duration_override is not None:
        item.duration_override = form.duration_override
    if form.color_mode_override is not None:
        item.color_mode_override = form.color_mode_override
    
    db.commit()
    db.refresh(item)
    
    therapy = db.get(Therapy, item.therapy_id)
    return PlaylistItemOut(
        id=item.id,
        therapy_id=item.therapy_id,
        therapy_name=therapy.name,
        order=item.order,
        duration_override=item.duration_override,
        color_mode_override=item.color_mode_override,
    )


@router.delete("/{playlist_id}/items/{item_id}")
async def delete_item(
    playlist_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Eliminar item de playlist."""
    item = db.get(PlaylistItem, item_id)
    if not item or item.playlist_id != playlist_id:
        raise HTTPException(status_code=404, detail="Item no encontrado")
    
    db.delete(item)
    db.commit()
    return {"ok": True, "message": "Item eliminado"}


@router.post("/{playlist_id}/reorder")
async def reorder_items(
    playlist_id: int,
    form: ReorderItemsRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth),
):
    """Reordenar items de playlist."""
    playlist = db.get(Playlist, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist no encontrada")
    
    for order, item_id in enumerate(form.item_ids):
        item = db.get(PlaylistItem, item_id)
        if item and item.playlist_id == playlist_id:
            item.order = order
    
    db.commit()
    return {"ok": True, "message": "Items reordenados"}
