# 09_Temperamentos.py (esqueleto)
import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config("Temperamentos", layout="wide")
st.title("09 — Temperamentos (Autoestudo)")

st.markdown("Preencha as 10 características de cada grupo com valores de 0 a 10.")

# Definição das questões (exemplo usando as frases que você enviou)
QUESTIONS = {
    "A_Sanguineo": [
        "gosta de se anunciar onde chega",
        "tem olhar esperto, alegre e movimentado",
        "anda de modo elegante, flexível, gracioso, com destaque nas pontas dos pés",
        "expressa-se muito com o rosto quando fala ou escuta",
        "demonstra espontaneidade para cumprimentar e conversar",
        "conversa demais e sobre assuntos diversos",
        "facilidade para esquecer o que a aborreceu sem ficar muito magoada",
        "dificuldade em terminar os projetos que se propõe a fazer",
        "interesse em participar de festas, gincanas, jogos, shows e reuniões sociais",
        "facilidade em fazer amigos onde quer que chegue"
    ],
    "B_Bilioso": [
        "tem dificuldade em esquecer as pessoas e os fatos que a magoaram",
        "tem olhar firme, concentrado e sério",
        "anda com firmeza, pressionando mais os calcanhares",
        "tem postura com ombros bem levantados, pescoço firme",
        "gesticula e conversa com certa rispidez",
        "é muito exigente com os outros e até consigo mesmo",
        "grande disposição para mandar, liderar, dar ordens",
        "mais focado em decidir e partir para a ação",
        "irrita-se com facilidade quando é corrigido",
        "ambiciona progredir em tudo que for possível"
    ],
    "C_Melancolico": [
        "evita ser notado onde chega",
        "possui olhar distante, um pouco tristonho",
        "tende a andar inclinando a cabeça e o corpo para frente",
        "parece que está sempre esperando alguma coisa acontecer",
        "perde tempo com muito detalhe quando conversa ou explica",
        "dificuldade em cumprimentar as pessoas com naturalidade",
        "tendência a ficar cismado ou pensando numa mesma coisa por muito tempo",
        "hábito de programar as conversas",
        "aprecia estórias e filmes com cenas de sofrimento humano",
        "momentos de empolgação alternados com pessimismo"
    ],
    "D_Linfatico": [
        "evita mostrar suas opiniões e talentos",
        "possui olhar meigo, cativante",
        "anda meio desajeitado, bamboleante e lento",
        "tem postura de gente sossegada, acomodada, mas observadora",
        "parece um pouco insensível diante de sentimentos alheios",
        "consegue criticar sem ofensas diretas, mas fazendo piada",
        "prefere seguir rotinas que garantem bem estar",
        "depende do contato com muitas pessoas animadas para se interessar",
        "dificuldade em aceitar fazer as coisas com pressa",
        "desinteresse para ginástica ou maiores esforços"
    ]
}

# coletar respostas
st.header("Autoestudo")
responses = {}
for group, qs in QUESTIONS.items():
    st.subheader(group.replace("_", " "))
    cols = st.columns(2)
    for i, q in enumerate(qs):
        key = f"{group}_{i}"
        responses[key] = cols[i % 2].slider(q, 0, 10, 0, key=key)

if st.button("Calcular resultado"):
    # soma por grupo
    scores = {}
    for group in QUESTIONS:
        vals = [responses[f"{group}_{i}"] for i in range(len(QUESTIONS[group]))]
        total = sum(vals)
        # normaliza para 0-100 (max 100)
        score = round(total, 2)
        scores[group] = score

    # exibir resultados
    df_scores = pd.DataFrame.from_dict(scores, orient="index", columns=["Score"])
    st.bar_chart(df_scores)

    # determinar dominante e secundário
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    dominant, secondary = sorted_scores[0], sorted_scores[1]
    st.markdown(f"**Dominante:** {dominant[0]} — {dominant[1]} pontos")
    st.markdown(f"**Secundário:** {secondary[0]} — {secondary[1]} pontos")

    # recomendações (exemplo)
    RECS = {
        "A_Sanguineo": {"Resumo":"Sanguíneo: sociável e entusiasta.","Pedras":["Citrino","Pirita"], "Dicas":["Exercício em grupo","Rotina leve"]},
        "B_Bilioso": {"Resumo":"Bilioso: decidido e enérgico.","Pedras":["Rubi","Granada"], "Dicas":["Atividade física intensa","Respiração ativa"]},
        "C_Melancolico": {"Resumo":"Melancólico: introspectivo e detalhista.","Pedras":["Ametista","Quartzo Rosa"], "Dicas":["Journaling","Meditação curta"]},
        "D_Linfatico": {"Resumo":"Linfático: calmo e estável.","Pedras":["Hematita","Jaspe"], "Dicas":["Rotina regular","Caminhada leve"]}
    }
    st.markdown("### Recomendações rápidas")
    st.write(RECS[dominant[0]])