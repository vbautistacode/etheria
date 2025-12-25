# 04_cristaloterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Cristaloterapia", layout="wide")
st.title("Cristaloterapia")

st.markdown(
    """
    Introdução à Cristaloterapia: propriedades simbólicas e usos práticos dos cristais
    para apoio emocional, foco e aterramento. Inclui orientações básicas de cuidado
    e sugestões por intenção.
    """
)

# --- Dados CSV (tabela de referência) ---
CSV_DATA = """Pedra,Família de Energia,Essência (Significado),Principais Benefícios,Limpeza,Energização
Turmalina Negra,Proteção,Escudo Energético,Bloqueia inveja e radiação de aparelhos.,Fumo/Terra,Sol/Terra
Obsidiana,Proteção,Espelho da Alma,Revela verdades e corta laços negativos.,Água/Terra,Sol ou Lua
Nuumita,Proteção,Pedra do Xamã,Bloqueia manipulação e protege a alma.,Fumo/Terra,Lua/Terra
Ônix,Proteção,Autocontrole,Dá força estrutural em tempos difíceis.,Água/Sal,Sol ou Lua
Hematita,Proteção,Foco e Lógica,Aterra a mente e evita a dispersão.,Fumo/Terra,Sol
Quartzo Fumê,Proteção,Desintoxicação,Transmuta stress em energia leve.,Água/Fumo,Sol ou Terra
Citrino,Prosperidade,Fluxo de Riqueza,Atrai dinheiro e sucesso nos negócios.,Autolimpante,Sol
Pirita,Prosperidade,Ímã de Ouro,Atrai bens materiais e autoconfiança.,Fumo,Sol
Aventurina,Prosperidade,Sorte e Oportunidade,Atrai sorte rápida e novas chances.,Água,Sol
Olho de Tigre,Prosperidade,Estrategista,Protege contra inveja e dá foco em metas.,Água/Sal,Sol
Topázio,Prosperidade,Manifestação,Atrai abundância e clareia intenções.,Fumo/Água,Sol ou Lua
Ametista,Espiritualidade,Transmutação,Transmuta dor em paz e ajuda no sono.,Água/Fumo,Lua
Selenita,Espiritualidade,Purificador Mestre,Limpa ambientes e outros cristais.,Fumo apenas,Lua
Celestina,Espiritualidade,Paz Angélica,Serenidade extrema e conexão com guias.,Fumo apenas,Lua
Quartzo Anjo,Espiritualidade,Paz Profunda,Alivia ansiedade e facilita a meditação.,Fumo,Lua
Quartzo Branco,Espiritualidade,Amplificador,Potencializa desejos e limpa a aura.,Todos,Sol ou Lua
Sodalita,Espiritualidade,Clareza Verbal,Une intuição à lógica na comunicação.,Fumo,Lua
Ágata Azul,Espiritualidade,Paz Interior,Acalma os nervos e suaviza as palavras.,Água/Sal,Lua
Cornalina,Vitalidade,Fogo e Ação,Vence a preguiça e dá coragem física.,Água/Sal,Sol
Granada,Vitalidade,Regeneração,Revitaliza o corpo e desperta a paixão.,Água (rápida),Sol
Quartzo Vermelho,Vitalidade,Força de Vontade,Tira as ideias do papel e dá foco.,Fumo/Água,Sol
Jaspe,Vitalidade,Nutridor Supremo,Sustenta e estabiliza em longas jornadas.,Água/Sal,Terra ou Sol
Esmeralda,Coração,Amor Sábio,Fortalece a lealdade e o amor maduro.,Fumo/Água,Lua
Turquesa Verde,Coração,Sabedoria Ancestral,Proteção em viagens e autoexpressão.,Fumo apenas,Lua ou Terra
"""

df = pd.read_csv(StringIO(CSV_DATA))

# --- Mapeamentos básicos (exemplos) ---
# Mapas simples de signo -> planeta regente e pedras sugeridas (personalizáveis)
SIGN_TO_PLANET = {
    "Áries": "Marte",
    "Touro": "Vênus",
    "Gêmeos": "Mercúrio",
    "Câncer": "Lua",
    "Leão": "Sol",
    "Virgem": "Mercúrio",
    "Libra": "Vênus",
    "Escorpião": "Plutão/Marte",
    "Sagitário": "Júpiter",
    "Capricórnio": "Saturno",
    "Aquário": "Urano/Saturno",
    "Peixes": "Netuno/Júpiter",
}

# Sugestões de pedras por signo (lista curta, baseada na tabela)
SIGN_TO_STONES = {
    "Áries": ["Granada", "Quartzo Vermelho"],
    "Touro": ["Citrino", "Esmeralda"],
    "Gêmeos": ["Aventurina", "Sodalita"],
    "Câncer": ["Turquesa Verde", "Quartzo Anjo"],
    "Leão": ["Topázio", "Citrino"],
    "Virgem": ["Quartzo Branco", "Hematita"],
    "Libra": ["Olho de Tigre", "Ágata Azul"],
    "Escorpião": ["Obsidiana", "Turmalina Negra"],
    "Sagitário": ["Ametista", "Turquesa Verde"],
    "Capricórnio": ["Jaspe", "Hematita"],
    "Aquário": ["Ametista", "Sodalita"],
    "Peixes": ["Ametista", "Celestina"],
}

# Sugestões por planeta regente (exemplo)
PLANET_TO_STONES = {
    "Sol": ["Citrino", "Topázio"],
    "Lua": ["Ametista", "Selenita", "Quartzo Anjo"],
    "Marte": ["Granada", "Quartzo Vermelho"],
    "Vênus": ["Esmeralda", "Aventurina"],
    "Mercúrio": ["Sodalita", "Quartzo Branco"],
    "Júpiter": ["Citrino", "Ametista"],
    "Saturno": ["Jaspe", "Hematita"],
    "Urano": ["Turquesa Verde"],
    "Netuno": ["Celestina"],
    "Plutão": ["Obsidiana", "Turmalina Negra"],
}

# --- Layout: filtros e busca ---
st.sidebar.header("Filtros e buscas")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por objetivo / uso", "Busca livre / tabela"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"])
    planet = SIGN_TO_PLANET.get(sign, "—")
    st.sidebar.markdown(f"**Planeta regente:** {planet}")
    suggested = SIGN_TO_STONES.get(sign, [])
    st.sidebar.markdown("**Pedras sugeridas:** " + (", ".join(suggested) if suggested else "Nenhuma sugerida"))

elif mode == "Por planeta regente":
    planet_choice = st.sidebar.selectbox("Selecione o planeta", sorted(list({v for v in SIGN_TO_PLANET.values()})))
    suggested = PLANET_TO_STONES.get(planet_choice, [])
    st.sidebar.markdown("**Pedras associadas:** " + (", ".join(suggested) if suggested else "Nenhuma sugerida"))

elif mode == "Por objetivo / uso":
    objectives = sorted(df["Família de Energia"].unique().tolist())
    obj = st.sidebar.selectbox("Escolha o objetivo", ["Proteção","Prosperidade","Espiritualidade","Vitalidade","Coração"] + objectives)
    # normalize selection to match table values
    # we'll filter by substring match
    st.sidebar.markdown("Resultados mostrados na tabela principal abaixo.")

else:
    # Busca livre / tabela
    query = st.sidebar.text_input("Busca livre (nome, essência, benefício)")

# --- Painel principal ---
st.header("Consulta rápida")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown(f"**Planeta regente:** {planet}")
        st.markdown("**Pedras sugeridas:**")
        for p in suggested:
            st.write(f"- {p}")
    elif mode == "Por planeta regente":
        st.markdown(f"**Planeta:** {planet_choice}")
        st.markdown("**Pedras associadas:**")
        for p in suggested:
            st.write(f"- {p}")
    elif mode == "Por objetivo / uso":
        st.markdown(f"**Objetivo selecionado:** {obj}")
        st.write("A tabela à direita mostra as pedras relacionadas.")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar a tabela.")

    st.markdown("---")
    st.subheader("Como usar")
    st.markdown(
        "- Selecione um modo de consulta na barra lateral.\n"
        "- Clique em uma linha da tabela para ver detalhes da pedra.\n"
        "- Use a busca livre para localizar por nome, essência ou benefício."
    )

with col2:
    st.subheader("Tabela de referência")
    # aplica filtros
    df_display = df.copy()
    if mode == "Por signo":
        if suggested:
            df_display = df_display[df_display["Pedra"].isin(suggested)]
    elif mode == "Por planeta regente":
        if suggested:
            df_display = df_display[df_display["Pedra"].isin(suggested)]
    elif mode == "Por objetivo / uso":
        if obj:
            # filtra por família de energia ou por substring
            df_display = df_display[df_display["Família de Energia"].str.contains(obj, case=False, na=False) |
                                     df_display["Principais Benefícios"].str.contains(obj, case=False, na=False)]
    else:
        if query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda row:
                q in str(row["Pedra"]).lower() or
                q in str(row["Essência (Significado)"]).lower() or
                q in str(row["Principais Benefícios"]).lower(), axis=1)]
    # exibe tabela interativa
    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    # seleção de pedra para detalhes
    st.markdown("### Detalhes da pedra")
    stone_names = df_display["Pedra"].tolist()
    if stone_names:
        selected = st.selectbox("Escolha uma pedra para ver detalhes", [""] + stone_names)
        if selected:
            row = df[df["Pedra"] == selected].iloc[0]
            st.markdown(f"**{row['Pedra']}** — *{row['Família de Energia']}*")
            st.markdown(f"**Essência:** {row['Essência (Significado)']}")
            st.markdown(f"**Principais benefícios:** {row['Principais Benefícios']}")
            st.markdown(f"**Limpeza recomendada:** {row['Limpeza']}")
            st.markdown(f"**Energização recomendada:** {row['Energização']}")
    else:
        st.info("Nenhuma pedra encontrada com os filtros atuais.")

# --- Extras: exportar visualização (cópia para área de transferência) ---
st.markdown("---")
st.subheader("Exportar / copiar")
st.markdown("Você pode copiar a tabela filtrada e colar em uma planilha. Use o botão abaixo para gerar CSV na tela.")
csv = df_display.to_csv(index=False)
st.download_button("Baixar CSV (tabela filtrada)", csv, file_name="cristaloterapia_tabela.csv", mime="text/csv")

# --- Observações e cuidados ---
st.markdown("---")
st.markdown(
    "**Observações:**\n\n"
    "- As sugestões são simbólicas e informativas; não substituem orientação profissional.\n"
    "- Ao limpar ou energizar cristais, siga práticas seguras (evite água em pedras solúveis, cuidado com luz solar prolongada, etc.).\n"
    "- Personalize os mapeamentos `SIGN_TO_STONES` e `PLANET_TO_STONES` conforme sua tradição ou fonte."
)