# etheria/astrology.py
from typing import Optional, Tuple
from typing import Dict, Any, List
from typing import Iterable
import unicodedata
import math

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

# Planeta -> (Verbo, Significado central)
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

# Signo -> (Substantivo, Qualidade central)
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

# Casas: número -> (Substantivo, Tema)
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

PLANET_ORDER = ["Sun", "Moon", "Mercury", "Venus", "Mars", "Jupiter", "Saturn", "Uranus", "Neptune", "Pluto"]

def lon_to_sign_degree(lon: float) -> Tuple[str, float, int]:
    """
    Converte longitude (0..360) e retorna (sign_name, degree_in_sign, sign_index 1..12).
    """
    lon = float(lon) % 360.0
    sign_index = int(lon // 30) % 12
    degree = lon % 30
    return SIGNS[sign_index], round(degree, 2), sign_index + 1

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
    """
    Converte posições em tabela legível: planeta, longitude, sign, degree, sign_index, house.
    - planets: mapa { "Sun": {"longitude": 123.4, "house": 10}, ... } ou { "Sun": 123.4, ... }
    - cusps: lista de 12 longitudes (0..360) para cálculo de casas; se None, usa house já presente em planets
    - compute_house_if_missing: se True, tenta calcular house a partir de cusps quando house ausente
    Retorna lista de rows com chaves: planet, longitude, sign, degree, sign_index, house
    """
    rows: List[Dict[str, Any]] = []

    # normalizar cusps (garantir floats 0..360) ou None
    norm_cusps: Optional[List[float]] = None
    if cusps and isinstance(cusps, (list, tuple)) and len(cusps) >= 12:
        try:
            norm_cusps = [float(c) % 360.0 for c in cusps[:12]]
        except Exception:
            norm_cusps = None

    # ordenar por PLANET_ORDER se possível
    keys = list(planets.keys())
    try:
        keys_sorted = sorted(keys, key=lambda k: PLANET_ORDER.index(k) if k in PLANET_ORDER else 999)
    except Exception:
        keys_sorted = keys

    for name in keys_sorted:
        v = planets.get(name, {})
        # extrair longitude de forma robusta
        lon = None
        if isinstance(v, dict):
            # aceitar chaves comuns
            for key in ("longitude", "lon", "long", "deg", "degree"):
                if key in v and v.get(key) not in (None, ""):
                    try:
                        lon = float(v.get(key))
                        break
                    except Exception:
                        continue
        else:
            # v pode ser número direto
            try:
                lon = float(v)
            except Exception:
                lon = None

        if lon is None:
            # sem longitude, pular
            continue

        # garantir 0..360
        lon = float(lon) % 360.0

        # signo, grau e índice do signo
        sign, degree, sign_index = lon_to_sign_degree(lon)

        # determinar house: priorizar valor já presente em v, senão calcular se cusps disponíveis
        house = None
        if isinstance(v, dict):
            # aceitar house já presente (int/str/float)
            h_raw = v.get("house")
            if h_raw not in (None, "", "None"):
                try:
                    house = int(float(h_raw))
                except Exception:
                    house = None

        # se não houver house e for permitido, calcular a partir de cusps normalizados
        if house is None and compute_house_if_missing and norm_cusps:
            try:
                calc = get_house_for_longitude(lon, norm_cusps)
                house = int(calc) if calc else None
            except Exception:
                house = None

        rows.append({
            "planet": name,
            "longitude": round(float(lon), 2),
            "sign": sign,
            "degree": round(degree, 2),
            "sign_index": sign_index,
            "house": house
        })

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

def _house_text(house: Optional[int]) -> Tuple[str, str]:
    """Retorna descrição da casa; se None, retorna vazio."""
    if not house:
        return ("Casa desconhecida", "")
    return HOUSE_DESCRIPTIONS.get(house, (f"Casa {house}", "Tema da casa"))

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
    - planet: nome canonical (ex: 'Moon', 'Sun')
    - sign: nome do signo (ex: 'Taurus')
    - degree: grau dentro do signo
    - house: número da casa (1..12) ou None
    - aspects: lista de aspectos (opcional) para incluir observações
    - context_name: nome do consulente para personalizar o texto (opcional)

    Retorna dict: {"short": "...", "long": "..."}
    """
    verb, pcore = _planet_core_text(planet)
    sign_noun, sign_quality = _sign_text(sign or "")
    house_noun, house_theme = _house_text(house)

    deg_text = _format_degree(degree)
    who = f"{context_name}, " if context_name else ""

    # Short: 1-2 frases
    short = (
        f"{who}{planet} em {sign or '—'} {deg_text} fala sobre {pcore.lower()} conectando {sign_quality.lower()}. "
        f"Resumo prático: {verb.lower()} no campo do(a) {house_noun.lower()}."
    )

    # Long: 3-5 parágrafos curtos
    long_parts = []

    # Parágrafo 1: síntese funcional
    p1 = (
        f"{planet} representa a(o)  {pcore.lower()}. Em {sign or '—'}, traz a ideia de {sign_quality.lower()}. "
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

    # Parágrafo 3: aspectos (se houver)
    if aspects:
        rel = []
        for a in aspects:
            if a.get("p1") == planet or a.get("p2") == planet:
                other = a["p2"] if a["p1"] == planet else a["p1"]
                rel.append(f"{a['type'].lower()} com {other} (orb {a.get('orb')})")
        if rel:
            p3 = "Aspectos relevantes: " + "; ".join(rel) + "."
        else:
            p3 = "Não há aspectos maiores registrados que modifiquem substancialmente esta leitura."
    else:
        p3 = "Sem dados de aspectos, considere que a leitura é focal e direta."
    long_parts.append(p3)

    # Parágrafo 4: recomendações práticas
    # proteger caso sign_quality seja vazio
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

# templates por planeta: cada entrada tem 'technical' e 'poetic' strings ou lambdas
_PLANET_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "Sun": {
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
    "Moon": {
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
    "Mercury": {
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
    "Venus": {
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
    "Mars": {
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
    "Jupiter": {
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
    "Saturn": {
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
    "Uranus": {
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
    "Neptune": {
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
    "Pluto": {
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
        r = _find_in_mapping(readings, pname) or _find_in_mapping(planets_map, pname)
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