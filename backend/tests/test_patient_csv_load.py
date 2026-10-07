from datetime import date

from scripts.load_patients_csv import parse_date, read_rows


def test_two_digit_birth_year_does_not_create_future_birth_date(tmp_path) -> None:
    csv_path = tmp_path / "patients.csv"
    csv_path.write_text(
        "CD_ATENDIMENTO,CD_PACIENTE,DT_NASCIMENTO,TP_SEXO,DT_ATENDIMENTO,DT_ALTA,"
        "CD_UNIDADE,DS_UNIDADE,CD_LEITO,DS_LEITO,CD_PRESTADOR,NM_PRESTADOR,CD_CONVENIO,NM_CONVENIO\n"
        "A1,P1,30/12/68,F,07/10/26,,U1,UTI,L1,Leito 1,M1,Medico,C1,Convenio\n",
        encoding="utf-8",
    )

    rows, digest = read_rows(csv_path)

    assert len(digest) == 64
    assert rows[0]["birth_date"] == date(1968, 12, 30)
    assert rows[0]["discharged_at"] is None


def test_regular_two_digit_year_is_preserved() -> None:
    assert parse_date("07/10/26").date() == date(2026, 10, 7)
