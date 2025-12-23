# 08_pranaterapia.py
import time
import base64
from pathlib import Path

import streamlit as st

# ---------------------------------------------------------
# Título e descrição
# ---------------------------------------------------------
st.title("🌬️ Pranaterapia")
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
    "Muladhara": {
        "color": "#CC0700",
        "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6},
        "affirmation": "Estou seguro e enraizado.",
    },
    "Svadhisthana": {
        "color": "#6A0F60",
        "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6},
        "affirmation": "Minha criatividade flui.",
    },
    "Manipura": {
        "color": "#F17C0F",
        "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8},
        "affirmation": "Ação com clareza.",
    },
    "Anahata": {
        "color": "#3DAE27",
        "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6},
        "affirmation": "Abro meu coração.",
    },
    "Vishuddha": {
        "color": "#346CDB",
        "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5},
        "affirmation": "Comunico com verdade.",
    },
    "Ajna": {
        "color": "#F4E922",
        "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5},
        "affirmation": "Minha percepção se afina.",
    },
    "Sahasrara": {
        "color": "#DF27C3",
        "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4},
        "affirmation": "Conecto-me ao silêncio.",
    },
}

# ---------------------------------------------------------
# Diretórios (assume estrutura do projeto: <repo-root>/static/audio/sessions)
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_ROOT = PROJECT_ROOT / "static"
SESSIONS_DIR = STATIC_ROOT / "audio" / "sessions"

# ---------------------------------------------------------
# Sidebar: seleção e configurações
# ---------------------------------------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]

# controles de tempo (visíveis e editáveis)
preset = theme["preset"]
inhale = st.sidebar.number_input("Inspire (s)", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold1 = st.sidebar.number_input("Segure após inspirar (s)", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5)
exhale = st.sidebar.number_input("Expire (s)", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5)
hold2 = st.sidebar.number_input("Segure após expirar (s)", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5)
cycles = st.sidebar.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# ---------------------------------------------------------
# Helpers (cache leitura de arquivos)
# ---------------------------------------------------------
@st.cache_data
def load_wav_from_path(path: str):
    p = Path(path)
    if not p.exists():
        return None
    return p.read_bytes()


def wav_bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


# ---------------------------------------------------------
# Funções para gerar HTML do player e da esfera (IDs únicos por chakra)
# ---------------------------------------------------------
def build_player_html(url: str, color: str, label_prefix: str = "", uid: str = "default") -> str:
    """
    Player HTML com botões Iniciar/Parar e elemento <audio>.
    O UID garante IDs únicos se houver múltiplos players na página.
    """
    sid = uid.replace(" ", "_").lower()
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <button id="startBtn_{sid}" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">▶️ Iniciar</button>
    <button id="stopBtn_{sid}" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">⏹️ Parar</button>
    <div id="status_{sid}" style="margin-left:12px;font-weight:600;color:#333">{label_prefix}Preparar...</div>
  </div>

  <audio id="sessionAudio_{sid}" src="{url}" preload="auto" style="display:none"></audio>

  <script>
  (function(){{
    try {{
      const audio = document.getElementById('sessionAudio_{sid}');
      const startBtn = document.getElementById('startBtn_{sid}');
      const stopBtn = document.getElementById('stopBtn_{sid}');
      const status = document.getElementById('status_{sid}');

      if (!audio || !startBtn || !stopBtn) {{
        console.warn('Player elements missing; skipping init.');
        return;
      }}

      startBtn.addEventListener('click', async () => {{
        try {{
          await audio.play();
          status.textContent = 'Tocando';
        }} catch (e) {{
          status.textContent = 'Erro ao tocar';
          console.warn('play failed', e);
        }}
      }});

      stopBtn.addEventListener('click', () => {{
        try {{
          audio.pause();
          audio.currentTime = 0;
          status.textContent = 'Parado';
        }} catch (e) {{
          console.warn('stop error', e);
        }}
      }});

      audio.addEventListener('error', () => {{
        console.warn('audio error code:', audio.error && audio.error.code);
        status.textContent = 'Erro no áudio';
      }});
    }} catch (err) {{
      console.error('Player init error:', err);
    }}
  }})();
  </script>
</div>
"""


def build_circle_html(color: str, uid: str = "default") -> str:
    """
    Esfera visual separada (renderizada abaixo do player).
    A animação será controlada pelo player JS (quando o áudio tocar, o player JS pode manipular a esfera se necessário).
    """
    sid = uid.replace(" ", "_").lower()
    # Usar concatenação em JS para evitar que Python tente avaliar {scale} dentro da f-string
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <div id="circle_{sid}" style="
      width:180px;height:180px;border-radius:50%;
      background:radial-gradient(circle at 30% 30%, #fff8, {color});
      box-shadow:0 12px 36px rgba(0,0,0,0.08);
      transform-origin:center;
      animation: initialPulse_{sid} 2000ms ease-in-out infinite;
      margin-bottom:12px;
  "></div>
  <style>
    @keyframes initialPulse_{sid} {{
      0% {{ transform: scale(1); opacity: 0.98; }}
      50% {{ transform: scale(1.04); opacity: 1; }}
      100% {{ transform: scale(1); opacity: 0.98; }}
    }}
  </style>

  <script>
  (function(){{
    // sincronização simples: quando o áudio do player tocar, remove o pulso e aplica animação baseada no tempo
    try {{
      const audio = document.getElementById('sessionAudio_{sid}');
      const circle = document.getElementById('circle_{sid}');
      if (!audio || !circle) return;

      let raf = null;
      function animateByAudio() {{
        if (audio.paused) {{
          if (raf) cancelAnimationFrame(raf);
          raf = null;
          return;
        }}
        const t = audio.currentTime || 0;
        const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
        // concatenação segura para evitar conflitos com f-strings Python
        circle.style.transform = 'scale(' + scale + ')';
        raf = requestAnimationFrame(animateByAudio);
      }}

      audio.addEventListener('play', () => {{
        circle.style.animation = 'none';
        animateByAudio();
      }});
      audio.addEventListener('pause', () => {{
        if (raf) cancelAnimationFrame(raf);
        raf = null;
        circle.style.animation = 'initialPulse_{sid} 2000ms ease-in-out infinite';
      }});
      audio.addEventListener('ended', () => {{
        if (raf) cancelAnimationFrame(raf);
        raf = null;
        circle.style.animation = 'initialPulse_{sid} 2000ms ease-in-out infinite';
      }});
    }} catch (e) {{
      console.warn('circle sync error', e);
    }}
  }})();
  </script>
</div>
"""

# ---------------------------------------------------------
# Inicializar session_state (flags únicas)
# ---------------------------------------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# ---------------------------------------------------------
# Calcular session_path de forma segura (após seleção do chakra)
# ---------------------------------------------------------
session_filename = f"{chakra.lower()}_session.wav"
session_path = SESSIONS_DIR / session_filename

# ---------------------------------------------------------
# Interface principal (texto e barra de cor)
# ---------------------------------------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(
    f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>",
    unsafe_allow_html=True,
)

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
    """Executa contagem no servidor com possibilidade de interrupção via st.session_state.stop_flag."""
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
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        if hold1_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1_s}s**")
            full = int(hold1_s)
            rem = hold1_s - full
            for _ in range(full):
                if st.session_state.stop_flag:
                    placeholder.markdown("### ⏹️ Prática interrompida.")
                    return
                time.sleep(1)
                elapsed += 1
                progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem)
                elapsed += rem
                progress.progress(min(1.0, elapsed / total_time))

        placeholder.markdown(f"### 💨 Expire por **{exhale_s}s**")
        full = int(exhale_s)
        rem = exhale_s - full
        for _ in range(full):
            if st.session_state.stop_flag:
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        if hold2_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2_s}s**")
            full = int(hold2_s)
            rem = hold2_s - full
            for _ in range(full):
                if st.session_state.stop_flag:
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
# Fluxo principal das práticas (servidor)
# ---------------------------------------------------------
if start_btn:
    st.session_state.stop_flag = False

    if intent == "Respiração guiada":
        # marca playing para indicar que o usuário iniciou a prática
        st.session_state.playing = True
        breathing_cycle(inhale, hold1, exhale, hold2, cycles=int(cycles))

    elif intent == "Respiração quadrada (Box Breathing)":
        st.session_state.playing = True
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
        st.session_state.playing = True
        st.subheader("🔄 Respiração alternada (Nadi Shodhana)")
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
            Repita por 6 ciclos.
            """
        )
        st.info("Esta técnica é guiada por instruções, não por contagem automática. Use o botão Parar para interromper a prática a qualquer momento.")


# ---------------------------------------------------------
# PLAYER (cliente) em primeiro plano, depois ESFERA, depois RENDER DO ÁUDIO (fallback)
# ---------------------------------------------------------
uid = chakra  # usado para gerar IDs únicos no HTML
if session_path.exists():
    url = f"/static/audio/sessions/{session_path.name}"

    # 1) Player HTML em primeiro plano (cliente)
    st.components.v1.html(build_player_html(url, theme["color"], f"{chakra} — ", uid=uid), height=120)

    # 2) Esfera logo abaixo (visual)
    st.components.v1.html(build_circle_html(theme["color"], uid=uid), height=240)

    # 3) Render do áudio (fallback) — apenas para arquivos pequenos
    try:
        size_bytes = session_path.stat().st_size
    except Exception:
        size_bytes = None

    MAX_ST_AUDIO_BYTES = 5 * 1024 * 1024  # 5 MB threshold
    if size_bytes is not None and size_bytes <= MAX_ST_AUDIO_BYTES:
        try:
            st.audio(str(session_path))
        except Exception:
            st.info("Fallback st.audio falhou; use o player acima para tocar o áudio.")
    else:
        st.info("Usando player por URL (clique em Iniciar). Arquivo grande — st.audio não foi usado como fallback.")
else:
    st.warning(f"Áudio de sessão não encontrado: {session_path}")

# ---------------------------------------------------------
# Rodapé: instruções rápidas, segurança e saúde
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Aviso de segurança e saúde:**  
- Este conteúdo é apenas para fins informativos e de bem‑estar geral; **não substitui orientação médica ou terapêutica profissional**.  
- Se você tem condições médicas preexistentes (por exemplo, problemas cardíacos, hipertensão, asma, distúrbios respiratórios, epilepsia), está grávida, ou tem qualquer dúvida sobre praticar exercícios respiratórios, **consulte um profissional de saúde antes de usar**.  
- Interrompa a prática imediatamente se sentir tontura, dor no peito, falta de ar intensa, náusea, desorientação ou qualquer desconforto significativo. Procure atendimento médico se os sintomas persistirem.  
- Ajuste os tempos de respiração conforme seu conforto; não force retenções ou respirações além do que é confortável para você.  
- Use fones de ouvido em volume moderado; evite ambientes com risco de queda ou onde seja necessário atenção constante enquanto pratica.  
- Se estiver usando medicação que afete respiração, consciência ou pressão arterial, consulte seu médico antes de praticar.  
- Para acessibilidade: disponibilize a transcrição do áudio (arquivo `.txt`) e ofereça modo visual apenas se preferir não ouvir o áudio.

Pratique com atenção e cuide de si.
"""
)

# ---------------------------------------------------------
# Observações rápidas (onde ajustar)
# - Para alterar o threshold do fallback st.audio, edite MAX_ST_AUDIO_BYTES.
# - Se quiser que o player tente autoplay no cliente, marque 'autoplay' no sidebar e adapte o JS.
# - Se os arquivos não estiverem sendo servidos via /static/, confirme que 'static/' está na raiz do repositório e que o app foi redeployado.
# ---------------------------------------------------------