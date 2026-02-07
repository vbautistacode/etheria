# 10_Mapa_do_Dia.py (versão simplificada: entrada por cidade e data/hora)
import streamlit as st
from datetime import datetime
import json

# importa o serviço que você forneceu (ajuste o caminho se necessário)
try:
    from etheria.services.generator_service import generate_ai_text_from_chart
    from etheria.services.daily_prompt import build_daily_prompt_from_chart_summary
    _IMPORT_ERROR = None
except Exception as e:
    generate_ai_text_from_chart = None
    build_daily_prompt_from_chart_summary = None
    _IMPORT_ERROR = str(e)

st.set_page_config(page_title="10 — Mapa do Dia", layout="wide")
st.title("Mapa do Dia 🧭")

st.markdown("""
Sinta o dia como um mapa vivo: gere uma leitura simbólica do **céu do dia** para o lugar que você indicar.  
Agora você informa **cidade** e **data/hora** manualmente; o sistema usará esses valores para gerar a leitura.
""")

# -------------------------
# Sidebar: entrada manual (cidade + data/hora)
# -------------------------
st.sidebar.header("Local e data do Mapa do Dia")
st.sidebar.markdown("Informe a cidade e a data/hora para a qual deseja gerar o mapa. Hora opcional — se não informada, será usada a hora atual do servidor.")

# cidade livre (string)
city = st.sidebar.text_input("Cidade (ex.: São Paulo, BR)", value="")

# data e hora: usar date_input + time_input para controle fino
col_date, col_time = st.sidebar.columns([2, 1])
with col_date:
    date_input = st.date_input("Data", value=datetime.now().date())
with col_time:
    time_input = st.sidebar.time_input("Hora (opcional)", value=None)

focus = st.sidebar.selectbox("Foco da leitura", ["Geral", "Trabalho", "Relacionamentos", "Saúde"], index=0)

st.sidebar.markdown("Se preferir, cole uma data/hora ISO no campo abaixo (ex.: 2026-02-07T08:30):")
iso_input = st.sidebar.text_input("Data/hora ISO (opcional)", value="")

# -------------------------
# Normalizar data/hora escolhida
# -------------------------
def _compose_iso_from_inputs(date_obj, time_obj, iso_text):
    # prioridade: iso_text se preenchido e válido
    if iso_text and iso_text.strip():
        try:
            # tenta parse ISO
            dt = datetime.fromisoformat(iso_text.replace("Z", "+00:00")) if iso_text.endswith("Z") else datetime.fromisoformat(iso_text)
            return dt.isoformat()
        except Exception:
            # se inválido, ignorar e cair para composição manual
            pass
    # compor a partir de date + time inputs
    if date_obj:
        if time_obj:
            dt = datetime.combine(date_obj, time_obj)
        else:
            # sem hora: usar meia-noite local (00:00) para a data escolhida
            dt = datetime.combine(date_obj, datetime.min.time())
        return dt.isoformat()
    # fallback: agora
    return datetime.now().isoformat()

client_time_iso = _compose_iso_from_inputs(date_input, time_input, iso_input)

# -------------------------
# Mostrar preferências ao usuário
# -------------------------
display_time = client_time_iso
st.markdown(f"**Data e hora (preferência):** {display_time}")
st.markdown(f"**Local (preferência):** {city if city else 'não informado'}")

st.markdown("---")
st.markdown("Pressione **Gerar Mapa do Dia** para enviar ao modelo Etheria IA.")

# -------------------------
# Montador de chart_summary para o serviço (sem lat/lon obrigatórios)
# -------------------------
def build_chart_summary_for_day(place: str, date_time_iso: str, focus: str):
    """
    Gera o dicionário chart_summary esperado pelo serviço.
    Note: lat/lon ficam vazios — o serviço deve aceitar ausência de coordenadas.
    """
    dt = date_time_iso or datetime.now().isoformat()
    try:
        dt_obj = datetime.fromisoformat(dt.replace("Z", "+00:00")) if dt.endswith("Z") else datetime.fromisoformat(dt)
        date_text = dt_obj.date().isoformat()
        time_text = dt_obj.time().strftime("%H:%M")
    except Exception:
        date_text = dt
        time_text = ""

    chart_summary = {
        "place": place or "",
        "bdate": date_text,
        "btime": time_text,
        "lat": "",   # removido requisito de coordenadas
        "lon": "",
        "focus": focus,
        "instruction": (
            f"Mapa do Dia para {date_text} {time_text} em {place or 'não informada'} "
            f"(sem coordenadas). Foco: {focus}. Gerar leitura prática e simbólica conforme o template diário."
        )
    }
    return chart_summary

# -------------------------
# Ação do botão: gerar mapa
# -------------------------
if st.button("Gerar Mapa do Dia"):
    if not city:
        st.error("Forneça ao menos a cidade para gerar o mapa.")
    else:
        chart_summary = build_chart_summary_for_day(city, client_time_iso, focus)

        # montar prompt via services.daily_prompt se disponível
        prompt_template = None
        try:
            if build_daily_prompt_from_chart_summary:
                prompt_template = build_daily_prompt_from_chart_summary(chart_summary)
        except Exception:
            prompt_template = None

        # chamar o serviço de geração (gera prompt internamente se prompt_template for None)
        if generate_ai_text_from_chart is None:
            st.error("Serviço de geração não disponível. Verifique import de services.generator_service.")
        else:
            with st.spinner("Gerando interpretação com o modelo..."):
                try:
                    result = generate_ai_text_from_chart(chart_summary, prompt_template=prompt_template)
                except Exception as e:
                    st.error(f"Erro ao chamar serviço de geração: {e}")
                    result = {"error": str(e)}

            if result.get("error"):
                st.error(result["error"])
                if result.get("prompt"):
                    st.markdown("**Prompt enviado (debug):**")
                    st.code(result["prompt"][:4000])
            else:
                text = result.get("analysis_text") or result.get("raw_text") or ""
                st.markdown("### Interpretação do Mapa do Dia")
                st.write(text)
                st.markdown("---")
                st.markdown("**Observação:** Esta leitura é simbólica e interpretativa. Use-a como orientação prática, não como previsão determinística.")

# -------------------------
# Dicas e debug
# -------------------------
st.markdown("---")
st.markdown("**Dicas de uso**")
st.markdown(
    "- Gere o Mapa do Dia pela manhã para planejar o dia.\n"
    "- Combine a leitura com uma prática curta (respiração, cristal, aroma) sugerida pelo texto."
)

if _IMPORT_ERROR:
    st.sidebar.error("Erro ao importar services: " + _IMPORT_ERROR)