from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import User, Role, Plan, UserPlan, CreditLedger
from ..auth import require_admin, get_password_hash

router = APIRouter(prefix="/api/admin/users", tags=["admin-users"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class UserOut(BaseModel):
    id: int
    email: str
    name: str | None
    role: str
    is_active: bool
    credits_balance: int
    plan_name: str | None = None

    class Config:
        from_attributes = True


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None
    role: str = "user"
    plan_id: int | None = None  # Opcional: asignar plan al crear


class UpdateCreditsRequest(BaseModel):
    delta: int  # +N para agregar, -N para restar
    reason: str


class AssignPlanRequest(BaseModel):
    plan_id: int


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.get("", response_model=list[UserOut])
async def list_users(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Listar todos los usuarios."""
    users = db.execute(select(User)).scalars().all()
    result = []
    for u in users:
        plan_name = None
        if u.user_plan and u.user_plan.plan:
            plan_name = u.user_plan.plan.name
        result.append(
            UserOut(
                id=u.id,
                email=u.email,
                name=u.name,
                role=u.role.value,
                is_active=u.is_active,
                credits_balance=u.credits_balance,
                plan_name=plan_name,
            )
        )
    return result


@router.post("", response_model=UserOut)
async def create_user(
    form: CreateUserRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Crear usuario (admin puede asignar rol)."""
    existing = db.execute(select(User).where(User.email == form.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya registrado")

    try:
        role = Role(form.role)
    except ValueError:
        raise HTTPException(status_code=400, detail="Rol inválido")

    user = User(
        email=form.email,
        password_hash=get_password_hash(form.password),
        name=form.name,
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    plan_name = None
    # Asignar plan si se proporcionó
    if form.plan_id:
        plan = db.get(Plan, form.plan_id)
        if plan and plan.is_active:
            # Crear UserPlan
            user_plan = UserPlan(user_id=user.id, plan_id=plan.id)
            db.add(user_plan)
            # Agregar créditos del plan
            user.credits_balance += plan.credits_included
            # Registrar en ledger
            ledger = CreditLedger(
                user_id=user.id,
                delta=plan.credits_included,
                reason=f"Plan asignado: {plan.name}"
            )
            db.add(ledger)
            db.commit()
            db.refresh(user)
            plan_name = plan.name

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        credits_balance=user.credits_balance,
        plan_name=plan_name,
    )


@router.post("/{user_id}/credits", response_model=UserOut)
async def update_credits(
    user_id: int,
    form: UpdateCreditsRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Ajustar créditos de un usuario (+N o -N)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    user.credits_balance += form.delta

    # Registrar en ledger
    ledger = CreditLedger(user_id=user.id, delta=form.delta, reason=form.reason)
    db.add(ledger)
    db.commit()
    db.refresh(user)

    plan_name = None
    if user.user_plan and user.user_plan.plan:
        plan_name = user.user_plan.plan.name

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        credits_balance=user.credits_balance,
        plan_name=plan_name,
    )


@router.post("/{user_id}/plan", response_model=UserOut)
async def assign_plan(
    user_id: int,
    form: AssignPlanRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Asignar plan a usuario (reemplaza el anterior)."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    plan = db.get(Plan, form.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    # Eliminar plan anterior si existe
    if user.user_plan:
        db.delete(user.user_plan)

    # Crear nuevo
    user_plan = UserPlan(user_id=user.id, plan_id=plan.id)
    db.add(user_plan)

    # Agregar créditos del plan
    if plan.credits_included > 0:
        user.credits_balance += plan.credits_included
        ledger = CreditLedger(
            user_id=user.id,
            delta=plan.credits_included,
            reason=f"Asignación de plan: {plan.name}",
        )
        db.add(ledger)

    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        is_active=user.is_active,
        credits_balance=user.credits_balance,
        plan_name=plan.name,
    )
