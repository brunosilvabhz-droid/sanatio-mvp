from pydantic import BaseModel, EmailStr, Field

from app.schemas.auth import RoleRead, UserHospitalRead


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role_name: str
    active: bool = True
    can_view_patient_name: bool = False
    hospital_ids: list[int] = []


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    password: str | None = Field(default=None, min_length=12, max_length=128)
    role_name: str | None = None
    active: bool | None = None
    can_view_patient_name: bool | None = None
    hospital_ids: list[int] | None = None


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    active: bool
    can_view_patient_name: bool
    role: RoleRead
    hospitals: list[UserHospitalRead] = []

    model_config = {"from_attributes": True}
