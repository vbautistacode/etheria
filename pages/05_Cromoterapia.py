# 05_cromoterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.title("Cromoterapia 🌈")
st.markdown(
    """
    Cromoterapia: exploração das cores e suas frequências para modular humor e energia.
    Ferramentas simples para exercícios visuais, paletas por intenção e recomendações
    rápidas para o dia a dia.
    """
)
st.caption("Utilize o menu lateral para selecionar o modo de consulta.")

# --- Mapeamentos padrão (substitua conforme sua referência) ---
SIGN_TO_PLANET = {
    "Áries": "Marte", "Touro": "Vênus", "Gêmeos": "Mercúrio", "Câncer": "Lua",
    "Leão": "Sol", "Virgem": "Mercúrio", "Libra": "Vênus", "Escorpião": "Plutão/Marte",
    "Sagitário": "Júpiter", "Capricórnio": "Saturno", "Aquário": "Urano/Saturno", "Peixes": "Netuno/Júpiter"
}

# Paletas por intenção e sugestões por signo/planeta (exemplos)
PALETTES_CSV = """Intenção,Cor Primária,Cor Secundária,Tom de Apoio,Descrição
Calma,Azul Claro,Verde Água,Lavanda,Reduz ansiedade e acalma o sistema nervoso
Foco,Amarelo Mostarda,Azul Profundo,Cinza,Estimula atenção e clareza mental
Energia,Vermelho,Âmbar,Dourado,Aumenta vigor e motivação
Equilíbrio,Verde Folha,Creme,Marrom Suave,Promove aterramento e estabilidade
Sono,Azul Noturno,Índigo,Prata,Prepara para relaxamento profundo
Criatividade,Roxo Magenta,Rosa Quente,Laranja Suave,Abre canais de imaginação
"""

palettes_df = pd.read_csv(StringIO(PALETTES_CSV))

# Sugestões por signo/planeta (exemplos)
SIGN_TO_PALETTE = {
    "Áries": "Energia", "Touro": "Equilíbrio", "Gêmeos": "Foco", "Câncer": "Calma",
    "Leão": "Energia", "Virgem": "Foco", "Libra": "Equilíbrio", "Escorpião": "Sono",
    "Sagitário": "Criatividade", "Capricórnio": "Equilíbrio", "Aquário": "Criatividade", "Peixes": "Calma"
}
PLANET_TO_PALETTE = {
    "Sol": "Energia", "Lua": "Calma", "Marte": "Energia", "Vênus": "Equilíbrio",
    "Mercúrio": "Foco", "Júpiter": "Criatividade", "Saturno": "Equilíbrio", "Urano": "Criatividade",
    "Netuno": "Calma", "Plutão": "Sono"
}

# --- Correspondência Planeta -> Cor (solicitada) ---
# Lua: Violeta; Marte: Vermelho; Mercurio: Amarelo; Jupiter: Azul (Púrpura);
# Venus: Índigo; Saturno: Verde; Sol: Laranja
PLANET_TO_COLOR = {
    "Lua": "Violeta",
    "Marte": "Vermelho",
    "Mercúrio": "Amarelo",
    "Júpiter": "Azul (Púrpura)",
    "Vênus": "Índigo",
    "Saturno": "Verde",
    "Sol": "Laranja",
    # entradas adicionais para completude
    "Urano": "Ciano",
    "Netuno": "Azul Profundo",
    "Plutão": "Bordô"
}

# --- Explicação resumida da energia da cor por planeta ---
PLANET_COLOR_ENERGY = {
    "Lua": "Violeta — energia introspectiva e sutil; favorece intuição, calma emocional e conexão com o inconsciente.",
    "Marte": "Vermelho — energia ativa e estimulante; aumenta vigor, coragem e impulso para ação.",
    "Mercúrio": "Amarelo — energia mental e comunicativa; estimula clareza, raciocínio e expressão.",
    "Júpiter": "Azul (Púrpura) — energia expansiva e inspiradora; amplia visão, otimismo e crescimento interior.",
    "Vênus": "Índigo — energia de harmonia e relação; favorece beleza, afeto e equilíbrio nos vínculos.",
    "Saturno": "Verde — energia estabilizadora e enraizada; promove disciplina, estrutura e aterramento.",
    "Sol": "Laranja — energia vital e calorosa; estimula criatividade, autoestima e presença.",
    "Urano": "Ciano — energia inovadora e libertadora; favorece originalidade e mudança.",
    "Netuno": "Azul Profundo — energia contemplativa e sensível; facilita imaginação e estados meditativos.",
    "Plutão": "Bordô — energia transformadora e profunda; auxilia processos de renascimento e liberação."
}

# --- Interface lateral ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por intenção / uso", "Busca livre"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_PLANET.keys()))
    planet = SIGN_TO_PLANET.get(sign, "—")
    suggested_palette = SIGN_TO_PALETTE.get(sign)
    suggested_color = PLANET_TO_COLOR.get(planet, "—")
    suggested_color_energy = PLANET_COLOR_ENERGY.get(planet, None)
elif mode == "Por planeta regente":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(set(SIGN_TO_PLANET.values()))))
    suggested_palette = PLANET_TO_PALETTE.get(planet)
    suggested_color = PLANET_TO_COLOR.get(planet, "—")
    suggested_color_energy = PLANET_COLOR_ENERGY.get(planet, None)
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", palettes_df["Intenção"].tolist())
    suggested_color = None
    suggested_color_energy = None
else:
    query = st.sidebar.text_input("Busca livre (cor, intenção)")
    suggested_color = None
    suggested_color_energy = None

# --- Painel principal ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown(f"**Planeta regente:** {planet}")
        st.markdown(f"**Paleta sugerida:** {suggested_palette or '—'}")
        st.markdown(f"**Cor associada ao planeta:** {suggested_color or '—'}")
        if suggested_color_energy:
            st.markdown(f"**Energia da cor:** {suggested_color_energy}")
    elif mode == "Por planeta regente":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown(f"**Paleta sugerida:** {suggested_palette or '—'}")
        st.markdown(f"**Cor associada:** {suggested_color or '—'}")
        if suggested_color_energy:
            st.markdown(f"**Energia da cor:** {suggested_color_energy}")
    elif mode == "Por intenção / uso":
        st.markdown(f"**Intenção:** {intent}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar paletas.")

with col2:
    st.subheader("Paletas")
    df_display = palettes_df.copy()
    if mode == "Por signo" and suggested_palette:
        df_display = df_display[df_display["Intenção"].str.contains(suggested_palette, case=False, na=False) | (df_display["Intenção"] == suggested_palette)]
    elif mode == "Por planeta regente" and suggested_palette:
        df_display = df_display[df_display["Intenção"].str.contains(suggested_palette, case=False, na=False) | (df_display["Intenção"] == suggested_palette)]
    elif mode == "Por intenção / uso":
        df_display = df_display[df_display["Intenção"] == intent]
    else:
        if mode == "Busca livre" and query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda r: q in str(r["Intenção"]).lower() or q in str(r["Descrição"]).lower(), axis=1)]

    # exibe apenas a tabela dentro do expander (oculta por padrão)
    with st.expander("Mostrar paletas disponíveis"):
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    # Detalhes da paleta ficam visíveis fora do expander
    st.markdown("### Detalhes")
    palettes = df_display["Intenção"].tolist()
    if palettes:
        sel = st.selectbox("Escolha uma paleta", [""] + palettes)
        if sel:
            row = df_display[df_display["Intenção"] == sel].iloc[0]
            st.markdown(f"**{row['Intenção']}**")
            st.markdown(f"- **Cor primária:** {row['Cor Primária']}")
            st.markdown(f"- **Cor secundária:** {row['Cor Secundária']}")
            st.markdown(f"- **Tom de apoio:** {row['Tom de Apoio']}")
            st.markdown(f"- **Descrição:** {row['Descrição']}")
    else:
        st.info("Nenhuma paleta encontrada com os filtros atuais.")

st.markdown("---")

# Correspondência Planeta → Cor dentro de expander
with st.expander("Correspondência Planeta → Cor"):
    st.subheader("Correspondência Planeta → Cor")
    st.markdown(
        "Referência rápida das cores associadas aos planetas (útil para exercícios tonais e visuais)."
    )
    planet_color_table = pd.DataFrame([
        {"Planeta": p, "Cor associada": c, "Energia resumida": PLANET_COLOR_ENERGY.get(p, "")}
        for p, c in sorted(PLANET_TO_COLOR.items())
    ])
    st.table(planet_color_table)

# --- Observações e cuidados ---
st.markdown("---")
st.markdown(
    "**Observações:**\n\n"
    "- Use a paleta sugerida para exercícios visuais (respiração com foco na cor).\n"
    "- Experimente 3–5 minutos olhando para a cor primária em baixa intensidade.\n"
    "- Combine com respiração lenta para melhores resultados."
)