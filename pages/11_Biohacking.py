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

Biohacking é o conjunto de práticas, ferramentas e experimentos pessoais usados para **otimizar saúde, desempenho cognitivo e longevidade** — do simples (sono, alimentação, rastreio com wearables) ao experimental (peptídeos, implantes, biologia DIY).  
Priorize sempre intervenções não invasivas e baseadas em evidência; intervenções médicas, hormônios, peptídeos e procedimentos invasivos exigem supervisão clínica.
"""
)

st.markdown(
    "> O corpo alterna o fluxo para permitir que os tecidos de uma narina se recuperem enquanto a outra trabalha.\n\n"
    "> A respiração é a única função do sistema nervoso autônomo que você controla conscientemente."
)

st.markdown("---")

# Consent (no sidebar)
consent = st.checkbox("Li o aviso: este conteúdo é informativo e não substitui avaliação médica", value=False)
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

# Mermaid minimalista: sem controles e sem painel de detalhes
import streamlit as st
import json

st.markdown("### Mapa mental: Guia de Biohacking e Neurofisiologia (versão limpa)")

# (opcional) exibir imagem local se houver
path_local = None
if path_local:
    try:
        with open(path_local, "rb") as f:
            st.image(f.read(), use_container_width=True, caption="Mapa mental (arquivo local)")
    except Exception:
        pass

st.markdown("---")

# Mermaid source gerado a partir da sua estrutura
mermaid_source = """
mindmap
  root((Guia de Biohacking e Neurofisiologia))
    Hemisférios Cerebrais
      LadoEsquerdo[Lado Esquerdo (Analista)\\nLógica e Matemática; Linguagem e Fala; Análise de Detalhes; Controle Motor Direito]
      LadoDireito[Lado Direito (Sintetizador)\\nHolístico e Criativo; Processamento Espacial; Linguagem Não-Verbal; Controle Motor Esquerdo]
      CorpoCaloso[Corpo Caloso (Integração)]
    Autorregulação (Biohacks)
      RespiraçãoNasal[Respiração Nasal\\nNarina Direita: Alerta/Simpático; Narina Esquerda: Calma/Parassimpático; Ciclo Nasal Natural]
      ControleVisual[Controle Visual\\nVisão Foveal (Foco/Norepinefrina); Visão Panorâmica (Calma/Criatividade); Movimentos Sacádicos (Desarmar Stress)]
      Termorregulação[Termorregulação\\nFrio: Dopamina e Resiliência; Calor: Reparação Celular]
    Química Cerebral
      Neurotransmissores[Neurotransmissores\\nDopamina (Motivação); Noradrenalina (Alerta); GABA (Calma); Acetilcolina (Aprendizado)]
      Hormônios[Hormônios\\nCortisol (Energia/Stress); Melatonina (Sono); Ocitocina (Vínculo)]
    Suplementação e Nutrição
      Nootrópicos[Nootrópicos\\nCafeína + L-Teanina (Foco Limpo); Alfa-GPC (Acetilcolina); Magnésio (Relaxamento); L-Tirosina (Dopamina)]
      Vitaminas[Vitaminas\\nComplexo B (Energia); Vitamina D (Hormonal/Imunidade); Vitamina C (Antioxidante)]
    Protocolos de Limite
      Jejum[Jejum Intermitente (Autofagia)]
      Sono[Sono Polifásico]
      Suspiro[Suspiro Fisiológico (Alívio de Stress)]
"""

# Template HTML/JS minimalista (sem controles, sem painel)
mermaid_template = """
<div id="mermaid-wrapper" style="border:1px solid #eee; padding:8px; border-radius:6px; background:#fff;">
  <div id="mermaid-diagram" class="mermaid">
MERMAID_SOURCE_PLACEHOLDER
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>

<script>
  // Inicializa mermaid sem startOnLoad
  mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });

  (function renderMermaid() {
    try {
      const graphDefinition = `MERMAID_RAW_PLACEHOLDER`;
      const renderId = 'mmd_' + Math.random().toString(36).slice(2,9);
      mermaid.mermaidAPI.render(renderId, graphDefinition, function(svgCode) {
        const container = document.getElementById('mermaid-wrapper');
        container.innerHTML = svgCode;
        // pequeno atraso para garantir DOM
        setTimeout(initMinimalInteractivity, 60);
      });
    } catch (err) {
      console.error('Erro ao renderizar Mermaid:', err);
      document.getElementById('mermaid-wrapper').innerText = 'Falha ao renderizar diagrama.';
    }
  })();

  function initMinimalInteractivity() {
    const svg = document.querySelector('#mermaid-wrapper svg');
    if (!svg) {
      console.warn('SVG do Mermaid não encontrado.');
      return;
    }

    // inicializa pan/zoom (instância guardada em window._mz)
    try {
      window._mz = svgPanZoom(svg, {
        zoomEnabled: true,
        controlIconsEnabled: false,
        fit: true,
        center: true,
        minZoom: 0.5,
        maxZoom: 4
      });
    } catch(e) { console.warn('svg-pan-zoom falhou', e); }

    // selecionar nós de forma tolerante
    const nodeGroups = Array.from(svg.querySelectorAll('g[class*="node"], g.node, g[class*="cluster"], g[class*="label"]'));
    const nodes = nodeGroups.map(g => {
      const textEl = g.querySelector('text') || g.querySelector('tspan');
      const label = textEl ? textEl.textContent.trim() : null;
      return { group: g, label };
    }).filter(n => n.label);

    // destaque simples ao clicar (sem painel)
    function clearHighlights() {
      nodes.forEach(n => n.group.querySelectorAll('rect, ellipse, path').forEach(el => {
        el.style.stroke = '';
        el.style.strokeWidth = '';
        el.style.opacity = '';
      }));
    }

    nodes.forEach(n => {
      n.group.style.cursor = 'pointer';
      n.group.addEventListener('click', (ev) => {
        ev.stopPropagation();
        clearHighlights();
        n.group.querySelectorAll('rect, ellipse, path').forEach(el => {
          el.style.stroke = '#ff7f50';
          el.style.strokeWidth = '2px';
        });
      });
      // hover visual sutil
      n.group.addEventListener('mouseenter', () => {
        n.group.style.opacity = 0.9;
      });
      n.group.addEventListener('mouseleave', () => {
        n.group.style.opacity = 1;
      });
    });

    // clique no fundo limpa destaque
    svg.addEventListener('click', (ev) => {
      if (ev.target === svg) {
        clearHighlights();
      }
    });
  }
</script>

<style>
  #mermaid-wrapper { max-width: 100%; overflow: auto; padding: 8px 0; background:#fff; }
  #mermaid-wrapper svg { max-width: 100%; height: auto; display:block; }
</style>
"""

# Substituições seguras
mermaid_html = mermaid_template.replace("MERMAID_SOURCE_PLACEHOLDER", mermaid_source).replace("MERMAID_RAW_PLACEHOLDER", mermaid_source.replace("`", "\\`"))

# Render the component
st.components.v1.html(mermaid_html, height=640, scrolling=True)


st.markdown("---")

# Permitir ao usuário selecionar quais ramos incluir no PDF
st.markdown("#### Selecionar ramos para o folheto imprimível")
opts = {
    "Hemisférios": st.checkbox("Hemisférios Cerebrais", value=True),
    "Autorregulação": st.checkbox("Autorregulação (respiração, visual, termorregulação)", value=True),
    "Química": st.checkbox("Química Cerebral (neurotransmissores e hormônios)", value=True),
    "Suplementação": st.checkbox("Suplementação e Nutrição", value=True),
    "Protocolos": st.checkbox("Protocolos de Limite", value=True),
}

# Função simples para montar texto do folheto
def _build_text_for_pdf(opts):
    lines = []
    lines.append("Guia de Biohacking e Neurofisiologia")
    lines.append(f"Gerado em: {datetime.utcnow().isoformat()}")
    lines.append("")
    if opts["Hemisférios"]:
        lines.append("HEMISFÉRIOS CEREBRAIS")
        lines.append("- Esquerdo (Analítico): lógica, linguagem, análise de detalhes, controle motor direito.")
        lines.append("- Direito (Sintetizador): criatividade, processamento espacial, linguagem não-verbal, controle motor esquerdo.")
        lines.append("- Corpo caloso: integração entre hemisférios.")
        lines.append("")
    if opts["Autorregulação"]:
        lines.append("AUTORREGULAÇÃO")
        lines.append("- Respiração nasal: narina direita -> alerta/simpático; narina esquerda -> calma/parassimpático; ciclo nasal natural.")
        lines.append("- Controle visual: visão foveal para foco; visão panorâmica para criatividade; movimentos sacádicos reduzem stress.")
        lines.append("- Termorregulação: frio aumenta dopamina; calor favorece reparação celular.")
        lines.append("")
    if opts["Química"]:
        lines.append("QUÍMICA CEREBRAL")
        lines.append("- Neurotransmissores: Dopamina (motivação), Noradrenalina (alerta), GABA (calma), Acetilcolina (aprendizado).")
        lines.append("- Hormônios: Cortisol (stress/energia), Melatonina (sono), Ocitocina (vínculo).")
        lines.append("")
    if opts["Suplementação"]:
        lines.append("SUPLEMENTAÇÃO E NUTRIÇÃO")
        lines.append("- Nootrópicos: Cafeína+L-Teanina, Alfa-GPC, Magnésio, L-Tirosina.")
        lines.append("- Vitaminas: Complexo B, Vitamina D, Vitamina C.")
        lines.append("- Estratégia econômica: ovos (colina), fígado (multivitamínico), sardinha (ômega-3).")
        lines.append("")
    if opts["Protocolos"]:
        lines.append("PROTOCOLOS DE LIMITE")
        lines.append("- Jejum intermitente (autofagia), Sono polifásico (experimental), Suspiro fisiológico (alívio de stress).")
        lines.append("")
    lines.append("AVISO: Este folheto é informativo e não substitui avaliação médica. Consulte um profissional antes de intervenções médicas.")
    return "\n".join(lines)

# Gerar PDF/texto em memória e oferecer download
def _build_pdf_bytes_from_text(text: str) -> bytes:
    # tenta usar reportlab; se não disponível, retorna bytes de texto simples
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import mm
        import io as _io
        buf = _io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story = []
        for line in text.split("\n"):
            if not line.strip():
                story.append(Spacer(1, 6))
            else:
                style = styles["Normal"]
                # título simples
                if line.isupper() and len(line.split()) < 6:
                    style = styles["Heading2"]
                story.append(Paragraph(line.replace("  ", "&nbsp;&nbsp;"), style))
        doc.build(story)
        pdf = buf.getvalue()
        buf.close()
        return pdf
    except Exception:
        return text.encode("utf-8")

if st.button("Gerar folheto PDF com seleção"):
    text = _build_text_for_pdf(opts)
    pdf_bytes = _build_pdf_bytes_from_text(text)
    st.success("Folheto pronto para download.")
    st.download_button("Baixar folheto (PDF)", data=pdf_bytes, file_name="mapa_biohacking.pdf", mime="application/pdf")

st.markdown("---")

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