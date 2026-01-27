from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import User, Plan
from ..auth import require_superadmin

router = APIRouter(prefix="/api/admin/plans", tags=["admin-plans"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class PlanOut(BaseModel):
    id: int
    name: str
    description: str | None
    credits_included: int
    therapies_access: str
    price: int
    is_active: bool

    class Config:
        from_attributes = True


class CreatePlanRequest(BaseModel):
    name: str
    description: str | None = None
    credits_included: int = 0
    therapies_access: str = "all"
    price: int = 0


class UpdatePlanRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    credits_included: int | None = None
    therapies_access: str | None = None
    price: int | None = None
    is_active: bool | None = None


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[PlanOut])
async def list_plans(db: Session = Depends(get_db), _: User = Depends(require_superadmin)):
    """Listar todos los planes."""
    plans = db.execute(select(Plan)).scalars().all()
    return [PlanOut.model_validate(p) for p in plans]


@router.post("", response_model=PlanOut)
async def create_plan(
    form: CreatePlanRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Crear nuevo plan."""
    existing = db.execute(select(Plan).where(Plan.name == form.name)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un plan con ese nombre")

    plan = Plan(
        name=form.name,
        description=form.description,
        credits_included=form.credits_included,
        therapies_access=form.therapies_access,
        price=form.price,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return PlanOut.model_validate(plan)


@router.get("/{plan_id}", response_model=PlanOut)
async def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Obtener un plan por ID."""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return PlanOut.model_validate(plan)


@router.put("/{plan_id}", response_model=PlanOut)
async def update_plan(
    plan_id: int,
    form: UpdatePlanRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Actualizar plan."""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    if form.name is not None:
        plan.name = form.name
    if form.description is not None:
        plan.description = form.description
    if form.credits_included is not None:
        plan.credits_included = form.credits_included
    if form.therapies_access is not None:
        plan.therapies_access = form.therapies_access
    if form.price is not None:
        plan.price = form.price
    if form.is_active is not None:
        plan.is_active = form.is_active

    db.commit()
    db.refresh(plan)
    return PlanOut.model_validate(plan)


@router.delete("/{plan_id}")
async def delete_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_superadmin),
):
    """Eliminar plan (soft delete: desactivar)."""
    plan = db.get(Plan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    plan.is_active = False
    db.commit()
    return {"ok": True, "message": "Plan desactivado"}
