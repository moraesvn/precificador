import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from backend.api.dependencies import get_db
from backend.constants import PROVIDER_TINY
from backend.repositories.oauth_connection_repository import OAuthConnectionRepository
from backend.services.oauth_tiny_service import (
    calculate_expires_at,
    normalize_company_code,
    refresh_tiny_tokens,
)
from backend.services.tiny_erp_api_service import listar_produtos


router = APIRouter(prefix="/tiny/produtos", tags=["tiny-produtos"])


def _ensure_internal_token(x_internal_token: str | None) -> None:
    """Mesmo critério do POST /oauth/tiny/refresh: só processos na VPS com segredo."""
    configured = os.getenv("INTERNAL_JOB_TOKEN", "").strip()
    if not configured:
        raise HTTPException(
            status_code=500,
            detail="Variavel INTERNAL_JOB_TOKEN nao configurada.",
        )
    if x_internal_token != configured:
        raise HTTPException(status_code=401, detail="Token interno invalido.")


def _access_token_with_optional_refresh(
    db: Session,
    company_code: str,
    x_internal_token: str | None,
) -> str:
    _ensure_internal_token(x_internal_token)

    try:
        normalized = normalize_company_code(company_code)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    repo = OAuthConnectionRepository(db)
    connection = repo.get_by_company_and_provider(
        company_code=normalized,
        provider=PROVIDER_TINY,
    )
    if connection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhuma conexao Tiny salva para a empresa {normalized}. "
            "Conclua o OAuth em /oauth/tiny/start antes.",
        )

    now = datetime.now(UTC)
    expires_at = connection.expires_at
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)

    expired = expires_at is not None and expires_at <= now
    if expired and not connection.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Access token Tiny expirado e sem refresh token. Execute POST /oauth/tiny/refresh.",
        )
    if expired and connection.refresh_token:
        try:
            token_data = refresh_tiny_tokens(
                company_code=normalized,
                refresh_token=connection.refresh_token,
            )
        except ValueError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        connection = repo.upsert_connection_tokens(
            company_code=normalized,
            provider=PROVIDER_TINY,
            access_token=str(token_data["access_token"]),
            refresh_token=str(token_data["refresh_token"])
            if token_data.get("refresh_token")
            else connection.refresh_token,
            token_type=str(token_data["token_type"]) if token_data.get("token_type") else connection.token_type,
            scope=str(token_data["scope"]) if token_data.get("scope") else connection.scope,
            expires_at=calculate_expires_at(token_data),
            external_account_id=connection.external_account_id,
        )

    return connection.access_token


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
    token = _access_token_with_optional_refresh(db, company, x_internal_token)

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
