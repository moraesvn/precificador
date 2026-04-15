from typing import Literal

# Empresas suportadas no contexto inicial do projeto.
COMPANY_SP = "SP"
COMPANY_SC = "SC"

# Provedores suportados.
PROVIDER_ML = "ml"
PROVIDER_TINY = "tiny"

CompanyCode = Literal["SP", "SC"]
Provider = Literal["ml", "tiny"]

SUPPORTED_COMPANIES: tuple[CompanyCode, ...] = (COMPANY_SP, COMPANY_SC)
SUPPORTED_PROVIDERS: tuple[Provider, ...] = (PROVIDER_ML, PROVIDER_TINY)
