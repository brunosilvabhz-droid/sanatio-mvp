from datetime import datetime

from pydantic import BaseModel


class MonitoringRunRead(BaseModel):
    source_key: str | None = None
    source_type: str | None = None
    id: int
    triggered_by_user_id: int | None
    triggered_by_name: str | None
    triggered_by_email: str | None
    status: str
    patients_processed: int
    alerts_created: int
    duration_ms: int | None
    error_message: str | None
    started_at: datetime
    finished_at: datetime | None


class MonitoringRunResult(BaseModel):
    run_id: int
    patients_processed: int
    alerts_created: int
    status: str
