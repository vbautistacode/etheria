# services/api_client.py
"""
Cliente HTTP simples para o backend ASTRO (endpoints /natal, etc).

Melhorias:
- não lê ASTRO_API_* no nível do módulo (evita comportamento rígido em import)
- permite configurar via configure() ou por argumentos nas chamadas
- usa requests.Session para reaproveitar conexões
- fornece health_check() para uso em UI/diagnóstico
- lança APIClientError com mensagens claras
"""

from typing import Dict, Any, Optional
from datetime import datetime
import os
import logging
import requests

logger = logging.getLogger("etheria.services.api_client")
logger.addHandler(logging.NullHandler())

class APIClientError(Exception):
    """Exceções relacionadas ao cliente da API ASTRO."""
    pass

# estado configurável (padrões lidos de env apenas quando necessário)
_config: Dict[str, Any] = {
    "base": None,
    "key": None,
    "timeout": None,
    "session": None,
}

def _load_defaults_from_env():
    """Carrega valores padrão das variáveis de ambiente se não configurados."""
    if _config["base"] is None:
        _config["base"] = os.getenv("ASTRO_API_BASE")
    if _config["key"] is None:
        _config["key"] = os.getenv("ASTRO_API_KEY")
    if _config["timeout"] is None:
        try:
            _config["timeout"] = int(os.getenv("ASTRO_API_TIMEOUT", "15"))
        except Exception:
            _config["timeout"] = 15
    if _config["session"] is None:
        _config["session"] = requests.Session()

def configure(base: Optional[str] = None, key: Optional[str] = None, timeout: Optional[int] = None, session: Optional[requests.Session] = None) -> None:
    """
    Configura o cliente globalmente. Útil para testes ou inicialização centralizada.
    Chamadas individuais também aceitam overrides.
    """
    if base is not None:
        _config["base"] = base
    if key is not None:
        _config["key"] = key
    if timeout is not None:
        _config["timeout"] = int(timeout)
    if session is not None:
        _config["session"] = session

def health_check() -> Dict[str, Any]:
    """
    Retorna um dicionário simples com o estado de configuração do cliente.
    Não faz chamadas externas.
    """
    _load_defaults_from_env()
    return {
        "configured": bool(_config.get("base") and _config.get("key")),
        "base": _config.get("base"),
        "timeout": _config.get("timeout"),
    }

def _ensure_config_or_raise(base: Optional[str], key: Optional[str]) -> (str, str, int, requests.Session):
    """Resolve base/key/timeout/session usando argumentos ou configuração global; lança APIClientError se faltar."""
    _load_defaults_from_env()
    base_final = base or _config.get("base")
    key_final = key or _config.get("key")
    timeout_final = _config.get("timeout") or 15
    session = _config.get("session") or requests.Session()

    if not base_final or not key_final:
        raise APIClientError("ASTRO_API_BASE ou ASTRO_API_KEY não configurados. Configure via env ou services.api_client.configure().")
    return base_final.rstrip("/"), key_final, int(timeout_final), session

def fetch_natal_chart_api(name: str, dt: datetime, lat: float, lon: float, tz: str, *, base: Optional[str] = None, key: Optional[str] = None, timeout: Optional[int] = None, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    Chama o endpoint /natal e retorna JSON normalizado.
    Parâmetros base/key/timeout/session podem sobrescrever a configuração global.
    Lança APIClientError em caso de falha.
    """
    # permitir overrides por chamada
    if session is not None:
        sess = session
    else:
        _load_defaults_from_env()
        sess = _config.get("session") or requests.Session()

    base_final = base or _config.get("base")
    key_final = key or _config.get("key")
    timeout_final = timeout if timeout is not None else (_config.get("timeout") or 15)

    if not base_final or not key_final:
        raise APIClientError("ASTRO_API_BASE ou ASTRO_API_KEY não configurados")

    payload = {
        "name": name,
        "datetime": dt.isoformat() if isinstance(dt, datetime) else str(dt),
        "latitude": lat,
        "longitude": lon,
        "timezone": tz
    }
    headers = {"Authorization": f"Bearer {key_final}", "Content-Type": "application/json"}
    url = f"{base_final.rstrip('/')}/natal"
    try:
        logger.debug("POST %s payload=%s", url, payload)
        resp = sess.post(url, json=payload, headers=headers, timeout=timeout_final)
        resp.raise_for_status()
        data = resp.json()
        # opcional: normalizar estrutura mínima esperada
        if not isinstance(data, dict):
            raise APIClientError("Resposta inesperada da API (não é um objeto JSON).")
        return data
    except requests.RequestException as e:
        logger.exception("Erro ao chamar API natal")
        raise APIClientError(str(e)) from e
    except ValueError as e:
        logger.exception("Erro ao decodificar JSON da resposta")
        raise APIClientError("Resposta inválida da API: " + str(e)) from e

def fetch_generic_api(endpoint: str, payload: Dict[str, Any], method: str = "POST", headers: Optional[Dict[str,str]] = None, timeout: Optional[int] = None, base: Optional[str] = None, key: Optional[str] = None, session: Optional[requests.Session] = None) -> Dict[str, Any]:
    """
    Chamada genérica para endpoints da API ASTRO. Útil para extensões.
    Aceita overrides por chamada.
    """
    # resolver config
    base_final = base or _config.get("base")
    key_final = key or _config.get("key")
    timeout_final = timeout if timeout is not None else (_config.get("timeout") or 15)
    sess = session or _config.get("session") or requests.Session()

    if not base_final or not key_final:
        raise APIClientError("ASTRO_API_BASE ou ASTRO_API_KEY não configurados")

    url = f"{base_final.rstrip('/')}/{endpoint.lstrip('/')}"
    headers = headers or {"Authorization": f"Bearer {key_final}", "Content-Type": "application/json"}
    try:
        logger.debug("%s %s payload=%s", method.upper(), url, payload)
        if method.upper() == "POST":
            resp = sess.post(url, json=payload, headers=headers, timeout=timeout_final)
        else:
            resp = sess.get(url, params=payload, headers=headers, timeout=timeout_final)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise APIClientError("Resposta inesperada da API (não é um objeto JSON).")
        return data
    except requests.RequestException as e:
        logger.exception("Erro ao chamar endpoint %s", endpoint)
        raise APIClientError(str(e)) from e
    except ValueError as e:
        logger.exception("Erro ao decodificar JSON da resposta")
        raise APIClientError("Resposta inválida da API: " + str(e)) from e

# proteção para execução direta (útil para debug)
if __name__ == "__main__":
    # exemplo rápido de health check
    print("api_client health:", health_check())