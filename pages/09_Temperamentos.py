# 09_Temperamentos.py
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="09 — Temperamentos", layout="wide")
st.title("Temperamentos 🌑🌔🌕🌖")

st.markdown("""
Este autoestudo soma as características dos quatro grupos (A, B, C, D) e indica o temperamento dominante e secundário.  
**O que são os temperamentos:** trata‑se de um modelo clássico que descreve padrões estáveis de comportamento, emoção e energia corporal. Cada temperamento reúne um conjunto de tendências — maneiras preferidas de reagir, de se relacionar e de gerir a própria vitalidade — que ajudam a entender por que certas rotinas, alimentos e práticas funcionam melhor para algumas pessoas do que para outras.  

- **Sanguíneo:** geralmente extrovertido, sociável e entusiasta; busca estímulos e variedade.  
- **Bilioso (colérico):** orientado à ação, decidido e ambicioso; tende a respostas rápidas e foco em resultados.  
- **Melancólico (nervoso):** introspectivo, detalhista e sensível; propenso à reflexão profunda e à cautela.  
- **Linfático (fleumático):** calmo, estável e rotineiro; prefere previsibilidade e conforto.

Este teste não rotula nem limita: serve como ferramenta prática para identificar tendências predominantes e sugerir ajustes simples (alimentação, sono, exercícios, práticas de relaxamento) que favoreçam equilíbrio. Responda com honestidade e use o resultado como ponto de partida para observar padrões ao longo do tempo.
""")

# -------------------------
# Perguntas por grupo
# -------------------------
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
        "possui olhar distante, um pouco tristonho, e às vezes voltado para baixo",
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

# -------------------------
# Recomendações por temperamento (alimentação incluída)
# -------------------------
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

# -------------------------
# UI: iniciar / formulário
# -------------------------
st.markdown("Clique em **Iniciar** para abrir o questionário. Use valores de 0 (nunca) a 10 (sempre).")

if "started" not in st.session_state:
    st.session_state.started = False

col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Iniciar"):
        st.session_state.started = True
        st.session_state.responses = {}

if not st.session_state.started:
    st.info("Pressione Iniciar para responder o autoestudo.")
    st.stop()

if "responses" not in st.session_state:
    st.session_state.responses = {}

# renderizar cada grupo dentro de um expander separado
for group, qs in QUESTIONS.items():
    exp_label = group.replace("_", " ")
    with st.expander(exp_label, expanded=True):
        cols = st.columns(2)
        for i, q in enumerate(qs):
            key = f"{group}_{i}"
            default = st.session_state.responses.get(key, 0)
            val = cols[i % 2].slider(q, 0, 10, value=default, key=key)
            st.session_state.responses[key] = val

# -------------------------
# Botão calcular e lógica de resultado
# -------------------------
if st.button("Calcular resultado"):
    # construir scores a partir das respostas
    scores = {}
    for group in QUESTIONS:
        vals = [st.session_state.responses.get(f"{group}_{i}", 0) for i in range(len(QUESTIONS[group]))]
        scores[group] = round(sum(vals), 2)  # soma 0-100

    # exibir gráfico de pizza com Plotly
    labels = [k.replace("_", " ") for k in scores.keys()]
    values = [v for v in scores.values()]
    color_map = {
        "A Sanguineo": "#FFD166",
        "B Bilioso": "#EF476F",
        "C Nervoso": "#118AB2",
        "D Linfatico": "#06D6A0"
    }
    colors = [color_map.get(lbl, None) for lbl in labels]

    if sum(values) == 0:
        st.warning("Sem respostas: todas as pontuações são 0. Preencha o questionário para ver o gráfico.")
    else:
        df_plot = pd.DataFrame({"Temperamento": labels, "Pontuação": values})
        fig = px.pie(df_plot, names="Temperamento", values="Pontuação",
                     color="Temperamento", color_discrete_sequence=colors,
                     hole=0.45)
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), legend=dict(orientation="v", x=1.02, y=0.5))
        st.subheader("Distribuição dos temperamentos")
        st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Determinar dominante e secundário com regra de 35%
    # -------------------------
    THRESHOLD_SECONDARY = 35.0  # mínimo para considerar secundário

    # ordenar
    try:
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    except Exception as e:
        st.error(f"Erro ao ordenar pontuações: {e}")
        st.stop()

    if not sorted_scores:
        st.error("Nenhuma pontuação válida encontrada.")
        st.stop()

    dominant_key, dominant_val = sorted_scores[0]
    secondary_key, secondary_val = (None, 0.0)
    if len(sorted_scores) > 1:
        secondary_key, secondary_val = sorted_scores[1]

    # utilitário para obter recomendação com fallback
    def get_rec_by_key(key):
        if not key:
            return None
        rec = RECOMMENDATIONS.get(key)
        if rec:
            return rec
        alt = key.replace(" ", "_")
        rec = RECOMMENDATIONS.get(alt)
        if rec:
            return rec
        # última tentativa: comparar sem underscores
        alt2 = key.replace("_", " ").lower()
        for k, v in RECOMMENDATIONS.items():
            if k.replace("_", " ").lower() == alt2:
                return v
        return None

    dominant_rec = get_rec_by_key(dominant_key)
    secondary_rec = get_rec_by_key(secondary_key) if secondary_key else None

    # exibir dominante sempre
    dominant_label = dominant_rec["nome"] if dominant_rec else dominant_key.replace("_", " ")
    st.markdown("---")
    st.markdown(f"**Temperamento dominante:** **{dominant_label}** — {dominant_val} pontos")

    # decidir se mostramos secundário
    show_secondary = False
    if secondary_key and isinstance(secondary_val, (int, float)):
        if secondary_val >= THRESHOLD_SECONDARY and secondary_val > 0:
            show_secondary = True

    if show_secondary:
        secondary_label = secondary_rec["nome"] if secondary_rec else secondary_key.replace("_", " ")
        st.markdown(f"**Temperamento secundário:** **{secondary_label}** — {secondary_val} pontos")
        if abs(dominant_val - secondary_val) <= 8:
            st.warning("Pontuações próximas: é possível que você tenha um temperamento misto. Considere ler as descrições de ambos.")
    else:
        st.info("Nenhum temperamento secundário significativo detectado.")

    # -------------------------
    # Exibir recomendações em expanders
    # -------------------------
    st.subheader("Interpretação e Recomendações")

    def show_rec_expander(rec, key, expanded=False):
        if not rec:
            with st.expander(f"{key.replace('_',' ')} — Recomendações (não encontradas)", expanded=False):
                st.write("Recomendações não disponíveis para esta chave. Verifique a consistência das chaves em QUESTIONS e RECOMMENDATIONS.")
                st.write("Chave detectada:", key)
            return
        with st.expander(f"{rec['nome']} — Recomendações", expanded=expanded):
            st.markdown(f"**Resumo:** {rec['resumo']}")
            st.markdown(f"**Pedras sugeridas:** {', '.join(rec['pedras'])}")
            st.markdown(f"**Cromoterapia (cor):** {rec['cor']}")
            st.markdown(f"**Aromaterapia (óleo):** {rec['oleo']}")
            st.markdown("**Dicas práticas:**")
            for d in rec["dicas"]:
                st.write(f"- {d}")
            st.markdown("**Alimentação (sugestão detalhada):**")
            st.markdown(rec["alimentacao"].replace("\n", "  \n"))

    # dominante (expandido por padrão)
    show_rec_expander(dominant_rec, dominant_key, expanded=True)
    # secundário condicional
    if show_secondary:
        show_rec_expander(secondary_rec, secondary_key, expanded=False)

    # -------------------------
    # Salvar resultado em session_state e oferecer exportação
    # -------------------------
    dominant_rec_serializable = None
    secondary_rec_serializable = None

    if dominant_rec:
        dominant_rec_serializable = {
            "key": dominant_key,
            "nome": dominant_rec.get("nome"),
            "resumo": dominant_rec.get("resumo"),
            "pedras": dominant_rec.get("pedras"),
            "cor": dominant_rec.get("cor"),
            "oleo": dominant_rec.get("oleo"),
            "dicas": dominant_rec.get("dicas"),
            "alimentacao": dominant_rec.get("alimentacao"),
        }

    if show_secondary and secondary_rec:
        secondary_rec_serializable = {
            "key": secondary_key,
            "nome": secondary_rec.get("nome"),
            "resumo": secondary_rec.get("resumo"),
            "pedras": secondary_rec.get("pedras"),
            "cor": secondary_rec.get("cor"),
            "oleo": secondary_rec.get("oleo"),
            "dicas": secondary_rec.get("dicas"),
            "alimentacao": secondary_rec.get("alimentacao"),
        }

    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "scores": scores,
        "dominant": dominant_label,
        "dominant_score": dominant_val,
        "dominant_rec": dominant_rec_serializable,
    }
    if show_secondary:
        result["secondary"] = secondary_rec_serializable["nome"] if secondary_rec_serializable else secondary_key.replace("_", " ")
        result["secondary_score"] = secondary_val
        result["secondary_rec"] = secondary_rec_serializable

    st.session_state.last_result = result

    st.markdown("---")
    
    st.success("Autoestudo concluído. Se desejar, repita em duas semanas para comparar resultados.")

# --- construção do PDF ---

from io import BytesIO
from datetime import datetime as _dt

def _create_pdf_bytes_reportlab(result: dict) -> bytes:
    """
    Gera PDF em memória usando reportlab. Retorna bytes do PDF.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception as e:
        raise ImportError("reportlab não disponível") from e

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Cabeçalho
    title_style = styles["Title"]
    normal = styles["Normal"]
    heading = styles["Heading3"]

    story.append(Paragraph("Autoestudo — Temperamentos", title_style))
    story.append(Spacer(1, 8))
    ts = result.get("timestamp") or _dt.utcnow().isoformat()
    story.append(Paragraph(f"Gerado em: {ts}", normal))
    story.append(Spacer(1, 12))

    # Scores
    scores = result.get("scores", {})
    if scores:
        data = [["Temperamento", "Pontuação"]]
        for k, v in scores.items():
            label = k.replace("_", " ")
            data.append([label, f"{v}"])
        table = Table(data, hAlign="LEFT", colWidths=[320, 80])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f2f2")),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

    # Dominante / secundário
    dominant = result.get("dominant", "-")
    dominant_score = result.get("dominant_score", "-")
    story.append(Paragraph(f"<b>Temperamento dominante:</b> {dominant} — {dominant_score}", heading))
    if result.get("secondary"):
        story.append(Paragraph(f"<b>Temperamento secundário:</b> {result.get('secondary')} — {result.get('secondary_score')}", normal))
    story.append(Spacer(1, 12))

    # Recomendações (tentar recuperar do dicionário RECOMMENDATIONS se disponível)
    try:
        rec_key = (result.get("dominant") or "").replace(" ", "_")
        rec = RECOMMENDATIONS.get(rec_key)
    except Exception:
        rec = None

    if rec:
        story.append(Paragraph("Resumo e recomendações", styles["Heading4"]))
        story.append(Spacer(1, 6))
        # resumo
        story.append(Paragraph(rec.get("resumo", ""), normal))
        story.append(Spacer(1, 6))
        # pedras, cor, óleo (novos campos)
        pedras = ", ".join(rec.get("pedras", []))
        cor = rec.get("cor", "")
        oleo = rec.get("oleo", "")
        if pedras:
            story.append(Paragraph(f"<b>Pedras sugeridas:</b> {pedras}", normal))
            story.append(Spacer(1, 4))
        if cor:
            story.append(Paragraph(f"<b>Cromoterapia (cor):</b> {cor}", normal))
            story.append(Spacer(1, 4))
        if oleo:
            story.append(Paragraph(f"<b>Aromaterapia (óleo):</b> {oleo}", normal))
            story.append(Spacer(1, 6))

        # dicas práticas
        story.append(Paragraph("Dicas práticas:", styles["Normal"]))
        for d in rec.get("dicas", []):
            story.append(Paragraph(f"- {d}", normal))
        story.append(Spacer(1, 8))

        # alimentação (resumo)
        story.append(Paragraph("Alimentação (resumo):", styles["Normal"]))
        # reportlab Paragraph aceita HTML limitado; substituir quebras de linha por <br/> já feito antes
        alimentacao_text = rec.get("alimentacao", "").replace("\n", "<br/>")
        story.append(Paragraph(alimentacao_text, normal))
        story.append(Spacer(1, 12))

    # Incluir recomendações do secundário, se houver
    if result.get("secondary"):
        try:
            sec_key = (result.get("secondary") or "").replace(" ", "_")
            sec_rec = RECOMMENDATIONS.get(sec_key)
        except Exception:
            sec_rec = None

        if sec_rec:
            story.append(Paragraph("Temperamento secundário — Recomendações", styles["Heading4"]))
            story.append(Spacer(1, 6))
            story.append(Paragraph(sec_rec.get("resumo", ""), normal))
            story.append(Spacer(1, 6))
            pedras = ", ".join(sec_rec.get("pedras", []))
            if pedras:
                story.append(Paragraph(f"<b>Pedras sugeridas:</b> {pedras}", normal))
                story.append(Spacer(1, 4))
            cor = sec_rec.get("cor", "")
            if cor:
                story.append(Paragraph(f"<b>Cromoterapia (cor):</b> {cor}", normal))
                story.append(Spacer(1, 4))
            oleo = sec_rec.get("oleo", "")
            if oleo:
                story.append(Paragraph(f"<b>Aromaterapia (óleo):</b> {oleo}", normal))
                story.append(Spacer(1, 6))
            story.append(Paragraph("Dicas práticas:", styles["Normal"]))
            for d in sec_rec.get("dicas", []):
                story.append(Paragraph(f"- {d}", normal))
            story.append(Spacer(1, 8))
            story.append(Paragraph("Alimentação (resumo):", styles["Normal"]))
            story.append(Paragraph(sec_rec.get("alimentacao", "").replace("\n", "<br/>"), normal))
            story.append(Spacer(1, 12))

    # Observações finais
    story.append(Paragraph("Observações:", styles["Heading4"]))
    story.append(Paragraph("Este relatório resume as pontuações do autoestudo. Use-o como referência e não como diagnóstico.", normal))
    story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

# Função wrapper que tenta reportlab e informa se não estiver instalado
def create_pdf_bytes(result: dict) -> bytes:
    try:
        return _create_pdf_bytes_reportlab(result)
    except ImportError:
        # fallback simples: gerar um PDF mínimo via texto plano com reportlab ausente não é trivial;
        # informar ao usuário que a dependência é necessária.
        raise

# --- Botões de download (colocar após a criação de st.session_state["last_result"]) ---
if "last_result" in st.session_state:
    try:
        pdf_bytes = create_pdf_bytes(st.session_state["last_result"])
        st.download_button(
            label="Baixar resultado em PDF",
            data=pdf_bytes,
            file_name="temperamentos_resultado.pdf",
            mime="application/pdf"
        )
    except ImportError:
        st.error("Para habilitar exportação em PDF instale a dependência 'reportlab' no ambiente (pip install reportlab).")
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {e}")