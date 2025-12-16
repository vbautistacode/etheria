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
st.title("Etheria | Painel Esotérico")
st.markdown(
    """
    *Etheria* é o espaço simbólico onde os ciclos astrológicos e numerológicos se encontram.  
    O **Painel Esotérico** funciona como um mapa interativo: cada planeta, cada número e cada ciclo 
    são chaves para compreender tanto os movimentos externos quanto os internos.  
    Aqui, você é convidado a transformar símbolos em práticas, e práticas em consciência.
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

st.sidebar.header("Ajustes de ciclos")
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

st.sidebar.divider()
st.sidebar.header("Entrada do Consulente")
# --- Sidebar (exemplo) ---
def _sync_sidebar_to_tab():
    # copia o valor do sidebar para a key usada na aba
    st.session_state["num_full_name"] = st.session_state.get("full_name", "")

# widget no sidebar (key "full_name")
full_name = st.sidebar.text_input(
    "Nome completo",
    value=st.session_state.get("full_name", ""),
    key="full_name",
    on_change=_sync_sidebar_to_tab
)

# data de nascimento no sidebar (mesma ideia)
def _sync_sidebar_dob_to_tab():
    st.session_state["num_dob"] = st.session_state.get("dob", st.session_state.get("num_dob", date(1990,4,25)))

dob = st.sidebar.date_input(
    "Data de nascimento",
    value=st.session_state.get("dob", date(1990,4,25)),
    key="dob",
    on_change=_sync_sidebar_dob_to_tab,
    min_value=date(1900, 1, 1),
    max_value=date(2100, 12, 31)
)

# inicializa antes de criar o widget
st.session_state.setdefault("birth_time_influences", "07:55")

# cria o widget uma única vez (sempre)
birth_time = st.sidebar.text_input(
    "Hora de nascimento (HH:MM)",
    value=st.session_state["birth_time_influences"],
    key="birth_time_influences"
)

generate_btn = st.sidebar.button("Gerar leitura")

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

st.header("Ciclos Astrológicos")
st.markdown("Os ciclos anuais refletem as energias predominantes que influenciam o consulente ao longo do ano atual.")

interp_ast, interp_teo, interp_35 = generate_three_interpretations(planet_ast, planet_teo, planet_35, summary=_summary_obj if '_summary_obj' in globals() else None)

c1, c2, c3 = st.columns(3)
with c1:
    style = get_planet_style(planet_ast, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(
    f"<h3 style='font-size:20px;font-weight:600' "
    f"title='{CICLO_MENOR_ASTROLOGICO_DESC}'>{style.get('icon','')} Ciclo Anual Astrológico</h3>",
    unsafe_allow_html=True
    )
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_ast}</div>", unsafe_allow_html=True)
    
    st.write(interp_ast["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_ast["long"])

with c2:
    style = get_planet_style(planet_teo, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(
    f"<h3 style='font-size:20px;font-weight:600' "
    f"title='{CICLO_MENOR_TEOSOFICO_DESC}'>{style.get('icon','')} Ciclo Anual Teosófico</h3>",
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
    f"title='{CICLO_MAIOR_DESC}'>{style.get('icon','')} Ciclo Maior de 35 anos</h3>",
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
    st.header("Relógio Tátvico e suas Correlações")
    st.markdown("Sistema esotérico que mede o tempo de acordo com a vibração desses princípios (tattwas). Está relacionado a mudança de energéticas ao longo do dia e suas influências.")

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

# Quando o botão Gerar leitura for pressionado, gerar e armazenar leitura
if generate_btn:
    try:
        from etheria import rules, interpretations
    except Exception:
        try:
            from esoteric_rules import rules, interpretations
        except Exception:
            rules = None
            interpretations = None

    if rules is None:
        # mostrar erro global no topo da página (ou no sidebar)
        st.sidebar.error("O pacote de regras não foi encontrado. Coloque 'etheria' ou 'esoteric_rules' no PYTHONPATH.")
    elif not full_name:
        st.sidebar.warning("Digite o nome completo.")
    else:
        tables = {
            "cycle_35": data.get("cycle_35"),
            "cycle_1year": data.get("cycle_1year"),
            "letter_map": data.get("letter_map"),
            "correlations": data["corr_df"],
        }
        try:
            reading = rules.generate_reading(full_name, dob, tables=tables, cycle_mode=DEFAULT_CYCLE_MODE)
            st.session_state["reading"] = reading
            st.sidebar.success("Leitura gerada e armazenada.")
        except Exception as e:
            st.sidebar.error(f"Erro ao gerar leitura: {e}")

# Área principal: manter visualizador (esquerda) e abaixo criar abas
# (o visualizador já está na coluna esquerda; aqui criamos as abas na área principal inteira)
st.header("Análises Planetárias e Numerológicas")

# Mostrar resumo rápido do consulente no topo da área principal
col_info, _ = st.columns([3, 1])
with col_info:
    # st.markdown("**Consulente**")
    # st.write(f"**Nome:** {full_name or '—'}")
    # st.write(f"**Data de nascimento:** {dob.isoformat() if dob else '—'}")
    if st.session_state.get("reading"):
        r = st.session_state["reading"]
        st.write(f"**Idade (estimada):** {r.get('age', '—')} anos")
    else:
        st.info("Preencha os dados de nascimento no formulário lateral para habilitar as abas com conteúdo detalhado.")

def planet_from_matrix_safe(mat: pd.DataFrame, weekday: str, hhmm: str) -> Optional[str]:
    """
    Retorna o valor da matriz 'mat' para o weekday e hora aproximada.
    - mat: DataFrame com índice de horas no formato 'HH:00' e colunas com nomes de dias.
    - weekday: nome do dia (ex.: 'Segunda-feira', 'Terça-feira', etc.).
    - hhmm: hora no formato 'HH:MM' ou 'HH'.
    Retorna string do planeta ou None se não encontrado.
    """
    if mat is None or not isinstance(mat, pd.DataFrame):
        return None

    # normalizar weekday para corresponder às colunas da matriz
    weekday_candidates = [weekday, weekday.capitalize(), weekday.title()]
    col = None
    for c in weekday_candidates:
        if c in mat.columns:
            col = c
            break
    if col is None:
        # tentar correspondência por substring curta (ex.: 'Segunda' -> 'Segunda-feira')
        for c in mat.columns:
            if weekday.lower().split("-")[0] in c.lower():
                col = c
                break
    if col is None:
        return None

    # extrair hora do hhmm
    try:
        hour = int(str(hhmm).split(":")[0])
    except Exception:
        try:
            hour = int(str(hhmm))
        except Exception:
            return None

    # formar bucket esperado 'HH:00'
    bucket = f"{hour:02d}:00"
    if bucket in mat.index:
        val = mat.at[bucket, col]
        return None if pd.isna(val) else str(val)

    # se bucket não existir, procurar índice de horas mais próximo
    try:
        # extrair horas do índice que contenham ':'
        idx_hours = []
        for idx in mat.index:
            s = str(idx)
            if ":" in s:
                try:
                    idx_hours.append(int(s.split(":")[0]))
                except Exception:
                    continue
        if not idx_hours:
            return None
        closest = min(idx_hours, key=lambda x: abs(x - hour))
        bucket = f"{closest:02d}:00"
        if bucket in mat.index:
            val = mat.at[bucket, col]
            return None if pd.isna(val) else str(val)
    except Exception:
        return None

    return None