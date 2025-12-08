# services/generator_service.py
from __future__ import annotations
"""
Gerador unificado de análise astrológica (SVG + texto).
- Prepara dados do mapa (geocode, timezone, parse hora, posições).
- Monta prompt consistente para o LLM.
- Chama SDK GenAI (compatível com várias versões).
- Aplica cache simples e rate limiting.
- Expondo duas funções públicas:
    - generate_ai_text_from_chart(chart_summary, ...)
    - generate_analysis(chart_input, prefer="auto", text_only=False, ...)
"""

import os
import json
import time
import threading
import hashlib
import logging
from typing import Any, Dict, Optional, Union, List
from datetime import datetime, date

# Importações de serviços do projeto (ajuste caminhos se necessário)
from services.swisseph_client import natal_positions
from .chart_builder import build_chart_summary_from_natal  # manter apenas summary-from-natal
from .astro_service import geocode_place, get_timezone_from_coords, parse_birth_time, compute_chart_positions

# Integrações externas (stubs/implementações no projeto)
from . import api_client
from . import chart_renderer

logger = logging.getLogger(__name__)

# -------------------------
# Configurações
# -------------------------
_CACHE_TTL_SECONDS = int(os.getenv("GENERATOR_CACHE_TTL", "300"))
_RATE_LIMIT_MIN_INTERVAL = float(os.getenv("GENERATOR_RATE_MIN_INTERVAL", "0.5"))

# Modelo: prioriza envs compatíveis com app.py e este serviço
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"
GEMINI_MODEL = (
    os.getenv("GEMINI_MODEL")
    or os.getenv("GENAI_MODEL")
    or GEMINI_MODEL_DEFAULT
)

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

import json
import logging
from datetime import date
from typing import Any, Dict, List, Optional, Union
import concurrent.futures

logger = logging.getLogger(__name__)

# Nome do modelo (defina em outro lugar do módulo se necessário)
GEMINI_MODEL = globals().get("GEMINI_MODEL", "gemini-default")

# -------------------------
# Normalização e validação
# -------------------------
def normalize_chart_positions(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Normaliza uma lista de registros garantindo:
      - longitude em float 0..360 (ou None)
      - degree em float 0..30 (ou None)
      - house em int 1..12 (ou None)
      - planet e sign como strings
    Retorna nova lista (não modifica a original).
    """
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
    """
    Retorna lista de avisos (strings). Lista vazia significa OK.
    """
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
# Compatibilidade com SDK: aceita prompt str ou estrutura
# -------------------------
def _call_gemini_sdk(
    prompt: Union[str, Dict[str, Any], List[Dict[str, Any]]],
    model: str = GEMINI_MODEL,
    max_tokens: int = 2000,
) -> str:
    """
    Chama o SDK google-genai (várias assinaturas).
    - Se receber string: envia diretamente.
    - Se receber lista: interpreta como lista de posições e monta bloco de posições + DEFAULT_PROMPT.
    - Se receber dict: prioriza prompt["chart_positions"] (list|dict) e opcional prompt["instruction"].
    - Usa funções auxiliares definidas em globals(): _rate_limit_wait, _init_genai_client, _extract_text_from_response.
    """
    _rate_limit_wait = globals().get("_rate_limit_wait")
    _init_genai_client = globals().get("_init_genai_client")
    _extract_text_from_response = globals().get("_extract_text_from_response")
    
    # aplicar rate limit se disponível
    if callable(_rate_limit_wait):
        try:
            _rate_limit_wait()
        except Exception:
            logger.debug("Rate limit wait falhou ou não implementado", exc_info=True)

    client = None
    if callable(_init_genai_client):
        try:
            client = _init_genai_client()
        except Exception as e:
            logger.debug("Falha ao inicializar genai client: %s", e, exc_info=True)

    # --- coercion defensiva: garantir prompt string com bloco de posições ---
def _positions_block_from_records(records):
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

def _ensure_prompt_is_string(p):
    if isinstance(p, str):
        return p
    try:
        # lista direta de registros
        if isinstance(p, list):
            records = p
            normalize_fn = globals().get("normalize_chart_positions")
            if callable(normalize_fn):
                try:
                    records = normalize_fn(records)
                except Exception:
                    logger.debug("normalize_chart_positions falhou ao normalizar lista", exc_info=True)
            return _positions_block_from_records(records) + "\n\n" + DEFAULT_PROMPT

        # dict: priorizar chart_positions
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
                normalize_fn = globals().get("normalize_chart_positions")
                if callable(normalize_fn):
                    try:
                        records = normalize_fn(records)
                    except Exception:
                        logger.debug("normalize_chart_positions falhou ao normalizar dict chart_positions", exc_info=True)
                instruction = p.get("instruction") or ""
                positions_block = _positions_block_from_records(records)
                if instruction:
                    return positions_block + "\n\n" + "Instrução:\n" + instruction
                return positions_block + "\n\n" + DEFAULT_PROMPT

            # fallback: serializar dict como JSON e anexar DEFAULT_PROMPT
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

    # aplicar coercion e logar
    prompt = _ensure_prompt_is_string(prompt)
    logger.debug("PROMPT FINAL (após coercion) type=%s len=%d", type(prompt), len(str(prompt)))
    logger.debug("PROMPT FINAL (preview): %s", str(prompt)[:8000])
    # --- fim coercion defensiva ---

    # Serializar estrutura para texto legível e compor com DEFAULT_PROMPT quando aplicável
    if not isinstance(prompt, str):
        try:
            # Caso: lista de registros (assumir lista de posições)
            if isinstance(prompt, list):
                # normalizar se função disponível
                normalize_fn = globals().get("normalize_chart_positions")
                records = prompt
                if callable(normalize_fn):
                    try:
                        records = normalize_fn(records)
                    except Exception:
                        logger.debug("normalize_chart_positions falhou ao normalizar lista", exc_info=True)
                prompt_text = _positions_block_from_records(records) + "\n\n" + DEFAULT_PROMPT
                prompt = prompt_text
            else:
                # prompt é dict: priorizar chart_positions
                if "chart_positions" in prompt and isinstance(prompt["chart_positions"], (list, dict)):
                    cp = prompt["chart_positions"]
                    # converter dict -> lista de registros se necessário
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
                    # normalizar se possível
                    normalize_fn = globals().get("normalize_chart_positions")
                    if callable(normalize_fn):
                        try:
                            records = normalize_fn(records)
                        except Exception:
                            logger.debug("normalize_chart_positions falhou ao normalizar dict chart_positions", exc_info=True)
                    # instrução customizável
                    instruction = prompt.get("instruction") or ""
                    positions_block = _positions_block_from_records(records)
                    if instruction:
                        prompt_text = positions_block + "\n\n" + "Instrução:\n" + instruction
                    else:
                        prompt_text = positions_block + "\n\n" + DEFAULT_PROMPT
                    prompt = prompt_text
                else:
                    # fallback: serializar dict como JSON legível (contexto) e anexar DEFAULT_PROMPT
                    try:
                        prompt_text = "Contexto:\n" + json.dumps(prompt, ensure_ascii=False, indent=2)
                        prompt = prompt_text + "\n\n" + DEFAULT_PROMPT
                    except Exception:
                        prompt = str(prompt) + "\n\n" + DEFAULT_PROMPT
        except Exception:
            try:
                prompt = json.dumps(prompt, ensure_ascii=False)
            except Exception:
                prompt = str(prompt)

    # debug: preview do prompt (cortar)
    try:
        logger.debug("Prompt preview: %s", str(prompt)[:4000])
    except Exception:
        pass

    last_exc = None

    # tentar assinaturas conhecidas do SDK
    try:
        if client and hasattr(client, "models") and hasattr(client.models, "generate_content"):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
            except TypeError:
                try:
                    resp = client.models.generate_content(model=model, content=prompt)
                except TypeError:
                    resp = client.models.generate_content(model=model, input=prompt)
            return _extract_text_from_response(resp) if callable(_extract_text_from_response) else str(resp)
    except Exception as e:
        last_exc = e

    if not isinstance(last_exc, ValueError):
        try:
            if client and hasattr(client, "responses") and hasattr(client.responses, "create"):
                try:
                    resp = client.responses.create(model=model, input=prompt)
                except TypeError:
                    resp = client.responses.create(model=model, prompt=prompt)
                return _extract_text_from_response(resp) if callable(_extract_text_from_response) else str(resp)
        except Exception as e:
            last_exc = e

    if not isinstance(last_exc, ValueError):
        try:
            if client and hasattr(client, "generate"):
                resp = client.generate(model=model, prompt=prompt, max_output_tokens=max_tokens)
                return _extract_text_from_response(resp) if callable(_extract_text_from_response) else str(resp)
        except Exception as e:
            last_exc = e

    msg = "Não foi possível chamar o SDK google-genai com as assinaturas conhecidas."
    if last_exc:
        msg += f" Último erro: {last_exc}"
    raise RuntimeError(msg)

# -------------------------
# Prompt template e builder
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

def build_prompt_from_chart_summary(
    chart_summary: Dict[str, Any],
    prompt_template: Optional[str] = None,
) -> str:
    """
    Monta o prompt final a partir de um chart_summary.
    - Prioriza chart_positions (lista de registros) ou summary.table.
    - Normaliza posições (chama normalize_chart_positions quando disponível).
    - Não usa str.format() no template para evitar KeyError com placeholders desconhecidos.
    """
    if not prompt_template:
        prompt_template = DEFAULT_PROMPT

    place = chart_summary.get("place") or ""
    bdate = chart_summary.get("bdate")
    btime = chart_summary.get("btime") or ""
    lat = chart_summary.get("lat")
    lon = chart_summary.get("lon")
    timezone = chart_summary.get("timezone")

    # Preferir chart_positions explícito, senão tentar summary.table ou chart_summary['table']
    chart_positions = chart_summary.get("chart_positions")
    if not chart_positions:
        summary_obj = chart_summary.get("summary") if isinstance(chart_summary.get("summary"), dict) else chart_summary
        chart_positions = summary_obj.get("table") if isinstance(summary_obj, dict) else chart_summary.get("table")

    # formatar data/hora para exibição
    date_text = bdate.strftime("%d/%m/%Y") if isinstance(bdate, date) else str(bdate or "")
    time_text = str(btime).strip() if btime else "Hora não informada"

    # montar header com contexto geográfico/temporal
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

    # preparar records a partir de chart_positions (aceita dict/list)
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
        else:
            records = []

    # normalizar registros se possível
    if records:
        try:
            # normalize_chart_positions deve estar definido no módulo; usar via globals() para evitar import circular
            normalize_fn = globals().get("normalize_chart_positions")
            if callable(normalize_fn):
                records = normalize_fn(records)
        except Exception:
            _logger.exception("normalize_chart_positions falhou; prosseguindo com registros originais")

    # montar positions_text legível
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

    # Substituições seguras no template apenas para compatibilidade com templates antigos
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
# Função utilitária para gerar interpretação (validação + preview + chamada)
# -------------------------
def generate_interpretation_from_summary(
    summary: Dict[str, Any],
    generate_fn,
    timeout_seconds: int = 60,
) -> Dict[str, Any]:
    """
    Normaliza e valida chart_positions, exibe preview via streamlit sidebar (se disponível),
    monta prompt e chama generate_fn (ex: generate_analysis). Retorna o dict de resposta.
    """
    try:
        import streamlit as st  # opcional, usado apenas para preview/avisos
    except Exception:
        st = None

    table = summary.get("table") or summary.get("planets") or []
    if isinstance(table, dict):
        table = [{"planet": k, **(v if isinstance(v, dict) else {"value": str(v)})} for k, v in table.items()]

    chart_positions = normalize_chart_positions(table)

    # preview no sidebar para depuração
    if st:
        st.sidebar.markdown("**Preview: chart_positions**")
        try:
            st.sidebar.json(chart_positions)
        except Exception:
            st.sidebar.text(str(chart_positions)[:4000])

    warnings = validate_chart_positions(chart_positions)
    if warnings:
        if st:
            for w in warnings:
                st.sidebar.warning(w)
            st.sidebar.info("Corrija os dados ou confirme manualmente antes de enviar à IA.")
        return {"error": "Dados incompletos: verifique chart_positions no sidebar.", "warnings": warnings}

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

    # prompt preview (curto) para debug
    prompt_preview = build_prompt_from_chart_summary(chart_input)
    logger.debug("Prompt preview (first 2000 chars): %s", prompt_preview[:2000])
    if st:
        try:
            st.sidebar.text_area("Prompt preview (início)", value=prompt_preview[:4000], height=200)
        except Exception:
            pass

    # chamar a função de geração com timeout em executor
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(generate_fn, chart_input, prefer="auto", text_only=True)
            res = future.result(timeout=timeout_seconds)
    except concurrent.futures.TimeoutError:
        logger.exception("Timeout ao chamar generate_fn")
        return {"error": f"Timeout: o serviço demorou mais que {timeout_seconds} segundos."}
    except Exception as e:
        logger.exception("Erro ao chamar generate_fn: %s", e)
        return {"error": str(e)}

    return res

# -------------------------
# prepare_chart_summary_from_inputs (garante chart_positions como lista de dicts)
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
    # Validação rígida de hora: o usuário SEMPRE deve informar.
    if not btime or not str(btime).strip():
        logger.error("Hora de nascimento não informada. place=%r bdate=%r", place, bdate)
        return {
            "place": place,
            "bdate": bdate,
            "btime": "",
            "lat": None,
            "lon": None,
            "timezone": None,
            "chart_positions": None,
            "birth_time_estimated": False,
        }

    lat, lon, display = geocode_place(place)
    if not (lat and lon):
        logger.warning("Geocode falhou para '%s'; lat/lon indisponíveis.", place)

    timezone = get_timezone_from_coords(lat, lon) if (lat and lon) else None
    if (lat and lon) and not timezone:
        logger.warning("Timezone não resolvido para coords (%s, %s).", lat, lon)

    # Hora: não estimamos. Se parse falhar, retornamos sem posições.
    local_dt: Optional[datetime] = None
    try:
        local_dt = parse_birth_time(str(btime).strip(), bdate, timezone) if timezone else None
        if local_dt is None:
            logger.error("Falha ao parsear hora/local_dt (timezone ausente ou inválida).")
    except Exception as e:
        logger.exception("Erro ao parsear hora de nascimento: %s", e)

    chart_positions = None
    if lat and lon and local_dt:
        try:
            raw_positions = compute_chart_positions(lat, lon, local_dt, house_system)
            # Normalizar para lista de dicts com as chaves esperadas
            if isinstance(raw_positions, list):
                # assumir que já está no formato correto
                chart_positions = raw_positions
            elif isinstance(raw_positions, dict):
                # converter dict -> lista de registros
                records = []
                for k, v in raw_positions.items():
                    if isinstance(v, dict):
                        rec = {
                            "planet": k,
                            "longitude": v.get("longitude", v.get("lon", "")),
                            "sign": v.get("sign", ""),
                            "degree": v.get("degree", v.get("deg", "")),
                            "house": v.get("house", v.get("casa", ""))
                        }
                    else:
                        # v é string/valor simples; armazenar em 'value'
                        rec = {"planet": k, "value": str(v)}
                    records.append(rec)
                chart_positions = records
            else:
                # formato inesperado: serializar para fallback
                chart_positions = [{"planet": "unknown", "value": str(raw_positions)}]
        except Exception as e:
            logger.exception("Erro ao calcular chart_positions: %s", e)
            chart_positions = None

    return {
        "place": (display or place),
        "bdate": bdate,
        "btime": str(btime).strip(),
        "lat": lat,
        "lon": lon,
        "timezone": timezone,
        "chart_positions": chart_positions,
        "birth_time_estimated": False,  # nunca estimamos
    }

# -------------------------
# Função principal: gerar texto via GenAI
# -------------------------
def generate_ai_text_from_chart(
    chart_summary: Dict[str, Any],
    model: Optional[str] = None,
    prompt_template: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Gera texto interpretativo via Gemini/GenAI.
    Aceita:
      - chart_summary já estruturado (com chart_positions), ou
      - dict bruto retornado por natal_positions (contendo 'planets'), ou
      - dict com keys 'place' e 'bdate' e 'btime' (inputs do usuário) para preparar o summary.
    Retorna dict com keys: raw_text, error, prompt, chart_summary.
    """
    result: Dict[str, Any] = {"raw_text": None, "error": None, "prompt": None, "chart_summary": None}

    target_model = model or os.getenv("GEMINI_MODEL") or os.getenv("GENAI_MODEL") or GEMINI_MODEL
    if not target_model:
        err = "Nenhum modelo configurado (GEMINI_MODEL/GENAI_MODEL)."
        logger.error(err)
        return {"raw_text": "", "error": err, "prompt": None, "chart_summary": None}

    # Inicializa cliente cedo
    try:
        _ = _init_genai_client()
    except Exception as e:
        logger.exception("Falha ao inicializar genai.Client")
        return {"raw_text": "", "error": f"Falha ao inicializar genai.Client: {e}", "prompt": None, "chart_summary": None}

    kwargs.pop("model", None)

    # Detecta formatos de entrada e normaliza para chart_summary_struct
    try:
        if isinstance(chart_summary, dict) and isinstance(chart_summary.get("planets"), dict):
            # raw natal_positions -> usar builder do projeto se disponível
            try:
                chart_summary_struct = build_chart_summary_from_natal(chart_summary)
            except Exception:
                logger.warning("Fallback: usando 'planets' como chart_positions.")
                chart_summary_struct = {"chart_positions": chart_summary.get("planets")}
            # garantir campos mínimos (se vierem no input)
            chart_summary_struct.setdefault("place", chart_summary.get("place", ""))
            chart_summary_struct.setdefault("bdate", chart_summary.get("bdate"))
            chart_summary_struct.setdefault("btime", chart_summary.get("btime", ""))

        elif isinstance(chart_summary, dict) and chart_summary.get("place") and chart_summary.get("bdate"):
            # inputs simples do usuário — exigir btime válido
            chart_summary_struct = prepare_chart_summary_from_inputs(
                place=chart_summary.get("place"),
                bdate=chart_summary.get("bdate"),
                btime=chart_summary.get("btime", ""),
                house_system=chart_summary.get("house_system", "Placidus"),
            )
            if not chart_summary_struct.get("btime"):
                err = "Hora de nascimento não informada. A interpretação exige hora precisa."
                logger.error(err)
                return {"raw_text": "", "error": err, "prompt": None, "chart_summary": chart_summary_struct}
        else:
            chart_summary_struct = chart_summary
    except Exception as e:
        logger.exception("Erro ao normalizar chart_summary")
        return {"raw_text": "", "error": f"Erro ao normalizar chart_summary: {e}", "prompt": None, "chart_summary": None}

    result["chart_summary"] = chart_summary_struct

    # Cache
    try:
        cache_key = _make_cache_key(target_model, chart_summary_struct)
        cached = _cache_get(cache_key)
        if cached:
            logger.debug("Cache hit para %s", cache_key)
            return cached
    except Exception:
        logger.exception("Erro ao acessar cache (continuando sem cache)")

    # Template padrão
    if not prompt_template:
        prompt_template = DEFAULT_PROMPT

    # Monta prompt
    try:
        prompt = build_prompt_from_chart_summary(chart_summary_struct, prompt_template=prompt_template)
        result["prompt"] = prompt
        logger.debug("Prompt (head): %s", (prompt or "")[:500])
        if not chart_summary_struct.get("chart_positions"):
            logger.warning(
                "Sem chart_positions. place=%r lat=%r lon=%r tz=%r btime=%r",
                chart_summary_struct.get("place"),
                chart_summary_struct.get("lat"),
                chart_summary_struct.get("lon"),
                chart_summary_struct.get("timezone"),
                chart_summary_struct.get("btime"),
            )
    except Exception as e:
        logger.exception("Erro ao montar prompt")
        return {"raw_text": "", "error": f"Erro ao montar prompt: {e}", "prompt": None, "chart_summary": chart_summary_struct}

    # Chama SDK
    try:
        raw = _call_gemini_sdk(prompt, model=target_model, **kwargs)
        result["raw_text"] = raw
    except Exception as e:
        logger.exception("Erro ao chamar _call_gemini_sdk")
        result["error"] = str(e)

    # Salva cache (se sucesso)
    try:
        if result.get("raw_text"):
            _cache_set(cache_key, result)
    except Exception:
        logger.exception("Erro ao gravar cache (ignorando)")

    return result

# -------------------------
# Função de alto nível: gerar SVG + texto (usa API externa quando disponível)
# -------------------------
def generate_analysis(chart_input: Dict[str, Any], prefer: str = "auto", text_only: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Gera SVG do mapa e/ou texto de análise.
    chart_input pode conter:
      - summary (chart_summary já preparado),
      - ou place/bdate/btime para preparar internamente,
      - ou dt/lat/lon/tz para chamadas à API externa.
    Retorna dict com keys: svg, analysis_text, analysis_json, source, error
    """
    result: Dict[str, Any] = {"svg": "", "analysis_text": "", "analysis_json": None, "source": "none", "error": None}

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

    # Fluxo text_only
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
                result.update({"analysis_text": analysis_text, "analysis_json": api_resp.get("analysis_json"), "source": "api"})
                result["svg"] = chart_input.get("svg", "")
                return result
            except Exception as e:
                api_error = str(e)

        # Fallback local AI
        try:
            summary = chart_input.get("summary")
            if not summary and chart_input.get("place") and chart_input.get("bdate"):
                # exigir hora
                if not chart_input.get("btime"):
                    result["error"] = (result.get("error") or "") + "; Hora de nascimento não informada."
                    result["analysis_text"] = ""
                    result["analysis_json"] = None
                    result["source"] = "local_ai"
                    return result
                summary = prepare_chart_summary_from_inputs(chart_input.get("place"), chart_input.get("bdate"), chart_input.get("btime", ""))
            if summary:
                model = kwargs.get("model") or kwargs.get("model_choice")
                _extra = {k: v for k, v in kwargs.items() if k != "model"}
                ai_res = generate_ai_text_from_chart(summary, model=model, **_extra)
                if ai_res.get("error"):
                    combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                    result["error"] = combined_err or result.get("error")
                else:
                    result["analysis_text"] = ai_res.get("raw_text") or ""
                    result["analysis_json"] = ai_res.get("parsed_json") or None
                    result["source"] = "local_ai"
            else:
                result["analysis_text"] = ""
                result["analysis_json"] = None
        except Exception as e:
            result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"

        result["svg"] = chart_input.get("svg", "")
        return result

    # Fluxo padrão (SVG + texto)
    if use_api:
        try:
            name = chart_input.get("name", "")
            dt = chart_input.get("dt")
            lat = chart_input.get("lat", 0.0)
            lon = chart_input.get("lon", 0.0)
            tz = chart_input.get("tz", "")
            api_resp = api_client.fetch_natal_chart_api(name, dt if isinstance(dt, datetime) else dt, lat, lon, tz)
            svg = chart_renderer.from_api_response_to_svg(api_resp)
            analysis_text = api_resp.get("analysis_text") or api_resp.get("interpretation") or ""
            result.update({"svg": svg, "analysis_text": analysis_text, "source": "api"})
            return result
        except Exception as e:
            api_error = str(e)

    # Fallback SVG local
    try:
        svg = chart_renderer.render_local_chart(chart_input)
        result["svg"] = svg
        result["source"] = "local"
    except Exception as e:
        result["error"] = f"Erro ao renderizar localmente: {e}"
        return result

    # Fallback AI local para texto
    try:
        summary = chart_input.get("summary")
        if not summary and chart_input.get("place") and chart_input.get("bdate"):
            # exigir hora
            if not chart_input.get("btime"):
                result["error"] = (result.get("error") or "") + "; Hora de nascimento não informada."
                result["analysis_text"] = ""
                result["analysis_json"] = None
                return result
            summary = prepare_chart_summary_from_inputs(chart_input.get("place"), chart_input.get("bdate"), chart_input.get("btime", ""))
        if summary:
            model = kwargs.get("model") or kwargs.get("model_choice")
            _extra = {k: v for k, v in kwargs.items() if k != "model"}
            ai_res = generate_ai_text_from_chart(summary, model=model, **_extra)
            if ai_res.get("error"):
                combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                result["error"] = combined_err or result.get("error")
            else:
                result["analysis_text"] = ai_res.get("raw_text") or ""
                result["analysis_json"] = ai_res.get("parsed_json") or None
        else:
            result["analysis_text"] = ""
            result["analysis_json"] = None
    except Exception as e:
        result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"

    return result