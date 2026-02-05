# 10_Mapa_do_Dia.py
import streamlit as st
from datetime import datetime
import time
import hashlib

st.set_page_config(page_title="10 — Mapa do Dia", layout="wide")
st.title("Mapa do Dia 🧭")

st.markdown(
    "Gere uma leitura simbólica do 'céu do dia' para a sua localização. "
    "O sistema monta um prompt e envia ao modelo configurado (Gemini)."
)

# --- Inputs de localização e preferências ---
st.sidebar.header("Localização e preferências")
use_manual = st.sidebar.checkbox("Inserir localização manualmente", value=True)

if use_manual:
    city = st.sidebar.text_input("Cidade (ex.: São Paulo)", "São Paulo")
    lat = st.sidebar.text_input("Latitude (opcional)", "")
    lon = st.sidebar.text_input("Longitude (opcional)", "")
else:
    st.sidebar.info("Se preferir, insira manualmente cidade/lat/lon.")
    city = st.sidebar.text_input("Cidade (ex.: São Paulo)", "São Paulo")
    lat = st.sidebar.text_input("Latitude (opcional)", "")
    lon = st.sidebar.text_input("Longitude (opcional)", "")

focus = st.sidebar.selectbox("Foco da leitura", ["Geral", "Trabalho", "Relacionamentos", "Saúde"], index=0)

now = datetime.now()
now_iso = now.isoformat(timespec="minutes")

st.markdown(f"**Data e hora local:** {now_iso}")
st.markdown(f"**Local:** {city} {f'({lat},{lon})' if lat and lon else ''}")
st.markdown("Pressione **Gerar Mapa do Dia** para enviar o prompt ao modelo.")

# --- Helper: prompt builder ---
def build_prompt(date_iso, time_iso, city, lat, lon, focus):
    prompt = (
        f"Interprete o 'Mapa do Dia' para {date_iso} às {time_iso} na localização {city}"
    )
    if lat and lon:
        prompt += f" (lat:{lat}, lon:{lon})"
    prompt += (
        f".\nContexto: foco da leitura = {focus}.\n"
        "Retorne em português com as seguintes seções numeradas:\n"
        "1) Resumo (2-3 frases): o que o dia oferece.\n"
        "2) Três pontos de atenção (cada um em 1 linha).\n"
        "3) Prática simples em 3 passos para aproveitar o dia.\n"
        "4) Sugestões simbólicas: 2 pedras, 1 cor para cromoterapia, 1 óleo essencial.\n"
        "Se não tiver acesso a efemérides precisas, use linguagem simbólica e prática. "
        "Se possível, inclua uma breve sugestão de ritual de 1-2 minutos."
    )
    return prompt

# --- Placeholder: função que chama o Gemini ---
def call_gemini(prompt_text):
    """
    Placeholder para integração com o Gemini.
    Substitua o corpo desta função pela chamada real à API que você já configurou.
    Deve retornar uma string com a resposta em português.
    """
    # Exemplo de retorno simulado (substituir pela chamada real)
    simulated = (
        "Resumo: O dia favorece comunicação e ajustes práticos; energia para resolver pendências.\n\n"
        "Pontos de atenção:\n"
        "- Evite decisões impulsivas nas primeiras horas.\n"
        "- Atenção a mal-entendidos em conversas rápidas.\n"
        "- Reserve tempo para revisar documentos importantes.\n\n"
        "Prática em 3 passos:\n"
        "1) Respire 3 vezes profundamente e defina a intenção 'clareza'.\n"
        "2) Faça uma lista de 3 prioridades para o dia.\n"
        "3) Ao final do dia, registre um aprendizado rápido.\n\n"
        "Sugestões simbólicas: Pedras: Citrino, Sodalita; Cor: Azul-claro; Óleo: Alecrim."
    )
    time.sleep(0.6)  # simula latência
    return simulated

# --- Cache curto para evitar chamadas repetidas (30 minutos) ---
@st.cache_data(ttl=1800)
def get_mapa_cached(prompt_text):
    # gerar hash simples para chave
    key = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest()
    # chamar a função que integra com Gemini (ou serviço)
    return call_gemini(prompt_text)

# --- Ação do botão ---
if st.button("Gerar Mapa do Dia"):
    date_iso = now.date().isoformat()
    time_iso = now.time().strftime("%H:%M")
    prompt = build_prompt(date_iso, time_iso, city, lat, lon, focus)
    with st.spinner("Consultando o modelo e interpretando o céu..."):
        try:
            response_text = get_mapa_cached(prompt)
        except Exception as e:
            st.error("Erro ao consultar o modelo. Verifique a integração com o Gemini.")
            response_text = None

    if response_text:
        st.markdown("### Interpretação do Mapa do Dia")
        st.write(response_text)
        st.markdown("---")
        st.markdown("**Observação:** Esta leitura é simbólica e interpretativa. Use-a como orientação prática, não como previsão determinística.")
        st.markdown("Se desejar uma leitura mais técnica (posições planetárias), forneça efemérides ou permita que o backend calcule as posições e as inclua no prompt.")
    else:
        st.error("Não foi possível obter a interpretação no momento. Tente novamente mais tarde.")

# --- Opções adicionais ---
st.markdown("---")
st.markdown("**Dicas de uso**")
st.markdown(
    "- Gere o Mapa do Dia pela manhã para planejar o dia.\n"
    "- Se usar frequentemente, considere cache local para reduzir chamadas.\n"
    "- Combine a leitura com uma prática curta (respiração, cristal, aroma) sugerida pelo texto."
)