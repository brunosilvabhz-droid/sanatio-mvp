from pydantic import BaseModel

from app.schemas.auth import RoleRead


class UserCreate(BaseModel):
    email: str
    full_name: str
    password: str
    role_name: str
    active: bool = True


class UserUpdate(BaseModel):
    full_name: str | None = None
    password: str | None = None
    role_name: str | None = None
    active: bool | None = None


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    active: bool
    role: RoleRead

    model_config = {"from_attributes": True}
