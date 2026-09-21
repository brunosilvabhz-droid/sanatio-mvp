from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.clinical import Atendimento, CulturaAtendimento, ProcedimentoInvasivoAtendimento
from app.models.epidemiology_reference import ReferenciaEpidemiologica


@dataclass(frozen=True)
class IndicadorSpec:
    codigo: str
    nome: str
    unidade_medida: str


INDICADORES = [
    IndicadorSpec("IPCSL", "IPCSL associada a CVC", "/ 1.000 CVC-dia"),
    IndicadorSpec("PAV", "PAV", "/ 1.000 VM-dia"),
    IndicadorSpec("ITU_CVD", "ITU associada a CVD", "/ 1.000 CVD-dia"),
    IndicadorSpec("RESISTENCIA_AM", "Resistência antimicrobiana", "% das culturas positivas"),
]

CODIGOS_REFERENCIA = {
    "IPCSL": ("IPCSL", "IPCSL_CVC"),
    "PAV": ("PAV", "PAV_VM"),
    "ITU_CVD": ("ITU_CVD",),
    "RESISTENCIA_AM": ("RESISTENCIA_AM",),
}


class BenchmarkEpidemiologicoService:
    def __init__(self, db: Session):
        self.db = db

    def comparar(self, indicador: str, periodo: str, tipo_unidade: str = "UTI_ADULTO", uf: str | None = None) -> dict:
        spec = self._spec(indicador)
        inicio, fim = self._periodo(periodo)
        numerador, denominador, valor = self._calcular_indicador(spec.codigo, inicio, fim, tipo_unidade)
        referencia = self._referencia(spec.codigo, tipo_unidade, uf)
        return {
            "indicador": spec.nome,
            "codigo_indicador": spec.codigo,
            "valor_hospital": valor,
            "numerador": numerador,
            "denominador": denominador,
            "unidade_medida": referencia.unidade_medida if referencia else spec.unidade_medida,
            "benchmark_utilizado": referencia.id if referencia else None,
            "p10": referencia.p10 if referencia else None,
            "p25": referencia.p25 if referencia else None,
            "p50": referencia.p50 if referencia else None,
            "p75": referencia.p75 if referencia else None,
            "p90": referencia.p90 if referencia else None,
            "faixa_estatistica": self._faixa(valor, referencia),
            "periodo_referencia": periodo,
            "ano_referencia": referencia.ano_referencia if referencia else None,
            "uf_referencia": referencia.uf if referencia else None,
            "regiao_referencia": referencia.regiao if referencia else None,
            "fonte": referencia.fonte if referencia else None,
            "url_fonte": referencia.url_fonte if referencia else None,
            "historico": self._historico(spec.codigo, periodo, referencia, tipo_unidade),
        }

    def fechamento_anvisa(self, periodo: str, tipo_unidade: str = "UTI_ADULTO") -> dict:
        inicio, fim = self._periodo(periodo)
        paciente_dia = self._patient_days(inicio, fim)
        casos_ipcsl, cvc_dia, densidade_ipcsl = self._calcular_indicador("IPCSL", inicio, fim)
        casos_pav, vm_dia, densidade_pav = self._calcular_indicador("PAV", inicio, fim)
        casos_itu_cvd, cvd_dia, densidade_itu_cvd = self._calcular_indicador("ITU_CVD", inicio, fim)
        return {
            "tipo_unidade": tipo_unidade,
            "periodo": periodo,
            "paciente_dia": paciente_dia,
            "cvc_dia": cvc_dia,
            "vm_dia": vm_dia,
            "cvd_dia": cvd_dia,
            "casos_ipcsl": casos_ipcsl,
            "casos_pav": casos_pav,
            "casos_itu_cvd": casos_itu_cvd,
            "densidade_ipcsl": densidade_ipcsl,
            "densidade_pav": densidade_pav,
            "densidade_itu_cvd": densidade_itu_cvd,
        }

    def _spec(self, codigo_ou_nome: str) -> IndicadorSpec:
        normalized = codigo_ou_nome.upper()
        for spec in INDICADORES:
            if normalized in {spec.codigo.upper(), spec.nome.upper()}:
                return spec
        return INDICADORES[0]

    def _referencia(self, codigo: str, tipo_unidade: str, uf: str | None = None) -> ReferenciaEpidemiologica | None:
        unidade = tipo_unidade.strip().upper().replace(" ", "_").replace("-", "_")
        codigos_base = CODIGOS_REFERENCIA.get(codigo, (codigo,))
        codigos = {base for base in codigos_base} | {f"{base}_{unidade}" for base in codigos_base}
        query = select(ReferenciaEpidemiologica).where(
            ReferenciaEpidemiologica.codigo_indicador.in_(codigos),
            ReferenciaEpidemiologica.tipo_unidade == unidade,
            ReferenciaEpidemiologica.ativo.is_(True),
        )
        if uf:
            query = query.where(ReferenciaEpidemiologica.uf == uf.strip().upper())
        return self.db.scalar(
            query.order_by(
                ReferenciaEpidemiologica.ano_referencia.desc(),
                ReferenciaEpidemiologica.data_importacao.desc(),
                ReferenciaEpidemiologica.id.desc(),
            )
        )

    def _historico(self, codigo: str, periodo: str, referencia: ReferenciaEpidemiologica | None, tipo_unidade: str) -> list[dict]:
        ano, mes = [int(part) for part in periodo.split("-")]
        atual = date(ano, mes, 1)
        rows = []
        for offset in range(5, -1, -1):
            month = self._add_months(atual, -offset)
            next_month = self._add_months(month, 1)
            _, _, value = self._calcular_indicador(codigo, self._as_datetime(month), self._as_datetime(next_month), tipo_unidade)
            rows.append({"mes": month.strftime("%m/%Y"), "valor": value, "p50": referencia.p50 if referencia else None, "p75": referencia.p75 if referencia else None})
        return rows

    def _calcular_indicador(self, codigo: str, inicio: datetime, fim: datetime, tipo_unidade: str | None = None) -> tuple[int, int, float]:
        cultures = self._positive_cultures(inicio, fim, tipo_unidade)
        if codigo == "IPCSL":
            numerador = sum(1 for culture in cultures if self._culture_matches(culture, ("sangue", "hemocultura", "cateter", "corrente sanguinea")))
            denominador = self._device_days(inicio, fim, ("cvc", "cateter venoso central", "venoso central"), tipo_unidade)
            return numerador, denominador, round((numerador / denominador) * 1000, 2) if denominador else 0.0
        if codigo == "PAV":
            numerador = sum(1 for culture in cultures if self._culture_matches(culture, ("respir", "traque", "pneumo", "pulmao", "secrecao")))
            denominador = self._device_days(inicio, fim, ("ventil", "vm", "respirador"), tipo_unidade)
            return numerador, denominador, round((numerador / denominador) * 1000, 2) if denominador else 0.0
        if codigo == "ITU_CVD":
            numerador = sum(1 for culture in cultures if self._culture_matches(culture, ("urina", "urin", "urocultura")))
            denominador = self._device_days(inicio, fim, ("cvd", "sonda vesical", "cateter vesical", "demora"), tipo_unidade)
            return numerador, denominador, round((numerador / denominador) * 1000, 2) if denominador else 0.0
        total = len(cultures)
        resistant = sum(1 for culture in cultures if self._culture_matches(culture, ("mrsa", "kpc", "esbl", "carbapenemase", "resistente", "resistencia", "oxacilina", "meticilina", "vancomicina")))
        return resistant, total, round((resistant / total) * 100, 2) if total else 0.0

    def _positive_cultures(self, inicio: datetime, fim: datetime, tipo_unidade: str | None = None) -> list[CulturaAtendimento]:
        stmt = select(CulturaAtendimento).join(Atendimento, Atendimento.id == CulturaAtendimento.atendimento_id).where(
                CulturaAtendimento.positivo.is_(True),
                CulturaAtendimento.data_hora_coleta >= inicio,
                CulturaAtendimento.data_hora_coleta < fim,
            )
        if tipo_unidade:
            stmt = stmt.where(self._unit_condition(tipo_unidade))
        return self.db.scalars(stmt).all()

    def _device_days(self, inicio: datetime, fim: datetime, needles: tuple[str, ...], tipo_unidade: str | None = None) -> int:
        stmt = select(ProcedimentoInvasivoAtendimento).join(Atendimento, Atendimento.id == ProcedimentoInvasivoAtendimento.atendimento_id).where(
                ProcedimentoInvasivoAtendimento.data_hora_inicio < fim,
                (ProcedimentoInvasivoAtendimento.data_hora_fim.is_(None)) | (ProcedimentoInvasivoAtendimento.data_hora_fim >= inicio),
            )
        if tipo_unidade:
            stmt = stmt.where(self._unit_condition(tipo_unidade))
        procedures = self.db.scalars(stmt).all()
        total = 0
        for procedure in procedures:
            searchable = " ".join([procedure.procedimento or "", procedure.local_instalacao or ""])
            if self._contains_any(searchable, needles):
                total += self._active_days(procedure.data_hora_inicio, procedure.data_hora_fim, inicio, fim)
        return total

    def _patient_days(self, inicio: datetime, fim: datetime) -> int:
        atendimentos = self.db.scalars(
            select(Atendimento).where(
                Atendimento.data_hora_entrada < fim,
                (Atendimento.data_hora_saida.is_(None)) | (Atendimento.data_hora_saida >= inicio),
            )
        ).all()
        return sum(self._active_days(item.data_hora_entrada, item.data_hora_saida, inicio, fim) for item in atendimentos)

    def _culture_matches(self, culture: CulturaAtendimento, needles: tuple[str, ...]) -> bool:
        searchable = " ".join([culture.exame or "", culture.material or "", culture.microorganismo or "", culture.resultado or ""])
        return self._contains_any(searchable, needles)

    def _contains_any(self, value: str | None, needles: tuple[str, ...]) -> bool:
        text = (value or "").lower()
        return any(needle in text for needle in needles)

    def _unit_condition(self, tipo_unidade: str):
        normalized = tipo_unidade.strip().lower().replace("_", " ")
        unit = func.lower(Atendimento.unidade_atual)
        if normalized == "uti adulto":
            return unit.like("%uti%adult%")
        if normalized in {"ui", "unidade internacao", "unidade de internacao"}:
            return unit.like("%internacao%")
        return unit == normalized

    def _active_days(self, start: datetime | None, end: datetime | None, period_start: datetime, period_end: datetime) -> int:
        start = self._normalize_datetime(start)
        end = self._normalize_datetime(end)
        if not start:
            return 0
        overlap_start = max(start, period_start)
        overlap_end = min(end or period_end, period_end)
        if overlap_end <= overlap_start:
            return 0
        return max((overlap_end.date() - overlap_start.date()).days, 1)

    def _faixa(self, valor: float, referencia: ReferenciaEpidemiologica | None) -> str:
        if not referencia:
            return "sem_referencia"
        points = [("p10", referencia.p10), ("p25", referencia.p25), ("p50", referencia.p50), ("p75", referencia.p75), ("p90", referencia.p90)]
        existing = [(label, point) for label, point in points if point is not None]
        if not existing:
            return "sem_percentis"
        if referencia.p10 is not None and valor < referencia.p10:
            return "abaixo_p10"
        if referencia.p10 is not None and referencia.p25 is not None and valor < referencia.p25:
            return "p10_p25"
        if referencia.p25 is not None and referencia.p50 is not None and valor < referencia.p50:
            return "p25_p50"
        if referencia.p50 is not None and referencia.p75 is not None and valor < referencia.p75:
            return "p50_p75"
        if referencia.p75 is not None and referencia.p90 is not None and valor < referencia.p90:
            return "p75_p90"
        if referencia.p90 is not None and valor >= referencia.p90:
            return "acima_p90"
        return "fora_da_faixa_cadastrada"

    def _periodo(self, periodo: str) -> tuple[datetime, datetime]:
        ano, mes = [int(part) for part in periodo.split("-")]
        start = date(ano, mes, 1)
        return self._as_datetime(start), self._as_datetime(self._add_months(start, 1))

    def _add_months(self, value: date, months: int) -> date:
        year = value.year + ((value.month - 1 + months) // 12)
        month = ((value.month - 1 + months) % 12) + 1
        return date(year, month, 1)

    def _as_datetime(self, value: date) -> datetime:
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)

    def _normalize_datetime(self, value: datetime | None) -> datetime | None:
        if value and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
