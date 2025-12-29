# 07_musicoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO
import streamlit.components.v1 as components
from urllib.parse import urlparse, parse_qs

st.title("Musicoterapia 🪉")
st.markdown(
    """
    Musicoterapia: uso terapêutico do som para regular estados emocionais e promover
    relaxamento ou foco. Sugestões de playlists, obras clássicas e sessões guiadas.
    """
)

# ---------------------------
# Dados iniciais de faixas
# ---------------------------
TRACKS_CSV = """Título,Artista/Coleção,Categoria,Efeito,URL
Ondas Suaves,Sons da Natureza,Relaxamento,Calmante,https://www.youtube.com/watch?v=VUnN0jILbmQ
Batida Alfa,Ambiente,Foco,Estimula concentração,https://www.youtube.com/watch?v=p2_zDvtPQ-g
Tonalidade Terra,Sons Amadeirados,Aterramento,Estabiliza,https://www.youtube.com/watch?v=MIo9jbjbO7o
Cascata Noturna,Sons da Natureza,Sono,Induz relaxamento profundo,https://www.youtube.com/watch?v=V1RPi2MYptM
Ritmo Vital,Trilhas Energéticas,Energia,Aumenta vigor,https://www.youtube.com/watch?v=Lju6h-C37hE
"""
tracks_df = pd.read_csv(StringIO(TRACKS_CSV))

# ---------------------------
# Obras clássicas: metadados
# ---------------------------
CLASSICAL_CSV = """Título,Composer,Work,Key,URL
"Symphony No.5","Beethoven","Symphony No.5","C minor","https://www.youtube.com/watch?v=3ug835LFixU"
"Symphony No.9","Beethoven","Symphony No.9 (Choral)","D minor","https://www.youtube.com/watch?v=fzyO3fLV5O0"
"Symphony No.3 (Eroica)","Beethoven","Symphony No.3 (Eroica)","E♭ major","https://www.youtube.com/watch?v=your_beethoven3_link"
"Symphony No.41 (Jupiter)","Mozart","Symphony No.41 (Jupiter)","C major","https://www.youtube.com/watch?v=0vfU4cmdx-s"
"Eine kleine Nachtmusik","Mozart","Serenade No.13","G major","https://www.youtube.com/watch?v=rHZ0nkZatJk"
"Toccata and Fugue","Bach","Toccata and Fugue in D minor","D minor","https://www.youtube.com/watch?v=erXG9vnN-GI"
"Brandenburg Concerto No.3","Bach","Brandenburg Concerto No.3","G major","https://www.youtube.com/watch?v=Czsd13Mmcg0"
"Ride of the Valkyries","Wagner","Die Walküre - Ride","G major","https://www.youtube.com/watch?v=hQM97_iNXhk"
"Symphony No.6 (Pastoral)","Beethoven","Symphony No.6 (Pastoral)","F major","https://www.youtube.com/watch?v=ZQcJLE57w0U"
"Piano Concerto No.23","Mozart","Piano Concerto No.23 in A major","A major","https://www.youtube.com/watch?v=-s68kHOnpiE"
"Prelude in B","Bach","Prelude in B (ex. WTC / organ)","B minor","https://www.youtube.com/watch?v=ES7fN2lXWHU"
"Violin Concerto No.5","Mozart","Violin Concerto No.5 in A major","A major","https://www.youtube.com/watch?v=iFnfPWLxVLw"
"Cum Sancto Spiritu","Bach","Mass in B minor BWV 232","B minor","https://www.youtube.com/watch?v=4gZe5ZZsE9U"
"Prelude in E minor","Bach","Prelude in E minor (WTC)","E minor","https://www.youtube.com/watch?v=jDjJ8aL6JK0"
"Chaconne (Partita No.2)","Bach","Partita No.2 in D minor (Chaconne transcr. in B)","B minor","https://www.youtube.com/watch?v=example_bach_chaconne"
"""
classical_df = pd.read_csv(StringIO(CLASSICAL_CSV), quotechar='"', skipinitialspace=True, encoding='utf-8')

# ---------------------------
# Funções utilitárias musicais
# ---------------------------
def tonic_to_note(key: str) -> str:
    """
    Extrai a letra base da tônica (C D E F G A B) a partir de uma string Key.
    Normaliza ♯/# e ♭/b e retorna a letra maiúscula ou string vazia se inválida.
    """
    if not isinstance(key, str) or key.strip() == "":
        return ""
    base = key.split()[0]  # ex.: "C#", "D", "E♭", "C"
    base = base.replace('♯', '#').replace('♭', 'b')
    return base[0].upper() if base[0].upper() in "CDEFGAB" else ""

def get_youtube_id(u: str) -> str | None:
    """
    Extrai o ID do YouTube de uma URL (suporta youtube.com/watch?v= e youtu.be/ e embed).
    Retorna None se não for possível extrair.
    """
    try:
        parsed = urlparse(u)
        netloc = parsed.netloc.lower()
        if 'youtube' in netloc:
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                return qs['v'][0]
            path_parts = [p for p in parsed.path.split('/') if p]
            if path_parts and path_parts[-1]:
                return path_parts[-1]
        if 'youtu.be' in netloc:
            return parsed.path.lstrip('/')
    except Exception:
        return None
    return None

def render_video_from_url(url: str, width: int = 800, height: int = 450):
    """
    Tenta renderizar o vídeo no app:
    1) usa st.video(url) (suporta YouTube),
    2) se falhar, tenta renderizar iframe com o ID do YouTube,
    3) se não for YouTube ou falhar, exibe link clicável.
    """
    if not url or pd.isna(url) or str(url).strip() == "":
        st.markdown("- **Fonte:** (nenhuma URL disponível)")
        return

    st.markdown(f"- **Fonte:** [{url}]({url})")
    yt_id = get_youtube_id(url)
    try:
        st.video(url)
    except Exception:
        if yt_id:
            iframe = f"""
            <iframe width="{width}" height="{height}"
             src="https://www.youtube.com/embed/{yt_id}?rel=0"
             frameborder="0" allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture"
             allowfullscreen></iframe>
            """
            components.html(iframe, height=height + 20)
        else:
            st.markdown(f"[Abrir no YouTube]({url})")

# ---------------------------
# Mapeamento nota -> planeta
# ---------------------------
NOTE_TO_PLANET_SHORT = {
    'C': 'Marte',
    'D': 'Sol',
    'E': 'Mercúrio',
    'F': 'Saturno',
    'G': 'Júpiter',
    'A': 'Vênus',
    'B': 'Lua'
}

# aplica transformação e mapeamento nas obras clássicas
if 'Key' not in classical_df.columns:
    classical_df['Key'] = ""
classical_df['Tonic'] = classical_df['Key'].apply(tonic_to_note)
classical_df['Planet'] = classical_df['Tonic'].map(NOTE_TO_PLANET_SHORT).fillna("—")

# ---------------------------
# Preparar tracks_df para concatenação
# ---------------------------
for col in ['Título', 'Artista/Coleção', 'Categoria', 'Efeito', 'URL', 'Composer', 'Work', 'Key', 'Tonic', 'Planet']:
    if col not in tracks_df.columns:
        tracks_df[col] = ""

classical_df_renamed = classical_df.rename(columns={'URL': 'URL', 'Título': 'Título'})
tracks_df = pd.concat([tracks_df, classical_df_renamed], ignore_index=True, sort=False)

# ---------------------------
# Explicações resumidas por planeta (para UI)
# ---------------------------
PLANET_MUSIC_EXPLANATIONS = {
    'Marte': 'Marte (Dó) — energia de ação e vigor; obras em C tendem a ser diretas e incisivas.',
    'Sol': 'Sol (Ré) — presença e clareza; obras em D costumam transmitir brilho e afirmação.',
    'Mercúrio': 'Mercúrio (Mi) — agilidade mental e comunicação; peças em E favorecem leveza e fluidez.',
    'Saturno': 'Saturno (Fá) — estrutura e profundidade; obras em F trazem sensação de estabilidade.',
    'Júpiter': 'Júpiter (Sol) — expansão e nobreza; obras em G costumam soar amplas e otimistas.',
    'Vênus': 'Vênus (Lá) — harmonia e beleza; peças em A evocam suavidade e afeto.',
    'Lua': 'Lua (Si) — sensibilidade e introspecção; obras em B podem soar etéreas ou contemplativas.'
}

# ---------------------------
# Mapeamentos por signo/planeta (exemplos)
# ---------------------------
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

# ---------------------------
# Interface lateral: filtros
# ---------------------------
st.sidebar.header("Filtros")
mode = st.sidebar.radio(
    "Modo de consulta",
    ["Por signo", "Por planeta", "Por nota", "Por intenção / uso", "Busca livre / tabela"]
)

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_TRACKS.keys()))
    suggested = SIGN_TO_TRACKS.get(sign, [])
elif mode == "Por planeta":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(set(PLANET_TO_TRACKS.keys()))))
    suggested = PLANET_TO_TRACKS.get(planet, [])
elif mode == "Por nota":
    note = st.sidebar.selectbox("Escolha a nota (solfejo)", list(NOTE_TO_PLANET_SHORT.keys()))
    mapped_planet = NOTE_TO_PLANET_SHORT.get(note)
    suggested = PLANET_TO_TRACKS.get(mapped_planet, [])
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", ["Relaxamento","Foco","Sono","Aterramento","Energia"])
else:
    query = st.sidebar.text_input("Busca livre (título, compositor, categoria)")

# Observação: filtros clássicos opcionais (se quiser reativar, descomente e ajuste)
# composer_sel, planet_sel, tonic_sel podem não existir; usaremos guards abaixo.

# ---------------------------
# Painel principal
# ---------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown("**Faixas sugeridas:**")
        for t in suggested:
            st.write(f"- {t}")
    elif mode == "Por planeta":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown("**Faixas associadas:**")
        for t in suggested:
            st.write(f"- {t}")
    elif mode == "Por nota":
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
        st.markdown("**Busca livre / tabela**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Use os filtros laterais para refinar a lista.")

with col2:
    st.subheader("Sons e Músicas")

    # prepara df_display com filtros aplicados
    df_display = tracks_df.copy()
    if mode == "Por signo" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por planeta" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por nota" and suggested:
        df_display = df_display[df_display["Título"].isin(suggested)]
    elif mode == "Por intenção / uso":
        if intent == "Relaxamento":
            df_display = df_display[df_display["Categoria"].str.contains("Relaxamento|Natureza", case=False, na=False)]
        elif intent == "Foco":
            df_display = df_display[df_display["Categoria"].str.contains("Foco|Ambiente", case=False, na=False)]
        elif intent == "Sono":
            df_display = df_display[df_display["Categoria"].str.contains("Sono|Natureza", case=False, na=False)]
    else:
        if mode == "Busca livre / tabela" and query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda r:
                q in str(r.get("Título","")).lower() or
                q in str(r.get("Composer","")).lower() or
                q in str(r.get("Categoria","")).lower(), axis=1)]

    # Se existirem filtros clássicos opcionais, aplique-os com guard
    if 'composer_sel' in locals() and composer_sel != "Todos":
        df_display = df_display[df_display['Composer'] == composer_sel]
    if 'planet_sel' in locals() and planet_sel != "Todos":
        df_display = df_display[df_display['Planet'] == planet_sel]
    if 'tonic_sel' in locals() and tonic_sel != "Todos":
        df_display = df_display[df_display['Tonic'] == tonic_sel]

    # ---------------------------
    # "Sons e Músicas" dentro de expander (oculto por padrão)
    # ---------------------------
    with st.expander("Mostrar Sons e Músicas"):
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

        st.markdown("### Player / Reprodução")
        playable_tracks = df_display["Título"].tolist()
        if playable_tracks:
            play_sel = st.selectbox("Escolha uma faixa para tocar", [""] + playable_tracks, key="player_select")
            if play_sel:
                play_row = df_display[df_display["Título"] == play_sel].iloc[0]
                play_url = play_row.get('URL', '')
                # renderiza player com fallback
                render_video_from_url(play_url)
        else:
            st.info("Nenhuma faixa disponível para reprodução com os filtros atuais.")

    # ---------------------------
    # Detalhes da Nota (visível fora do expander)
    # ---------------------------
    st.markdown("### Detalhes da Nota")
    tracks = df_display["Título"].tolist()
    if tracks:
        sel = st.selectbox("Escolha uma faixa/obra para ver detalhes", [""] + tracks, key="details_select")
        if sel:
            row = df_display[df_display["Título"] == sel].iloc[0]
            title = row.get('Título', '')
            artist = row.get('Artista/Coleção', '') or row.get('Composer', '')
            category = row.get('Categoria', '')
            effect = row.get('Efeito', '')
            tonic = row.get('Tonic', '')
            planet_for_piece = row.get('Planet', '')

            st.markdown(f"**{title}** — *{artist}*")
            if category:
                st.markdown(f"- **Categoria:** {category}")
            if effect:
                st.markdown(f"- **Efeito:** {effect}")
            # OMITIR 'Key' e 'Fonte' conforme solicitado (não exibir Key nem URL aqui)
            if tonic:
                st.markdown(f"- **Tônica (nota):** {tonic}")
            if planet_for_piece and planet_for_piece != "—":
                st.markdown(f"- **Planeta (via tônica):** {planet_for_piece}")
                explanation = PLANET_MUSIC_EXPLANATIONS.get(planet_for_piece)
                if explanation:
                    st.markdown(f"- **Resumo:** {explanation}")
    else:
        st.info("Nenhuma faixa encontrada com os filtros atuais.")

# ---------------------------
# Visualização nota -> planeta (visível fora do expander)
# ---------------------------
st.markdown("---")
st.subheader("Correspondência Nota → Planeta")
note_table = pd.DataFrame([
    {"Nota (solfejo)": f"{k} ({'Dó' if k=='C' else 'Ré' if k=='D' else 'Mi' if k=='E' else 'Fá' if k=='F' else 'Sol' if k=='G' else 'Lá' if k=='A' else 'Si'})", "Planeta": v}
    for k, v in NOTE_TO_PLANET_SHORT.items()
])
st.table(note_table)

# ---------------------------
# Observações finais
# ---------------------------
st.markdown("---")
st.markdown(
    "**Observações:**\n\n"
    "- Para foco: experimente faixas em tonalidades com notas associadas a Mercúrio (Mi) ou Sol (Ré).\n"
    "- Para aterramento: escolha faixas com ênfase em Fá (Saturno) ou Sol (Júpiter).\n"
    "- Para energia: prefira Dó (Marte) e Lá (Vênus) dependendo da intenção."
)