# 09_Temperamentos.py
import streamlit as st
import pandas as pd
import numpy as np
import json
from datetime import datetime
import matplotlib.pyplot as plt

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

# --- Recomendações por temperamento (alimentação detalhada incluída) ---
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
        "alimentacao": (
            "Padrão: dieta mista com tendência a opções vegetais; propensão ao vegetariano/frugívoro.\n\n"
            "- Priorize frutas frescas, saladas e vegetais crus/cozidos; inclua grãos integrais e leguminosas em porções moderadas.\n"
            "- No verão, evite refeições muito pesadas (carne gordurosa, excesso de batata e feijão em grandes porções) para reduzir risco de desconforto e insolação.\n"
            "- Prefira porções menores e mais frequentes em dias quentes; mantenha hidratação adequada.\n"
            "- Reduza estimulantes e álcool em excesso; observe sinais de pressão arterial elevada e ajuste a dieta conforme necessário."
        )
    },
    "B_Bilioso": {
        "nome": "Bilioso / Colérico",
        "resumo": "Decidido, enérgico e orientado à ação; tende à liderança e ambição.",
        "pedras": ["Rubi", "Granada"],
        "cor": "Vermelho / Laranja",
        "oleo": "Alecrim ou pimenta preta para foco",
        "dicas": [
            "Canalize energia em exercícios intensos (treino intervalado).",
            "Pratique respiração ativa antes de decisões importantes.",
            "Reserve momentos para desacelerar e revisar planos."
        ],
        "alimentacao": (
            "Padrão: dieta mista semelhante ao nervoso, com atenção especial ao fígado.\n\n"
            "- Evite gorduras saturadas e frituras que sobrecarreguem o fígado; prefira carnes magras quando consumir proteína animal.\n"
            "- Inclua fibras (vegetais, frutas, cereais integrais) para apoiar a digestão e o trânsito intestinal.\n"
            "- Modere alimentos muito condimentados ou alcoólicos; se houver problemas digestivos (colite, hemorróidas), reduza gorduras e alimentos irritantes.\n"
            "- Mantenha refeições regulares e inclua atividade física para favorecer o fluxo biliar."
        )
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
        "alimentacao": (
            "Padrão: frutas e legumes em destaque; evitar excitantes.\n\n"
            "- Baseie a dieta em frutas, verduras, legumes e cereais integrais; inclua fontes leves de proteína (ovos, peixe, leguminosas) conforme tolerância.\n"
            "- Evite cafeína, bebidas energéticas e excesso de açúcar, que aumentam ansiedade e prejudicam o sono.\n"
            "- Considere alimentos ricos em cálcio e magnésio (verduras escuras, sementes) para suporte nervoso; ajuste proteínas conforme orientação profissional.\n"
            "- Priorize refeições regulares e alimentos que favoreçam sono e recuperação emocional."
        )
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
        "alimentacao": (
            "Padrão: alimentação mista com tendência a carne; moderação em álcool e excessos.\n\n"
            "- Prefira refeições equilibradas e regulares; inclua proteínas (carne magra, aves, peixes) com moderação e muitas verduras.\n"
            "- Evite excessos alimentares e comportamentos dependentes (tabagismo, consumo compulsivo); reduza álcool ou limite a vinho nas refeições com moderação.\n"
            "- Mantenha hidratação e controle porções para evitar letargia; pratique atividade física leve para estimular metabolismo."
        )
    }
}

# --- UI: instruções e formulário com expanders por grupo ---
st.markdown("Clique em **Iniciar** para abrir o questionário. Use valores de 0 (nunca) a 10 (sempre).")
if "started" not in st.session_state:
    st.session_state.started = False

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Iniciar / Reiniciar"):
        st.session_state.started = True
        st.session_state.responses = {}

if not st.session_state.started:
    st.info("Pressione Iniciar para responder o autoestudo.")
    st.stop()

# inicializar respostas se necessário
if "responses" not in st.session_state:
    st.session_state.responses = {}

# renderizar cada grupo dentro de um expander separado
for group, qs in QUESTIONS.items():
    exp_label = group.replace("_", " ")
    with st.expander(exp_label, expanded=True):
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

    # Preparar dados para gráfico de pizza
    labels = [k.replace("_", " ") for k in scores.keys()]
    values = [v for v in scores.values()]
    colors = ["#FFD166", "#EF476F", "#118AB2", "#06D6A0"]  # cores sugeridas para cada temperamento

    # Plot pie chart com matplotlib
    fig, ax = plt.subplots(figsize=(6, 6))
    # evitar fatias zero invisíveis: se todas zero, mostrar mensagem
    if sum(values) == 0:
        ax.text(0.5, 0.5, "Sem respostas (todas as pontuações são 0)", ha="center", va="center")
        ax.axis("off")
    else:
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 0 else "",
            startangle=90,
            colors=colors[:len(values)],
            wedgeprops=dict(width=0.5, edgecolor="w")
        )
        ax.axis("equal")
        # legenda ao lado
        legend_labels = [f"{lab}: {val} pts" for lab, val in zip(labels, values)]
        ax.legend(wedges, legend_labels, title="Temperamentos", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    st.subheader("Distribuição dos temperamentos (pizza)")
    st.pyplot(fig)

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

    # exibir recomendações em expanders separados para melhor leitura
    st.subheader("Interpretação e recomendações")
    def show_rec_expander(key):
        rec = RECOMMENDATIONS[key]
        with st.expander(f"{rec['nome']} — Recomendações", expanded=(key == dominant_key)):
            st.markdown(f"**Resumo:** {rec['resumo']}")
            st.markdown(f"**Pedras sugeridas:** {', '.join(rec['pedras'])}")
            st.markdown(f"**Cromoterapia (cor):** {rec['cor']}")
            st.markdown(f"**Aromaterapia (óleo):** {rec['oleo']}")
            st.markdown("**Dicas práticas:**")
            for d in rec["dicas"]:
                st.write(f"- {d}")
            st.markdown("**Alimentação (sugestão detalhada):**")
            st.markdown(rec["alimentacao"].replace("\n", "  \n"))

    # mostrar dominante e secundário em expanders
    show_rec_expander(dominant_key)
    show_rec_expander(secondary_key)

    # salvar resultado em session_state (opcional)
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scores": scores,
        "dominant": RECOMMENDATIONS[dominant_key]["nome"],
        "dominant_score": dominant_val,
        "secondary": RECOMMENDATIONS[secondary_key]["nome"],
        "secondary_score": secondary_val
    }
    st.session_state.last_result = result

    st.success("Autoestudo concluído. Se desejar, repita em duas semanas para comparar resultados.")