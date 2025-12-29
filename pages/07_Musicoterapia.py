# 07_musicoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.title("Musicoterapia 🪉")
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

# --- Obras clássicas: metadados e mapeamento nota->planeta ---
CLASSICAL_CSV = """Título,Composer,Work,Key,URL
Symphony No.5,Beethoven,Symphony No.5,C minor,https://youtu.be/your_beethoven5_link
Symphony No.9,Beethoven,Symphony No.9 (Choral),D minor,https://youtu.be/your_beethoven9_link
Symphony No.3,Eroica,Beethoven,Symphony No.3,E♭ major,https://youtu.be/your_beethoven3_link
Symphony No.41,Jupiter,Mozart,Symphony No.41,C major,https://youtu.be/your_mozart41_link
Eine kleine Nachtmusik,Mozart,Serenade No.13,G major,https://youtu.be/your_mozart_nachtmusik_link
Toccata and Fugue,Bach,Toccata and Fugue in D minor,D minor,https://youtu.be/your_bach_toccata_link
Brandenburg Concerto No.3,Bach,Brandenburg Concerto No.3,G major,https://youtu.be/your_bach_brandenburg3_link
Ride of the Valkyries,Wagner,Die Walküre - Ride,G major,https://youtu.be/your_wagner_ride_link
"""
# carregar obras clássicas
classical_df = pd.read_csv(StringIO(CLASSICAL_CSV))

# função para extrair a nota tônica base (C D E F G A B) de uma string Key
def tonic_to_note(key):
    if not isinstance(key, str) or key.strip() == "":
        return ""
    # pega a primeira "palavra" da key (ex.: "C#", "D", "E♭", "C")
    base = key.split()[0]
    # normaliza enarmônicos e símbolos
    base = base.replace('♯', '#').replace('♭', 'b')
    # retorna apenas a letra base (C D E F G A B)
    return base[0].upper()

# mapa curto nota -> planeta (letras)
NOTE_TO_PLANET_SHORT = {
    'C': 'Marte',
    'D': 'Sol',
    'E': 'Mercúrio',
    'F': 'Saturno',
    'G': 'Júpiter',
    'A': 'Vênus',
    'B': 'Lua'
}

# aplica transformação e mapeamento
classical_df['Tonic'] = classical_df['Key'].apply(tonic_to_note)
classical_df['Planet'] = classical_df['Tonic'].map(NOTE_TO_PLANET_SHORT).fillna("—")

# padroniza colunas para concatenar com tracks_df
# se tracks_df não tiver as colunas Composer/Work/Key, criá-las antes da concatenação
for col in ['Composer','Work','Key','Tonic','Planet','URL','Título']:
    if col not in tracks_df.columns:
        tracks_df[col] = ""

# concatena (mantém o catálogo original e adiciona as obras clássicas)
tracks_df = pd.concat([tracks_df, classical_df.rename(columns={'Título':'Título'})], ignore_index=True, sort=False)

# --- Explicações resumidas por planeta (para mostrar ao usuário) ---
PLANET_MUSIC_EXPLANATIONS = {
    'Marte': 'Marte (Dó) — energia de ação e vigor; obras em C tendem a ser percebidas como diretas e incisivas.',
    'Sol': 'Sol (Ré) — presença e clareza; obras em D costumam transmitir brilho e afirmação.',
    'Mercúrio': 'Mercúrio (Mi) — agilidade mental e comunicação; peças em E favorecem leveza e fluidez.',
    'Saturno': 'Saturno (Fá) — estrutura e profundidade; obras em F trazem sensação de estabilidade.',
    'Júpiter': 'Júpiter (Sol) — expansão e nobreza; obras em G costumam soar amplas e otimistas.',
    'Vênus': 'Vênus (Lá) — harmonia e beleza; peças em A evocam suavidade e afeto.',
    'Lua': 'Lua (Si) — sensibilidade e introspecção; obras em B podem soar etéreas ou contemplativas.'
}

# --- UI adicional: filtros por Composer / Planet / Tonic ---
# (substitua ou acrescente aos controles laterais existentes)
st.sidebar.markdown("---")
st.sidebar.subheader("Filtros clássicos")
composer_choices = sorted([c for c in tracks_df['Composer'].unique() if pd.notna(c) and c != ""])
composer_choices = ["Todos"] + composer_choices
composer_sel = st.sidebar.selectbox("Compositor", composer_choices)

planet_choices = sorted([p for p in tracks_df['Planet'].unique() if pd.notna(p) and p != ""])
planet_choices = ["Todos"] + planet_choices
planet_sel = st.sidebar.selectbox("Planeta (via tônica)", planet_choices)

tonic_choices = sorted([t for t in tracks_df['Tonic'].unique() if pd.notna(t) and t != ""])
tonic_choices = ["Todos"] + tonic_choices
tonic_sel = st.sidebar.selectbox("Tônica (nota)", tonic_choices)

# aplica filtros no df_display (exemplo simples)
def apply_classical_filters(df):
    df2 = df.copy()
    if composer_sel != "Todos":
        df2 = df2[df2['Composer'] == composer_sel]
    if planet_sel != "Todos":
        df2 = df2[df2['Planet'] == planet_sel]
    if tonic_sel != "Todos":
        df2 = df2[df2['Tonic'] == tonic_sel]
    return df2

# quando exibir detalhes de uma faixa clássica, mostrar explicação do planeta
# (integre isso no bloco que mostra detalhes da faixa/track)

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