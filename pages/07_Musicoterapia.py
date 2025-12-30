# 07_musicoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO
import streamlit.components.v1 as components
from urllib.parse import urlparse, parse_qs

# --- Configuração da página (deve vir antes de qualquer saída) ---
st.set_page_config(page_title="Musicoterapia", layout="wide")
st.title("Musicoterapia 🪉")
st.markdown(
    """
    Musicoterapia: uso terapêutico do som para regular estados emocionais e promover
    relaxamento ou foco. Sugestões de playlists, obras clássicas e sessões guiadas.
    """
)

# ---------------------------
# Helpers e carregamento (com cache)
# ---------------------------
@st.cache_data
def load_tracks_csv():
    # TRACKS_CSV com apenas 4 categorias (elementos): Água, Fogo, Terra, Ar
    TRACKS_CSV = """Título,Artista/Coleção,Categoria,Efeito,URL
Ondas Suaves,Sons da Natureza,Água,"Calmante; texturas aquáticas e camadas suaves que reduzem a tensão e favorecem respiração lenta",https://www.youtube.com/watch?v=VUnN0jILbmQ
Cascata Noturna,Sons da Natureza,Água,"Induz relaxamento profundo; ruído branco filtrado e camadas suaves que facilitam a transição para o sono",https://www.youtube.com/watch?v=V1RPi2MYptM
Batida Alfa,Ambiente,Fogo,"Estimula concentração; batidas regulares e frequências que aumentam energia e foco",https://www.youtube.com/watch?v=p2_zDvtPQ-g
Ritmo Vital,Trilhas Energéticas,Fogo,"Aumenta vigor; ritmos ascendentes e percussão leve para ativar corpo e motivação",https://www.youtube.com/watch?v=Lju6h-C37hE
Tonalidade Terra,Sons Terrosos,Terra,"Aterramento; timbres graves e harmônicos terrosos que promovem sensação de estabilidade",https://www.youtube.com/watch?v=MIo9jbjbO7o
Sons do Solo,Sons Terrosos,Terra,"Apoia aterramento; texturas orgânicas e graves que ajudam a estabilizar o sistema nervoso",https://www.youtube.com/watch?v=NHUJ4upi6Q8
Brisa Leve,Sons Atmosféricos,Ar,"Clareza mental; pads leves e texturas arejadas que facilitam circulação de ideias",https://www.youtube.com/watch?v=--h6buReAvw
Vento Claro,Sons Atmosféricos,Ar,"Estimula criatividade; texturas cintilantes e movimentos rítmicos que clareiam o pensamento",https://www.youtube.com/watch?v=CYpl431hPGk
"""
    return pd.read_csv(StringIO(TRACKS_CSV), quotechar='"', skipinitialspace=True, encoding='utf-8')

@st.cache_data
def load_classical_csv():
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
"Piano Concerto No.23","Mozart","Piano Concerto No.23 in A major","A major","https://www.youtube.com/watch?v=V4S6UYv8-W4"
"Prelude in B","Bach","Prelude in B (ex. WTC / organ)","B minor","https://www.youtube.com/watch?v=ES7fN2lXWHU"
"Violin Concerto No.5","Mozart","Violin Concerto No.5 in A major","A major","https://www.youtube.com/watch?v=iFnfPWLxVLw"
"Cum Sancto Spiritu","Bach","Mass in B minor BWV 232","B minor","https://www.youtube.com/watch?v=4gZe5ZZsE9U"
"Prelude in E minor","Bach","Prelude in E minor (WTC)","E minor","https://www.youtube.com/watch?v=jDjJ8aL6JK0"
"Chaconne (Partita No.2)","Bach","Partita No.2 in D minor (Chaconne transcr. in B)","B minor","https://www.youtube.com/watch?v=example_bach_chaconne"
"""
    return pd.read_csv(StringIO(CLASSICAL_CSV), quotechar='"', skipinitialspace=True, encoding='utf-8')

def tonic_to_note(key: str) -> str:
    if not isinstance(key, str) or key.strip() == "":
        return ""
    base = key.split()[0]
    base = base.replace('♯', '#').replace('♭', 'b')
    return base[0].upper() if base[0].upper() in "CDEFGAB" else ""

def get_youtube_id(u: str) -> str | None:
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
# Carrega dados
# ---------------------------
tracks_df = load_tracks_csv()
classical_df = load_classical_csv()

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

# garante coluna Key e extrai tônica/planeta nas obras clássicas
if 'Key' not in classical_df.columns:
    classical_df['Key'] = ""
classical_df['Tonic'] = classical_df['Key'].apply(tonic_to_note)
classical_df['Planet'] = classical_df['Tonic'].map(NOTE_TO_PLANET_SHORT).fillna("—")

# ---------------------------
# Normalização de colunas e concatenação
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

# concatena mantendo colunas consistentes
common_cols = list(classical_df.columns.intersection(tracks_df.columns))
tracks_df = pd.concat([tracks_df, classical_df[common_cols]], ignore_index=True, sort=False)
tracks_df = tracks_df.fillna("")

# cria rótulo único para selectbox (título — artista/composer) para evitar ambiguidade
def make_label(row):
    artist = row.get('Artista/Coleção') or row.get('Composer') or ""
    return f"{row.get('Título','').strip()} — {artist.strip()}" if artist else row.get('Título','').strip()

tracks_df['_label'] = tracks_df.apply(make_label, axis=1)

# ---------------------------
# Elementos e mapeamentos astrológicos
# ---------------------------
SIGN_TO_ELEMENT = {
    "Áries": "Fogo", "Leão": "Fogo", "Sagitário": "Fogo",
    "Touro": "Terra", "Virgem": "Terra", "Capricórnio": "Terra",
    "Gêmeos": "Ar", "Libra": "Ar", "Aquário": "Ar",
    "Câncer": "Água", "Escorpião": "Água", "Peixes": "Água"
}

ELEMENT_EXPLANATIONS = {
    "Água": "Água — introspecção, sensibilidade e acolhimento; sons fluidos, texturas suaves e ambientes imersivos.",
    "Fogo": "Fogo — ação, vigor e presença; ritmos dinâmicos, percussão e linhas ascendentes que ativam.",
    "Terra": "Terra — estabilidade, enraizamento e segurança; timbres graves, texturas orgânicas e harmônicos terrosos.",
    "Ar": "Ar — clareza mental, comunicação e leveza; pads arejados, texturas cintilantes e movimentos rítmicos leves."
}

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
# Interface lateral: filtros (inclui elemento)
# ---------------------------
st.sidebar.header("Filtros")
mode = st.sidebar.radio(
    "Modo de consulta",
    ["Por signo", "Por elemento", "Por planeta", "Por nota", "Por intenção / uso", "Busca livre / tabela"]
)

# variáveis de controle
sign = planet = element = note = mapped_planet = intent = query = None
suggested = []

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_ELEMENT.keys()))
    element = SIGN_TO_ELEMENT.get(sign)
elif mode == "Por elemento":
    element = st.sidebar.selectbox("Selecione o elemento", ["Água", "Fogo", "Terra", "Ar"])
elif mode == "Por planeta":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(PLANET_MUSIC_EXPLANATIONS.keys())))
elif mode == "Por nota":
    note = st.sidebar.selectbox("Escolha a nota (solfejo)", list(NOTE_TO_PLANET_SHORT.keys()))
    mapped_planet = NOTE_TO_PLANET_SHORT.get(note)
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", ["Relaxamento","Foco","Sono","Aterramento","Energia"])
else:
    query = st.sidebar.text_input("Busca livre (título, compositor, categoria)")

# ---------------------------
# Prepara df_display com filtros aplicados (agora por elemento/signo)
# ---------------------------
df_display = tracks_df.copy()

if mode == "Por signo" and element:
    df_display = df_display[df_display["Categoria"] == element]
elif mode == "Por elemento" and element:
    df_display = df_display[df_display["Categoria"] == element]
elif mode == "Por planeta" and planet:
    # usa PLANET_MUSIC_EXPLANATIONS keys como lista de planetas; tenta mapear títulos por planeta se houver
    # aqui mantemos filtro por títulos associados a planetas (se desejar, pode mapear PLANET_TO_TRACKS)
    df_display = df_display  # sem filtro específico por planeta no catálogo elemental
elif mode == "Por nota" and mapped_planet:
    # tenta usar classical_df mapeado por tônica/planeta (se houver)
    df_display = df_display  # manter catálogo; planetas clássicos aparecem nas obras concatenadas
elif mode == "Por intenção / uso":
    if intent == "Relaxamento":
        df_display = df_display[df_display["Categoria"].str.contains("Água|Relaxamento|Natureza|Sono", case=False, na=False)]
    elif intent == "Foco":
        df_display = df_display[df_display["Categoria"].str.contains("Fogo|Foco|Ambiente|Concentração", case=False, na=False)]
    elif intent == "Sono":
        df_display = df_display[df_display["Categoria"].str.contains("Água|Sono|Relaxamento", case=False, na=False)]
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
        st.markdown(f"**Elemento (quadruplicidade):** {element}")
        st.markdown("**Faixas sugeridas (por elemento):**")
        for t in df_display["Título"].unique().tolist():
            st.write(f"- {t}")
        if element:
            expl = ELEMENT_EXPLANATIONS.get(element)
            if expl:
                st.markdown("---")
                st.markdown(f"**Sobre o elemento {element}:**")
                st.markdown(expl)
    elif mode == "Por elemento":
        st.markdown(f"**Elemento:** {element}")
        st.markdown("**Faixas na categoria:**")
        for t in df_display["Título"].unique().tolist():
            st.write(f"- {t}")
        if element:
            expl = ELEMENT_EXPLANATIONS.get(element)
            if expl:
                st.markdown("---")
                st.markdown(f"**Sobre o elemento {element}:**")
                st.markdown(expl)
    elif mode == "Por planeta":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown("**Observação:** selecione obras na tabela à direita; obras clássicas têm mapeamento tônica→planeta.")
    elif mode == "Por nota":
        st.markdown(f"**Nota selecionada:** {note}")
        st.markdown(f"**Planeta correspondente:** {mapped_planet}")
        st.markdown("**Observação:** obras clássicas concatenadas podem exibir tônica/planeta.")
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
    # Seletor unificado: player + detalhes (usa rótulos unívocos)
    # ---------------------------
    st.markdown("### Player e Detalhes")
    labels = df_display['_label'].tolist()
    if labels:
        sel_label = st.selectbox("Escolha uma faixa/obra", [""] + labels, key="track_select")
        if sel_label:
            row = df_display[df_display['_label'] == sel_label].iloc[0]

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
                cat = (category or "").strip()
                eff = (effect or "").strip()
                if ';' in eff:
                    parts = [p.strip().capitalize() for p in eff.split(';') if p.strip()]
                    eff_text = " ".join(p if p.endswith('.') else p + '.' for p in parts)
                else:
                    eff_text = eff if eff.endswith('.') else (eff + '.') if eff else ""
                if cat:
                    return f"**Categoria (Elemento):** {cat}\n\n**Efeito:** {eff_text}"
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

            # mostra categoria (elemento) e efeito enriquecido como bloco de texto
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
    "- As faixas agora usam apenas as quatro categorias elementares (Água, Fogo, Terra, Ar).\n"
    "- Ao escolher um signo, o app infere o elemento correspondente e filtra as faixas por essa categoria.\n"
    "- Se quiser, posso: (a) mapear obras clássicas automaticamente para elementos; (b) adicionar subcategorias (ex.: 'clássico', 'ambiente') dentro de cada elemento; (c) gerar rótulos unívocos que incluam o elemento no selectbox."
)