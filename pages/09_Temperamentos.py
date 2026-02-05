# 09_Temperamentos.py
import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime

st.set_page_config(page_title="09 — Temperamentos", layout="wide")
st.title("Temperamentos 🌑🌔🌕🌖")

st.markdown(
    "Este autoestudo soma as características dos quatro grupos (A, B, C, D) "
    "e indica o temperamento dominante e secundário. Responda com honestidade."
)

# --- Perguntas por grupo (texto conforme fornecido) ---
QUESTIONS = {
    "A_Sanguineo": [
        "gosta de se anunciar onde chega",
        "tem olhar esperto, alegre e movimentado",
        "anda de modo elegante, flexível, gracioso, com destaque nas pontas dos pés",
        "expressa-se muito com o rosto quando fala ou escuta",
        "demonstra espontaneidade para cumprimentar e conversar",
        "conversa demais e sobre assuntos diversos",
        "facilidade para esquecer o que a aborreceu sem ficar muito magoada",
        "dificuldade em terminar os projetos que se propõe a fazer (cursinhos, poupança, arrumações, diários)",
        "interesse em participar de festas, gincanas, jogos, shows e reuniões sociais",
        "facilidade em fazer amigos onde quer que chegue"
    ],
    "B_Bilioso": [
        "tem dificuldade em esquecer as pessoas e os fatos que a magoaram",
        "tem olhar firme, concentrado e sério",
        "anda com firmeza, pressionando mais os calcanhares",
        "tem postura com ombros bem levantados, pescoço firme (ar de superioridade)",
        "gesticula e conversa com certa rispidez",
        "é muito exigente com os outros e até consigo mesmo",
        "grande disposição para mandar, liderar, dar ordens",
        "mais focado em decidir e partir para a ação",
        "irrita-se com facilidade quando é corrigido",
        "ambiciona progredir em tudo que for possível (bens, dinheiro, prestígio)"
    ],
    "C_Nervoso": [
        "evita ser notado onde chega",
        "possui olhar distante, um pouco tristonho e, às vezes, voltado para baixo",
        "tende a andar inclinando a cabeça e o corpo para frente, com ombros caídos",
        "parece que está sempre esperando alguma coisa acontecer",
        "perde tempo com muito detalhe quando conversa ou explica",
        "dificuldade em cumprimentar as pessoas com naturalidade",
        "tendência a ficar cismado ou pensando numa mesma coisa por muito tempo",
        "hábito de programar as conversas, prevendo perguntas e respostas",
        "aprecia estórias e filmes com cenas de sofrimento humano",
        "momentos de empolgação alternados com pessimismo e desânimo"
    ],
    "D_Linfatico": [
        "evita mostrar suas opiniões e talentos",
        "possui olhar meigo, cativante, como quem está pedindo algo",
        "anda meio desajeitado, bamboleante e lento",
        "tem postura de gente sossegada, acomodada, mas observadora",
        "parece um pouco insensível diante de sentimentos e reclamações alheias",
        "consegue criticar sem ofensas diretas, mas fazendo piada ou deboche",
        "prefere seguir rotinas que lhe garantem sensação de bem estar",
        "depende do contato com muitas pessoas animadas para se interessar por eventos sociais",
        "dificuldade em aceitar fazer as coisas com pressa ou sob pressão",
        "desinteresse por ginástica, dança ou maiores esforços físicos"
    ]
}

# --- Recomendações por temperamento (padrão; ajuste conforme desejar) ---
RECOMMENDATIONS = {
    "A_Sanguineo": {
        "nome": "Sanguíneo",
        "resumo": "Sociável, entusiasta e expansivo; busca estímulos sociais e variedade.",
        "pedras": ["Citrino", "Pirita", "Aventurina"],
        "cor": "Amarelo / Dourado",
        "oleo": "Laranja doce (energizante)",
        "dicas": [
            "Pratique atividades em grupo (dança, aulas coletivas).",
            "Estabeleça micro-rotinas para concluir projetos.",
            "Use exercícios de grounding ao final do dia."
        ],
        "alimentacao": "Tendência a dieta mista com ênfase em frutas e vegetais; evitar excessos."
    },
    "B_Bilioso": {
        "nome": "Bilioso / Colérico",
        "resumo": "Decidido, enérgico e orientado à ação; tende à liderança e ambição.",
        "pedras": ["Rubi", "Granada"],
        "cor": "Vermelho / Laranja",
        "oleo": "Pimenta preta (estimulante) ou alecrim para foco",
        "dicas": [
            "Canalize energia em exercícios intensos (treino intervalado).",
            "Pratique respiração ativa antes de decisões importantes.",
            "Reserve momentos para desacelerar e revisar planos."
        ],
        "alimentacao": "Evitar gorduras excessivas; preferir refeições equilibradas e regulares."
    },
    "C_Nervoso": {
        "nome": "Nervoso / Melancólico",
        "resumo": "Introspectivo, detalhista e sensível; tendência à reflexão profunda.",
        "pedras": ["Ametista", "Quartzo Rosa"],
        "cor": "Azul / Lilás",
        "oleo": "Lavanda (calmante)",
        "dicas": [
            "Pratique journaling para organizar pensamentos.",
            "Inclua pausas regulares e técnicas de relaxamento.",
            "Evite estimulantes e priorize sono reparador."
        ],
        "alimentacao": "Preferir frutas, legumes e evitar excitantes; atenção ao cálcio e proteínas leves."
    },
    "D_Linfatico": {
        "nome": "Linfático / Fleumático",
        "resumo": "Calmo, estável e rotineiro; busca conforto e previsibilidade.",
        "pedras": ["Hematita", "Jaspe"],
        "cor": "Verde / Marrom",
        "oleo": "Camomila ou sândalo (suavizante)",
        "dicas": [
            "Mantenha rotina regular e exercícios leves (caminhada).",
            "Introduza mudanças graduais para evitar resistência.",
            "Use práticas de mobilidade para energia corporal."
        ],
        "alimentacao": "Alimentação mista; moderação em álcool e gorduras; rotina alimentar regular."
    }
}

# --- UI: instruções e formulário ---
st.markdown("Clique em **Iniciar** para abrir o questionário. Use valores de 0 (nunca) a 10 (sempre).")
if "started" not in st.session_state:
    st.session_state.started = False

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Iniciar / Reiniciar"):
        st.session_state.started = True
        # reset responses
        st.session_state.responses = {}

if not st.session_state.started:
    st.info("Pressione Iniciar para responder o autoestudo.")
    st.stop()

# render sliders por grupo
if "responses" not in st.session_state:
    st.session_state.responses = {}

for group, qs in QUESTIONS.items():
    st.header(group.replace("_", " "))
    cols = st.columns(2)
    for i, q in enumerate(qs):
        key = f"{group}_{i}"
        default = st.session_state.responses.get(key, None)
        val = cols[i % 2].slider(q, 0, 10, value=default if default is not None else 0, key=key)
        st.session_state.responses[key] = val

# botão calcular
if st.button("Calcular resultado"):
    # soma por grupo
    scores = {}
    for group in QUESTIONS:
        vals = [st.session_state.responses[f"{group}_{i}"] for i in range(len(QUESTIONS[group]))]
        total = sum(vals)  # 0-100
        score = round(total, 2)
        scores[group] = score

    # DataFrame para exibição
    df_scores = pd.DataFrame.from_dict(scores, orient="index", columns=["Pontuação"])
    df_scores.index = df_scores.index.str.replace("_", " ")
    st.subheader("Resultados (0–100)")
    st.bar_chart(df_scores["Pontuação"])

    # ordenar e determinar dominante/secundário
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    dominant_key, dominant_val = sorted_scores[0]
    secondary_key, secondary_val = sorted_scores[1]

    dominant_label = RECOMMENDATIONS[dominant_key]["nome"]
    secondary_label = RECOMMENDATIONS[secondary_key]["nome"]

    st.markdown("---")
    st.markdown(f"**Temperamento dominante:** **{dominant_label}** — {dominant_val} pontos")
    st.markdown(f"**Temperamento secundário:** **{secondary_label}** — {secondary_val} pontos")

    # detectar mistura próxima
    if abs(dominant_val - secondary_val) <= 8:
        st.warning("Pontuações próximas: é possível que você tenha um temperamento misto. Considere ler as descrições de ambos.")

    # exibir recomendações
    st.subheader("Interpretação e recomendações")
    def show_rec(key):
        rec = RECOMMENDATIONS[key]
        st.markdown(f"### {rec['nome']}")
        st.markdown(f"**Resumo:** {rec['resumo']}")
        st.markdown(f"**Pedras sugeridas:** {', '.join(rec['pedras'])}")
        st.markdown(f"**Cromoterapia (cor):** {rec['cor']}")
        st.markdown(f"**Aromaterapia (óleo):** {rec['oleo']}")
        st.markdown("**Dicas práticas:**")
        for d in rec["dicas"]:
            st.write(f"- {d}")
        st.markdown(f"**Alimentação (sugestão):** {rec['alimentacao']}")

    show_rec(dominant_key)
    st.markdown("---")
    show_rec(secondary_key)

    # salvar resultado em session_state (opcional)
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scores": scores,
        "dominant": dominant_label,
        "dominant_score": dominant_val,
        "secondary": secondary_label,
        "secondary_score": secondary_val
    }
    st.session_state.last_result = result

    # opção de exportar como JSON (usuário pode copiar)
    st.markdown("---")
    st.subheader("Exportar / Salvar")
    st.markdown("Você pode copiar o JSON abaixo para salvar localmente.")
    st.code(json.dumps(result, indent=2, ensure_ascii=False))

    st.success("Autoestudo concluído. Se desejar, repita em duas semanas para comparar resultados.")