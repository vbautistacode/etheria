#app.py

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Etheria — Apresentação", layout="wide")

st.title("Etheria — Apresentação")

# URL do vídeo no YouTube
youtube_url = "https://www.youtube.com/watch?v=odibXYdEBPo"
st.video(youtube_url)

# Alternativa local (fallback) — use apenas se o arquivo for pequeno
local_demo = Path("static/institucional.mp4")
if youtube_url:
    st.video(youtube_url)
elif local_demo.exists():
    st.video("static/institucional.mp4")
else:
    st.info("Vídeo de demonstração não encontrado. Coloque assets/demo_screen.mp4 ou defina youtube_url.")