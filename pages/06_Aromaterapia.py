# 06_aromaterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.title("Aromaterapia 🌿")
st.markdown(
    """
    Aromaterapia: guia introdutório sobre óleos essenciais, métodos de uso e receitas
    seguras para relaxamento, foco e sono. Inclui avisos de segurança e contraindicações.
    """
)

# --- Dados de óleos e usos (exemplos) ---
OILS_CSV = """Óleo,Família,Principais Efeitos,Modo de Uso,Contraindicações
Lavanda,Floral,Calmante,Inalação/ Difusor/Topical (diluído),Evitar em alergia conhecida
Hortelã-Pimenta,Cítrico/Herbal,Alerta e foco,Inalação/Topical (diluído),Evitar em crianças pequenas
Laranja Doce,Cítrico,Elevação de humor,Difusor/Topical (diluído),Fotosensibilidade leve
Camomila,Floral,Relaxamento,Inalação/Topical (diluído),Evitar se alérgico a Asteraceae
Eucalipto,Herbal,Respiração clara,Inalação/Difusor,Evitar em bebês
Rosa,Floral,Equilíbrio emocional,Topical (diluído),Custo elevado
Cedro,Amadeirado,Aterramento,Difusor/Topical (diluído),Uso moderado
"""

oils_df = pd.read_csv(StringIO(OILS_CSV))

# Mapeamentos por signo/planeta (exemplos)
SIGN_TO_OILS = {
    "Áries": ["Hortelã-Pimenta", "Cedro"],
    "Touro": ["Rosa", "Laranja Doce"],
    "Gêmeos": ["Hortelã-Pimenta", "Lavanda"],
    "Câncer": ["Camomila", "Lavanda"],
    "Leão": ["Laranja Doce", "Cedro"],
    "Virgem": ["Eucalipto", "Lavanda"],
    "Libra": ["Rosa", "Lavanda"],
    "Escorpião": ["Cedro", "Eucalipto"],
    "Sagitário": ["Laranja Doce", "Hortelã-Pimenta"],
    "Capricórnio": ["Cedro", "Camomila"],
    "Aquário": ["Eucalipto", "Hortelã-Pimenta"],
    "Peixes": ["Lavanda", "Rosa"]
}
PLANET_TO_OILS = {
    "Sol": ["Laranja Doce"], "Lua": ["Lavanda", "Camomila"], "Marte": ["Hortelã-Pimenta"],
    "Vênus": ["Rosa"], "Mercúrio": ["Hortelã-Pimenta"], "Júpiter": ["Laranja Doce"],
    "Saturno": ["Cedro"], "Netuno": ["Lavanda"], "Urano": ["Eucalipto"], "Plutão": ["Cedro"]
}

# --- Novas correspondências Perfume → Planeta (solicitadas) ---
# Lua: Jasmim; Marte: Verbena; Mercurio: Gardênia; Jupiter: Flor de Maçã; Venus: Hortênsia; Saturno: Alecrim; Sol: Sândalo
PLANET_TO_PERFUMES = {
    "Lua": ["Jasmim"],
    "Marte": ["Verbena"],
    "Mercúrio": ["Gardênia"],
    "Júpiter": ["Flor de Maçã"],
    "Vênus": ["Hortênsia"],
    "Saturno": ["Alecrim"],
    "Sol": ["Sândalo"],
    # complementar para outros planetas se necessário
    "Urano": ["Notas Cítricas"],
    "Netuno": ["Notas Marinhas"],
    "Plutão": ["Notas Amadeiradas"]
}

# --- Explicação resumida da energia aromática por planeta ---
PLANET_PERFUME_ENERGY = {
    "Lua": "Jasmim — aroma suave e envolvente; favorece introspecção, sensibilidade emocional e conexão com o feminino interior.",
    "Marte": "Verbena — nota cítrica-herbal estimulante; desperta coragem, ação e clareza energética para iniciar tarefas.",
    "Mercúrio": "Gardênia — fragrância clara e comunicativa; auxilia expressão, foco mental e fluidez nas ideias.",
    "Júpiter": "Flor de Maçã — aroma leve e expansivo; inspira otimismo, abertura e sensação de abundância interior.",
    "Vênus": "Hortênsia — nota floral harmonizadora; promove afeto, suavidade nas relações e equilíbrio afetivo.",
    "Saturno": "Alecrim — aroma amadeirado-herbal, enraizante; favorece disciplina, memória, estrutura e foco prático.",
    "Sol": "Sândalo — nota quente e resinosa; fortalece vitalidade, presença, autoestima e clareza de propósito.",
    "Urano": "Notas Cítricas — estimulam inovação e leveza.",
    "Netuno": "Notas Marinhas — evocam imaginação e estados contemplativos.",
    "Plutão": "Notas Amadeiradas — apoiam transformação profunda e aterramento."
}

# --- Interface lateral ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por objetivo / uso", "Busca livre"])

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_OILS.keys()))
    suggested = SIGN_TO_OILS.get(sign, [])
    # infer planet if desired (not shown in sidebar here)
elif mode == "Por planeta regente":
    # combina chaves de óleos e perfumes para garantir lista completa
    planet_choices = sorted(list(set(list(PLANET_TO_OILS.keys()) + list(PLANET_TO_PERFUMES.keys()))))
    planet = st.sidebar.selectbox("Selecione o planeta", planet_choices)
    suggested = PLANET_TO_OILS.get(planet, [])
    suggested_perfumes = PLANET_TO_PERFUMES.get(planet, [])
    suggested_perfume_energy = PLANET_PERFUME_ENERGY.get(planet)
elif mode == "Por objetivo / uso":
    objective = st.sidebar.selectbox("Escolha o objetivo", ["Relaxamento","Foco","Sono","Aterramento","Elevação de humor"])
else:
    query = st.sidebar.text_input("Busca livre (óleo, efeito)")
    suggested_perfume_energy = None

# --- Painel principal ---
st.header("Óleos essenciais, perfumes e recomendações")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Resumo")
    if mode == "Por signo":
        st.markdown(f"**Signo:** {sign}")
        st.markdown("**Óleos sugeridos:**")
        for o in suggested:
            st.write(f"- {o}")
    elif mode == "Por planeta regente":
        st.markdown(f"**Planeta:** {planet}")
        st.markdown("**Óleos associados:**")
        for o in suggested:
            st.write(f"- {o}")
        st.markdown("**Perfumes/Notas sugeridas:**")
        for p in suggested_perfumes:
            st.write(f"- {p}")
        if suggested_perfume_energy:
            st.markdown("---")
            st.subheader("Energia aromática resumida")
            st.markdown(suggested_perfume_energy)
    elif mode == "Por objetivo / uso":
        st.markdown(f"**Objetivo:** {objective}")
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar óleos.")

    st.markdown("---")
    st.subheader("Segurança rápida")
    st.markdown(
        "- Sempre dilua óleos essenciais antes do uso tópico (ex.: 1–3% para adultos).\n"
        "- Evite uso em gestantes, bebês e pessoas com condições médicas sem orientação.\n"
        "- Faça teste de sensibilidade antes do uso tópico."
    )

with col2:
    st.subheader("Lista de óleos")
    df_display = oils_df.copy()
    if mode == "Por signo" and suggested:
        df_display = df_display[df_display["Óleo"].isin(suggested)]
    elif mode == "Por planeta regente" and suggested:
        df_display = df_display[df_display["Óleo"].isin(suggested)]
    elif mode == "Por objetivo / uso":
        if objective == "Relaxamento":
            df_display = df_display[df_display["Principais Efeitos"].str.contains("Calmante|Relaxamento|Sono", case=False, na=False)]
        elif objective == "Foco":
            df_display = df_display[df_display["Principais Efeitos"].str.contains("Alerta|foco|clareza", case=False, na=False)]
        # adicione mais regras conforme necessário
    else:
        if mode == "Busca livre" and query:
            q = query.strip().lower()
            df_display = df_display[df_display.apply(lambda r: q in str(r["Óleo"]).lower() or q in str(r["Principais Efeitos"]).lower(), axis=1)]

    st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    st.markdown("### Detalhes do óleo")
    oils = df_display["Óleo"].tolist()
    if oils:
        sel = st.selectbox("Escolha um óleo", [""] + oils)
        if sel:
            row = df_display[df_display["Óleo"] == sel].iloc[0]
            st.markdown(f"**{row['Óleo']}** — *{row['Família']}*")
            st.markdown(f"- **Principais efeitos:** {row['Principais Efeitos']}")
            st.markdown(f"- **Modo de uso:** {row['Modo de Uso']}")
            st.markdown(f"- **Contraindicações:** {row['Contraindicações']}")
    else:
        st.info("Nenhum óleo encontrado com os filtros atuais.")

# --- Correspondência Planeta → Perfume (nova seção) ---
st.markdown("---")
st.subheader("Correspondência Planeta → Perfume / Nota olfativa")
st.markdown(
    "Sugestões de perfumes ou notas olfativas associadas aos planetas. Use como inspiração para blends e escolhas aromáticas."
)
planet_perfume_table = pd.DataFrame([
    {"Planeta": p, "Nota Olfativa": ", ".join(v), "Energia aromática (resumida)": PLANET_PERFUME_ENERGY.get(p, "")}
    for p, v in sorted(PLANET_TO_PERFUMES.items())
])
st.table(planet_perfume_table)