# services/generator_service.py
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
from typing import Dict, Any, Optional
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
    """
    Inicializa genai.Client (API key ou Vertex). Lança RuntimeError em falha.
    """
    try:
        import genai
    except Exception:
        try:
            from google import genai  # type: ignore
        except Exception:
            raise RuntimeError("Biblioteca 'genai' não encontrada. Instale 'genai' ou 'google-genai'.")

    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

    # Unificar fallback de região
    location = (
        os.getenv("GOOGLE_CLOUD_LOCATION")
        or os.getenv("GOOGLE_CLOUD_REGION")
        or os.getenv("GENAI_LOCATION")
        or "us-central1"
    )

    use_vertex = str(os.getenv("GENAI_VERTEXAI", "")).lower() in ("1", "true", "yes")
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # API key mode
    if api_key:
        try:
            try:
                genai.configure(api_key=api_key)
            except Exception:
                pass
            logger.info("Inicializando genai.Client com API key.")
            return genai.Client(api_key=api_key)
        except Exception as e:
            raise RuntimeError("Falha ao inicializar genai.Client com API key: " + str(e)) from e

    # Vertex mode
    if use_vertex:
        if not project:
            raise RuntimeError("Para usar Vertex AI defina GENAI_VERTEXAI=1 e GOOGLE_CLOUD_PROJECT.")
        if not cred_path or not os.path.exists(cred_path) or not os.access(cred_path, os.R_OK):
            raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS inválido ou inacessível: {cred_path}")
        try:
            logger.info("Inicializando genai.Client para Vertex AI: project=%s, location=%s", project, location)
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


def _call_gemini_sdk(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = 2000) -> str:
    """
    Chama o SDK google-genai de forma compatível com várias versões.
    Aplica rate limiting e retorna o texto gerado.
    """
    _rate_limit_wait()
    client = _init_genai_client()
    last_exc = None

    def _handle_api_error(e, model_name):
        err_str = str(e)
        if "404" in err_str and ("Publisher Model" in err_str or "NOT_FOUND" in err_str):
            raise ValueError(
                f"Erro Crítico: O modelo '{model_name}' não foi encontrado. Verifique nome e região. Detalhes: {err_str}"
            )
        return e

    # Tentativa 1: client.models.generate_content
    try:
        if hasattr(client, "models") and hasattr(client.models, "generate_content"):
            try:
                resp = client.models.generate_content(model=model, contents=prompt)
            except TypeError:
                try:
                    resp = client.models.generate_content(model=model, content=prompt)
                except TypeError:
                    resp = client.models.generate_content(model=model, input=prompt)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = _handle_api_error(e, model)

    # Tentativa 2: client.responses.create
    if not isinstance(last_exc, ValueError):
        try:
            if hasattr(client, "responses") and hasattr(client.responses, "create"):
                try:
                    resp = client.responses.create(model=model, input=prompt)
                except TypeError:
                    resp = client.responses.create(model=model, prompt=prompt)
                return _extract_text_from_response(resp)
        except Exception as e:
            last_exc = _handle_api_error(e, model)

    # Tentativa 3: client.generate (antigo)
    if not isinstance(last_exc, ValueError):
        try:
            if hasattr(client, "generate"):
                resp = client.generate(model=model, prompt=prompt, max_output_tokens=max_tokens)
                return _extract_text_from_response(resp)
        except Exception as e:
            last_exc = _handle_api_error(e, model)

    msg = "Não foi possível chamar o SDK google-genai com as assinaturas conhecidas."
    if last_exc:
        msg += f" Último erro: {last_exc}"
    raise RuntimeError(msg)


# -------------------------
# Prompt template e builder
# -------------------------
DEFAULT_PROMPT = (
    "1) Me explique com analogia ao teatro, o que é o planeta, o signo e a casa na astrologia (máx. 8 linhas) de forma clara.\n\n"
    "2) Interprete o posicionamento da primeira tríade de planetas pessoais, com o detalhe de cada casa: ASC, Sol e Lua (máx.8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "3) Interprete o posicionamento da segunda tríade de planetas pessoais, com o detalhe de cada casa: Marte, Mercúrio e Vênus (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "4) Interprete o posicionamento da tríade de planetas sociais, com o detalhe de cada casa: Júpiter e Saturno (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "5) Interprete o posicionamento da tríade de planetas geracionais, com o detalhe de cada casa: Urano, Netuno e Plutão (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
    "6) Para encerrar esta análise, foque nos quatro elementos (Terra, Água, Fogo, Ar) e indique qual energia domina o temperamento; explique brevemente como isso se manifesta (máx. 6 linhas), fornecendo aplicações práticas.\n\n"
    "7) Informação adicional sobre astrologia cármica: comente sobre Sol, Lua, Nodo Sul, Nodo Norte e Roda da Fortuna e Planetas Retrógrados (máx. 6 linhas), fornecendo aplicações práticas.\n\n"
    "Por favor, responda apenas com o texto interpretativo numerado conforme as seções acima."
)


def build_prompt_from_chart_summary(
    chart_summary: Dict[str, Any],
    prompt_template: Optional[str] = None,
) -> str:
    """
    Recebe um chart_summary estruturado (ou parcial) e monta o prompt final.
    Espera keys: place, bdate (date), btime (str), lat, lon, timezone, chart_positions (dict).
    Nunca assume hora padrão: se faltou hora, deixa explícito no contexto.
    """
    if not prompt_template:
        prompt_template = DEFAULT_PROMPT

    place = chart_summary.get("place", "")
    bdate = chart_summary.get("bdate")
    btime = chart_summary.get("btime", "") or ""
    lat = chart_summary.get("lat")
    lon = chart_summary.get("lon")
    timezone = chart_summary.get("timezone")
    chart_positions = chart_summary.get("chart_positions")
    birth_time_estimated = chart_summary.get("birth_time_estimated", False)

    date_text = bdate.strftime("%d/%m/%Y") if isinstance(bdate, date) else str(bdate or "")
    time_text = btime.strip() if btime and btime.strip() else "Hora de nascimento não informada"

    context = (
        f"Cidade de nascimento: {place}\n"
        f"Data de nascimento: {date_text}\n"
        f"Hora de nascimento (local): {time_text}\n"
    )
    if birth_time_estimated:
        # Por política do projeto, não estimamos hora — mas se essa flag vier de entradas cruas, alertar
        context += "Observação: a hora informada é inválida/indisponível; interpretação das casas/ASC pode ficar comprometida.\n"
    if lat is not None and lon is not None:
        context += f"Coordenadas: {lat:.6f}, {lon:.6f}\n"
    if timezone:
        context += f"Timezone: {timezone}\n"

    if chart_positions:
        positions_text = "\nPosições calculadas:\n"
        for k, v in chart_positions.items():
            positions_text += f"- {k}: {v}\n"
        positions_text += "\n"
    else:
        positions_text = "\nPosições calculadas: indisponíveis (verifique cidade/hora/timezone). Sem hora precisa, não há casas/ASC.\n\n"

    return context + positions_text + prompt_template


# -------------------------
# Preparação do chart a partir de inputs simples
# -------------------------
def prepare_chart_summary_from_inputs(
    place: str,
    bdate: date,
    btime: Optional[str],
    house_system: str = "Placidus",
) -> Dict[str, Any]:
    """
    Faz geocode, timezone, parse de hora e cálculo de posições.
    Retorna dict com keys: place, bdate, btime, lat, lon, timezone, chart_positions.
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
            chart_positions = compute_chart_positions(lat, lon, local_dt, house_system)
        except Exception as e:
            logger.exception("Erro ao calcular chart_positions: %s", e)

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