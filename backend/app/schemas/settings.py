from pydantic import BaseModel


class SettingRead(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None

    model_config = {"from_attributes": True}


class SettingUpdate(BaseModel):
    key: str
    value: str | None = None
    description: str | None = None
