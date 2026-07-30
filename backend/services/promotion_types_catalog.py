"""Catálogo resumido dos tipos de promoção do Mercado Livre (MLB)."""

from __future__ import annotations

from typing import Any


# Códigos ativáveis no MVP (fluxo implementado nas próximas etapas).
MVP_ENABLED_BY_DEFAULT = frozenset({"SELLER_CAMPAIGN", "DEAL"})

DEFAULT_DISCOUNT_RULES: dict[str, float] = {
    "premium_traditional_percent": 10.0,
    "classic_traditional_percent": 10.0,
    "premium_catalog_percent": 10.0,
    "classic_catalog_percent": 10.0,
    "other_percent": 10.0,
}

PROMOTION_TYPE_CATALOG: list[dict[str, Any]] = [
    {
        "code": "SELLER_CAMPAIGN",
        "name": "Campanha do vendedor",
        "summary": (
            "Você cria a campanha, define datas (máx. 14 dias) e envia deal_price "
            "por ITEM_ID. Sem bônus do ML. Ideal para promoção própria."
        ),
        "created_by": "seller",
        "price_mode": "deal_price",
        "meli_bonus": False,
        "mvp_supported": True,
    },
    {
        "code": "DEAL",
        "name": "Campanha tradicional",
        "summary": (
            "Convite do ML (ex.: Hot Sale). Você adere aos itens candidatos "
            "definindo deal_price. Pode exigir aprovação. Sem bônus do ML."
        ),
        "created_by": "meli_invite",
        "price_mode": "deal_price",
        "meli_bonus": False,
        "mvp_supported": True,
    },
    {
        "code": "MARKETPLACE_CAMPAIGN",
        "name": "Co-financiada",
        "summary": "Convite do ML; você aceita oferta pronta. ML banca parte do desconto.",
        "created_by": "meli_invite",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "SMART",
        "name": "Co-financiada automática",
        "summary": "Seleção automática de itens pelo ML; você aceita. Com bônus MELI.",
        "created_by": "meli_auto",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "PRICE_MATCHING",
        "name": "Preço competitivo",
        "summary": "Alinha preço à concorrência; ML ajuda no desconto. Você aceita a oferta.",
        "created_by": "meli",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "PRICE_MATCHING_MELI_ALL",
        "name": "Preço competitivo 100% ML",
        "summary": "ML paga 100% do desconto e pode ativar automaticamente.",
        "created_by": "meli_auto",
        "price_mode": "automatic",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "PRICE_DISCOUNT",
        "name": "Desconto individual",
        "summary": "Desconto por item sugerido/elegível; você define deal_price conforme regras.",
        "created_by": "meli_or_item",
        "price_mode": "deal_price",
        "meli_bonus": None,
        "mvp_supported": False,
    },
    {
        "code": "DOD",
        "name": "Oferta do dia",
        "summary": "Destaque ~24h por convite. Você define deal_price. Estoque informativo.",
        "created_by": "meli_invite",
        "price_mode": "deal_price",
        "meli_bonus": False,
        "mvp_supported": False,
    },
    {
        "code": "LIGHTNING",
        "name": "Oferta relâmpago",
        "summary": "Oferta curta; exige deal_price + estoque reservado. Encerra quando acaba o estoque.",
        "created_by": "meli_invite",
        "price_mode": "deal_price_and_stock",
        "meli_bonus": False,
        "mvp_supported": False,
    },
    {
        "code": "VOLUME",
        "name": "Desconto por quantidade",
        "summary": "Leve X pague Y / % na Nª unidade. Convite ML ou criação pelo seller.",
        "created_by": "meli_or_seller",
        "price_mode": "accept_or_rules",
        "meli_bonus": None,
        "mvp_supported": False,
    },
    {
        "code": "PRE_NEGOTIATED",
        "name": "Pré-acordado",
        "summary": "Desconto negociado com o comercial do ML; você aceita o acordo.",
        "created_by": "meli_commercial",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "UNHEALTHY_STOCK",
        "name": "Liquidação Full",
        "summary": "Liquidar estoque Full parado; acordo + aceitação. Com bônus MELI.",
        "created_by": "meli",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
    {
        "code": "SELLER_COUPON_CAMPAIGN",
        "name": "Cupom do vendedor",
        "summary": "Você cria cupom (% ou R$) no checkout. Só MLB. Sem bônus do ML.",
        "created_by": "seller",
        "price_mode": "percent_or_fixed",
        "meli_bonus": False,
        "mvp_supported": False,
    },
    {
        "code": "BANK",
        "name": "Co-participação PIX",
        "summary": "Desconto no PIX (sub_type COFINANCED). Convite ML; seller + ML cofinanciam.",
        "created_by": "meli_invite",
        "price_mode": "accept_offer",
        "meli_bonus": True,
        "mvp_supported": False,
    },
]


def get_promotion_type_catalog() -> list[dict[str, Any]]:
    return [dict(item) for item in PROMOTION_TYPE_CATALOG]


def get_catalog_entry(code: str) -> dict[str, Any] | None:
    normalized = (code or "").strip().upper()
    for item in PROMOTION_TYPE_CATALOG:
        if item["code"] == normalized:
            return dict(item)
    return None
