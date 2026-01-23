"""
Router para gestión de categorías y modos de luz.
- Categorías: Pueden crearse/editarse desde el panel de admin.
- Modos de luz: Son fijos (no modificables desde frontend).
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import User, Category, LightMode
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/api/categories", tags=["categories"])


def _slugify(value: str) -> str:
    return value.lower().replace(" ", "_").replace("/", "_")


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class CategoryOut(BaseModel):
    id: int
    name: str
    slug: str = ""  # Alias for name (compatibility)
    description: str | None
    color: str
    icon: str
    is_active: bool

    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        if 'slug' not in data or not data['slug']:
            data['slug'] = _slugify(data.get('name', ''))
        super().__init__(**data)


class CreateCategoryRequest(BaseModel):
    name: str
    description: str | None = None
    color: str = "#6366f1"
    icon: str = "🌀"


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    color: str | None = None
    icon: str | None = None
    is_active: bool | None = None


class LightModeOut(BaseModel):
    id: int
    name: str
    slug: str = ""  # Alias for name (compatibility)
    display_name: str
    description: str | None
    esp32_command: str
    color: str
    icon: str
    is_active: bool

    class Config:
        from_attributes = True
    
    def __init__(self, **data):
        if 'slug' not in data or not data['slug']:
            data['slug'] = _slugify(data.get('name', ''))
        super().__init__(**data)


# ──────────────────────────────────────────────────────────────
# Categories Endpoints (Users can view, Admin can CRUD)
# ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[CategoryOut])
async def list_categories(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Listar categorías activas (para usuarios)."""
    rows = db.execute(select(Category).where(Category.is_active == True)).scalars().all()
    return list(rows)


@router.get("/all", response_model=list[CategoryOut])
async def list_all_categories(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Listar todas las categorías incluyendo inactivas (admin)."""
    rows = db.execute(select(Category).order_by(Category.id)).scalars().all()
    return list(rows)


@router.post("", response_model=CategoryOut)
async def create_category(
    form: CreateCategoryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Crear nueva categoría (admin)."""
    # Check if name exists
    existing = db.execute(
        select(Category).where(Category.name == form.name)
    ).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una categoría con ese nombre")

    category = Category(
        name=form.name,
        description=form.description,
        color=form.color,
        icon=form.icon,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    form: UpdateCategoryRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Actualizar categoría (admin)."""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")

    if form.name is not None:
        # Check duplicate name
        existing = db.execute(
            select(Category).where(Category.name == form.name, Category.id != category_id)
        ).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Ya existe otra categoría con ese nombre")
        category.name = form.name
    
    if form.description is not None:
        category.description = form.description
    if form.color is not None:
        category.color = form.color
    if form.icon is not None:
        category.icon = form.icon
    if form.is_active is not None:
        category.is_active = form.is_active

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Eliminar categoría (admin). Soft delete."""
    category = db.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    
    # Soft delete
    category.is_active = False
    db.commit()
    return {"message": "Categoría desactivada"}


# ──────────────────────────────────────────────────────────────
# Light Modes Endpoints (Read-only for everyone)
# ──────────────────────────────────────────────────────────────
@router.get("/light-modes", response_model=list[LightModeOut])
async def list_light_modes(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Listar modos de luz disponibles.
    Estos modos son fijos y no pueden ser modificados desde el frontend.
    Solo se usan para personalización temporal de sesiones.
    """
    rows = db.execute(
        select(LightMode).where(LightMode.is_active == True).order_by(LightMode.id)
    ).scalars().all()
    
    # If no modes in DB, return hardcoded defaults
    if not rows:
        return get_default_light_modes()
    
    return list(rows)


@router.get("/light-modes/all", response_model=list[LightModeOut])
async def list_all_light_modes(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Listar todos los modos de luz (admin)."""
    rows = db.execute(select(LightMode).order_by(LightMode.id)).scalars().all()
    
    if not rows:
        return get_default_light_modes()
    
    return list(rows)


def get_default_light_modes():
    """
    Modos de luz por defecto (hardcoded).
    Estos se usan si no hay modos en la base de datos.
    """
    return [
        LightModeOut(id=1, name="general", display_name="Patrón Complejo", description="11 patrones variables", esp32_command="general", color="#06b6d4", icon="🔄", is_active=True),
        LightModeOut(id=2, name="intermitente", display_name="Intermitente", description="Cambio rápido 500ms", esp32_command="intermitente", color="#f59e0b", icon="⚡", is_active=True),
        LightModeOut(id=3, name="pausado", display_name="Pausado", description="Cambio lento 1.5s", esp32_command="pausado", color="#8b5cf6", icon="⏸️", is_active=True),
        LightModeOut(id=4, name="cascada", display_name="Cascada", description="Efecto cascada", esp32_command="cascada", color="#10b981", icon="🌊", is_active=True),
        LightModeOut(id=5, name="cascrev", display_name="Cascada Reversa", description="Cascada invertida", esp32_command="cascrev", color="#182521", icon="🌊", is_active=True),
        LightModeOut(id=6, name="rojo", display_name="Solo Rojo", description="Rojo sólido", esp32_command="rojo", color="#ef4444", icon="🔴", is_active=True),
        LightModeOut(id=7, name="verde", display_name="Solo Verde", description="Verde sólido", esp32_command="verde", color="#22c55e", icon="🟢", is_active=True),
        LightModeOut(id=8, name="azul", display_name="Solo Azul", description="Azul sólido", esp32_command="azul", color="#3b82f6", icon="🔵", is_active=True),
        LightModeOut(id=9, name="blanco", display_name="Solo Blanco", description="Blanco sólido", esp32_command="blanco", color="#ffffff", icon="⚪", is_active=True),
    ]
