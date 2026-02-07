# 10_Mapa do Dia.py (refatorado: entrada por cidade e data/hora + Lottie local)
import streamlit as st
from datetime import datetime
import json
from pathlib import Path

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

st.markdown(
    """
Sinta o dia como um mapa vivo: gere uma leitura simbólica do **céu do dia** para o lugar que você indicar.  
Agora você informa **cidade** e **data/hora** manualmente; o sistema usará esses valores para gerar a leitura.
"""
)

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

focus = st.sidebar.selectbox(
    "Foco da leitura",
    ["Geral", "Trabalho", "Relacionamentos", "Saúde"],
    index=0
)

# -------------------------
# Normalizar data/hora escolhida (composição direta)
# -------------------------
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
st.markdown(f"**Data e hora (preferência):** {client_time_iso}")
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
# Lottie: carregar JSON local (se existir)
# -------------------------
# Ajuste o caminho se necessário; o arquivo deve estar no repositório do app
LOTTIE_LOCAL_PATH = Path("static/lottie/my_anim.json")
_lottie_json = None
if LOTTIE_LOCAL_PATH.exists():
    try:
        with open(LOTTIE_LOCAL_PATH, "r", encoding="utf-8") as f:
            _lottie_json = json.load(f)
    except Exception as e:
        st.sidebar.warning(f"Falha ao carregar animação Lottie local: {e}")
else:
    # se não houver arquivo local, você pode usar um URL público (opcional)
    # Exemplo (comentado): LOTTIE_URL = "https://assets10.lottiefiles.com/packages/lf20_touohxv0.json"
    _lottie_json = None

# Função utilitária para montar HTML que injeta animationData (usa lottie-web via CDN)
def _build_lottie_html(animation_data, width=320, height=220):
    """
    Recebe um objeto JSON (animation_data) e retorna HTML que carrega lottie-web
    e inicializa a animação via animationData.
    """
    anim_js = json.dumps(animation_data)
    html = f"""
<div id="lottie-container" style="display:flex;align-items:center;justify-content:center;">
  <div id="lottie-player" style="width:{width}px;height:{height}px;"></div>
</div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/bodymovin/5.9.6/lottie.min.js"></script>
<script>
  (function() {{
    try {{
      var animData = {anim_js};
      var container = document.getElementById('lottie-player');
      container.innerHTML = '';
      lottie.loadAnimation({{
        container: container,
        renderer: 'svg',
        loop: true,
        autoplay: true,
        animationData: animData
      }});
    }} catch (err) {{
      console.error("Erro ao inicializar Lottie:", err);
    }}
  }})();
</script>
"""
    return html

# -------------------------
# Ação do botão: gerar mapa (com Lottie se disponível)
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
            # se houver Lottie local, exibir via st.components.v1.html
            if _lottie_json is not None:
                try:
                    _lottie_html = _build_lottie_html(_lottie_json, width=320, height=220)
                    st.components.v1.html(_lottie_html, height=260)
                except Exception as e:
                    # não interrompe a execução; apenas loga/avisa
                    st.sidebar.warning(f"Não foi possível exibir animação Lottie: {e}")

            # mostrar spinner textual (acessibilidade)
            with st.spinner("Gerando interpretação com o modelo..."):
                try:
                    result = generate_ai_text_from_chart(chart_summary, prompt_template=prompt_template)
                except Exception as e:
                    st.error(f"Erro ao chamar serviço de geração: {e}")
                    result = {"error": str(e)}

            # garantir que o prompt fique disponível localmente para inspeção, se não vier da API
            if prompt_template and isinstance(result, dict) and "prompt" not in result:
                result["prompt"] = prompt_template

            # exibir resultado e prompt (debug opcional)
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
                st.markdown(
                    " **Observação:** Esta leitura é simbólica e interpretativa. Use-a como orientação prática, não como previsão determinística."
                )

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