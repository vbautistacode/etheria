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

# Inserir este bloco no lugar do Mermaid atual em pages/11_Biohacking.py
# Ele tenta extrair automaticamente descrições do PDF (se enviado),
# cria details_map dinamicamente, adiciona interatividade (pan/zoom, busca, clique -> callback Python),
# e implementa colapsar/expandir ramos no SVG gerado pelo Mermaid.

import streamlit as st
import io
import json
import re

st.markdown("### Mapa mental: Guia de Biohacking e Neurofisiologia (Mermaid interativo melhorado)")

# --- Upload opcional do PDF (se o usuário quiser fornecer/atualizar o documento)
pdf_file = st.file_uploader("Enviar PDF do dossiê (opcional) para mapear descrições automaticamente", type=["pdf"])

# Se houver imagem local do mapa, exiba com use_container_width
path_local = None  # "assets/mindmap.png"
if path_local:
    try:
        with open(path_local, "rb") as f:
            st.image(f.read(), use_container_width=True, caption="Mapa mental (arquivo local)")
    except Exception:
        pass

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

# Lista de chaves/nós que queremos mapear automaticamente
node_keys = [
    "Guia de Biohacking e Neurofisiologia", "Esquerdo", "Direito", "CorpoCaloso",
    "RespiraçãoNasal", "ControleVisual", "Termorregulação",
    "Neurotransmissores", "Hormônios",
    "Nootrópicos", "Vitaminas", "Alimentos",
    "Limite"
]

# Função para extrair texto do PDF (se PyPDF2 estiver disponível)
def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n".join(pages)
    except Exception:
        # fallback: return empty string if PyPDF2 não disponível
        return ""

# Função que cria details_map procurando por termos no texto do PDF
def build_details_map_from_text(text: str, keys: list) -> dict:
    details = {}
    lower_text = text.lower()
    for k in keys:
        # tentativa de localizar ocorrências exatas ou aproximadas
        k_clean = k.lower()
        # procurar por palavra-chave exata
        idx = lower_text.find(k_clean)
        if idx == -1:
            # tentar variações (ex.: "respiração nasal" -> "respiração")
            parts = re.split(r'[\s_\\-]+', k_clean)
            found = False
            for p in parts:
                if len(p) > 3 and p in lower_text:
                    idx = lower_text.find(p)
                    found = True
                    break
            if not found:
                idx = -1
        if idx >= 0:
            # extrair contexto: 200 chars antes e depois, limpar quebras
            start = max(0, idx - 200)
            end = min(len(text), idx + 200)
            snippet = text[start:end].strip()
            snippet = re.sub(r'\s+', ' ', snippet)
            # se snippet muito curto, pegar a sentença inteira
            details[k] = snippet
        else:
            details[k] = ""  # preencher vazio para posterior fallback
    return details

# Tentar construir details_map a partir do PDF enviado; se não houver, usar fallback embutido
details_map = {}

if pdf_file is not None:
    pdf_bytes = pdf_file.read()
    extracted = extract_text_from_pdf_bytes(pdf_bytes)
    if extracted:
        details_map = build_details_map_from_text(extracted, node_keys)

# Fallback manual (conteúdo extraído do dossiê enviado anteriormente)
fallback_map = {
    "Guia de Biohacking e Neurofisiologia": "Visão geral: Hemisférios, Autorregulação, Química, Suplementação, Protocolos.",
    "Esquerdo": "Hemisfério esquerdo: linguagem, lógica, análise de detalhes; controla o lado direito do corpo.",
    "Direito": "Hemisfério direito: criatividade, processamento espacial, linguagem não-verbal; controla o lado esquerdo do corpo.",
    "CorpoCaloso": "Corpo caloso: ponte de fibras que integra os dois hemisférios.",
    "RespiraçãoNasal": "Respiração nasal: narina direita tende a ativar o simpático (alerta); narina esquerda tende a ativar o parassimpático (calma).",
    "ControleVisual": "Controle visual: visão foveal aumenta foco; visão panorâmica favorece criatividade; movimentos sacádicos ajudam a reduzir carga emocional.",
    "Termorregulação": "Termorregulação: exposição ao frio aumenta dopamina e resiliência; calor (sauna) libera proteínas de choque térmico e favorece reparação.",
    "Neurotransmissores": "Neurotransmissores chave: Dopamina (motivação), Noradrenalina (alerta), GABA (calma), Acetilcolina (aprendizado).",
    "Hormônios": "Hormônios relevantes: Cortisol (stress/energia), Melatonina (sono), Ocitocina (vínculo).",
    "Nootrópicos": "Nootrópicos: Cafeína+L-Teanina (foco limpo), Alfa-GPC (colina/acetilcolina), Magnésio (relaxamento), L-Tirosina (precursor de dopamina).",
    "Vitaminas": "Vitaminas importantes: Complexo B (energia), Vitamina D (hormonal/imunidade), Vitamina C (antioxidante).",
    "Alimentos": "Alimentos-chave: ovos (colina), fígado (multivitamínico), sardinha (ômega-3).",
    "Limite": "Protocolos de limite: jejum intermitente (autofagia), sono polifásico (experimental), suspiro fisiológico (alívio de stress)."
}

# Merge: se algum valor extraído estiver vazio, use fallback
for k in node_keys:
    val = details_map.get(k, "")
    if not val:
        details_map[k] = fallback_map.get(k, "")

# Prepare JSON to inject into the client-side JS
details_json = json.dumps(details_map)

# HTML + JS que renderiza o Mermaid e adiciona interatividade avançada
mermaid_html = f"""
<div style="display:flex; gap:16px; align-items:flex-start;">
  <div style="flex:1; min-width:60%;">
    <div style="margin-bottom:8px;">
      <input id="searchBox" placeholder="Buscar nó (ex.: Dopamina, RespiraçãoNasal)" style="width:60%; padding:6px;"/>
      <button id="btnSearch" style="margin-left:8px;padding:6px 10px;">Buscar</button>
      <button id="btnClear" style="margin-left:6px;padding:6px 10px;">Limpar destaque</button>
      <button id="btnCollapse" style="margin-left:6px;padding:6px 10px;">Colapsar ramos</button>
      <button id="btnExpand" style="margin-left:6px;padding:6px 10px;">Expandir ramos</button>
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
          <li>Use o mouse para arrastar e a roda para dar zoom.</li>
          <li>Busque por rótulos com a caixa de busca.</li>
          <li>Exporte o diagrama como PNG com o botão Exportar.</li>
        </ul>
      </div>
    </div>
  </div>
</div>

<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>

<script>
  mermaid.initialize({{ startOnLoad: true, theme: 'default', securityLevel: 'loose' }});
  const DETAILS = {details_json};

  function waitForMermaidSVG(timeout = 4000) {{
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

  waitForMermaidSVG(6000).then(svg => {{
    // init pan/zoom and keep instance global
    try {{
      window._mz = svgPanZoom(svg, {{
        zoomEnabled: true,
        controlIconsEnabled: false,
        fit: true,
        center: true,
        minZoom: 0.5,
        maxZoom: 4
      }});
    }} catch(e){{ console.warn('svg-pan-zoom falhou', e); }}

    // collect node groups (Mermaid usually creates g[class*="node"])
    const nodeGroups = Array.from(svg.querySelectorAll('g[class*="node"], g.node'));
    const nodes = nodeGroups.map(g => {{
      const textEl = g.querySelector('text');
      const label = textEl ? textEl.textContent.trim() : null;
      return {{ group: g, label }};
    }}).filter(n => n.label);

    // helper: clear highlights
    function clearHighlights() {{
      nodes.forEach(n => n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
        el.style.stroke = '';
        el.style.strokeWidth = '';
        el.style.opacity = '';
      }}));
    }}

    // click handler: highlight and show details; also send selection to Streamlit via safe URL update
    nodes.forEach(n => {{
      n.group.style.cursor = 'pointer';
      n.group.addEventListener('click', (ev) => {{
        ev.stopPropagation();
        clearHighlights();
        n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
          el.style.stroke = '#ff7f50';
          el.style.strokeWidth = '2px';
        }});
        const title = n.label;
        const key = title.split('\\n')[0].trim();
        const detail = DETAILS[key] || DETAILS[title] || 'Descrição não disponível.';
        document.getElementById('nodeTitle').innerText = title;
        document.getElementById('nodeDetail').innerText = detail;

        // safe update of query params: use pathname + search
        try {{
          const params = new URLSearchParams(window.location.search);
          params.set('selected_node', key);
          const newSearch = params.toString();
          const newUrl = window.location.pathname + (newSearch ? ('?' + newSearch) : '');
          window.location.href = newUrl;
        }} catch (err) {{
          console.error('Erro ao atualizar query params:', err);
          window.location.href = window.location.pathname + '?selected_node=' + encodeURIComponent(key);
        }}
      }});
    }});

    // search: highlight nodes containing query
    document.getElementById('btnSearch').addEventListener('click', () => {{
      const q = document.getElementById('searchBox').value.trim().toLowerCase();
      if (!q) return;
      clearHighlights();
      let found = false;
      nodes.forEach(n => {{
        if (n.label.toLowerCase().includes(q)) {{
          n.group.querySelectorAll('rect, ellipse, path').forEach(el => {{
            el.style.stroke = '#2b8cbe';
            el.style.strokeWidth = '2px';
          }});
          // try to center on node using svg-pan-zoom instance
          try {{
            const bbox = n.group.getBBox();
            const cx = bbox.x + bbox.width/2;
            const cy = bbox.y + bbox.height/2;
            if (window._mz && typeof window._mz.pan === 'function') {{
              // compute pan to center node (approx)
              const pan = window._mz.getPan();
              const zoom = window._mz.getZoom();
              // center by setting pan so that node center maps to viewport center
              const vb = svg.viewBox.baseVal;
              const viewW = vb.width;
              const viewH = vb.height;
              const newPanX = -cx * zoom + viewW/2;
              const newPanY = -cy * zoom + viewH/2;
              window._mz.pan({{ x: newPanX, y: newPanY }});
            }}
          }} catch(e){{ console.warn(e); }}
          found = true;
        }}
      }});
      if (!found) alert('Nenhum nó encontrado para: ' + q);
    }});

    document.getElementById('btnClear').addEventListener('click', () => {{
      clearHighlights();
      document.getElementById('searchBox').value = '';
    }});

    // collapse: hide all nodes except root and top-level headings
    const topLevel = ['Guia de Biohacking e Neurofisiologia','Hemisférios','Autorregulação','QuímicaCerebral','Suplementação','Protocolos'];
    document.getElementById('btnCollapse').addEventListener('click', () => {{
      nodes.forEach(n => {{
        const key = n.label.split('\\n')[0].trim();
        if (!topLevel.includes(key)) {{
          n.group.style.display = 'none';
        }}
      }});
    }});
    document.getElementById('btnExpand').addEventListener('click', () => {{
      nodes.forEach(n => n.group.style.display = '');
    }});

    // export SVG -> PNG
    document.getElementById('btnExport').addEventListener('click', () => {{
      try {{
        const serializer = new XMLSerializer();
        let source = serializer.serializeToString(svg);
        if(!source.match(/^<svg[^>]+xmlns="http\\:\\/\\/www\\.w3\\.org\\/2000\\/svg"/)) {{
          source = source.replace(/^<svg/, '<svg xmlns="http://www.w3.org/2000/svg"');
        }}
        source = '<?xml version="1.0" standalone="no"?>\\r\\n' + source;
        const svg64 = btoa(unescape(encodeURIComponent(source)));
        const image64 = 'data:image/svg+xml;base64,' + svg64;
        const img = new Image();
        img.onload = function() {{
          const canvas = document.createElement('canvas');
          canvas.width = img.width;
          canvas.height = img.height;
          const ctx = canvas.getContext('2d');
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

    // click on background clears selection
    svg.addEventListener('click', (ev) => {{
      if (ev.target === svg) {{
        clearHighlights();
        document.getElementById('nodeTitle').innerText = 'Clique em um nó';
        document.getElementById('nodeDetail').innerText = 'Ao clicar em um nó, a descrição aparecerá aqui.';
      }}
    }});

  }}).catch(err => {{
    console.warn('Não foi possível inicializar interatividade do Mermaid:', err);
  }});
</script>

<style>
  #mermaid-container {{ max-width: 100%; overflow: auto; padding: 8px 0; background:#fff; }}
  .mermaid svg {{ max-width: 100%; height: auto; display:block; }}
</style>
"""

st.components.v1.html(mermaid_html, height=560, scrolling=True)

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