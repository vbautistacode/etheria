# 10_Mapa_do_Dia.py (versão simplificada: entrada por cidade e data/hora + Lottie)
import streamlit as st
from datetime import datetime
import json
from streamlit.components.v1 import html as st_html

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

st.caption("Preencha os campos na barra lateral e clique em 'Gerar Leitura do Dia' para receber a interpretação simbólica.")

# -------------------------
# Sidebar: entrada manual (cidade + data/hora)
# -------------------------
st.sidebar.header("Local e data")
st.sidebar.markdown("Informe a cidade e a data/hora para a qual deseja gerar a leitura.")

# cidade livre (string)
city = st.sidebar.text_input("Cidade (ex.: São Paulo, BR)", value="")

# data e hora: usar date_input + time_input para controle fino
col_date, col_time = st.sidebar.columns([2, 1])
with col_date:
    date_input = st.date_input("Data", value=datetime.now().date())
with col_time:
    # usar hora atual como valor padrão; o usuário pode ajustar
    time_input = st.sidebar.time_input("Hora (opcional)", value=datetime.now().time())

focus = st.sidebar.selectbox("Foco da leitura", ["Geral", "Trabalho", "Relacionamentos", "Saúde"], index=0)

# -------------------------
# Normalizar data/hora escolhida (sem função ISO separada)
# -------------------------
# compor ISO a partir de date_input e time_input; se hora não fornecida, usar 00:00
if date_input:
    if time_input:
        client_dt = datetime.combine(date_input, time_input)
    else:
        client_dt = datetime.combine(date_input, datetime.min.time())
else:
    client_dt = datetime.now()
client_time_iso = client_dt.isoformat()

# -------------------------
# Mostrar preferências ao usuário
# -------------------------
display_time = client_time_iso
st.markdown(f"**Data e hora (preferência):** {display_time}")
st.markdown(f"**Local (preferência):** {city if city else 'não informado'}")

st.markdown("---")
st.markdown("Pressione **Gerar Leitura do Dia** para enviar ao modelo Etheria IA.")

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
# Lottie animation setup
# -------------------------
LOTTIE_URL = "https://assets10.lottiefiles.com/packages/lf20_touohxv0.json"  # substitua se desejar outro
_lottie_html = f"""
<script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>
<div style="display:flex;align-items:center;justify-content:center;">
  <lottie-player src="{LOTTIE_URL}"  background="transparent"  speed="1"  style="width:320px;height:220px;"  loop  autoplay></lottie-player>
</div>
"""

# -------------------------
# Ação do botão: gerar mapa (com Lottie)
# -------------------------
if st.button("Gerar Leitura do Dia"):
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
            # placeholder para animação Lottie
            _anim_placeholder = st.empty()
            _anim_placeholder.components.v1.html(_lottie_html, height=240)

            with st.spinner("Gerando interpretação com o modelo..."):
                try:
                    result = generate_ai_text_from_chart(chart_summary, prompt_template=prompt_template)
                except Exception as e:
                    st.error(f"Erro ao chamar serviço de geração: {e}")
                    result = {"error": str(e)}

            # remover animação visual após a execução
            _anim_placeholder.empty()

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
    "- Gere a Leitura do Dia pela manhã para planejar o dia.\n"
    "- Combine a leitura com uma prática curta (respiração, cristal, aroma) sugerida pelo texto."
)

if _IMPORT_ERROR:
    st.sidebar.error("Erro ao importar services: " + _IMPORT_ERROR)