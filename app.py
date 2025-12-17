#app.py

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Etheria", layout="wide", initial_sidebar_state="expanded")

st.title("Etheria — Apresentação")

# URL do vídeo no YouTube
col1, col2 = st.columns([2.5,1])
with col1:
    st.video("https://www.youtube.com/watch?v=odibXYdEBPo")

st.markdown(
    """
    *Etheria* é o espaço simbólico onde os ciclos astrológicos e numerológicos se encontram.  
    O **Painel Esotérico** funciona como um mapa interativo: cada planeta, cada número e cada ciclo 
    são chaves para compreender tanto os movimentos externos quanto os internos.  
    Aqui, você é convidado a transformar símbolos em práticas, e práticas em consciência.
    """
)