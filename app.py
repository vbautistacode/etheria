#app.py

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Etheria — Apresentação", layout="wide")

st.title("Etheria — Apresentação")

# URL do vídeo no YouTube
col1, col2 = st.columns([2,1])  # proporção 2:1
with col1:
    st.video("https://www.youtube.com/watch?v=odibXYdEBPo")

# Alternativa local (fallback) — use apenas se o arquivo for pequeno
local_demo = Path("static/institucional.mp4")
if youtube_url:
    st.video(youtube_url)
elif local_demo.exists():
    st.video("static/institucional.mp4")
else:
    st.info("Vídeo de demonstração não encontrado. Coloque assets/demo_screen.mp4 ou defina youtube_url.")