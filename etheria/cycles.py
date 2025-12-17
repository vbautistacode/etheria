# cycles.py
"""
Módulo de ciclos astrológicos e teosóficos com lógica fixa para regentes por ano.
"""

from typing import List, Dict, Optional, Any
from datetime import date, datetime
import pandas as pd

# -------------------------
# Descrições curtas (UI)
# -------------------------
CICLO_MAIOR_DESC = (
    "O Ciclo Maior é como uma longa travessia da alma. "
    "Assim como os dias da semana se sucedem em ordem inversa, ele nos lembra que o tempo "
    "não é apenas linear, mas também espiralado. Cada retorno é um convite à reflexão: "
    "o que aprendemos ao caminhar contra o fluxo aparente da vida?"
)

CICLO_MENOR_TEOSOFICO_DESC = (
    "O Ciclo Menor Teosófico revela o paradoxo do tempo: "
    "os dias da semana giram em sentido contrário, como se nos ensinassem que o espírito "
    "cresce ao desafiar a direção comum. É um chamado à interioridade, à escuta do silêncio, "
    "onde o ritmo do cosmos se torna espelho da nossa própria busca."
)

CICLO_MENOR_ASTROLOGICO_DESC = (
    "O Ciclo Menor Astrológico é guiado pela dança dos planetas em torno do Sol. "
    "Cada translação é um gesto cósmico que nos recorda: somos parte de uma sinfonia maior. "
    "A influência planetária não é destino fixo, mas metáfora viva daquilo que pulsa em nós. "
    "Assim como os astros se movem, também nós somos chamados a mover-nos em direção à verdade interior."
)

# -------------------------
# Sequências e parâmetros padrão
# -------------------------
PLANETS_ASTROLOGICAL: List[str] = ["Jupiter", "Saturn", "Moon", "Mercury", "Venus", "Sun", "Mars"]
PLANETS_TEOSOPHICAL: List[str] = ["Venus", "Saturn", "Sun", "Moon", "Mars", "Mercury", "Jupiter"]
PLANETS_MAJOR: List[str] = ["Saturn", "Venus", "Jupite", "Sun", "Mercury", "Mars", "Moon"]

MAJOR_STEP = -36
MAJOR_BLOCK = MAJOR_STEP * len(PLANETS_MAJOR)  # 252

# Valores de alinhamento (ajuste conforme sua convenção)
BASE_YEAR_ASTRO = 2025
BASE_YEAR_TEOS = 2025
BASE_YEAR_MAJOR = (2025-8)

# -------------------------
# Helpers
# -------------------------
def _resolve_planet_list(mode: str = "astrologico", planets: Optional[List[str]] = None) -> List[str]:
    if planets:
        return planets
    key = (mode or "astrologico").lower()
    if key in ("teosofico", "teosófico"):
        return PLANETS_TEOSOPHICAL
    return PLANETS_ASTROLOGICAL

def _as_int_safe(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None

# -------------------------
# Regente fixo por ano (regra determinística)
# -------------------------
def regent_by_year(year: int, cycle: str = "astrologico",
                    base_year_astro: int = BASE_YEAR_ASTRO,
                    base_year_teos: int = BASE_YEAR_TEOS,
                    base_year_major: int = BASE_YEAR_MAJOR,
                    planets_override: Optional[List[str]] = None) -> str:
    """
    Retorna o nome do planeta regente para o ano civil 'year' segundo o ciclo escolhido.
    cycle: 'astrologico' | 'teosofico' | 'maior'
    Os base_year permitem alinhar historicamente a sequência.
    """
    if year < 1:
        raise ValueError("year must be >= 1")

    key = (cycle or "astrologico").lower()
    if key in ("astrologico", "astrológico"):
        planet_list = planets_override or PLANETS_ASTROLOGICAL
        idx = (year - base_year_astro) % len(planet_list)
        return planet_list[idx]

    if key in ("teosofico", "teosófico"):
        planet_list = planets_override or PLANETS_TEOSOPHICAL
        idx = (year - base_year_teos) % len(planet_list)
        return planet_list[idx]

    # ciclo maior (35/252 logic): cada planeta domina um bloco de MAJOR_STEP anos
    if key in ("maior", "cycle35", "cycle_35"):
        planet_list = planets_override or PLANETS_MAJOR
        offset = (year - base_year_major) % MAJOR_BLOCK
        index = offset // MAJOR_STEP
        return planet_list[int(index)]

    # fallback: astrologico
    planet_list = planets_override or PLANETS_ASTROLOGICAL
    idx = (year - base_year_astro) % len(planet_list)
    return planet_list[idx]

# -------------------------
# Funções auxiliares já existentes (compatibilidade)
# -------------------------
def planet_for_year(year: int, mode: str = "astrologico", planets: Optional[List[str]] = None) -> str:
    return regent_by_year(year, cycle=mode, planets_override=planets)

def generate_cycle_table(max_year: int = 4060, mode: str = "astrologico", planets: Optional[List[str]] = None) -> pd.DataFrame:
    data = [{"Year": y, "Planet": regent_by_year(y, cycle=mode, planets_override=planets)} for y in range(1, max_year + 1)]
    return pd.DataFrame(data)

def cycle35_for_age(age: int, mode: str = "astrologico", planets: Optional[List[str]] = None) -> Dict[str, Any]:
    if age < 0:
        raise ValueError("age must be >= 0")
    cycle_year = ((age - 1) % 35) + 1 if age >= 1 else 1
    planet = regent_by_year(cycle_year, cycle="maior", planets_override=planets)
    return {"age": age, "cycle_year": cycle_year, "planet": planet, "mode": mode}

def planet_for_major_year(year: int, planets: Optional[List[str]] = None) -> str:
    return regent_by_year(year, cycle="maior", planets_override=planets)

def cycle_major_for_age(age: int, planets: Optional[List[str]] = None) -> Dict[str, Any]:
    if age < 0:
        raise ValueError("age must be >= 0")
    major_year = ((age - 1) % MAJOR_BLOCK) + 1 if age >= 1 else 1
    planet = regent_by_year(major_year, cycle="maior", planets_override=planets)
    return {"age": age, "major_year": major_year, "planet": planet}

def cycle1_for_date(month: int, day: int, hour: Optional[int] = None,
                    df_cycle1: Optional[pd.DataFrame] = None, mode: str = "astrologico") -> Dict[str, Any]:
    """
    Determina regência do ciclo anual para uma data (month, day).
    Se df_cycle1 tiver Month/Day, usa tabela; senão usa weekday invertido como fallback.
    """
    if df_cycle1 is not None:
        cols = {c.lower(): c for c in df_cycle1.columns}
        if "month" in cols and "day" in cols:
            mcol = cols["month"]; dcol = cols["day"]
            row = df_cycle1[(df_cycle1[mcol].astype(str) == str(month)) & (df_cycle1[dcol].astype(str) == str(day))]
            if not row.empty:
                r = row.iloc[0].to_dict()
                return {"planet": r.get("Planet") or r.get("planet"), "source": "table", "row": r}
    try:
        dt = date(2000, month, day)
    except Exception:
        return {"planet": None, "source": "none", "row": None}
    weekday = dt.weekday()  # 0..6 Mon..Sun
    inv = 6 - weekday
    planet_list = _resolve_planet_list(mode, None)
    planet = planet_list[inv % len(planet_list)]
    return {"planet": planet, "source": "rule", "weekday_index": weekday, "inverted_index": inv, "mode": mode}

# -------------------------
# Lookup em DataFrame
# -------------------------
def _find_row_by_key(df: Optional[pd.DataFrame], key_value: Any) -> Optional[pd.Series]:
    if df is None or df.empty:
        return None
    cols_lower = {c.lower(): c for c in df.columns}
    candidates = ("yearindex", "year_index", "arcano", "arcanonumber", "arcano_number", "number", "id")
    for cand in candidates:
        if cand in cols_lower:
            col = cols_lower[cand]
            match = df[df[col].astype(str) == str(key_value)]
            if not match.empty:
                return match.iloc[0]
    first = df.columns[0]
    match = df[df[first].astype(str) == str(key_value)]
    if not match.empty:
        return match.iloc[0]
    return None

def get_regent_from_table(df: Optional[pd.DataFrame], key_value: Any) -> Optional[Dict[str, Any]]:
    row = _find_row_by_key(df, key_value)
    if row is None:
        return None
    return row.to_dict()

def get_regent_for_cycle(
    cycle_name: str,
    target_date: Optional[datetime] = None,
    data_sources: Optional[Dict[str, Optional[pd.DataFrame]]] = None,
    *,
    base_year_astro: int = BASE_YEAR_ASTRO,
    base_year_teos: int = BASE_YEAR_TEOS,
    base_year_major: int = BASE_YEAR_MAJOR
) -> Dict[str, Any]:
    """
    Retorna {cycle, index_or_year, regent(dict or None), source}.
    Usa regent_by_year como regra fixa; prioriza tabelas em data_sources quando presentes.
    """
    data_sources = data_sources or {}
    df35 = data_sources.get("cycle_35")
    df1 = data_sources.get("cycle_1year")
    corr = data_sources.get("corr_df")

    now = target_date or datetime.now()
    key = (cycle_name or "astrologico").strip().lower()

    # preferir tabela se existir e contiver mapeamento por ano/índice
    if key in ("maior", "cycle35", "cycle_35"):
        year = now.year
        # tentar lookup em df35 por YearIndex ou por ano
        reg = get_regent_from_table(df35, year) or get_regent_from_table(df35, ((year - base_year_major) % 35) + 1) or get_regent_from_table(corr, year)
        if reg:
            return {"cycle": "cycle_35", "index_or_year": year, "regent": reg, "source": "table"}
        planet = regent_by_year(year, cycle="maior", base_year_major=base_year_major)
        return {"cycle": "cycle_35", "index_or_year": year, "regent": {"Planeta": planet}, "source": "computed"}

    if key in ("astrologico", "astrológico", "teosofico", "teosófico"):
        year = now.year
        reg = get_regent_from_table(df1, year) or get_regent_from_table(corr, year)
        if reg:
            return {"cycle": key, "index_or_year": year, "regent": reg, "source": "table"}
        planet = regent_by_year(year, cycle=key, base_year_astro=base_year_astro, base_year_teos=base_year_teos)
        return {"cycle": key, "index_or_year": year, "regent": {"Planeta": planet}, "source": "computed"}

    # fallback
    year = now.year
    planet = regent_by_year(year, cycle="astrologico", base_year_astro=base_year_astro)
    return {"cycle": key, "index_or_year": year, "regent": {"Planeta": planet}, "source": "computed"}

def short_regent_label(reg: Optional[Dict[str, Any]]) -> str:
    if not reg:
        return "—"
    for k in ("Planeta", "planeta", "Planet", "Arcano", "arcano", "Valor", "valor", "Nota Musical", "nota musical", "Regente", "regente"):
        if k in reg and pd.notna(reg[k]) and str(reg[k]).strip() != "":
            return str(reg[k])
    for v in reg.values():
        if pd.notna(v) and str(v).strip() != "":
            return str(v)
    return "—"