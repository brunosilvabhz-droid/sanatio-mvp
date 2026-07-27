from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin, alerts, antimicrobial_audits, auth, dashboard, ingestion, interventions, monitoring, patients
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(alerts.router)
app.include_router(antimicrobial_audits.router)
app.include_router(interventions.router)
app.include_router(ingestion.router)
app.include_router(monitoring.router)
app.include_router(dashboard.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mock_soulmv": settings.use_mock_soulmv}
