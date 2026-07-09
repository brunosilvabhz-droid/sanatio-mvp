from datetime import date, datetime, timedelta

TODAY = datetime(2026, 7, 9, 12, 0, 0)


def mock_patients() -> list[dict]:
    units = ["UTI Adulto", "Clínica Médica", "Cirurgia", "Pediatria"]
    doctors = ["Dra. Ana Lima", "Dr. Bruno Alves", "Dra. Carla Rocha", "Dr. Diego Santos"]
    plans = ["SUS", "Unimed", "Bradesco Saúde", "Particular"]
    patients = []
    for i in range(1, 21):
        admitted_days = (i * 2) % 18 + 1
        patients.append(
            {
                "cd_atendimento": str(10000 + i),
                "cd_paciente": str(20000 + i),
                "nm_paciente": f"Paciente Sanatio {i:02d}",
                "dt_nascimento": date(1950 + (i % 45), (i % 12) + 1, (i % 27) + 1),
                "tp_sexo": "F" if i % 2 else "M",
                "dt_atendimento": TODAY - timedelta(days=admitted_days),
                "cd_unidade": f"U{(i % 4) + 1}",
                "ds_unidade": units[i % 4],
                "cd_leito": f"L{i:03d}",
                "ds_leito": f"Leito {i:03d}",
                "cd_prestador": f"P{(i % 4) + 1}",
                "nm_prestador": doctors[i % 4],
                "cd_convenio": f"C{(i % 4) + 1}",
                "nm_convenio": plans[i % 4],
            }
        )
    return patients


def mock_antimicrobials() -> list[dict]:
    names = ["Ceftriaxona", "Piperacilina/Tazobactam", "Vancomicina", "Meropenem"]
    rows = []
    for p in mock_patients():
        idx = int(p["cd_atendimento"]) - 10000
        if idx % 2 == 0 or idx % 5 == 0:
            days = 4 + (idx % 12)
            rows.append(
                {
                    "cd_atendimento": p["cd_atendimento"],
                    "cd_paciente": p["cd_paciente"],
                    "cd_prescricao": f"PR{idx}",
                    "cd_item_prescricao": f"IT{idx}",
                    "cd_produto": f"AM{idx % 4}",
                    "ds_antimicrobiano": names[idx % 4],
                    "dt_inicio": TODAY - timedelta(days=days),
                    "dt_fim": None if idx % 3 else TODAY - timedelta(days=1),
                    "sn_ativo": "S" if idx % 3 else "N",
                    "ds_frequencia": "12/12h",
                    "ds_via": "EV",
                    "ds_dose": "1g",
                }
            )
    return rows


def mock_cultures() -> list[dict]:
    rows = []
    for p in mock_patients():
        idx = int(p["cd_atendimento"]) - 10000
        if idx % 3 == 0:
            positive = idx % 6 == 0
            rows.append(
                {
                    "cd_atendimento": p["cd_atendimento"],
                    "cd_paciente": p["cd_paciente"],
                    "cd_pedido": f"CP{idx}",
                    "cd_exame": "HC",
                    "ds_exame": "Hemocultura",
                    "dt_coleta": TODAY - timedelta(days=idx % 8 + 1),
                    "dt_resultado": TODAY - timedelta(days=idx % 5),
                    "ds_material": "Sangue",
                    "ds_microorganismo": "Klebsiella pneumoniae" if positive else None,
                    "ds_resultado": "Positivo" if positive else "Negativo",
                    "sn_positivo": "S" if positive else "N",
                }
            )
    return rows


def mock_invasive_procedures() -> list[dict]:
    rows = []
    for p in mock_patients():
        idx = int(p["cd_atendimento"]) - 10000
        if idx % 4 == 0 or idx % 7 == 0:
            days = 3 + idx % 16
            rows.append(
                {
                    "cd_atendimento": p["cd_atendimento"],
                    "cd_paciente": p["cd_paciente"],
                    "cd_procedimento": f"PI{idx}",
                    "ds_procedimento": "Cateter venoso central" if idx % 2 else "Sonda vesical de demora",
                    "dt_inicio": TODAY - timedelta(days=days),
                    "dt_fim": None if idx % 5 else TODAY - timedelta(days=2),
                    "sn_ativo": "S" if idx % 5 else "N",
                    "ds_local_instalacao": "Jugular direita" if idx % 2 else "Uretral",
                }
            )
    return rows


def mock_isolations() -> list[dict]:
    rows = []
    for p in mock_patients():
        idx = int(p["cd_atendimento"]) - 10000
        if idx in {6, 12, 18}:
            rows.append(
                {
                    "cd_atendimento": p["cd_atendimento"],
                    "cd_paciente": p["cd_paciente"],
                    "cd_isolamento": f"ISO{idx}",
                    "ds_isolamento": "Contato",
                    "dt_inicio": TODAY - timedelta(days=2 + idx % 5),
                    "dt_fim": None,
                    "sn_ativo": "S",
                }
            )
    return rows
