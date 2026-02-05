# 10_Mapa_do_Dia.py
import streamlit as st
from datetime import datetime
import time
import hashlib
import json
import requests

# importa o serviço que você forneceu (ajuste o caminho se necessário)
try:
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    from etheria.services.generator_service import generate_ai_text_from_chart
except Exception as e:
    generate_ai_text_from_chart = None
    _IMPORT_ERROR = str(e)

st.set_page_config(page_title="10 — Mapa do Dia", layout="wide")
st.title("Mapa do Dia 🧭")

st.markdown(
    "Gere uma leitura simbólica do 'céu do dia' para a sua localização. "
    "O sistema monta um prompt e envia ao modelo Gemini via o serviço configurado."
)

# --- tentativa de detecção automática de localização via IP (fallback para manual) ---
def detect_location_by_ip():
    """Tenta obter cidade, latitude e longitude via serviço público de IP.
    Retorna (city, lat, lon) ou (None, None, None) em caso de falha."""
    try:
        # ipapi.co é simples e costuma funcionar; você pode trocar por outro serviço
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

st.sidebar.header("Localização e preferências")
auto_detect = st.sidebar.checkbox("Detectar localização automaticamente (via IP)", value=True)

city = ""
lat = ""
lon = ""

if auto_detect:
    with st.spinner("Detectando localização..."):
        city_det, lat_det, lon_det = detect_location_by_ip()
        if city_det:
            city = city_det
            lat = lat_det
            lon = lon_det
            st.sidebar.success(f"Local detectado: {city} {f'({lat},{lon})' if lat and lon else ''}")
        else:
            st.sidebar.warning("Detecção automática falhou. Insira manualmente abaixo.")
            city = st.sidebar.text_input("Cidade (ex.: São Paulo)", "")
            lat = st.sidebar.text_input("Latitude (opcional)", "")
            lon = st.sidebar.text_input("Longitude (opcional)", "")
else:
    city = st.sidebar.text_input("Cidade (ex.: São Paulo)", "")
    lat = st.sidebar.text_input("Latitude (opcional)", "")
    lon = st.sidebar.text_input("Longitude (opcional)", "")

focus = st.sidebar.selectbox("Foco da leitura", ["Geral", "Trabalho", "Relacionamentos", "Saúde"], index=0)

now = datetime.now()
now_iso = now.isoformat(timespec="minutes")

st.markdown(f"**Data e hora local:** {now_iso}")
st.markdown(f"**Local:** {city if city else 'não informado'} {f'({lat},{lon})' if lat and lon else ''}")
st.markdown("Pressione **Gerar Mapa do Dia** para enviar o prompt ao modelo.")

# --- construtor de chart_summary simples para o serviço generator_service ---
def build_chart_summary_for_day(place: str, lat: str, lon: str, date_time: datetime, focus: str):
    """
    Monta um chart_summary mínimo que o generator_service aceita.
    O serviço irá montar o prompt a partir desses campos; se não houver posições planetárias,
    o prompt ainda será gerado com instruções contextuais.
    """
    chart_summary = {
        "place": place or "",
        "bdate": date_time.date().isoformat(),
        "btime": date_time.time().strftime("%H:%M"),
        "lat": lat or "",
        "lon": lon or "",
        # instrução customizada para o prompt do generator_service
        "instruction": (
            f"Interprete o 'Mapa do Dia' para {date_time.date().isoformat()} às {date_time.time().strftime('%H:%M')} "
            f"na localização {place or 'não informada'} (lat:{lat or 'n/a'}, lon:{lon or 'n/a'}). "
            f"Contexto: foco da leitura = {focus}. Retorne em português com seções: "
            "1) Resumo (2-3 frases). 2) Três pontos de atenção. 3) Prática simples em 3 passos. "
            "4) Sugestões simbólicas: 2 pedras, 1 cor para cromoterapia, 1 óleo essencial. "
            "Se não houver efemérides, use linguagem simbólica e prática."
        )
    }
    return chart_summary

# --- função que usa o serviço para gerar texto (com mensagens de erro amigáveis) ---
def generate_mapa(chart_summary):
    if generate_ai_text_from_chart is None:
        return {
            "error": "Serviço de geração não disponível. Verifique import de services.generator_service.",
            "analysis_text": None,
            "raw_text": None,
            "prompt": None
        }
    try:
        # generate_ai_text_from_chart retorna um dict com analysis_text, raw_text, prompt, error, etc.
        out = generate_ai_text_from_chart(chart_summary)
        # garantir formato mínimo
        if not isinstance(out, dict):
            return {"error": "Resposta inesperada do serviço de geração.", "analysis_text": str(out), "raw_text": str(out), "prompt": None}
        return out
    except Exception as e:
        return {"error": f"Erro ao chamar serviço de geração: {e}", "analysis_text": None, "raw_text": None, "prompt": None}

# --- botão de ação ---
if st.button("Gerar Mapa do Dia"):
    if not city and not (lat and lon):
        st.error("Forneça ao menos a cidade ou latitude/longitude (detecção automática falhou).")
    else:
        chart_summary = build_chart_summary_for_day(city, lat, lon, now, focus)
        with st.spinner("Gerando interpretação com o modelo..."):
            result = generate_mapa(chart_summary)

        if result.get("error"):
            st.error(result["error"])
            # se houver prompt disponível, mostrar para debug
            if result.get("prompt"):
                st.markdown("**Prompt enviado (para debug):**")
                st.code(result["prompt"][:4000])
        else:
            # preferir analysis_text, fallback para raw_text
            text = result.get("analysis_text") or result.get("raw_text") or ""
            st.markdown("### Interpretação do Mapa do Dia")
            st.write(text)
            st.markdown("---")
            st.markdown("**Observação:** Esta leitura é simbólica e interpretativa. Use-a como orientação prática, não como previsão determinística.")
            # mostrar prompt (opcional, útil para debug)
            if result.get("prompt"):
                with st.expander("Mostrar prompt enviado ao modelo (debug)"):
                    st.code(result["prompt"][:8000])

# --- dicas de uso ---
st.markdown("---")
st.markdown("**Dicas de uso**")
st.markdown(
    "- Gere o Mapa do Dia pela manhã para planejar o dia.\n"
    "- Se usar frequentemente, o serviço do backend já aplica cache para reduzir chamadas.\n"
    "- Combine a leitura com uma prática curta (respiração, cristal, aroma) sugerida pelo texto."
)

# --- mostrar erro de import se houver ---
if ' _IMPORT_ERROR' in globals():
    st.sidebar.error("Erro ao importar services.generator_service: " + _IMPORT_ERROR)