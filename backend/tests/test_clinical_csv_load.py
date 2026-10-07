from decimal import Decimal
from types import SimpleNamespace

import pytest

from app.services.antimicrobial_quantity import calculate_product_quantity
from scripts.load_clinical_csv import antimicrobial_rows, movement_rows, parse_date, read_csv, validate_columns


def antimicrobial(**overrides):
    row = {
        "CD_ATENDIMENTO": "10", "CD_PACIENTE": "20", "CD_PRESCRICAO": "30",
        "CD_ITEM_PRESCRICAO": "40", "CD_PRODUTO": "50", "DS_ANTIMICROBIANO": "Medicamento",
        "PRINCIPIO_ATIVO": "Principio A", "DT_INICIO": "01/10/26", "DT_APLICACAO": "02/10/26",
        "DT_FIM": "", "SN_ATIVO": "S", "DS_DOSE": "1", "DS_VIA": "EV",
        "DS_FREQUENCIA": "12/12h", "DIAS_USO": "2", "QT_DOSE": "2",
    }
    row.update(overrides)
    return row


def test_antimicrobial_rows_removes_exact_duplicates():
    row = antimicrobial()
    result, duplicates, conflicts = antimicrobial_rows([row, dict(row)])

    assert result == [row]
    assert duplicates == 1
    assert conflicts == 0


def test_antimicrobial_rows_merges_only_principle_conflict():
    result, duplicates, conflicts = antimicrobial_rows([
        antimicrobial(PRINCIPIO_ATIVO="Principio B"),
        antimicrobial(PRINCIPIO_ATIVO="Principio A"),
    ])

    assert result[0]["PRINCIPIO_ATIVO"] == "Principio A + Principio B"
    assert duplicates == 0
    assert conflicts == 1


def test_antimicrobial_rows_rejects_other_conflicts():
    with pytest.raises(ValueError, match="DS_DOSE"):
        antimicrobial_rows([antimicrobial(), antimicrobial(DS_DOSE="2")])


def test_movement_rows_keeps_distinct_same_day_movements():
    first = {"CD_ATENDIMENTO": "10", "DT_MOVIMENTACAO": "01/10/26", "DS_LEITO_DESTINO": "A"}
    second = {**first, "DS_LEITO_DESTINO": "B"}

    result, duplicates = movement_rows([first, dict(first), second])

    assert result == [first, second]
    assert duplicates == 1


def test_validate_columns_reports_missing_fields():
    with pytest.raises(ValueError, match="CD_PACIENTE"):
        validate_columns("exam-requests", [{"CD_PEDIDO": "1"}])


def test_parse_date_preserves_application_time():
    assert parse_date("01-08-2019 14:30:00").hour == 14
    assert parse_date("01-08-2019 14:30:00").minute == 30


def test_calculate_product_quantity_converts_milligrams_to_grams():
    product = SimpleNamespace(quantidade="500", unidade_medida="mg")

    dose, display, grams, unit = calculate_product_quantity("2", product)

    assert dose == Decimal("2")
    assert display == "1000"
    assert grams == Decimal("1")
    assert unit == "mg"


def test_calculate_product_quantity_preserves_combination_components():
    product = SimpleNamespace(quantidade="500/125", unidade_medida="mg")

    _, display, grams, _ = calculate_product_quantity("2", product)

    assert display == "1000/250"
    assert grams is None


def test_read_csv_repairs_unquoted_decimal_comma_in_dose(tmp_path):
    path = tmp_path / "antimicrobials.csv"
    path.write_text(
        "CD_ATENDIMENTO,CD_PACIENTE,CD_PRESCRICAO,CD_ITEM_PRESCRICAO,CD_PRODUTO,"
        "DS_ANTIMICROBIANO,PRINCIPIO_ATIVO,DT_INICIO,DT_APLICACAO,DT_FIM,SN_ATIVO,"
        "QT_DOSE,DS_DOSE,DS_VIA,DS_FREQUENCIA,DIAS_USO\n"
        "1,2,3,4,150,Vancomicina,VANCOMICINA,01-08-2019 10:00:00,01-08-2019 16:00:00,,"
        "S,0,25,FRASCO/AMPOLA,INTRAVENOSA,6 HS X 6 HS,10\n",
        encoding="utf-8",
    )

    rows, _ = read_csv(path)

    assert rows[0]["QT_DOSE"] == "0,25"
    assert rows[0]["DS_DOSE"] == "FRASCO/AMPOLA"
    assert rows[0]["DS_VIA"] == "INTRAVENOSA"
    assert rows[0]["DS_FREQUENCIA"] == "6 HS X 6 HS"
    assert rows[0]["DIAS_USO"] == "10"
