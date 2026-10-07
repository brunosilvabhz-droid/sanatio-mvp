from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.routes import admin, alerts, antimicrobial_audits, antimicrobial_products, auth, dashboard, epidemiology, epidemiology_reference, ingestion, interventions, lab_pdf, monitoring, patients, support_tickets
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    docs_url=None if settings.is_production else "/docs",
    redoc_url=None if settings.is_production else "/redoc",
    openapi_url=None if settings.is_production else "/openapi.json",
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex or None,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(alerts.router)
app.include_router(antimicrobial_audits.router)
app.include_router(antimicrobial_products.router)
app.include_router(interventions.router)
app.include_router(epidemiology.router)
app.include_router(epidemiology_reference.router)
app.include_router(ingestion.router)
app.include_router(lab_pdf.router)
app.include_router(monitoring.router)
app.include_router(dashboard.router)
app.include_router(support_tickets.router)
app.include_router(admin.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
