# 07_musicoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.title("Musicoterapia 🪉🎼🎵🎶🎻")
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

# --- Mapeamentos por signo/planeta (exemplos) ---
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

# --- Nova correspondência Nota -> Planeta (solfejo) ---
# Nota: Dó "C" = Marte, Ré "D" = Sol, Mi "E" = Mercúrio,
# Fá "F" = Saturno, Sol "G" = Júpiter, Lá "A" = Vênus, Si "B" = Lua
NOTE_TO_PLANET = {
    "C (Dó)": "Marte",
    "D (Ré)": "Sol",
    "E (Mi)": "Mercúrio",
    "F (Fá)": "Saturno",
    "G (Sol)": "Júpiter",
    "A (Lá)": "Vênus",
    "B (Si)": "Lua"
}

# --- Interface lateral ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por nota musical", "Por intenção / uso", "Busca livre"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_TRACKS.keys()))
    suggested = SIGN_TO_TRACKS.get(sign, [])
elif mode == "Por planeta regente":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(set(PLANET_TO_TRACKS.keys()))))
    suggested = PLANET_TO_TRACKS.get(planet, [])
elif mode == "Por nota musical":
    note = st.sidebar.selectbox("Escolha a nota (solfejo)", list(NOTE_TO_PLANET.keys()))
    mapped_planet = NOTE_TO_PLANET.get(note)
    # sugerir faixas associadas ao planeta mapeado, se houver
    suggested = PLANET_TO_TRACKS.get(mapped_planet, [])
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", ["Relaxamento","Foco","Sono","Aterramento","Energia"])
else:
    query = st.sidebar.text_input("Busca livre (título, categoria)")

# --- Painel principal ---
st.header("Faixas, notas e correspondências")

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
    elif mode == "Por nota musical":
        st.markdown(f"**Nota selecionada:** {note}")
        st.markdown(f"**Planeta correspondente:** {mapped_planet}")
        st.markdown("**Faixas sugeridas (pelo planeta):**")
        for t in suggested:
            st.write(f"- {t}")
        st.markdown("---")
        st.markdown("**Como usar a correspondência nota→planeta**")
        st.markdown(
            "- Use a nota correspondente ao planeta para criar exercícios tonais curtos.\n"
            "- Por exemplo, tocar ou ouvir faixas centradas em Dó (Marte) para vigor e ação.\n"
            "- Combine com intenção (foco, relaxamento) para modular o efeito."
        )
    elif mode == "Por intenção / uso":
        st.markdown(f"**Intenção:** {intent}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar faixas.")

    st.markdown("---")
    st.subheader("Sugestões práticas")
    st.markdown(
        "- Para foco: experimente faixas em tonalidades com notas associadas a Mercúrio (Mi) ou Sol (Ré).\n"
        "- Para aterramento: escolha faixas com ênfase em Fá (Saturno) ou Sol (Júpiter).\n"
        "- Para energia: prefira Dó (Marte) e Lá (Vênus) dependendo da intenção."
    )

with col2:
    st.subheader("Catálogo de faixas")
    df_display = tracks_df.copy()
    if mode == "Por signo" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por planeta regente" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por nota musical" and suggested:
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

# --- Visualização rápida das correspondências nota -> planeta ---
st.markdown("---")
st.subheader("Correspondência Nota → Planeta (solfejo)")
note_table = pd.DataFrame([
    {"Nota (solfejo)": k, "Planeta": v} for k, v in NOTE_TO_PLANET.items()
])
st.table(note_table)

st.markdown("---")
st.subheader("Personalize as correspondências")
st.markdown("Se quiser fornecer listas próprias de faixas, notas ou mapeamentos signo→faixas, cole aqui e eu adapto o código.")