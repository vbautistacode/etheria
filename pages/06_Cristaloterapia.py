# 04_cristaloterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Cristaloterapia", layout="wide")
st.title("Cristaloterapia 💎")

st.markdown(
    """
    Introdução: A cirstaloterapia é a prática de usar cristais para apoio emocional, foco e aterramento. 
    Aqui, você encontra orientações básicas de cuidado e sugestões por intenção.
    """
)
st.caption("Utilize o menu lateral para selecionar o modo de consulta.")

# --- Dados CSV Corrigidos e Incrementados ---
CSV_DATA = """Pedra,Família de Energia,Essência (Significado),Principais Benefícios,Limpeza,Energização
"Ágata Azul","Espiritualidade","Paz Interior","Acalma os nervos e suaviza as palavras.","Água/Sal","Lua"
"Amazonita","Comunicação","Equilíbrio","Suaviza emoções e facilita expressão.","Água/Sal","Lua"
"Ametista","Espiritualidade","Transmutação","Transmuta dor em paz e ajuda no sono.","Água/Fumo","Lua"
"Aventurina","Prosperidade","Sorte e Oportunidade","Atrai sorte rápida e novas chances.","Água","Sol"
"Celestina","Espiritualidade","Paz Angélica","Serenidade extrema e conexão com guias.","Fumo apenas","Lua"
"Cianita Azul","Alinhamento","Comunicação","Alinha chakras sem necessidade de limpeza.","Autolimpante","Lua"
"Citrino","Prosperidade","Abundância","Sucesso e alegria solar.","Autolimpante","Sol"
"Cornalina","Vitalidade","Fogo e Ação","Vence a preguiça e dá coragem física.","Água/Sal","Sol"
"Esmeralda","Coração","Amor Sábio","Fortalece a lealdade e o equilíbrio.","Fumo/Água","Lua"
"Fluorita","Clareza","Organização Mental","Ajuda concentração e ordena pensamentos.","Água","Sol ou Lua"
"Granada (Carbúnculo)","Vitalidade","Regeneração","Revitaliza o corpo e desperta paixão.","Água (rápida)","Sol"
"Hematita","Proteção","Aterramento","Foco, lógica e proteção pessoal.","Fumo","Sol"
"Jaspe Vermelho","Vitalidade","Nutridor Supremo","Sustenta e estabiliza em longas jornadas.","Água/Sal","Terra ou Sol"
"Labradorita","Proteção","Escudo Mágico","Protege a aura e intensifica intuição.","Fumo/Terra","Lua"
"Lápis-Lazúli","Espiritualidade","Visão Interior","Clareia a mente e favorece intuição.","Fumo","Lua"
"Malaquita","Transformação","Proteção e Cura","Transmuta padrões (Cuidado: Tóxica em pó).","Fumo/Terra","Sol"
"Morganita","Coração","Amor Divino","Abre o coração para compaixão e cura.","Água/Sal","Lua"
"Obsidiana","Proteção","Espelho da Alma","Revela verdades e corta laços.","Fumo/Terra","Sol ou Lua"
"Olho de Tigre","Prosperidade","Estrategista","Protege contra inveja e dá foco.","Água/Sal","Sol"
"Ônix","Proteção","Autocontrole","Dá força estrutural em tempos difíceis.","Fumo","Sol ou Lua"
"Pedra da Lua","Intuição","Renovação","Estimula intuição e ciclos femininos.","Água","Lua"
"Pirita","Prosperidade","Ímã de Ouro","Atrai bens materiais e confiança.","Fumo (Não molhar)","Sol"
"Quartzo Anjo","Espiritualidade","Paz Profunda","Alivia ansiedade e facilita meditação.","Fumo","Lua"
"Quartzo Branco","Espiritualidade","Amplificador","Potencializa desejos e limpa aura.","Todos","Sol ou Lua"
"Quartzo Fumê","Proteção","Desintoxicação","Transmuta stress em energia leve.","Fumo/Água","Sol ou Terra"
"Quartzo Rosa","Coração","Amor e Cura","Promove amor próprio e harmonia.","Água/Sal","Lua"
"Rubi","Vitalidade","Paixão e Coragem","Aumenta energia vital e coragem.","Água/Sal","Sol"
"Rubina","Prosperidade","Manifestação Ativa","Foca a paixão na conquista material.","Água/Sal","Sol"
"Safira","Espiritualidade","Sabedoria Real","Estimula a disciplina e clareza mental.","Água/Sal","Lua"
"Selenita","Espiritualidade","Purificador Mestre","Limpa ambientes e outros cristais.","Fumo (Não molhar)","Lua"
"Sodalita","Espiritualidade","Clareza Mental","Une intuição à lógica na comunicação.","Água","Lua"
"Topázio","Prosperidade","Manifestação","Atrai abundância e clareia intenções.","Fumo","Sol"
"Turmalina Negra","Proteção","Escudo Energético","Bloqueia inveja e radiação.","Fumo/Terra","Sol/Terra"
"Turquesa Verde","Intuição","Proteção e Cura","Equilibra emoções e protege o viajante.","Fumo/Terra","Sol ou Lua"
"""

# leitura tolerante e correta do CSV (campos entre aspas)
df = pd.read_csv(StringIO(CSV_DATA), quotechar='"', skipinitialspace=True, encoding='utf-8')

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
    "Escorpião": "Marte",
    "Escorpião": "Plutão",
    "Sagitário": "Júpiter",
    "Capricórnio": "Saturno",
    "Aquário": "Saturno",
    "Aquário": "Urano",
    "Peixes": "Júpiter",
    "Peixes": "Netuno"
}

# Sugestões de pedras por signo (lista curta, baseada na tabela)
SIGN_TO_STONES = {
    "Áries": ["Jaspe Vermelho", "Granada (Carbúnculo)", "Rubi"],
    "Touro": ["Quartzo Rosa", "Esmeralda", "Malaquita"],
    "Gêmeos": ["Citrino", "Sodalita", "Ágata"],
    "Câncer": ["Pedra da Lua", "Quartzo Rosa", "Quartzo Anjo"],
    "Leão": ["Olho de Tigre", "Citrino", "Pirita"],
    "Virgem": ["Amazonita", "Aventurina", "Hematita"],
    "Libra": ["Quartzo Verde", "Lápis-Lazúli", "Topázio Imperial"],
    "Escorpião": ["Obsidiana", "Turmalina Negra", "Granada (Carbúnculo)"],
    "Sagitário": ["Sodalita", "Ametista", "Lápis-Lazúli"],
    "Capricórnio": ["Ônix", "Hematita", "Quartzo Fumê"],
    "Aquário": ["Ametista", "Fluorita", "Labradorita"],
    "Peixes": ["Ametista", "Celestina", "Cianita Azul"],
}

# Sugestões por planeta regente (exemplo) — inclui correspondências clássicas e as novas fornecidas
PLANET_TO_STONES = {
    "Sol": [],
    "Lua": [],
    "Marte": [],
    "Vênus": [],
    "Mercúrio": [],
    "Júpiter": [],
    "Saturno": [],
    "Urano": ["Turquesa Verde"],
    "Netuno": ["Celestina"],
    "Plutão": ["Obsidiana"],
}

# --- Novas correspondências solicitadas (sobrepõem/acompanham PLANET_TO_STONES) ---
# Atualizações fornecidas pelo usuário, com nomes em português
PLANET_TO_STONES_UPDATE = {
    "Lua": ["Ametista"],
    "Marte": ["Rubi"],
    "Mercúrio": ["Topázio"],
    "Júpiter": ["Rubina"],
    "Vênus": ["Safira"],
    "Saturno": ["Esmeralda"],
    "Sol": ["Granada (Carbúnculo)"],
}

# Mescla as atualizações em PLANET_TO_STONES, preservando entradas existentes e adicionando as novas
for planet, stones in PLANET_TO_STONES_UPDATE.items():
    existing = PLANET_TO_STONES.get(planet, [])
    merged = []
    for s in stones + existing:
        if s not in merged:
            merged.append(s)
    PLANET_TO_STONES[planet] = merged

# --- Explicações resumidas para pedras associadas aos planetas ---
PLANET_STONE_EXPLANATIONS = {
    "Lua": "Ametista — favorece intuição, calma emocional e conexão com o mundo interior.",
    "Marte": "Rubi — estimula coragem, vitalidade e força de vontade; ativa energia física.",
    "Mercúrio": "Topázio — clareza mental e comunicação; auxilia expressão e raciocínio.",
    "Júpiter": "Rubina — favorece expansão, sorte e crescimento; atua na prosperidade e otimismo.",
    "Vênus": "Safira — harmonia, beleza e equilíbrio afetivo; favorece relacionamentos e sensibilidade estética.",
    "Saturno": "Esmeralda — estabilidade, sabedoria prática e cura do coração; apoio em processos longos.",
    "Sol": "Granada (Carbúnculo) — vigor, presença e autoestima; fortalece propósito e ação criativa.",
    # novas explicações pedidas
    "Netuno": "Celestina — favorece sensibilidade psíquica, sonhos lúcidos e conexão com o inconsciente coletivo.",
    "Urano": "Turquesa Verde — estimula originalidade, intuição inventiva e proteção em mudanças súbitas.",
    "Plutão": "Obsidiana — transformação profunda, liberação de padrões e proteção contra influências densas.",
}

# mapa inverso pedra -> planeta (para exibir explicação ao selecionar uma pedra)
STONE_TO_PLANET = {}
for p, stones in PLANET_TO_STONES.items():
    for s in stones:
        STONE_TO_PLANET[s] = p

# --- Tema 'Sorte' (novidade solicitada) ---
# Lista com nomes em português presentes na tabela CSV; entradas em inglês foram removidas
THEME_TO_STONES = {
    "Sorte": [
        "Citrino",
        "Pirita",
        "Aventurina",
        "Olho de Tigre",
        "Chrysoprase"  # Chrysoprase está no CSV; manter nome (pode ser "Crisoprase" em pt-br dependendo da preferência)
    ]
}

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
    base_objectives = [
        "Alinhamento",
        "Amor",
        "Calma",
        "Calmante",
        "Clareza",
        "Comunicação",
        "Coração",
        "Emoção",
        "Equilíbrio",
        "Espiritualidade",
        "Intuição",
        "Prosperidade",
        "Proteção",
        "Proteção e Comunicação",
        "Proteção Espiritual",
        "Renovação",
        "Sorte",
        "Transformação",
        "Visão Interior",
        "Vitalidade",
    ]

    # limpar e ordenar
    base_sorted = sorted(set([b.strip() for b in base_objectives if b.strip()]), key=lambda s: s.casefold())

    # pegar e ordenar os objetivos vindos da tabela, excluindo os já em base_sorted
    table_objectives = sorted(set([o.strip() for o in df["Família de Energia"].unique().tolist() if o and o.strip() and o not in base_sorted]), key=lambda s: s.casefold())

    combined_objectives = base_sorted + table_objectives
    obj = st.sidebar.selectbox("Escolha o objetivo", combined_objectives)

    st.sidebar.markdown("Resultados mostrados na tabela principal abaixo.")

else:
    # Busca livre / tabela
    query = st.sidebar.text_input("Busca livre (nome, essência, benefício)")

# --- Painel principal ---
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
        if obj in THEME_TO_STONES:
            st.markdown("**Pedras para Sorte:**")
            for p in THEME_TO_STONES[obj]:
                st.write(f"- {p}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar a tabela.")

with col2:
    st.subheader("Tabela de Referência")
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
            # se for um tema especial (ex.: Sorte), filtra pela lista definida
            if obj in THEME_TO_STONES:
                df_display = df_display[df_display["Pedra"].isin(THEME_TO_STONES[obj])]
            else:
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

    # exibe tabela interativa dentro de um expander (oculta por padrão)
    with st.expander("Mostrar tabela de referência"):
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    # seleção de pedra para detalhes (com explicação planetária quando aplicável)
    st.markdown("### Detalhes")
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
            # se a pedra estiver mapeada para um planeta, mostrar a explicação resumida
            planet_for_stone = STONE_TO_PLANET.get(selected)
            if planet_for_stone:
                explanation = PLANET_STONE_EXPLANATIONS.get(planet_for_stone)
                st.markdown("---")
                st.markdown(f"**Correspondência planetária:** {planet_for_stone}")
                if explanation:
                    st.markdown(f"**Resumo:** {explanation}")
    else:
        st.info("Nenhuma pedra encontrada com os filtros atuais.")

# --- Correspondência planeta → pedra (nova seção) com explicações dentro de expander ---
st.markdown("---")
with st.expander("Correspondência Planeta → Pedra"):
    st.subheader("Correspondência Planeta → Pedra")
    st.markdown(
        "Lista de correspondências clássicas e adicionais. Use como referência rápida ao escolher cristais por influência planetária."
    )

    planet_table = pd.DataFrame([
        {
            "Planeta": p,
            #"Pedras (sugestões)": ", ".join(v),
            "Explicação resumida": PLANET_STONE_EXPLANATIONS.get(p, "")
        }
        for p, v in sorted(PLANET_TO_STONES.items())
    ])
    st.table(planet_table)

# --- Observações e cuidados ---
st.markdown("---")
st.markdown(""
    "**Como utilizar cristais no dia a dia:**\n\n")
st.markdown("""
**1. No Corpo (Uso Pessoal)**

**Lado Esquerdo (Receber):** Use pedras de Espiritualidade e Proteção — por exemplo, **Ametista** e **Turmalina Negra** — no pulso ou no bolso esquerdo para absorver energia de paz e proteger seu campo sensível.

**Lado Direito (Dar/Agir):** Use pedras de Prosperidade e Vitalidade — por exemplo, **Citrino**, **Cornalina** e **Pirita** — no lado direito para projetar sua vontade, manter foco no trabalho e atrair abundância.

**Plexo Solar (estômago):** Pedras como o **Citrino** ajudam a aumentar a autoconfiança antes de reuniões ou apresentações.

**2. No Ambiente (Casa ou Escritório)**

**Porta de entrada:** Coloque uma **Turmalina Negra** ou **Ônix** do lado de fora ou logo na entrada para barrar energias negativas de quem chega.

**Canto da prosperidade:** No fundo à esquerda da porta de entrada, disponha um arranjo com **Pirita**, **Citrino** e **Aventurina** para estimular o fluxo financeiro do ambiente.

**Quarto de dormir:** Use **Ametista** ou **Quartzo Azul** na mesa de cabeceira para sono reparador e sonhos lúcidos. Evite pedras vermelhas (por exemplo, **Granada**) no quarto, pois podem aumentar a energia e prejudicar o sono.

**3. Programação e Intenção (O Segredo)**

Um cristal sem intenção é apenas um objeto bonito. Ao adquirir uma pedra nova:

- Segure-a com as duas mãos.
- Feche os olhos e respire fundo.
- Mentalize claramente sua intenção e diga: **"Eu programo este cristal para [sua intenção, ex.: atrair sorte / proteger minha casa] para o meu bem maior."**

**4. Manutenção Expresso**

**Limpeza rápida:** Passe a pedra pelo fumo de um incenso de arruda ou sálvia.

**Recarga de emergência:** Coloque a pedra sobre uma **Selenita** por 15 minutos (a Selenita ajuda a limpar outras pedras automaticamente).

**Vitalidade máxima:** Pedras de cor quente (amarelo, laranja, vermelho) beneficiam-se do sol da manhã; pedras de cor fria (azul, lilás, rosa) preferem a lua.

**Observações finais:**  
- As sugestões são simbólicas e informativas; não substituem orientação profissional.  
- Ao limpar ou energizar cristais, siga práticas seguras (evite água em pedras solúveis, cuidado com exposição solar prolongada, etc.).
""")