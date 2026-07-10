from pydantic import BaseModel, Field


class MonitoringScheduleRead(BaseModel):
    enabled: bool
    interval_minutes: int
    daily_time: str
    timezone: str


class MonitoringScheduleUpdate(BaseModel):
    enabled: bool
    interval_minutes: int = Field(ge=5, le=1440)
    daily_time: str
    timezone: str = "America/Sao_Paulo"
