import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

DEFAULT_API_BASE_URL = "https://auth.grupocavalcante.net.br"


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", DEFAULT_API_BASE_URL).strip().rstrip("/")


def get_internal_token() -> str:
    return os.getenv("INTERNAL_JOB_TOKEN", "").strip()


def config_ok() -> tuple[bool, str]:
    if not get_internal_token():
        return False, f"Defina INTERNAL_JOB_TOKEN em {_ENV_PATH}"
    if not get_api_base_url():
        return False, "Defina API_BASE_URL no .env"
    return True, ""
