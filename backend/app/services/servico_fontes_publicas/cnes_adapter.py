import json
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import urlopen


@dataclass
class DadosCNES:
    cnes: str
    nome_estabelecimento: str | None = None
    municipio: str | None = None
    uf: str | None = None
    quantidade_leitos: int | None = None
    quantidade_leitos_uti: int | None = None
    fonte: str = "CNES / Ministério da Saúde"


class CNESAdapter:
    """Adapter isolado para fontes públicas do CNES.

    A consulta é propositalmente simples e tolerante a falhas. Se a fonte pública
    estiver indisponível, o chamador mantém os dados internos existentes.
    """

    def consultar_estabelecimento(self, cnes: str) -> DadosCNES:
        cnes = "".join(ch for ch in cnes if ch.isdigit())
        if not cnes:
            raise ValueError("CNES inválido")
        try:
            with urlopen(f"https://apidadosabertos.saude.gov.br/cnes/estabelecimentos/{cnes}", timeout=8) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Não foi possível consultar a fonte pública do CNES: {exc}") from exc

        data = payload.get("estabelecimento") if isinstance(payload, dict) else None
        if not data and isinstance(payload, dict):
            data = payload
        if not isinstance(data, dict):
            raise RuntimeError("Fonte pública do CNES retornou formato não reconhecido")

        return DadosCNES(
            cnes=cnes,
            nome_estabelecimento=data.get("nome_fantasia") or data.get("nome") or data.get("no_fantasia"),
            municipio=data.get("municipio") or data.get("no_municipio"),
            uf=data.get("uf") or data.get("sg_uf"),
            quantidade_leitos=self._to_int(data.get("quantidade_leitos") or data.get("qt_leitos")),
            quantidade_leitos_uti=self._to_int(data.get("quantidade_leitos_uti") or data.get("qt_leitos_uti")),
        )

    def _to_int(self, value: object) -> int | None:
        try:
            return int(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None
