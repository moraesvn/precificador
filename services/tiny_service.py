"""
Serviço de integração com a API Tiny
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime
from config.settings import TINY_ACCESS_TOKEN, TINY_BASE_URL


class TinyService:
    """Classe para interagir com a API Tiny"""
    
    def __init__(self):
        self.access_token = TINY_ACCESS_TOKEN
        self.base_url = TINY_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict[Any, Any]]:
        """
        Faz uma requisição à API Tiny
        
        Args:
            method: Método HTTP (GET, POST, PUT, DELETE)
            endpoint: Endpoint da API
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Resposta da API em formato JSON ou None em caso de erro
        """
        url = f"{self.base_url}/{endpoint}"
        
        try:
            response = requests.request(method, url, headers=self.headers, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição à API Tiny: {str(e)}")
            return None
    
    def listar_produtos(
        self, 
        dataAlteracao: Optional[str] = None,
        limit: int = 100, 
        offset: int = 0
    ) -> Optional[Dict[Any, Any]]:
        """
        Lista produtos com filtro opcional de data de modificação
        
        Args:
            data_modificacao: Data de modificação no formato YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS
            limit: Limite de resultados por página (padrão: 100)
            offset: Offset para paginação (padrão: 0)
            
        Returns:
            Lista de produtos ou None em caso de erro
        """
        params = {
            "limit": limit,
            "offset": offset
        }
        
        # Adicionar filtro de data de modificação se fornecido
        if dataAlteracao:
            # Se a data não contém hora, adicionar 00:00:00 como padrão
            if len(dataAlteracao) == 10:  # Formato YYYY-MM-DD (10 caracteres)
                params["dataAlteracao"] = f"{dataAlteracao} 00:00:00"
            else:
                params["dataAlteracao"] = dataAlteracao

        
        return self._make_request("GET", "produtos", params=params)
