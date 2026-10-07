from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AntimicrobialProductWrite(BaseModel):
    codigo_produto: str = Field(min_length=1, max_length=60)
    descricao: str = Field(min_length=1, max_length=255)
    quantidade: str = Field(min_length=1, max_length=80)
    unidade_medida: str = Field(min_length=1, max_length=20)
    codigo_atc: str = Field(min_length=3, max_length=20)


class AntimicrobialProductRead(AntimicrobialProductWrite):
    model_config = ConfigDict(from_attributes=True)

    id: int
    criado_em: datetime
    atualizado_em: datetime
