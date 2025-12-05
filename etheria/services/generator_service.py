# services/generator_service.py
"""
Função de alto nível generate_analysis(chart_data, prefer="api|local") que:
- tenta API Gemini/Google GenAI se configurada;
- em caso de falha usa renderer local ou templates;
- aplica caching simples e rate limiting.
"""

import os
import json
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from services.swisseph_client import natal_positions
from services.chart_builder import build_chart_summary_from_natal, build_prompt_from_chart_summary

# Tenta importar as dependências internas (ajuste os caminhos se necessário no seu projeto)
from . import api_client
from . import chart_renderer

# Configurações de cache e rate limit
_CACHE_TTL_SECONDS = int(os.getenv("GENERATOR_CACHE_TTL", "300"))  # 5 minutos por padrão
_RATE_LIMIT_MIN_INTERVAL = float(os.getenv("GENERATOR_RATE_MIN_INTERVAL", "0.5"))  # segundos entre chamadas externas

# --- ATUALIZAÇÃO: Definição de modelo padrão seguro ---
# Modelos válidos recomendados: "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.5-pro-002"
# Evite "gemini-2.5" ou versões inexistentes.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Estado para cache e rate limiting
_cache_lock = threading.Lock()
_cache: Dict[str, Dict[str, Any]] = {}  # key -> {"ts": float, "value": Any}
_rate_lock = threading.Lock()
_last_call_ts = 0.0


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


def _init_genai_client():
    """
    Inicializa genai.Client de forma explícita e defensiva.
    Usa GENAI_API_KEY (modo API) ou GENAI_VERTEXAI + GOOGLE_CLOUD_PROJECT + GOOGLE_CLOUD_LOCATION (modo Vertex).
    """
    # importar genai (tentar google.genai como fallback)
    try:
        import genai
    except Exception:
        try:
            from google import genai  # type: ignore
        except Exception:
            raise RuntimeError("Biblioteca 'genai' não encontrada. Instale 'genai' ou 'google-genai'.")

    api_key = os.getenv("GENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    use_vertex = str(os.getenv("GENAI_VERTEXAI", "")).lower() in ("1", "true", "yes")
    
    project = os.getenv("GOOGLE_CLOUD_PROJECT")
    
    # --- ATUALIZAÇÃO: Fallback seguro para região ---
    # Se não houver região definida, usa us-central1 para garantir acesso aos modelos mais novos
    location = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("GOOGLE_CLOUD_REGION") or "us-central1"
    
    cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    # modo API key
    if api_key:
        try:
            try:
                genai.configure(api_key=api_key)
            except Exception:
                pass
            return genai.Client(api_key=api_key)
        except Exception as e:
            raise RuntimeError("Falha ao inicializar genai.Client com API key: " + str(e)) from e

    # modo Vertex
    if use_vertex:
        if not project:
            raise RuntimeError(
                "Para usar Vertex AI defina GENAI_VERTEXAI=1 e a variável GOOGLE_CLOUD_PROJECT."
            )
        # checar arquivo de credenciais
        if not cred_path or not os.path.exists(cred_path) or not os.access(cred_path, os.R_OK):
            # Aviso logável poderia ser inserido aqui, mas vamos lançar erro para segurança
            raise RuntimeError(f"GOOGLE_APPLICATION_CREDENTIALS inválido ou inacessível: {cred_path}")
        try:
            # passar explicitamente vertexai, project e location
            return genai.Client(vertexai=True, project=project, location=location)
        except Exception as e:
            raise RuntimeError("Falha ao inicializar genai.Client para Vertex AI: " + str(e)) from e

    # nenhum modo configurado
    raise RuntimeError(
        "Missing key inputs argument! Defina GENAI_API_KEY (modo API) ou GENAI_VERTEXAI=1 com GOOGLE_CLOUD_PROJECT (modo Vertex)."
    )


def _extract_text_from_response(resp) -> str:
    """
    Extrai texto de diferentes formatos de resposta do SDK.
    """
    if resp is None:
        return ""
    # Atributo text (comum)
    if hasattr(resp, "text"):
        try:
            return resp.text
        except Exception:
            pass
    # Estruturas com output / content
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
    # candidates / alternatives
    try:
        if hasattr(resp, "candidates"):
            cand = getattr(resp, "candidates")
            if isinstance(cand, (list, tuple)) and len(cand) > 0:
                first = cand[0]
                if hasattr(first, "content"):
                    return str(first.content)
    except Exception:
        pass
    # Fallback
    try:
        return str(resp)
    except Exception:
        return ""


def _call_gemini_sdk(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = 2000) -> str:
    """
    Chama o SDK google-genai de forma compatível com várias versões.
    Aplica rate limiting e retorna o texto gerado.
    """
    # Rate limit local
    _rate_limit_wait()

    client = _init_genai_client()
    last_exc = None

    # Função auxiliar para tratar erros conhecidos (como 404 Model Not Found)
    def _handle_api_error(e, model_name):
        err_str = str(e)
        if "404" in err_str and ("Publisher Model" in err_str or "NOT_FOUND" in err_str):
            raise ValueError(
                f"Erro Crítico: O modelo '{model_name}' não foi encontrado. "
                f"Verifique se o nome está correto (ex: use 'gemini-1.5-flash' ou 'gemini-1.5-pro') "
                f"e se a região (location) suporta este modelo. Detalhes: {err_str}"
            )
        return e

    # Tentativa 1: client.models.generate_content
    try:
        if hasattr(client, "models") and hasattr(client.models, "generate_content"):
            # Ajuste de payload para diferentes versões da lib
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

    # Tentativa 2: client.responses.create (deprecated em algumas versões)
    if not isinstance(last_exc, ValueError): # Só tenta se não foi erro fatal de modelo 404
        try:
            if hasattr(client, "responses") and hasattr(client.responses, "create"):
                try:
                    resp = client.responses.create(model=model, input=prompt)
                except TypeError:
                    resp = client.responses.create(model=model, prompt=prompt)
                return _extract_text_from_response(resp)
        except Exception as e:
            last_exc = _handle_api_error(e, model)

    # Tentativa 3: client.generate (versões antigas)
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


def generate_ai_text_from_chart(chart_summary: Dict[str, Any],
                                model: Optional[str] = None,
                                prompt_template: Optional[str] = None,
                                **kwargs) -> Dict[str, Any]:
    """
    Gera texto interpretativo via Gemini/GenAI.
    Retorna dict com keys: raw_text, error.

    Aceita como `chart_summary`:
      - um resumo já estruturado (lista de planetas, cusps, ascendant), ou
      - o dicionário bruto retornado por natal_positions(...) (detectado automaticamente).
    """
    # Força modelo alvo (env var ou constante)
    target_model = model or os.getenv("GEMINI_MODEL") or GEMINI_MODEL

    # Inicialização antecipada para falhar rápido se credenciais estiverem erradas
    try:
        _ = _init_genai_client()
    except Exception as e:
        logger.exception("Falha ao inicializar genai.Client")
        return {"raw_text": "", "error": f"Falha ao inicializar genai.Client: {e}"}

    # Remover model duplicado em kwargs, se houver
    kwargs.pop("model", None)

    # Detecta se chart_summary é o retorno bruto de natal_positions (planets como dict)
    try:
        is_natal_raw = isinstance(chart_summary, dict) and isinstance(chart_summary.get("planets"), dict)
    except Exception:
        is_natal_raw = False

    # Se for natal raw, converte para chart_summary estruturado
    if is_natal_raw:
        try:
            chart_summary_struct = build_chart_summary_from_natal(chart_summary)
        except Exception as e:
            logger.exception("Erro ao construir chart_summary a partir de natal_positions")
            return {"raw_text": "", "error": f"Erro ao construir resumo do mapa: {e}"}
    else:
        chart_summary_struct = chart_summary

    # Cache key simplificado (usar repr para evitar json.dumps grandes)
    cache_key = f"ai_text:{target_model}:" + repr(chart_summary_struct)
    try:
        cached = _cache_get(cache_key)
        if cached:
            logger.debug("Cache hit para %s", cache_key)
            return cached
    except Exception:
        logger.exception("Erro ao acessar cache (continuando sem cache)")

    result = {"raw_text": None, "error": None}

    # Se não houver template, usa o padrão atualizado (sem JSON)
    if not prompt_template:
        prompt_template = (
            "1) Me explique com analogia ao teatro, o que é o planeta, o signo e a casa na astrologia (máx. 8 linhas) de forma clara.\n\n"
            "2) Interprete o posicionamento da primeira tríade de planetas pessoais, com o detalhe de cada casa: ASC, Sol e Lua (máx.8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
            "3) Interprete o posicionamento da segunda tríade de planetas pessoais, com o detalhe de cada casa: Marte, Mercúrio e Vênus (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
            "4) Interprete o posicionamento da tríade de planetas sociais, com o detalhe de cada casa: Júpiter e Saturno (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
            "5) Interprete o posicionamento da tríade de planetas geracionais, com o detalhe de cada casa: Urano, Netuno e Plutão (máx. 8-10 linhas por planeta), fornecendo aplicações práticas.\n\n"
            "6) Para encerrar esta análise, foque nos quatro elementos (Terra, Água, Fogo, Ar) e indique qual energia domina o temperamento; explique brevemente como isso se manifesta (máx. 6 linhas), fornecendo aplicações práticas.\n\n"
            "7) Informação adicional sobre astrologia cármica: comente sobre Sol, Lua, Nodo Sul, Nodo Norte e Roda da Fortuna e Planetas Retrógrados (máx. 6 linhas), fornecendo aplicações práticas.\n\n"
            "Por favor, responda apenas com o texto interpretativo numerado conforme as seções acima."
        )

    # Monta prompt usando o builder (inclui ASC e cúspides quando disponíveis)
    try:
        prompt = build_prompt_from_chart_summary(chart_summary_struct, prompt_template=prompt_template)
    except Exception as e:
        logger.exception("Erro ao montar prompt a partir do chart_summary")
        return {"raw_text": "", "error": f"Erro ao montar prompt: {e}"}

    # Chama o SDK/serviço de IA
    try:
        raw = _call_gemini_sdk(prompt, model=target_model, **kwargs)
        result["raw_text"] = raw
    except Exception as e:
        logger.exception("Erro ao chamar _call_gemini_sdk")
        result["error"] = str(e)

    # Tenta salvar no cache (não falhar se cache der erro)
    try:
        _cache_set(cache_key, result)
    except Exception:
        logger.exception("Erro ao gravar cache (ignorando)")

    return result

def generate_analysis(chart_input: Dict[str, Any], prefer: str = "auto", text_only: bool = False, **kwargs) -> Dict[str, Any]:
    """
    Gera SVG do mapa e/ou texto de análise.
    Retorna dict com keys: svg, analysis_text, analysis_json, source, error
    """
    result: Dict[str, Any] = {
        "svg": "",
        "analysis_text": "",
        "analysis_json": None,
        "source": "none",
        "error": None
    }

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

    # --- Fluxo text_only ---
    if text_only:
        if use_api:
            try:
                name = chart_input.get("name", "")
                dt = chart_input.get("dt")
                lat = chart_input.get("lat", 0.0)
                lon = chart_input.get("lon", 0.0)
                tz = chart_input.get("tz", "")
                
                # Assume que api_client é robusto
                api_resp = api_client.fetch_natal_chart_api(name, dt if isinstance(dt, datetime) else dt, lat, lon, tz)
                
                analysis_text = api_resp.get("analysis_text") or api_resp.get("interpretation") or ""
                result.update({"analysis_text": analysis_text, "analysis_json": api_resp.get("analysis_json"), "source": "api"})
                result["svg"] = chart_input.get("svg", "")
                return result
            except Exception as e:
                api_error = str(e)

        # Fallback Local AI
        try:
            if chart_input.get("summary"):
                model = kwargs.get("model") or kwargs.get("model_choice")
                _extra = {k: v for k, v in kwargs.items() if k != "model"}
                
                ai_res = generate_ai_text_from_chart(chart_input.get("summary"), model=model, **_extra)
                
                if ai_res.get("error"):
                    result["analysis_text"] = ""
                    result["analysis_json"] = None
                    combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                    result["error"] = combined_err or result.get("error")
                else:
                    result["analysis_text"] = ai_res.get("raw_text") or ai_res.get("text") or ""
                    result["analysis_json"] = ai_res.get("parsed_json") or ai_res.get("json") or None
                    result["source"] = "local_ai"
            else:
                result["analysis_text"] = ""
                result["analysis_json"] = None
        except Exception as e:
            result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"

        result["svg"] = chart_input.get("svg", "")
        return result

    # --- Fluxo Padrão (SVG + Texto) ---
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

    # Fallback SVG Local
    try:
        svg = chart_renderer.render_local_chart(chart_input)
        result["svg"] = svg
        result["source"] = "local"
    except Exception as e:
        result["error"] = f"Erro ao renderizar localmente: {e}"
        return result

    # Fallback AI Local para texto
    try:
        if chart_input.get("summary"):
            model = kwargs.get("model") or kwargs.get("model_choice")
            _extra = {k: v for k, v in kwargs.items() if k != "model"}
            ai_res = generate_ai_text_from_chart(chart_input.get("summary"), model=model, **_extra)

            if ai_res.get("error"):
                result["analysis_text"] = ""
                result["analysis_json"] = None
                combined_err = (api_error or "") + ("; " if api_error else "") + ai_res.get("error", "")
                result["error"] = combined_err or result.get("error")
            else:
                result["analysis_text"] = ai_res.get("raw_text") or ai_res.get("text") or ""
                result["analysis_json"] = ai_res.get("parsed_json") or ai_res.get("json") or None
        else:
            result["analysis_text"] = ""
            result["analysis_json"] = None
    except Exception as e:
        result["error"] = (result.get("error") or "") + f"; AI generation error: {e}"

    return result