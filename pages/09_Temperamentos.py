# 09_Temperamentos.py (refatorado)
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# Gerador de IA (ajuste o import conforme sua estrutura)
from etheria.services.generator_service import generate_ai_text_from_chart
from services.temperamento_prompt import generate_diagnostic_report

# Configuração da página
st.set_page_config(page_title="09 — Temperamentos", layout="wide")
st.title("Temperamentos 🌑🌔🌕🌖")

# -------------------------
# Constantes e dados
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
# Utilitários
# -------------------------
def get_rec_by_key(key: str):
    if not key:
        return None
    rec = RECOMMENDATIONS.get(key)
    if rec:
        return rec
    alt = key.replace(" ", "_")
    rec = RECOMMENDATIONS.get(alt)
    if rec:
        return rec
    alt2 = key.replace("_", " ").lower()
    for k, v in RECOMMENDATIONS.items():
        if k.replace("_", " ").lower() == alt2:
            return v
    return None

# -------------------------
# Estado inicial
# -------------------------
if "started" not in st.session_state:
    st.session_state.started = False
if "responses" not in st.session_state:
    st.session_state.responses = {}
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# -------------------------
# UI: iniciar / formulário
# -------------------------
st.markdown("Clique em **Iniciar** para abrir o questionário. Use valores de 0 (nunca) a 10 (sempre).")
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("Iniciar / Reiniciar"):
        st.session_state.started = True
        st.session_state.responses = {}

if not st.session_state.started:
    st.info("Pressione Iniciar para responder o autoestudo.")
    st.stop()

# renderizar perguntas
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
# Calcular resultado
# -------------------------
if st.button("Calcular resultado"):
    scores = {}
    for group in QUESTIONS:
        vals = [st.session_state.responses.get(f"{group}_{i}", 0) for i in range(len(QUESTIONS[group]))]
        scores[group] = round(sum(vals), 2)

    # gráfico
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

    # determinar dominante e secundário
    THRESHOLD_SECONDARY = 35.0
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    dominant_key, dominant_val = sorted_scores[0]
    secondary_key, secondary_val = (None, 0.0)
    if len(sorted_scores) > 1:
        secondary_key, secondary_val = sorted_scores[1]

    dominant_rec = get_rec_by_key(dominant_key)
    secondary_rec = get_rec_by_key(secondary_key) if secondary_key else None

    dominant_label = dominant_rec["nome"] if dominant_rec else dominant_key.replace("_", " ")

    st.markdown("---")
    st.markdown(f"**Temperamento dominante:** **{dominant_label}** — {dominant_val} pontos")

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

    # mostrar recomendações na UI
    st.subheader("Interpretação e Recomendações")
    def show_rec_expander(rec, key, expanded=False):
        if not rec:
            with st.expander(f"{key.replace('_',' ')} — Recomendações (não encontradas)", expanded=False):
                st.write("Recomendações não disponíveis para esta chave.")
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

    show_rec_expander(dominant_rec, dominant_key, expanded=True)
    if show_secondary:
        show_rec_expander(secondary_rec, secondary_key, expanded=False)

    # serializar recomendações no result
    def _serializable_rec(rec, key):
        if not rec:
            return None
        return {
            "key": key,
            "nome": rec.get("nome"),
            "resumo": rec.get("resumo"),
            "pedras": rec.get("pedras"),
            "cor": rec.get("cor"),
            "oleo": rec.get("oleo"),
            "dicas": rec.get("dicas"),
            "alimentacao": rec.get("alimentacao"),
        }

    dominant_rec_serializable = _serializable_rec(dominant_rec, dominant_key)
    secondary_rec_serializable = _serializable_rec(secondary_rec, secondary_key) if show_secondary else None

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

# -------------------------
# PDF generation helpers
# -------------------------
from io import BytesIO
from datetime import datetime as _dt

def _create_pdf_bytes_reportlab(result: dict) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    except Exception as e:
        raise ImportError("reportlab não disponível") from e

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal = styles["Normal"]
    heading = styles["Heading3"]

    story = []
    story.append(Paragraph("Autoestudo — Temperamentos", title_style))
    story.append(Spacer(1, 8))
    ts = result.get("timestamp") or _dt.utcnow().isoformat()
    story.append(Paragraph(f"Gerado em: {ts}", normal))
    story.append(Spacer(1, 12))

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

    dominant = result.get("dominant", "-")
    dominant_score = result.get("dominant_score", "-")
    story.append(Paragraph(f"<b>Temperamento dominante:</b> {dominant} — {dominant_score}", heading))
    if result.get("secondary"):
        story.append(Paragraph(f"<b>Temperamento secundário:</b> {result.get('secondary')} — {result.get('secondary_score')}", normal))
    story.append(Spacer(1, 12))

    # recomendações serializadas
    def _append_rec(rec_obj, title=None):
        if not rec_obj:
            return
        if title:
            story.append(Paragraph(title, styles["Heading4"]))
            story.append(Spacer(1, 6))
        resumo = rec_obj.get("resumo", "")
        if resumo:
            story.append(Paragraph(resumo, normal))
            story.append(Spacer(1, 6))
        pedras = rec_obj.get("pedras") or []
        if pedras:
            story.append(Paragraph(f"<b>Pedras sugeridas:</b> {', '.join(pedras)}", normal))
            story.append(Spacer(1, 4))
        cor = rec_obj.get("cor", "")
        if cor:
            story.append(Paragraph(f"<b>Cromoterapia (cor):</b> {cor}", normal))
            story.append(Spacer(1, 4))
        oleo = rec_obj.get("oleo", "")
        if oleo:
            story.append(Paragraph(f"<b>Aromaterapia (óleo):</b> {oleo}", normal))
            story.append(Spacer(1, 6))
        dicas = rec_obj.get("dicas") or []
        if dicas:
            story.append(Paragraph("Dicas práticas:", styles["Normal"]))
            for d in dicas:
                story.append(Paragraph(f"- {d}", normal))
            story.append(Spacer(1, 6))
        alimentacao = rec_obj.get("alimentacao", "") or ""
        if alimentacao.strip():
            story.append(Paragraph("Alimentação (resumo):", styles["Normal"]))
            paras = [p.strip() for p in alimentacao.split("\n\n") if p.strip()]
            if not paras:
                paras = [p.strip() for p in alimentacao.split("\n") if p.strip()]
            for p in paras:
                story.append(Paragraph(p.replace("\n", "<br/>"), normal))
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 6))

    dominant_rec = result.get("dominant_rec") or {}
    _append_rec(dominant_rec, title="Resumo e recomendações (dominante)")

    secondary_rec = result.get("secondary_rec") or {}
    if secondary_rec:
        _append_rec(secondary_rec, title="Resumo e recomendações (secundário)")

    story.append(Paragraph("Observações:", styles["Heading4"]))
    story.append(Paragraph("Este relatório resume as pontuações do autoestudo. Use-o como referência e não como diagnóstico.", normal))
    story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

def create_pdf_bytes_with_model_text(result: dict) -> bytes:
    """
    Gera PDF incluindo model_report_text quando presente.
    """
    model_text = (result.get("model_report_text") or "").strip()
    # se não houver model_text, usar create_pdf_bytes padrão
    if not model_text:
        try:
            return _create_pdf_bytes_reportlab(result)
        except Exception:
            pass

    # gerar PDF que inclui model_text
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
        from io import BytesIO
    except Exception as e:
        raise ImportError("reportlab não disponível") from e

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    title_style = styles["Title"]
    heading = styles["Heading3"]

    story = []
    story.append(Paragraph("Introdução ao Perfil Bioenergético e Distribuição de Temperamentos", title_style))
    story.append(Spacer(1, 8))
    ts = result.get("timestamp") or _dt.utcnow().isoformat()
    story.append(Paragraph(f"Gerado em: {ts}", normal))
    story.append(Spacer(1, 12))

    # tabela de scores
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

    dominant = result.get("dominant", "-")
    dominant_score = result.get("dominant_score", "-")
    story.append(Paragraph(f"<b>Temperamento dominante:</b> {dominant} — {dominant_score}", heading))
    if result.get("secondary"):
        story.append(Paragraph(f"<b>Temperamento secundário:</b> {result.get('secondary')} — {result.get('secondary_score')}", normal))
    story.append(Spacer(1, 12))

    # recomendações serializadas
    dominant_rec = result.get("dominant_rec") or {}
    secondary_rec = result.get("secondary_rec") or {}
    def _append_rec_simple(rec_obj, title=None):
        if not rec_obj:
            return
        if title:
            story.append(Paragraph(title, styles["Heading4"]))
            story.append(Spacer(1, 6))
        resumo = rec_obj.get("resumo", "")
        if resumo:
            story.append(Paragraph(resumo, normal))
            story.append(Spacer(1, 6))
        pedras = rec_obj.get("pedras") or []
        if pedras:
            story.append(Paragraph(f"<b>Pedras sugeridas:</b> {', '.join(pedras)}", normal))
            story.append(Spacer(1, 4))
        cor = rec_obj.get("cor", "")
        if cor:
            story.append(Paragraph(f"<b>Cromoterapia (cor):</b> {cor}", normal))
            story.append(Spacer(1, 4))
        oleo = rec_obj.get("oleo", "")
        if oleo:
            story.append(Paragraph(f"<b>Aromaterapia (óleo):</b> {oleo}", normal))
            story.append(Spacer(1, 6))
        dicas = rec_obj.get("dicas") or []
        if dicas:
            story.append(Paragraph("Dicas práticas:", styles["Normal"]))
            for d in dicas:
                story.append(Paragraph(f"- {d}", normal))
            story.append(Spacer(1, 6))
        alimentacao = rec_obj.get("alimentacao", "") or ""
        if alimentacao.strip():
            story.append(Paragraph("Alimentação (resumo):", styles["Normal"]))
            paras = [p.strip() for p in alimentacao.split("\n\n") if p.strip()]
            if not paras:
                paras = [p.strip() for p in alimentacao.split("\n") if p.strip()]
            for p in paras:
                story.append(Paragraph(p.replace("\n", "<br/>"), normal))
                story.append(Spacer(1, 4))
            story.append(Spacer(1, 6))

    _append_rec_simple(dominant_rec, title="Resumo e recomendações (dominante)")
    if secondary_rec:
        _append_rec_simple(secondary_rec, title="Resumo e recomendações (secundário)")

    # inserir texto do modelo em nova página
    story.append(PageBreak())
    story.append(Paragraph("Relatório diagnóstico (modelo)", styles["Heading4"]))
    story.append(Spacer(1, 6))
    paras = [p.strip() for p in model_text.split("\n\n") if p.strip()]
    if not paras:
        paras = [p.strip() for p in model_text.split("\n") if p.strip()]
    for p in paras:
        story.append(Paragraph(p.replace("\n", "<br/>"), normal))
        story.append(Spacer(1, 6))

    story.append(Paragraph("Observações:", styles["Heading4"]))
    story.append(Paragraph("Este relatório não é um diagnóstico médico. Consulte um profissional de saúde antes de seguir recomendações clínicas.", normal))
    story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

# -------------------------
# Gerar relatório diagnóstico via IA
# -------------------------
st.markdown("---")
st.subheader("Gerar relatório diagnóstico com IA Etheria")
st.caption("Aviso: este relatório não é um diagnóstico médico. Consulte um profissional de saúde antes de seguir recomendações clínicas.")

def _generator_wrapper(chart_summary, prompt):
    """
    Wrapper que garante instrução no chart_summary e fallback para btime.
    Ajuste se generate_ai_text_from_chart aceitar (chart_summary, prompt) ou apenas chart_summary.
    """
    cs = dict(chart_summary)
    cs["instruction"] = prompt
    cs.setdefault("btime", "00:00")
    # Tentar chamar com duas assinaturas possíveis
    try:
        return generate_ai_text_from_chart(cs, prompt)
    except TypeError:
        return generate_ai_text_from_chart(cs)

if st.button("Gerar relatório diagnóstico"):
    if not st.session_state.last_result:
        st.warning("Nenhum resultado disponível. Execute o autoestudo primeiro.")
    else:
        result = st.session_state.last_result
        # chamar o serviço de geração com wrapper
        try:
            out = generate_diagnostic_report(result, generator=_generator_wrapper)
        except Exception as e:
            st.error("Erro ao chamar o serviço de geração.")
            st.exception(e)
            out = None

        if out:
            # debug: mostrar prompt (limitado)
            with st.expander("Prompt enviado ao modelo (debug)", expanded=False):
                st.code(out.get("prompt", "")[:4000])

            model_text = out.get("model_text")
            if not model_text:
                st.error("O modelo não retornou texto. Verifique logs do serviço.")
                # mostrar raw result para debug
                st.write(out.get("raw_model_result"))
            else:
                # renderizar e salvar
                st.markdown("### Relatório diagnóstico (modelo)")
                st.write(model_text)

                # anexar ao result e persistir
                result_for_pdf = dict(result)
                result_for_pdf["model_report_text"] = model_text
                st.session_state.last_result = result_for_pdf

                # gerar PDF com texto do modelo
                try:
                    pdf_bytes = create_pdf_bytes_with_model_text(result_for_pdf)
                    st.download_button(
                        label="Baixar relatório diagnóstico em PDF",
                        data=pdf_bytes,
                        file_name="temperamentos_diagnostico.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error("Erro ao gerar PDF do relatório.")
                    st.exception(e)

# -------------------------
# Exportar resultado simples (PDF/Parquet/JSON)
# -------------------------
if st.session_state.last_result:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        try:
            pdf_bytes = create_pdf_bytes_with_model_text(st.session_state.last_result)
            st.download_button("Baixar relatório completo (PDF)", data=pdf_bytes, file_name="temperamentos_resultado.pdf", mime="application/pdf")
        except Exception:
            st.info("PDF não disponível (reportlab ausente ou erro).")
    with col_b:
        st.download_button("Baixar resultado (JSON)", data=pd.io.json.dumps(st.session_state.last_result, ensure_ascii=False, indent=2), file_name="temperamentos_resultado.json", mime="application/json")
    with col_c:
        # salvar Parquet simples com scores
        try:
            df_scores = pd.DataFrame(list(st.session_state.last_result["scores"].items()), columns=["Temperamento", "Pontuação"])
            buf = BytesIO()
            df_scores.to_parquet(buf, index=False)
            st.download_button("Baixar scores (Parquet)", data=buf.getvalue(), file_name="temperamentos_scores.parquet", mime="application/octet-stream")
        except Exception:
            st.info("Export Parquet indisponível.")

# Fim do arquivo