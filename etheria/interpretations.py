# etheria/interpretations.py
"""
Módulo de interpretações textuais (camada de orquestração).

Responsabilidades:
- Fornecer interpretações clássicas por planeta (curta/longa) usando `summary` gerado pelo pipeline.
- Fornecer interpretação do Arcano associada a um planeta, incluindo influência sobre a casa (usa `influences` + `rules`).
- Gerar interpretação completa a partir de uma leitura numerológica (mantém templates de arcanos).
"""

from typing import Dict, Optional, Any, List
import textwrap

from . import rules, influences, astrology

# -------------------------
# Templates embutidos (curtos e longos) para arcanos
# (mantidos aqui para geração direta quando necessário)
# -------------------------
# -------------------------
# Templates embutidos (curtos e longos)
# -------------------------
BASE_TEMPLATES: Dict[str, Dict[str, str]] = {
    "21": {
        "short": "{name}, o Arcano 21 (O Louco) aponta para começos inesperados e um chamado à confiança.",
        "long": (
            "{name}, o Arcano 21 (O Louco) simboliza o impulso primordial de partir rumo ao desconhecido. "
            "Este arcano fala de liberdade, espontaneidade e do risco criativo que antecede toda forma. "
            "Quando o Louco aparece como referência pessoal, há um convite para soltar certezas que já não servem, "
            "experimentar sem garantias e confiar na intuição. Em termos práticos, isso pode significar iniciar um projeto sem roteiro completo, "
            "aceitar mudanças abruptas ou permitir-se errar como forma de aprendizado. O desafio associado é a falta de ancoragem: "
            "evite decisões impulsivas sem avaliar consequências básicas. Recurso: cultivar pequenos rituais de aterramento (respiração, rotina matinal) "
            "que permitam agir com coragem sem perder a estabilidade."
        )
    },
    "1": {
        "short": "{name}, o Arcano 1 (O Mago) indica início, astúcia e capacidade de manifestar.",
        "long": (
            "{name}, o Arcano 1 (O Mago) representa a ponte entre intenção e forma. É o arquétipo da habilidade de transformar ideias em realidade "
            "usando ferramentas, foco e vontade. Quando este arcano é central, você dispõe de recursos internos e externos para materializar objetivos: "
            "clareza mental, comunicação eficaz e habilidade técnica. Prática recomendada: definir um objetivo pequeno e aplicar um método simples para alcançá‑lo, "
            "avaliando resultados e ajustando. O desafio é a dispersão ou o uso de talento para fins superficiais; mantenha a ética e a coerência entre intenção e ação."
        )
    },
    "2": {
        "short": "{name}, o Arcano 2 (A Sacerdotisa) fala de interioridade, intuição e mistério.",
        "long": (
            "{name}, o Arcano 2 (A Sacerdotisa) convida à profundidade e à escuta do inconsciente. Este arcano aponta para processos internos, sonhos, símbolos e "
            "sabedoria que não se revela por força, mas por atenção paciente. Em prática, favorece meditação, estudo contemplativo e o cultivo da sensibilidade. "
            "A Sacerdotisa protege segredos e pede discrição: nem tudo precisa ser exposto. O desafio é a passividade excessiva ou o isolamento; equilibre a interioridade "
            "com momentos de expressão seletiva. Recurso: manter um diário de sonhos e insights para transformar intuição em orientação prática."
        )
    },
    "3": {
        "short": "{name}, o Arcano 3 (A Imperatriz) traz criatividade, afeto e prosperidade.",
        "long": (
            "{name}, o Arcano 3 (A Imperatriz) celebra fertilidade, cuidado e a capacidade de gerar formas belas e nutritivas. É o arquétipo da abundância criativa: "
            "produção artística, cultivo de relacionamentos e prosperidade material que nasce do cuidado. Quando presente, favorece projetos que envolvem estética, "
            "nutrição e acolhimento. Prática: dedicar tempo ao cultivo (jardim, arte, relações) e observar como o cuidado gera retorno. O desafio é o apego ao conforto "
            "ou a tendência a superproteger; exercite generosidade e delegação."
        )
    },
    "4": {
        "short": "{name}, o Arcano 4 (O Imperador) aponta para estrutura, lei e liderança.",
        "long": (
            "{name}, o Arcano 4 (O Imperador) representa ordem, responsabilidade e a construção de alicerces duráveis. É o princípio da autoridade legítima, "
            "da disciplina e da organização. Quando este arcano é central, é tempo de planejar, estabelecer limites e criar estruturas que sustentem crescimento. "
            "Prática: elaborar um plano com etapas e prazos, delegar funções e revisar processos. O desafio é a rigidez e o autoritarismo; combine firmeza com flexibilidade."
        )
    },
    "5": {
        "short": "{name}, o Arcano 5 (O Papa) fala de tradição, ensino e mediação espiritual.",
        "long": (
            "{name}, o Arcano 5 (O Papa) simboliza a ponte entre o humano e o sagrado por meio de rituais, ensinamentos e códigos. Favorece estudo sistemático, orientação "
            "e participação em comunidades de sentido. Quando presente, há benefício em buscar mentoria, aprofundar práticas espirituais ou compartilhar conhecimento. "
            "O desafio é o dogmatismo: evite aceitar verdades prontas sem investigação pessoal. Recurso: questionar com respeito e integrar ensinamentos à experiência direta."
        )
    },
    "6": {
        "short": "{name}, o Arcano 6 (O Enamorado) destaca escolhas, afetos e compromisso.",
        "long": (
            "{name}, o Arcano 6 (O Enamorado) centra-se nas decisões que envolvem o coração e os valores. Mais do que romance, fala de alinhamento entre desejo e ética, "
            "parcerias e a responsabilidade afetiva. Quando este arcano aparece, surgem encruzilhadas que pedem escuta do que é realmente importante. Prática: mapear opções e avaliar consequências emocionais. "
            "O desafio é a indecisão ou a busca de aprovação externa; cultive clareza sobre seus valores antes de escolher."
        )
    },
    "7": {
        "short": "{name}, o Arcano 7 (O Carro) indica vitória, direção e controle.",
        "long": (
            "{name}, o Arcano 7 (O Carro) é o arquétipo da conquista orientada: disciplina, foco e habilidade de manter o rumo apesar de obstáculos. Favorece ações coordenadas, "
            "viagens e movimentos decisivos. Prática: estabelecer metas claras e medir progresso; usar a força de vontade para superar resistências. O desafio é o excesso de controle "
            "ou a pressa; equilibre velocidade com prudência."
        )
    },
    "8": {
        "short": "{name}, o Arcano 8 (A Justiça) fala de equilíbrio, responsabilidade e consequência.",
        "long": (
            "{name}, o Arcano 8 (A Justiça) remete à equidade, à avaliação imparcial e à necessidade de assumir resultados. Este arcano pede honestidade intelectual e moral, "
            "bem como a revisão de contratos e acordos. Prática: revisar compromissos, ajustar expectativas e agir com transparência. O desafio é a rigidez moral; busque compaixão junto à justiça."
        )
    },
    "9": {
        "short": "{name}, o Arcano 9 (O Eremita) aponta para introspecção, sabedoria e retiro.",
        "long": (
            "{name}, o Arcano 9 (O Eremita) convida ao recolhimento para encontrar luz interior. É tempo de estudo profundo, silêncio e orientação interna. Quando presente, favorece "
            "a busca por sentido e a construção de conhecimento pessoal. Prática: reservar períodos de solitude para leitura, meditação e reflexão. O desafio é o isolamento prolongado; "
            "mantenha contato com uma rede de apoio seletiva."
        )
    },
    "10": {
        "short": "{name}, o Arcano 10 (Roda da Fortuna) fala de ciclos, destino e mudança.",
        "long": (
            "{name}, o Arcano 10 (Roda da Fortuna) lembra que a vida se move em ciclos: altos e baixos, oportunidades e reveses. Este arcano pede adaptabilidade e percepção do timing. "
            "Quando aparece, mudanças significativas podem ocorrer; a atitude recomendada é flexibilidade e preparação para aproveitar janelas de oportunidade. O desafio é resistir à mudança; "
            "pratique desapego e planejamento contingente."
        )
    },
    "11": {
        "short": "{name}, o Arcano 11 (A Força) fala de coragem, disciplina e transformação.",
        "long": (
            "{name}, o Arcano 11 (A Força) representa a coragem serena que transforma desafios em crescimento. Não se trata apenas de vigor físico, mas de domínio das emoções e da vontade. "
            "Quando este arcano é central, há capacidade de enfrentar medos e transformar padrões. Prática: exercícios que integrem corpo e mente (respiração, movimento consciente). "
            "O desafio é a agressividade mal canalizada; direcione energia para objetivos construtivos."
        )
    },
    "12": {
        "short": "{name}, o Arcano 12 (O Enforcado) indica sacrifício, pausa e nova perspectiva.",
        "long": (
            "{name}, o Arcano 12 (O Enforcado) sugere um tempo de suspensão produtiva: renúncia voluntária que permite ver a realidade sob outro ângulo. É um convite a aceitar atrasos "
            "ou perdas como oportunidade de reorientação. Prática: cultivar paciência e observar o que se revela quando a ação é interrompida. O desafio é a estagnação; busque sentido no silêncio."
        )
    },
    "13": {
        "short": "{name}, o Arcano 13 (A Morte) fala de transformação profunda e renascimento.",
        "long": (
            "{name}, o Arcano 13 (A Morte) simboliza término necessário para que algo novo nasça. Trata‑se de transformação radical: deixar ir estruturas obsoletas, padrões e identidades que não servem. "
            "Quando este arcano aparece, processos de luto e liberação são parte do caminho. Prática: rituais de encerramento e planejamento para reconstrução. O desafio é o apego; permita o fluxo natural de renovação."
        )
    },
    "14": {
        "short": "{name}, o Arcano 14 (A Temperança) aponta para equilíbrio, integração e cura.",
        "long": (
            "{name}, o Arcano 14 (A Temperança) convida à moderação, à síntese de opostos e à cura gradual. É o princípio da alquimia interior: combinar elementos para criar harmonia. "
            "Prática: exercícios de integração (respiração, alimentação equilibrada, práticas contemplativas). O desafio é a impaciência; trabalhe com constância e pequenas mudanças sustentáveis."
        )
    },
    "15": {
        "short": "{name}, o Arcano 15 (O Diabo) revela sombras, desejos e padrões de dependência.",
        "long": (
            "{name}, o Arcano 15 (O Diabo) expõe as amarras internas: vícios, compulsões e identidades que aprisionam. Sua função é tornar visível o que está oculto para que possa ser transformado. "
            "Quando aparece, é momento de honestidade radical sobre hábitos e contratos que limitam. Prática: identificar um padrão autodestrutivo e criar um plano de substituição. "
            "O desafio é a negação; a cura começa com reconhecimento e pequenas ações de libertação."
        )
    },
    "16": {
        "short": "{name}, o Arcano 16 (A Torre) indica ruptura, choque e reconstrução.",
        "long": (
            "{name}, o Arcano 16 (A Torre) anuncia eventos que derrubam estruturas frágeis, expondo verdades e forçando reconstrução. Embora doloroso, esse processo limpa o terreno para algo mais autêntico. "
            "Prática: após a ruptura, priorize segurança básica e reavalie valores; construa de forma mais consciente. O desafio é o trauma; busque apoio e processos de integração."
        )
    },
    "17": {
        "short": "{name}, o Arcano 17 (A Estrela) traz esperança, comunicação e inspiração.",
        "long": (
            "{name}, o Arcano 17 (A Estrela) é um farol de esperança e renovação. Favorece cura emocional, criatividade e a partilha de visão. Quando presente, há abertura para inspirar outros e receber orientação. "
            "Prática: atividades que expressem beleza e sentido (arte, ensino, serviço). O desafio é a idealização; mantenha pés no chão enquanto sonha."
        )
    },
    "18": {
        "short": "{name}, o Arcano 18 (A Lua) fala de mistério, medo e processos inconscientes.",
        "long": (
            "{name}, o Arcano 18 (A Lua) revela o terreno do inconsciente: medos, imagens e intuições que influenciam o comportamento. É um convite a explorar sonhos e símbolos para desvelar padrões. "
            "Prática: trabalho com sonhos, imaginação ativa e terapia. O desafio é a confusão; busque clareza por meio de práticas que organizem o mundo interior."
        )
    },
    "19": {
        "short": "{name}, o Arcano 19 (O Sol) simboliza vitalidade, clareza e realização.",
        "long": (
            "{name}, o Arcano 19 (O Sol) representa alegria, saúde e expressão autêntica. É um período de visibilidade e energia criativa. Quando aparece, favorece projetos que iluminam e fortalecem o eu. "
            "Prática: atividades que aumentem vitalidade (exercício, exposição criativa). O desafio é o orgulho; mantenha humildade enquanto celebra conquistas."
        )
    },
    "20": {
        "short": "{name}, o Arcano 20 (O Julgamento) aponta para avaliação, carreira e responsabilidade.",
        "long": (
            "{name}, o Arcano 20 (O Julgamento) convoca à revisão de escolhas e à responsabilização. É um momento de prestação de contas e de colheita dos frutos de ações passadas. "
            "Quando presente, favorece decisões maduras e a assunção de papéis públicos ou profissionais. Prática: revisar trajetória, ajustar metas e alinhar ações com propósito. "
            "O desafio é a autocrítica paralisante; transforme avaliação em aprendizado e ação corretiva."
        )
    },
    "22": {
        "short": "{name}, o Arcano 22 (O Mundo) simboliza realização, brilho e integração.",
        "long": (
            "{name}, o Arcano 22 (O Mundo) indica culminação e integração de ciclos. É o arquétipo da realização que surge quando partes fragmentadas se unem em sentido. "
            "Quando este arcano é central, há reconhecimento, fechamento de etapas e preparação para novos começos em outro nível. Prática: celebrar conquistas, documentar aprendizados e planejar o próximo ciclo. "
            "O desafio é a complacência; use a conclusão como trampolim para novos propósitos."
        )
    },
    "default": {
        "short": "{name}, este é um momento para atenção interior e ação consciente.",
        "long": (
            "{name}, com Life Path {life_path} e Número Cabalístico {cabalistic}, concentre-se em práticas que fortaleçam seu equilíbrio interno. "
            "Identifique um desafio pessoal e transforme‑o em objetivo prático. Sugestão: pequenas ações diárias que sustentem mudança consistente."
        )
    }
}

# correlação Signo -> Arcano (usar nomes em português; normalização aplicada)
SIGN_TO_ARCANO = {
    "aries": "5",
    "touro": "6",
    "gemeos": "7",
    "gêmeos": "7",
    "gemeós": "7",
    "cancer": "8",
    "câncer": "8",
    "leao": "9",
    "leão": "9",
    "virgem": "10",
    "libra": "12",
    "escorpiao": "14",
    "escorpião": "14",
    "escorpiÃo": "14",
    "sagitario": "15",
    "sagitário": "15",
    "capricornio": "16",
    "capricórnio": "16",
    "aquario": "18",
    "aquário": "18",
    "peixes": "19"
}

import unicodedata

EN_TO_PT = {
    "aries":"aries","taurus":"touro","gemini":"gemeos","cancer":"cancer","leo":"leao",
    "virgo":"virgem","libra":"libra","scorpio":"escorpiao","sagittarius":"sagitario",
    "capricorn":"capricornio","aquarius":"aquario","pisces":"peixes"
}

def _normalize_sign(s: Optional[str]) -> Optional[str]:
    if not s:
        return None
    try:
        s2 = str(s).strip().lower()
        s2 = unicodedata.normalize("NFKD", s2)
        s2 = "".join(ch for ch in s2 if not unicodedata.combining(ch))
        # mapear inglês para pt quando aplicável
        return EN_TO_PT.get(s2, s2)
    except Exception:
        return str(s).strip().lower()

def arcano_for_sign(sign: Optional[str], name: Optional[str] = None, length: str = "long") -> Dict[str, Any]:
    """
    Retorna dict com keys: sign, arcano, text, template_key, error.
    Usa SIGN_TO_ARCANO e BASE_TEMPLATES. name é usado para formatar o template (ex: nome do consulente).
    """
    out = {"sign": sign, "arcano": None, "text": "", "template_key": None, "error": None}
    try:
        if not sign:
            out["error"] = "Signo não informado"
            return out

        norm = _normalize_sign(sign)
        arc = SIGN_TO_ARCANO.get(norm)
        if not arc:
            out["error"] = f"Não foi possível inferir arcano para o signo '{sign}' (normalizado: '{norm}')"
            return out

        out["arcano"] = str(arc)
        out["template_key"] = str(arc) if str(arc) in BASE_TEMPLATES else "default"

        # montar contexto mínimo para format
        ctx = {
            "name": name or "Consulente",
            "life_path": out["arcano"],
            "cabalistic": "-",
            "challenge": "-",
            "fluency": "-",
            "practice": "-",
            "quantics_potential": "-"
        }

        template_entry = BASE_TEMPLATES.get(out["template_key"], BASE_TEMPLATES.get("default"))
        text_template = template_entry.get(length) or template_entry.get("long") or template_entry.get("short") or ""
        try:
            text = text_template.format(**ctx)
        except Exception:
            # fallback simples de substituição
            text = text_template
            for k, v in ctx.items():
                text = text.replace("{" + k + "}", str(v))
        out["text"] = textwrap.fill(text, width=100)
        return out
    except Exception as e:
        try:
            logger.exception("Erro em arcano_for_sign: %s", e)
        except Exception:
            pass
        out["error"] = str(e)
        return out

# -------------------------
# Helpers internos
# -------------------------
def _safe_get(d: Dict, *keys, default=None):
    """
    Busca a primeira chave presente em d entre 'keys'.
    Retorna 'default' se nada for encontrado.
    """
    if not isinstance(d, dict):
        return default
    for k in keys:
        try:
            if k in d and d[k] is not None:
                return d[k]
        except Exception:
            # fallback por comparação de igualdade (caso keys não sejam hashable)
            try:
                for existing_key, val in d.items():
                    if existing_key == k and val is not None:
                        return val
            except Exception:
                continue
    return default

def _format_value(v):
    if v is None:
        return "-"
    return str(v)

# -------------------------
# Funções públicas (API do módulo)
# -------------------------
def classic_for_planet(summary: Dict[str, Any], planet_name: str) -> Dict[str, str]:
    """
    Retorna interpretação clássica curta e longa para um planeta.
    Prioriza campos em summary['readings'][planet], senão usa fallback via rules.classic_fallback.
    Retorno: {"short": str, "long": str}
    """
    readings = summary.get("readings", {}) if summary else {}
    r = readings.get(planet_name, {}) or {}
    short = r.get("interpretation_short_classic") or r.get("interpretation_short") or rules.classic_fallback(summary, planet_name)
    long = r.get("interpretation_long_classic") or r.get("interpretation_long") or short
    return {"short": short, "long": long}

def _normalize_arcano_input(arc):
    """
    Normaliza o valor de arcano para um formato previsível:
    - se dict: retorna dict
    - se int/str: retorna str(id)
    - se None: retorna None
    """
    if arc is None:
        return None
    if isinstance(arc, dict):
        return arc
    try:
        # tenta converter números para string
        return str(int(arc)) if (isinstance(arc, (int, float)) or (isinstance(arc, str) and arc.isdigit())) else str(arc)
    except Exception:
        return str(arc)

def safe_arcano_for_planet(summary: Dict[str, Any], planet_name: str) -> Dict[str, Any]:
    """
    Wrapper defensivo para arcano_for_planet.
    Garante que sempre retorne um dict com chaves mínimas:
      - planet
      - arcano
      - influence
      - text
      - error (opcional)
    Use este wrapper no UI para evitar None/exceptions.
    """
    try:
        # chama a implementação principal (se existir)
        res = arcano_for_planet(summary, planet_name)
    except Exception as e:
        # captura qualquer exceção e retorna dict consistente
        try:
            logger.exception("Erro em arcano_for_planet: %s", e)
        except Exception:
            pass
        return {
            "planet": planet_name,
            "arcano": None,
            "influence": None,
            "text": "",
            "error": f"Erro interno ao gerar interpretação por arcanos: {e}"
        }

    # normalizar retorno inesperado
    if res is None:
        return {"planet": planet_name, "arcano": None, "influence": None, "text": "", "error": "Retorno None do gerador de arcanos"}

    if not isinstance(res, dict):
        return {"planet": planet_name, "arcano": res, "influence": None, "text": "", "error": "Retorno inesperado (não-dict) do gerador de arcanos"}

    # garantir chaves mínimas e normalizar arcano
    arc = res.get("arcano")
    arc_norm = _normalize_arcano_input(arc)
    influence = res.get("influence")
    text = res.get("text") or res.get("interpretation") or ""

    out = {
        "planet": res.get("planet", planet_name),
        "arcano": arc_norm,
        "influence": influence,
        "text": text,
        "error": res.get("error")
    }
    return out

# Versão reforçada de arcano_for_planet (substitua a original por esta se preferir)
def arcano_for_planet(summary: Dict[str, Any], planet_name: str) -> Dict[str, Any]:
    """
    Versão defensiva de arcano_for_planet que tenta:
      - usar arcano explícito em summary['readings'][planet]['arcano_info'|'arcano']
      - se ausente, inferir arcano a partir do signo do planeta usando SIGN_TO_ARCANO
      - obter influência da casa via influences.arcano_house_influence
      - renderizar texto via rules.render_arcano_text
    Sempre retorna dict com chaves mínimas.
    """
    try:
        readings = summary.get("readings", {}) if summary else {}
        r = readings.get(planet_name, {}) or {}
        arc_raw = r.get("arcano_info") or r.get("arcano") or None

        # posição/casa e signo
        try:
            pos = rules.get_position_from_summary(summary, planet_name)
        except Exception as e:
            logger.exception("Erro ao obter posição do planeta via rules.get_position_from_summary: %s", e)
            pos = None

        house = pos.get("house") if isinstance(pos, dict) else None
        sign = None
        if isinstance(pos, dict):
            # pos pode ter 'sign' ou 'zodiac' etc.
            sign = pos.get("sign") or pos.get("zodiac") or pos.get("sign_name")
        # fallback: procurar na tabela summary['table']
        if not sign and isinstance(summary, dict):
            table = summary.get("table") or []
            for row in table:
                try:
                    if (row.get("planet") or "").lower() == (planet_name or "").lower():
                        sign = row.get("sign") or row.get("zodiac") or sign
                        break
                except Exception:
                    continue

        # normalizar arcano explícito
        arc = _normalize_arcano_input(arc_raw)

        # se não houver arcano explícito, tentar inferir pelo signo
        if not arc:
            norm_sign = _normalize_sign(sign)
            if norm_sign:
                inferred = SIGN_TO_ARCANO.get(norm_sign)
                if inferred:
                    arc = str(inferred)
                    logger.debug("Arcano inferido por signo: planet=%s sign=%s arcano=%s", planet_name, sign, arc)

        # obter estrutura de influência (arcano + tema da casa)
        try:
            influence = influences.arcano_house_influence(arc if arc is not None else "0", house)
        except Exception as e:
            logger.exception("Erro ao obter influence via influences.arcano_house_influence: %s", e)
            influence = None

        # montar texto final combinando arcano e casa
        try:
            arc_text = rules.render_arcano_text(arc, influence)
            if arc_text is None:
                arc_text = ""
        except Exception as e:
            logger.exception("Erro ao renderizar texto do arcano via rules.render_arcano_text: %s", e)
            arc_text = ""

        return {
            "planet": planet_name,
            "arcano": arc,
            "influence": influence,
            "text": arc_text
        }
    except Exception as e:
        try:
            logger.exception("Erro inesperado em arcano_for_planet: %s", e)
        except Exception:
            pass
        return {
            "planet": planet_name,
            "arcano": None,
            "influence": None,
            "text": "",
            "error": f"Erro interno ao gerar arcano: {e}"
        }

def chart_overview(summary: Dict[str, Any]) -> str:
    """
    Gera um parágrafo resumo do mapa (curto). Usa summary['table'] quando disponível.
    Exemplo de saída: "Sun em Taurus 12.34° / Moon em Aries 3.21° / ..."
    """
    if not summary:
        return "Nenhum resumo disponível."
    table = summary.get("table", [])
    parts: List[str] = []
    for row in table:
        pname = row.get("planet")
        sign = row.get("sign")
        degree = row.get("degree")
        if pname and sign is not None and degree is not None:
            parts.append(f"{pname} em {sign} {degree}°")
    return " / ".join(parts) if parts else "Mapa sem posições legíveis."

# -------------------------
# Função de geração de interpretação (numerologia / arcano)
# -------------------------
def generate_interpretation(
    reading: Dict,
    arcano_key: Optional[str] = None,
    templates_override: Optional[Dict[str, Dict[str, str]]] = None,
    length: str = "long",
    prepend_cycle_description: bool = False
) -> str:
    """
    Gera interpretação textual a partir do dicionário `reading`.
    Usa templates locais (BASE_TEMPLATES) por padrão; permite override.
    Se arcano_key for fornecido, usa o template correspondente; caso contrário, usa life_path/cabalistic do reading.
    prepend_cycle_description adiciona a descrição do ciclo (reading['cycle_description']) no início.
    """
    templates = dict(BASE_TEMPLATES)
    if templates_override:
        templates.update(templates_override)

    name = reading.get("name", "Consulente")
    numerology = reading.get("numerology", {}) or {}
    life_path = _safe_get(numerology, "life_path", "value", default=_safe_get(numerology.get("life_path", {}), "value"))
    cabalistic = _safe_get(numerology, "cabalistic", "reduced", default=_safe_get(numerology.get("cabalistic", {}), "reduced"))

    arcano = arcano_key or str(life_path or "default")
    template_entry = templates.get(str(arcano)) or templates.get("default")
    text_template = template_entry.get(length) or template_entry.get("long") or template_entry.get("short")

    # construir contexto seguro para format
    quantics_obj = _safe_get(numerology, "quantics", default={}) or {}
    quantics_potential = quantics_obj.get("potential")

    context = {
        "name": name,
        "life_path": _format_value(life_path),
        "cabalistic": _format_value(cabalistic),
        "challenge": _format_value(_safe_get(reading, "challenge", default="—")),
        "fluency": _format_value(_safe_get(reading, "fluency", default="—")),
        "practice": _format_value(_safe_get(reading, "practice", default="—")),
        "quantics_potential": _format_value(quantics_potential)
    }

    try:
        body = text_template.format(**context)
    except Exception:
        # fallback simples: substituir chaves manualmente
        body = text_template
        for k, v in context.items():
            body = body.replace("{" + k + "}", str(v))

    prefix = ""
    if prepend_cycle_description:
        cycle_desc = reading.get("cycle_description")
        if cycle_desc:
            prefix = cycle_desc.strip() + "\n\n"

    text = prefix + body
    # quebra de linha para legibilidade
    text = textwrap.fill(text, width=100)
    return text

# -------------------------
# Utilitários públicos adicionais (opcionais)
# -------------------------
def available_templates(templates_override: Optional[Dict[str, Dict[str, str]]] = None) -> List[str]:
    keys = set(BASE_TEMPLATES.keys())
    if templates_override:
        keys.update(templates_override.keys())
    return sorted(list(keys))

def get_template(key: str, templates_override: Optional[Dict[str, Dict[str, str]]] = None) -> Optional[Dict[str, str]]:
    templates = dict(BASE_TEMPLATES)
    if templates_override:
        templates.update(templates_override)
    return templates.get(str(key))