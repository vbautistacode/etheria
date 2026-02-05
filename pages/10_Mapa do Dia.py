# 10_Mapa_do_Dia.py (esqueleto)
import streamlit as st
from datetime import datetime
import requests  # ou a lib que você usa para chamar Gemini

st.set_page_config("Mapa do Dia", layout="wide")
st.title("10 — Mapa do Dia")

# captura simples: pedir cidade/latlon
city = st.text_input("Cidade (ex.: São Paulo)", "São Paulo")
lat = st.text_input("Latitude", "")
lon = st.text_input("Longitude", "")
now = datetime.now().isoformat(timespec='minutes')

if st.button("Gerar Mapa do Dia"):
    prompt = f"""Interprete o "Mapa do Dia" para {now} na localização {city} (lat:{lat}, lon:{lon}). 
    Retorne em português com: 1) Resumo 2) Três pontos de atenção 3) Prática em 3 passos 4) Sugestões simbólicas (2 pedras, 1 cor, 1 óleo)."""
    # chame aqui sua função que envia prompt ao Gemini e retorna texto
    # exemplo fictício:
    # response_text = call_gemini_api(prompt)
    response_text = "Resposta simulada — substitua pela chamada real ao Gemini."
    st.markdown("### Interpretação do Gemini")
    st.write(response_text)