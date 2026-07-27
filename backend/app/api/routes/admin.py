from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.setting import Setting
from app.models.user import Role, User
from app.schemas.auth import RoleRead
from app.schemas.settings import SettingRead, SettingUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/roles", response_model=list[RoleRead])
def roles(db: Session = Depends(get_db)) -> list[Role]:
    return list(db.scalars(select(Role).order_by(Role.name)))


@router.get("/users", response_model=list[UserRead])
def users(db: Session = Depends(get_db)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.email)))


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    role = db.scalar(select(Role).where(Role.name == payload.role_name))
    if not role:
        raise HTTPException(status_code=422, detail="Perfil inválido")
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role_id=role.id,
        active=payload.active,
        can_view_patient_name=payload.can_view_patient_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password:
        user.hashed_password = get_password_hash(payload.password)
    if payload.active is not None:
        user.active = payload.active
    if payload.can_view_patient_name is not None:
        user.can_view_patient_name = payload.can_view_patient_name
    if payload.role_name:
        role = db.scalar(select(Role).where(Role.name == payload.role_name))
        if not role:
            raise HTTPException(status_code=422, detail="Perfil inválido")
        user.role_id = role.id
    db.commit()
    db.refresh(user)
    return user


@router.get("/settings", response_model=list[SettingRead])
def settings(db: Session = Depends(get_db)) -> list[Setting]:
    return list(db.scalars(select(Setting).order_by(Setting.key)))


@router.patch("/settings", response_model=SettingRead)
def patch_setting(payload: SettingUpdate, db: Session = Depends(get_db)) -> Setting:
    setting = db.scalar(select(Setting).where(Setting.key == payload.key))
    if not setting:
        setting = Setting(key=payload.key)
        db.add(setting)
    setting.value = payload.value
    setting.description = payload.description
    db.commit()
    db.refresh(setting)
    return setting
