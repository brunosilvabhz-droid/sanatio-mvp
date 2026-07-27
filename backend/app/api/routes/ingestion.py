import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.alert import Alert
from app.models.hospital_integration import HospitalIntegration
from app.models.patient_monitoring_snapshot import PatientMonitoringSnapshot
from app.schemas.hospital_integration import HospitalIntegrationCreate, HospitalIntegrationRead, IngestPayload

router = APIRouter(tags=["Integracao hospitalar"])


@router.get("/hospital-integrations", response_model=list[HospitalIntegrationRead], dependencies=[Depends(require_admin)])
def list_integrations(db: Session = Depends(get_db)) -> list[HospitalIntegration]:
    return list(db.scalars(select(HospitalIntegration).order_by(HospitalIntegration.created_at.desc())))


@router.post("/hospital-integrations", response_model=HospitalIntegrationRead, dependencies=[Depends(require_admin)])
def create_integration(payload: HospitalIntegrationCreate, db: Session = Depends(get_db)) -> HospitalIntegration:
    integration = HospitalIntegration(hospital_name=payload.hospital_name, token=secrets.token_urlsafe(32), active=True)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


@router.post("/ingest/snapshots")
def ingest_snapshots(
    payload: IngestPayload,
    x_sanatio_token: str | None = Header(default=None, alias="X-Sanatio-Token"),
    db: Session = Depends(get_db),
) -> dict:
    integration = db.scalar(select(HospitalIntegration).where(HospitalIntegration.token == x_sanatio_token, HospitalIntegration.active.is_(True)))
    if not integration:
        raise HTTPException(status_code=401, detail="Token hospitalar invalido")

    created_alerts = 0
    for item in payload.patients:
        db.add(PatientMonitoringSnapshot(**item.model_dump()))
        reasons = []
        if item.risk_status == "alto":
            reasons.append("risco alto")
        if item.has_positive_culture:
            reasons.append("cultura positiva")
        if item.max_antimicrobial_days >= 7:
            reasons.append(f"antimicrobiano por {item.max_antimicrobial_days} dias")
        if item.max_invasive_device_days >= 7:
            reasons.append(f"procedimento invasivo por {item.max_invasive_device_days} dias")
        if item.days_in_hospital >= 10:
            reasons.append(f"{item.days_in_hospital} dias de internacao")
        if not reasons:
            continue
        existing = db.scalar(
            select(Alert).where(
                Alert.cd_atendimento == item.cd_atendimento,
                Alert.status.in_(["ABERTO", "EM_ANALISE"]),
                Alert.source == "client_ingestion",
            )
        )
        if existing:
            continue
        db.add(
            Alert(
                cd_atendimento=item.cd_atendimento,
                cd_paciente=item.cd_paciente,
                patient_name=None,
                unit=item.unit,
                rule_id=None,
                alert_type="INGESTED_RISK",
                severity="ALTA" if item.risk_status == "alto" else "MEDIA",
                title="Alerta recebido do hospital",
                description="Motivos: " + ", ".join(reasons),
                recommendation="Avaliar paciente e registrar evolucao/intervencao quando necessario.",
                status="ABERTO",
                source="client_ingestion",
            )
        )
        created_alerts += 1
    db.commit()
    return {"hospital": integration.hospital_name, "snapshots_received": len(payload.patients), "alerts_created": created_alerts}
