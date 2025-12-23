# 08_pranaterapia.py (integrado: st.audio dispara player visual e esfera)
import time
from pathlib import Path
import base64
from html import escape

import streamlit as st

# ---------------------------------------------------------
# Configuração inicial
# ---------------------------------------------------------
st.title("Pranaterapia 🌬️")
st.markdown(
    "Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital). "
    "Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença."
)
st.caption(
    "Integra respiração, som e visual para harmonizar o seu ser. Escolha um chakra para aplicar um preset e iniciar a prática."
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
# Sidebar e controles
# ---------------------------------------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]
autoplay_flag = False

preset = theme["preset"]
inhale = st.sidebar.number_input("Inspire (s)", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold1 = st.sidebar.number_input("Segure após inspirar (s)", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5)
exhale = st.sidebar.number_input("Expire (s)", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5)
hold2 = st.sidebar.number_input("Segure após expirar (s)", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5)
cycles = st.sidebar.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
@st.cache_data
def load_wav_bytes(path: str):
    p = Path(path)
    if not p.exists():
        return None
    return p.read_bytes()

# ---------------------------------------------------------
# Interface principal
# ---------------------------------------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Controles principais: escolha de prática e botões Iniciar / Parar (servidor)
# ---------------------------------------------------------
intent = st.selectbox(
    "Prática",
    options=[
        "Respiração guiada",
        "Respiração quadrada (Box Breathing)",
        "Respiração alternada (Nadi Shodhana)",
    ],
)

col_start, col_stop = st.columns([1, 1])
with col_start:
    start_btn = st.button("▶️ Iniciar prática")
with col_stop:
    stop_btn = st.button("⏹️ Parar prática")

if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.playing = False
    st.success("Prática interrompida. Aguarde a atualização da interface.")

# ---------------------------------------------------------
# Função de ciclo de respiração (servidor)
# ---------------------------------------------------------
def breathing_cycle(inhale_s, hold1_s, exhale_s, hold2_s, cycles=5):
    st.session_state.stop_flag = False
    placeholder = st.empty()
    total_time = (inhale_s + hold1_s + exhale_s + hold2_s) * cycles
    elapsed = 0.0
    progress = st.progress(0)
    for c in range(int(cycles)):
        if st.session_state.stop_flag:
            placeholder.markdown("### ⏹️ Prática interrompida.")
            return
        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inhale_s}s**")
        full = int(inhale_s)
        rem = inhale_s - full
        for _ in range(full):
            if st.session_state.stop_flag:
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem); elapsed += rem; progress.progress(min(1.0, elapsed / total_time))

        if hold1_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1_s}s**")
            full = int(hold1_s); rem = hold1_s - full
            for _ in range(full):
                if st.session_state.stop_flag:
                    placeholder.markdown("### ⏹️ Prática interrompida."); return
                time.sleep(1); elapsed += 1; progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem); elapsed += rem; progress.progress(min(1.0, elapsed / total_time))

        placeholder.markdown(f"### 💨 Expire por **{exhale_s}s**")
        full = int(exhale_s); rem = exhale_s - full
        for _ in range(full):
            if st.session_state.stop_flag:
                placeholder.markdown("### ⏹️ Prática interrompida."); return
            time.sleep(1); elapsed += 1; progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem); elapsed += rem; progress.progress(min(1.0, elapsed / total_time))

        if hold2_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2_s}s**")
            full = int(hold2_s); rem = hold2_s - full
            for _ in range(full):
                if st.session_state.stop_flag:
                    placeholder.markdown("### ⏹️ Prática interrompida."); return
                time.sleep(1); elapsed += 1; progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem); elapsed += rem; progress.progress(min(1.0, elapsed / total_time))

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
    progress.progress(1.0)

# ---------------------------------------------------------
# Fluxo principal das práticas (servidor)
# ---------------------------------------------------------
if start_btn:
    st.session_state.stop_flag = False
    st.session_state.playing = True

    if intent == "Respiração guiada":
        breathing_cycle(inhale, hold1, exhale, hold2, cycles=int(cycles))
    elif intent == "Respiração quadrada (Box Breathing)":
        st.subheader("🟦 Respiração quadrada (Box Breathing)")
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
        breathing_cycle(4, 4, 4, 4, cycles=5)
    elif intent == "Respiração alternada (Nadi Shodhana)":
        st.subheader("🔄 Respiração alternada (Nadi Shodhana)")
        st.markdown(
            """
            Técnica tradicional para equilibrar os canais energéticos (nadis) e acalmar a mente.
            Instruções guiadas (manual) — use o botão Parar para interromper.
            """
        )
        st.info("Esta técnica é guiada por instruções, não por contagem automática.")

# ---------------------------------------------------------
# Localizar e renderizar o áudio (st.audio) e sincronizar com esfera
# ---------------------------------------------------------
session_filename = f"{chakra.lower()}_session.wav"
session_path = SESSIONS_DIR / session_filename

if session_path.exists():
    # 1) Renderiza st.audio (Streamlit serve internamente)
    try:
        st.audio(str(session_path))
    except Exception as e:
        st.error(f"Erro ao renderizar st.audio: {e}")
        st.stop()

    # 2) Injeta componente que encontra o <audio> criado por st.audio e sincroniza a esfera
    fname = session_path.name  # ex: "ajna_session.wav"
    escaped_fname = escape(fname)
    color = theme["color"]

    html_sync = f"""
<div id="prana_sync_{escaped_fname}" style="display:flex;flex-direction:column;align-items:center;margin-top:12px;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <button id="prana_start_{escaped_fname}" style="padding:8px 12px;border-radius:6px;">▶️ Iniciar</button>
    <button id="prana_stop_{escaped_fname}" style="padding:8px 12px;border-radius:6px;">⏹️ Parar</button>
    <div id="prana_status_{escaped_fname}" style="margin-left:12px;font-weight:600;">Pronto</div>
  </div>

  <div id="prana_circle_wrap_{escaped_fname}" style="display:flex;flex-direction:column;align-items:center;">
    <div id="prana_circle_{escaped_fname}" style="
      width:180px;height:180px;border-radius:50%;
      background:radial-gradient(circle at 30% 30%, #fff8, {color});
      box-shadow:0 12px 36px rgba(0,0,0,0.08);
      transform-origin:center;
      animation: prana_initial_pulse_{escaped_fname} 2000ms ease-in-out infinite;
      ">
    </div>
  </div>

  <style>
    @keyframes prana_initial_pulse_{escaped_fname} {{
      0% {{ transform: scale(1); opacity: 0.98; }}
      50% {{ transform: scale(1.04); opacity: 1; }}
      100% {{ transform: scale(1); opacity: 0.98; }}
    }}
  </style>
</div>

<script>
(function(){{
  function findAudioByFilename(fname) {{
    const audios = Array.from(document.querySelectorAll('audio'));
    for (const a of audios) {{
      try {{
        if (a.currentSrc && a.currentSrc.indexOf(fname) !== -1) return a;
        if (a.src && a.src.indexOf(fname) !== -1) return a;
      }} catch(e){{ }}
    }}
    return null;
  }}

  const fname = "{escaped_fname}";
  const statusEl = document.getElementById('prana_status_' + fname);
  const startBtn = document.getElementById('prana_start_' + fname);
  const stopBtn = document.getElementById('prana_stop_' + fname);
  const circle = document.getElementById('prana_circle_' + fname);

  let audio = findAudioByFilename(fname);

  if (!audio) {{
    const obs = new MutationObserver((mutations, observer) => {{
      audio = findAudioByFilename(fname);
      if (audio) {{
        observer.disconnect();
        initWithAudio(audio);
      }}
    }});
    obs.observe(document.body, {{ childList: true, subtree: true }});
  }} else {{
    initWithAudio(audio);
  }}

  function initWithAudio(audioEl) {{
    function setStatus(t) {{ if (statusEl) statusEl.textContent = t; }}
    let raf = null;

    function animate() {{
      if (!audioEl || audioEl.paused) {{
        if (raf) cancelAnimationFrame(raf);
        raf = null;
        return;
      }}
      const t = audioEl.currentTime || 0;
      const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
      circle.style.transform = 'scale(' + scale + ')';
      raf = requestAnimationFrame(animate);
    }}

    audioEl.addEventListener('play', () => {{
      circle.style.animation = 'none';
      setStatus('Tocando');
      requestAnimationFrame(animate);
    }});

    audioEl.addEventListener('pause', () => {{
      setStatus('Pausado');
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      circle.style.animation = 'prana_initial_pulse_{escaped_fname} 2000ms ease-in-out infinite';
    }});

    audioEl.addEventListener('ended', () => {{
      setStatus('Concluído');
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      circle.style.animation = 'prana_initial_pulse_{escaped_fname} 2000ms ease-in-out infinite';
    }});

    audioEl.addEventListener('error', () => {{
      setStatus('Erro no áudio (veja console)');
      console.warn('audio error', audioEl.error);
    }});

    startBtn.addEventListener('click', async () => {{
      try {{
        await audioEl.play();
        setStatus('Tocando');
      }} catch (e) {{
        console.warn('play failed', e);
        setStatus('Clique no controle nativo para tocar');
      }}
    }});

    stopBtn.addEventListener('click', () => {{
      try {{
        audioEl.pause();
        audioEl.currentTime = 0;
        setStatus('Parado');
        circle.style.animation = 'prana_initial_pulse_{escaped_fname} 2000ms ease-in-out infinite';
      }} catch (e) {{
        console.warn('stop error', e);
      }}
    }});

    try {{
      const shouldPlay = {str(bool(st.session_state.get('playing', False))).lower()};
      if (shouldPlay) {{
        audioEl.play().catch(err => console.warn('autoplay blocked', err));
      }}
    }} catch(e){{ }}
  }}
}})();
</script>
"""

    st.components.v1.html(html_sync, height=380)

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