# etheria/rules.py
from typing import Optional, Dict, Any, List
from datetime import date
from . import astrology, influences
from .utils import age_from_dob, reduce_number, format_degree, validate_cycle35, validate_cycle1
from .numerology import life_path_from_dob, name_value_pythag, name_value_cabal, quantics_from_dob
from .cycles import cycle35_for_age, cycle_major_for_age, cycle1_for_date, CICLO_MAIOR_DESC, CICLO_MENOR_ASTROLOGICO_DESC, CICLO_MENOR_TEOSOFICO_DESC

# --- constantes de numerologia (mantidas) ---
PITAGORIC_MEANINGS = {
    1: "Individual | Iniciador",
    2: "Perceptivo | Cooperador",
    3: "Talentoso | Criativo",
    4: "Estável | Seguro",
    5: "Versátil | Aventureiro",
    6: "Conciliador | Justo",
    7: "Intelectual | Buscador",
    8: "Sábio | Administrador",
    9: "Humanitário | Generoso",
    11: "Idealismo | Inspiração",
    22: "Construtor | Empreendedor",
    33: "Liderança | Comando",
    44: "Eficiente | Comunicativo",
    55: "Intuitivo | Canalizador",
    66: "Amoroso | Compaixão",
    77: "Liberdade | Discernimento",
    88: "Força Divina Transformadora",
    99: "Aperfeiçoamento"
}

CABALISTIC_MEANINGS = {
    1: "Muitas inteligências ou uma inteligência mal aplicada",
    2: "Número de revelação ou ocultar verdade",
    3: "Força muito grande de plasmação ou falta de vontade muito grande",
    4: "O poder da decisão ou uma tirania absoluta",
    5: "Grande espiritualidade e aberturas espirituais ou um fanatismo muito grande",
    6: "Poder de decisão seguindo o coração ou momento de grande indecisão",
    7: "Direcionamento bacana das energias ou um direcionamento erroneo das mesmas",
    8: "Éticas, bons valores, moral ou falta de ética e imoralidade",
    9: "Ter um pouco de isolamento, quietude, para achar a luz interior ou imprudência e não saber aquietar a alma",
    10: "Viver os caminhos que o destino demonstra, observar através do Karma ou correr do destino",
    11: "Equilíbrio grande entre as energias espirituais e terrenas ou não colocar em prática as duas energias juntas",
    12: "Comprometimento. Aprender a se comprometer com o que é sério para você ou irresponsabilidade, fugir do dever",
    13: "Aceitar as grandes transformações que o mundo oferece ou não aceitar e ser judiado pelas transformações",
    14: "Equilíbrio entre passado e futuro ou viver aprisionado no passado e futuro",
    15: "Aceitar as sombras e com elas transformar em luz ou ser conduzido por sombras",
    16: "Desconstruir o falso para construir o verdadeiro ou apostar em coisas desgastadas",
    17: "Aprender a ter fé e espiritualidade ou falta de fé, otimismo cego",
    18: "Ter força através dos medos ou excesso de confiança",
    19: "Trabalhar a verdadeira gratidão ou gratidão falsa",
    20: "Libertação verdadeira ou estar preso de luz para morrer",
    21: "Posicionamento claro ou experiências desconectadas",
    22: "Finalização de ciclo importante ou não saber finalizar ciclos"
}

ANNUAL_GROUPS = {
    "1/2/3": "Realize! São números de mão na massa",
    "4/5/6": "Utilize sua energia em coisas que valham a pena",
    "7/8/9": "Vibrar no positivo! Possibilidades bacanas",
    "10/11/12": "Quais conhecimentos você coloca dentro de ti? Racionalidade; alicerce de grandes intuições",
    "13/14/15": "Mundo da abstração. Está no 5° princípio; mente criativa",
    "16/17/18": "O que mais vale é a intuição. Poder de escolha",
    "19/20/21": "Pessoa está pronta para experiências maiores"
}

def _annual_group_description(n: int) -> str:
    for group, desc in ANNUAL_GROUPS.items():
        nums = [int(x) for x in group.split("/")]
        if n in nums:
            return desc
    return ""

def _cycle_description_for_mode(mode: str) -> str:
    m = (mode or "astrologico").lower()
    if m == "maior":
        return CICLO_MAIOR_DESC
    if m == "teosofico":
        return CICLO_MENOR_TEOSOFICO_DESC
    return CICLO_MENOR_ASTROLOGICO_DESC

# -------------------------
# Função principal: gerar leitura numerológica/ciclos (limpa e única)
# -------------------------
def generate_reading(
    full_name: str,
    dob,
    tables: Optional[Dict[str, Any]] = None,
    keep_master: bool = False,
    cycle_mode: str = "astrologico"
) -> Dict[str, Any]:
    """
    Gera leitura combinada (numerologia + ciclos).
    Retorna dicionário com campos: name, dob, age, cycle_mode, cycle_description,
    numerology (life_path, hidden, cabalistic, quantics), cycle_selected, cycle1.
    """
    # normalizar dob se for string ISO
    if isinstance(dob, str):
        from datetime import datetime
        dob = datetime.fromisoformat(dob).date()

    age = age_from_dob(dob)
    life_reduced, life_raw = life_path_from_dob(dob, keep_masters=keep_master)
    hidden_reduced, hidden_raw = name_value_pythag(full_name, keep_master=keep_master)
    quantics = quantics_from_dob(dob, keep_master=keep_master)

    # cabalistic (usar tabela se fornecida)
    letter_map_df = None
    if tables and tables.get("letter_map") is not None:
        letter_map_df = tables.get("letter_map")
    cab = name_value_cabal(full_name, letter_map_df, keep_master=keep_master)

    # ciclo anual (1 ano) - preferir tabela se fornecida
    cycle1_result = None
    if tables and tables.get("cycle_1year") is not None:
        try:
            validate_cycle1(tables["cycle_1year"])
            cycle1_result = cycle1_for_date(dob.month, dob.day, None, tables["cycle_1year"], mode=cycle_mode)
        except Exception:
            cycle1_result = None
    if cycle1_result is None:
        cycle1_result = cycle1_for_date(dob.month, dob.day, mode=cycle_mode)

    # ciclo selecionado (35 anos ou maior)
    cycle_desc = _cycle_description_for_mode(cycle_mode)
    cycle_result = None

    if cycle_mode and cycle_mode.lower() == "maior":
        if tables and tables.get("cycle_35") is not None:
            try:
                validate_cycle35(tables["cycle_35"])
                df = tables["cycle_35"]
                cols = [c.lower() for c in df.columns]
                if "year" in cols:
                    year_col = [c for c in df.columns if c.lower() == "year"][0]
                    row = df[df[year_col] == age]
                    if not row.empty:
                        cycle_result = {"source": "table", "row": row.iloc[0].to_dict(), "mode": "maior"}
            except Exception:
                cycle_result = None
        if cycle_result is None:
            cycle_result = {"source": "rule", **cycle_major_for_age(age)}
    else:
        if tables and tables.get("cycle_35") is not None:
            try:
                validate_cycle35(tables["cycle_35"])
                df = tables["cycle_35"]
                cols = [c.lower() for c in df.columns]
                if "year" in cols:
                    year_col = [c for c in df.columns if c.lower() == "year"][0]
                    row = df[df[year_col] == age]
                    if not row.empty:
                        cycle_result = {"source": "table", "row": row.iloc[0].to_dict(), "mode": cycle_mode}
            except Exception:
                cycle_result = None
        if cycle_result is None:
            cycle_result = {"source": "rule", **cycle35_for_age(age, mode=cycle_mode)}

    # montar retorno final (único)
    result = {
        "name": full_name,
        "dob": dob.isoformat(),
        "age": age,
        "cycle_mode": cycle_mode,
        "cycle_description": cycle_desc,
        "numerology": {
            "life_path": {"value": life_reduced, "raw": life_raw},
            "hidden": {"value": hidden_reduced, "raw": hidden_raw},
            "cabalistic": cab,
            "quantics": quantics
        },
        "cycle_selected": cycle_result,
        "cycle1": cycle1_result
    }

    # enriquecer com significados (opcional)
    def _pit(n): return PITAGORIC_MEANINGS.get(n, "")
    def _cab(n): return CABALISTIC_MEANINGS.get(n, "")

    # adicionar interpretações resumidas (não obrigatório; útil para UI)
    try:
        life_val = result["numerology"]["life_path"]["value"]
        hidden_val = result["numerology"]["hidden"]["value"]
        result["numerology"]["life_path"]["meaning"] = _pit(life_val)
        result["numerology"]["hidden"]["meaning"] = _pit(hidden_val)
        quantics_list = result["numerology"].get("quantics", []) or []
        result["numerology"]["quantics_meanings"] = [
            {"index": i + 1, "value": q, "meaning": _pit(q)} for i, q in enumerate(quantics_list)
        ]
        total = sum(quantics_list) if quantics_list else 0
        result["numerology"]["potential"] = {"value": total, "meaning": _pit(reduce_number(total))}
    except Exception:
        # não falhar se algo inesperado ocorrer
        pass

    return result

# -------------------------
# utilitários de posição e síntese textual (usados pelo UI)
# -------------------------
def get_position_from_summary(summary: Dict[str, Any], planet: str) -> Optional[Dict[str, Any]]:
    """
    Extrai posição do planeta a partir do summary.
    Retorna dict com keys: planet, sign, degree, sign_index, longitude, house (se disponível).
    """
    if not summary:
        return None
    table = summary.get("table", []) or []
    for row in table:
        if row.get("planet") == planet:
            return {
                "planet": planet,
                "sign": row.get("sign"),
                "degree": row.get("degree"),
                "sign_index": row.get("sign_index"),
                "longitude": row.get("longitude"),
                "house": row.get("house") or row.get("house_number") or row.get("house_index")
            }
    # fallback para summary["planets"]
    planets = summary.get("planets", {}) or {}
    p = planets.get(planet)
    if p:
        lon = p.get("longitude") if isinstance(p, dict) else p
        sign, degree, sign_index = astrology.lon_to_sign_degree(lon or 0.0)
        return {
            "planet": planet,
            "sign": sign,
            "degree": degree,
            "sign_index": sign_index,
            "longitude": lon,
            "house": p.get("house") if isinstance(p, dict) else None
        }
    return None

# Templates simples
SYNTH_TEMPLATE = "{name}: {planet} em {sign} (Casa {house}) — {verb}: {core}. Síntese: {synthesis}"
ARCANO_HOUSE_TEMPLATE = "Arcano {arcano} na Casa {house} ({house_theme}) — {arcano_text}"

def synth_rule_for_planet(planet: str, summary: Dict[str, Any], consulente_name: str = "Consulente", synthesis_override: Optional[str] = None) -> str:
    """
    Gera síntese configuracional curta para exportação.
    """
    pos = get_position_from_summary(summary, planet)
    if not pos:
        return f"Nenhuma posição encontrada para {planet}."
    sign = pos.get("sign", "N/A")
    house = pos.get("house", "N/A")
    degree = pos.get("degree", 0.0)
    verb, core = astrology.PLANET_CORE.get(planet, ("Atuar", "Função planetária"))
    if synthesis_override:
        synthesis = synthesis_override
    else:
        sign_qual = astrology.SIGN_DESCRIPTIONS.get(sign, ("", ""))[1] if sign in astrology.SIGN_DESCRIPTIONS else ""
        house_theme = influences.HOUSE_THEMES.get(house, influences.HOUSE_THEMES.get(int(house) if isinstance(house, int) else None, "Área não especificada"))
        synthesis = f"{verb} ligado a {sign} ({sign_qual}). Área: {house_theme}."
    context = {
        "name": consulente_name,
        "planet": planet,
        "sign": sign,
        "house": house,
        "degree": format_degree(degree),
        "verb": verb,
        "core": core,
        "synthesis": synthesis
    }
    return SYNTH_TEMPLATE.format(**context)

def synthesize_export_text(summary: Dict[str, Any], planet_name: str, consulente_name: str = "Consulente", synthesis_override: Optional[str] = None) -> str:
    """
    Conveniência para UI: texto pronto para exportar (síntese configuracional).
    """
    return synth_rule_for_planet(planet_name, summary, consulente_name, synthesis_override)

def classic_fallback(summary: Dict[str, Any], planet_name: str) -> str:
    """
    Fallback clássico curto combinando verbo + signo + grau.
    """
    pos = get_position_from_summary(summary, planet_name)
    if not pos:
        return f"Nenhuma interpretação disponível para {planet_name}."
    verb = astrology.PLANET_CORE.get(planet_name, ("Atuar", ""))[0]
    sign = pos.get("sign")
    degree = pos.get("degree")
    core = astrology.PLANET_CORE.get(planet_name, ("", ""))[1]
    return f"{planet_name} ({verb}) em {sign} {format_degree(degree)} — {core}"

def render_arcano_text(arcano_obj: Any, influence_obj: Dict[str, Any]) -> str:
    """
    Monta parágrafo combinando arcano (obj ou id) e influência na casa.
    """
    arc_id = None
    arc_name = None
    arc_keywords = []
    if isinstance(arcano_obj, dict):
        arc_id = str(arcano_obj.get("arcano") or arcano_obj.get("value") or arcano_obj.get("id"))
        arc_name = arcano_obj.get("name")
        arc_keywords = arcano_obj.get("keywords") or arcano_obj.get("kw") or []
    else:
        arc_id = str(arcano_obj) if arcano_obj is not None else "0"
    arc_text = influences.ARCANO_BASE_TEXTS.get(arc_id, influence_obj.get("arcano_text", "Energia simbólica."))
    house = influence_obj.get("house") or "N/A"
    house_theme = influence_obj.get("house_theme", "Área não especificada")
    header = ARCANO_HOUSE_TEMPLATE.format(arcano=arc_id, house=house, house_theme=house_theme, arcano_text=arc_text)
    keywords_text = ""
    if arc_keywords:
        keywords_text = "\n\nPalavras-chave: " + ", ".join(arc_keywords)
    return f"{header}\n\n{arc_text} {(' ' + house_theme) if house_theme else ''}.{keywords_text}"

# -------------------------
# utilitários adicionais
# -------------------------
def arcano_from_dob(dob: date) -> int:
    """
    Calcula arcano a partir da data de nascimento (redução até 0..21).
    """
    if isinstance(dob, str):
        from datetime import datetime
        dob = datetime.fromisoformat(dob).date()
    digits = [int(ch) for ch in dob.strftime("%d%m%Y") if ch.isdigit()]
    total = sum(digits)
    while total > 21:
        total = sum(int(ch) for ch in str(total))
    return total