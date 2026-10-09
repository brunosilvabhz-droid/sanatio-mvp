from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import require_admin, require_admin_or_support
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.setting import Setting
from app.models.hospital_integration import HospitalIntegration
from app.models.user import Role, User, UserHospital
from app.schemas.auth import RoleRead
from app.schemas.settings import SettingRead, SettingUpdate
from app.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(tags=["Admin"], dependencies=[Depends(require_admin_or_support)])


def _allowed_hospital_ids(user: User) -> set[int] | None:
    if user.role.name == "ADMIN":
        return None
    return {hospital.id for hospital in user.hospitals}


def _validate_assignment(current_user: User, role_name: str, hospital_ids: list[int]) -> None:
    if current_user.role.name == "SUPORTE_TI" and role_name == "ADMIN":
        raise HTTPException(status_code=403, detail="SUPORTE_TI não pode criar ou alterar administradores gerais")
    allowed = _allowed_hospital_ids(current_user)
    if allowed is not None and not set(hospital_ids).issubset(allowed):
        raise HTTPException(status_code=403, detail="Hospital fora da área de atuação do usuário")
    if role_name != "ADMIN" and not hospital_ids:
        raise HTTPException(status_code=422, detail="Selecione ao menos um hospital")


def _set_hospitals(db: Session, user: User, hospital_ids: list[int]) -> None:
    existing = {hospital.id for hospital in db.scalars(select(HospitalIntegration).where(HospitalIntegration.id.in_(hospital_ids))).all()} if hospital_ids else set()
    if existing != set(hospital_ids):
        raise HTTPException(status_code=422, detail="Um ou mais hospitais são inválidos")
    db.query(UserHospital).filter(UserHospital.user_id == user.id).delete(synchronize_session=False)
    for hospital_id in hospital_ids:
        db.add(UserHospital(user_id=user.id, hospital_id=hospital_id))


@router.get("/roles", response_model=list[RoleRead])
def roles(db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_support)) -> list[Role]:
    stmt = select(Role).order_by(Role.name)
    if current_user.role.name == "SUPORTE_TI":
        stmt = stmt.where(Role.name != "ADMIN")
    return list(db.scalars(stmt))


@router.get("/user-hospitals")
def user_hospitals(db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_support)) -> list[dict]:
    stmt = select(HospitalIntegration).where(HospitalIntegration.active.is_(True)).order_by(HospitalIntegration.hospital_name)
    allowed = _allowed_hospital_ids(current_user)
    if allowed is not None:
        stmt = stmt.where(HospitalIntegration.id.in_(allowed))
    return [{"id": item.id, "hospital_name": item.hospital_name} for item in db.scalars(stmt)]


@router.get("/users", response_model=list[UserRead])
def users(db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_support)) -> list[User]:
    stmt = select(User).options(selectinload(User.role), selectinload(User.hospitals)).order_by(User.email)
    allowed = _allowed_hospital_ids(current_user)
    if allowed is not None:
        stmt = stmt.join(UserHospital).where(UserHospital.hospital_id.in_(allowed), User.role.has(Role.name != "ADMIN")).distinct()
    return list(db.scalars(stmt))


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_support)) -> User:
    normalized_email = str(payload.email).strip().lower()
    role = db.scalar(select(Role).where(Role.name == payload.role_name))
    if not role:
        raise HTTPException(status_code=422, detail="Perfil inválido")
    _validate_assignment(current_user, role.name, payload.hospital_ids)
    if db.scalar(select(User).where(User.email == normalized_email)):
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")
    user = User(
        email=normalized_email,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role_id=role.id,
        active=payload.active,
        can_view_patient_name=payload.can_view_patient_name,
    )
    db.add(user)
    db.flush()
    _set_hospitals(db, user, payload.hospital_ids)
    db.commit()
    return db.scalar(select(User).options(selectinload(User.role), selectinload(User.hospitals)).where(User.id == user.id))


@router.patch("/users/{user_id}", response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin_or_support)) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    allowed = _allowed_hospital_ids(current_user)
    if allowed is not None and (user.role.name == "ADMIN" or not {hospital.id for hospital in user.hospitals}.intersection(allowed)):
        raise HTTPException(status_code=403, detail="Usuário fora da área de atuação")
    if payload.email is not None:
        normalized_email = str(payload.email).strip().lower()
        email_owner = db.scalar(select(User).where(User.email == normalized_email, User.id != user.id))
        if email_owner:
            raise HTTPException(status_code=409, detail="E-mail já cadastrado")
        user.email = normalized_email
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
    target_role = payload.role_name or user.role.name
    target_hospitals = payload.hospital_ids if payload.hospital_ids is not None else [hospital.id for hospital in user.hospitals]
    _validate_assignment(current_user, target_role, target_hospitals)
    if payload.hospital_ids is not None:
        _set_hospitals(db, user, payload.hospital_ids)
    db.commit()
    return db.scalar(select(User).options(selectinload(User.role), selectinload(User.hospitals)).where(User.id == user.id))


@router.get("/settings", response_model=list[SettingRead], dependencies=[Depends(require_admin)])
def settings(db: Session = Depends(get_db)) -> list[Setting]:
    return list(db.scalars(select(Setting).order_by(Setting.key)))


@router.patch("/settings", response_model=SettingRead, dependencies=[Depends(require_admin)])
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
