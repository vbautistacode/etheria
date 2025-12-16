import streamlit as st
st.set_page_config(page_title="Início", layout="wide")

from pages.Inicio import main as inicio_main
inicio_main()