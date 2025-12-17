#app.py

import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Etheria", layout="wide", initial_sidebar_state="expanded")

st.title("Etheria — Apresentação ☯️")

# URL do vídeo no YouTube
col1, col2 = st.columns([2.5,1])
with col1:
    st.video("https://www.youtube.com/watch?v=odibXYdEBPo")

st.markdown(
    """
    **Etheria** é um espaço simbólico onde ciclos astrológicos e numerológicos se entrelaçam, 
    conectando-se aos arquétipos e revelando padrões que atravessam o tempo e a experiência humana.  
    Neste ambiente, você pode compreender as relações entre planetas, números e outras linhas de conhecimento,
    descobrindo sua própria conexão com eles.  
    Cada elemento funciona como uma chave que abre portas para interpretar tanto os movimentos 
    externos do cosmos quanto os fluxos internos da consciência.

    Mais do que observar símbolos, aqui você é convidado a vivenciá-los: transformar arquétipos em 
    práticas, práticas em consciência e consciência em presença.  
    **Etheria** é uma jornada de autoconhecimento, onde céu e terra se encontram em diálogo constante, 
    e cada escolha se integra a uma narrativa maior.

    Desfrute da sua jornada com **Etheria**
    """
)
st.caption("Navegue pelo menu ao lado")