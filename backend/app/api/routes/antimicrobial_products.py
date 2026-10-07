from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.clinical import ProdutoAntimicrobiano
from app.models.user import User
from app.schemas.antimicrobial_product import AntimicrobialProductRead, AntimicrobialProductWrite

router = APIRouter(prefix="/antimicrobial-products", tags=["Produtos antimicrobianos"])
VALID_UNITS = {"mg", "g", "mcg", "mL", "UI", "g/mg"}


def require_pharmacy(user: User = Depends(get_current_user)) -> User:
    if user.role.name not in {"ADMIN", "FARMACIA"}:
        raise HTTPException(status_code=403, detail="Acesso restrito a FARMACIA ou ADMIN")
    return user


def normalize(payload: AntimicrobialProductWrite) -> dict:
    data = payload.model_dump()
    data["codigo_produto"] = data["codigo_produto"].strip()
    data["descricao"] = data["descricao"].strip()
    data["quantidade"] = data["quantidade"].strip().replace(",", ".")
    data["codigo_atc"] = data["codigo_atc"].strip().upper()
    if data["unidade_medida"] not in VALID_UNITS:
        raise HTTPException(status_code=422, detail="Unidade de medida invalida")
    return data


@router.get("", response_model=list[AntimicrobialProductRead])
def list_products(db: Session = Depends(get_db), _: User = Depends(require_pharmacy)) -> list[ProdutoAntimicrobiano]:
    return list(db.scalars(select(ProdutoAntimicrobiano).order_by(ProdutoAntimicrobiano.descricao)))


@router.post("", response_model=AntimicrobialProductRead)
def create_product(payload: AntimicrobialProductWrite, db: Session = Depends(get_db), _: User = Depends(require_pharmacy)) -> ProdutoAntimicrobiano:
    data = normalize(payload)
    if db.scalar(select(ProdutoAntimicrobiano).where(ProdutoAntimicrobiano.codigo_produto == data["codigo_produto"])):
        raise HTTPException(status_code=409, detail="Codigo de produto ja cadastrado")
    item = ProdutoAntimicrobiano(**data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{product_id}", response_model=AntimicrobialProductRead)
def update_product(product_id: int, payload: AntimicrobialProductWrite, db: Session = Depends(get_db), _: User = Depends(require_pharmacy)) -> ProdutoAntimicrobiano:
    item = db.get(ProdutoAntimicrobiano, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    data = normalize(payload)
    duplicate = db.scalar(select(ProdutoAntimicrobiano).where(ProdutoAntimicrobiano.codigo_produto == data["codigo_produto"], ProdutoAntimicrobiano.id != product_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Codigo de produto ja cadastrado")
    for key, value in data.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db), _: User = Depends(require_pharmacy)) -> None:
    item = db.get(ProdutoAntimicrobiano, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    db.delete(item)
    db.commit()
