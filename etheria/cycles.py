# cycles.py
"""
Módulo de ciclos astrológicos e teosóficos com lógica fixa para regentes por ano.
Internamente usa nomes canônicos em inglês; fornece rótulos em pt_BR para UI.
Mantém chaves antigas (ex.: "Planeta") para compatibilidade.
"""

from typing import List, Dict, Optional, Any, Tuple
from datetime import date, datetime
import unicodedata
import pandas as pd

# -------------------------
# Descrições curtas (UI) - em pt_BR
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
# Canonical names (internos) e rótulos pt_BR para UI
# -------------------------
CANONICAL_PLANETS: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
]

# Rótulos em português (para UI)
CANONICAL_TO_PT_PLANET: Dict[str, str] = {
    "Sun": "Sol",
    "Moon": "Lua",
    "Mercury": "Mercúrio",
    "Venus": "Vênus",
    "Mars": "Marte",
    "Jupiter": "Júpiter",
    "Saturn": "Saturno",
    "Uranus": "Urano",
    "Neptune": "Netuno",
    "Pluto": "Plutão",
}

# Variantes em pt_BR (raw) -> canonical EN
_raw_pt_to_canonical_planet = {
    "Sol": "Sun", "sol": "Sun",
    "Lua": "Moon", "lua": "Moon",
    "Mercúrio": "Mercury", "Mercurio": "Mercury", "mercurio": "Mercury", "mercury": "Mercury",
    "Vênus": "Venus", "Venus": "Venus", "venus": "Venus",
    "Marte": "Mars", "marte": "Mars", "mars": "Mars",
    "Júpiter": "Jupiter", "Jupiter": "Jupiter", "jupiter": "Jupiter",
    "Saturno": "Saturn", "saturno": "Saturn", "saturn": "Saturn",
    "Urano": "Uranus", "urano": "Uranus", "uranus": "Uranus",
    "Netuno": "Neptune", "netuno": "Neptune", "neptune": "Neptune",
    "Plutão": "Pluto", "Plutao": "Pluto", "plutao": "Pluto", "pluto": "Pluto",
}

def _strip_accents(s: str) -> str:
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nkfd if not unicodedata.combining(ch))

def _norm_key(s: str) -> str:
    return _strip_accents(s).strip().lower()

# Normaliza o mapeamento PT -> canonical (chaves sem acento e lower)
PT_TO_CANONICAL_PLANET: Dict[str, str] = {_norm_key(k): v for k, v in _raw_pt_to_canonical_planet.items()}

# -------------------------
# Sequências e parâmetros padrão (internos: canonical EN)
# -------------------------
PLANETS_ASTROLOGICAL: List[str] = [
    "Jupiter", "Saturn", "Moon", "Mercury", "Venus", "Sun", "Mars"
]

PLANETS_TEOSOPHICAL: List[str] = [
    "Venus", "Saturn", "Sun", "Moon", "Mars", "Mercury", "Jupiter"
]

PLANETS_MAJOR: List[str] = [
    "Saturn", "Venus", "Jupiter", "Sun", "Mercury", "Mars", "Moon"
]

MAJOR_STEP = -36
MAJOR_BLOCK = MAJOR_STEP * len(PLANETS_MAJOR)  # 252

# Valores de alinhamento (ajuste conforme sua convenção)
BASE_YEAR_ASTRO = 2025
BASE_YEAR_TEOS = 2025
BASE_YEAR_MAJOR = (2025 - 8)

# -------------------------
# Conteúdos interpretativos (chaves canônicas EN, valores em pt_BR)
# -------------------------
PLANET_CORE: Dict[str, Tuple[str, str]] = {
    "Sun": ("Ser", "Identidade, Essência e Brilho"),
    "Moon": ("Sentir", "Emoção, Nutrição e Hábito"),
    "Mercury": ("Comunicar", "Pensamento e Conexão, Raciocínio"),
    "Venus": ("Relacionar", "Valor, Afeto e Atração"),
    "Mars": ("Agir", "Impulso, Luta e Iniciativa"),
    "Jupiter": ("Expandir", "Crescimento, Otimismo e Fé"),
    "Saturn": ("Estruturar", "Limite, Disciplina e Responsabilidade"),
    "Uranus": ("Inovar", "Quebra, Mudança Súbita e Revolução"),
    "Neptune": ("Idealizar", "Dissolver, Sonhar e Ilusão"),
    "Pluto": ("Transformar", "Poder, Crise e Regeneração"),
}

# Signos canônicos (EN) e rótulos PT para UI
CANONICAL_SIGNS: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

CANONICAL_TO_PT_SIGN: Dict[str, str] = {
    "Aries": "Áries",
    "Taurus": "Touro",
    "Gemini": "Gêmeos",
    "Cancer": "Câncer",
    "Leo": "Leão",
    "Virgo": "Virgem",
    "Libra": "Libra",
    "Scorpio": "Escorpião",
    "Sagittarius": "Sagitário",
    "Capricorn": "Capricórnio",
    "Aquarius": "Aquário",
    "Pisces": "Peixes",
}

SIGN_DESCRIPTIONS: Dict[str, Tuple[str, str]] = {
    "Aries": ("Início", "Impulso, Coragem e Ponto de Partida"),
    "Taurus": ("Valor", "Estabilidade, Materialidade e Posse"),
    "Gemini": ("Conexão", "Curiosidade, Dualidade e Troca"),
    "Cancer": ("Acolhimento", "Emoção, Raiz e Família"),
    "Leo": ("Expressão", "Brilho, Centralidade e Liderança"),
    "Virgo": ("Serviço", "Análise, Detalhe e Método"),
    "Libra": ("Equilíbrio", "Justiça, Parceria e Harmonia"),
    "Scorpio": ("Profundidade", "Intensidade, Crise e Transformação"),
    "Sagittarius": ("Busca", "Expansão, Conhecimento e Aventura"),
    "Capricorn": ("Realização", "Estrutura, Ambição e Autoridade"),
    "Aquarius": ("Liberdade", "Humanidade, Inovação e Coletivo"),
    "Pisces": ("União", "Sensibilidade, Empatia e Totalidade"),
}

HOUSE_DESCRIPTIONS: Dict[int, Tuple[str, str]] = {
    1: ("Eu", "Identidade, Aparência e Início de Tudo"),
    2: ("Recursos", "Finanças, Bens Materiais e Valor Pessoal"),
    3: ("Comunidade", "Comunicação Diária, Irmãos e Estudos Básicos"),
    4: ("Raízes", "Lar, Família, Passado e Base Emocional"),
    5: ("Criação", "Prazer, Filhos, Hobbies e Criatividade"),
    6: ("Rotina", "Trabalho Diário, Saúde, Serviço e Hábitos"),
    7: ("Parceria", "Relacionamentos, Casamento e Associações"),
    8: ("Transformação", "Crises, Intimidade, Finanças Compartilhadas e Morte e Renascimento"),
    9: ("Sentido", "Filosofia, Ensino Superior, Viagens Longas e Crenças"),
    10: ("Carreira", "Status, Reputação Pública, Vocação e Autoridade"),
    11: ("Grupo", "Amizades, Metas, Causas e Coletividade"),
    12: ("Inconsciente", "Isolamento, Espiritualidade, Sacrifício e Assuntos Ocultos"),
}

PLANET_ORDER: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
]

# -------------------------
# Helpers de normalização e conversão
# -------------------------
def planet_to_canonical(name: Optional[str]) -> Optional[str]:
    """Converte nome (pt_BR ou EN) para canonical EN. Retorna None se name falsy."""
    if not name:
        return None
    s = str(name).strip()
    # já canonical?
    for can in CANONICAL_PLANETS:
        if can.lower() == s.lower():
            return can
    key = _norm_key(s)
    return PT_TO_CANONICAL_PLANET.get(key, s)

def planet_label_pt(canonical: Optional[str]) -> Optional[str]:
    """Retorna rótulo em pt_BR para um nome canônico EN."""
    if not canonical:
        return None
    return CANONICAL_TO_PT_PLANET.get(canonical, canonical)

def sign_to_canonical(name: Optional[str]) -> Optional[str]:
    """Converte nome de signo (pt_BR ou EN) para canonical EN."""
    if not name:
        return None
    s = str(name).strip()
    for can in CANONICAL_SIGNS:
        if can.lower() == s.lower():
            return can
    key = _norm_key(s)
    # tenta mapear por rótulos PT conhecidos
    for en, pt in CANONICAL_TO_PT_SIGN.items():
        if _norm_key(pt) == key:
            return en
    return s

def sign_label_pt(canonical: Optional[str]) -> Optional[str]:
    if not canonical:
        return None
    return CANONICAL_TO_PT_SIGN.get(canonical, canonical)

def normalize_planet_list(planets: Optional[List[str]]) -> Optional[List[str]]:
    """Converte lista de nomes (pt_BR/EN) para lista de canonical EN."""
    if planets is None:
        return None
    return [planet_to_canonical(p) for p in planets]

# -------------------------
# Helpers internos
# -------------------------
def _resolve_planet_list(mode: str = "astrologico", planets: Optional[List[str]] = None) -> List[str]:
    """Retorna lista de planetas canônicos (EN) conforme modo ou override (normalizado)."""
    if planets:
        normalized = normalize_planet_list(planets)
        return normalized
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
    Retorna o nome canônico (EN) do planeta regente para o ano civil 'year' segundo o ciclo escolhido.
    cycle: 'astrologico' | 'teosofico' | 'maior'
    planets_override aceita nomes em pt_BR ou EN; será normalizado para canonical EN.
    """
    if year < 1:
        raise ValueError("year must be >= 1")

    key = (cycle or "astrologico").lower()

    if key in ("astrologico", "astrológico"):
        planet_list = normalize_planet_list(planets_override) if planets_override else PLANETS_ASTROLOGICAL
        idx = (year - base_year_astro) % len(planet_list)
        return planet_list[idx]

    if key in ("teosofico", "teosófico"):
        planet_list = normalize_planet_list(planets_override) if planets_override else PLANETS_TEOSOPHICAL
        idx = (year - base_year_teos) % len(planet_list)
        return planet_list[idx]

    # ciclo maior: cada planeta domina um bloco de MAJOR_STEP anos
    if key in ("maior", "cycle35", "cycle_35"):
        planet_list = normalize_planet_list(planets_override) if planets_override else PLANETS_MAJOR
        offset = (year - base_year_major) % MAJOR_BLOCK
        index = offset // MAJOR_STEP
        return planet_list[int(index)]

    # fallback: astrologico
    planet_list = normalize_planet_list(planets_override) if planets_override else PLANETS_ASTROLOGICAL
    idx = (year - base_year_astro) % len(planet_list)
    return planet_list[idx]

# -------------------------
# Funções auxiliares (compatibilidade e utilitários)
# -------------------------
def planet_for_year(year: int, mode: str = "astrologico", planets: Optional[List[str]] = None) -> str:
    return regent_by_year(year, cycle=mode, planets_override=planets)

def generate_cycle_table(max_year: int = 4060, mode: str = "astrologico", planets: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Gera DataFrame com colunas:
      - Year (int)
      - Planet (canonical EN)
      - PlanetLabel (pt_BR)
      - Planeta (legacy PT key)
    """
    planet_list_override = normalize_planet_list(planets) if planets else None
    data = []
    for y in range(1, max_year + 1):
        p = regent_by_year(y, cycle=mode, planets_override=planet_list_override)
        data.append({
            "Year": y,
            "Planet": p,
            "PlanetLabel": planet_label_pt(p),
            "Planeta": planet_label_pt(p)  # chave antiga para compatibilidade
        })
    return pd.DataFrame(data)

def cycle35_for_age(age: int, mode: str = "astrologico", planets: Optional[List[str]] = None) -> Dict[str, Any]:
    if age < 0:
        raise ValueError("age must be >= 0")
    cycle_year = ((age - 1) % 35) + 1 if age >= 1 else 1
    planet = regent_by_year(cycle_year, cycle="maior", planets_override=planets)
    return {
        "age": age,
        "cycle_year": cycle_year,
        "planet": planet,
        "planet_label": planet_label_pt(planet),
        "Planeta": planet_label_pt(planet),  # legacy
        "mode": mode
    }

def planet_for_major_year(year: int, planets: Optional[List[str]] = None) -> str:
    return regent_by_year(year, cycle="maior", planets_override=planets)

def cycle_major_for_age(age: int, planets: Optional[List[str]] = None) -> Dict[str, Any]:
    if age < 0:
        raise ValueError("age must be >= 0")
    major_year = ((age - 1) % MAJOR_BLOCK) + 1 if age >= 1 else 1
    planet = regent_by_year(major_year, cycle="maior", planets_override=planets)
    return {
        "age": age,
        "major_year": major_year,
        "planet": planet,
        "planet_label": planet_label_pt(planet),
        "Planeta": planet_label_pt(planet)  # legacy
    }

def cycle1_for_date(month: int, day: int, hour: Optional[int] = None,
                    df_cycle1: Optional[pd.DataFrame] = None, mode: str = "astrologico") -> Dict[str, Any]:
    """
    Determina regência do ciclo anual para uma data (month, day).
    Se df_cycle1 tiver Month/Day, usa tabela; senão usa weekday invertido como fallback.
    Retorna planet canônico e label pt_BR, incluindo chave antiga 'Planeta'.
    """
    if df_cycle1 is not None:
        cols = {c.lower(): c for c in df_cycle1.columns}
        if "month" in cols and "day" in cols:
            mcol = cols["month"]; dcol = cols["day"]
            row = df_cycle1[(df_cycle1[mcol].astype(str) == str(month)) & (df_cycle1[dcol].astype(str) == str(day))]
            if not row.empty:
                r = row.iloc[0].to_dict()
                planet_raw = r.get("Planet") or r.get("planet") or r.get("Planeta") or r.get("planeta")
                planet = planet_to_canonical(planet_raw) if planet_raw else None
                return {
                    "planet": planet,
                    "planet_label": planet_label_pt(planet),
                    "Planeta": planet_label_pt(planet),
                    "source": "table",
                    "row": r
                }
    try:
        dt = date(2000, month, day)
    except Exception:
        return {"planet": None, "planet_label": None, "Planeta": None, "source": "none", "row": None}
    weekday = dt.weekday()  # 0..6 Mon..Sun
    inv = 6 - weekday
    planet_list = _resolve_planet_list(mode, None)
    planet = planet_list[inv % len(planet_list)]
    return {
        "planet": planet,
        "planet_label": planet_label_pt(planet),
        "Planeta": planet_label_pt(planet),
        "source": "rule",
        "weekday_index": weekday,
        "inverted_index": inv,
        "mode": mode
    }

# -------------------------
# Lookup em DataFrame
# -------------------------
def _find_row_by_key(df: Optional[pd.DataFrame], key_value: Any) -> Optional[pd.Series]:
    if df is None or df.empty:
        return None
    cols_lower = {c.lower(): c for c in df.columns}
    candidates = ("yearindex", "year_index", "arcano", "arcanonumber", "arcano_number", "number", "id", "year")
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
    O campo 'regent' contém chaves: 'planet' (canonical EN), 'planet_label' (pt_BR) e 'Planeta' (legacy).
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
        reg = get_regent_from_table(df35, year) or get_regent_from_table(df35, ((year - base_year_major) % 35) + 1) or get_regent_from_table(corr, year)
        if reg:
            # manter retorno da tabela inalterado (compatibilidade), mas também adicionar campos legacy se possível
            if "Planet" in reg or "planet" in reg or "Planeta" in reg:
                # normalize planet value for convenience
                raw = reg.get("Planet") or reg.get("planet") or reg.get("Planeta")
                canonical = planet_to_canonical(raw) if raw else None
                reg["planet"] = canonical
                reg["planet_label"] = planet_label_pt(canonical)
                reg["Planeta"] = planet_label_pt(canonical)
            return {"cycle": "cycle_35", "index_or_year": year, "regent": reg, "source": "table"}
        planet = regent_by_year(year, cycle="maior", base_year_major=base_year_major)
        reg = {"planet": planet, "planet_label": planet_label_pt(planet), "Planeta": planet_label_pt(planet)}
        return {"cycle": "cycle_35", "index_or_year": year, "regent": reg, "source": "computed"}

    if key in ("astrologico", "astrológico", "teosofico", "teosófico"):
        year = now.year
        reg = get_regent_from_table(df1, year) or get_regent_from_table(corr, year)
        if reg:
            if "Planet" in reg or "planet" in reg or "Planeta" in reg:
                raw = reg.get("Planet") or reg.get("planet") or reg.get("Planeta")
                canonical = planet_to_canonical(raw) if raw else None
                reg["planet"] = canonical
                reg["planet_label"] = planet_label_pt(canonical)
                reg["Planeta"] = planet_label_pt(canonical)
            return {"cycle": key, "index_or_year": year, "regent": reg, "source": "table"}
        planet = regent_by_year(year, cycle=key, base_year_astro=base_year_astro, base_year_teos=base_year_teos)
        reg = {"planet": planet, "planet_label": planet_label_pt(planet), "Planeta": planet_label_pt(planet)}
        return {"cycle": key, "index_or_year": year, "regent": reg, "source": "computed"}

    # fallback
    year = now.year
    planet = regent_by_year(year, cycle="astrologico", base_year_astro=base_year_astro)
    reg = {"planet": planet, "planet_label": planet_label_pt(planet), "Planeta": planet_label_pt(planet)}
    return {"cycle": key, "index_or_year": year, "regent": reg, "source": "computed"}

# -------------------------
# Utilitário para rótulo curto (compatível com várias formas de regent dict)
# -------------------------
def short_regent_label(reg: Optional[Dict[str, Any]]) -> str:
    """
    Retorna um rótulo curto legível para exibição.
    Procura chaves preferenciais: 'planet_label', 'Planeta', 'planet', 'Planet', etc.
    """
    if not reg:
        return "—"
    if isinstance(reg, dict):
        # prefer explicit canonical + label keys
        if "planet_label" in reg and pd.notna(reg["planet_label"]) and str(reg["planet_label"]).strip():
            return str(reg["planet_label"])
        if "Planeta" in reg and pd.notna(reg["Planeta"]) and str(reg["Planeta"]).strip():
            return str(reg["Planeta"])
        if "planet" in reg and pd.notna(reg["planet"]) and str(reg["planet"]).strip():
            return str(planet_label_pt(reg["planet"]))
    # fallback: check common legacy keys
    for k in ("Planeta", "planeta", "Planet", "planet", "Arcano", "arcano", "Valor", "valor", "Nota Musical", "nota musical", "Regente", "regente"):
        if isinstance(reg, dict) and k in reg and pd.notna(reg[k]) and str(reg[k]).strip() != "":
            return str(reg[k])
    # last resort: any non-empty value
    if isinstance(reg, dict):
        for v in reg.values():
            if pd.notna(v) and str(v).strip() != "":
                return str(v)
    return "—"