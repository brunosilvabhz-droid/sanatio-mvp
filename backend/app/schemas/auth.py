from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RoleRead(BaseModel):
    id: int
    name: str
    description: str | None = None

    model_config = {"from_attributes": True}


class UserRead(BaseModel):
    id: int
    email: str
    full_name: str
    active: bool
    can_view_patient_name: bool
    role: RoleRead

    model_config = {"from_attributes": True}
