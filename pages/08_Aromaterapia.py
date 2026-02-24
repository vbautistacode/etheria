# 06_aromaterapia.py
import streamlit as st
import pandas as pd
from io import StringIO

st.set_page_config(page_title="Aromaterapia", layout="wide")
st.title("Aromaterapia 🌿")
st.markdown(
    """
    Guia introdutório sobre óleos essenciais, métodos de uso e receitas
    seguras para relaxamento, foco e sono. Inclui avisos de segurança e contraindicações.
    """
)
st.caption("Utilize o menu lateral para selecionar o modo de consulta.")

# --- Dados de óleos e usos (exemplos) ---
OILS_CSV = """Óleo,Família,Principais Efeitos,Modo de Uso,Contraindicações
Lavanda,Floral,Calmante; Relaxamento; Sono,Inalação/Difusor/Topical (diluído),Evitar em alergia conhecida
Hortelã-Pimenta,Herbal/Mentolada,Alerta; Foco; Clareza mental,Inalação/Topical (diluído),Evitar em crianças pequenas; não aplicar puro
Laranja Doce,Cítrico,Elevação de humor; Energizante,Difusor/Topical (diluído),Fotosensibilidade leve; evitar exposição solar direta
Camomila,Floral,Relaxamento; Calmante; Sono,Inalação/Topical (diluído),Evitar se alérgico a Asteraceae
Eucalipto,Herbal,Respiração clara; Descongestionante,Inalação/Difusor/Topical (diluído),Evitar em bebês; cuidado com asma
Rosa,Floral,Equilíbrio emocional; Acalma; Afeto,Topical (diluído)/Inalação,Custo elevado; testar sensibilidade
Cedro,Amadeirado,Aterramento; Enraizamento,Difusor/Topical (diluído),Uso moderado; evitar em excesso na pele sensível
Alecrim,Herbal/Amadeirado,Memória; Concentração; Estímulo mental,Inalação/Topical (diluído),Evitar em hipertensão não controlada; não em gestantes
Sândalo,Resinoso,Presença; Aterramento; Meditação,Inalação/Difusor/Topical (diluído),Uso moderado; custo elevado
Bergamota,Cítrico,Elevação de humor; Relaxamento leve,Difusor/Topical (diluído),Fotosensibilidade; diluir bem
Ylang Ylang,Floral,Afeto; Relaxamento; Equilíbrio emocional,Inalação/Topical (diluído),Pode baixar a pressão em pessoas sensíveis
Jasmim,Floral,Sensibilidade; Introspecção; Afrodisíaco,Inalação/Topical (diluído),Custo alto; testar sensibilidade
Tea Tree (Melaleuca),Herbal/Antisséptico,Antisséptico; Suporte imunológico; Pele,Topical (diluído)/Inalação,Evitar ingestão; diluir para uso tópico
Gerânio,Floral/Herbal,Equilíbrio hormonal; Estabilidade emocional,Topical (diluído)/Difusor,Testar sensibilidade cutânea
Lavandin,Floral/Herbal,Relaxamento; Alternativa à lavanda,Inalação/Difusor/Topical (diluído),Sem contraindicações específicas além de alergia
Patchouli,Amadeirado,Aterramento; Estabilidade emocional,Difusor/Topical (diluído),Pode manchar roupas; uso moderado
Limão,Cítrico,Energia; Clareza; Elevação de humor,Difusor/Topical (diluído),Fotosensibilidade; evitar sol direto após aplicação
Lima (Lime),Cítrico,Refrescante; Estímulo; Elevação de humor,Difusor/Topical (diluído),Fotosensibilidade leve
Gengibre,Herbal/Especiado,Estimulante; Aquecimento; Digestão,Topical (diluído)/Inalação,Evitar pele sensível; diluir bem
Canela,Especiado,Estimulante; Aquecimento; Vitalidade,Topical (muito diluído)/Difusor,Potente irritante; não usar puro; evitar em gestantes
Pimenta Preta,Especiado,Estímulo; Aquecimento; Alívio muscular,Topical (diluído)/Massagem,Evitar pele sensível; diluir bem
Vetiver,Amadeirado,Aterramento profundo; Resiliência emocional,Difusor/Topical (diluído),Uso moderado; aroma intenso
Néroli,Floral,Calmante; Equilíbrio emocional; Sono,Inalação/Topical (diluído),Caro; testar sensibilidade
Cipreste,Amadeirado/Resinoso,Apoio circulatório; Aterramento,Inalação/Topical (diluído),Evitar em gestantes em alguns casos
Tomilho,Herbal,Antisséptico; Estímulo respiratório,Inalação/Topical (diluído),Potente; diluir bem; evitar ingestão sem orientação
Manjericão,Herbal,Clareza mental; Foco; Alívio de tensão,Inalação/Topical (diluído),Evitar em gestantes; diluir para uso tópico
Olíbano (Frankincense),Resinoso,Meditação; Regulação emocional; Respiração profunda,Inalação/Difusor/Topical (diluído),Uso seguro em geral; testar sensibilidade
Hissopo,Herbal,Respiração; Apoio respiratório,Inalação/Difusor,Evitar em gestantes e epilepsia
Palmarosa,Floral/Herbal,Hidratação da pele; Equilíbrio emocional,Topical (diluído)/Difusor,Testar sensibilidade
Cajeput,Herbal,Respiração clara; Antisséptico,Inalação/Difusor,Evitar em crianças pequenas
Balsamo do Peru,Resinoso,Conforto; Acolhimento,Topical (diluído)/Difusor,Alto potencial alergênico; evitar em pele sensível
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
PLANET_TO_PERFUMES = {
    "Lua": ["Jasmim"],
    "Marte": ["Verbena"],
    "Mercúrio": ["Gardênia"],
    "Júpiter": ["Flor de Maçã"],
    "Vênus": ["Hortênsia"],
    "Saturno": ["Alecrim"],
    "Sol": ["Sândalo"],
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

# --- Interface lateral (ampliada) ---
st.sidebar.header("Filtros")
mode = st.sidebar.radio("Modo de consulta", ["Por signo", "Por planeta regente", "Por objetivo / uso", "Busca livre"])

# garantir variáveis usadas posteriormente
suggested = []
suggested_perfumes = []
suggested_perfume_energy = None
objective = None
query = ""

if mode == "Por signo":
    sign = st.sidebar.selectbox("Selecione o signo", list(SIGN_TO_OILS.keys()))
    suggested = SIGN_TO_OILS.get(sign, [])
elif mode == "Por planeta regente":
    planet_choices = sorted(list(set(list(PLANET_TO_OILS.keys()) + list(PLANET_TO_PERFUMES.keys()))))
    planet = st.sidebar.selectbox("Selecione o planeta", planet_choices)
    suggested = PLANET_TO_OILS.get(planet, [])
    suggested_perfumes = PLANET_TO_PERFUMES.get(planet, [])
    suggested_perfume_energy = PLANET_PERFUME_ENERGY.get(planet)
elif mode == "Por objetivo / uso":
    objective = st.sidebar.selectbox(
       "Escolha o objetivo",
        [
            "Alívio de dor",
            "Aterramento",
            "Concentração",
            "Criatividade",
            "Despertar/Alerta",
            "Elevação de humor",
            "Energia",
            "Equilíbrio emocional",
            "Foco",
            "Memória",
            "Relaxamento",
            "Sono"
        ]

    )
else:
    query = st.sidebar.text_input("Busca livre (óleo, efeito)")

# --- Painel principal (resumo do objetivo selecionado) ---
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
        st.markdown("**Perfumes | Notas Olfativas:**")
        for p in suggested_perfumes:
            st.write(f"- {p}")
        if suggested_perfume_energy:
            st.markdown("---")
            st.subheader("Energia aromática resumida")
            st.markdown(suggested_perfume_energy)
    elif mode == "Por objetivo / uso":
        st.markdown(f"**Objetivo:** {objective}")
        st.markdown("**Filtro aplicado:**")
        st.write(objective)
    else:
        st.markdown("**Busca livre**")
        if query:
            st.write(f"Termo: **{query}**")
        else:
            st.write("Digite um termo na barra lateral para filtrar óleos.")

with col2:
    st.subheader("Fragrâncias")
    df_display = oils_df.copy()

    # Filtragem por signo / planeta (mantém comportamento anterior)
    if mode == "Por signo" and suggested:
        df_display = df_display[df_display["Óleo"].isin(suggested)]
    elif mode == "Por planeta regente" and suggested:
        df_display = df_display[df_display["Óleo"].isin(suggested)]

    # Filtragem por objetivo / uso (ampliada)
    elif mode == "Por objetivo / uso" and objective:
        obj = objective.lower()

        if obj == "relaxamento":
            pattern = r"calmante|relaxamento|sono|calma|relax"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "foco" or obj == "concentração":
            pattern = r"alerta|foco|clareza|atenção|concentra"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "sono":
            pattern = r"sono|dormir|insônia|adormecer|relaxamento|calmante"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "aterramento":
            # busca por palavras relacionadas e por famílias amadeiradas
            df_display = df_display[
                df_display["Principais Efeitos"].str.contains(r"aterramento|enraiz|enraizamento|enraizar", case=False, na=False) |
                df_display["Família"].str.contains(r"Amadeirado|Amadeirado/Herbal|Amadeirado", case=False, na=False)
            ]

        elif obj == "elevação de humor":
            pattern = r"elevação|elevar|humor|alegria|euforia|uplift|elevat"
            df_display = df_display[
                df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False) |
                df_display["Óleo"].str.contains(r"laranja|bergamota|limão|cítrico|doce", case=False, na=False)
            ]

        elif obj == "energia":
            pattern = r"energia|vitalidade|estimula|revigora|vigor"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "memória":
            pattern = r"memória|memoria|lembrar|recordar|memória|memoria"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)] \
                         | df_display["Família"].str.contains(r"Herbal|Amadeirado|Floral", case=False, na=False)

        elif obj == "criatividade":
            pattern = r"criativ|insight|imagina|inov|abertura|fluxo"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "alívio de dor":
            pattern = r"analgésico|dor|alívio|anti-inflamatório|anti-inflamatorio|reduz dor"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "equilíbrio emocional":
            pattern = r"equilíbrio|equilibrar|emocional|estabilidade|ansiedade|humor"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        elif obj == "despertar/alerta" or obj == "despertar/alerta" or obj == "despertar":
            pattern = r"alerta|despertar|estimula|vigilância|energia|clareza"
            df_display = df_display[df_display["Principais Efeitos"].str.contains(pattern, case=False, na=False)]

        else:
            # fallback: mantém df completo
            df_display = df_display

    # Busca livre
    elif mode == "Busca livre" and query:
        q = query.strip().lower()
        df_display = df_display[df_display.apply(lambda r: q in str(r["Óleo"]).lower() or q in str(r["Principais Efeitos"]).lower(), axis=1)]

    # exibe apenas a tabela dentro do expander (oculta por padrão)
    with st.expander("Mostrar lista de óleos"):
        st.dataframe(df_display.reset_index(drop=True), use_container_width=True)

    # Detalhes do óleo ficam visíveis fora do expander (sempre acessíveis)
    st.markdown("### Detalhes")
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

st.markdown("---")

# Correspondência Planeta → Perfume / Nota olfativa dentro de expander
with st.expander("Correspondência Planeta → Perfume / Nota Olfativa"):
    st.subheader("Correspondência Planeta → Perfume / Nota Olfativa")
    st.markdown(
        "Sugestões de perfumes ou notas olfativas associadas aos planetas. Use como inspiração para blends e escolhas aromáticas."
    )
    planet_perfume_table = pd.DataFrame([
        {"Planeta": p, 
         #"Nota Olfativa": ", ".join(v), 
         "Energia aromática (resumida)": PLANET_PERFUME_ENERGY.get(p, "")}
        for p, v in sorted(PLANET_TO_PERFUMES.items())
    ])
    st.table(planet_perfume_table)

# --- Observações e cuidados ---
st.markdown("---")
st.markdown("**Prática sugerida — 5 minutos**")
st.markdown("""
Siga este exercício curto para usar óleos essenciais de forma segura e eficaz:

1. **Escolha e diluição:** selecione um óleo adequado à intenção (ex.: lavanda para relaxamento, hortelã para foco). Dilua 1–2 gotas do óleo essencial em 10 ml de óleo carreador (ex.: óleo de amêndoas ou jojoba) para uso tópico, ou use 1–2 gotas em um difusor pessoal para inalação.  
2. **Ambiente:** sente-se confortavelmente num local ventilado e com luz suave. Desligue notificações e reserve 5 minutos.  
3. **Inalação consciente:** segure o frasco (ou posicione o difusor) a uma distância confortável; inspire lenta e profundamente pelo nariz por 4 segundos, segure 1–2 segundos, expire pela boca por 6 segundos. Repita por 6 ciclos (aprox. 3–5 minutos).  
4. **Foco na intenção:** enquanto respira, mantenha uma palavra‑intenção simples (ex.: "calma", "clareza") ou visualize o efeito desejado.  
5. **Encerramento:** abra os olhos devagar, movimente os ombros e beba um copo de água. Se usar tópico, lave as mãos após a aplicação.

**Aviso:** interrompa imediatamente se sentir tontura, náusea, irritação cutânea ou qualquer desconforto. Consulte um profissional em caso de dúvidas ou condições médicas.
""")

st.markdown("---")
st.markdown(
    "**Observações:**\n\n"
    "- Sempre dilua óleos essenciais antes do uso tópico (ex.: 1–3% para adultos).\n"
    "- Evite uso em gestantes, bebês e pessoas com condições médicas sem orientação.\n"
    "- Faça teste de sensibilidade antes do uso tópico."
)