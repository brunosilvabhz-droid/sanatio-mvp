from app.api.routes.ingestion import _risk_reasons


def test_risk_reasons_describe_concrete_clinical_factors() -> None:
    reasons = _risk_reasons(
        {
            "has_positive_culture": True,
            "max_antimicrobial_days": 8,
            "max_invasive_device_days": 9,
            "days_in_hospital": 12,
            "has_active_isolation": True,
        },
        antimicrobial_days=7,
        invasive_device_days=7,
        hospital_stay_days=10,
    )

    assert reasons == [
        "Cultura positiva",
        "Antimicrobiano por 8 dias",
        "Procedimento invasivo por 9 dias",
        "Internacao por 12 dias",
        "Isolamento ativo",
    ]
    assert "risco alto" not in reasons
