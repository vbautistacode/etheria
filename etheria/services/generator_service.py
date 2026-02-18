# services/generator_service.py
from __future__ import annotations
from functools import wraps
import os
import json
import time
import threading
import hashlib
import logging
import random
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, date
import concurrent.futures

# Importações de serviços do projeto (ajuste caminhos se necessário)
from services.swisseph_client import natal_positions
from .chart_builder import build_chart_summary_from_natal
from .astro_service import geocode_place, get_timezone_from_coords, parse_birth_time, compute_chart_positions

# Integrações externas (API client)
from . import api_client

logger = logging.getLogger(__name__)

# -------------------------
# Configurações
# -------------------------
_CACHE_TTL_SECONDS = int(os.getenv("GENERATOR_CACHE_TTL", "300"))
_RATE_LIMIT_MIN_INTERVAL = float(os.getenv("GENERATOR_RATE_MIN_INTERVAL", "0.5"))

GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MODEL = os.getenv("GEMINI_MODEL") or os.getenv("GENAI_MODEL") or GEMINI_MODEL_DEFAULT

# -------------------------
# Estado para cache e rate limiting
# -------------------------
_cache_lock = threading.Lock()
_cache: Dict[str, Dict[str, Any]] = {}
_rate_lock = threading.Lock()
_last_call_ts = 0.0

# -------------------------
# Utilitários: cache & rate
# -------------------------
def _cache_get(key: str):
    with _cache_lock:
        entry = _cache.get(key)
        if not entry:
            return None
        if time.time() - entry["ts"] > _CACHE_TTL_SECONDS:
            del _cache[key]
            return None
        return entry["value"]

def _cache_set(key: str, value: Any):
    with _cache_lock:
        _cache[key] = {"ts": time.time(), "value": value}

def _rate_limit_wait():
    global _last_call_ts
    with _rate_lock:
        now = time.time()
        elapsed = now - _last_call_ts
        wait_for = _RATE_LIMIT_MIN_INTERVAL - elapsed
        if wait_for > 0:
            time.sleep(wait_for)
        _last_call_ts = time.time()

def _make_cache_key(model: str, payload: Any) -> str:
    rep = repr(payload).encode("utf-8")
    h = hashlib.sha256(rep).hexdigest()[:16]
    return f"ai_text:{model}:{h}"

# -------------------------
# Retry e Circuit Breaker
# -------------------------
_circuit_lock = threading.Lock()
_circuit_failures = 0
_CIRCUIT_THRESHOLD = int(os.getenv("GENERATOR_CIRCUIT_THRESHOLD", "3"))
_CIRCUIT_OPEN_SECONDS = float(os.getenv("GENERATOR_CIRCUIT_OPEN_SECONDS", "60"))
_circuit_open_until = 0.0

def _is_transient_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(x in msg for x in ("503", "unavailable", "overloaded", "timeout", "temporarily unavailable"))

def _circuit_allows_call() -> bool:
    global _circuit_open_until
    now = time.time()
    return now >= _circuit_open_until

def _record_failure():
    global _circuit_failures, _circuit_open_until
    with _circuit_lock:
        _circuit_failures += 1
        if _circuit_failures >= _CIRCUIT_THRESHOLD:
            _circuit_open_until = time.time() + _CIRCUIT_OPEN_SECONDS
            logger.warning("Circuit breaker aberto por %.0f segundos (falhas=%d)", _CIRCUIT_OPEN_SECONDS, _circuit_failures)

def _record_success():
    global _circuit_failures
    with _circuit_lock:
        _circuit_failures = 0

def retry_with_backoff(fn, max_attempts: int = 4, base_delay: float = 0.6, max_delay: float = 8.0):
    attempt = 0
    last_exc = None
    while attempt < max_attempts:
        try:
            return fn()
        except Exception as e:
            last_exc = e
            if not _is_transient_error(e):
                # erro não transitório: propagar imediatamente
                raise
            attempt += 1
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, delay * 0.25)
            sleep_for = delay + jitter
            logger.warning("Erro transitório detectado (tentativa %d/%d): %s. Retentando em %.2fs", attempt, max_attempts, e, sleep_for)
            time.sleep(sleep_for)
    logger.error("Esgotadas tentativas de retry; última exceção: %s", last_exc)
    raise last_exc

# -------------------------
# Logging helpers / decorator
# -------------------------
def _log_and_return(result: Dict[str, Any], fn_name: Optional[str] = None) -> Dict[str, Any]:
    try:
        fn = fn_name or ""
        logger.debug(
            "%s retorno preview: error=%s source=%s text_len=%d",
            fn,
            result.get("error"),
            result.get("source"),
            len((result.get("analysis_text") or "")),
        )
    except Exception:
        logger.exception("Falha ao logar retorno")
    return result

def log_io(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            logger.debug("Entrando %s kwargs_keys=%s", func.__name__, list(kwargs.keys()))
        except Exception:
            logger.exception("Erro ao logar entrada")
        res = func(*args, **kwargs)
        try:
            logger.debug("Saindo %s retorno_type=%s keys=%s", func.__name__, type(res).__name__, list(res.keys()) if isinstance(res, dict) else None)
        except Exception:
            logger.exception("Erro ao logar saída")
        return res
    return wrapper

# -------------------------
# GenAI client + SDK caller
# -------------------------
def _init_genai_client():
    try:
        import genai
    except Exception:
        try:
            from google import genai  # type: ignore
        except Exception:
            raise RuntimeError("Biblioteca 'genai' não encontrada. Instale 'genai' ou 'google-genai'.")

    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    location = (
        os.getenv("GOOGLE_CLOUD_LOCATION")
        or os.getenv("GOOGLE_CLOUD_REGION")
        or os.getenv("GENAI_LOCATION")
        or "us-central1"
    )

    use_vertex = str(os.getenv("GENAI_VERTEXAI", "")).lower() in ("1", "true", "yes")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    if api_key:
        try:
            try:
                genai.configure(api_key=api_key)
            except Exception:
                pass
            logger.info("Inicializando genai.Client (API key).")
            return genai.Client(api_key=api_key)
        except Exception as e:
            raise RuntimeError("Falha ao inicializar genai.Client com API key: " + str(e)) from e

    if use_vertex:
        if not project:
            raise RuntimeError("Para usar Vertex AI defina GENAI_VERTEXAI=1 e GOOGLE_CLOUD_PROJECT.")
        if not cred_path or not os.path.exists(cred_path) or not os.access(cred_path, os.R_OK):
            raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS inválido ou inacessível: {cred_path}")
        try:
            logger.info("Inicializando genai.Client (Vertex): project=%s, location=%s", project, location)
            return genai.Client(vertexai=True, project=project, location=location)
        except Exception as e:
            raise RuntimeError("Falha ao inicializar genai.Client para Vertex AI: " + str(e)) from e

    raise RuntimeError("Defina GENAI_API_KEY (modo API) ou GENAI_VERTEXAI=1 com GOOGLE_CLOUD_PROJECT.")

def _extract_text_from_response(resp) -> str:
    """Extrai texto de várias formas de resposta do SDK."""
    if resp is None:
        return ""
    if hasattr(resp, "text"):
        try:
            return resp.text
        except Exception:
            pass
    try:
        out = getattr(resp, "output", None)
        if out:
            if isinstance(out, (list, tuple)) and len(out) > 0:
                first = out[0]
                if isinstance(first, dict):
                    content = first.get("content") or first.get("text") or first.get("message")
                    if isinstance(content, list) and len(content) > 0:
                        for c in content:
                            if isinstance(c, dict) and "text" in c:
                                return c["text"]
                        return " ".join([str(x) for x in content])
                    if isinstance(content, str):
                        return content
            if isinstance(out, dict):
                return json.dumps(out, ensure_ascii=False)
    except Exception:
        pass
    try:
        if hasattr(resp, "candidates"):
            cand = getattr(resp, "candidates")
            if isinstance(cand, (list, tuple)) and len(cand) > 0:
                first = cand[0]
                if hasattr(first, "content"):
                    return str(first.content)
    except Exception:
        pass
    try:
        return str(resp)
    except Exception:
        return ""

# -------------------------
# Normalização e validação
# -------------------------
def normalize_chart_positions(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def parse_float(v: Any) -> Optional[float]:
        try:
            return float(v)
        except Exception:
            return None

    def parse_degree_string(s: Any) -> Optional[float]:
        if not s:
            return None
        try:
            t = str(s).replace("°", " ").replace("'", " ").replace('"', " ").replace(",", ".")
            parts = [p for p in t.split() if p.strip()]
            if len(parts) == 1:
                return float(parts[0])
            deg = float(parts[0])
            minutes = float(parts[1]) if len(parts) > 1 else 0.0
            seconds = float(parts[2]) if len(parts) > 2 else 0.0
            return deg + minutes / 60.0 + seconds / 3600.0
        except Exception:
            return None

    out: List[Dict[str, Any]] = []
    for row in records or []:
        planet = row.get("planet") or row.get("name") or ""
        lon_raw = row.get("longitude") or row.get("lon") or row.get("long") or row.get("ecl_lon") or row.get("deg") or row.get("degree")
        longitude = parse_float(lon_raw) if lon_raw is not None else None
        if longitude is None and isinstance(lon_raw, str):
            longitude = parse_degree_string(lon_raw)
        if longitude is not None:
            longitude = float(longitude) % 360.0

        degree_raw = row.get("degree")
        degree = parse_float(degree_raw) if degree_raw is not None else None
        if degree is None and longitude is not None:
            degree = float(longitude) % 30.0

        sign = row.get("sign") or row.get("zodiac") or ""
        try:
            house_raw = row.get("house") or row.get("casa")
            house = int(float(house_raw)) if house_raw not in (None, "", "None") else None
        except Exception:
            house = None

        out.append({
            "planet": str(planet) if planet is not None else "",
            "longitude": longitude,
            "sign": str(sign) if sign is not None else "",
            "degree": degree,
            "house": house,
        })
    return out

def validate_chart_positions(records: List[Dict[str, Any]]) -> List[str]:
    warnings: List[str] = []
    for r in records:
        planet = r.get("planet", "<unknown>")
        if r.get("longitude") is None:
            warnings.append(f"Longitude ausente para {planet}")
        if r.get("degree") is None:
            warnings.append(f"Degree ausente para {planet}")
        if r.get("house") is None:
            warnings.append(f"House ausente para {planet}")
    return warnings

# -------------------------
# Helpers para prompt
# -------------------------
DEFAULT_PROMPT = (
    "A partir das posições calculadas, gere uma interpretação do mapa astral:\n\n"
    "Lista de planetas com campos planet, longitude, sign, degree e house.\n\n"
    "Interprete o meu mapa astral seguindo as seções numeradas:\n\n"
    "1) Me explique com analogia ao teatro, o que é o planeta, o signo e a casa na astrologia (máx. 8 linhas) de forma clara.\n\n"
    "2) Interprete o posicionamento da primeira tríade de planetas pessoais, com o detalhe de cada casa: Ascendente, Sol e Lua (máx.8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "3) Interprete o posicionamento da segunda tríade de planetas pessoais, com o detalhe de cada casa: Marte, Mercúrio e Vênus (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "4) Interprete o posicionamento dos planetas sociais, com o detalhe de cada casa: Júpiter e Saturno (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "5) Interprete o posicionamento da tríade de planetas geracionais, com o detalhe de cada casa: Urano, Netuno e Plutão (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "6) Para encerrar esta análise, foque nos quatro elementos (Terra, Água, Fogo, Ar) e indique qual energia domina o temperamento; explique brevemente como isso se manifesta (máx. 8 linhas), fornecendo aplicações práticas.\n\n"
    "7) Informação adicional sobre astrologia cármica: comente sobre Sol, Lua, Nodo Sul, Nodo Norte e Roda da Fortuna e Planetas Retrógrados (máx. 10 linhas), fornecendo aplicações práticas.\n\n"
    "Por favor, responda apenas com o texto interpretativo numerado conforme as seções acima."
)

def _positions_block_from_records(records: List[Dict[str, Any]]) -> str:
    lines = ["Posições (planet, longitude, sign, degree, house):"]
    for r in records or []:
        planet = r.get("planet") or r.get("name") or ""
        lon = r.get("longitude", r.get("lon", ""))
        sign = r.get("sign", "")
        degree = r.get("degree", r.get("deg", ""))
        house = r.get("house", r.get("casa", ""))
        try:
            lon_s = f"{float(lon):.6f}" if lon not in (None, "") else ""
        except Exception:
            lon_s = str(lon)
        try:
            deg_s = f"{float(degree):.6f}" if degree not in (None, "") else ""
        except Exception:
            deg_s = str(degree)
        house_s = str(int(house)) if house not in (None, "") and house != "" else ""
        lines.append(f"- {planet}, {lon_s}, {sign}, {deg_s}, {house_s}")
    return "\n".join(lines)

def _ensure_prompt_is_string(p: Union[str, Dict[str, Any], List[Dict[str, Any]]]) -> str:
    if isinstance(p, str):
        return p
    try:
        if isinstance(p, list):
            records = p
            try:
                records = normalize_chart_positions(records)
            except Exception:
                logger.debug("normalize_chart_positions falhou ao normalizar lista", exc_info=True)
            return _positions_block_from_records(records) + "\n\n" + DEFAULT_PROMPT

        if isinstance(p, dict):
            if "chart_positions" in p and isinstance(p["chart_positions"], (list, dict)):
                cp = p["chart_positions"]
                if isinstance(cp, dict):
                    records = []
                    for k, v in cp.items():
                        if isinstance(v, dict):
                            rec = {
                                "planet": k,
                                "longitude": v.get("longitude", v.get("lon", v.get("deg", v.get("degree", "")))),
                                "sign": v.get("sign", v.get("zodiac", "")),
                                "degree": v.get("degree", v.get("deg", "")),
                                "house": v.get("house", v.get("casa", "")),
                            }
                        else:
                            rec = {"planet": k, "value": str(v)}
                        records.append(rec)
                else:
                    records = list(cp)
                try:
                    records = normalize_chart_positions(records)
                except Exception:
                    logger.debug("normalize_chart_positions falhou ao normalizar dict chart_positions", exc_info=True)
                instruction = p.get("instruction") or ""
                positions_block = _positions_block_from_records(records)
                if instruction:
                    return positions_block + "\n\n" + "Instrução:\n" + instruction
                return positions_block + "\n\n" + DEFAULT_PROMPT

            try:
                return "Contexto:\n" + json.dumps(p, ensure_ascii=False, indent=2) + "\n\n" + DEFAULT_PROMPT
            except Exception:
                return str(p) + "\n\n" + DEFAULT_PROMPT
    except Exception:
        logger.exception("Falha ao converter prompt para string; usando str(prompt) como fallback")
        try:
            return json.dumps(p, ensure_ascii=False)
        except Exception:
            return str(p)
    return str(p)

# -------------------------
# Chamada ao SDK (compatível com várias assinaturas)
# -------------------------
def _call_gemini_sdk(
    prompt: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    model: str = GEMINI_MODEL,
    max_tokens: int = 2000,
) -> str:
    # rate limit
    try:
        _rate_limit_wait()
    except Exception:
        logger.debug("Rate limit wait falhou ou não implementado", exc_info=True)

    client = None
    try:
        client = _init_genai_client()
    except Exception as e:
        logger.debug("Falha ao inicializar genai client: %s", e, exc_info=True)
        client = None

    # coercion defensiva para string
    try:
        prompt_text = _ensure_prompt_is_string(prompt)
    except Exception:
        prompt_text = str(prompt)

    logger.debug("PROMPT FINAL (preview): %s", str(prompt_text)[:4000])

    last_exc = None

    # tentar assinaturas conhecidas do SDK
    try:
        if client and hasattr(client, "models") and hasattr(client.models, "generate_content"):
            try:
                resp = client.models.generate_content(model=model, contents=prompt_text)
            except TypeError:
                try:
                    resp = client.models.generate_content(model=model, content=prompt_text)
                except TypeError:
                    resp = client.models.generate_content(model=model, input=prompt_text)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e

    try:
        if client and hasattr(client, "responses") and hasattr(client.responses, "create"):
            try:
                resp = client.responses.create(model=model, input=prompt_text)
            except TypeError:
                resp = client.responses.create(model=model, prompt=prompt_text)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e

    try:
        if client and hasattr(client, "generate"):
            resp = client.generate(model=model, prompt=prompt_text, max_output_tokens=max_tokens)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e

    msg = "Não foi possível chamar o SDK google-genai com as assinaturas conhecidas."
    if last_exc:
        msg += f" Último erro: {last_exc}"
    raise RuntimeError(msg)

def _call_gemini_sdk_with_retry(prompt: Union[str, Dict[str, Any], List[Dict[str, Any]]], model: str = GEMINI_MODEL, max_tokens: int = 2000):
    """
    Envolve _call_gemini_sdk com circuit breaker e retry.
    Retorna string com texto bruto ou lança exceção.
    """
    cache_key = None
    # Se circuito aberto, recusar chamada
    if not _circuit_allows_call():
        raise RuntimeError("Circuit breaker aberto: serviço de IA temporariamente indisponível")

    def _call():
        return _call_gemini_sdk(prompt, model=model, max_tokens=max_tokens)

    try:
        raw = retry_with_backoff(_call, max_attempts=int(os.getenv("GENERATOR_RETRY_ATTEMPTS", "4")), base_delay=float(os.getenv("GENERATOR_RETRY_BASE_DELAY", "0.6")))
        _record_success()
        return raw
    except Exception as e:
        _record_failure()
        logger.exception("Chamada ao SDK falhou após retries: %s", e)
        raise

# -------------------------
# Builder de prompt a partir de chart_summary
# -------------------------
def build_prompt_from_chart_summary(
    chart_summary: Dict[str, Any],
    prompt_template: Optional[str] = None,
) -> str:
    if not prompt_template:
        prompt_template = DEFAULT_PROMPT

    place = chart_summary.get("place") or ""
    bdate = chart_summary.get("bdate")
    btime = chart_summary.get("btime") or ""
    lat = chart_summary.get("lat")
    lon = chart_summary.get("lon")
    timezone = chart_summary.get("timezone")

    chart_positions = chart_summary.get("chart_positions")
    if not chart_positions:
        summary_obj = chart_summary.get("summary") if isinstance(chart_summary.get("summary"), dict) else chart_summary
        chart_positions = summary_obj.get("table") if isinstance(summary_obj, dict) else chart_summary.get("table")

    date_text = bdate.strftime("%d/%m/%Y") if isinstance(bdate, date) else str(bdate or "")
    time_text = str(btime).strip() if btime else "Hora não informada"

    header_lines: List[str] = []
    if place:
        header_lines.append(f"Cidade: {place}")
    if date_text:
        header_lines.append(f"Data de nascimento: {date_text}")
    if time_text:
        header_lines.append(f"Hora de nascimento (local): {time_text}")
    if lat is not None and lon is not None:
        try:
            header_lines.append(f"Coordenadas: {float(lat):.6f}, {float(lon):.6f}")
        except Exception:
            header_lines.append(f"Coordenadas: {lat}, {lon}")
    if timezone:
        header_lines.append(f"Timezone: {timezone}")
    header = ("\n".join(header_lines) + "\n\n") if header_lines else ""

    records: List[Dict[str, Any]] = []
    if chart_positions:
        if isinstance(chart_positions, dict):
            for k, v in chart_positions.items():
                if isinstance(v, dict):
                    rec = {
                        "planet": k,
                        "longitude": v.get("longitude", v.get("lon", v.get("deg", v.get("degree", "")))),
                        "sign": v.get("sign", v.get("zodiac", "")),
                        "degree": v.get("degree", v.get("deg", "")),
                        "house": v.get("house", v.get("casa", "")),
                    }
                else:
                    rec = {"planet": k, "value": str(v)}
                records.append(rec)
        elif isinstance(chart_positions, list):
            records = list(chart_positions)

    if records:
        try:
            records = normalize_chart_positions(records)
        except Exception:
            logger.exception("normalize_chart_positions falhou; prosseguindo com registros originais")

    if records:
        lines = ["Posições calculadas:"]
        for r in records:
            planet = r.get("planet") or r.get("name") or ""
            longitude = r.get("longitude", r.get("value", ""))
            sign = r.get("sign", "") or ""
            degree = r.get("degree", "")
            house = r.get("house", "")
            try:
                lon_str = f"{float(longitude):.6f}" if longitude not in (None, "") else ""
            except Exception:
                lon_str = str(longitude)
            deg_str = f"{float(degree):.6f}" if degree not in (None, "") else ""
            house_str = str(int(house)) if house not in (None, "") else ""
            lines.append(f"- {planet}: longitude={lon_str}; sign={sign}; degree={deg_str}; house={house_str}")
        positions_text = "\n".join(lines) + "\n\n"
    else:
        positions_text = "\nPosições calculadas: indisponíveis (sem hora precisa ou erro no cálculo).\n\n"

    try:
        prompt_body = (
            prompt_template
            .replace("{place}", place)
            .replace("{bdate}", date_text)
            .replace("{btime}", time_text)
        )
    except Exception:
        prompt_body = prompt_template

    return header + positions_text + prompt_body

# -------------------------
# Funções públicas
# -------------------------
def _fallback_result(source: str = "local_ai", error: Optional[str] = None) -> Dict[str, Any]:
    return {
        "analysis_text": "",
        "analysis_json": None,
        "raw_text": "",
        "source": source,
        "error": error,
    }

@log_io
def generate_ai_text_from_chart(
    chart_summary: Dict[str, Any],
    model: Optional[str] = None,
    prompt_template: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Gera texto interpretativo via GenAI. Retorna dict consistente:
      - analysis_text (string, pode ser fallback)
      - analysis_json (dict/list|null)
      - raw_text (string bruto)
      - error (string|null)
      - prompt (string|null)
      - chart_summary (o summary normalizado)
      - source (local_ai)
    """
    result: Dict[str, Any] = {
        "analysis_text": "",
        "analysis_json": None,
        "raw_text": "",
        "error": None,
        "prompt": None,
        "chart_summary": None,
        "source": "local_ai",
    }

    target_model = model or GEMINI_MODEL
    if not target_model:
        err = "Nenhum modelo configurado (GEMINI_MODEL/GENAI_MODEL)."
        logger.error(err)
        result["error"] = err
        result["analysis_text"] = "Interpretação não disponível: configuração de modelo ausente."
        return _log_and_return(result, "generate_ai_text_from_chart")

    # Inicializa cliente cedo (apenas para validar)
    try:
        _ = _init_genai_client()
    except Exception as e:
        logger.exception("Falha ao inicializar genai.Client")
        result["error"] = f"Falha ao inicializar genai.Client: {e}"
        result["analysis_text"] = "Interpretação não disponível: falha ao inicializar o cliente de IA."
        return _log_and_return(result, "generate_ai_text_from_chart")

    kwargs.pop("model", None)

    # Normaliza chart_summary
    try:
        if isinstance(chart_summary, dict) and isinstance(chart_summary.get("planets"), dict):
            try:
                chart_summary_struct = build_chart_summary_from_natal(chart_summary)
            except Exception:
                logger.warning("Fallback: usando 'planets' como chart_positions.")
                chart_summary_struct = {"chart_positions": chart_summary.get("planets")}
            chart_summary_struct.setdefault("place", chart_summary.get("place", ""))
            chart_summary_struct.setdefault("bdate", chart_summary.get("bdate"))
            chart_summary_struct.setdefault("btime", chart_summary.get("btime", ""))
        elif isinstance(chart_summary, dict) and chart_summary.get("place") and chart_summary.get("bdate"):
            chart_summary_struct = prepare_chart_summary_from_inputs(
                place=chart_summary.get("place"),
                bdate=chart_summary.get("bdate"),
                btime=chart_summary.get("btime", ""),
                house_system=chart_summary.get("house_system", "Placidus"),
            )
            if not chart_summary_struct.get("btime"):
                err = "Hora de nascimento não informada. A interpretação exige hora precisa."
                logger.error(err)
                result["error"] = err
                result["analysis_text"] = "Interpretação não disponível: informe a hora de nascimento."
                result["chart_summary"] = chart_summary_struct
                return _log_and_return(result, "generate_ai_text_from_chart")
        else:
            chart_summary_struct = chart_summary or {}
    except Exception as e:
        logger.exception("Erro ao normalizar chart_summary")
        result["error"] = f"Erro ao normalizar chart_summary: {e}"
        result["analysis_text"] = "Interpretação não disponível: erro ao preparar dados do mapa."
        return _log_and_return(result, "generate_ai_text_from_chart")

    result["chart_summary"] = chart_summary_struct

    # Cache
    try:
        cache_key = _make_cache_key(target_model, chart_summary_struct)
        cached = _cache_get(cache_key)
        if cached:
            logger.debug("Cache hit para %s", cache_key)
            # garantir formato mínimo
            cached.setdefault("analysis_text", cached.get("raw_text") or "Interpretação não disponível no momento.")
            return cached
    except Exception:
        logger.exception("Erro ao acessar cache (continuando sem cache)")

    # Prompt
    if not prompt_template:
        prompt_template = DEFAULT_PROMPT

    try:
        prompt = build_prompt_from_chart_summary(chart_summary_struct, prompt_template=prompt_template)
        result["prompt"] = prompt
        logger.debug("Prompt (head): %s", (prompt or "")[:500])
    except Exception as e:
        logger.exception("Erro ao montar prompt")
        result["error"] = f"Erro ao montar prompt: {e}"
        result["analysis_text"] = "Interpretação não disponível: erro ao montar prompt."
        return _log_and_return(result, "generate_ai_text_from_chart")

        # Chamada ao SDK com retry e circuit breaker; fallback para cache se disponível
    try:
        raw = _call_gemini_sdk_with_retry(prompt, model=target_model, max_tokens=kwargs.get("max_tokens", 2000))
        result["raw_text"] = raw or ""
    except Exception as e:
        logger.exception("Erro ao chamar _call_gemini_sdk_with_retry: %s", e)
        # tentar retornar cache se existir
        try:
            cache_key = _make_cache_key(target_model, chart_summary_struct)
            cached = _cache_get(cache_key)
            if cached:
                logger.warning("Retornando resultado em cache devido a falha no SDK")
                return cached
        except Exception:
            logger.exception("Erro ao acessar cache durante fallback")
        # fallback amigável
        result["error"] = str(e)
        result["analysis_text"] = "Interpretação não disponível no momento: serviço de IA temporariamente indisponível."
        result["raw_text"] = ""
        result["source"] = "fallback"
        return _log_and_return(result, "generate_ai_text_from_chart")

    # Normaliza saída
    text = (result.get("raw_text") or "").strip()
    parsed_json = None
    try:
        if text:
            # tenta parsear JSON se o texto começar com { ou [
            t = text.strip()
            if t.startswith("{") or t.startswith("["):
                try:
                    parsed_json = json.loads(t)
                except Exception:
                    parsed_json = None
    except Exception:
        parsed_json = None

    if not text and parsed_json:
        try:
            text = json.dumps(parsed_json, ensure_ascii=False, indent=2)
        except Exception:
            text = ""

    if not text:
        name = chart_summary_struct.get("name") or "Interpretação"
        text = f"{name}: interpretação não disponível no momento. Verifique os dados do mapa ou tente novamente."

    result["analysis_text"] = text
    result["analysis_json"] = parsed_json

    # Salva cache
    try:
        if result.get("analysis_text"):
            _cache_set(cache_key, result)
    except Exception:
        logger.exception("Erro ao gravar cache (ignorando)")

    return _log_and_return(result, "generate_ai_text_from_chart")

@log_io
def generate_analysis(
    chart_input: Dict[str, Any],
    prefer: str = "auto",
    text_only: bool = False,
    **kwargs
) -> Dict[str, Any]:
    """
    Gera texto de análise (sem SVG).
    Retorna dict com keys: analysis_text, analysis_json, raw_text, source, error
    """
    result: Dict[str, Any] = {"analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none", "error": None}

    # Decide se usa API externa
    use_api = False
    if prefer == "api":
        use_api = True
    elif prefer == "auto":
        try:
            api_ok = api_client.health_check().get("configured", False)
            use_api = bool(api_ok)
        except Exception:
            use_api = False

    api_error: Optional[str] = None

    # Fluxo somente texto (text_only True)
    if text_only:
        if use_api:
            try:
                name = chart_input.get("name", "")
                dt = chart_input.get("dt")
                lat = chart_input.get("lat", 0.0)
                lon = chart_input.get("lon", 0.0)
                tz = chart_input.get("tz", "")
                api_resp = api_client.fetch_natal_chart_api(name, dt if isinstance(dt, datetime) else dt, lat, lon, tz)
                analysis_text = api_resp.get("analysis_text") or api_resp.get("interpretation") or ""
                result.update({
                    "analysis_text": analysis_text or f"{name or 'Interpretação'}: interpretação não disponível no momento.",
                    "analysis_json": api_resp.get("analysis_json"),
                    "raw_text": api_resp.get("raw_text", ""),
                    "source": "api"
                })
                return _log_and_return(result, "generate_analysis")
            except Exception as e:
                logger.exception("Erro ao chamar API externa")
                api_error = str(e)

        # Fallback local AI
        try:
            summary = chart_input.get("summary")
            if not summary and chart_input.get("place") and chart_input.get("bdate"):
                if not chart_input.get("btime"):
                    result["error"] = (result.get("error") or "") + "; Hora de nascimento não informada."
                    result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: hora não informada."
                    result["source"] = "local_ai"
                    return _log_and_return(result, "generate_analysis")
                summary = prepare_chart_summary_from_inputs(chart_input.get("place"), chart_input.get("bdate"), chart_input.get("btime", ""))

            if summary:
                model = kwargs.get("model") or kwargs.get("model_choice")
                _extra = {k: v for k, v in kwargs.items() if k != "model"}
                ai_res = generate_ai_text_from_chart(summary, model=model, **_extra)
                if ai_res.get("error"):
                    combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                    result["error"] = combined_err or result.get("error")
                result["analysis_text"] = ai_res.get("analysis_text") or ai_res.get("raw_text") or f"{summary.get('name','Interpretação')}: interpretação não disponível."
                result["analysis_json"] = ai_res.get("analysis_json")
                result["raw_text"] = ai_res.get("raw_text") or ""
                result["source"] = "local_ai"
            else:
                result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: interpretação não disponível."
                result["analysis_json"] = None
                result["source"] = "local_ai"
        except Exception as e:
            logger.exception("AI generation error")
            result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"
            result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: interpretação não disponível."
            result["analysis_json"] = None
            result["source"] = "local_ai"

        return _log_and_return(result, "generate_analysis")

    # Fluxo padrão (sem SVG): tentar API, senão fallback local
    if use_api:
        try:
            name = chart_input.get("name", "")
            dt = chart_input.get("dt")
            lat = chart_input.get("lat", 0.0)
            lon = chart_input.get("lon", 0.0)
            tz = chart_input.get("tz", "")
            api_resp = api_client.fetch_natal_chart_api(name, dt if isinstance(dt, datetime) else dt, lat, lon, tz)
            analysis_text = api_resp.get("analysis_text") or api_resp.get("interpretation") or ""
            result.update({
                "analysis_text": analysis_text or f"{name or 'Interpretação'}: interpretação não disponível no momento.",
                "analysis_json": api_resp.get("analysis_json"),
                "raw_text": api_resp.get("raw_text", ""),
                "source": "api"
            })
            return _log_and_return(result, "generate_analysis")
        except Exception as e:
            logger.exception("Erro ao chamar API externa")
            api_error = str(e)

    # Fallback local AI (sem SVG)
    try:
        summary = chart_input.get("summary")
        if not summary and chart_input.get("place") and chart_input.get("bdate"):
            if not chart_input.get("btime"):
                result["error"] = (result.get("error") or "") + "; Hora de nascimento não informada."
                result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: hora não informada."
                result["analysis_json"] = None
                return _log_and_return(result, "generate_analysis")
            summary = prepare_chart_summary_from_inputs(chart_input.get("place"), chart_input.get("bdate"), chart_input.get("btime", ""))

        if summary:
            model = kwargs.get("model") or kwargs.get("model_choice")
            _extra = {k: v for k, v in kwargs.items() if k != "model"}
            ai_res = generate_ai_text_from_chart(summary, model=model, **_extra)
            if ai_res.get("error"):
                combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                result["error"] = combined_err or result.get("error")
            result["analysis_text"] = ai_res.get("analysis_text") or ai_res.get("raw_text") or f"{summary.get('name','Interpretação')}: interpretação não disponível."
            result["analysis_json"] = ai_res.get("analysis_json")
            result["raw_text"] = ai_res.get("raw_text") or ""
            result["source"] = "local_ai"
        else:
            result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: interpretação não disponível."
            result["analysis_json"] = None
    except Exception as e:
        logger.exception("AI generation error")
        result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"
        result["analysis_text"] = f"{chart_input.get('name','Interpretação')}: interpretação não disponível."
        result["analysis_json"] = None

    return _log_and_return(result, "generate_analysis")

# -------------------------
# Função utilitária para gerar interpretação (validação + preview + chamada)
# -------------------------
def generate_interpretation_from_summary(
    summary: Dict[str, Any],
    generate_fn,
    timeout_seconds: int = 60,
) -> Dict[str, Any]:
    """
    Normaliza e valida chart_positions, monta prompt e chama generate_fn (ex: generate_analysis).
    Retorna o dict de resposta (nunca None).
    """
    table = summary.get("table") or summary.get("planets") or []
    if isinstance(table, dict):
        table = [{"planet": k, **(v if isinstance(v, dict) else {"value": str(v)})} for k, v in table.items()]

    chart_positions = normalize_chart_positions(table)

    warnings = validate_chart_positions(chart_positions)
    if warnings:
        return {"error": "Dados incompletos: chart_positions inválido.", "warnings": warnings, "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}

    chart_input = {
        "name": summary.get("name"),
        "place": summary.get("place"),
        "bdate": summary.get("bdate"),
        "btime": summary.get("btime"),
        "lat": summary.get("lat"),
        "lon": summary.get("lon"),
        "timezone": summary.get("timezone"),
        "chart_positions": chart_positions,
        "summary": summary,
    }

    prompt_preview = build_prompt_from_chart_summary(chart_input)
    logger.debug("Prompt preview (first 2000 chars): %s", prompt_preview[:2000])

    # chamar a função de geração com timeout (defensivo)
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(generate_fn, chart_input, prefer="auto", text_only=True)
            try:
                res = future.result(timeout=timeout_seconds)
            except concurrent.futures.TimeoutError:
                logger.exception("Timeout ao chamar generate_fn")
                return {"error": f"Timeout: o serviço demorou mais que {timeout_seconds} segundos.", "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}
            except Exception as e:
                logger.exception("generate_fn lançou exceção: %s", e)
                try:
                    exc = future.exception()
                    if exc:
                        logger.exception("Detalhe da exceção na future: %s", exc)
                except Exception:
                    logger.exception("Falha ao obter exceção da future")
                return {"error": f"Erro interno no gerador: {e}", "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}

            if res is None:
                logger.error("generate_fn retornou None para chart_input=%r", chart_input)
                return {"error": "Serviço retornou None", "raw_response": None, "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}

            # garantir que res seja dict e contenha chaves mínimas
            if not isinstance(res, dict):
                logger.warning("generate_fn retornou tipo inesperado: %r", type(res))
                return {"error": "Resposta inválida do serviço", "raw_response": str(res), "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}

            # normalizar chaves mínimas
            res.setdefault("analysis_text", res.get("raw_text", "") or "")
            res.setdefault("analysis_json", None)
            res.setdefault("raw_text", res.get("raw_text", "") or "")
            res.setdefault("source", res.get("source", "unknown"))
            res.setdefault("error", res.get("error", None))

            return res
    except Exception as e:
        logger.exception("Erro inesperado ao submeter generate_fn: %s", e)
        return {"error": str(e), "analysis_text": "", "analysis_json": None, "raw_text": "", "source": "none"}

# -------------------------
# prepare_chart_summary_from_inputs
# -------------------------
def prepare_chart_summary_from_inputs(
    place: str,
    bdate: date,
    btime: Optional[str],
    house_system: str = "Placidus",
) -> Dict[str, Any]:
    """
    Faz geocode, timezone, parse de hora e cálculo de posições.
    Retorna dict com keys: place, bdate, btime, lat, lon, timezone, chart_positions (lista de dicts).
    Nunca assume hora padrão: se btime faltar/for inválida, retorna sem chart_positions.
    """
    out: Dict[str, Any] = {"place": place, "bdate": bdate, "btime": btime, "lat": None, "lon": None, "timezone": None, "chart_positions": None}
    try:
        # geocode
        coords = geocode_place(place)
        if coords:
            out["lat"], out["lon"] = coords.get("lat"), coords.get("lon")
        # timezone
        if out["lat"] is not None and out["lon"] is not None:
            tz = get_timezone_from_coords(out["lat"], out["lon"])
            out["timezone"] = tz
        # parse hora
        if not btime or not str(btime).strip():
            logger.error("Hora de nascimento não informada. place=%r bdate=%r", place, bdate)
            return out
        parsed_time = parse_birth_time(btime)
        if not parsed_time:
            logger.error("Hora de nascimento inválida: %r", btime)
            return out
        # compute positions (pode lançar)
        try:
            positions = compute_chart_positions(out["lat"], out["lon"], bdate, parsed_time, house_system=house_system)
            out["chart_positions"] = positions
        except Exception:
            logger.exception("Falha ao calcular posições do mapa")
            out["chart_positions"] = None
    except Exception:
        logger.exception("Erro em prepare_chart_summary_from_inputs")
    return out