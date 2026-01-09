# services/analysis.py
from typing import Dict, Any, Optional, Tuple
from datetime import date
from etheria import astrology

import logging
logger = logging.getLogger(__name__)

# Tentar importar generate_interpretation do pacote etheria, depois relativo
try:
    from etheria.interpretations import generate_interpretation
except Exception as e_pkg:
    try:
        # caso services esteja dentro do pacote etheria e import relativo funcione
        from .interpretations import generate_interpretation  # type: ignore
    except Exception as e_rel:
        logger.exception(
            "Falha ao importar 'generate_interpretation'. "
            "Tentativas: etheria.interpretations error=%s ; relative error=%s",
            e_pkg, e_rel
        )
        raise ImportError(
            "Não foi possível importar 'generate_interpretation'. "
            "Verifique que 'etheria/interpretations.py' existe e que 'etheria' é um pacote (contém __init__.py). "
            "Se preferir, mova interpretations.py para o diretório do projeto raiz ou para services/ e ajuste o import."
        ) from e_rel
# -------------------------
# Mapeamento Planeta -> Arcano (baseado na sua tabela)
# Chaves aceitam nomes em inglês e português
# -------------------------
PLANET_ARCANO: Dict[str, Dict[str, Any]] = {
    "Moon": {"arcano": 2, "name": "Lua", "keywords": ["intuição","ciclos","sensibilidade"]},
    "Lua": {"arcano": 2, "name": "Lua", "keywords": ["intuição","ciclos","sensibilidade"]},

    "Mars": {"arcano": 11, "name": "Marte", "keywords": ["ação","coragem","conflito"]},
    "Marte": {"arcano": 11, "name": "Marte", "keywords": ["ação","coragem","conflito"]},

    "Saturn": {"arcano": 20, "name": "Saturno", "keywords": ["limites","estrutura","responsabilidade"]},
    "Saturno": {"arcano": 20, "name": "Saturno", "keywords": ["limites","estrutura","responsabilidade"]},

    "Sun": {"arcano": 22, "name": "Sol", "keywords": ["identidade","vitalidade","expressão"]},
    "Sol": {"arcano": 22, "name": "Sol", "keywords": ["identidade","vitalidade","expressão"]},

    "Venus": {"arcano": 3, "name": "Vênus", "keywords": ["afeto","valores","beleza"]},
    "Vênus": {"arcano": 3, "name": "Vênus", "keywords": ["afeto","valores","beleza"]},

    "Jupiter": {"arcano": 4, "name": "Júpiter", "keywords": ["expansão","sorte","crescimento"]},
    "Júpiter": {"arcano": 4, "name": "Júpiter", "keywords": ["expansão","sorte","crescimento"]},

    "Mercury": {"arcano": 17, "name": "Mercúrio", "keywords": ["comunicação","mente","movimento"]},
    "Mercúrio": {"arcano": 17, "name": "Mercúrio", "keywords": ["comunicação","mente","movimento"]},

    # signos mapeados como arcanos (quando relevante)
    "Libra": {"arcano": 12, "name": "Libra", "keywords": ["equilíbrio","parcerias"]},
    "Escorpio": {"arcano": 14, "name": "Escorpião", "keywords": ["transformação","profundidade"]},
    "Sagitarius": {"arcano": 15, "name": "Sagitário", "keywords": ["busca","expansão"]},

    # restantes conforme sua lista (nomes em PT/EN)
    "Aries": {"arcano": 5, "name": "Áries", "keywords": ["iniciativa","coragem"]},
    "Áries": {"arcano": 5, "name": "Áries", "keywords": ["iniciativa","coragem"]},

    "Gemini": {"arcano": 7, "name": "Gêmeos", "keywords": ["curiosidade","comunicação"]},
    "Gêmeos": {"arcano": 7, "name": "Gêmeos", "keywords": ["curiosidade","comunicação"]},

    "Cancer": {"arcano": 8, "name": "Câncer", "keywords": ["cuidado","memória"]},
    "Câncer": {"arcano": 8, "name": "Câncer", "keywords": ["cuidado","memória"]},

    "Leo": {"arcano": 9, "name": "Leão", "keywords": ["expressão","liderança"]},
    "Leão": {"arcano": 9, "name": "Leão", "keywords": ["expressão","liderança"]},

    "Aquarius": {"arcano": 18, "name": "Aquário", "keywords": ["visão","inovação"]},
    "Aquário": {"arcano": 18, "name": "Aquário", "keywords": ["visão","inovação"]},

    "Pisces": {"arcano": 19, "name": "Peixes", "keywords": ["imaginação","compaixão"]},
    "Peixes": {"arcano": 19, "name": "Peixes", "keywords": ["imaginação","compaixão"]},

    "Capricorn": {"arcano": 16, "name": "Capricórnio", "keywords": ["disciplina","ambição"]},
    "Capricórnio": {"arcano": 16, "name": "Capricórnio", "keywords": ["disciplina","ambição"]},

    "Virgo": {"arcano": 10, "name": "Virgem", "keywords": ["serviço","detalhe"]},
    "Virgem": {"arcano": 10, "name": "Virgem", "keywords": ["serviço","detalhe"]},

    "Taurus": {"arcano": 6, "name": "Touro", "keywords": ["valores","estabilidade"]},
    "Touro": {"arcano": 6, "name": "Touro", "keywords": ["valores","estabilidade"]},

    "Uranus": {"arcano": 1, "name": "Urano", "keywords": ["ruptura","inovação"]},
    "Urano": {"arcano": 1, "name": "Urano", "keywords": ["ruptura","inovação"]},

    "Pluto": {"arcano": 13, "name": "Plutão", "keywords": ["transformação profunda"]},
    "Plutão": {"arcano": 13, "name": "Plutão", "keywords": ["transformação profunda"]},

    "Neptune": {"arcano": 21, "name": "Netuno", "keywords": ["sonho","espiritualidade"]},
    "Netuno": {"arcano": 21, "name": "Netuno", "keywords": ["sonho","espiritualidade"]},
}

# -------------------------
# Numerology helpers
# -------------------------
LETTER_VALUES = {c: ((i % 9) or 9) for i, c in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", start=1)}

def _reduce_number(n: int) -> int:
    while n > 9 and n not in (11, 22):
        n = sum(int(d) for d in str(n))
    return n

def life_path_from_date(bdate: date) -> int:
    total = bdate.day + bdate.month + bdate.year
    return _reduce_number(total)

def name_sum(name: str, vowels_only: bool = False) -> int:
    s = 0
    for ch in name.upper():
        if not ch.isalpha():
            continue
        if vowels_only and ch not in "AEIOU":
            continue
        s += LETTER_VALUES.get(ch, 0)
    return _reduce_number(s)

def numerology_summary(name: str, bdate: date) -> Dict[str, Any]:
    return {
        "life_path": life_path_from_date(bdate),
        "expression": name_sum(name, vowels_only=False),
        "soul_urge": name_sum(name, vowels_only=True)
    }

# -------------------------
# Core correlation and reading generation
# -------------------------
def correlate_planet_arcano(planet_name: str, lon: float) -> Dict[str, Any]:
    """
    Retorna o arcano base e ajusta confiança por posição (ex.: perto de cúspide reduz confiança).
    """
    base = PLANET_ARCANO.get(planet_name) or PLANET_ARCANO.get(planet_name.capitalize())
    if not base:
        return {"arcano": None, "name": None, "keywords": [], "confidence": 0.0}
    confidence = float(base.get("confidence", 0.5))
    deg_in_sign = float(lon) % 30
    # reduzir confiança se estiver muito perto da cúspide
    if deg_in_sign < 2 or deg_in_sign > 28:
        confidence *= 0.85
    return {**base, "confidence": round(confidence, 2)}

def _normalize_planets(raw: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Garante formato {name: {"longitude": float}} aceitando várias chaves.
    """
    out = {}
    for name, pdata in (raw or {}).items():
        lon = None
        if isinstance(pdata, dict):
            for k in ("longitude", "lon", "long", "ecl_lon"):
                if k in pdata and pdata[k] is not None:
                    try:
                        lon = float(pdata[k])
                        break
                    except Exception:
                        lon = None
        else:
            try:
                lon = float(pdata)
            except Exception:
                lon = None
        if lon is not None:
            out[name] = {"longitude": lon}
    return out

def generate_planet_reading(planet_name: str, planet_lon: float, person_name: str, bdate: date, extra: Optional[Dict]=None) -> Dict[str, Any]:
    """
    Gera um dicionário 'reading' pronto para passar a interpretations.generate_interpretation.
    """
    sign, degree, sign_index = astrology.lon_to_sign_degree(planet_lon)
    arcano_info = correlate_planet_arcano(planet_name, planet_lon)
    numerology = numerology_summary(person_name, bdate)

    reading = {
        "name": person_name,
        "planet": planet_name,
        "lon": round(float(planet_lon), 4),
        "sign": sign,
        "degree": round(float(degree), 3),
        "sign_index": sign_index,
        "arcano": arcano_info,
        "numerology": numerology,
    }
    if extra:
        reading.update(extra)

    # gerar texto via interpretations
    arcano_key = arcano_info.get("arcano")
    text_long = generate_interpretation(reading, arcano_key=arcano_key, length="long")
    text_short = generate_interpretation(reading, arcano_key=arcano_key, length="short")

    reading["interpretation_long"] = text_long
    reading["interpretation_short"] = text_short
    reading["arcano_info"] = arcano_info
    return reading

def generate_chart_summary(planets_raw: Dict[str, Any], person_name: str, bdate: date) -> Dict[str, Any]:
    """
    Normaliza planets, gera tabela de posições, aspectos e leituras por planeta.
    Retorna dict com keys: planets, table, aspects, readings, numerology
    """
    planets = _normalize_planets(planets_raw)
    table = astrology.positions_table(planets)
    aspects = astrology.compute_aspects(planets)
    numerology = numerology_summary(person_name, bdate)

    readings = {}
    for row in table:
        pname = row["planet"]
        lon = row["longitude"]
        readings[pname] = generate_planet_reading(pname, lon, person_name, bdate)

    return {
        "planets": planets,
        "table": table,
        "aspects": aspects,
        "readings": readings,
        "numerology": numerology
    }

    # services/analysis.py  -- adicionar no final do arquivo

import os
import json
from typing import Optional
import streamlit as _st

# cache para evitar chamadas repetidas
@_st.cache_data(show_spinner=False)
def generate_ai_interpretation_cached(summary: dict, selected_planet: Optional[str], use_ai: bool = True) -> Optional[str]:
    """
    Gera interpretação IA para o planeta selecionado ou para o mapa inteiro.
    - Tenta usar OpenAI se disponível e configurado (OPENAI_API_KEY).
    - Se não houver configuração, retorna None (o caller deve usar fallback local).
    """
    if not use_ai:
        return None

    # preparar prompt básico a partir do summary
    try:
        if selected_planet and summary.get("readings", {}).get(selected_planet):
            reading = summary["readings"][selected_planet]
            prompt_intro = f"Gerar uma interpretação astrológica clara e prática para: {reading.get('planet')} em {reading.get('sign')} {reading.get('degree')}°.\n\n"
            prompt_intro += f"Dados: longitude={reading.get('lon')}, grau={reading.get('degree')}, numerology={reading.get('numerology')}\n\n"
            prompt_intro += "Incluir: resumo curto (3-4 linhas), sugestões práticas (3 itens) e uma frase de encerramento."
        else:
            # resumo geral do mapa
            table = summary.get("table", [])
            prompt_intro = "Gerar um resumo astrológico geral do mapa com foco em temas principais. Forneça: resumo curto (3-4 linhas) e 5 pontos de destaque.\n\n"
            prompt_intro += "Posições:\n"
            for r in table:
                prompt_intro += f"- {r.get('planet')}: {r.get('sign')} {r.get('degree')}°\n"
    except Exception:
        prompt_intro = "Gerar um resumo astrológico breve a partir dos dados fornecidos."

    # tentar usar OpenAI
    try:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENAI_KEY")
        if not api_key:
            return None
        openai.api_key = api_key

        # montar mensagem
        system_msg = {
            "role": "system",
            "content": "Você é um assistente que gera interpretações astrológicas claras, práticas e respeitosas. Evite previsões deterministas; foque em orientação."
        }
        user_msg = {"role": "user", "content": prompt_intro}

        # chamada simples (compatível com ChatCompletion or Chat API)
        try:
            # tentativa moderna
            resp = openai.ChatCompletion.create(model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"), messages=[system_msg, user_msg], max_tokens=600, temperature=0.8)
            text = resp.choices[0].message.content.strip()
        except Exception:
            # fallback para completions
            resp = openai.Completion.create(engine=os.environ.get("OPENAI_ENGINE", "text-davinci-003"), prompt=prompt_intro, max_tokens=600, temperature=0.8)
            text = resp.choices[0].text.strip()

        return text
    except Exception:
        # se openai não estiver disponível ou falhar, retornar None para indicar fallback
        return None