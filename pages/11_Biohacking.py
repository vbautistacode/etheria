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

# Substitua o bloco Mermaid anterior por este (cole no seu pages/11_Biohacking.py)
import streamlit as st
import io
from datetime import datetime

# Se quiser usar um arquivo local já presente no repositório, defina path_local = "assets/mindmap.png"
path_local = None  # ou "assets/mindmap.png"

st.markdown("### Mapa mental: Guia de Biohacking e Neurofisiologia")

# upload do arquivo (opcional)
uploaded = None
if path_local:
    try:
        with open(path_local, "rb") as f:
            uploaded = f.read()
    except Exception:
        uploaded = None

# Exibir imagem se houver (use_container_width substitui use_column_width)
if uploaded:
    st.image(uploaded, use_container_width=True, caption="Mapa mental enviado")

st.markdown("---")

# Mermaid source (resumido do mapa)
mermaid_source = """
mindmap
  root((Guia de Biohacking e Neurofisiologia))
    Hemisférios
      Esquerdo[Esquerdo: Analítico\\nLógica, Linguagem, Detalhes, Controle motor direito]
      Direito[Direito: Sintetizador\\nCriatividade, Espaço, Não-verbal, Controle motor esquerdo]
      CorpoCaloso[Corpo Caloso: Integração]
    Autorregulação
      RespiraçãoNasal[Narinas\\nDireita=Alerta; Esquerda=Calma; Ciclo nasal]
      ControleVisual[Visão foveal vs panorâmica\\nMovimentos sacádicos]
      Termorregulação[Frio -> Dopamina; Calor -> Reparação]
    QuímicaCerebral
      Neurotransmissores[Dopamina; Noradrenalina; GABA; Acetilcolina]
      Hormônios[Cortisol; Melatonina; Ocitocina]
    Suplementação
      Nootrópicos[Cafeína+L-Teanina; Alfa-GPC; Magnésio; L-Tirosina]
      Vitaminas[B-complex; Vit D; Vit C]
      Alimentos[Ovos; Fígado; Sardinha]
    Protocolos
      Limite[Jejum intermitente; Sono polifásico; Suspiro fisiológico]
"""

# Mapeamento de detalhes (usado no painel de detalhes ao clicar)
# Você pode estender/editar as descrições abaixo conforme desejar.
details_map = {
    "Guia de Biohacking e Neurofisiologia": "Visão geral: Hemisférios, Autorregulação, Química, Suplementação, Protocolos.",
    "Esquerdo": "Lado esquerdo: linguagem, lógica, análise de detalhes; controla o lado direito do corpo.",
    "Direito": "Lado direito: criatividade, processamento espacial, linguagem não-verbal; controla o lado esquerdo do corpo.",
    "CorpoCaloso": "Corpo caloso: integra os dois hemisférios.",
    "RespiraçãoNasal": "Respiração nasal: narina direita -> alerta/simpático; narina esquerda -> calma/parassimpático; existe ciclo nasal natural.",
    "ControleVisual": "Controle visual: visão foveal para foco; visão panorâmica para criatividade; movimentos sacádicos ajudam a reduzir stress.",
    "Termorregulação": "Termorregulação: exposição ao frio aumenta dopamina; calor favorece reparação celular.",
    "Neurotransmissores": "Neurotransmissores chave: Dopamina, Noradrenalina, GABA, Acetilcolina.",
    "Hormônios": "Hormônios relevantes: Cortisol (stress/energia), Melatonina (sono), Ocitocina (vínculo).",
    "Nootrópicos": "Nootrópicos: Cafeína+L-Teanina, Alfa-GPC, Magnésio, L-Tirosina (uso com cautela).",
    "Vitaminas": "Vitaminas: Complexo B, Vitamina D, Vitamina C.",
    "Alimentos": "Alimentos ricos: ovos (colina), fígado (multivitamínico), sardinha (ômega-3).",
    "Limite": "Protocolos de limite: jejum intermitente, sono polifásico (experimental), suspiro fisiológico."
}

# HTML que renderiza Mermaid e adiciona interatividade via JS
mermaid_html = f"""
<div style="display:flex; gap:16px; align-items:flex-start;">
  <div style="flex:1; min-width:60%;">
    <div style="margin-bottom:8px;">
      <input id="searchBox" placeholder="Buscar nó (ex.: Dopamina, RespiraçãoNasal)" style="width:60%; padding:6px;"/>
      <button id="btnSearch" style="margin-left:8px;padding:6px 10px;">Buscar</button>
      <button id="btnClear" style="margin-left:6px;padding:6px 10px;">Limpar destaque</button>
      <button id="btnExport" style="float:right;padding:6px 10px;">Exportar PNG</button>
    </div>
    <div id="mermaid-container" style="border:1px solid #eee; padding:8px; border-radius:6px; background:#fff;">
      <div class="mermaid">
{mermaid_source}
      </div>
    </div>
  </div>

  <div style="width:34%; min-width:260px;">
    <div style="padding:10px;border:1px solid #eee;border-radius:6px;background:#fafafa;">
      <h4 style="margin:6px 0 8px 0;">Detalhes do nó</h4>
      <div id="nodeTitle" style="font-weight:600;color:#2b8cbe;margin-bottom:6px;">Clique em um nó</div>
      <div id="nodeDetail" style="font-size:13px;color:#333;line-height:1.4;">Ao clicar em um nó, a descrição aparecerá aqui.</div>
      <hr style="margin:12px 0;">
      <div style="font-size:12px;color:#666;">
        <strong>Dicas de interação</strong>
        <ul style="padding-left:18px;margin:6px 0;">
          <li>Use o mouse para arrastar e rolar para dar zoom.</li>
          <li>Busque por rótulos com a caixa de busca.</li>
          <li>Exporte o diagrama como PNG com o botão Exportar.</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<!-- Mermaid -->
<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<!-- svg-pan-zoom para pan/zoom do SVG -->
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>

<script>
  // Inicializa mermaid
  mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});

  // Função utilitária: aguarda o SVG do Mermaid estar presente
  function waitForMermaidSVG(timeout = 3000) {{
    return new Promise((resolve, reject) => {{
      const start = Date.now();
      (function check() {{
        const svg = document.querySelector('#mermaid-container svg');
        if (svg) return resolve(svg);
        if (Date.now() - start > timeout) return reject(new Error('SVG não encontrado'));
        requestAnimationFrame(check);
      }})();
    }});
  }}

  // Mapeamento de detalhes (mesmo conteúdo do Python)
  const DETAILS = {json.dumps(details_map)};

  // Após render do SVG, adicionamos interatividade
  waitForMermaidSVG(5000).then(svg => {{
    // 1) aplicar pan/zoom
    try {{
      const panZoomInstance = svgPanZoom(svg, {{
        zoomEnabled: true,
        controlIconsEnabled: false,
        fit: true,
        center: true,
        minZoom: 0.5,
        maxZoom: 4
      }});
    }} catch (e) {{
      console.warn('svg-pan-zoom falhou:', e);
    }}

    // 2) localizar elementos de texto/nó e transformar em "clicáveis"
    // Mermaid gera <g class="node"> com <text> dentro; vamos selecionar por 'g.node' ou 'g[class*="node"]'
    const nodeGroups = svg.querySelectorAll('g[class*="node"], g.node');
    const nodes = [];
    nodeGroups.forEach(g => {{
      // extrair texto principal (primeira <text> ou tspan)
      const textEl = g.querySelector('text');
      if (!textEl) return;
      const label = textEl.textContent.trim();
      // guardar referência
      nodes.push({{ group: g, label }});
      // estilo cursor
      g.style.cursor = 'pointer';
      // hover effect
      g.addEventListener('mouseenter', () => {{
        g.style.opacity = 0.85;
      }});
      g.addEventListener('mouseleave', () => {{
        g.style.opacity = 1;
      }});
      // click handler: destacar e mostrar detalhes
      g.addEventListener('click', (ev) => {{
        ev.stopPropagation();
        // limpar destaque anterior
        nodes.forEach(n => n.group.querySelectorAll('rect, ellipse, path').forEach(el => el.style.stroke = ''));
        // destacar borda do nó clicado (se houver rect/ellipse)
        g.querySelectorAll('rect, ellipse, path').forEach(el => {{
          el.style.stroke = '#ff7f50';
          el.style.strokeWidth = '2px';
        }});
        // preencher painel de detalhes
        const title = label || 'Nó';
        const key = label.split('\\n')[0].trim(); // tentativa de chave curta
        const detail = DETAILS[key] || DETAILS[title] || DETAILS[label] || 'Descrição não disponível.';
        document.getElementById('nodeTitle').innerText = title;
        document.getElementById('nodeDetail').innerText = detail;
      }});
    }});

    // 3) busca por rótulo: destaca nós que contenham o termo
    document.getElementById('btnSearch').addEventListener('click', () => {{
      const q = document.getElementById('searchBox').value.trim().toLowerCase();
      if (!q) return;
      let found = false;
      nodes.forEach(n => {{
        const label = n.label.toLowerCase();
        if (label.includes(q)) {{
          // destacar
          n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
            el.style.stroke = '#2b8cbe';
            el.style.strokeWidth = '2px';
          }});
          // scroll/zoom to node: compute bbox and center
          try {{
            const bbox = n.group.getBBox();
            const svgEl = svg;
            const svgWidth = svgEl.viewBox.baseVal.width || svgEl.clientWidth;
            const svgHeight = svgEl.viewBox.baseVal.height || svgEl.clientHeight;
            const cx = bbox.x + bbox.width/2;
            const cy = bbox.y + bbox.height/2;
            // pan/zoom via svg-pan-zoom instance if exists
            if (window.svgPanZoom && typeof window.svgPanZoom === 'function') {{
              // try to get instance (we didn't keep reference), so re-init quick fit
              // fallback: no reliable instance handle; just set viewBox centered (best-effort)
              // (Note: advanced control would require storing the instance globally)
            }}
          }} catch(e){{}}
          found = true;
        }} else {{
          // remover destaque
          n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
            el.style.stroke = '';
            el.style.strokeWidth = '';
          }});
        }}
      }});
      if (!found) {{
        alert('Nenhum nó encontrado para: ' + q);
      }}
    }});

    // limpar destaque
    document.getElementById('btnClear').addEventListener('click', () => {{
      nodes.forEach(n => n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
        el.style.stroke = '';
        el.style.strokeWidth = '';
      }}));
      document.getElementById('searchBox').value = '';
    }});

    // exportar PNG (converte SVG para canvas e baixa)
    document.getElementById('btnExport').addEventListener('click', () => {{
      try {{
        const svgEl = svg;
        const serializer = new XMLSerializer();
        let source = serializer.serializeToString(svgEl);
        // add name spaces
        if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) {{
          source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
        }}
        if(!source.match(/^<svg[^>]+"http\\:\\/\\/www\\.w3\\.org\\/1999\\/xlink"/)) {{
          source = source.replace(/^<svg/, '<svg xmlns:xlink="http://www.w3.org/1999/xlink"');
        }}
        // add xml declaration
        source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
        const svg64 = btoa(unescape(encodeURIComponent(source)));
        const b64Start = 'data:image/svg+xml;base64,';
        const image64 = b64Start + svg64;
        const img = new Image();
        img.onload = function() {{
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
          // white background
          ctx.fillStyle = '#ffffff';
          ctx.fillRect(0,0,canvas.width,canvas.height);
          ctx.drawImage(img,0,0);
          const png = canvas.toDataURL('image/png');
          const a = document.createElement('a');
          a.href = png;
          a.download = 'mapa_biohacking.png';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
        }};
        img.src = image64;
      }} catch (err) {{
        console.error('Erro ao exportar PNG:', err);
        alert('Falha ao exportar PNG. Veja console para detalhes.');
      }}
    }});

    // clique no fundo limpa seleção
    svg.addEventListener('click', (ev) => {{
      if (ev.target === svg) {{
        nodes.forEach(n => n.group.querySelectorAll('rect, ellipse, path').forEach(el => el.style.stroke = ''));
        document.getElementById('nodeTitle').innerText = 'Clique em um nó';
        document.getElementById('nodeDetail').innerText = 'Ao clicar em um nó, a descrição aparecerá aqui.';
      }}
    }});

  }}).catch(err => {{
    console.warn('Não foi possível inicializar interatividade do Mermaid:', err);
  }});
</script>

<style>
  /* Ajustes visuais para o container Mermaid */
  #mermaid-container {{ max-width: 100%; overflow: auto; padding: 8px 0; background:#fff; }}
  .mermaid svg {{ max-width: 100%; height: auto; display:block; }}
</style>
"""

st.markdown("#### Versão interativa do mapa")
st.components.v1.html(mermaid_html, height=520, scrolling=True)

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