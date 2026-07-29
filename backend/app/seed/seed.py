from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.monitoring_rule import MonitoringRule
from app.models.setting import Setting
from app.models.user import Role, User

ROLES = [
    ("ADMIN", "Administracao do sistema"),
    ("SCIH", "Servico de Controle de Infeccao Hospitalar"),
    ("FARMACIA", "Farmacia clinica"),
    ("DIRETORIA", "Diretoria"),
    ("MEDICO", "Medico assistente"),
    ("INFECTO", "Infectologista"),
]

USERS = [
    ("admin@sanatio.local", "Administrador SANATIO", "ADMIN", True),
    ("scih@sanatio.local", "Equipe SCIH", "SCIH", True),
    ("farmacia@sanatio.local", "Farmacia", "FARMACIA", False),
]

RULES = [
    ("Mesmo antimicrobiano prolongado", "ANTIMICROBIAL_SAME_PROLONGED", "same_antimicrobial_days", "7", "MEDIA"),
    ("Exposicao antimicrobiana prolongada", "ANTIMICROBIAL_EXPOSURE_PROLONGED", "antimicrobial_exposure_days", "14", "ALTA"),
    ("Trocas frequentes de esquema antimicrobiano", "ANTIMICROBIAL_FREQUENT_SCHEME_CHANGES", "scheme_changes_in_window", "3/7", "ALTA"),
    ("Cultura positiva", "POSITIVE_CULTURE", "has_positive_culture", "true", "ALTA"),
    ("Procedimento invasivo ativo por mais de 7 dias", "INVASIVE_DEVICE_DAYS", "max_invasive_device_days", "7", "MEDIA"),
    ("Paciente internado ha mais de 10 dias", "LONG_STAY", "days_in_hospital", "10", "MEDIA"),
    ("Isolamento ativo", "ACTIVE_ISOLATION", "has_active_isolation", "true", "ALTA"),
    ("Cultura positiva com mesmo antimicrobiano prolongado", "COMPOSITE", "all", '["positive_culture","same_antimicrobial_prolonged"]', "ALTA"),
]

SETTINGS = [
    ("general.institution_name", "Hospital Demonstracao", "Nome da instituicao"),
    ("alerts.threshold.same_antimicrobial_days", "7", "Dias de uso continuo do mesmo antimicrobiano/principio ativo para gerar alerta"),
    ("alerts.threshold.antimicrobial_exposure_days", "14", "Dias consecutivos com algum antimicrobiano para gerar alerta"),
    ("alerts.threshold.antimicrobial_scheme_changes_count", "3", "Quantidade de alteracoes de esquema antimicrobiano para gerar alerta"),
    ("alerts.threshold.antimicrobial_scheme_changes_window_days", "7", "Janela em dias para avaliar trocas frequentes de esquema"),
    ("alerts.threshold.invasive_device_days", "7", "Dias de procedimento invasivo ativo para gerar alerta"),
    ("alerts.threshold.hospital_stay_days", "10", "Dias de internacao para gerar alerta"),
    ("monitoring.schedule.enabled", "false", "Ativa a execucao automatica do monitoramento"),
    ("monitoring.schedule.interval_minutes", "60", "Intervalo entre execucoes automaticas em minutos"),
    ("monitoring.schedule.daily_time", "07:00", "Horario preferencial de execucao diaria"),
    ("monitoring.schedule.timezone", "America/Sao_Paulo", "Fuso horario da agenda automatica"),
]


def main() -> None:
    db = SessionLocal()
    try:
        role_by_name = {}
        for name, description in ROLES:
            role = db.scalar(select(Role).where(Role.name == name))
            if not role:
                role = Role(name=name, description=description)
                db.add(role)
                db.flush()
            role_by_name[name] = role

        for email, full_name, role_name, can_view_patient_name in USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(
                    User(
                        email=email,
                        full_name=full_name,
                        hashed_password=get_password_hash("123456"),
                        role_id=role_by_name[role_name].id,
                        active=True,
                        can_view_patient_name=can_view_patient_name,
                    )
                )

        for name, rule_type, key, value, severity in RULES:
            if not db.scalar(select(MonitoringRule).where(MonitoringRule.rule_type == rule_type)):
                db.add(
                    MonitoringRule(
                        name=name,
                        description=name,
                        rule_type=rule_type,
                        parameter_key=key,
                        parameter_value=value,
                        severity=severity,
                        active=True,
                    )
                )

        for key, value, description in SETTINGS:
            if not db.scalar(select(Setting).where(Setting.key == key)):
                db.add(Setting(key=key, value=value, description=description))
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
