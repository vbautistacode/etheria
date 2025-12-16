# app.py - Apresentação audiovisual do projeto
import streamlit as st
from pathlib import Path
import time

st.set_page_config(page_title="Apresentação ETHERIA", layout="wide")

# --- Configurações de slides: editar conforme seu projeto ---
# Cada slide: title, subtitle, text, image (path or URL), audio (path), video (URL or path)
SLIDES = [
    {
        "title": "ETHERIA",
        "subtitle": "Plataforma de astrologia e ferramentas",
        "text": "Visão geral do projeto: objetivos, arquitetura e principais recursos.",
        "image": "assets/cover.png",
        "audio": "assets/cover_narration.mp3",
        "video": None
    },
    {
        "title": "Arquitetura",
        "subtitle": "Como o sistema está organizado",
        "text": "Microserviços, módulos principais e fluxo de dados.",
        "image": "assets/architecture.png",
        "audio": "assets/arch_narration.mp3",
        "video": None
    },
    {
        "title": "Demonstração",
        "subtitle": "Renderização de mapas e export",
        "text": "Mostramos a função render_wheel_plotly e export PNG.",
        "image": None,
        "audio": None,
        "video": "https://www.youtube.com/watch?v=EXAMPLE"  # substitua por URL real ou "assets/demo.mp4"
    },
    {
        "title": "Roadmap",
        "subtitle": "Próximos passos",
        "text": "Funcionalidades planejadas, integração e deploy.",
        "image": "assets/roadmap.png",
        "audio": "assets/roadmap_narration.mp3",
        "video": None
    },
    {
        "title": "Contato",
        "subtitle": "Contribua e participe",
        "text": "Repositório, issues e como colaborar.",
        "image": "assets/contact.png",
        "audio": None,
        "video": None
    }
]

ASSETS_DIR = Path(__file__).parent / "assets"

# --- Utilitários ---
def exists_local(path):
    if not path:
        return False
    p = Path(path)
    if p.is_absolute():
        return p.is_file()
    return (ASSETS_DIR / path).is_file()

def local_path(path):
    p = Path(path)
    if p.is_absolute():
        return str(p)
    return str(ASSETS_DIR / path)

# --- UI principal ---
st.title("Apresentação do projeto")
st.markdown("Use as setas ou os botões abaixo para navegar. Se houver narração, clique em play para ouvir.")

col1, col2 = st.columns([1, 3])
with col1:
    start = st.button("Iniciar apresentação")
    slide_index = st.number_input("Slide", min_value=1, max_value=len(SLIDES), value=1, step=1)
    auto_play = st.checkbox("Auto avançar slides", value=False)
    auto_delay = st.slider("Segundos por slide", 2, 20, 8)
with col2:
    # espaço para preview do slide atual
    pass

# manter estado entre reruns
if "current" not in st.session_state:
    st.session_state.current = 0

if start:
    st.session_state.current = 0
else:
    # sincronizar com number_input
    st.session_state.current = max(0, min(len(SLIDES)-1, int(slide_index)-1))

# navegação simples
nav_col1, nav_col2, nav_col3 = st.columns([1,1,1])
with nav_col1:
    if st.button("Anterior"):
        st.session_state.current = max(0, st.session_state.current - 1)
with nav_col2:
    if st.button("Próximo"):
        st.session_state.current = min(len(SLIDES)-1, st.session_state.current + 1)
with nav_col3:
    if st.button("Ir para último"):
        st.session_state.current = len(SLIDES)-1

# render do slide atual
slide = SLIDES[st.session_state.current]
st.markdown("---")
st.header(slide.get("title", ""))
if slide.get("subtitle"):
    st.subheader(slide["subtitle"])
st.write(slide.get("text", ""))

# imagem
if slide.get("image"):
    if exists_local(slide["image"]):
        st.image(local_path(slide["image"]), use_column_width=True)
    else:
        # assume URL
        st.image(slide["image"], use_column_width=True)

# vídeo
if slide.get("video"):
    vid = slide["video"]
    if exists_local(vid):
        st.video(local_path(vid))
    else:
        st.video(vid)

# áudio de narração
if slide.get("audio"):
    aud = slide["audio"]
    if exists_local(aud):
        st.audio(local_path(aud))
    else:
        st.audio(aud)

# indicadores e auto play
st.markdown(f"**Slide {st.session_state.current + 1} de {len(SLIDES)}**")
if auto_play:
    # avançar automaticamente com delay
    time.sleep(auto_delay)
    if st.session_state.current < len(SLIDES)-1:
        st.session_state.current += 1
        # forçar rerun
        st.experimental_rerun()

# rodapé com créditos
st.markdown("---")
st.caption("Apresentação gerada pelo wrapper app.py — personalize SLIDES para ajustar conteúdo e mídias.")
