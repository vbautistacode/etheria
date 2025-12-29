# 04_cristaloterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.title("Cristaloterapia 💎")

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
Turmalina Negra (var.) ,Proteção,Escudo Energético,Bloqueia energias negativas e radiação.,Fumo/Terra,Sol/Terra
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
Quartzo Cristal,Amplificador,Purificação e amplificação,Amplifica intenções e outros cristais.,Água/Sal,Sol ou Lua
Quartzo Rosa,Coração,Amor e Cura Emocional,Promove amor próprio e cura de feridas emocionais.,Água/Sal,Lua
Pedra da Lua (Moonstone),Intuição,Renovação Emocional,Estimula intuição e ciclos femininos.,Água/Lua,Lua
Lápis-Lazúli,Espiritualidade,Visão Interior,Clareia a mente e favorece comunicação espiritual.,Fumo,Lua
Malachita,Transformação,Proteção e Cura,Transmuta padrões e protege em viagens, cuidado com água.,Fumo/Terra,Sol
Fluorita,Clareza,Organização Mental,Ajuda concentração e ordena pensamentos dispersos.,Água/Sal,Sol ou Lua
Labradorita,Proteção Intuitiva,Escudo Mágico,Protege a aura e intensifica intuição.,Fumo/Terra,Lua
Cianita (Kyanite),Alinhamento,Comunicação e Alinhamento,Alinha chakras sem necessidade de limpeza,Água,Lua
Rhodonita,Coração,Reconciliação,Ajuda cura emocional e relações,Água/Sal,Sol ou Lua
Amazonita,Comunicação,Equilíbrio Emocional,Suaviza emoções e facilita expressão,Água/Sal,Lua
Peridoto,Renovação,Liberação de Padrões,Apoia renovação e prosperidade,Água/Sal,Sol
Morganita,Coração,Amor Divino,Abre o coração para compaixão e cura,Água/Sal,Lua
Kunzita,Emoção,Amor e Cura Emocional,Suporta liberação de traumas emocionais,Água/Sal,Lua
Sapphire (Safira),Proteção Espiritual,Clareza e Sabedoria,Favorece discernimento e proteção,Água/Sal,Sol ou Lua
Rubi (Rubi),Vitalidade,Paixão e Coragem,Aumenta energia vital e coragem,Água/Sal,Sol
Safira Azul,Espiritualidade,Clareza Mental,Auxilia concentração e intuição,Água/Sal,Lua
Rubiina (variante de Granada),Prosperidade,Paixão e Manifestação,Estimula ação e prosperidade,Água/Sal,Sol
Bloodstone (Heliotrópio),Proteção,Vitalidade e Coragem,Fortalece resistência e coragem,Água/Sal,Sol
Chrysocolla,Comunicação,Calma e Expressão,Suaviza emoções e melhora expressão,Água/Sal,Lua
Chrysoprase,Prosperidade,Renovação do Coração,Abre o coração para novas oportunidades,Água/Sal,Sol
Howlita,Calma,Redução de Ansiedade,Ajuda sono e pacificação mental,Água/Sal,Lua
Turquesa,Proteção e Comunicação,Viagem e Cura,Protege em viagens e favorece expressão,Água/Sal,Lua ou Terra
Sodalita (var.),Comunicação,Clareza e Verdade,Melhora expressão e lógica,Água/Sal,Lua
Fluorita Arco-Íris,Equilíbrio,Integração,Equilibra emoções e mente,Água/Sal,Sol ou Lua
Lepidolita,Calmante,Alívio de Ansiedade,Contém lítio natural; acalma e estabiliza,Água/Sal,Lua
Obsidiana Negra,Proteção,Limpeza Profunda,Libera padrões e protege,Água/Terra,Sol ou Lua
Turmalina Rosa,Amor,Autoaceitação,Suporta cura emocional,Água/Sal,Lua
Sodalita Azul,Comunicação,Clareza Verbal,Auxilia expressão autêntica,Água/Sal,Lua
Ametista Chevron,Espiritualidade,Proteção e Intuição,Combina propriedades de ametista e quartzo,Água/Fumo,Lua
Angel Quartz (Quartzo Anjo),Espiritualidade,Conexão e Cura,Facilita estados meditativos,Água/Fumo,Lua
Celestita (var.),Espiritualidade,Paz e Conexão,Promove calma e conexão com guias,Água/Fumo,Lua
Black Onyx (Ônix Negro),Proteção,Força e Estabilidade,Oferece suporte em tempos difíceis,Água/Sal,Sol
Pyrite (Pirita),Prosperidade,Confiança e Ação,Aumenta iniciativa e proteção,Água/Sal,Sol
Garnet (Granada),Vitalidade,Paixão e Proteção,Revitaliza energia e coragem,Água/Sal,Sol
Peridot (var.),Prosperidade,Renovação e Cura,Ajuda liberação de padrões antigos,Água/Sal,Sol
Moonstone Rainbow,Intuição,Ciclos e Renovação,Suporta equilíbrio emocional,Água/Lua,Lua
Lapis Lazuli,Visão Interior,Clareza Espiritual,Ajuda expressão e intuição,Água/Sal,Lua
Malachite (var.),Transformação,Proteção e Cura,Transmuta energias densas,Água/Terra,Sol
Fluorite Verde,Clareza,Equilíbrio Emocional,Auxilia foco e limpeza mental,Água/Sal,Sol
Labradorita (var.),Proteção,Intuição e Magia,Amplifica intuição e protege aura,Água/Terra,Lua
Kyanite Azul,Alinhamento,Comunicação Clara,Alinha chakras sem limpeza,Água,Lua
Rhodonite (var.),Coração,Reconciliação e Cura,Suporta relações e perdão,Água/Sal,Sol ou Lua
Amazonita (var.),Comunicação,Equilíbrio e Coragem,Suaviza emoções e facilita expressão,Água/Sal,Lua
Bloodstone (var.),Proteção,Vitalidade e Coragem,Fortalece resistência física,Água/Sal,Sol
Chrysocolla (var.),Comunicação,Calma e Cura,Suporta expressão compassiva,Água/Sal,Lua
Smoky Quartz (Quartzo Fumê),Proteção,Desintoxicação,Transmuta stress em energia leve.,Água/Fumo,Sol ou Terra
Clear Quartz (Quartzo Cristal),Amplificador,Purificação e Amplificação,Amplifica intenções e outros cristais.,Água/Sal,Sol ou Lua
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

# Sugestões por planeta regente (exemplo) — inclui correspondências clássicas e as novas fornecidas
PLANET_TO_STONES = {
    # mapeamentos originais (mantidos quando aplicáveis)
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

# --- Novas correspondências solicitadas (sobrepõem/acompanham PLANET_TO_STONES) ---
# Lua: Ametista; Marte: Rubi; Mercurio: Topázio; Jupiter: Rubina; Venus: Safira; Saturno: Esmeralda; Sol: Granada (Cárbunculo).
PLANET_TO_STONES_UPDATE = {
    "Lua": ["Ametista"],
    "Marte": ["Rubi"],
    "Mercúrio": ["Topázio"],
    "Júpiter": ["Rubina"],
    "Vênus": ["Safira"],
    "Saturno": ["Esmeralda"],
    "Sol": ["Granada (Cárbunculo)"],
}

# Mescla as atualizações em PLANET_TO_STONES, preservando entradas existentes e adicionando as novas
for planet, stones in PLANET_TO_STONES_UPDATE.items():
    existing = PLANET_TO_STONES.get(planet, [])
    # cria lista única preservando ordem: novas pedras primeiro, depois as existentes que não duplicam
    merged = []
    for s in stones + existing:
        if s not in merged:
            merged.append(s)
    PLANET_TO_STONES[planet] = merged

# --- Layout: filtros e busca ---
st.sidebar.header("Filtros e buscas")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por objetivo / uso", "Busca livre / tabela"])

if mode == "Por signo":
    sign = st.sidebar.selectbox(
        "Selecione o signo",
        ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]
    )
    planet = SIGN_TO_PLANET.get(sign, "—")
    st.sidebar.markdown(f"**Planeta regente:** {planet}")
    suggested = SIGN_TO_STONES.get(sign, [])
    st.sidebar.markdown("**Pedras sugeridas:** " + (", ".join(suggested) if suggested else "Nenhuma sugerida"))

elif mode == "Por planeta regente":
    # cria lista única e ordenada de planetas (remove duplicatas)
    planet_list = sorted(set(SIGN_TO_PLANET.values()))
    planet_choice = st.sidebar.selectbox("Selecione o planeta", planet_list)
    suggested = PLANET_TO_STONES.get(planet_choice, [])
    st.sidebar.markdown("**Pedras associadas:** " + (", ".join(suggested) if suggested else "Nenhuma sugerida"))

elif mode == "Por objetivo / uso":
    # lista base + valores da tabela sem duplicatas, preservando ordem legível
    base_objectives = ["Coração","Espiritualidade","Proteção","Prosperidade","Vitalidade"]
    table_objectives = [o for o in df["Família de Energia"].unique().tolist() if o not in base_objectives]
    combined_objectives = base_objectives + table_objectives
    obj = st.sidebar.selectbox("Escolha o objetivo", combined_objectives)
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

# --- Correspondência planeta → pedra (nova seção) ---
st.markdown("---")
st.subheader("Correspondência Planeta → Pedra")
st.markdown(
    "Lista de correspondências clássicas e adicionais. Use como referência rápida ao escolher cristais por influência planetária."
)

planet_table = pd.DataFrame([
    {"Planeta": p, "Pedras (sugestões)": ", ".join(v)}
    for p, v in sorted(PLANET_TO_STONES.items())
])
st.table(planet_table)

# --- Extras: exportar visualização (cópia para área de transferência) ---
#st.markdown("---")
#st.subheader("Exportar / copiar")
#st.markdown("Você pode copiar a tabela filtrada e colar em uma planilha. Use o botão abaixo para gerar CSV na tela.")
#csv = df_display.to_csv(index=False)
#st.download_button("Baixar CSV (tabela filtrada)", csv, file_name="cristaloterapia_tabela.csv", mime="text/csv")

# --- Observações e cuidados ---
st.markdown("---")
st.markdown(
    "**Observações:**\n\n"
    "- As sugestões são simbólicas e informativas; não substituem orientação profissional.\n"
    "- Ao limpar ou energizar cristais, siga práticas seguras (evite água em pedras solúveis, cuidado com luz solar prolongada, etc.).\n"
)