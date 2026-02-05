# 10_Mapa_do_Dia.py (atualizado: usa st.query_params e título "Mapa do Dia 🧭")
import streamlit as st
from datetime import datetime
import time
import hashlib
import json
import requests
import urllib.parse

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
    "Gere uma leitura simbólica do 'céu do dia' para a sua localização. "
    "O sistema tenta obter a localização e hora do seu navegador; se não for possível, usa detecção por IP ou entrada manual."
)

# -------------------------
# Leitura de query params (usada para receber dados do navegador)
# -------------------------
# substituído st.experimental_get_query_params por st.query_params (API estável)
query_params = st.query_params
# parâmetros esperados: lat, lon, city, client_time (ISO)
qp_lat = query_params.get("lat", [None])[0]
qp_lon = query_params.get("lon", [None])[0]
qp_city = query_params.get("city", [None])[0]
qp_client_time = query_params.get("client_time", [None])[0]

# -------------------------
# Função para detectar via IP (fallback)
# -------------------------
def detect_location_by_ip():
    try:
        resp = requests.get("https://ipapi.co/json/", timeout=3.5)
        if resp.status_code == 200:
            data = resp.json()
            city = data.get("city") or data.get("region") or ""
            lat = str(data.get("latitude") or data.get("lat") or "")
            lon = str(data.get("longitude") or data.get("lon") or "")
            return city, lat, lon
    except Exception:
        pass
    return None, None, None

# -------------------------
# Botão para obter localização do navegador (JS -> redireciona com query params)
# -------------------------
st.sidebar.header("Localização e preferências")
st.sidebar.markdown(
    "Se possível, clique em **Detectar pelo navegador** para usar a localização e hora do seu dispositivo."
)

if st.sidebar.button("Detectar pelo navegador"):
    html = """
    <script>
    function toQueryString(obj) {
      return Object.keys(obj).map(k => encodeURIComponent(k) + '=' + encodeURIComponent(obj[k])).join('&');
    }
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(function(pos) {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        const now = new Date().toISOString();
        const params = {
          lat: lat,
          lon: lon,
          client_time: now,
          city: ''
        };
        const qs = toQueryString(params);
        const base = window.location.href.split('?')[0];
        window.location.href = base + '?' + qs;
      }, function(err) {
        const now = new Date().toISOString();
        const qs = 'client_time=' + encodeURIComponent(now);
        const base = window.location.href.split('?')[0];
        window.location.href = base + '?' + qs;
      }, {timeout:10000});
    } else {
      const now = new Date().toISOString();
      const base = window.location.href.split('?')[0];
      window.location.href = base + '?client_time=' + encodeURIComponent(now);
    }
    </script>
    <p>Detectando localização no navegador... se nada acontecer, permita o acesso à localização ou recarregue a página.</p>
    """
    st.components.v1.html(html, height=120)
    st.stop()

# -------------------------
# Preencher campos com prioridade: query params (navegador) -> IP detect -> manual
# -------------------------
city = qp_city or ""
lat = qp_lat or ""
lon = qp_lon or ""
client_time_iso = qp_client_time or ""

if not (lat and lon):
    # tentar detecção por IP
    ip_city, ip_lat, ip_lon = detect_location_by_ip()
    if ip_city and (not city):
        city = ip_city
    if ip_lat and ip_lon and (not lat and not lon):
        lat = ip_lat
        lon = ip_lon

# inputs manuais (se necessário)
st.sidebar.markdown("Se necessário, ajuste manualmente:")
city = st.sidebar.text_input("Cidade (opcional)", value=city or "")
lat = st.sidebar.text_input("Latitude (opcional)", value=lat or "")
lon = st.sidebar.text_input("Longitude (opcional)", value=lon or "")

focus = st.sidebar.selectbox("Foco da leitura", ["Geral", "Trabalho", "Relacionamentos", "Saúde"], index=0)

# usar client_time_iso se disponível; caso contrário, usar hora local do servidor como fallback
if client_time_iso:
    try:
        client_dt = datetime.fromisoformat(client_time_iso.replace("Z", "+00:00")) if client_time_iso.endswith("Z") else datetime.fromisoformat(client_time_iso)
        display_time = client_dt.isoformat(timespec="minutes")
    except Exception:
        display_time = client_time_iso
else:
    display_time = datetime.now().isoformat(timespec="minutes")

st.markdown(f"**Data e hora (preferência):** {display_time}")
st.markdown(f"**Local (preferência):** {city if city else 'não informado'} {f'({lat},{lon})' if lat and lon else ''}")

st.markdown("---")
st.markdown("Pressione **Gerar Mapa do Dia** para enviar o prompt ao modelo (usa o template diário).")

# -------------------------
# Montador de chart_summary para o serviço
# -------------------------
def build_chart_summary_for_day(place: str, lat: str, lon: str, date_time_iso: str, focus: str):
    def _normalize_coord(v):
        if v is None:
            return ""
        s = str(v).strip()
        s = s.replace(",", ".")
        try:
            _ = float(s)
            return s
        except Exception:
            return ""
    lat_n = _normalize_coord(lat)
    lon_n = _normalize_coord(lon)

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
        "lat": lat_n,
        "lon": lon_n,
        "focus": focus,
        "instruction": (
            f"Mapa do Dia para {date_text} {time_text} em {place or 'não informada'} (lat:{lat_n or 'n/a'}, lon:{lon_n or 'n/a'}). "
            f"Foco: {focus}. Gerar leitura prática e simbólica conforme o template diário."
        )
    }
    return chart_summary

# -------------------------
# Ação do botão: gerar mapa
# -------------------------
if st.button("Gerar Mapa do Dia"):
    if not city and not (lat and lon):
        st.error("Forneça ao menos a cidade ou latitude/longitude (detecção automática falhou).")
    else:
        chart_summary = build_chart_summary_for_day(city, lat, lon, client_time_iso or datetime.now().isoformat(), focus)

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
                if result.get("prompt"):
                    with st.expander("Mostrar prompt enviado ao modelo (debug)"):
                        st.code(result["prompt"][:8000])

# -------------------------
# Dicas e debug
# -------------------------
st.markdown("---")
st.markdown("**Dicas de uso**")
st.markdown(
    "- Gere o Mapa do Dia pela manhã para planejar o dia.\n"
    "- Se usar frequentemente, o serviço do backend já aplica cache para reduzir chamadas.\n"
    "- Combine a leitura com uma prática curta (respiração, cristal, aroma) sugerida pelo texto."
)

if _IMPORT_ERROR:
    st.sidebar.error("Erro ao importar services: " + _IMPORT_ERROR)