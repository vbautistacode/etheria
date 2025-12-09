# app.py
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

st.set_page_config(page_title="Etheria — Painel Esotérico", layout="wide")
st.title("Etheria — Painel Esotérico")
st.markdown("Leituras personalizadas: Numerologia pitagórica e Cabalística, Arcanos, Influências planetárias.")

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

st.sidebar.markdown("---")
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

c1, c2, c3 = st.columns(3)
with c1:
    style = get_planet_style(planet_ast, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(f"### {style.get('icon','')} Ano Astrológico - Matéria")
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_ast}</div>", unsafe_allow_html=True)
    st.caption(CICLO_MENOR_ASTROLOGICO_DESC)
with c2:
    style = get_planet_style(planet_teo, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(f"### {style.get('icon','')} Ano Teosófico - Espírito")
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_teo}</div>", unsafe_allow_html=True)
    st.caption(CICLO_MENOR_TEOSOFICO_DESC)
with c3:
    style = get_planet_style(planet_35, lang="pt") if use_colors else {"color": "#000000", "icon": ""}
    st.markdown(f"### {style.get('icon','')} Ciclo Maior de 35")
    st.markdown(f"<div style='font-size:20px;color:{style['color']};font-weight:600'>{planet_35}</div>", unsafe_allow_html=True)
    st.caption(CICLO_MAIOR_DESC)

# --------------------------------------------------------------------
# --- Interpretação coletiva dinâmica
# UI snippet para exibir em 3 colunas (colar onde apropriado em app.py)
interp_ast, interp_teo, interp_35 = generate_three_interpretations(planet_ast, planet_teo, planet_35, summary=_summary_obj if '_summary_obj' in globals() else None)

col1, col2, col3 = st.columns(3)

with col1:
    
    st.write(interp_ast["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_ast["long"])

with col2:
    st.write(interp_teo["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_teo["long"])

with col3:
    st.write(interp_35["short"])
    with st.expander("Ver interpretação completa"):
        st.markdown(interp_35["long"])
# -------------------------

# -------------------------
# Layout principal: visualizador e área de resultados
# -------------------------
left, = st.columns([4])

with left:
    st.subheader("Relógio Tátvico e suas Correlações")
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
st.markdown("---")
st.header("Análises do Consulente")

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
        st.info("Gere a leitura para habilitar as abas com conteúdo detalhado.")

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

# Criar abas principais
tab_influencias, tab_num, tab_cabalistica = st.tabs(
    ["Influências", "Numerologia", "Numerologia Cabalística"]
)

#-------------------------
# --- Aba: Influências ---
#-------------------------

with tab_influencias:
    # garantir que 'influences' esteja importado (se não estiver, importe defensivamente)
    # --- import defensivo do módulo influences ---
    try:
        from etheria import influences
    except Exception as e:
        influences = None
        st.error(f"Erro ao importar 'influences': {e}")
        st.stop()

    # --- util auxiliar (normalização simples) ---
    def _normalize_name(name: str) -> str:
        if not name:
            return ""
        nfkd = unicodedata.normalize("NFKD", str(name))
        only_ascii = "".join([c for c in nfkd if not unicodedata.combining(c)])
        return only_ascii.strip().lower()

    # --- garantir dob (tenta várias fontes) ---
    _dob = None
    if 'dob' in locals() and dob:
        _dob = dob
    elif 'dob' in globals() and globals().get('dob'):
        _dob = globals().get('dob')
    elif st.session_state.get("dob"):
        _dob = st.session_state.get("dob")
    elif isinstance(data, dict) and data.get("dob"):
        _dob = data.get("dob")

    if not _dob:
        st.warning("Data de nascimento (dob) não encontrada. Use a entrada do consulente; usando data atual como fallback.")
        _dob = datetime.now()

    # garantir variáveis derivadas de dob
    try:
        dob = _dob
        birth_year = int(dob.year)
    except Exception:
        try:
            birth_year = int(datetime.fromisoformat(str(_dob)).year)
            dob = datetime.fromisoformat(str(_dob))
        except Exception:
            birth_year = datetime.now().year
            dob = datetime.now()

    current_year = datetime.now().year
    birth_age = current_year - birth_year

    # garantir weekday (se não definido em escopo anterior)
    if 'weekday' not in locals() or not weekday:
        try:
            weekday_map = {
                0: "Segunda-feira", 1: "Terça-feira", 2: "Quarta-feira",
                3: "Quinta-feira", 4: "Sexta-feira", 5: "Sábado", 6: "Domingo"
            }
            weekday = weekday_map.get(dob.weekday(), "Segunda-feira")
        except Exception:
            weekday = "Segunda-feira"

    # garantir função planet_from_matrix_safe disponível
    if 'planet_from_matrix_safe' not in globals():
        st.error("Função planet_from_matrix_safe não encontrada. Verifique sua definição no app.")
        st.stop()

    # --- calcular/reusar cycles, p_age, p_year_now (defensivo) ---
    cycles = locals().get('cycles') if 'cycles' in locals() else None
    p_age = locals().get('p_age') if 'p_age' in locals() else None
    p_year_now = locals().get('p_year_now') if 'p_year_now' in locals() else None

    try:
        if not cycles:
            cycles = influences.build_major_cycles(birth_year=birth_year, max_age=120)
    except Exception:
        try:
            cycles = influences.build_major_cycles(birth_year, 120)
        except Exception:
            cycles = []

    try:
        if p_age is None:
            p_age = influences.planet_for_age(cycles, birth_age) if cycles else None
    except Exception:
        p_age = None

    try:
        if p_year_now is None:
            p_year_now = influences.planet_for_year(cycles, current_year) if cycles else None
    except Exception:
        p_year_now = None

    # --- obter matriz de Planeta/Hora e calcular p_hour / p_weekday ---
    p_hour = None
    p_weekday = None
    birth_time = st.session_state.get("birth_time_influences") or st.session_state.get("birth_time") or "07:55"
    mat = (data.get("matrices") or {}).get("Planeta") if isinstance(data, dict) else None

    if mat is None:
        st.info("Matriz de planetas não encontrada em data['matrices']. Leituras por hora serão ignoradas.")
    else:
        try:
            p_hour = planet_from_matrix_safe(mat, weekday, birth_time)
        except Exception as e:
            st.write("DEBUG: erro ao calcular p_hour:", str(e))
            p_hour = None
        try:
            p_weekday = mat.iloc[0].get(weekday)
            if pd.isna(p_weekday):
                p_weekday = None
        except Exception:
            p_weekday = None

    # --- definir start_planet com prioridade: p_hour > p_age > p_year_now ---
    start_planet = p_hour or p_age or p_year_now or None

    # --- reconstruir ciclos para exibição (se possível com start_planet) ---
    try:
        cycles_for_display = influences.build_major_cycles(birth_year=birth_year, max_age=120, start_planet=start_planet)
    except TypeError:
        cycles_for_display = cycles or []
    except Exception:
        cycles_for_display = cycles or []

    # --- preparar DataFrame de ciclos com validações ---
    if not cycles_for_display:
        df_cycles = pd.DataFrame(columns=["planet", "start_age", "end_age", "start_year", "end_year"])
    else:
        df_cycles = pd.DataFrame(cycles_for_display)

    expected_cols = ["planet", "start_age", "end_age", "start_year", "end_year"]
    for c in expected_cols:
        if c not in df_cycles.columns:
            df_cycles[c] = pd.NA

    # converter colunas para numérico com coerção
    for col in ["start_age", "end_age", "start_year", "end_year"]:
        df_cycles[col] = pd.to_numeric(df_cycles[col], errors="coerce").fillna(-1).astype(int)

    df_cycles_display = df_cycles[expected_cols].copy()
    df_cycles_display["current"] = df_cycles_display.apply(
        lambda r: (birth_age >= r["start_age"] and birth_age <= r["end_age"]) if (r["start_age"] >= 0 and r["end_age"] >= 0) else False,
        axis=1
    )

    # --- Leituras por ciclo: um expander por ciclo (ordem da tabela) ---
    st.markdown("### Influências dos Tattwas ao longo da vida")
    st.markdown("Esta seção apresenta as influências planetárias ao longo dos ciclos de vida, com interpretações específicas para cada período.")
    # st.write(f"**Nome:** {full_name or '—'}")
    # st.write(f"**Nascimento:** {dob.isoformat()}  **Idade:** {birth_age}")
    # checkbox para controlar exibição da tabela (opcional)
    show_table = st.checkbox("Mostrar tabela resumida de ciclos ao final", value=False)
    st.success(f"**Roadmap de ciclos (ordem de interpretação)**")
    
    # garantir result como fallback
    result = locals().get('result') or {}

    for idx, row in df_cycles_display.reset_index(drop=True).iterrows():
        planet_name = row["planet"] if pd.notna(row["planet"]) else "—"
        start_age = int(row["start_age"]) if row["start_age"] >= 0 else None
        end_age = int(row["end_age"]) if row["end_age"] >= 0 else None
        start_year = int(row["start_year"]) if row["start_year"] >= 0 else None
        end_year = int(row["end_year"]) if row["end_year"] >= 0 else None
        is_current = bool(row["current"])

        age_range = f"{start_age}–{end_age} anos" if start_age is not None and end_age is not None else "faixa desconhecida"
        year_range = f"{start_year}–{end_year}" if start_year is not None and end_year is not None else "anos desconhecidos"
        header = f"{idx+1}. {planet_name} — {age_range} ({year_range})"
        if is_current:
            header = f"**➡ {header} (período atual)**"

        # tentar obter interpretação específica do módulo influences (várias assinaturas)
        interp_short = None
        interp_long = None
        try:
            if hasattr(influences, "planet_interpretation"):
                p = influences.planet_interpretation(planet_name, birth_year=birth_year, age=birth_age)
                if isinstance(p, dict):
                    interp_short = p.get("short")
                    interp_long = p.get("long")
            elif hasattr(influences, "interpret_planet"):
                p = influences.interpret_planet(planet_name, birth_year=birth_year, age=birth_age)
                if isinstance(p, dict):
                    interp_short = p.get("short")
                    interp_long = p.get("long")
            elif hasattr(influences, "interpret_combined"):
                try_sources = {"year": planet_name, "hour": planet_name, "weekday": planet_name}
                p = influences.interpret_combined(try_sources, cycles=cycles_for_display, birth_year=birth_year, birth_age=start_age or birth_age)
                if isinstance(p, dict) and p.get("interpretation"):
                    interp_short = p["interpretation"].get("short")
                    interp_long = p["interpretation"].get("long")
        except Exception:
            interp_short = interp_short or "Interpretação não disponível."
            interp_long = interp_long or "Detalhes não disponíveis para este ciclo."

        # fallback final: usar result (interpretação já calculada) ou texto genérico
        if not interp_short and not interp_long:
            try:
                if isinstance(result, dict) and result.get("by_planet") and result["by_planet"].get(planet_name):
                    p = result["by_planet"][planet_name]
                    interp_short = p.get("short")
                    interp_long = p.get("long")
                else:
                    interp_short = result.get("interpretation", {}).get("short") or "Interpretação não disponível."
                    interp_long = result.get("interpretation", {}).get("long") or "Detalhes não disponíveis."
            except Exception:
                interp_short = interp_short or "Interpretação não disponível."
                interp_long = interp_long or "Detalhes não disponíveis."

        # exibir expander (aberto se for o período atual)
        with st.expander(header, expanded=is_current):
            st.markdown(f"**Resumo:** {interp_short or '—'}")
            st.write(interp_long or "—")
            st.markdown(f"_Período: {age_range} — {year_range}_")
            if is_current:
                st.markdown(
                    "<div style='padding:6px;border-left:6px solid #006100;background:#C6EFCE'>"
                    "<strong>Você está neste período agora.</strong></div>",
                    unsafe_allow_html=True
                )
    # Exibir tabela resumida apenas se o usuário marcar a opção
    if show_table:
        st.markdown("---")
        st.markdown("**Tabela resumida de ciclos**")
        st.dataframe(
            df_cycles_display.style.apply(
                lambda row: ['background-color: #fff3b0' if row['current'] else '' for _ in row],
                axis=1
            ),
            use_container_width=True
        )

# --- Aba: Numerologia (Pitagórica) ---
with tab_num:
    st.subheader("Numerologia Pitagórica")

    # imports necessários (assegure que estão no topo do arquivo também)
    from datetime import date, datetime

    # garantir session_state básicos (uma única vez)
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("dob", date(1990, 4, 25))
    st.session_state.setdefault("num_keep_masters", True)

    # chaves locais para inputs visíveis nesta aba (evitam conflito com sidebar)
    st.session_state.setdefault("num_full_name", st.session_state.get("full_name", ""))
    st.session_state.setdefault("num_dob", st.session_state.get("dob", date(1990, 4, 25)))

    # Input visível (opcional). Se preferir oculto, comente estas linhas.
    # full_name_input = st.text_input("Nome completo", value=st.session_state.get("num_full_name", ""), key="num_full_name_input")
    # dob_input = st.date_input("Data de nascimento", value=st.session_state.get("num_dob", date(1990, 4, 25)), key="num_dob_input")

    # checkbox (usar chave única)
    keep_masters = st.checkbox(
        "Preservar números mestres (11,22,33)",
        value=st.session_state.get("num_keep_masters", True),
        key="num_keep_masters"
    )

    # decidir valores finais: priorizar sidebar (full_name/dob) se preenchidos, senão inputs locais
    full_name_val = st.session_state.get("full_name") or full_name_input or ""
    dob_val = st.session_state.get("dob") or dob_input or None

    # Mensagem informativa se dados faltarem
    if not full_name_val or not dob_val:
        st.info("Preencha nome e data no sidebar ou aqui para ver a numerologia automaticamente.")
    else:
        # calcular Número de Poder apenas quando dob_val for válido
        try:
            power_num = numerology.power_number_from_dob(dob_val, keep_masters=keep_masters, master_min=11)
        except Exception:
            power_num = {"value": None, "raw": None}

        # Tentar calcular sem deixar exceções vazarem para a UI
        try:
            rpt = numerology.full_numerology_report(
                full_name_val,
                dob_val,
                method="pythagorean",
                keep_masters=keep_masters
            )

            # Header com principais números
            c1, c2, c3 = st.columns([2, 3, 2])
            with c1:
                st.markdown("**Nome**")
                st.write(rpt.get("full_name", "—"))
                st.markdown("**Nascimento**")
                st.write(rpt.get("dob", "—"))
            with c2:
                st.markdown("### Principais números")
                cols = st.columns(4)
                cols[0].metric("Caminho de Vida", rpt.get("life_path", {}).get("value", "—"))
                cols[1].metric("Expressão", rpt.get("expression", {}).get("value", "—"))
                cols[2].metric("Desejo da Alma", rpt.get("soul_urge", {}).get("value", "—"))
                cols[3].metric("Personalidade", rpt.get("personality", {}).get("value", "—"))
            with c3:
                st.markdown("**Maturidade**")
                maturity = rpt.get("maturity", {}) or {}
                st.write(f"{maturity.get('value','—')} — {maturity.get('short','')}")

                st.markdown("**Número de Poder**")

                # obter objeto power do relatório ou do cálculo local
                pv = rpt.get("power_number") or power_num or {}
                if not isinstance(pv, dict):
                    pv = {}

                pv_value = pv.get("value")
                pv_raw = pv.get("raw")

                # se value ausente mas raw presente, reduzir raw para obter value
                if pv_value is None and pv_raw is not None:
                    try:
                        pv_value = numerology.reduce_number(pv_raw, keep_masters=keep_masters, master_min=11)
                    except Exception:
                        # fallback manual: somar dígitos e reduzir
                        try:
                            digits = numerology._to_digit_list(pv_raw) if hasattr(numerology, "_to_digit_list") else [int(ch) for ch in str(pv_raw) if ch.isdigit()]
                            s = sum(digits) if digits else None
                            pv_value = numerology.reduce_number(s, keep_masters=keep_masters, master_min=11) if s is not None and hasattr(numerology, "reduce_number") else s
                        except Exception:
                            pv_value = None

                # obter texto curto associado (fallbacks: NUM_INTERPRETATIONS_SHORT -> NUM_TEMPLATES -> "")
                pv_short = ""
                try:
                    if pv_value is not None:
                        pv_short = numerology.NUM_INTERPRETATIONS_SHORT.get(str(pv_value), "")
                        if not pv_short and hasattr(numerology, "NUM_TEMPLATES"):
                            pv_short = numerology.NUM_TEMPLATES.get(int(pv_value), {}).get("short", "")
                except Exception:
                    pv_short = ""

                # exibir no mesmo formato de maturity: "valor — texto curto"
                display_value = pv_value if pv_value is not None else "—"
                display_short = pv_short or "—"
                st.write(f"{display_value} — {display_short}")

            st.markdown("---")

            # Personal (Ano / Mês / Dia)
            # st.markdown("#### Números Pessoais (Ano / Mês / Dia)")
            # personal = rpt.get("personal", {})
            # st.write(f"**Ano**: {personal.get('year', {}).get('value','—')} — {personal.get('year', {}).get('description','')}")
            # st.write(f"**Mês**: {personal.get('month', {}).get('value','—')} — {personal.get('month', {}).get('description','')}")
            # st.write(f"**Dia**: {personal.get('day', {}).get('value','—')} — {personal.get('day', {}).get('description','')}")

            # rótulos em português
            PORTUGUESE_LABELS = {
                "life_path": "Caminho de Vida",
                "expression": "Expressão",
                "soul_urge": "Desejo da Alma",
                "personality": "Personalidade",
                "maturity": "Maturidade"
            }

            # interpretação detalhada
            st.markdown("### Interpretações")
            for key in ("life_path", "expression", "soul_urge", "personality", "maturity", "power_number"):
                block = rpt.get(key, {}) or {}
                label = block.get("number") or block.get("value") or "—"
                title = PORTUGUESE_LABELS.get(key, key.replace("_", " ").title())
                with st.expander(f"{title} — {label}"):
                    st.markdown(f"**Qualidade:** {block.get('short','—')}")
                    st.markdown(f"**Definição:** {block.get('medium','—')}")

            st.session_state["last_calc_error"] = None

            # análise do número do ano (usar dob_val)
            try:
                today_year = datetime.now().year
                ann_analysis = analyze_personal_year_from_dob(dob_val, target_year=today_year)
                st.markdown("---")
                st.markdown("### Análise do Número do Ano")
                st.write(f"**Data:** {ann_analysis.get('date','—')}")
                st.write(f"**Número reduzido:** {ann_analysis.get('reduced_number','—')}")
                st.markdown("**Resumo:**")
                st.write(ann_analysis.get('short','—'))
                st.markdown("**Detalhe:**")
                st.write(ann_analysis.get('long','—'))
            except Exception:
                pass

        except Exception as exc:
            st.session_state["last_calc_error"] = str(exc)
            st.warning("Não foi possível calcular a numerologia no momento. Verifique os dados e tente novamente.")
            if st.session_state.get("debug_influences"):
                st.write("DEBUG: erro resumido:", st.session_state["last_calc_error"])

# --- Aba: Numerologia Cabalística (refatorado, defensivo) ---
with tab_cabalistica:
    # importar numerology defensivamente
    try:
        from etheria import numerology
    except Exception as e:
        st.error(f"Erro ao importar 'numerology': {e}")
        st.stop()

    st.subheader("Numerologia Cabalística")

    # Inicializar chaves básicas (sidebar pode ter definido "full_name" e "dob")
    st.session_state.setdefault("full_name", "")
    st.session_state.setdefault("dob", date(1990, 4, 25))
    st.session_state.setdefault("numc_keep_masters", True)

    # Chaves locais da aba (evitam conflito com sidebar)
    st.session_state.setdefault("numc_full_name", st.session_state.get("full_name", ""))
    st.session_state.setdefault("numc_dob", st.session_state.get("dob", date(1990, 4, 25)))

    keep_masters_c = st.checkbox(
        "Preservar números mestres (11,22,33)",
        value=st.session_state.get("numc_keep_masters", True),
        key="numc_keep_masters"
    )

    # Priorizar valores do sidebar se existirem (modo "oculto")
    # Leitura tolerante: primeiro sidebar/session_state "full_name"/"dob", senão inputs locais
    if st.session_state.get("full_name"):
        full_name = st.session_state["full_name"]
    else:
        # usar valor do input local (já definido acima)
        try:
            full_name = full_name_input_c
        except NameError:
            full_name = st.session_state.get("numc_full_name", "")

    if st.session_state.get("dob"):
        dob = st.session_state["dob"]
    else:
        dob = dob_input_c or st.session_state.get("numc_dob", date(1990, 4, 25))

    # util: formatar date para string dd/mm/YYYY
    def _fmt_date(d):
        try:
            return d.strftime("%d/%m/%Y")
        except Exception:
            return str(d)

    # Renderers (idênticos, mas usando .get para evitar KeyError)
    def _render_header(report):
        c1, c2, c3 = st.columns([2, 3, 2])
        with c1:
            st.markdown("**Nome**")
            st.write(report.get("full_name", "—"))
            st.markdown("**Nascimento**")
            st.write(report.get("dob", "—"))
        with c2:
            st.markdown("### Principais números")
            cols = st.columns(4)
            cols[0].metric("Caminho de Vida", report.get("life_path", {}).get("value", "—"))
            cols[1].metric("Expressão", report.get("expression", {}).get("value", "—"))
            cols[2].metric("Desejo da Alma", report.get("soul_urge", {}).get("value", "—"))
            cols[3].metric("Personalidade", report.get("personality", {}).get("value", "—"))
        with c3:
            st.markdown("**Maturidade**")
            maturity = report.get("maturity", {})
            st.write(f"{maturity.get('value','—')} — {maturity.get('short','')}")
            st.markdown("**Influência Anual (vigente)**")
            annual = report.get("annual_influence_by_name", {})
            st.write(annual.get("value", "—"))

    # _render_pinnacles removed intentionally; inline rendering used where needed

    def _render_personal(report):
        st.markdown("#### Personal (Ano / Mês / Dia)")
        personal = report.get("personal", {})
        year = personal.get("year", {})
        month = personal.get("month", {})
        day = personal.get("day", {})
        st.write(f"**Ano**: {year.get('value','—')} — {year.get('description','')}")
        st.write(f"**Mês**: {month.get('value','—')} — {month.get('description','')}")
        st.write(f"**Dia**: {day.get('value','—')} — {day.get('description','')}")

    def _render_brutos_e_breakdown(report, name):
        cols_raw = st.columns(3)
        cols_raw[0].write(f"Expressão (bruto): {report.get('expression', {}).get('raw_total')}")
        cols_raw[1].write(f"Desejo da Alma (bruto): {report.get('soul_urge', {}).get('raw_total')}")
        cols_raw[2].write(f"Personalidade (bruto): {report.get('personality', {}).get('raw_total')}")

        # breakdown por letra (se a função existir)
        if hasattr(numerology, "letter_value_breakdown"):
            try:
                dbg = numerology.letter_value_breakdown(name)
                # exibir sumário compacto se desejar (opcional)
            except Exception:
                pass

    def _render_interpretations(report):
        st.markdown("### Interpretações")
        for key in ("life_path", "expression", "soul_urge", "personality", "maturity"):
            block = report.get(key, {})
            label = block.get("number", block.get("value", "—"))
            with st.expander(f"{key.replace('_',' ').title()} — {label}"):
                st.markdown(f"**Curto:** {block.get('short','—')}")
                st.markdown(f"**Médio:** {block.get('medium','—')}")
                st.markdown(f"**Longo:** {block.get('long','—')}")

    # Validar e calcular (defensivo)
    if full_name and dob:
        try:
            rptc = numerology.full_cabalistic_report(full_name, dob, keep_masters=keep_masters_c)

            # exibir cabeçalho e seções principais
            _render_header(rptc)

            # Inline rendering for pinnacles (replaces removed _render_pinnacles)
            try:
                pinn = rptc.get("pinnacles", {}) or {}
                if pinn:
                    st.markdown("---")
                    st.markdown("#### Pinnacles / Períodos")
                    # build a safe table dict with explicit values (avoid None entries)
                    table_data = {
                        "Pinnacle": ["P1", "P2", "P3", "P4"],
                        "Valor": [
                            pinn.get("pinnacle_1", "—"),
                            pinn.get("pinnacle_2", "—"),
                            pinn.get("pinnacle_3", "—"),
                            pinn.get("pinnacle_4", "—")
                        ]
                    }
                    st.table(table_data)
            except Exception:
                # não interromper a renderização se pinnacles falhar
                pass

            _render_personal(rptc)
            _render_brutos_e_breakdown(rptc, full_name)
            _render_interpretations(rptc)

            # análise da data de aniversário vigente (ex.: aniversário deste ano)
            try:
                today_year = datetime.now().year
                ann_date = date(today_year, dob.month, dob.day)
                ann_str = ann_date.strftime("%d/%m/%Y")
                ann_analysis = numerology.analyze_date_str(ann_str)
                st.markdown("---")
                st.markdown("### Análise do Número do Ano")
                st.write(f"**Data:** {ann_analysis.get('date','—')}")
                st.write(f"**Número reduzido:** {ann_analysis.get('reduced_number','—')}")
                st.write(f"**Quadrante:** {ann_analysis.get('quadrant','—')} — {ann_analysis.get('theme','—')}")
                st.write(f"**Chakra:** {ann_analysis.get('chakra','—')}")
                st.markdown("**Resumo:**")
                st.write(ann_analysis.get('short','—'))
                st.markdown("**Detalhe:**")
                st.write(ann_analysis.get('long','—'))
            except Exception:
                # falha na análise do aniversário não interrompe o restante
                pass

            # Roadmap/cycles: só executar se 'cycles' estiver definido e for iterável
            cycles_obj = locals().get("cycles") or globals().get("cycles")
            go_to_last = locals().get("go_to_last", False)
            if cycles_obj and isinstance(cycles_obj, (list, tuple)):
                st.markdown("---")
                last_idx = len(cycles_obj) - 1 if cycles_obj else None
                for idx, c in enumerate(cycles_obj):
                    is_current = False
                    try:
                        is_current = (c.get("start_age") == (datetime.now().year - dob.year))
                    except Exception:
                        pass
                    open_expander = is_current or (go_to_last and last_idx is not None and idx == last_idx)
                    header = f"{idx+1}. {c.get('label','—')} — Número {c.get('number','—')}"
                    if is_current:
                        header = f"**➡ {header} (período atual)**"
                    if go_to_last and last_idx is not None and idx == last_idx:
                        header = f"**🔚 {header} (último)**"

                    num = c.get("number")
                    template = numerology.NUM_TEMPLATES.get(num, {}) if hasattr(numerology, "NUM_TEMPLATES") else {}
                    short = c.get("short") or template.get("short") or "—"
                    long = c.get("long") or template.get("long") or "—"
                    chakra = None
                    if hasattr(numerology, "quadrant_for_number"):
                        try:
                            chakra = numerology.quadrant_for_number(num).get("chakra")
                        except Exception:
                            chakra = None

                    with st.expander(header, expanded=open_expander):
                        st.markdown(f"**Número:** {num}  —  **Chakra:** {chakra or '—'}")
                        st.markdown(f"**Resumo:** {short}")
                        st.write(long)
                        st.markdown(f"_Idade: {c.get('start_age')} — Ano: {c.get('start_year')}_")
                        if is_current:
                            st.markdown(
                                "<div style='padding:6px;border-left:4px solid #8a2be2;background:#fff9e6'>"
                                "<strong>Você está neste período agora.</strong></div>",
                                unsafe_allow_html=True
                            )
                        if go_to_last and last_idx is not None and idx == last_idx:
                            st.markdown(
                                "<div style='padding:6px;border-left:4px solid #2b8aef;background:#eef6ff'>"
                                "<strong>Último ciclo (120 anos).</strong></div>",
                                unsafe_allow_html=True
                            )

        except Exception as e:
            # registrar erro resumido sem expor traceback; não bloqueia a UI
            st.warning("Não foi possível calcular a numerologia cabalística no momento. Verifique os dados e tente novamente.")
            if st.session_state.get("debug_influences"):
                st.write("DEBUG: erro resumido:", str(e))
    else:
        st.info("Preencha nome e data (no sidebar ou aqui) para ver a numerologia cabalística automaticamente.")