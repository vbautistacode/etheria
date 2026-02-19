# pages/11_Biohacking.py
import streamlit as st
import io
import json
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

st.markdown("---")

# --- Mapa mental interativo com Cytoscape.js ---
st.markdown("### Mapa mental interativo")
st.markdown("Explore o mapa: clique em um nó para ver detalhes; use colapsar/expandir e exportar PNG.")

# Read selected node from query params (callback from the Cytoscape component)
params = st.experimental_get_query_params()
selected_node_id = params.get("selected_node", [None])[0]

# Detailed graph structure (expanded with sub-nodes)
graph_data = {
    "nodes": [
        {"data": {"id": "root", "label": "Guia de Biohacking e Neurofisiologia", "detail": "Visão geral: Hemisférios, Autorregulação, Química, Suplementação, Protocolos."}},
        # Hemisférios
        {"data": {"id": "hemis", "label": "Hemisférios Cerebrais", "detail": "Especializações e integração via corpo caloso."}},
        {"data": {"id": "left", "label": "Lado Esquerdo (Analítico)", "detail": "Linguagem, lógica, análise de detalhes, controle motor direito.", "parent": "hemis"}},
        {"data": {"id": "right", "label": "Lado Direito (Sintetizador)", "detail": "Criatividade, processamento espacial, linguagem não-verbal, controle motor esquerdo.", "parent": "hemis"}},
        {"data": {"id": "cc", "label": "Corpo Caloso", "detail": "Integração entre hemisférios.", "parent": "hemis"}},
        # Autorregulação
        {"data": {"id": "autor", "label": "Autorregulação (Biohack)", "detail": "Respiração nasal, controle visual, termorregulação."}},
        {"data": {"id": "resp", "label": "Respiração Nasal", "detail": "Narina direita -> alerta; narina esquerda -> calma; ciclo nasal natural.", "parent": "autor"}},
        {"data": {"id": "resp_right", "label": "Narina Direita (Alerta)", "detail": "Aumenta alerta, frequência cardíaca e energia.", "parent": "resp"}},
        {"data": {"id": "resp_left", "label": "Narina Esquerda (Calma)", "detail": "Ativa parassimpático, reduz frequência cardíaca.", "parent": "resp"}},
        {"data": {"id": "visual", "label": "Controle Visual", "detail": "Visão foveal para foco; visão panorâmica para criatividade; movimentos sacádicos reduzem stress.", "parent": "autor"}},
        {"data": {"id": "thermo", "label": "Termorregulação", "detail": "Frio -> dopamina/resiliência; calor -> proteínas de choque térmico e reparação.", "parent": "autor"}},
        # Química cerebral
        {"data": {"id": "chem", "label": "Química Cerebral", "detail": "Neurotransmissores e hormônios que modulam estados."}},
        {"data": {"id": "dop", "label": "Dopamina", "detail": "Motivação, recompensa, aumentada por frio e conclusão de tarefas.", "parent": "chem"}},
        {"data": {"id": "nor", "label": "Noradrenalina", "detail": "Alerta e vigilância.", "parent": "chem"}},
        {"data": {"id": "gaba", "label": "GABA", "detail": "Inibição, calma e redução de ansiedade.", "parent": "chem"}},
        {"data": {"id": "ach", "label": "Acetilcolina", "detail": "Aprendizado e atenção.", "parent": "chem"}},
        {"data": {"id": "horm", "label": "Hormônios", "detail": "Cortisol, Melatonina, Ocitocina.", "parent": "chem"}},
        # Suplementação e nutrição
        {"data": {"id": "supp", "label": "Suplementação e Nutrição", "detail": "Nootrópicos, vitaminas e alimentos-chave."}},
        {"data": {"id": "noots", "label": "Nootrópicos", "detail": "Cafeína+L-Teanina, Alfa-GPC, Magnésio, L-Tirosina.", "parent": "supp"}},
        {"data": {"id": "vits", "label": "Vitaminas", "detail": "Complexo B, Vitamina D, Vitamina C.", "parent": "supp"}},
        {"data": {"id": "foods", "label": "Alimentos-chave", "detail": "Ovos (colina), fígado (multivitamínico), sardinha (ômega-3).", "parent": "supp"}},
        # Protocolos de limite
        {"data": {"id": "prot", "label": "Protocolos de Limite", "detail": "Jejum intermitente, sono polifásico, suspiro fisiológico."}},
        {"data": {"id": "fast", "label": "Jejum Intermitente", "detail": "Autofagia e periodização alimentar (experimental).", "parent": "prot"}},
        {"data": {"id": "poly", "label": "Sono Polifásico", "detail": "Padrões de sono alternativos (experimental).", "parent": "prot"}},
        {"data": {"id": "sigh", "label": "Suspiro Fisiológico", "detail": "Técnica rápida para alívio de stress.", "parent": "prot"}}
    ],
    "edges": [
        {"data": {"source": "root", "target": "hemis"}},
        {"data": {"source": "root", "target": "autor"}},
        {"data": {"source": "root", "target": "chem"}},
        {"data": {"source": "root", "target": "supp"}},
        {"data": {"source": "root", "target": "prot"}},
        {"data": {"source": "hemis", "target": "left"}},
        {"data": {"source": "hemis", "target": "right"}},
        {"data": {"source": "hemis", "target": "cc"}},
        {"data": {"source": "autor", "target": "resp"}},
        {"data": {"source": "resp", "target": "resp_right"}},
        {"data": {"source": "resp", "target": "resp_left"}},
        {"data": {"source": "autor", "target": "visual"}},
        {"data": {"source": "autor", "target": "thermo"}},
        {"data": {"source": "chem", "target": "dop"}},
        {"data": {"source": "chem", "target": "nor"}},
        {"data": {"source": "chem", "target": "gaba"}},
        {"data": {"source": "chem", "target": "ach"}},
        {"data": {"source": "chem", "target": "horm"}},
        {"data": {"source": "supp", "target": "noots"}},
        {"data": {"source": "supp", "target": "vits"}},
        {"data": {"source": "supp", "target": "foods"}},
        {"data": {"source": "prot", "target": "fast"}},
        {"data": {"source": "prot", "target": "poly"}},
        {"data": {"source": "prot", "target": "sigh"}}
    ]
}

# Convert to JSON string for embedding
graph_json = json.dumps(graph_data)

# HTML/JS for Cytoscape with collapse/expand and query-string callback
html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Mapa Biohacking - Cytoscape</title>
  <script src="https://unpkg.com/cytoscape@3.24.0/dist/cytoscape.min.js"></script>
  <style>
    body {{ margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial; }}
    #container {{ display:flex; gap:0; }}
    #cy {{ width: 66%; height: 720px; display: inline-block; vertical-align: top; border: 1px solid #e6e6e6; box-sizing: border-box; }}
    #panel {{ width: 34%; height: 720px; display: inline-block; vertical-align: top; padding: 12px; box-sizing: border-box; border-left: 1px solid #f0f0f0; overflow: auto; }}
    .btn {{ display:inline-block; padding:8px 12px; margin:6px 6px 12px 0; background:#2b8cbe; color:#fff; border-radius:6px; cursor:pointer; text-decoration:none; }}
    .btn-ghost {{ background:#f0f0f0; color:#333; border:1px solid #ddd; }}
    .small {{ font-size: 13px; color:#666; }}
    h3 {{ margin: 6px 0 8px 0; }}
    p {{ margin: 6px 0; line-height:1.4; }}
    .section-title {{ font-weight:600; margin-top:10px; }}
  </style>
</head>
<body>
  <div id="container">
    <div id="cy"></div>
    <div id="panel">
      <h3>Detalhes do nó</h3>
      <div id="nodetitle"><em>Clique em um nó no grafo</em></div>
      <div id="nodedetail" class="small"></div>
      <div style="margin-top:12px;">
        <a id="btn-reset" class="btn">Centralizar grafo</a>
        <a id="btn-collapse" class="btn btn-ghost">Colapsar ramos</a>
        <a id="btn-expand" class="btn btn-ghost">Expandir ramos</a>
        <a id="btn-export" class="btn">Exportar PNG</a>
      </div>
      <hr/>
      <div class="small">
        <strong>Interação</strong>
        <ul>
          <li>Clique em um nó para ver detalhes e enviar seleção ao app (recarrega a página).</li>
          <li>Arraste o canvas para mover; role para dar zoom.</li>
          <li>Use "Colapsar ramos" para ocultar sub-nós; "Expandir ramos" para restaurar.</li>
        </ul>
      </div>
      <div class="section-title">Nó selecionado (Python)</div>
      <div id="selected_python" class="small" style="background:#fafafa;padding:8px;border-radius:6px;margin-top:6px;"></div>
    </div>
  </div>

  <script>
    const graph = {graph_json};

    // Initialize cytoscape
    const cy = cytoscape({{
      container: document.getElementById('cy'),
      elements: graph,
      style: [
        {{
          selector: 'node',
          style: {{
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'background-color': '#2b8cbe',
            'color': '#fff',
            'text-wrap': 'wrap',
            'text-max-width': 140,
            'font-size': 12,
            'padding': '8px',
            'shape': 'round-rectangle',
            'width': 'label',
            'height': 'label'
          }}
        }},
        {{
          selector: 'edge',
          style: {{
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': '#cfd8dc',
            'target-arrow-color': '#cfd8dc',
            'width': 2
          }}
        }},
        {{
          selector: ':selected',
          style: {{
            'background-color': '#ff7f50',
            'line-color': '#ff7f50',
            'target-arrow-color': '#ff7f50'
          }}
        }},
        {{
          selector: '.hidden',
          style: {{
            'display': 'none'
          }}
        }}
      ],
      layout: {{
        name: 'cose',
        animate: true,
        fit: true,
        padding: 30,
        nodeRepulsion: 8000,
        idealEdgeLength: 120
      }},
      wheelSensitivity: 0.2
    }});

    cy.ready(function() {{
      cy.fit(50);
    }});

    // Helper: get children of a parent node (by parent property)
    function getChildren(parentId) {{
      return cy.nodes().filter(n => n.data('parent') === parentId);
    }}

    // Collapse: hide all nodes that have a parent (except top-level parents)
    function collapseAll() {{
      // hide nodes that have a parent (i.e., sub-nodes)
      cy.nodes().forEach(n => {{
        if (n.data('parent')) {{
          n.addClass('hidden');
        }}
      }});
      // hide edges connected to hidden nodes
      cy.edges().forEach(e => {{
        if (e.source().hasClass('hidden') || e.target().hasClass('hidden')) {{
          e.addClass('hidden');
        }}
      }});
    }}

    // Expand: remove hidden class
    function expandAll() {{
      cy.nodes().removeClass('hidden');
      cy.edges().removeClass('hidden');
    }}

    document.getElementById('btn-collapse').addEventListener('click', function() {{
      collapseAll();
    }});
    document.getElementById('btn-expand').addEventListener('click', function() {{
      expandAll();
    }});

    // Node click: show details and send selection to Python by updating query string (reload)
    cy.on('tap', 'node', function(evt) {{
      const node = evt.target;
      const id = node.id();
      const title = node.data('label') || 'Nó';
      const detail = node.data('detail') || '';
      document.getElementById('nodetitle').innerHTML = '<strong>' + title + '</strong>';
      document.getElementById('nodedetail').innerText = detail;
      cy.elements().unselect();
      node.select();

      // Send selection to Python by updating query string (this reloads the page)
      const url = new URL(window.location.href);
      url.searchParams.set('selected_node', id);
      window.location.href = url.toString();
    }});

    // Reset / centralizar
    document.getElementById('btn-reset').addEventListener('click', function() {{
      cy.fit(50);
      cy.zoom(1);
    }});

    // Export PNG
    document.getElementById('btn-export').addEventListener('click', function() {{
      try {{
        const png64 = cy.png({{ full: true, scale: 2 }});
        const a = document.createElement('a');
        a.href = png64;
        a.download = 'mapa_biohacking.png';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      }} catch (err) {{
        alert('Falha ao exportar imagem: ' + err);
      }}
    }});

    // If Python passed a selected node via query param, highlight it
    (function highlightFromQuery() {{
      const params = new URLSearchParams(window.location.search);
      const sel = params.get('selected_node');
      if (sel) {{
        const node = cy.getElementById(sel);
        if (node) {{
          node.select();
          document.getElementById('nodetitle').innerHTML = '<strong>' + node.data('label') + '</strong>';
          document.getElementById('nodedetail').innerText = node.data('detail') || '';
          cy.animate({{ fit: {{ eles: node }}, duration: 600 }});
        }}
      }}
    }})();
  </script>
</body>
</html>
"""

# Render the Cytoscape component
st.components.v1.html(html, height=760, scrolling=True)

# Show the selected node id (from Python side) and details if present
if selected_node_id:
    # find node in graph_data
    node = next((n for n in graph_data["nodes"] if n["data"]["id"] == selected_node_id), None)
    if node:
        st.markdown("---")
        st.subheader("Nó selecionado (recebido pelo app)")
        st.markdown(f"**ID:** `{selected_node_id}`")
        st.markdown(f"**Título:** {node['data'].get('label')}")
        st.markdown(f"**Descrição:** {node['data'].get('detail')}")
        st.info("A página foi recarregada para enviar a seleção ao app. Use o botão 'Centralizar grafo' no painel para reposicionar a visualização.")
    else:
        st.warning("Nó selecionado não encontrado no grafo.")
else:
    st.markdown("---")
    st.info("Nenhum nó selecionado. Clique em um nó no grafo para enviar a seleção ao app (a página será recarregada).")

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