#app.py

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Etheria — Apresentação", layout="wide")

st.title("Etheria — Apresentação")

# URL do vídeo no YouTube
col1, col2 = st.columns([1,1])  # proporção 2:1
with col1:
    st.video("https://www.youtube.com/watch?v=odibXYdEBPo")