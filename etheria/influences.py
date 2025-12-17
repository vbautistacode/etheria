# etheria/influences.py
"""
Módulo de Influências Tattvicas (refatorado)

Principais objetivos:
- Usar nomes canônicos internamente (Sun, Moon, Mercury, Venus, Mars, Jupiter, Saturn)
- Aceitar entradas em português (Lua, Sol, Mercúrio, etc.) e mapear automaticamente
- Retornar estruturas (dicts) em vez de strings quando útil (facilita i18n e testes)
- Isolar dependência de pandas (planet_from_matrix aceita DataFrame ou dict)
"""

from typing import List, Dict, Optional, Any, Tuple, Union
from datetime import date
import pandas as pd

from .utils import age_from_dob

# -------------------------
# Mapeamentos de nomes
# -------------------------
# canonical names (internos)
from typing import Dict, List, Optional
import unicodedata

# canonical names in English (internal)
CANONICAL_PLANETS: List[str] = [
    "Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"
]

# raw PT variants (human-friendly) -> canonical (EN)
_raw_pt_to_canonical = {
    "Sol": "Sun",
    "Lua": "Moon",
    "Mercúrio": "Mercury",
    "Mercurio": "Mercury",
    "Vênus": "Venus",
    "Venus": "Venus",
    "Marte": "Mars",
    "Júpiter": "Jupiter",
    "Jupiter": "Jupiter",
    "Saturno": "Saturn",
    "Urano": "Uranus",
    "Netuno": "Neptune",
    "Plutão": "Pluto",
    "Plutao": "Pluto",
}

def _strip_accents(s: str) -> str:
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nkfd if not unicodedata.combining(ch))

def _norm_key(s: str) -> str:
    return _strip_accents(s).strip().lower()

# normalized PT -> canonical mapping (keys are lower/no-accent)
PT_TO_CANONICAL: Dict[str, str] = {_norm_key(k): v for k, v in _raw_pt_to_canonical.items()}

# explicit canonical -> PT labels for UI
CANONICAL_TO_PT: Dict[str, str] = {
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

def to_canonical(name: Optional[str]) -> Optional[str]:
    """Return canonical English name. Accepts PT/EN, with/without accents, any case."""
    if not name:
        return None
    s = str(name).strip()
    # if already canonical (case-insensitive)
    for can in CANONICAL_PLANETS:
        if can.lower() == s.lower():
            return can
    # normalized lookup PT -> EN
    key = _norm_key(s)
    if key in PT_TO_CANONICAL:
        return PT_TO_CANONICAL[key]
    # fallback: return original string (or raise if you prefer strictness)
    return s

# -------------------------
# Convenções de ciclo (usando nomes canônicos)
# -------------------------
PLANET_ORDER: List[str] = ["Moon", "Mercury", "Venus", "Sun", "Mars", "Jupiter", "Saturn"]
PLANET_YEARS: Dict[str, int] = {
    "Moon": 10,
    "Mercury": 8,
    "Venus": 4,
    "Sun": 3,
    "Mars": 2,
    "Jupiter": 7,
    "Saturn": 6,
}

DEFAULT_WEIGHTS: Dict[str, int] = {"year": 3, "hour": 2, "weekday": 1}

PHASES: List[Tuple[str, int, int]] = [
    ("Física", 0, 39),
    ("Psíquica", 40, 79),
    ("Espiritual", 80, 120)
]

# -------------------------
# Textos interpretativos (chaves em canonical)
# -------------------------
PLANET_TO_TATWA: Dict[str, str] = {
    "Lua": "Apas",
    "Mercúrio": "Anupádaka",
    "Vênus": "Akasha",
    "Sol": "Prithvi",
    "Marte": "Tejas",
    "Júpiter": "Adi",
    "Saturno": "Vayu",
}

# manter textos originais, mas indexados por canonical
PLANET_TEXTS: Dict[str, Dict[str, str]] = {
    "Lua": {
        "title": "Lua — Apas",
        "summary": "Emoção, sensibilidade, intuição; assuntos passageiros, família.",
        "long": (
            "A LUA refere-se aos assuntos de popularidade e vulgaridade. Rápida e mutável como é, diz respeito a tudo que é "
            "passageiro e inconstante. Deste modo, fornece uma disposição inquieta, volúvel, um temperamento apreciador de tudo "
            "que é mutável, como das viagens. Assim como o Sol representa a vida, a Lua diz respeito à alma passional, com toda a "
            "sua “fluidez” característica do Elemento Água. A Lua diz respeito em especial à mulher, à mãe, à concepção, à fertilidade; "
            "ela determina a intensidade das paixões e dos desejos passageiros. Ao mesmo tempo a Lua faz surgir na alma os sonhos, a "
            "imaginação, as ilusões, as esperanças, e também a loucura. As vibrações do Tattwa da Lua favorecem as viagens curtas, mudanças "
            "transitórias; é uma boa hora para convencer os outros de alguma nova idéia. É favorável a todos os indivíduos que trabalham "
            "com líquidos: pescadores, marinheiros, leiteiros, etc.; nesta hora não se deve iniciar nada que deva ter longa duração ou que "
            "exija esforços continuados. É associada com o sistema alimentar, incluindo o esôfago, estomago, fígado, vesícula, pâncreas e "
            "intestinos. Está, portanto, intimamente ligada à dieta; relaciona-se também com os seios (regidos em geral por Câncer). "
            "Qualidades: Mãe, mulheres em geral, esposa, rainha, líquidos, imaginação, impressionabilidade, mediunidade, duplo etérico, alma, crendices, "
            "lar, família, sonhador, inconstância, hereditariedade, etc."
        ),
        "advice": (
            "Práticas de respiração e estabilização emocional; evitar iniciar projetos de longa duração em horas lunares; "
            "cuidar da dieta e rotinas alimentares; favorecer atividades ligadas a líquidos e ao cuidado."
        )
    },
    "Mercúrio": {
        "title": "Mercúrio — Anupádaka",
        "summary": "Atividade mental, memória, estudos, comunicação, comércio.",
        "long": (
            "MERCÚRIO diz respeito, principalmente, à atividade mental, à memória, aos estudos. Mercúrio dá uma disposição eloqüente, "
            "prolixa, e também sofística, intrusa e impertinente. Fornece um temperamento fácil de se adaptar, porque vive essencialmente "
            "de aparências. Por ter relação com o intelecto, dá aos seres o temperamento “frio”, que resolve tudo pela razão e não com o "
            "calor da alma. Por tudo isto favorece muita a profissão do comerciante. A hora de Mercúrio é própria para os assuntos que requerem "
            "expressão literária, verbal ou escrita, tais como escrever cartas, documentos, trabalhos literários, discursos, conferências, aulas, "
            "etc., por isto que também é favorável para tratar com professores, escritores e todos os que se ocupam com empresas literárias e jornalísticas. "
            "Qualidades: Irmãos, comércio, intelecto, estudo, praticidade, viagem, roubo, mentira, mensageiro, falar, escrever, curso, publicação, telefone, livro, raciocínio, etc. "
            "O cérebro e o sistema nervoso como um todo são regidos por Mercúrio, que exerce influências também na maneira pela qual respiramos."
        ),
        "advice": (
            "Aproveitar horas de Mercúrio para estudo, escrita, comunicação e negociações; exercícios de concentração; atenção à clareza na fala e documentos."
        )
    },
    "Vênus": {
        "title": "Vênus — Akasha",
        "summary": "Beleza, artes, vida social, afeto, estética.",
        "long": (
            "VÊNUS representa o aspecto belo da existência, as artes, a alegria, a vida social, as coisas supérfluas. Vênus cria a ordem, a harmonia; "
            "fornece os temperamentos artísticos, quer como criadores de novas formas de expressão estética, quer como os grandes intérpretes da arte. "
            "A hora do Tattwa de Vênus favorece as alegrias, as reuniões sociais e artísticas, as diversões, a dança, os concertos; é a hora favorável "
            "às exibições de vestuários, de ornamentos, de luxo, e por isto, também própria para a aquisição desses objetos, jóias, etc. Qualidades: Estética, beleza, afeto, "
            "união, casamento, mulheres em geral, festas, luxuria, charme, canto, amor, jóia, dança, elegância, dinheiro, arte, etc. As paratireóides, que controla o nível "
            "de cálcio nos fluidos do corpo, são regidas por Vênus que tradicionalmente é relacionado com a garganta, rins e região lombar."
        ),
        "advice": (
            "Favorecer atividades artísticas e sociais; aproveitar para negociações relacionadas a estética, moda e bens de luxo; cuidar da garganta e rins."
        )
    },
    "Sol": {
        "title": "Sol — Prithvi",
        "summary": "Vitalidade, vontade, autoridade, criatividade.",
        "long": (
            "O SOL é o distribuidor da vida. Representa, pois, no homem, sua saúde geral e sua vitalidade; indica a força de vontade e o idealismo. Dá uma disposição magnânima "
            "e um espírito compreensivo. Relaciona-se com tudo o que de nobre há na vida e na natureza. É o centro motor, a causa da ação, o que dá impulso às realizações. "
            "As influências do Sol fornecem qualidades de sinceridade, confiança e franqueza, constância, firmeza e justiça. A hora em que vibra o Tattwa Solar é especialmente "
            "próprio para manter relações com pessoas de posição firme e elevada, com as autoridades, juizes, chefes de empresas distribuidoras de mercadorias e pedir os seus préstimos. "
            "Qualidades: Autoridade, realeza, Pai, glória, tudo que brilha, honra, rei, dirigente, palácio, ouro, teatro, vigor, criatividade, etc. é particularmente associado com o timo, "
            "embora também governe (tradicionalmente) o coração, costas e coluna vertebral."
        ),
        "advice": (
            "Usar horas solares para iniciativas que exijam autoridade, visibilidade e liderança; cuidar da vitalidade e postura; buscar apoio de figuras de autoridade."
        )
    },
    "Marte": {
        "title": "Marte — Tejas",
        "summary": "Ação, luta, energia, coragem, risco.",
        "long": (
            "MARTE é o Planeta da violência, da luta. É o grande exaltador. É o espírito das explosões, dos entusiasmos. Fornece os temperamentos belicosos, lutadores, os conquistadores, "
            "quer sejam conquistadores militares, pela força, quer os conquistadores pela mente, os cientistas, pesquisadores. Favorece as profissões que dizem respeito as violências, tais como "
            "fabricantes de armas, ferreiros, instrumentos cirúrgicos, cirurgiões, etc. As influências de Marte são avassaladoras, arrastam todos os obstáculos; não admite perda de tempo, não faz considerações. "
            "Marte representa o poder criador que antes tem de destruir; é o realizador por excelência, em todos os ramos da atividade. As horas do Tatwa são próprias para as realizações temerosas, empresas ousadas, "
            "para travar lutas e abrir questões; esta hora leva ao impulso irresponsável. Assim, não se deve tratar nesta hora de assuntos que exigem ponderação, calma, diplomacia e argumentação; evite-se realizações de risco. "
            "No entanto, a hora de Marte é própria pra negócios relativos a coisas brutas, como mecânicos, fundição, minas, materiais pesados, industria extrativa, etc. Qualidades: Cirurgia, luta, exército, esporte, raiva, ataque, competição, "
            "assassino, soldado, crime, perigo, instrumento cortante, míssil, incêndio, violência, guerra, paixão, sexo, energia, bomba, etc. é tradicionalmente um planeta de violência, mas é relacionado também com o sexo: não é de surpreender, "
            "portanto, sua ligação com as glândulas sexuais (gônadas), e também com o sistema muscular em geral."
        ),
        "advice": (
            "Evitar decisões impulsivas em horas de Marte; usar para ações que exijam coragem e energia; precaução em atividades de risco; atenção à saúde muscular e sexual."
        )
    },
    "Júpiter": {
        "title": "Júpiter — Adi",
        "summary": "Sabedoria, expansão, ensino, estabilidade de longo prazo.",
        "long": (
            "JÚPITER caracteriza a ponderação, a sabedoria interior, a mística elevada. Suas vibrações fornecem o temperamento do juiz, do religioso, do sacerdote, do ministro, do professor universitário, "
            "enfim, a autoridade em qualquer ramo, com todos os seus característicos, como a serenidade, a decisão, a austeridade. Pode também, em seu aspecto inferior, representar o conservador, o reacionário, o dogmático. "
            "A hora de Júpiter é favorável ao começo de qualquer nova empresa, principalmente as permanentes ou de longa duração, em virtude da firmeza serena que caracteriza este Planeta, e de sua fecundidade, como resultado favorável de qualquer negócio. "
            "Júpiter preside as posses materiais e a solidez moral. É favorável a solicitação de proteção e favores.Qualidades: Religião, leis, universidades, filosofias, valores éticos, sacerdote, guru, professor, juiz, fórum, filantropia, protetor, ritual, cerimônia, fortuna, estrangeiro, etc. "
            "O relacionamento de Júpiter com o fígado e sua função digestiva, mas afeta também a glândula pituitária, que regula a produção de hormônios e governa nosso desenvolvimento físico."
        ),
        "advice": (
            "Usar horas de Júpiter para iniciar projetos duradouros, estudos superiores e pedidos de proteção; cultivar práticas de longo prazo e ensino."
        )
    },
    "Saturno": {
        "title": "Saturno — Vayu",
        "summary": "Perseverança, responsabilidade, estrutura, provas e limitações.",
        "long": (
            "SATURNO significa a experiência sólida, a abnegação, a responsabilidade; fornece o temperamento melancólico que pode se tornar avaro, miserável, ou elevar-se ao pícaro do saber profundo e místico. Saturno é o Planeta que dá força ao destino, que precipita os efeitos, por isto que é considerado como violento e mau, embora as causas não tenham sido por ele geradas; é o Planeta que recolhe o que foi deixado pelos outros; é o que faz ressaltar os obstáculos, mas também é o que não esquece de premiar as boas ações semeadas. Saturno não permite que fique nada por fazer; ele é o grande redutor universal. Saturno dá ao ser um temperamento laborioso, tenaz, critico e desconfiado; favorece os filósofos incompreendidos, quer sejam místicos espirituais, quer ateus materialistas. A hora de Saturno favorece o trato com assuntos de natureza durável e sólida, as terras, as construções e tudo o que exige tempo, perseverança e paciência, como a agricultura. Tudo o que se inicia nesta hora desenvolve-se devagar, sofre atrasos, encontra obstáculos; por isto não é própria para assuntos que requerem rápida conclusão, inclusive reuniões sociais, viagens rápidas e tratamentos médicos. É boa hora para travar relações e negócios com pessoas ligadas aos assuntos de Saturno. Qualidades: Austeridade, avareza, medo, agricultura, sofrimento, isolamento, calamidade, conservador, cronômetro, desastre, responsabilidade, duro, gelo, limitação, morte, trabalhador, depressão, minas, miséria, velhice, rocha, etc. Os dentes e ossos são regidos por Saturno, que se relaciona também com a vesícula e baço e com a pele. Age sobre o lóbulo anterior da glândula pituitária, regulando a estrutura óssea e muscular das glândulas sexuais."
        ),
        "advice": (
            "Planejar a longo prazo, cultivar disciplina e paciência; evitar iniciar projetos que exijam rapidez; cuidar de ossos e dentes; aceitar provas como aprendizado."
        )
    }
}

# -------------------------
# Funções de ciclo e utilitários
# -------------------------
def build_major_cycles(birth_year: int, max_age: int = 120, start_planet: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Gera lista de blocos sequenciais (planet, start_year, end_year, start_age, end_age)
    usando nomes canônicos. start_planet aceita canonical ou PT.
    """
    if start_planet:
        start_planet = _to_canonical(start_planet)
    if start_planet and start_planet not in PLANET_ORDER:
        raise ValueError(f"start_planet '{start_planet}' não está em PLANET_ORDER")

    if start_planet:
        start_idx = PLANET_ORDER.index(start_planet)
        order = PLANET_ORDER[start_idx:] + PLANET_ORDER[:start_idx]
    else:
        order = PLANET_ORDER.copy()

    cycles: List[Dict[str, Any]] = []
    age = 0
    year = birth_year
    i = 0

    while age <= max_age:
        planet = order[i % len(order)]
        dur = int(PLANET_YEARS.get(planet, 1))
        start_year = year
        end_year = year + dur - 1
        start_age = age
        end_age = age + dur - 1

        cycles.append({
            "planet": planet,
            "start_year": start_year,
            "end_year": end_year,
            "start_age": start_age,
            "end_age": end_age
        })

        year = end_year + 1
        age = end_age + 1
        i += 1

    return cycles


def planet_for_year(cycles: List[Dict[str, Any]], year: int) -> Optional[str]:
    for c in cycles:
        if c["start_year"] <= year <= c["end_year"]:
            return c["planet"]
    return None


def planet_for_age(cycles: List[Dict[str, Any]], age: int) -> Optional[str]:
    for c in cycles:
        if c["start_age"] <= age <= c["end_age"]:
            return c["planet"]
    return None


def phase_for_age(age: int) -> str:
    for name, start, end in PHASES:
        if start <= age <= end:
            return name
    return PHASES[-1][0]


# -------------------------
# Extração a partir da matriz Hora x Dia
# -------------------------
def _hour_bucket(hhmm: str) -> str:
    try:
        hh = int(str(hhmm).split(":")[0])
        return f"{hh:02d}:00"
    except Exception:
        return str(hhmm)


def planet_from_matrix(mat: Union[pd.DataFrame, Dict[str, Dict[str, str]]], weekday: str, hhmm: str) -> Optional[str]:
    """
    mat: pd.DataFrame index=Hour 'HH:MM', columns=Weekday (em português) OR
         dict-of-dicts {hour_bucket: {weekday: planet_pt_or_canonical}}
    weekday: ex 'Quarta-feira' ou 'quarta-feira' (coluna do DataFrame ou chave do dict)
    hhmm: '07:55' -> mapeia para '07:00'
    Retorna planeta em canonical name (ex: 'Moon') ou None.
    """
    bucket = _hour_bucket(hhmm)

    # DataFrame path
    if isinstance(mat, pd.DataFrame):
        if weekday not in mat.columns:
            return None
        if bucket not in mat.index:
            try:
                hour = int(bucket.split(":")[0])
                idxs = [int(i.split(":")[0]) for i in mat.index if ":" in i]
                if not idxs:
                    return None
                closest = min(idxs, key=lambda x: abs(x - hour))
                bucket = f"{closest:02d}:00"
            except Exception:
                return None
        val = mat.at[bucket, weekday]
        if pd.isna(val):
            return None
        return _to_canonical(str(val))

    # dict-of-dicts path
    if isinstance(mat, dict):
        row = mat.get(bucket)
        if not row:
            # tentar aproximar por hora
            try:
                hour = int(bucket.split(":")[0])
                keys = [k for k in mat.keys() if ":" in k]
                if not keys:
                    return None
                idxs = [int(k.split(":")[0]) for k in keys]
                closest = min(idxs, key=lambda x: abs(x - hour))
                bucket = f"{closest:02d}:00"
                row = mat.get(bucket)
            except Exception:
                return None
        if not row:
            return None
        val = row.get(weekday) or row.get(weekday.capitalize()) or row.get(weekday.lower())
        if not val:
            return None
        return _to_canonical(str(val))

    return None


# -------------------------
# Combinação de fontes e interpretação
# -------------------------
def combine_sources(sources: Dict[str, Optional[str]], weights: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    sources: {"year": "Lua" or "Moon", "hour": "Lua", "weekday": "Mercúrio"}
    Retorna: {"tally": {...}, "dominant": canonical_name_or_None, "scores": {...}}
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS
    tally: Dict[str, int] = {}
    scores: Dict[str, int] = {}
    for key, planet in sources.items():
        if not planet:
            continue
        can = _to_canonical(planet)
        w = int(weights.get(key, 1))
        scores[key] = w
        tally[can] = tally.get(can, 0) + w
    if not tally:
        return {"tally": {}, "dominant": None, "scores": scores}
    dominant = max(tally.items(), key=lambda x: x[1])[0]
    return {"tally": tally, "dominant": dominant, "scores": scores}


def _format_block(planet: Optional[str]) -> Dict[str, str]:
    """
    Retorna bloco estruturado com title/summary/advice para um planeta canonical.
    """
    if not planet:
        return {"title": "", "summary": "", "advice": ""}
    ptext = PLANET_TEXTS.get(planet, {})
    return {
        "title": ptext.get("title", CANONICAL_TO_PT.get(planet, planet)),
        "summary": ptext.get("summary", ""),
        "advice": ptext.get("advice", "")
    }


def render_short(planet: Optional[str]) -> str:
    """Mantém compatibilidade: retorna string curta formatada (PT)."""
    if not planet:
        return "Nenhum planeta dominante identificado."
    block = _format_block(planet)
    tatwa = PLANET_TO_TATWA.get(planet, "—")
    return f"Planeta dominante: {CANONICAL_TO_PT.get(planet, planet)}. Tatwa: {tatwa}. Tema: {block['summary']}"


def render_medium(planet: Optional[str], sources: Dict[str, Optional[str]]) -> str:
    if not planet:
        return "Nenhum planeta dominante identificado."
    block = _format_block(planet)
    srcs = ", ".join([f"{k}={v or '—'}" for k, v in sources.items()])
    return f"O planeta predominante é {CANONICAL_TO_PT.get(planet, planet)} (tatwa {PLANET_TO_TATWA.get(planet)}). Isso indica ênfase em: {block['summary']} Recomendações: {block['advice']}"


def render_long(planet: Optional[str], sources: Dict[str, Optional[str]], cycles: List[Dict[str, Any]], birth_year: int, birth_age: int) -> str:
    if not planet:
        return "Nenhum planeta dominante identificado."
    ptext = PLANET_TEXTS.get(planet, {})
    phase = phase_for_age(birth_age)
    advice = ptext.get("advice", "")
    return f"{ptext.get('long','')}\n\nFase atual: {phase} (idade {birth_age}). Recomendações práticas: {advice}"


def interpret_combined(sources: Dict[str, Optional[str]], cycles: Optional[List[Dict[str, Any]]] = None,
                       birth_year: Optional[int] = None, birth_age: Optional[int] = None,
                       weights: Optional[Dict[str, int]] = None) -> Dict[str, Any]:
    """
    Fluxo completo: combina fontes, identifica dominante e retorna interpretações em 3 níveis.
    Retorna dicionário com keys: sources, combined, dominant (canonical), tatwa, phase, interpretation:{short,medium,long}
    """
    combined = combine_sources(sources, weights=weights)
    dominant = combined.get("dominant")
    # calcular birth_age se não fornecido e birth_year disponível
    if birth_age is None and birth_year is not None:
        # tentativa simples: usar birth_year -> age aproximada (ano atual - birth_year)
        from datetime import date
        birth_age = date.today().year - int(birth_year)
    birth_age = int(birth_age or 0)
    short = render_short(dominant)
    medium = render_medium(dominant, sources)
    long_text = render_long(dominant, sources, cycles or [], birth_year or 0, birth_age)
    tatwa = PLANET_TO_TATWA.get(dominant)
    phase = phase_for_age(birth_age)
    return {
        "sources": sources,
        "combined": combined,
        "dominant": dominant,
        "tatwa": tatwa,
        "phase": phase,
        "interpretation": {
            "short": short,
            "medium": medium,
            "long": long_text
        }
    }