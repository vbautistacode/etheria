# etheria/astrology.py
from typing import Optional, Tuple
from typing import Dict, Any, List
from typing import Iterable
import unicodedata
import math
import logging
logger = logging.getLogger("etheria.astrology")

from typing import Dict, Tuple

# -------------------------
# Canônicos em inglês (internos)
# -------------------------
CANONICAL_PLANETS: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars",
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
]

CANONICAL_SIGNS: List[str] = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGNS = CANONICAL_SIGNS

# -------------------------
# Rótulos em português para UI (EN -> PT)
# -------------------------
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

# -------------------------
# Conteúdos interpretativos usando chaves canônicas em inglês
# Valores em português para exibição
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
    "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

# -------------------------
# Mapeamentos PT -> canonical (normalizados)
# -------------------------
_raw_pt_planet = {
    "Sol": "Sun", "sol": "Sun",
    "Lua": "Moon", "lua": "Moon",
    "Mercúrio": "Mercury", "Mercurio": "Mercury", "mercurio": "Mercury",
    "Vênus": "Venus", "Venus": "Venus", "venus": "Venus",
    "Marte": "Mars", "marte": "Mars",
    "Júpiter": "Jupiter", "Jupiter": "Jupiter", "jupiter": "Jupiter",
    "Saturno": "Saturn", "saturno": "Saturn",
    "Urano": "Uranus", "urano": "Uranus",
    "Netuno": "Neptune", "netuno": "Neptune",
    "Plutão": "Pluto", "Plutao": "Pluto", "plutao": "Pluto",
}

_raw_pt_sign = {
    "Áries": "Aries", "Aries": "Aries", "aries": "Aries",
    "Touro": "Taurus", "touro": "Taurus",
    "Gêmeos": "Gemini", "Gemeos": "Gemini", "gemeos": "Gemini",
    "Câncer": "Cancer", "Cancer": "Cancer", "cancer": "Cancer",
    "Leão": "Leo", "Leao": "Leo", "leo": "Leo",
    "Virgem": "Virgo", "virgem": "Virgo",
    "Libra": "Libra", "libra": "Libra",
    "Escorpião": "Scorpio", "Escorpiao": "Scorpio", "escorpiao": "Scorpio",
    "Sagitário": "Sagittarius", "Sagitario": "Sagittarius", "sagitario": "Sagittarius",
    "Capricórnio": "Capricorn", "Capricornio": "Capricorn", "capricornio": "Capricorn",
    "Aquário": "Aquarius", "Aquario": "Aquarius", "aquario": "Aquarius",
    "Peixes": "Pisces", "peixes": "Pisces",
}

def _strip_accents(s: str) -> str:
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nkfd if not unicodedata.combining(ch))

def _norm_key(s: str) -> str:
    return _strip_accents(s).strip().lower()

PT_TO_CANONICAL_PLANET: Dict[str, str] = {_norm_key(k): v for k, v in _raw_pt_planet.items()}
PT_TO_CANONICAL_SIGN: Dict[str, str] = {_norm_key(k): v for k, v in _raw_pt_sign.items()}

# -------------------------
# Funções utilitárias de conversão
# -------------------------
def planet_to_canonical(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    s = str(name).strip()
    # já canônico?
    for can in CANONICAL_PLANETS:
        if can.lower() == s.lower():
            return can
    key = _norm_key(s)
    return PT_TO_CANONICAL_PLANET.get(key, s)

def sign_to_canonical(name: Optional[str]) -> Optional[str]:
    if not name:
        return None
    s = str(name).strip()
    for can in CANONICAL_SIGNS:
        if can.lower() == s.lower():
            return can
    key = _norm_key(s)
    return PT_TO_CANONICAL_SIGN.get(key, s)

def planet_label_pt(canonical: Optional[str]) -> str:
    return CANONICAL_TO_PT_PLANET.get(canonical, canonical or "—")

def sign_label_pt(canonical: Optional[str]) -> str:
    return CANONICAL_TO_PT_SIGN.get(canonical, canonical or "—")

def lon_to_sign_degree(lon: float):
    """
    Recebe longitude e retorna (sign_canonical, degree_in_sign, sign_index_1based).
    Ex.: lon=45.5 -> ("Taurus", 15.5, 2)
    """
    # normaliza longitude para 0..360
    lon_norm = float(lon) % 360.0
    # cada signo tem 30 graus
    sign_index = int(lon_norm // 30)  # 0..11
    degree = lon_norm % 30.0
    # SIGNS deve existir (veja import/def acima)
    try:
        sign = SIGNS[sign_index]
    except Exception:
        # fallback seguro: use CANONICAL_SIGNS se disponível
        try:
            from path.to.cycles import CANONICAL_SIGNS  # type: ignore # ajuste caminho se necessário
            sign = CANONICAL_SIGNS[sign_index]
        except Exception:
            raise RuntimeError("Sign list not available: define SIGNS or import CANONICAL_SIGNS")
    return sign, round(degree, 2), sign_index + 1

def compute_aspects(positions: Dict[str, Dict[str, float]], orb: float = 6.0) -> List[Dict[str, Any]]:
    """
    Calcula aspectos básicos entre planetas.
    positions: {"Sun": {"longitude": 123.4}, ...} ou {"Sun": 123.4}
    Retorna lista de dicts: p1, p2, angle, type, orb
    """
    aspects: List[Dict[str, Any]] = []
    # normalizar items para (name, longitude)
    items = []
    for name, v in positions.items():
        if isinstance(v, dict):
            lon = v.get("longitude")
        else:
            lon = v
        if lon is None:
            continue
        items.append((name, float(lon)))
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            p1, lon1 = items[i]
            p2, lon2 = items[j]
            diff = abs((lon1 - lon2 + 180) % 360 - 180)
            for angle, name_type in [(0, "Conjunction"), (180, "Opposition"), (120, "Trine"), (90, "Square"), (60, "Sextile")]:
                if abs(diff - angle) <= orb:
                    aspects.append({
                        "p1": p1,
                        "p2": p2,
                        "angle": angle,
                        "type": name_type,
                        "orb": round(abs(diff - angle), 3)
                    })
    return aspects

def positions_table(
    planets: Dict[str, Dict[str, float]],
    cusps: Optional[List[float]] = None,
    compute_house_if_missing: bool = True
) -> List[Dict[str, Any]]:
    import logging, json, pathlib
    logger = logging.getLogger("etheria.astrology.positions_table")
    rows: List[Dict[str, Any]] = []

    try:
        from etheria import influences  # type: ignore
    except Exception:
        influences = None  # type: ignore

    # normalizar cusps
    norm_cusps: Optional[List[float]] = None
    if cusps and isinstance(cusps, (list, tuple)) and len(cusps) >= 12:
        try:
            norm_cusps = [float(c) % 360.0 for c in cusps[:12]]
        except Exception:
            norm_cusps = None

    # ordenar
    keys = list(planets.keys())
    try:
        keys_sorted = sorted(keys, key=lambda k: PLANET_ORDER.index(k) if k in PLANET_ORDER else 999)
    except Exception:
        keys_sorted = keys

    for name in keys_sorted:
        v = planets.get(name, {})
        lon: Optional[float] = None
        if isinstance(v, dict):
            for key in ("longitude", "lon", "long", "deg", "degree"):
                if key in v and v.get(key) not in (None, ""):
                    try:
                        lon = float(v.get(key))
                        break
                    except Exception:
                        continue
        else:
            try:
                lon = float(v)
            except Exception:
                lon = None

        if lon is None:
            logger.debug("skip %r: no longitude", name)
            continue

        lon = float(lon) % 360.0

        # obter signo/grau/índice
        sign_can = None
        degree = None
        sign_index = None
        try:
            sign_can, degree, sign_index = lon_to_sign_degree(lon)
        except Exception:
            try:
                sign_index = int(float(lon) // 30) % 12
                degree = float(lon) % 30
            except Exception:
                sign_index = None
                degree = None
            sign_can = None

        # ajustar sign_index 1..12
        if isinstance(sign_index, int) and sign_index == 0:
            sign_index = 12

        # house
        house = None
        if isinstance(v, dict):
            h_raw = v.get("house") or v.get("casa")
            if h_raw not in (None, "", "None"):
                try:
                    house = int(float(h_raw))
                except Exception:
                    house = None
        if house is None and compute_house_if_missing and norm_cusps:
            try:
                calc = get_house_for_longitude(lon, norm_cusps)
                house = int(calc) if calc else None
            except Exception:
                house = None

        # fallback sign_can pelo índice
        if not sign_can:
            try:
                if isinstance(sign_index, int) and 1 <= sign_index <= 12:
                    sign_can = CANONICAL_SIGNS[sign_index - 1]
            except Exception:
                sign_can = None

        # obter rótulos PT
        try:
            sign_label_pt = influences.sign_label_pt(sign_can) if (influences and hasattr(influences, "sign_label_pt") and sign_can) else (sign_can or "")
        except Exception:
            sign_label_pt = sign_can or ""

        try:
            if influences and hasattr(influences, "to_canonical") and hasattr(influences, "planet_label_pt"):
                pname_can = influences.to_canonical(name)
                planet_label_pt = influences.planet_label_pt(pname_can)
            elif influences and hasattr(influences, "planet_label_pt"):
                planet_label_pt = influences.planet_label_pt(name)
            else:
                planet_label_pt = name
        except Exception:
            planet_label_pt = name

        row = {
            "planet": name,
            "planet_label_pt": planet_label_pt,
            "longitude": round(float(lon), 2),
            "sign": sign_label_pt or (sign_can or ""),
            "sign_label": sign_label_pt or (sign_can or ""),
            "sign_label_pt": sign_label_pt or (sign_can or ""),
            "sign_canonical": sign_can or "",
            "degree": round(float(degree), 2) if degree is not None else None,
            "sign_index": sign_index,
            "house": house
        }

        rows.append(row)

    # escrever debug file com primeiras linhas (ajuda a inspecionar fora do Streamlit)
    try:
        p = pathlib.Path("/tmp/positions_debug.json")
        p.write_text(json.dumps(rows[:20], ensure_ascii=False, default=str))
        logger.debug("wrote /tmp/positions_debug.json with %d rows", len(rows[:20]))
    except Exception:
        pass

    return rows

def get_house_for_longitude(lon: float, cusps: List[float]) -> Optional[int]:
    """
    Determina a casa (1..12) para uma longitude usando lista de cusps (12 valores, casas 1..12).
    Retorna None se cusps inválidos.
    """
    if not cusps or len(cusps) < 12:
        return None
    lon = float(lon) % 360.0
    # cusps expected as list of 12 longitudes for houses 1..12
    for i in range(12):
        start = cusps[i] % 360.0
        end = cusps[(i + 1) % 12] % 360.0
        if start <= end:
            if start <= lon < end:
                return i + 1
        else:
            # wrap-around
            if lon >= start or lon < end:
                return i + 1
    return None

# helper para formatar grau (colocar antes de interpret_planet_position)
def _format_degree(deg: Any) -> str:
    """
    Formata o grau para apresentação: aceita None, str ou número.
    Retorna string vazia se inválido, ou 'X°' com 2 casas decimais.
    """
    if deg is None or deg == "":
        return ""
    try:
        d = float(deg)
        # grau dentro do signo (0..30) já deve ser passado; apenas formatar
        return f"{round(d, 2)}°"
    except Exception:
        # tentar extrair número de string (ex: "6.91")
        try:
            s = str(deg).strip()
            # remover caracteres não numéricos comuns
            import re
            m = re.search(r"[-+]?\d+(\.\d+)?", s)
            if m:
                return f"{round(float(m.group(0)), 2)}°"
        except Exception:
            pass
    return ""

# -------------------------
# Interpretações por posicionamento
# -------------------------

def _planet_core_text(planet: str) -> Tuple[str, str]:
    """Retorna verbo e significado central para o planeta (fallback se desconhecido)."""
    return PLANET_CORE.get(planet, ("Atuar", "Função específica relacionada ao planeta"))

def _sign_text(sign: str) -> Tuple[str, str]:
    """Retorna substantivo e qualidade central do signo (fallback)."""
    return SIGN_DESCRIPTIONS.get(sign, (sign, "Qualidade específica do signo"))

def _house_text(house: Optional[Any]) -> Tuple[str, str]:
    """
    Retorna descrição da casa; aceita int ou string numérica.
    Se house for None ou inválido, retorna fallback legível.
    """
    if house is None:
        return ("Casa desconhecida", "Tema da casa não disponível")
    # tentar converter para inteiro se for string numérica
    try:
        h_int = int(house)
    except Exception:
        return ("Casa desconhecida", "Tema da casa não disponível")
    # buscar descrição
    return HOUSE_DESCRIPTIONS.get(h_int, (f"Casa {h_int}", "Tema da casa não disponível"))

def interpret_planet_position(
    planet: str,
    sign: Optional[str] = None,
    degree: Optional[float] = None,
    house: Optional[int] = None,
    aspects: Optional[Iterable[Dict[str, Any]]] = None,
    context_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Gera interpretação curta e longa para um planeta numa posição.
    Usa nomes canônicos para lookups e rótulos em pt_BR para exibição.
    """
    # importar influences defensivamente
    try:
        from etheria import influences
    except Exception:
        influences = None

        # normalizar para canônicos para lookups internos
    try:
        planet_can = influences.to_canonical(planet) if influences and hasattr(influences, "to_canonical") else planet
    except Exception:
        planet_can = planet

    try:
        sign_can = influences.sign_to_canonical(sign) if influences and hasattr(influences, "sign_to_canonical") else sign
    except Exception:
        sign_can = sign

    # rótulos em pt_BR para exibição (defensivo)
    try:
        planet_label_pt = influences.planet_label_pt(planet_can) if influences and hasattr(influences, "planet_label_pt") else (planet or "")
    except Exception:
        planet_label_pt = planet or ""
        logger.debug("interpret_planet_position: planet_label_pt fallback for %r", planet_can)

    try:
        sign_label_pt = influences.sign_label_pt(sign_can) if influences and hasattr(influences, "sign_label_pt") else (sign or "")
    except Exception:
        sign_label_pt = sign or ""
        logger.debug("interpret_planet_position: sign_label_pt fallback for %r", sign_can)

    # lookups internos com canônicos
    verb, pcore = _planet_core_text(planet_can)
    sign_noun, sign_quality = _sign_text(sign_can or "")
    house_noun, house_theme = _house_text(house)

    deg_text = house_noun if house_noun else _format_degree(degree)
    who = f"{context_name}, " if context_name else ""

    # Short: 1-2 frases usando rótulos PT
    short = (
        f"{who}{planet_label_pt} em {sign_label_pt or '—'} {deg_text} fala sobre {pcore.lower()} conectando {sign_quality.lower()}. "
        f"Resumo prático: {verb.lower()} no campo do(a) {house_noun.lower()}."
    )

    # Long: 3-5 parágrafos curtos
    long_parts = []

    # Parágrafo 1: síntese funcional
    p1 = (
        f"{planet_label_pt} representa a(o) {pcore.lower()}. Em {sign_label_pt or '—'}, traz a ideia de {sign_quality.lower()}. "
        f"Essa energia tende a se expressar como {verb.lower()} orientado para {sign_noun.lower()}."
    )
    if deg_text:
        p1 += f" (grau {deg_text})."
    long_parts.append(p1)

    # Parágrafo 2: casa e aplicação prática
    p2 = (
        f"A presença na casa do(a) {house_noun} aponta para ênfase em {house_theme.lower()}. "
        f"Na prática, espere que assuntos ligados a(ao) {house_noun.lower()} sejam o palco onde essa energia se manifesta."
    )
    long_parts.append(p2)

    # Parágrafo 3: aspectos (se houver) — converter planetas dos aspectos para PT
    if aspects:
        rel = []
        for a in aspects:
            p1_name = a.get("p1")
            p2_name = a.get("p2")
            try:
                p1_can = influences.to_canonical(p1_name) if influences and hasattr(influences, "to_canonical") else p1_name
            except Exception:
                p1_can = p1_name
            try:
                p2_can = influences.to_canonical(p2_name) if influences and hasattr(influences, "to_canonical") else p2_name
            except Exception:
                p2_can = p2_name

            if p1_can == planet_can or p2_can == planet_can:
                other_can = p2_can if p1_can == planet_can else p1_can
                try:
                    other_label = influences.planet_label_pt(other_can) if influences and hasattr(influences, "planet_label_pt") else (other_can or "")
                except Exception:
                    other_label = other_can or ""
                rel.append(f"{a.get('type','').lower()} com {other_label} (orb {a.get('orb')})")
        if rel:
            p3 = "Aspectos relevantes: " + "; ".join(rel) + "."
        else:
            p3 = "Não há aspectos maiores registrados que modifiquem substancialmente esta leitura."
    else:
        p3 = "Sem dados de aspectos, considere que a leitura é focal e direta."
    long_parts.append(p3)

    # Parágrafo 4: recomendações práticas
    first_quality = (sign_quality.split(",")[0] if sign_quality else "equilíbrio")
    p4 = (
        f"Recomendações práticas: cultive {first_quality.lower()} e aplique de forma consciente "
        f"no âmbito da(o) {house_noun.lower()}. Evite extremos e busque equilíbrio entre intenção e ação."
    )
    long_parts.append(p4)

    long = "\n\n".join(long_parts)

    return {"short": short, "long": long}

"""
Gera interpretação para os ciclos planetários em dois estilos: técnico e poético.
- planet: nome do planeta (ex: 'Sun', 'Moon')
"""

# helpers simples
def _keywords_from_text(text: Optional[str], max_items: int = 4) -> List[str]:
    if not text:
        return []
    parts = [p.strip() for p in text.split(",") if p.strip()]
    seen = []
    for p in parts:
        token = p.split()[0].strip()
        if token and token not in seen:
            seen.append(token)
        if len(seen) >= max_items:
            break
    return seen

# templates por planeta (ciclos astrologicos): cada entrada tem 'technical' e 'poetic' strings ou lambdas
_PLANET_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Sol": {
        "technical": {
            "short": "É tempo de: afirmar identidade e propósito.",
            "long": (
                "É tempo de: afirmar identidade e propósito.\n\n"
                "Ações práticas:\n"
                "- Defina um objetivo central para o ano.\n"
                "- Meça impacto por visibilidade (ex.: feitos, reconhecimento recebido).\n"
                "- Revise mensalmente prioridades e ajuste conforme resultados.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: frequência de ações alinhadas ao seu propósito.\n"
                "- Secundária: relatos de mudanças percebida."
            )
        },
        "poetic": {
            "short": "É tempo de: deixar o Sol revelar sua presença.",
            "long": (
                "O Sol é a centelha que revela quem somos. Sua luz não pede permissão, apenas se mostra. "
                "Cada gesto é um raio que ilumina o caminho da identidade.\n\n"
                "Reflexão filosófica:\n"
                "- A presença é prática de autenticidade.\n"
                "- O brilho não é medido em números, mas em coerência.\n\n"
                "Metáfora: cultivar o próprio Sol é aprender a ser janela aberta para o mundo."
            )
        }
    },
    "Lua": {
        "technical": {
            "short": "É tempo de: cuidar das emoções e da rotina.",
            "long": (
                "É tempo de: cuidar das emoções e da rotina.\n\n"
                "Ações práticas:\n"
                "- Crie um hábito noturno de relaxamento.\n"
                "- Registre humor e qualidade do sono diariamente.\n"
                "- Ajuste hábitos semanais conforme padrões percebidos.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: consistência do autocuidado.\n"
                "- Secundária: variação de humor registrada."
            )
        },
        "poetic": {
            "short": "É tempo de: ouvir as marés internas da Lua.",
            "long": (
                "A Lua nos lembra que somos feitos de ciclos. Suas fases refletem o movimento íntimo das emoções. "
                "Cuidar da maré interior é manter fértil a costa da vida.\n\n"
                "Reflexão filosófica:\n"
                "- Emoções são ondas que pedem aceitação.\n"
                "- O silêncio noturno é convite à escuta.\n\n"
                "Metáfora: cada hábito de cuidado é como devolver água ao rio que nos sustenta."
            )
        }
    },
    "Mercúrio": {
        "technical": {
            "short": "É tempo de: comunicar com clareza e foco.",
            "long": (
                "É tempo de: comunicar com clareza e foco.\n\n"
                "Ações práticas:\n"
                "- Defina uma mensagem-chave por semana.\n"
                "- Meça clareza pelo feedback recebido.\n"
                "- Use ciclos curtos de revisão para reduzir ruído.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: taxa de compreensão.\n"
                "- Secundária: tempo médio de resposta."
            )
        },
        "poetic": {
            "short": "É tempo de: deixar Mercúrio soprar ideias organizadas.",
            "long": (
                "Mercúrio é vento que leva palavras. Cada frase é fio que tece a rede da convivência. "
                "Comunicar é mais que transmitir: é criar pontes invisíveis.\n\n"
                "Reflexão filosófica:\n"
                "- A palavra é gesto de cuidado.\n"
                "- O silêncio também comunica.\n\n"
                "Metáfora: tratar ideias como cartas que precisam ser endereçadas com atenção."
            )
        }
    },
    "Vênus": {
        "technical": {
            "short": "É tempo de: nutrir valores, vínculos e estética.",
            "long": (
                "É tempo de: nutrir valores, vínculos e estética.\n\n"
                "Ações práticas:\n"
                "- Ofereça um gesto de carinho ou apreço por dia.\n"
                "- Crie um ritual semanal de apreciação (flores, música, encontro).\n"
                "- Observe como a reciprocidade se transforma em 21 dias.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: satisfação relacional.\n"
                "- Secundária: frequência de gestos de cuidado."
            )
        },
        "poetic": {
            "short": "É tempo de: deixar Vênus suavizar o mundo com beleza.",
            "long": (
                "Vênus lembra que relações e estética são práticas de cuidado. "
                "Pequenos atos de apreço transformam ambientes e vínculos.\n\n"
                "Reflexão filosófica:\n"
                "- A beleza é ponte para o afeto.\n"
                "- O gesto simples é o que sustenta o vínculo.\n\n"
                "Metáfora: cada gesto é uma semente que floresce em vínculos."
            )
        }
    },
    "Marte": {
        "technical": {
            "short": "É tempo de: agir com energia e direção.",
            "long": (
                "É tempo de: agir com energia e direção.\n\n"
                "Ações práticas:\n"
                "- Trabalhe em blocos de 25–50 minutos com foco total.\n"
                "- Registre ao final de cada bloco o que foi conquistado.\n"
                "- Use pausas conscientes para renovar a chama.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: tarefas concluídas por dia.\n"
                "- Secundária: qualidade e rapidez de seus feitos."
            )
        },
        "poetic": {
            "short": "É tempo de: acender a tocha de Marte.",
            "long": (
                "Marte é faísca que pede direção. Cada ação é uma tocha acesa no caminho.\n\n"
                "Reflexão filosófica:\n"
                "- Energia sem foco é dispersão.\n"
                "- O movimento consciente é criação.\n\n"
                "Metáfora: acender uma tocha por dia é revelar o caminho."
            )
        }
    },
    "Júpiter": {
        "technical": {
            "short": "É tempo de: expandir horizontes com prudência.",
            "long": (
                "É tempo de: expandir horizontes com prudência.\n\n"
                "Ações práticas:\n"
                "- Escolha uma área para expandir e defina metas trimestrais.\n"
                "- Experimente uma nova prática de aprendizado por 30 dias.\n"
                "- Registre insights e aplique um por semana.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: novos contatos ou conhecimentos aplicados.\n"
                "- Secundária: impacto qualitativo."
            )
        },
        "poetic": {
            "short": "É tempo de: abrir a janela de Júpiter.",
            "long": (
                "Júpiter amplia o campo de visão. Cada curiosidade é uma semente que cresce em árvore de sabedoria.\n\n"
                "Reflexão filosófica:\n"
                "- Crescer é escolher conscientemente.\n"
                "- A expansão é convite à responsabilidade.\n\n"
                "Metáfora: plantar sementes de curiosidade é ver a copa se erguer."
            )
        }
    },
    "Saturno": {
        "technical": {
            "short": "É tempo de: construir com disciplina e método.",
            "long": (
                "É tempo de: construir com disciplina e método.\n\n"
                "Ações práticas:\n"
                "- Planeje projetos com etapas claras e prazos realistas.\n"
                "- Revise progresso mensalmente e ajuste estruturas.\n"
                "- Reserve tempo para manutenção e cuidado das bases.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: cumprimento de marcos.\n"
                "- Secundária: estabilidade ao longo do tempo."
            )
        },
        "poetic": {
            "short": "É tempo de: erguer a pedra de Saturno.",
            "long": (
                "Saturno ensina que disciplina é liberdade construída. Cada compromisso é uma pedra que fortalece a obra da vida.\n\n"
                "Reflexão filosófica:\n"
                "- A disciplina é forma de cuidado.\n"
                "- O limite é espaço para crescer.\n\n"
                "Metáfora: construir devagar é garantir que a obra dure."
            )
        }
    },
    "Urano": {
        "technical": {
            "short": "Inovação, ruptura e experimentação controlada.",
            "long": (
                "Resumo: testar novas abordagens com salvaguardas.\n\n"
                "Ações recomendadas:\n"
                "- 1) Projete experimentos de baixo risco.\n"
                "- 2) Meça por aprendizado e taxa de iteração.\n"
                "- 3) Documente falhas e hipóteses para ajustar rapidamente.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: número de experimentos válidos.\n"
                "- Secundária: insights aplicáveis."
            )
        },
        "poetic": {
            "short": "Sopro de novidade e surpresa.",
            "long": (
                "Urano é vento que muda a paisagem. Permita-se um gesto inesperado que quebre a rotina e revele novas rotas.\n\n"
                "Rituais sugeridos:\n"
                "- Faça algo fora do padrão uma vez por semana.\n"
                "- Observe reações e ajuste o próximo gesto.\n\n"
                "Metáfora: um sopro que redesenha o mapa."
            )
        }
    },
    "Netuno": {
        "technical": {
            "short": "Imaginação, intuição e sensibilidade.",
            "long": (
                "Resumo: integrar intuição com práticas concretas.\n\n"
                "Ações recomendadas:\n"
                "- 1) Reserve tempo para reflexão criativa.\n"
                "- 2) Meça por ideias geradas e protótipos simples.\n"
                "- 3) Proteja-se de confusão com critérios claros de validação.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: número de ideias testadas.\n"
                "- Secundária: clareza de critérios."
            )
        },
        "poetic": {
            "short": "Névoa que revela imagens interiores.",
            "long": (
                "Netuno convoca imagens e sonhos. Use práticas de imaginação guiada para transformar intuição em gesto.\n\n"
                "Rituais sugeridos:\n"
                "- Meditação breve antes de criar.\n"
                "- Registro de sonhos ou insights por 21 dias.\n\n"
                "Metáfora: navegue a névoa com um leme de intenção."
            )
        }
    },
    "Plutão": {
        "technical": {
            "short": "Transformação profunda e reestruturação.",
            "long": (
                "Resumo: processos de eliminação e renascimento.\n\n"
                "Ações recomendadas:\n"
                "- 1) Identifique padrões a serem transformados.\n"
                "- 2) Planeje passos de desapego e reconstrução.\n"
                "- 3) Meça por mudanças estruturais e resiliência.\n\n"
                "Métricas sugeridas:\n"
                "- Primária: indicadores de mudança estrutural.\n"
                "- Secundária: recuperação pós-transformação."
            )
        },
        "poetic": {
            "short": "Subsolo que revela raízes e renovações.",
            "long": (
                "Plutão trabalha nas profundezas. Encare o processo como poda radical que permite novo crescimento.\n\n"
                "Rituais sugeridos:\n"
                "- Trabalho simbólico de liberação (escrever e queimar, por exemplo).\n"
                "- Período de reconstrução com metas pequenas e firmes.\n\n"
                "Metáfora: renascer a partir do que foi deixado para trás."
            )
        }
    },
    # fallback genérico para planetas menos comuns
    "default": {
        "technical": {
            "short": "Função planetária específica.",
            "long": (
                "Resumo: foco prático.\n\n"
                "Ações recomendadas:\n"
                "- 1) Defina objetivo claro.\n"
                "- 2) Meça progresso com indicadores simples.\n"
                "- 3) Revise periodicamente."
            )
        },
        "poetic": {
            "short": "Sopro singular que pede atenção.",
            "long": (
                "Resumo poético: atenção e ritual.\n\n"
                "Rituais sugeridos:\n"
                "- Pequeno gesto diário por 21 dias.\n"
                "- Observação e registro."
            )
        }
    }
}

def _format_aspects_summary(planet: str, aspects: Optional[List[Dict[str, Any]]]) -> Optional[str]:
    if not aspects:
        return None
    notes = []
    for a in aspects:
        if a.get("p1") == planet or a.get("p2") == planet:
            other = a["p2"] if a["p1"] == planet else a["p1"]
            notes.append(f"{a.get('type','')} com {other} (orb {a.get('orb')})")
    return "; ".join(notes) if notes else None

# util de normalização (remove acentos e normaliza caixa)
def _normalize_name(name: str) -> str:
    if not name:
        return ""
    nfkd = unicodedata.normalize("NFKD", name)
    only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return only_ascii.strip().lower()

# busca robusta por template usando nomes em português
def _get_planet_template_by_name(name: str, templates: dict):
    """
    Tenta encontrar o template correspondente ao nome do planeta.
    - Normaliza acentos e caixa.
    - Tenta correspondência exata, capitalizada e sem acento.
    - Retorna template ou templates['default'] se não achar.
    """
    if not templates:
        return None
    # normalizar todas as chaves do templates uma vez
    normalized_map = {}
    for k in templates.keys():
        normalized_map[_normalize_name(k)] = k

    # formas a testar
    candidates = [name, name.capitalize(), name.title()] if name else []
    # normalizar candidato
    norm = _normalize_name(name)
    # 1) correspondência direta normalizada
    if norm in normalized_map:
        return templates[normalized_map[norm]]
    # 2) tentar sem acento em outras formas
    for cand in candidates:
        if _normalize_name(cand) in normalized_map:
            return templates[normalized_map[_normalize_name(cand)]]
    # 3) fallback para default
    return templates.get("default")

def planet_interpretation(
    planet: str,
    sign: Optional[str] = None,
    degree: Optional[float] = None,
    house: Optional[int] = None,
    aspects: Optional[List[Dict[str, Any]]] = None,
    context_name: Optional[str] = None,
    style: str = "technical"
) -> Dict[str, str]:
    """
    Gera interpretação individual por planeta.
    style: 'technical' ou 'poetic'
    Retorna dict com 'short' e 'long'.
    """
    key = planet if planet in _PLANET_TEMPLATES else "default"
    tpl = _get_planet_template_by_name(planet, _PLANET_TEMPLATES)
    chosen = tpl.get(style, tpl.get("technical"))

    # enriquecer com sign/house/aspects quando possível
    sign_label = sign or ""
    house_label = f"Casa {house}" if house else ""
    deg_text = f"{round(float(degree),3)}°" if degree not in (None, "") else ""

    short = chosen["short"]
    # prefixar contexto se houver
    if context_name:
        short = f"{context_name}, {short}"

    long_text = chosen["long"]
    # inserir contexto adicional em final do long
    extras = []
    if deg_text:
        extras.append(f"Grau: {deg_text}.")
    if sign_label:
        sign_quality = ""
        try:
            sign_quality = SIGN_DESCRIPTIONS.get(sign_label, ("", ""))[1].split(",")[0].lower()
        except Exception:
            sign_quality = ""
        if sign_quality:
            extras.append(f"Em {sign_label}, a expressão tende a {sign_quality}.")
    if house:
        try:
            house_theme = HOUSE_DESCRIPTIONS.get(house, (f"Casa {house}", ""))[1].split(",")[0].lower()
            extras.append(f"No âmbito da casa {house}, foco em {house_theme}.")
        except Exception:
            pass
    aspect_line = _format_aspects_summary(planet, aspects)
    if aspect_line:
        extras.append(f"Aspectos relevantes: {aspect_line}.")

    if extras:
        long_text = f"{long_text}\n\n" + " ".join(extras)

    return {"short": short, "long": long_text}

def _info_from_summary(pname: str, summary: Optional[Dict]) -> Tuple[Optional[str], Optional[float], Optional[int], Optional[List[Dict[str, Any]]]]:
    if not summary:
        return None, None, None, None
    readings = summary.get("readings") or {}
    planets_map = summary.get("planets") or {}
    # tentar variantes
    r = readings.get(pname) or readings.get(pname.capitalize()) or planets_map.get(pname) or planets_map.get(pname.capitalize())
    if not r:
        # tentar aliases
        r = _find_in_mapping(readings, pname) or _find_in_mapping(planets_map, pname) # type: ignore
    if not r:
        return None, None, None, None
    sign = r.get("sign")
    degree = r.get("degree") or r.get("deg") or r.get("longitude")
    house = r.get("house")
    try:
        house = int(float(house)) if house not in (None, "", "None") else None
    except Exception:
        house = None
    aspects = summary.get("aspects")
    return sign, degree, house, aspects

def generate_three_interpretations(planet_ast, planet_teo, planet_35, summary=None):
    def _info(pname):
        if not summary:
            return None, None, None, None
        readings = summary.get("readings") or {}
        planets_map = summary.get("planets") or {}
        r = readings.get(pname) or readings.get(pname.capitalize()) or planets_map.get(pname) or planets_map.get(pname.capitalize())
        if not r:
            return None, None, None, None
        sign = r.get("sign")
        degree = r.get("degree") or r.get("deg") or r.get("longitude")
        house = r.get("house")
        try:
            house = int(float(house)) if house not in (None, "", "None") else None
        except Exception:
            house = None
        aspects = summary.get("aspects")
        return sign, degree, house, aspects

    s_ast, d_ast, h_ast, a_ast = _info(planet_ast)
    s_teo, d_teo, h_teo, a_teo = _info(planet_teo)
    s_35, d_35, h_35, a_35 = _info(planet_35)

    interp_ast = planet_interpretation(planet_ast, sign=s_ast, degree=d_ast, house=h_ast, aspects=a_ast, style="technical")
    interp_teo = planet_interpretation(planet_teo, sign=s_teo, degree=d_teo, house=h_teo, aspects=a_teo, style="technical")
    interp_35 = planet_interpretation(planet_35, sign=s_35, degree=d_35, house=h_35, aspects=a_35, style="poetic")

    return interp_ast, interp_teo, interp_35