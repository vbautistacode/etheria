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

# --- Interface lateral ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por intenção / uso", "Busca livre"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_PLANET.keys()))
    planet = SIGN_TO_PLANET.get(sign, "—")
    suggested_palette = SIGN_TO_PALETTE.get(sign)
elif mode == "Por planeta regente":
    planet = st.sidebar.selectbox("Selecione o planeta", sorted(list(set(SIGN_TO_PLANET.values()))))
    suggested_palette = PLANET_TO_PALETTE.get(planet)
elif mode == "Por intenção / uso":
    intent = st.sidebar.selectbox("Escolha a intenção", palettes_df["Intenção"].tolist())
else:
    query = st.sidebar.text_input("Busca livre (cor, intenção)")

# --- Painel principal ---
st.header("Paletas e recomendações")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown(f"**Planeta regente:** {planet}")
        st.markdown(f"**Paleta sugerida:** {suggested_palette or '—'}")
    elif mode == "Por planeta regente":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown(f"**Paleta sugerida:** {suggested_palette or '—'}")
    elif mode == "Por intenção / uso":
        st.markdown(f"**Intenção:** {intent}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar paletas.")

    st.markdown("---")
    st.subheader("Como usar")
    st.markdown(
        "- Use a paleta sugerida para exercícios visuais (respiração com foco na cor).\n"
        "- Experimente 3–5 minutos olhando para a cor primária em baixa intensidade.\n"
        "- Combine com respiração lenta para melhores resultados."
    )

with col2:
    st.subheader("Paletas disponíveis")
    df_display = palettes_df.copy()
    if mode == "Por signo" and suggested_palette:
        df_display = df_display[df_display["Intenção"].str.contains(suggested_palette, case=False, na=False) |
                                 (df_display["Intenção"] == suggested_palette)]
    elif mode == "Por planeta regente" and suggested_palette:
        df_display = df_display[df_display["Intenção"].str.contains(suggested_palette, case=False, na=False) |
                                 (df_display["Intenção"] == suggested_palette)]
    elif mode == "Por intenção / uso":
        df_display = df_display[df_display["Intenção"] == intent]
    else:
        if mode == "Busca livre" and query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda r: q in str(r["Intenção"]).lower() or q in str(r["Descrição"]).lower(), axis=1)]

    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    st.markdown("### Detalhes da paleta")
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

st.markdown("---")
st.subheader("Personalize as correspondências")
st.markdown(
    "Se quiser fornecer mapeamentos próprios (signo → paleta ou planeta → paleta), cole aqui no formato JSON "
    "ou descreva as preferências; eu atualizo o código para usar seus dados."
)