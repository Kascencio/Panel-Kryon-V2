from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from sqlalchemy import select

from ..db import get_db
from ..models import User
from ..auth import verify_password, get_password_hash, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


# ──────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: str | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    name: str | None
    role: str
    credits_balance: int
    low_credits: bool  # True si <= 15

    # Plan actual (si existe)
    plan_id: int | None = None
    plan_name: str | None = None
    therapies_access: str | None = None

    class Config:
        from_attributes = True


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────
@router.post("/login", response_model=TokenResponse)
async def login(form: LoginRequest, db: Session = Depends(get_db)):
    """Login de usuario (email + password)."""
    user = db.execute(select(User).where(User.email == form.email)).scalar_one_or_none()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return TokenResponse(access_token=token)


@router.post("/login/form", response_model=TokenResponse)
async def login_form(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login compatible con OAuth2PasswordRequestForm (para /docs)."""
    user = db.execute(select(User).where(User.email == form.username)).scalar_one_or_none()

    if not user or not verify_password(form.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    return TokenResponse(access_token=token)


@router.post("/register", response_model=UserResponse)
async def register(form: RegisterRequest, db: Session = Depends(get_db)):
    """Registro de nuevo usuario (rol: user)."""
    existing = db.execute(select(User).where(User.email == form.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user = User(
        email=form.email,
        password_hash=get_password_hash(form.password),
        name=form.name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role.value,
        credits_balance=user.credits_balance,
        low_credits=user.credits_balance <= 15,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obtener perfil del usuario actual."""
    plan_id = None
    plan_name = None
    therapies_access = None
    if current_user.user_plan and current_user.user_plan.plan:
        plan_id = current_user.user_plan.plan.id
        plan_name = current_user.user_plan.plan.name
        therapies_access = current_user.user_plan.plan.therapies_access

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role.value,
        credits_balance=current_user.credits_balance,
        low_credits=current_user.credits_balance <= 15,
        plan_id=plan_id,
        plan_name=plan_name,
        therapies_access=therapies_access,
    )
