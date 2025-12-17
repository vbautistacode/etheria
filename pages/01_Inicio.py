# pages/Inicio.py

import os
import json
import sys
import logging
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Ler secrets do Streamlit (retorna None se não existir)
sa_json = st.secrets.get("GCP_SA_JSON")
project_id = st.secrets.get("GCP_PROJECT_ID", "etheria-480312")
location = st.secrets.get("GENAI_LOCATION", "us-central1")
model_name = st.secrets.get("GENAI_MODEL", "gemini-2.5-flash")

# Se o secret não existir, logue e continue (evita NameError)
if not sa_json:
    logging.warning("GCP_SA_JSON não encontrado em st.secrets; verifique Streamlit Secrets.")
else:
    # escrever credencial em arquivo temporário e definir variável de ambiente
    cred_path = "/tmp/gcp_sa.json" if os.name != "nt" else os.path.join(os.environ["TEMP"], "gcp_sa.json")
    with open(cred_path, "w", encoding="utf-8") as f:
        f.write(sa_json)
    try:
        os.chmod(cred_path, 0o600)
    except Exception:
        pass
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = cred_path

import pandas as pd
from etheria import cycles
from etheria import astrology
from etheria import numerology
from services.chakra_panel import render_chakra_image
from etheria.astrology import planet_interpretation, generate_three_interpretations
from pandas.io.formats.style import Styler
from datetime import date, datetime
from typing import Optional, Dict, List, Any
from etheria.personal_year import analyze_personal_year_from_dob
from dotenv import load_dotenv

# Import loaders and cycles (assume pacote local etheria)
from etheria.loaders import (
    read_matrix_csv,
    wide_matrix_to_long,
    read_correlations,
    join_matrix_with_map,
    build_type_matrices,
    validation_report,
)
from etheria.cycles import (
    get_regent_for_cycle,
    regent_by_year,
    short_regent_label,
    CICLO_MAIOR_DESC,
    CICLO_MENOR_ASTROLOGICO_DESC,
    CICLO_MENOR_TEOSOFICO_DESC,
)

st.set_page_config(page_title="Etheria", layout="wide", initial_sidebar_state="expanded")

st.title("Ciclos Astrológicos e Relógio Tátvico ♾️")
st.markdown(
    """  
    Cada planeta percorre sua órbita como um ponteiro cósmico, marcando fases que se refletem 
    nos ciclos internos da consciência.  

    O **Relógio Tátvico** mostra como esses movimentos dialogam com os cinco elementos sutis — 
    os *tátvvas*:  
    - **Éter (Akasha)**: o espaço que acolhe todos os ritmos, a matriz silenciosa do ser.  
    - **Ar (Vayu)**: o sopro das ideias e da comunicação, que acompanha Mercúrio e os ventos da mente.  
    - **Fogo (Tejas)**: a chama da ação e da vontade, refletida nos ciclos solares e na energia de Marte.  
    - **Água (Apas)**: o fluxo das emoções e da intuição, espelhado na Lua e em Vênus.  
    - **Terra (Prithivi)**: a estabilidade e a forma, sustentada por Saturno e pelos ciclos de materialização.  

    Assim, cada transição astrológica desperta um tátvva correspondente, convidando você a alinhar 
    práticas externas com estados internos.  
    Mais do que observar símbolos, aqui você é chamado a vivenciá-los: transformar arquétipos em 
    experiências, experiências em consciência, e consciência em presença.  

    Este espaço é uma jornada de autoconhecimento, onde o relógio celeste e o relógio tátvico 
    se sincronizam, revelando que cada instante é uma oportunidade de integração entre corpo, mente 
    e espírito.
    """
)

# -------------------------
# Parâmetros padrão
# -------------------------
DEFAULT_CYCLE_MODE = "astrologico"

# -------------------------
# Carregamento centralizado (sem uploads)
# -------------------------
@st.cache_data
def load_data() -> Dict[str, Any]:
    default_matrix_path = "data/matrix_hour.csv"
    default_corr_path = "data/correlations.csv"

    df_matrix = read_matrix_csv(default_matrix_path, sep=";")
    df_corr = read_correlations(default_corr_path, sep=";")

    df_long = wide_matrix_to_long(df_matrix)
    df_merged = join_matrix_with_map(df_long, df_corr)
    matrices = build_type_matrices(df_merged)
    report = validation_report(df_long, df_corr)
    return {
        "matrix_df": df_matrix,
        "corr_df": df_corr,
        "long": df_long,
        "merged": df_merged,
        "matrices": matrices,
        "report": report,
    }

data = load_data()

# -------------------------
# Sidebar: ajustes e Entrada do consulente
# -------------------------
from datetime import datetime
current_year = datetime.now().year

st.sidebar.header("Ajustes de Ciclos")
# usar session_state para persistência entre interações
if "base_astro" not in st.session_state:
    st.session_state["base_astro"] = current_year
if "base_teos" not in st.session_state:
    st.session_state["base_teos"] = current_year
if "base_major" not in st.session_state:
    st.session_state["base_major"] = current_year

col_a, col_b = st.sidebar.columns([3,1])
with col_a:
    base_astro = st.sidebar.number_input(
        "Ano Astrológico",
        min_value=1, max_value=10000,
        value=st.session_state["base_astro"], step=1, key="base_astro_input"
    )
    base_teos = st.sidebar.number_input(
        "Ano Teosófico",
        min_value=1, max_value=10000,
        value=st.session_state["base_teos"], step=1, key="base_teos_input"
    )
    base_major = st.sidebar.number_input(
        "Ano Base | Ciclo Maior",
        min_value=1, max_value=10000,
        value=st.session_state["base_major"], step=1, key="base_major_input"
    )
with col_b:
    # botão para resetar todos os base_years para o ano vigente
    if st.sidebar.button("Resetar para ano atual"):
        st.session_state["base_astro"] = current_year
        st.session_state["base_teos"] = current_year
        st.session_state["base_major"] = current_year

        # Gatilho extra para forçar atualização em versões sem experimental_rerun
        st.session_state["_rerun_trigger"] = st.session_state.get("_rerun_trigger", 0) + 1

        # Se a função experimental_rerun existir, use-a (compatibilidade)
        if hasattr(st, "experimental_rerun"):
            try:
                st.experimental_rerun()
            except Exception:
                # se falhar por algum motivo, apenas continue; session_state já foi atualizado
                pass

# sincronizar session_state com valores atuais dos inputs
st.session_state["base_astro"] = int(base_astro)
st.session_state["base_teos"] = int(base_teos)
st.session_state["base_major"] = int(base_major)

use_colors = st.sidebar.checkbox("Ativar cores por planeta", value=True)

# -------------------------
# Planet styles (cores e ícones)
# --- Planet styles (canônico em inglês) + aliases PT/EN ---
PLANET_STYLES = {
    # nomes canônicos (usar internamente)
    "Sun":    {"color": "#FFA500", "icon": "☉", "label_pt": "Sol",     "label_en": "Sun"},
    "Moon":   {"color": "#EE82EE", "icon": "☾", "label_pt": "Lua",     "label_en": "Moon"},
    "Mars":   {"color": "#FF0000", "icon": "♂️", "label_pt": "Marte",   "label_en": "Mars"},
    "Mercury":{"color": "#FFD700", "icon": "☿️", "label_pt": "Mercúrio","label_en": "Mercury"},
    "Jupiter":{"color": "#0000FF", "icon": "♃", "label_pt": "Júpiter", "label_en": "Jupiter"},
    "Venus":  {"color": "#87CEEB", "icon": "♀️", "label_pt": "Vênus",   "label_en": "Venus"},
    "Saturn": {"color": "#008000", "icon": "♄", "label_pt": "Saturno", "label_en": "Saturn"},
    "Uranus": {"color": "#7FFFD4", "icon": "⛢", "label_pt": "Urano",   "label_en": "Uranus"},
    "Neptune":{"color": "#6A5ACD", "icon": "♆", "label_pt": "Netuno",  "label_en": "Neptune"},
    "Pluto":  {"color": "#A52A2A", "icon": "♇", "label_pt": "Plutão",  "label_en": "Pluto"},
    "default":{"color": "#E0E0E0", "icon": "✨", "label_pt": "Default", "label_en": "Default"}
}

# aliases para mapear variantes (sem acento, pt/eng, abreviações)
PLANET_ALIASES = {
    "sol": "Sun", "sun": "Sun",
    "lua": "Moon", "moon": "Moon",
    "marte": "Mars", "mars": "Mars",
    "mercurio": "Mercury", "mercurio": "Mercury", "mercury": "Mercury", "mercúrio": "Mercury",
    "jupiter": "Jupiter", "júpiter": "Jupiter",
    "venus": "Venus", "vênus": "Venus",
    "saturno": "Saturn", "saturn": "Saturn",
    "urano": "Uranus", "uranus": "Uranus",
    "netuno": "Neptune", "neptune": "Neptune",
    "plutao": "Pluto", "plutão": "Pluto", "pluto": "Pluto"
}

import unicodedata
from typing import Optional, Dict

def _normalize_key(name: str) -> str:
    """Remove acentos, espaços e normaliza caixa para lookup."""
    if not name:
        return ""
    s = str(name)
    nfkd = unicodedata.normalize("NFKD", s)
    only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
    return only_ascii.strip().lower()

def canonical_planet_name(name: str) -> Optional[str]:
    """
    Converte uma variante (pt/eng/acentos) para o nome canônico usado em PLANET_STYLES.
    Retorna None se não puder mapear.
    """
    if not name:
        return None
    norm = _normalize_key(name)
    # busca direta em aliases
    if norm in PLANET_ALIASES:
        return PLANET_ALIASES[norm]
    # tentar corresponder às chaves de PLANET_STYLES normalizadas
    for k in PLANET_STYLES.keys():
        if _normalize_key(k) == norm or norm in _normalize_key(k) or _normalize_key(k) in norm:
            return k
    return None

def get_planet_style(name: str, lang: str = "pt") -> Dict[str, str]:
    """
    Retorna o dicionário de estilo para o planeta dado (aceita variantes).
    - name: qualquer variante (ex.: 'Vênus', 'venus', 'Venus', 'Júpiter', 'Jupiter')
    - lang: 'pt' ou 'en' para obter label no idioma desejado (label_pt/label_en)
    Retorna o estilo 'default' se não encontrar.
    """
    canon = canonical_planet_name(name)
    style = PLANET_STYLES.get(canon) if canon else PLANET_STYLES["default"]
    # construir retorno com label no idioma pedido
    label_key = "label_pt" if lang and lang.lower().startswith("pt") else "label_en"
    return {
        "color": style.get("color", PLANET_STYLES["default"]["color"]),
        "icon": style.get("icon", PLANET_STYLES["default"]["icon"]),
        "label": style.get(label_key, style.get("label_en", "—"))
    }

# -------------------------
# Snippets de ciclos (usando base_years do sidebar)
# -------------------------
# --- Interpretação coletiva dinâmica
# UI snippet para exibir em 3 colunas (colar onde apropriado em app.py)

_now = datetime.now()
reg_ast = get_regent_for_cycle("astrologico", _now, {"corr_df": data["corr_df"]},
                               base_year_astro=base_astro, base_year_teos=base_teos, base_year_major=base_major)
reg_teo = get_regent_for_cycle("teosofico", _now, {"corr_df": data["corr_df"]},
                               base_year_astro=base_astro, base_year_teos=base_teos, base_year_major=base_major)
reg_35  = get_regent_for_cycle("maior", _now, {"corr_df": data["corr_df"]},
                               base_year_astro=base_astro, base_year_teos=base_teos, base_year_major=base_major)

planet_ast = short_regent_label(reg_ast.get("regent"))
planet_teo = short_regent_label(reg_teo.get("regent"))
planet_35  = short_regent_label(reg_35.get("regent"))

st.header("Os Ciclos")
st.markdown(
    """
    Os ciclos anuais representam padrões de energia que se manifestam ao longo de cada ano. 
    No campo **astrológico**, o retorno solar marca o início de um novo ciclo,  indicando temas 
    que tendem a se destacar em diferentes áreas da vida.  

    No campo **teosófico**, o ciclo anual é definido pelo chamado **Relógio Cósmico**. Esse relógio segue a ordem dos planetas associada 
      aos dias da semana — de sábado a domingo — em seu 
    movimento inverso. Cada planeta, ao reger simbolicamente um dia, imprime sua qualidade sobre o período, 
    revelando tendências de expansão, recolhimento, criatividade ou disciplina conforme o ritmo cósmico.  

    Além dos ciclos anuais, existe o ciclo maior de **35 anos**, considerado um marco de integração 
    e maturidade. Ele simboliza a consolidação de aprendizados acumulados e a abertura para novas 
    etapas de desenvolvimento.  
    Esse ciclo é entendido como parte de uma espiral evolutiva, na qual cada fase da existência 
    contribui para o processo contínuo de autoconhecimento e realização.
    """
)

interp_ast, interp_teo, interp_35 = generate_three_interpretations(planet_ast, planet_teo, planet_35, summary=_summary_obj if '_summary_obj' in globals() else None)

c1, c2, c3 = st.columns(3)
# título com botão de ajuda exatamente em frente
help_key = f"help_btn_{planet_ast}"
flag_key = f"show_help_{planet_ast}"

with c1:
    style = get_planet_style(planet_ast, lang="pt") if use_colors else {"color": "#000000", "icon": ""}

    # colunas: título (maior) + botão (estreita)
    col_title, col_help = st.columns([0.40, 0.60])

    # título com display:flex para garantir alinhamento vertical do conteúdo interno
    with col_title:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:0px; margin:0;">
                <div style="font-size:20px; font-weight:600; line-height:3;">
                    {style.get('icon','')} Ciclo Astrológico
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # coluna do botão: centraliza vertical e horizontalmente
    with col_help:
        st.markdown(
            """
            <div style="display:flex; align-items:right; justify-content:center; height:100%;">
            """,
            unsafe_allow_html=True,
        )
        # botão que aciona o expander (use key único por bloco)
        if st.button("🔻", key=help_key):
            st.session_state[flag_key] = not st.session_state.get(flag_key, False)
        st.markdown("</div>", unsafe_allow_html=True)

    # quando o flag estiver ativo, mostra o expander já expandido
    if st.session_state.get(flag_key, False):
        with st.expander("*Saiba mais!*", expanded=True):
            st.markdown(CICLO_MENOR_ASTROLOGICO_DESC)

    # restante do conteúdo
    st.markdown(
        f"<div style='font-size:20px;color:{style['color']};font-weight:600;margin-top:8px'>{planet_ast}</div>",
        unsafe_allow_html=True,
    )

    st.write(interp_ast["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_ast["long"])




with c2:
    style = get_planet_style(planet_teo, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(
    f"<h3 style='font-size:20px;font-weight:600' "
    f"title='{CICLO_MENOR_TEOSOFICO_DESC}'>{style.get('icon','')} Ciclo Teosófico</h3>",
    unsafe_allow_html=True
    )
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_teo}</div>", unsafe_allow_html=True)

    st.write(interp_teo["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_teo["long"])

with c3:
    style = get_planet_style(planet_35, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(
    f"<h3 style='font-size:20px;font-weight:600' "
    f"title='{CICLO_MAIOR_DESC}'>{style.get('icon','')} Ciclo Maior</h3>",
    unsafe_allow_html=True
    )
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_35}</div>", unsafe_allow_html=True)

    st.write(interp_35["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_35["long"])
# --------------------------------------------------------------------

# -------------------------
# Layout principal: visualizador e área de resultados
# -------------------------
left, = st.columns([4])

with left:
    st.header("Relógio Tátvico e Correlações")
    st.markdown(
        """
        Sistema esotérico que mede o tempo segundo a vibração dos *tattwas* (princípios elementares).  
        O Relógio Tátvico descreve como as qualidades sutis — éter, ar, fogo, água e terra — se alternam 
        ao longo do dia, modulando ritmos energéticos e influenciando estados mentais, emocionais e físicos.  

        Trata-se de uma matriz temporal que correlaciona fases do dia com princípios elementares, oferecendo 
        um quadro para interpretar variações de disposição, atenção e ação em diferentes momentos.
        """
    )

    types = list(data["matrices"].keys())
    if not types:
        st.info("Nenhum tipo disponível para visualização.")
    else:
        # três seletores na mesma linha: Tipo | Dia | Hora
        col_type, col_day, col_hour = st.columns([1, 1, 1])

        with col_type:
            type_choice = st.selectbox("Seleção", options=types, index=0, key="type_choice")

        # obter matriz após escolher o tipo
        mat = data["matrices"][type_choice].fillna("-")
        weekdays = mat.columns.tolist()
        hours = mat.index.tolist()

        # Ordem correta dos dias da semana
        ordered_days = ["Segunda-feira", "Terca-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
        # Reordenar colunas da matriz
        mat = mat[[day for day in ordered_days if day in mat.columns]]

        with col_day:
            default_weekday_idx = 0
            if "Segunda-feira" in weekdays:
                default_weekday_idx = weekdays.index("Segunda-feira")
            weekday_choice = st.selectbox("Dia", options=weekdays, index=default_weekday_idx, key="weekday_choice")

        with col_hour:
            default_hour_idx = 0
            if "06:00" in hours:
                default_hour_idx = hours.index("06:00")
            hour_choice = st.selectbox("Hora", options=hours, index=default_hour_idx, key="hour_choice")

        def highlight_selected(df: pd.DataFrame, sel_wd: str, sel_hr: str) -> pd.io.formats.style.Styler:
            def _style(row):
                return [("background-color: #fffb0" if (col == sel_wd and row.name == sel_hr) else "") for col in df.columns]
            return df.style.apply(_style, axis=1)

        st.dataframe(highlight_selected(mat, weekday_choice, hour_choice), use_container_width=True, width=800)
        try:
            val = mat.loc[hour_choice, weekday_choice]
        except Exception:
            val = None
        # st.markdown(f"**{type_choice}** para **{weekday_choice} {hour_choice}**: **{val if val is not None else '-'}**")

# Garantir que a leitura esteja no session_state
if "reading" not in st.session_state:
    st.session_state["reading"] = None
