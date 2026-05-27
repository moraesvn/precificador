from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.api.routes.tiny_auth import get_tiny_access_token_with_optional_refresh
from backend.services.tiny_erp_api_service import listar_produtos


router = APIRouter(prefix="/tiny/produtos", tags=["tiny-produtos"])


@router.get("")
@router.get("/")
def listar_produtos_tiny(
    data_alteracao: str = Query(
        ...,
        description="Filtro obrigatorio: data de ultima alteracao no Tiny (dataAlteracao).",
        example="2024-01-15 00:00:00",
    ),
    company: str = Query(default="SP", description="Empresa (ex.: SP, SC)"),
    limit: int = Query(default=100, ge=1, le=500, description="Quantidade maxima por pagina"),
    offset: int = Query(default=0, ge=0, description="Deslocamento para paginacao"),
    nome: str | None = Query(default=None, description="Filtro opcional por nome (parcial)"),
    codigo: str | None = Query(default=None, description="Filtro opcional pelo codigo do produto"),
    situacao: str | None = Query(
        default=None,
        description="A=Ativo, I=Inativo, E=Excluido (opcional)",
    ),
    id_lista_preco: int | None = Query(default=None, description="Lista de precos (opcional)"),
    x_internal_token: str | None = Header(
        default=None,
        description="Token interno (mesmo valor de INTERNAL_JOB_TOKEN no .env da VPS).",
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Proxy seguro para GET /produtos da API do Tiny.

    O token OAuth fica no banco; quem chama este endpoint envia apenas o
    INTERNAL_JOB_TOKEN no header X-Internal-Token (igual ao refresh do Tiny).
    O parametro obrigatorio `data_alteracao` e enviado ao Tiny como `dataAlteracao`.
    """
    token = get_tiny_access_token_with_optional_refresh(db, company, x_internal_token)

    nome_f = (nome or "").strip() or None
    codigo_f = (codigo or "").strip() or None
    situacao_raw = (situacao or "").strip().upper()
    situacao_f = situacao_raw or None

    try:
        return listar_produtos(
            token,
            data_alteracao=data_alteracao.strip(),
            limit=limit,
            offset=offset,
            nome=nome_f,
            codigo=codigo_f,
            situacao=situacao_f,
            id_lista_preco=id_lista_preco,
        )
    except ValueError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
