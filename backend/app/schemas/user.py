from pydantic import BaseModel

from app.schemas.auth import RoleRead


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role_name: str
    active: bool = True
    can_view_patient_name: bool = False


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    role_name: str | None = None
    active: bool | None = None
    can_view_patient_name: bool | None = None


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    active: bool
    can_view_patient_name: bool
    role: RoleRead

    model_config = {"from_attributes": True}
