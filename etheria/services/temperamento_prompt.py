# services/temperamento_prompt.py

from typing import Optional, Callable, Dict, Any, Union, List
from datetime import datetime
import os
import json
import logging
import threading
import time
import hashlib
import random
from functools import wraps

# Integrações externas (SDK client)
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
# Retry / Circuit breaker
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
                raise
            attempt += 1
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            jitter = random.uniform(0, delay * 0.25)
            sleep_for = delay + jitter
            logger.warning("Erro transitório (tentativa %d/%d): %s. Retentando em %.2fs", attempt, max_attempts, e, sleep_for)
            time.sleep(sleep_for)
    logger.error("Esgotadas tentativas de retry; última exceção: %s", last_exc)
    raise last_exc

# -------------------------
# Helpers de logging
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
            logger.debug("Saindo %s retorno_type=%s", func.__name__, type(res).__name__)
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
# Função que chama o SDK (string prompt)
# -------------------------
@log_io
def _call_model_api(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = 2000) -> str:
    """
    Chama Google GenAI (genai.Client) e retorna string com o texto gerado.
    Tenta várias assinaturas conhecidas do SDK para máxima compatibilidade.
    """
    # rate limit defensivo
    try:
        _rate_limit_wait()
    except Exception:
        logger.debug("Rate limit wait falhou ou não implementado", exc_info=True)

    client = None
    try:
        client = _init_genai_client()
    except Exception as e:
        logger.exception("Falha ao inicializar genai client: %s", e)
        client = None

    prompt_text = str(prompt)
    logger.debug("PROMPT (preview): %s", prompt_text[:4000])

    last_exc = None

    # 1) genai.Client.models.generate_content (novas versões)
    try:
        if client and hasattr(client, "models") and hasattr(client.models, "generate_content"):
            try:
                resp = client.models.generate_content(model=model, contents=prompt_text)
            except TypeError:
                # algumas versões usam 'content' ou 'input'
                try:
                    resp = client.models.generate_content(model=model, content=prompt_text)
                except TypeError:
                    resp = client.models.generate_content(model=model, input=prompt_text)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e
        logger.debug("models.generate_content falhou: %s", e, exc_info=True)

    # 2) genai.Client.responses.create (outra assinatura comum)
    try:
        if client and hasattr(client, "responses") and hasattr(client.responses, "create"):
            try:
                resp = client.responses.create(model=model, input=prompt_text)
            except TypeError:
                # fallback para 'prompt'
                resp = client.responses.create(model=model, prompt=prompt_text)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e
        logger.debug("responses.create falhou: %s", e, exc_info=True)

    # 3) genai.Client.generate (algumas versões)
    try:
        if client and hasattr(client, "generate"):
            resp = client.generate(model=model, prompt=prompt_text, max_output_tokens=max_tokens)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e
        logger.debug("client.generate falhou: %s", e, exc_info=True)

    # 4) fallback: tentar chamada direta via client.predict (algumas libs custom)
    try:
        if client and hasattr(client, "predict"):
            resp = client.predict(model=model, prompt=prompt_text)
            return _extract_text_from_response(resp)
    except Exception as e:
        last_exc = e
        logger.debug("client.predict falhou: %s", e, exc_info=True)

    # se chegou aqui, nenhuma assinatura funcionou
    msg = "Não foi possível chamar o SDK genai com as assinaturas conhecidas."
    if last_exc:
        msg += f" Último erro: {last_exc}"
    logger.error(msg)
    raise RuntimeError(msg)

def _call_model_api_with_retry(prompt: str, model: str = GEMINI_MODEL, max_tokens: int = 2000) -> str:
    """
    Envolve _call_model_api com circuit breaker e retry. Retorna string.
    """
    if not _circuit_allows_call():
        raise RuntimeError("Circuit breaker aberto: serviço de IA temporariamente indisponível")

    cache_key = _make_cache_key(model, prompt)
    cached = _cache_get(cache_key)
    if cached:
        return cached

    def _call():
        return _call_model_api(prompt, model=model, max_tokens=max_tokens)

    try:
        raw = retry_with_backoff(_call, max_attempts=int(os.getenv("GENERATOR_RETRY_ATTEMPTS", "4")), base_delay=float(os.getenv("GENERATOR_RETRY_BASE_DELAY", "0.6")))
        _record_success()
        _cache_set(cache_key, raw)
        return raw
    except Exception as e:
        _record_failure()
        logger.exception("Chamada ao SDK falhou após retries: %s", e)
        raise

# -------------------------
# Prompt builder e normalização
# -------------------------
def build_prompt_from_result(result: Dict[str, Any]) -> str:
    ts = result.get("timestamp", datetime.utcnow().isoformat())
    scores = result.get("scores", {})
    dominant = result.get("dominant", "")
    dominant_score = result.get("dominant_score", "")
    secondary = result.get("secondary", None)
    secondary_score = result.get("secondary_score", None)

    dominant_rec = result.get("dominant_rec") or {}
    secondary_rec = result.get("secondary_rec") or {}

    parts = []
    parts.append("Introdução ao Perfil Bioenergético e Distribuição de Temperamentos")
    parts.append(f"Gerado em: {ts}")
    parts.append("")
    parts.append("Distribuição atingida no estudo (pontuações por temperamento):")
    for k, v in scores.items():
        parts.append(f"- {k.replace('_',' ')}: {v}")
    parts.append("")
    parts.append(f"Temperamento dominante identificado: {dominant} — {dominant_score}")
    if secondary:
        parts.append(f"Temperamento secundário identificado: {secondary} — {secondary_score}")
    parts.append("")

    def _append_rec_block(label, rec):
        if not rec:
            return
        parts.append(f"--- {label} ---")
        if rec.get("resumo"):
            parts.append(f"Resumo: {rec.get('resumo')}")
        if rec.get("pedras"):
            parts.append(f"Pedras sugeridas: {', '.join(rec.get('pedras'))}")
        if rec.get("cor"):
            parts.append(f"Cromoterapia (cor): {rec.get('cor')}")
        if rec.get("oleo"):
            parts.append(f"Aromaterapia (óleo): {rec.get('oleo')}")
        if rec.get("dicas"):
            parts.append("Dicas práticas:")
            for d in rec.get("dicas", []):
                parts.append(f"- {d}")
        if rec.get("alimentacao"):
            parts.append("Alimentação (detalhe):")
            parts.append(rec.get("alimentacao"))
        parts.append("")

    _append_rec_block("Dominant", dominant_rec)
    _append_rec_block("Secondary", secondary_rec)

    # Instrução principal aprimorada (em português)
    instruction = (
        "INSTRUÇÃO PRINCIPAL:\n"
        "Comservando fielmente o texto-fonte acima, gere um relatório privado em estilo clínico chamado:\n"
        "'Introdução ao Perfil Bioenergético e Distribuição de Temperamentos'.\n\n"
        "Inclua, logo no início, um disclaimer claro em português: "
        "'Isto não é um diagnóstico médico. Consulte um profissional de saúde qualificado antes de implementar mudanças clínicas.'\n\n"
        "O relatório deve conter as seguintes seções, na ordem e com o nível de detalhe solicitado:\n\n"
        "A) Sumário executivo (1 parágrafo): síntese da distribuição obtida no estudo e implicações gerais.\n\n"
        "B) Detalhe da distribuição atingida: descreva a porcentagem/ponderação relativa dos temperamentos com base nas pontuações fornecidas, interpretando o que significa ter o temperamento X em Y% do perfil; destaque se há perfil misto e o grau de proximidade entre dominante e secundário.\n\n"
        "C) Análise profunda do temperamento dominante:\n"
        "   - Características centrais (2–4 parágrafos): comportamento, energia, padrões alimentares e de sono, reatividade emocional e pontos fortes/fragilidades.\n"
        "   - Interpretação funcional: como essas características impactam rotina, trabalho e relações.\n\n"
        "D) Prescrição dietética integrada e plano alimentar (detalhado):\n"
        "   1) Princípios gerais da dieta para este temperamento (objetivos metabólicos e bioenergéticos).\n"
        "   2) Lista de alimentos a favorecer e alimentos a evitar, com justificativa breve para cada grupo.\n"
        "   3) Bloco de refeições sugeridas (exemplo de 3 refeições + 2 lanches para um dia típico):\n"
        "      - Café da manhã: itens e porções exemplares.\n"
        "      - Almoço: itens, composição de prato (proteína, carboidrato, vegetais, gorduras saudáveis).\n"
        "      - Lanche da tarde: opções práticas.\n"
        "      - Jantar: recomendações de leveza e composição.\n"
        "      - Ceia/opcional: quando indicada e o que evitar.\n"
        "   4) Plano alimentar semanal (esboço de 7 dias com variações e substituições simples).\n\n"
        "E) Recomendações de exercício (tipo, frequência, intensidade) com exemplos práticos e adaptações para níveis iniciantes/intermediários.\n\n"
        "F) Suplementação (se aplicável): sugestões de suplementos com justificativa, faixas de dosagem comumente aceitas e advertências explícitas para consultar um clínico antes de iniciar.\n\n"
        "G) Terapias complementares integradas:\n"
        "   - Cromoterapia: cores recomendadas e como aplicá-las (ambiente, roupas, luzes) com justificativa energética.\n"
        "   - Aromaterapia: óleos essenciais sugeridos, modo de uso (difusor, inalação breve, diluição tópica) e precauções.\n"
        "   - Cristaloterapia: pedras sugeridas, modo de uso prático (uso diário, meditação, colocação no ambiente) e intenções associadas.\n\n"
        "H) Plano de Implementação (30 dias) — 'Plano de Ação Prático': 8–12 passos organizados por semanas, com metas mensuráveis e checkpoints semanais; inclua sugestões de monitoramento (sono, humor, energia, apetite) e quando reavaliar.\n\n"
        "I) Considerações diagnósticas finais e sinais de alerta: liste sinais que justificariam busca imediata por avaliação clínica (ex.: perda de peso rápida, fadiga extrema, sintomas gastrointestinais persistentes), mantendo linguagem não-alarmista.\n\n"
        "Formato e tom: profissional, empático e não-alarmista. Use títulos claros, subtítulos e listas com marcadores para Diet/Exercise/Supplementation/Plano. Preserve frases-chave do material fonte quando relevantes.\n\n"
        "Restrições: NÃO emita diagnósticos médicos formais nem prescreva medicamentos. Sempre inclua a recomendação de consultar um profissional de saúde para decisões clínicas.\n\n"
        "Saída: retorne o relatório em texto plano em português, pronto para exibição direta na UI e para inclusão em PDF. Comece o documento com o título exato: 'Introdução ao Perfil Bioenergético e Distribuição de Temperamentos'."
    )

    prompt = "\n".join(parts) + "\n\n" + instruction
    return prompt

# -------------------------
# Função pública text-only
# -------------------------
def generate_text_only(prompt: str, max_tokens: int = 1200, temperature: float = 0.7) -> Dict[str, Any]:
    """
    Chama o modelo diretamente com um prompt string e retorna dict com 'text' e 'raw'.
    Use esta função quando quiser evitar qualquer pré-processamento.
    """
    if not isinstance(prompt, str) or not prompt.strip():
        return {"error": "prompt vazio", "text": None, "raw": None}
    try:
        raw_text = _call_model_api_with_retry(prompt, model=GEMINI_MODEL, max_tokens=max_tokens)
        return {"text": raw_text, "raw": raw_text}
    except Exception as e:
        logger.exception("generate_text_only falhou")
        return {"error": str(e), "text": None, "raw": None}

# -------------------------
# Função principal: gera relatório (usa text-only por padrão)
# -------------------------
def generate_diagnostic_report(
    result: Dict[str, Any],
    generator: Optional[Callable[[str], Any]] = None,
    prompt_override: Optional[str] = None,
    max_tokens: int = 1200,
    temperature: float = 0.7,
) -> Dict[str, Any]:
    """
    Gera o relatório diagnóstico chamando o modelo diretamente com prompt string.
    - Por padrão usa generate_text_only (que chama o SDK diretamente).
    - Se 'generator' for fornecido, ele deve aceitar um prompt string e retornar raw result.
    Retorna: { 'prompt': str, 'model_text': str|None, 'raw_model_result': Any }
    """
    prompt = prompt_override or build_prompt_from_result(result)

    # prefer generator fornecido (útil para testes/mocks)
    if generator is not None:
        try:
            raw = generator(prompt)
        except Exception as e:
            logger.exception("generator fornecido falhou")
            raw = {"error": str(e)}
        # normalizar
        if isinstance(raw, dict):
            text = raw.get("text") or raw.get("analysis_text") or raw.get("raw_text") or raw.get("output")
        elif isinstance(raw, str):
            text = raw
        else:
            text = str(raw)
        return {"prompt": prompt, "model_text": text, "raw_model_result": raw}

    # caminho padrão: chamar generate_text_only
    raw = generate_text_only(prompt, max_tokens=max_tokens, temperature=temperature)
    model_text = raw.get("text") if isinstance(raw, dict) else (raw if isinstance(raw, str) else None)

    # se o modelo pedir hora de nascimento, tentar uma re-chamada com instrução reforçada
    if isinstance(model_text, str) and "hora" in model_text.lower() and "nascimento" in model_text.lower():
        prompt2 = prompt + "\n\nINSTRUÇÃO ADICIONAL: Ignore solicitações de hora de nascimento e gere o relatório com os dados disponíveis."
        raw2 = generate_text_only(prompt2, max_tokens=max_tokens, temperature=temperature)
        model_text2 = raw2.get("text") if isinstance(raw2, dict) else None
        if model_text2 and "hora" not in model_text2.lower():
            return {"prompt": prompt2, "model_text": model_text2, "raw_model_result": raw2}

    return {"prompt": prompt, "model_text": model_text, "raw_model_result": raw}