# 08_pranaterapia.py (refatorado: player + esfera sincronizados)
import time
from pathlib import Path
import base64

import streamlit as st

# -------------------------
# Configuração inicial
# -------------------------
st.set_page_config(page_title="Pranaterapia", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
    "Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital). "
    "Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença."
)
st.caption(
    "Integra respiração, som e visual para harmonizar o seu ser. Escolha um chakra para aplicar um preset e iniciar a prática."
)

# -------------------------
# Presets por chakra
# -------------------------
CHAKRAS = {
    "Muladhara": {"color": "#CC0700", "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Estou seguro e enraizado."},
    "Svadhisthana": {"color": "#6A0F60", "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6}, "affirmation": "Minha criatividade flui."},
    "Manipura": {"color": "#F17C0F", "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8}, "affirmation": "Ação com clareza."},
    "Anahata": {"color": "#3DAE27", "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Abro meu coração."},
    "Vishuddha": {"color": "#346CDB", "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Comunico com verdade."},
    "Ajna": {"color": "#F4E922", "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Minha percepção se afina."},
    "Sahasrara": {"color": "#DF27C3", "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4}, "affirmation": "Conecto-me ao silêncio."},
}

# -------------------------
# Paths
# -------------------------
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_ROOT = PROJECT_ROOT / "static"
SESSIONS_DIR = STATIC_ROOT / "audio" / "sessions"

# -------------------------
# Sidebar e controles
# -------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]
autoplay_flag = st.sidebar.checkbox("Autoplay ao iniciar (cliente)", value=False)

preset = theme["preset"]
inhale = st.sidebar.number_input("Inspire (s)", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold1 = st.sidebar.number_input("Segure após inspirar (s)", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5)
exhale = st.sidebar.number_input("Expire (s)", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5)
hold2 = st.sidebar.number_input("Segure após expirar (s)", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5)
cycles = st.sidebar.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# -------------------------
# Session state
# -------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# -------------------------
# Helpers
# -------------------------
@st.cache_data
def load_wav_bytes(path: str):
    p = Path(path)
    if not p.exists():
        return None
    return p.read_bytes()

def bytes_to_data_url(b: bytes, mime: str = "audio/wav"):
    import base64
    return f"data:{mime};base64," + base64.b64encode(b).decode("ascii")

# -------------------------
# Função que gera o HTML unificado (player + esfera sincronizados)
# -------------------------
def build_unified_player(url: str, color: str, uid: str = "default", autoplay: bool = False) -> str:
    sid = uid.replace(" ", "_").lower()
    # autoplay_attr será usado para tentar tocar automaticamente quando a flag do servidor estiver ativa
    autoplay_attr = "autoplay" if autoplay else ""
    # controls visíveis para fallback/diagnóstico; crossorigin e playsinline para compatibilidade
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <!-- Controles em primeiro plano -->
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <button id="startBtn_{sid}" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">▶️ Iniciar</button>
    <button id="stopBtn_{sid}" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">⏹️ Parar</button>
    <div id="status_{sid}" style="margin-left:12px;font-weight:600;color:#333">Preparar...</div>
  </div>

  <!-- Elemento de áudio principal (controls visíveis) -->
  <audio id="sessionAudio_{sid}" preload="auto" controls playsinline crossorigin="anonymous" style="width:100%;max-width:640px;" {autoplay_attr}>
    <source src="{url}" type="audio/wav">
    Seu navegador não suporta o elemento de áudio.
  </audio>

  <!-- Esfera visual -->
  <div id="circleWrap_{sid}" style="display:flex;flex-direction:column;align-items:center;margin-top:12px;">
    <div id="circle_{sid}" style="
      width:180px;height:180px;border-radius:50%;
      background:radial-gradient(circle at 30% 30%, #fff8, {color});
      box-shadow:0 12px 36px rgba(0,0,0,0.08);
      transform-origin:center;
      animation: initialPulse_{sid} 2000ms ease-in-out infinite;
      ">
    </div>
  </div>

  <style>
    @keyframes initialPulse_{sid} {{
      0% {{ transform: scale(1); opacity: 0.98; }}
      50% {{ transform: scale(1.04); opacity: 1; }}
      100% {{ transform: scale(1); opacity: 0.98; }}
    }}
  </style>

  <script>
  (function(){{
    try {{
      const audio = document.getElementById('sessionAudio_{sid}');
      const startBtn = document.getElementById('startBtn_{sid}');
      const stopBtn = document.getElementById('stopBtn_{sid}');
      const status = document.getElementById('status_{sid}');
      const circle = document.getElementById('circle_{sid}');

      function setStatus(t){{ status.textContent = t; }}
      function animateByAudio() {{
        if (!audio || audio.paused) return;
        const t = audio.currentTime || 0;
        const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
        circle.style.transform = 'scale(' + scale + ')';
        requestAnimationFrame(animateByAudio);
      }}

      // play/pause/ended sincronizam a esfera
      audio.addEventListener('play', () => {{
        circle.style.animation = 'none';
        setStatus('Tocando');
        requestAnimationFrame(animateByAudio);
      }});
      audio.addEventListener('pause', () => {{
        setStatus('Pausado');
        circle.style.animation = 'initialPulse_{sid} 2000ms ease-in-out infinite';
      }});
      audio.addEventListener('ended', () => {{
        setStatus('Concluído');
        circle.style.animation = 'initialPulse_{sid} 2000ms ease-in-out infinite';
      }});

      // botões que controlam o mesmo elemento <audio>
      startBtn.addEventListener('click', async () => {{
        try {{
          await audio.play();
          setStatus('Tocando');
        }} catch (e) {{
          console.warn('play failed', e);
          setStatus('Clique no controle nativo para tocar');
        }}
      }});
      stopBtn.addEventListener('click', () => {{
        try {{
          audio.pause();
          audio.currentTime = 0;
          setStatus('Parado');
          circle.style.animation = 'initialPulse_{sid} 2000ms ease-in-out infinite';
        }} catch (e) {{
          console.warn('stop error', e);
        }}
      }});

      // se a página for re-renderizada com a intenção de tocar (server-side), tentamos play()
      // o atributo autoplay pode já ter sido adicionado; aqui tentamos novamente para garantir
      try {{
        if (audio && {str(autoplay).lower()}) {{
          audio.play().catch(err => {{
            console.warn('autoplay attempt blocked', err);
          }});
        }}
      }} catch(e){{/* ignore */}}

      audio.addEventListener('error', () => {{
        const err = audio.error;
        console.warn('audio error code:', err && err.code, err);
        setStatus('Erro no áudio (veja console)');
      }});
    }} catch (err) {{
      console.error('Player init error:', err);
    }}
  }})();
  </script>
</div>
"""

# -------------------------
# Calcular session_path
# -------------------------
session_filename = f"{chakra.lower()}_session.wav"
session_path = SESSIONS_DIR / session_filename

# -------------------------
# Interface principal
# -------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# -------------------------
# Controles de prática (servidor)
# -------------------------
intent = st.selectbox("Prática", options=["Respiração guiada", "Respiração quadrada (Box Breathing)", "Respiração alternada (Nadi Shodhana)"])
col_start, col_stop = st.columns([1, 1])
with col_start:
    start_btn = st.button("▶️ Iniciar prática")
with col_stop:
    stop_btn = st.button("⏹️ Parar prática")

if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.playing = False
    st.success("Prática interrompida. Aguarde a atualização da interface.")

# -------------------------
# Função de ciclo de respiração (servidor)
# -------------------------
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

# -------------------------
# Quando o usuário clica em Start (servidor), marcamos playing e executamos a prática
# -------------------------
if start_btn:
    st.session_state.stop_flag = False
    st.session_state.playing = True

    if intent == "Respiração guiada":
        breathing_cycle(inhale, hold1, exhale, hold2, cycles=int(cycles))
    elif intent == "Respiração quadrada (Box Breathing)":
        st.subheader("🟦 Respiração quadrada (Box Breathing)")
        st.markdown("""
            Técnica usada para foco, estabilidade emocional e redução de ansiedade.
            **Ciclo sugerido:**
            - Inspire: 4s
            - Segure: 4s
            - Expire: 4s
            - Segure: 4s
            - 5 ciclos
        """)
        breathing_cycle(4, 4, 4, 4, cycles=5)
    elif intent == "Respiração alternada (Nadi Shodhana)":
        st.subheader("🔄 Respiração alternada (Nadi Shodhana)")
        st.markdown("""
            Técnica tradicional para equilibrar os canais energéticos (nadis) e acalmar a mente.
            Instruções guiadas (manual) — use o botão Parar para interromper.
        """)
        st.info("Esta técnica é guiada por instruções, não por contagem automática.")

# -------------------------
# PLAYER + ESFERA + fallback st.audio (se arquivo pequeno)
# -------------------------
uid = chakra
if session_path.exists():
    url = f"/static/audio/sessions/{session_path.name}"

    # se o servidor marcou playing, tentamos autoplay no componente (autoplay flag)
    autoplay_for_component = st.session_state.playing or autoplay_flag

    # renderiza o player unificado (player em primeiro plano, esfera abaixo)
    st.components.v1.html(build_unified_player(url, theme["color"], uid=uid, autoplay=autoplay_for_component), height=520)

    # fallback: st.audio apenas para arquivos pequenos (opcional)
    try:
        size_bytes = session_path.stat().st_size
    except Exception:
        size_bytes = None

    MAX_ST_AUDIO_BYTES = 5 * 1024 * 1024
    if size_bytes is not None and size_bytes <= MAX_ST_AUDIO_BYTES:
        try:
            st.audio(str(session_path))
        except Exception:
            st.info("Fallback st.audio falhou; use o player acima para tocar o áudio.")
    else:
        st.info("Usando player por URL (clique em Iniciar). Arquivo grande — st.audio não foi usado como fallback.")
else:
    st.warning(f"Áudio de sessão não encontrado: {session_path}")

# -------------------------
# Rodapé
# -------------------------
st.markdown("---")
st.caption(
    """
Aviso de segurança e saúde:
- Este conteúdo é apenas para fins informativos e de bem‑estar geral; não substitui orientação médica.
- Interrompa a prática se sentir tontura, dor no peito, falta de ar intensa ou desconforto significativo.
- Ajuste os tempos conforme seu conforto; não force retenções.
"""
)