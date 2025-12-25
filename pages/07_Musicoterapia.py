# 07_musicoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Musicoterapia", layout="wide")
st.title("Musicoterapia")
st.markdown(
    """
    Musicoterapia: uso terapêutico do som para regular estados emocionais e promover
    relaxamento ou foco. Sugestões de playlists, sons elementais e sessões guiadas.
    """
)

# --- Dados de faixas e categorias (exemplos) ---
TRACKS_CSV = """Título,Artista/Coleção,Categoria,Efeito,URL
Ondas Suaves,Sons da Natureza,Relaxamento,Calmante,https://example.com/waves
Batida Alfa,Ambiente,Foco,Estimula concentração,https://example.com/alpha
Tonalidade Terra,Sons Amadeirados,Aterramento,Estabiliza,https://example.com/earth
Cascata Noturna,Sons da Natureza,Sono,Induz relaxamento profundo,https://example.com/water
Ritmo Vital,Trilhas Energéticas,Energia,Aumenta vigor,https://example.com/energy
"""
tracks_df = pd.read_csv(StringIO(TRACKS_CSV))

# Mapeamentos por signo/planeta (exemplos)
SIGN_TO_TRACKS = {
    "Áries": ["Ritmo Vital"], "Touro": ["Tonalidade Terra"], "Gêmeos": ["Batida Alfa"],
    "Câncer": ["Cascata Noturna"], "Leão": ["Ritmo Vital"], "Virgem": ["Batida Alfa"],
    "Libra": ["Tonalidade Terra"], "Escorpião": ["Ondas Suaves"], "Sagitário": ["Ritmo Vital"],
    "Capricórnio": ["Tonalidade Terra"], "Aquário": ["Batida Alfa"], "Peixes": ["Ondas Suaves"]
}
PLANET_TO_TRACKS = {
    "Sol": ["Ritmo Vital"], "Lua": ["Cascata Noturna"], "Marte": ["Ritmo Vital"],
    "Vênus": ["Tonalidade Terra"], "Mercúrio": ["Batida Alfa"], "Júpiter": ["Ondas Suaves"],
    "Saturno": ["Tonalidade Terra"], "Netuno": ["Ondas Suaves"], "Urano": ["Batida Alfa"], "Plutão": ["Ondas Suaves"]
}

# --- Interface lateral ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por intenção / uso", "Busca livre"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_TRACKS.keys()))
    suggested = SIGN_TO_TRACKS.get(sign, [])
elif mode == "Por planeta regente":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(set(PLANET_TO_TRACKS.keys()))))
    suggested = PLANET_TO_TRACKS.get(planet, [])
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", ["Relaxamento","Foco","Sono","Aterramento","Energia"])
else:
    query = st.sidebar.text_input("Busca livre (título, categoria)")

# --- Painel principal ---
st.header("Faixas e playlists")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown("**Faixas sugeridas:**")
        for t in suggested:
            st.write(f"- {t}")
    elif mode == "Por planeta regente":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown("**Faixas associadas:**")
        for t in suggested:
            st.write(f"- {t}")
    elif mode == "Por intenção / uso":
        st.markdown(f"**Intenção:** {intent}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar faixas.")

    st.markdown("---")
    st.subheader("Sugestões de uso")
    st.markdown(
        "- Para relaxamento: ouvir 10–20 minutos em volume baixo, com foco na respiração.\n"
        "- Para foco: usar faixas com batidas suaves e frequências alfa por 20–40 minutos.\n"
        "- Para sono: reduzir estímulos visuais e usar trilhas contínuas sem picos."
    )

with col2:
    st.subheader("Catálogo de faixas")
    df_display = tracks_df.copy()
    if mode == "Por signo" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por planeta regente" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por intenção / uso":
        if intent == "Relaxamento":
            df_display = df_display[df_display["Categoria"].str.contains("Relaxamento|Natureza", case=False, na=False)]
        elif intent == "Foco":
            df_display = df_display[df_display["Categoria"].str.contains("Foco|Ambiente", case=False, na=False)]
        elif intent == "Sono":
            df_display = df_display[df_display["Categoria"].str.contains("Sono|Natureza", case=False, na=False)]
    else:
        if mode == "Busca livre" and query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda r: q in str(r["Título"]).lower() or q in str(r["Categoria"]).lower(), axis=1)]

    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    st.markdown("### Detalhes da faixa")
    tracks = df_display["Título"].tolist()
    if tracks:
        sel = st.selectbox("Escolha uma faixa", [""] + tracks)
        if sel:
            row = df_display[df_display["Título"] == sel].iloc[0]
            st.markdown(f"**{row['Título']}** — *{row['Artista/Coleção']}*")
            st.markdown(f"- **Categoria:** {row['Categoria']}")
            st.markdown(f"- **Efeito:** {row['Efeito']}")
            st.markdown(f"- **URL / referência:** {row['URL']}")
    else:
        st.info("Nenhuma faixa encontrada com os filtros atuais.")

st.markdown("---")
st.subheader("Personalize as correspondências")
st.markdown("Se quiser fornecer listas próprias de faixas ou mapeamentos signo→faixas, cole aqui e eu adapto o código.")