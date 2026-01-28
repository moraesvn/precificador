"""
Configurações do projeto Precificador
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Tiny
TINY_ACCESS_TOKEN = os.getenv("TINY_ACCESS_TOKEN")
TINY_REFRESH_TOKEN = os.getenv("TINY_REFRESH_TOKEN")
TINY_BASE_URL = "https://api.tiny.com.br/public-api/v3"

# API Mercado Livre (será configurado posteriormente)
MERCADO_LIVRE_APP_ID = os.getenv("MERCADO_LIVRE_APP_ID")
MERCADO_LIVRE_SECRET_KEY = os.getenv("MERCADO_LIVRE_SECRET_KEY")
MERCADO_LIVRE_ACCESS_TOKEN = os.getenv("MERCADO_LIVRE_ACCESS_TOKEN")
MERCADO_LIVRE_BASE_URL = "https://api.mercadolivre.com"
