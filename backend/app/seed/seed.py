from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.monitoring_rule import MonitoringRule
from app.models.setting import Setting
from app.models.user import Role, User

ROLES = [
    ("ADMIN", "Administração do sistema"),
    ("SCIH", "Serviço de Controle de Infecção Hospitalar"),
    ("FARMACIA", "Farmácia clínica"),
    ("DIRETORIA", "Diretoria"),
]

USERS = [
    ("admin@sanatio.local", "Administrador SANATIO", "ADMIN"),
    ("scih@sanatio.local", "Equipe SCIH", "SCIH"),
    ("farmacia@sanatio.local", "Farmácia", "FARMACIA"),
]

RULES = [
    ("Antimicrobiano ativo por mais de 7 dias", "ANTIMICROBIAL_GT7", "dias_uso", "7", "MEDIA"),
    ("Cultura positiva", "POSITIVE_CULTURE", "sn_positivo", "S", "ALTA"),
    ("Procedimento invasivo ativo por mais de 7 dias", "INVASIVE_GT7", "dias_permanencia", "7", "MEDIA"),
    ("Paciente internado há mais de 10 dias", "LONG_STAY", "dias_internacao", "10", "MEDIA"),
    ("Isolamento ativo", "ACTIVE_ISOLATION", "sn_ativo", "S", "ALTA"),
]

SETTINGS = [
    ("oracle.connection.mode", "env", "Conexão Oracle configurada por variáveis de ambiente"),
    ("soulmv.view.patients", "VW_SANATIO_PACIENTES_INTERNADOS", "View de pacientes internados"),
    ("soulmv.view.antimicrobials", "VW_SANATIO_ANTIMICROBIANOS", "View de antimicrobianos"),
    ("soulmv.view.cultures", "VW_SANATIO_CULTURAS", "View de culturas"),
    ("soulmv.view.invasive_procedures", "VW_SANATIO_PROCEDIMENTOS_INVASIVOS", "View de procedimentos invasivos"),
    ("soulmv.view.isolations", "VW_SANATIO_ISOLAMENTOS", "View de isolamentos"),
    ("general.institution_name", "Hospital Demonstração", "Nome da instituição"),
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

        for email, full_name, role_name in USERS:
            if not db.scalar(select(User).where(User.email == email)):
                db.add(
                    User(
                        email=email,
                        full_name=full_name,
                        hashed_password=get_password_hash("123456"),
                        role_id=role_by_name[role_name].id,
                        active=True,
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
