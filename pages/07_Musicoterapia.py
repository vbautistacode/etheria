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
# Dados iniciais de faixas (textos de efeito enriquecidos)
# ---------------------------
TRACKS_CSV = """Título,Artista/Coleção,Categoria,Efeito,URL
Ondas Suaves,Sons da Natureza,Relaxamento,"Calmante; ondas contínuas e texturas suaves que reduzem a tensão e favorecem respiração lenta",https://www.youtube.com/watch?v=VUnN0jILbmQ
Batida Alfa,Ambiente,Foco,"Estimula concentração; batidas regulares e frequências alfa que ajudam a sincronizar atenção e reduzir distrações",https://www.youtube.com/watch?v=p2_zDvtPQ-g
Tonalidade Terra,Sons Amadeirados,Aterramento,"Estabiliza; timbres graves, harmônicos terrosos e texturas orgânicas que promovem sensação de enraizamento",https://www.youtube.com/watch?v=MIo9jbjbO7o
Cascata Noturna,Sons da Natureza,Sono,"Induz relaxamento profundo; camadas sonoras suaves e ruído branco filtrado que facilitam a transição para o sono",https://www.youtube.com/watch?v=V1RPi2MYptM
Ritmo Vital,Trilhas Energéticas,Energia,"Aumenta vigor; ritmos ascendentes, percussão leve e linhas melódicas que ativam corpo e motivação",https://www.youtube.com/watch?v=Lju6h-C37hE
"""
tracks_df = pd.read_csv(StringIO(TRACKS_CSV), quotechar='"', skipinitialspace=True, encoding='utf-8')

# ---------------------------
# Obras clássicas: metadados (CSV bem formado)
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
    """Extrai a letra base da tônica (C D E F G A B) a partir de uma string Key."""
    if not isinstance(key, str) or key.strip() == "":
        return ""
    base = key.split()[0]
    base = base.replace('♯', '#').replace('♭', 'b')
    return base[0].upper() if base[0].upper() in "CDEFGAB" else ""

def get_youtube_id(u: str) -> str | None:
    """Extrai o ID do YouTube de uma URL (youtube.com/watch?v=, youtu.be/, embed)."""
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
        st.info("Nenhuma fonte de reprodução disponível para esta faixa.")
        return

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

# aplica transformação e mapeamento nas obras clássicas (garante coluna Key)
if 'Key' not in classical_df.columns:
    classical_df['Key'] = ""
classical_df['Tonic'] = classical_df['Key'].apply(tonic_to_note)
classical_df['Planet'] = classical_df['Tonic'].map(NOTE_TO_PLANET_SHORT).fillna("—")

# ---------------------------
# Preparar tracks_df para concatenação
# ---------------------------
required_cols = ['Título', 'Artista/Coleção', 'Categoria', 'Efeito', 'URL', 'Composer', 'Work', 'Key', 'Tonic', 'Planet']
for col in required_cols:
    if col not in tracks_df.columns:
        tracks_df[col] = ""
    tracks_df[col] = tracks_df[col].fillna("")

for col in required_cols:
    if col not in classical_df.columns:
        classical_df[col] = ""
    classical_df[col] = classical_df[col].fillna("")

# concatena obras clássicas ao catálogo de faixas (mantendo colunas consistentes)
tracks_df = pd.concat([tracks_df, classical_df[list(classical_df.columns.intersection(tracks_df.columns))]], ignore_index=True, sort=False)
tracks_df = tracks_df.fillna("")

# ---------------------------
# Explicações resumidas por planeta (para UI)
# ---------------------------
PLANET_MUSIC_EXPLANATIONS = {
    'Marte': 'Marte (Dó) — energia de ação e vigor; obras em Dó tendem a ser diretas e incisivas.',
    'Sol': 'Sol (Ré) — presença e clareza; obras em Ré costumam transmitir brilho e afirmação.',
    'Mercúrio': 'Mercúrio (Mi) — agilidade mental e comunicação; peças em Mi favorecem leveza e fluidez.',
    'Saturno': 'Saturno (Fá) — estrutura e profundidade; obras em Fá trazem sensação de estabilidade.',
    'Júpiter': 'Júpiter (Sol) — expansão e nobreza; obras em Sol costumam soar amplas e otimistas.',
    'Vênus': 'Vênus (Lá) — harmonia e beleza; peças em Lá evocam suavidade e afeto.',
    'Lua': 'Lua (Si) — sensibilidade e introspecção; obras em Si podem soar etéreas ou contemplativas.'
}

# ---------------------------
# Mapeamentos por signo/planeta (conteúdo melhorado)
# ---------------------------
SIGN_TO_TRACKS = {
    "Áries": ["Ritmo Vital"],            # ação, coragem, impulso
    "Touro": ["Tonalidade Terra"],   # estabilidade, conforto, beleza sensorial
    "Gêmeos": ["Batida Alfa"],  # agilidade mental, leveza e movimento
    "Câncer": ["Cascata Noturna"],          # acolhimento, segurança emocional
    "Leão": ["Ritmo Vital"],               # presença, brilho, expressão
    "Virgem": ["Batida Alfa"],              # foco prático, ordem e clareza
    "Libra": ["Tonalidade Terra"],  # harmonia, equilíbrio estético
    "Escorpião": ["Symphony No.5"], # profundidade, intensidade transformadora
    "Sagitário": ["Ritmo Vital"], # expansão, aventura e otimismo
    "Capricórnio": ["Tonalidade Terra"], # disciplina, estrutura
    "Aquário": ["Batida Alfa"],    # inovação, surpresa e movimento coletivo
    "Peixes": ["Ondas Suaves"]        # sensibilidade, imaginação e sonho
}

# Planet_To_Tracks agora reflete categorias/regentes de cada signo
PLANET_TO_TRACKS = {
    # Sol (regente de Leão) -> energia, presença, obras brilhantes
    "Sol": ["Ritmo Vital", "Symphony No.9", "Piano Concerto No.23"],
    # Lua (regente de Câncer) -> introspecção, sono, acolhimento
    "Lua": ["Cascata Noturna", "Ondas Suaves", "Prelude in E minor"],
    # Marte (regente de Áries) -> ação, intensidade
    "Marte": ["Ritmo Vital", "Toccata and Fugue", "Symphony No.5"],
    # Vênus (regente de Touro/Libra) -> harmonia, beleza, peças líricas
    "Vênus": ["Tonalidade Terra", "Violin Concerto No.5", "Piano Concerto No.23"],
    # Mercúrio (regente de Gêmeos/Virgem) -> agilidade mental, foco
    "Mercúrio": ["Batida Alfa", "Brandenburg Concerto No.3", "Symphony No.3 (Eroica)"],
    # Júpiter (regente de Sagitário/Peixes) -> expansão, nobreza
    "Júpiter": ["Symphony No.41 (Jupiter)", "Ondas Suaves", "Symphony No.6 (Pastoral)"],
    # Saturno (regente de Capricórnio/Aquário) -> estrutura, profundidade
    "Saturno": ["Brandenburg Concerto No.3", "Tonalidade Terra", "Chaconne (Partita No.2)"],
    # Netuno (regente moderno de Peixes) -> sonho, atmosfera
    "Netuno": ["Ondas Suaves", "Chaconne (Partita No.2)"],
    # Urano (regente moderno de Aquário) -> inovação, surpresa
    "Urano": ["Ride of the Valkyries", "Batida Alfa"],
    # Plutão (regente moderno de Escorpião) -> transformação, intensidade
    "Plutão": ["Symphony No.5", "Chaconne (Partita No.2)"]
}

# ---------------------------
# Interface lateral: filtros
# ---------------------------
st.sidebar.header("Filtros")
mode = st.sidebar.radio(
    "Modo de consulta",
    ["Por signo", "Por planeta", "Por nota", "Por intenção / uso", "Busca livre / tabela"]
)

# variáveis de controle
sign = planet = note = mapped_planet = intent = query = None
suggested = []

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

# ---------------------------
# Prepara df_display com filtros aplicados
# ---------------------------
df_display = tracks_df.copy()

if mode == "Por signo" and suggested:
    df_display = df_display[df_display["Título"].isin(suggested)]
elif mode == "Por planeta" and suggested:
    df_display = df_display[df_display["Título"].isin(suggested)]
elif mode == "Por nota" and suggested:
    df_display = df_display[df_display["Título"].isin(suggested)]
elif mode == "Por intenção / uso":
    if intent == "Relaxamento":
        df_display = df_display[df_display["Categoria"].str.contains("Relaxamento|Natureza|Sono", case=False, na=False)]
    elif intent == "Foco":
        df_display = df_display[df_display["Categoria"].str.contains("Foco|Ambiente|Concentração", case=False, na=False)]
    elif intent == "Sono":
        df_display = df_display[df_display["Categoria"].str.contains("Sono|Relaxamento", case=False, na=False)]
else:
    if mode == "Busca livre / tabela" and query:
        q = query.strip().lower()
        df_display = df_display[df_display.apply(lambda r:
            q in str(r.get("Título","")).lower() or
            q in str(r.get("Composer","")).lower() or
            q in str(r.get("Categoria","")).lower(), axis=1)]

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

    # exibe tabela dentro de expander (oculta por padrão)
    with st.expander("Mostrar Sons e Músicas"):
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    # ---------------------------
    # Seletor unificado: player + detalhes
    # ---------------------------
    st.markdown("### Player e Detalhes")
    tracks = df_display["Título"].tolist()
    if tracks:
        sel = st.selectbox("Escolha uma faixa/obra", [""] + tracks, key="track_select")
        if sel:
            row = df_display[df_display["Título"] == sel].iloc[0]

            # Player (renderiza se houver URL)
            play_url = row.get('URL', '')
            if play_url and pd.notna(play_url) and str(play_url).strip() != "":
                st.markdown("**Reprodução**")
                render_video_from_url(play_url)
            else:
                st.info("Nenhuma fonte de reprodução disponível para esta faixa.")

            # ---------------------------
            # Detalhes (omitindo 'Key' e 'Fonte') com fallbacks para Categoria/Efeito
            # ---------------------------
            def format_effect_text(category: str, effect: str) -> str:
                """
                Retorna um texto enriquecido combinando categoria e efeito.
                - category: rótulo curto (ex.: 'Energia', 'Relaxamento')
                - effect: descrição mais longa (pode conter ponto-e-vírgula para separar frases)
                """
                cat = (category or "").strip()
                eff = (effect or "").strip()
                if ';' in eff:
                    parts = [p.strip().capitalize() for p in eff.split(';') if p.strip()]
                    eff_text = " ".join(p if p.endswith('.') else p + '.' for p in parts)
                else:
                    eff_text = eff if eff.endswith('.') else (eff + '.') if eff else ""
                if cat:
                    return f"**Categoria:** {cat}\n\n**Efeito:** {eff_text}"
                else:
                    return f"**Efeito:** {eff_text}" if eff_text else ""

            st.markdown("**Detalhes da faixa**")
            title = (row.get('Título') or "").strip()
            artist = (row.get('Artista/Coleção') or row.get('Composer') or "").strip()
            category = (row.get('Categoria') or "").strip()
            effect = (row.get('Efeito') or "").strip()
            tonic = (row.get('Tonic') or "").strip()
            planet_for_piece = (row.get('Planet') or "").strip()

            st.markdown(f"**{title}** — *{artist}*")

            # mostra categoria e efeito enriquecido como bloco de texto
            effect_block = format_effect_text(category, effect)
            if effect_block:
                st.markdown(effect_block)

            def show_if(value):
                return value is not None and str(value).strip() != "" and str(value).strip().lower() != "nan"

            if show_if(tonic):
                st.markdown(f"- **Tônica (nota):** {tonic}")
            if show_if(planet_for_piece) and planet_for_piece != "—":
                st.markdown(f"- **Planeta (via tônica):** {planet_for_piece}")
                explanation = PLANET_MUSIC_EXPLANATIONS.get(planet_for_piece)
                if explanation:
                    st.markdown(f"- **Resumo:** {explanation}")
    else:
        st.info("Nenhuma faixa encontrada com os filtros atuais.")

# ---------------------------
# Visualização nota -> planeta (dentro de expander)
# ---------------------------
with st.expander("Correspondência Nota → Planeta"):
    st.markdown("---")
    st.subheader("Correspondência Nota → Planeta")
    note_table = pd.DataFrame([
        {
            "Nota (solfejo)": f"{k} ({'Dó' if k=='C' else 'Ré' if k=='D' else 'Mi' if k=='E' else 'Fá' if k=='F' else 'Sol' if k=='G' else 'Lá' if k=='A' else 'Si'})",
            "Planeta": v
        }
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