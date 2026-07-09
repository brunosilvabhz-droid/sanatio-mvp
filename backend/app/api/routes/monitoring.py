from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.services.monitoring_service import run_monitoring

router = APIRouter(prefix="/monitoring", tags=["Monitoramento"], dependencies=[Depends(get_current_user)])


@router.post("/run")
def run(db: Session = Depends(get_db)) -> dict:
    return run_monitoring(db)
