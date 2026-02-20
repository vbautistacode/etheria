# pages/11_Biohacking.py
import streamlit as st
import io
from datetime import datetime
from typing import List

st.set_page_config(page_title="Biohacking", layout="wide")
st.title("Biohacking — 🧬")

st.markdown(
    """
**O que é Biohacking**

É o conjunto de práticas, ferramentas e experimentos pessoais usados para **otimizar saúde, desempenho cognitivo e longevidade**, como sono, alimentação, rastreio com wearables.  
Priorize sempre intervenções não invasivas e baseadas em evidência; intervenções médicas, hormônios, peptídeos e procedimentos invasivos exigem supervisão clínica.
"""
)

st.markdown(
    "> O corpo alterna o fluxo para permitir que os tecidos de uma narina se recuperem enquanto a outra trabalha.\n\n"
    "> A respiração é a única função do sistema nervoso autônomo que você controla conscientemente."
)

st.markdown("---")

# Consent (no sidebar)
consent = st.checkbox("Confirme: Este conteúdo é informativo e não substitui avaliação médica", value=False)
if not consent:
    st.warning("Marque a caixa de consentimento para desbloquear as ferramentas.")
    st.stop()

st.markdown(
    """
## Como usar esta página
1. Leia as descrições dos biohacks por objetivo.  
2. Marque os cards que deseja **ativar** (usar) agora.  
3. Clique em **Gerar PDF** para baixar um folheto imprimível com os biohacks selecionados.
"""
)

st.markdown("---")

# Core concepts (brief)
st.header("Conceitos centrais")
st.markdown(
    """
- **Hemisférios e integração:** o cérebro funciona como uma rede integrada; cada hemisfério tem especialidades (lógico/analítico vs. holístico/criativo), mas ambos trabalham juntos via corpo caloso.  
- **Narina e estado autonômico:** técnicas de respiração nasal podem modular o sistema nervoso (narina direita → alerta/simpático; narina esquerda → relaxamento/parassimpático).  
- **Nervo vago e termorregulação:** expiração longa e exposição ao frio ativam vias que reduzem o estresse e aumentam resiliência.
"""
)

st.markdown("### Guia de Biohacking e Neurofisiologia: Sinstese prática")

from pathlib import Path
from PIL import Image, UnidentifiedImageError

# path_local pode ser None ou "assets/mindmap.png"
path_local = "assets/mindmap.png"

# --- carregar arquivo local (compatível com seu código original) ---
uploaded = None
if path_local:
    try:
        with open(path_local, "rb") as f:
            uploaded = f.read()
    except Exception:
        uploaded = None

# --- abrir expander e exibir imagem se válida ---
with st.expander("Visualize o mapa mental (clique para expandir)"):
    if uploaded:
        try:
            # validação com Pillow
            img = Image.open(io.BytesIO(uploaded))
            img.verify()  # valida sem carregar totalmente
            # reabrir para exibir (verify() deixa o objeto inválido)
            img = Image.open(io.BytesIO(uploaded)).convert("RGBA")
            st.image(img, use_container_width=True)
        except UnidentifiedImageError:
            st.error("O arquivo local não é uma imagem válida ou está corrompido.")
        except Exception as e:
            st.error(f"Erro ao processar a imagem local: {e}")
    else:
        st.info("Nenhuma imagem local encontrada. Faça upload ou defina path_local.")
        # opcional: permitir upload direto dentro do expander
        uploaded_file = st.file_uploader("Envie um PNG/JPG (opcional)", type=["png", "jpg", "jpeg"])
        if uploaded_file is not None:
            try:
                data = uploaded_file.getvalue()
                img = Image.open(io.BytesIO(data)).convert("RGBA")
                st.image(img, use_container_width=True, caption="Mapa mental enviado (upload)")
            except UnidentifiedImageError:
                st.error("O arquivo enviado não é uma imagem válida.")
            except Exception as e:
                st.error(f"Erro ao processar o upload: {e}")

# Cards for objectives
st.header("Escolha um objetivo e ative os biohacks correspondentes")

cards = [
    {
        "id": "foco",
        "title": "Foco imediato",
        "summary": "Aumentar atenção e processamento analítico por curto período.",
        "items": [
            "Tape a narina esquerda e respire pela direita por 60-120 segundos.",
            "Olhar fixo em um ponto por 30-60 segundos (visão foveal).",
            "Suplemento opcional: cafeína + L-teanina (uso pontual).",
            "Técnica de SOS: tape a narina esquerda + respire vigorosamente por 60s."
        ]
    },
    {
        "id": "calma",
        "title": "Calma imediata",
        "summary": "Reduzir ansiedade e ativar o sistema parassimpático.",
        "items": [
            "Suspiro fisiológico: duas inspirações curtas pelo nariz + expiração longa pela boca (2-3 repetições).",
            "Expiração prolongada 1:2 (ex.: inspire 4s, expire 8s).",
            "Exposição breve ao frio (lavar o rosto com água gelada) para reflexo de mergulho.",
            "Técnica de SOS: suspiro fisiológico + movimentos oculares laterais."
        ]
    },
    {
        "id": "criatividade",
        "title": "Criatividade / insight",
        "summary": "Estimular pensamento holístico e geração de ideias.",
        "items": [
            "Caminhada ao ar livre com fluxo óptico (olhar para o horizonte) por 10-20 minutos.",
            "Respiração narina esquerda por 2 minutos para ativar relaxamento criativo.",
            "Relaxar o olhar (visão panorâmica) para integrar informações.",
            "Técnica de SOS: tape a narina direita e respire pela esquerda por 2 minutos."
        ]
    },
    {
        "id": "sono",
        "title": "Sono",
        "summary": "Melhorar início e qualidade do sono com higiene e rotinas.",
        "items": [
            "Exposição à luz solar matinal 5-10 minutos para regular o ciclo circadiano.",
            "Evitar luz azul 60-90 minutos antes de dormir; usar luzes quentes/alaranjadas.",
            "Banho morno 60 minutos antes de deitar para facilitar queda de temperatura corporal.",
            "Suplemento opcional: magnésio (bisglicinato/treonato) 1h antes, se indicado."
        ]
    }
]

# Render cards with checkboxes
selected_ids: List[str] = []
cols = st.columns(2)
for i, card in enumerate(cards):
    col = cols[i % 2]
    with col:
        st.subheader(card["title"])
        st.write(card["summary"])
        for it in card["items"]:
            st.markdown(f"- {it}")
        checked = st.checkbox(f"Ativar: {card['title']}", key=f"chk_{card['id']}")
        if checked:
            selected_ids.append(card["id"])
        st.markdown("---")

# Supplement quick guide card
st.header("Suplementação estratégica")
st.markdown(
    """
**Foco/energia:** L-Tirosina, cafeína (uso pontual), creatina.  
**Calma/sono:** Magnésio (bisglicinato/treonato), inositol, L-teanina.  
**Memória/fluxo:** Alfa-GPC (colina biodisponível).  

**Regras de segurança:** ciclagem; não combinar sem supervisão; cheque interações com medicações; consulte um profissional antes de iniciar.
"""
)

st.markdown("---")

# Risk assessment (simple)
st.header("Avaliação rápida de risco")
rq1 = st.radio("Tem condição médica crônica?", ["Não", "Sim"], key="rq1")
rq2 = st.radio("Usa medicação prescrita?", ["Não", "Sim"], key="rq2")
rq3 = st.radio("Tem acompanhamento médico disponível?", ["Sim", "Não"], key="rq3")

risk_score = 0
if rq1 == "Sim": risk_score += 2
if rq2 == "Sim": risk_score += 2
if rq3 == "Não": risk_score += 2

if risk_score >= 3:
    st.warning("Risco aumentado: consulte um profissional antes de intervenções médicas ou experimentos invasivos.")
else:
    st.info("Risco baixo-moderado: priorize intervenções não invasivas e monitoramento.")

st.markdown("---")

# PDF generation: compile selected cards into printable PDF
def _build_pdf_bytes(selected_cards: List[dict], title: str = "Biohacks Selecionados") -> bytes:
    """
    Gera PDF em memória com reportlab. Se reportlab não estiver disponível, gera texto simples em PDF via fallback.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
    except Exception:
        # fallback: simple text PDF using fpdf if available, else plain bytes of text
        try:
            from fpdf import FPDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(0, 10, title, ln=True)
            pdf.ln(4)
            for c in selected_cards:
                pdf.set_font("Arial", "B", 12)
                pdf.multi_cell(0, 8, c["title"])
                pdf.set_font("Arial", size=11)
                for it in c["items"]:
                    pdf.multi_cell(0, 7, f"- {it}")
                pdf.ln(4)
            return pdf.output(dest="S").encode("latin-1")
        except Exception:
            # last fallback: plain text bytes
            txt = title + "\n\n"
            for c in selected_cards:
                txt += c["title"] + "\n"
                for it in c["items"]:
                    txt += f"- {it}\n"
                txt += "\n"
            return txt.encode("utf-8")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    normal = styles["Normal"]
    heading = styles["Heading1"]
    story = []
    story.append(Paragraph(title, heading))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"Gerado em: {datetime.utcnow().isoformat()}", normal))
    story.append(Spacer(1, 12))

    for c in selected_cards:
        story.append(Paragraph(c["title"], styles["Heading3"]))
        story.append(Spacer(1, 6))
        story.append(Paragraph(c["summary"], normal))
        story.append(Spacer(1, 6))
        # items as bullet-like table
        for it in c["items"]:
            story.append(Paragraph(f"• {it}", normal))
            story.append(Spacer(1, 4))
        story.append(Spacer(1, 10))

    # safety note
    story.append(Spacer(1, 12))
    story.append(Paragraph("<b>Aviso:</b> Este folheto é informativo e não substitui avaliação médica. Consulte um profissional antes de intervenções médicas.", normal))

    doc.build(story)
    pdf_bytes = buf.getvalue()
    buf.close()
    return pdf_bytes

# Button to generate PDF
st.markdown("### Gerar folheto imprimível")
if st.button("Gerar PDF com biohacks selecionados"):
    # collect selected cards
    selected_cards = [c for c in cards if c["id"] in selected_ids]
    if not selected_cards:
        st.error("Nenhum biohack selecionado. Marque ao menos um card para gerar o PDF.")
    else:
        try:
            pdf_bytes = _build_pdf_bytes(selected_cards, title="Biohacks Selecionados")
            st.success("PDF gerado. Clique para baixar.")
            st.download_button("Baixar folheto (PDF)", data=pdf_bytes, file_name="biohacks_selecionados.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"Falha ao gerar PDF: {e}")

st.markdown("---")

# Education and cautions (from attached document)
st.header("Educação e mitos comuns")
st.markdown(
    """
- **Mito:** "Sou cérebro esquerdo ou direito." A verdade: usamos ambos; há inclinações, não rótulos fixos.  
- **Cuidado:** implantes, edição genética e auto-injeções são experimentais e de alto risco; evite fora de ambientes regulados.  
- **Privacidade:** dados de wearables e testes são sensíveis — verifique políticas de armazenamento e compartilhamento.
"""
)

st.markdown("---")

st.header("Próximos passos sugeridos")
st.markdown(
    """
1. Escolha 1-2 biohacks do folheto e teste por 1-2 semanas.  
2. Meça sono/energia/funcionalidade com um diário simples (papel ou app).  
3. Pare imediatamente se houver sinais adversos.  
4. Consulte um profissional antes de suplementos fortes, hormônios ou procedimentos invasivos.
"""
)