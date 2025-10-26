"""
Segurança e Autenticação da API
Conforme PRD: autenticação por Bearer Token (API_SECRET) para routers protegidos
"""

from fastapi import Security, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging

from app.core.config import settings

logger = logging.getLogger("security")


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
    """
    Verifica o header Authorization: Bearer <token> contra settings.API_SECRET.
    - Retorna True se válido
    - Levanta HTTPException 401 se inválido
    """
    if not credentials or not credentials.scheme or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Credenciais ausentes")

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Esquema de autenticação inválido")

    expected = settings.API_SECRET
    provided = credentials.credentials

    # Log de diagnóstico (não imprime o token em si)
    try:
        logger.info(
            "Auth check: scheme=%s, provided_len=%s, expected_len=%s, match=%s",
            credentials.scheme,
            len(provided) if provided else 0,
            len(expected) if expected else 0,
            provided == expected,
        )
    except Exception:
        # Evita qualquer falha de logging impactar a autenticação
        pass

    if not expected or provided != expected:
        raise HTTPException(status_code=401, detail="Token inválido")

    return True