# 08_pranaterapia.py (integração: st.audio controla esfera e ciclo no cliente)
import time
from pathlib import Path
from html import escape

import streamlit as st

# ---------------------------------------------------------
# Configuração inicial
# ---------------------------------------------------------
st.title("Pranaterapia 🌬️")
st.markdown(
    """
    A Pranaterapia é uma prática que utiliza técnicas de respiração consciente para equilibrar o prana (energia vital) no corpo.  
    Sessões curtas por intenção (calma, foco, sono) com exercícios para integrar respiração, corpo e presença.
    """
)

st.caption(
    """
    Selecione um chakra no menu lateral.  
    Na opção “Respiração guiada” o áudio correspondente será carregado automaticamente.  
    Use o player para iniciar, pausar ou parar; a esfera e a contagem sincronizam-se com o player.
    """    
)

# ---------------------------------------------------------
# Presets por chakra
# ---------------------------------------------------------
CHAKRAS = {
    "Muladhara": {"color": "#CC0700", "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Estou seguro e enraizado."},
    "Svadhisthana": {"color": "#6A0F60", "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6}, "affirmation": "Minha criatividade flui."},
    "Manipura": {"color": "#F17C0F", "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8}, "affirmation": "Ação com clareza."},
    "Anahata": {"color": "#3DAE27", "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Abro meu coração."},
    "Vishuddha": {"color": "#346CDB", "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Comunico com verdade."},
    "Ajna": {"color": "#F4E922", "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Minha percepção se afina."},
    "Sahasrara": {"color": "#DF27C3", "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4}, "affirmation": "Conecto-me ao silêncio."},
}

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_ROOT = PROJECT_ROOT / "static"
SESSIONS_DIR = STATIC_ROOT / "audio" / "sessions"

# ---------------------------------------------------------
# Sidebar e controles (sem autoplay exposto)
# ---------------------------------------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]

preset = theme["preset"]
inhale = st.sidebar.number_input("Inspire", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold1 = st.sidebar.number_input("Segure após inspirar", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5)
exhale = st.sidebar.number_input("Expire", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5)
hold2 = st.sidebar.number_input("Segure após expirar", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5)
cycles = st.sidebar.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# ---------------------------------------------------------
# Interface principal
# ---------------------------------------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# defina intent primeiro
intent = st.selectbox(
    "Prática",
    options=[
        "Respiração guiada",
        "Respiração quadrada (Box Breathing)",
        "Respiração alternada (Nadi Shodhana)",
    ],
)

# Renderiza botões apenas quando NÃO for "Respiração guiada"
if intent != "Respiração guiada":
    col_start, col_stop = st.columns([1, 1])
    with col_start:
        start_btn = st.button("▶️ Iniciar prática")
    with col_stop:
        stop_btn = st.button("⏹️ Parar prática")
else:
    # evita NameError em código que verifica start_btn/stop_btn
    start_btn = None
    stop_btn = None

# comportamento do botão Parar (se existir)
if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.playing = False
    st.success("Prática interrompida. Aguarde a atualização da interface.")

# ---------------------------------------------------------
# Função de ciclo de respiração (servidor) — mantém comportamento atual
# ---------------------------------------------------------
def breathing_cycle(inhale_s, hold1_s, exhale_s, hold2_s, cycles=5):
    """
    Executa o ciclo de respiração no servidor e atualiza placeholder/progress.
    Chame esta função diretamente quando o usuário clicar em 'Iniciar prática'.
    Atenção: esta implementação é síncrona e usa time.sleep; durante a execução
    o servidor ficará ocupado com esta função até o término.
    """
    # reset flag caso exista
    st.session_state.stop_flag = False

    placeholder = st.empty()
    total_time = (inhale_s + hold1_s + exhale_s + hold2_s) * cycles
    elapsed = 0.0
    progress = st.progress(0.0)

    for c in range(int(cycles)):
        if st.session_state.get("stop_flag", False):
            placeholder.markdown("### ⏹️ Prática interrompida.")
            return

        # Inspire
        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inhale_s}s**")
        full = int(inhale_s)
        rem = inhale_s - full
        for _ in range(full):
            if st.session_state.get("stop_flag", False):
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        # Segure 1
        if hold1_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1_s}s**")
            full = int(hold1_s)
            rem = hold1_s - full
            for _ in range(full):
                if st.session_state.get("stop_flag", False):
                    placeholder.markdown("### ⏹️ Prática interrompida.")
                    return
                time.sleep(1)
                elapsed += 1
                progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem)
                elapsed += rem
                progress.progress(min(1.0, elapsed / total_time))

        # Expire
        placeholder.markdown(f"### 💨 Expire por **{exhale_s}s**")
        full = int(exhale_s)
        rem = exhale_s - full
        for _ in range(full):
            if st.session_state.get("stop_flag", False):
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        # Segure 2
        if hold2_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2_s}s**")
            full = int(hold2_s)
            rem = hold2_s - full
            for _ in range(full):
                if st.session_state.get("stop_flag", False):
                    placeholder.markdown("### ⏹️ Prática interrompida.")
                    return
                time.sleep(1)
                elapsed += 1
                progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem)
                elapsed += rem
                progress.progress(min(1.0, elapsed / total_time))

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
    progress.progress(1.0)

# ---------------------------------------------------------
# Quando o usuário clica em Start (servidor) mantemos a flag
# ---------------------------------------------------------
if start_btn:
    st.session_state.stop_flag = False
    st.session_state.playing = True

    if intent == "Respiração guiada":
        # opcional: não iniciar contagem server-side automaticamente; a contagem cliente será a principal
        # manter a chamada server-side caso queira registro ou fallback
        pass
    elif intent == "Respiração quadrada (Box Breathing)":
        st.subheader("🫁 Respiração quadrada (Box Breathing)")
        st.markdown(
            """
            Técnica usada para foco, estabilidade emocional e redução de ansiedade.
            **Ciclo sugerido:**
            - Inspire: 4s
            - Segure: 4s
            - Expire: 4s
            - Segure: 4s
            - 5 ciclos
            """
        )
        # não forçar reprodução do áudio aqui; o usuário usará o player nativo
    elif intent == "Respiração alternada (Nadi Shodhana)":
        st.subheader("🫁🔀 Respiração alternada (Nadi Shodhana)")
        st.markdown(
             """ 
             Técnica tradicional para equilibrar os canais energéticos (nadis) e acalmar a mente. 
             
             **Instruções guiadas (manual):** 
             1. Use o polegar direito para fechar a narina direita. 
             2. Inspire pela narina esquerda (4s). 
             3. Feche a narina esquerda com o anelar. 
             4. Expire pela direita (4s). 
             5. Inspire pela direita (4s). 
             6. Feche a direita. 
             7. Expire pela esquerda (4s). 
             Repita por 6 ciclos. """ 
        )

# ---------------------------------------------------------
# Localizar e renderizar o áudio (st.audio) e sincronizar com esfera e ciclo no cliente
# ---------------------------------------------------------
session_filename = f"{chakra.lower()}_session.wav"
session_path = SESSIONS_DIR / session_filename

if session_path.exists() and intent == "Respiração guiada":
    # 1) Renderiza st.audio (Streamlit serve internamente)
    try:
        st.audio(str(session_path))
    except Exception as e:
        st.error(f"Erro ao renderizar st.audio: {e}")
        st.stop()

    # 2) Injeta componente que encontra o <audio> criado por st.audio e sincroniza esfera + contagem cliente
    escaped_fname = escape(session_path.name)
    color = theme["color"]

    # HTML/JS que:
    # - localiza o <audio> do st.audio (por currentSrc / source.src / fallback)
    # - anexa listeners play/pause/ended
    # - anima a esfera com requestAnimationFrame
    # - executa a contagem de respiração no cliente (respeitando pausas do áudio)
    # Cole este trecho imediatamente após st.audio(str(session_path))
    # variáveis já presentes no seu contexto: session_path, theme, inhale, hold1, exhale, hold2, cycles
    # Bloco HTML/JS robusto: botão visual aciona o <audio>, espera o elemento aparecer e inicia esfera+contagem
    # Substitua seu bloco html_sync por este. Ele faz a esfera seguir exatamente o script
    # breathing_cycle (inhale / hold1 / exhale / hold2 / cycles) sem depender do st.audio.
    # Cole no lugar do html_sync atual e chame st.components.v1.html(html_sync, height=520).

    html_sync = f"""
    <div id="prana_control_wrap_{escaped_fname}" style="display:flex;flex-direction:column;align-items:center;margin-top:12px; gap:12px;">
      <button id="prana_visual_play_{escaped_fname}" style="padding:9px 12px;border-radius:10px;border:none;background:#fff;cursor:pointer;font-weight:700;">
        ▶️ Iniciar / Pausar
      </button>
      <button id="prana_visual_stop_{escaped_fname}" style="padding:9px 12px;border-radius:10px;border:none;background:#fff;cursor:pointer;font-weight:700;margin-left:8px;">
        ⏹️ Parar
      </button>

      <div id="prana_circle_{escaped_fname}" style="width:160px;height:160px;border-radius:50%;margin-top:12px;
          background:radial-gradient(circle at 30% 30%, #fff8, {color});
          box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;animation:prana_pulse_{escaped_fname} 2000ms ease-in-out infinite;">
      </div>
      <div id="prana_status_{escaped_fname}" style="margin-top:8px;font-weight:600;color:#222">Pronto</div>
      <div id="prana_breath_log_{escaped_fname}" style="min-height:36px;color:#333;font-weight:600;margin-top:8px;"></div>
    </div>

    <style>
    @keyframes prana_pulse_{escaped_fname} {{ 0%{{transform:scale(1)}}50%{{transform:scale(1.04)}}100%{{transform:scale(1)}} }}
    </style>

    <script>
    (function(){{
      const filename = "{escaped_fname}";
      const playBtn = document.getElementById('prana_visual_play_' + filename);
      const stopBtn = document.getElementById('prana_visual_stop_' + filename);
      const circle = document.getElementById('prana_circle_' + filename);
      const statusEl = document.getElementById('prana_status_' + filename);
      const logEl = document.getElementById('prana_breath_log_' + filename);

      const inhale = {inhale};
      const hold1 = {hold1};
      const exhale = {exhale};
      const hold2 = {hold2};
      const cycles = {int(cycles)};

      function setStatus(t){{ if (statusEl) statusEl.textContent = t; }}
      function setLog(t){{ if (logEl) logEl.textContent = t; console.log('[prana]', t); }}

      // Estado do ciclo (cliente-only)
      let breathingRunning = false;
      let paused = false;
      let currentCycle = 0;
      let currentSegmentIndex = 0;
      let segmentStart = 0;
      let raf = null;

      // Sequência de segmentos por ciclo
      function buildSeq() {{
        return [
          {{ label: 'Inspire', t: inhale }},
          {{ label: 'Segure', t: hold1 }},
          {{ label: 'Expire', t: exhale }},
          {{ label: 'Segure', t: hold2 }}
        ];
      }}

      // Função que calcula a escala da esfera com base no progresso do segmento
      // Inspire: escala sobe de 1.0 -> 1.25
      // Expire: escala desce de 1.25 -> 1.0
      // Holds: mantém escala no início/fim do segmento (dependendo se hold after inhale or exhale)
      function computeScaleForSegment(segLabel, progress) {{
        // progress: 0..1
        const minScale = 1.0;
        const maxScale = 1.25;
        if (segLabel === 'Inspire') {{
          // ease in (sinusoidal)
          const eased = Math.sin(progress * Math.PI / 2); // 0..1
          return minScale + (maxScale - minScale) * eased;
        }} else if (segLabel === 'Expire') {{
          // ease out (cosine)
          const eased = 1 - Math.cos(progress * Math.PI / 2); // 0..1
          // but we want decreasing: start at maxScale -> minScale
          return maxScale - (maxScale - minScale) * eased;
        }} else {{
          // holds: decide whether it's hold after inhale (keep max) or hold after exhale (keep min)
          // We'll keep the scale at maxScale if previous segment was Inspire, else minScale
          return (currentSegmentIndex === 1) ? maxScale : minScale;
        }}
      }}

      // animação por requestAnimationFrame que usa o relógio do cliente (performance.now)
      function animateFrameLoop() {{
        if (!breathingRunning || paused) {{
          if (raf) cancelAnimationFrame(raf);
          raf = null;
          return;
        }}

        const now = performance.now();
        const seq = buildSeq();
        const seg = seq[currentSegmentIndex];
        const segDuration = Math.max(0.001, seg.t * 1000); // ms
        const elapsed = now - segmentStart;
        const progress = Math.min(1, elapsed / segDuration);

        // atualiza log e status
        setLog('Ciclo ' + (currentCycle+1) + '/' + cycles + ' — ' + seg.label + ' ' + Math.ceil(seg.t * (1 - progress)) + 's');
        setStatus('Tocando');

        // calcula escala e aplica
        const scale = computeScaleForSegment(seg.label, progress);
        circle.style.transform = 'scale(' + scale + ')';

        if (progress >= 1) {{
          // avançar para próximo segmento
          currentSegmentIndex++;
          if (currentSegmentIndex >= seq.length) {{
            // fim do ciclo
            currentCycle++;
            if (currentCycle >= cycles) {{
              // fim da prática
              breathingRunning = false;
              paused = false;
              setLog('Prática concluída');
              setStatus('Concluído');
              circle.style.animation = 'prana_pulse_{escaped_fname} 2000ms ease-in-out infinite';
              if (raf) cancelAnimationFrame(raf);
              raf = null;
              return;
            }} else {{
              // próximo ciclo: reinicia segmentos
              currentSegmentIndex = 0;
            }}
          }}
          // iniciar próximo segmento
          segmentStart = performance.now();
        }}

        raf = requestAnimationFrame(animateFrameLoop);
      }}

      // inicia ou retoma a contagem cliente
      function startClientBreathing() {{
        if (breathingRunning && !paused) return;
        if (!breathingRunning) {{
          // iniciar do começo
          breathingRunning = true;
          paused = false;
          currentCycle = 0;
          currentSegmentIndex = 0;
          segmentStart = performance.now();
          circle.style.animation = 'none';
          setLog('Iniciando prática');
          playBtn.textContent = '⏸️ Pausar';
          setStatus('Tocando');
          raf = requestAnimationFrame(animateFrameLoop);
        }} else if (breathingRunning && paused) {{
          // retomar
          paused = false;
          // ajustar segmentStart para compensar o tempo em pausa
          segmentStart = performance.now() - (pausedElapsed || 0);
          setLog('Retomando prática');
          playBtn.textContent = '⏸️ Pausar';
          setStatus('Tocando');
          raf = requestAnimationFrame(animateFrameLoop);
        }}
      }}

      // pausa a contagem cliente
      let pauseTime = 0;
      let pausedElapsed = 0;
      function pauseClientBreathing() {{
        if (!breathingRunning || paused) return;
        paused = true;
        pauseTime = performance.now();
        // compute elapsed in current segment to resume later
        pausedElapsed = pauseTime - segmentStart;
        setLog('Pausado');
        setStatus('Pausado');
        playBtn.textContent = '▶️ Iniciar / Pausar';
        if (raf) cancelAnimationFrame(raf);
        raf = null;
      }}

      // para e reseta a contagem cliente
      function stopClientBreathing() {{
        breathingRunning = false;
        paused = false;
        currentCycle = 0;
        currentSegmentIndex = 0;
        segmentStart = 0;
        pausedElapsed = 0;
        setLog('');
        setStatus('Parado');
        playBtn.textContent = '▶️ Iniciar / Pausar';
        circle.style.animation = 'prana_pulse_{escaped_fname} 2000ms ease-in-out infinite';
        if (raf) cancelAnimationFrame(raf);
        raf = null;
      }}

      // Botão Iniciar / Pausar controla apenas o cliente
      playBtn.addEventListener('click', async () => {{
        try {{
          if (!breathingRunning) {{
            startClientBreathing();
          }} else {{
            if (paused) {{
              // retomar
              // recompute segmentStart so that pausedElapsed is respected
              segmentStart = performance.now() - (pausedElapsed || 0);
              paused = false;
              setLog('Retomando prática');
              setStatus('Tocando');
              playBtn.textContent = '⏸️ Pausar';
              raf = requestAnimationFrame(animateFrameLoop);
            }} else {{
              // pausar
              pauseClientBreathing();
            }}
          }}
        }} catch (err) {{
          console.warn('Erro no playBtn handler', err);
          setStatus('Erro interno');
        }}
      }});

      // Botão Parar
      stopBtn.addEventListener('click', () => {{
        try {{
          stopClientBreathing();
        }} catch (err) {{
          console.warn('Erro no stopBtn handler', err);
          setStatus('Erro interno');
        }}
      }});

      // clique na esfera também alterna play/pause
      circle.addEventListener('click', () => {{
        playBtn.click();
      }});

      // Inicialização visual
      setStatus('Pronto');
      setLog('Pronto para iniciar. A esfera seguirá o ciclo de respiração definido.');

}})();
</script>
"""

    st.components.v1.html(html_sync, height=520)

else:
    # se não houver áudio para a prática selecionada, apenas mostra instruções
    if intent != "Respiração guiada":
        st.info("Esta prática não possui áudio associado. Use as instruções na tela para guiar a respiração.")
    else:
        st.warning(f"Áudio de sessão não encontrado: {session_path}")

# ---------------------------------------------------------
# Rodapé: instruções rápidas, segurança e saúde
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Aviso de segurança e saúde:**  
- Este conteúdo é apenas para fins informativos e de bem‑estar geral; não substitui orientação médica ou terapêutica profissional.  
- Interrompa a prática imediatamente se sentir tontura, dor no peito, falta de ar intensa, náusea, desorientação ou qualquer desconforto significativo.  
- Ajuste os tempos de respiração conforme seu conforto; não force retenções ou respirações além do que é confortável para você.
"""
)