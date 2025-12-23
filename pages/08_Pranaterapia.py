# 08_pranaterapia.py
import streamlit as st
import time
import base64
from pathlib import Path

st.title("🌬️ Pranaterapia")
st.markdown(
    """ Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital). Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença. """
)
st.caption(
    """ Integra respiração, som e visual para harmonizar o seu ser. Escolha um chakra para aplicar um preset e iniciar a prática. """
)

# -------------------------
# Presets por chakra (nomes em sânscrito)
# -------------------------
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

# -------------------------
# Paths para assets de áudio (sessões e fases)
# -------------------------
from pathlib import Path
import streamlit as st

# BASE_DIR assume que este arquivo está em <project>/pages
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent

# STATIC_ROOT deve apontar para a pasta static na raiz do projeto
STATIC_ROOT = PROJECT_ROOT / "static"

# diretório onde ficam os áudios de sessão
SESSIONS_DIR = STATIC_ROOT / "audio" / "sessions"

# -------------------------
# Sidebar: controles (sempre no sidebar)
# -------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra ", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]
# único modo: Sessão única (arquivo)
autoplay = st.sidebar.checkbox("Autoplay ao iniciar", value=True)

# -------------------------
# Helpers: carregar bytes de arquivo local com cache
# -------------------------
@st.cache_data
def load_wav_from_path(path: str):
    p = Path(path)
    if not p.exists():
        return None
    return p.read_bytes()

def wav_bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")


# -------------------------
# Uso integrado no fluxo
# -------------------------
# garantir flags
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# localizar arquivo de sessão
session_path = SESSIONS_DIR / f"{chakra.lower()}_session.wav"

# renderizar player sempre que o arquivo existir (esfera visível imediatamente)
if session_path.exists():
    url = f"/static/audio/sessions/{session_path.name}"
    html = build_synced_html_from_url(url, color=CHAKRAS[chakra]["color"], label_prefix=f"{chakra} — ")
    st.components.v1.html(html, height=300)  # ajuste height se necessário

    # fallback st.audio apenas para arquivos pequenos
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
    st.info("Áudio de sessão não encontrado.")

# -------------------------
# Interface principal
# -------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(
    f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>",
    unsafe_allow_html=True,
)

# localizar arquivo de sessão automaticamente (apenas session_path)
session_path = SESSIONS_DIR / f"{chakra.lower()}_session.wav"

preset = theme["preset"]

# controles de tempo no sidebar (visíveis e editáveis)
inhale = st.sidebar.number_input(
    "Inspire", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5
)
hold1 = st.sidebar.number_input(
    "Segure após inspirar", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5
)
exhale = st.sidebar.number_input(
    "Expire", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5
)
hold2 = st.sidebar.number_input(
    "Segure após expirar", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5
)
cycles = st.sidebar.number_input(
    "Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1
)

# -------------------------
# Função: player manual com esfera animada
# -------------------------
def build_synced_html_from_url(url: str, color: str, label_prefix: str = "") -> str:
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;font-family:Inter,system-ui,Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <div style="display:flex;gap:8px;align-items:center;margin-bottom:8px;">
    <button id="startBtn" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">▶️ Iniciar (clique)</button>
    <button id="stopBtn" style="padding:8px 12px;border-radius:6px;border:1px solid #ddd;background:#fff;cursor:pointer">⏹️ Parar</button>
    <div id="status" style="margin-left:12px;font-weight:600;color:#333">{label_prefix}Preparar...</div>
  </div>

  <div id="animWrap" style="display:flex;flex-direction:column;align-items:center;">
    <div id="circle" style="
      width:160px;height:160px;border-radius:50%;
      background:radial-gradient(circle at 30% 30%, #fff8, {color});
      box-shadow:0 12px 36px rgba(0,0,0,0.08);
      transform-origin:center;
      animation: initialPulse 2000ms ease-in-out infinite;
      ">
    </div>
    <div id="log" style="margin-top:10px;font-size:12px;color:#666;min-height:18px"></div>
  </div>

  <audio id="sessionAudio" src="{url}" preload="auto" style="display:none"></audio>

  <style>
    @keyframes initialPulse {{
      0% {{ transform: scale(1); opacity: 0.98; }}
      50% {{ transform: scale(1.04); opacity: 1; }}
      100% {{ transform: scale(1); opacity: 0.98; }}
    }}
  </style>
</div>

<script>
(function(){{
  try {{
    const audio = document.getElementById('sessionAudio');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const circle = document.getElementById('circle');
    const status = document.getElementById('status');
    const log = document.getElementById('log');

    if (!audio || !circle || !startBtn || !stopBtn) {{
      console.warn('Player elements missing; skipping player init.');
      return;
    }}

    function setStatus(text){{ status.textContent = text; }}
    function addLog(msg){{ log.textContent = msg; console.log(msg); }}

    let raf = null;
    function animateByAudio() {{
      if (audio.paused) {{
        if (raf) cancelAnimationFrame(raf);
        raf = null;
        return;
      }}
      const t = audio.currentTime || 0;
      const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
      circle.style.transform = `scale(${{scale}})`;
      raf = requestAnimationFrame(animateByAudio);
    }}

    audio.addEventListener('play', () => {{
      circle.style.animation = 'none';
      setStatus('Sessão em andamento');
      animateByAudio();
      addLog('audio play');
    }});

    audio.addEventListener('pause', () => {{
      setStatus('Pausado');
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      addLog('audio pause');
    }});

    audio.addEventListener('ended', () => {{
      setStatus('Concluído');
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      addLog('audio ended');
    }});

    startBtn.addEventListener('click', async () => {{
      try {{
        await audio.play();
      }} catch (e) {{
        addLog('play failed: ' + (e && e.name) + ' - ' + (e && e.message));
      }}
    }});

    stopBtn.addEventListener('click', () => {{
      try {{
        audio.pause();
        audio.currentTime = 0;
        circle.style.animation = 'initialPulse 2000ms ease-in-out infinite';
        setStatus('Parado');
        addLog('stopped');
      }} catch (e) {{
        addLog('stop error: ' + (e && e.message));
      }}
    }});

    audio.addEventListener('error', () => addLog('audio error code: ' + (audio.error && audio.error.code)));
  }} catch (err) {{
    console.error('Player init error:', err);
  }}
}})();
</script>
"""

# -------------------------
# Session state flags e função de ciclo de respiração
# -------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

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
        # contar segundos inteiros
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

# -------------------------
# Controles principais: escolha de prática e botões Iniciar / Parar
# -------------------------
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

# ação de parar: sinaliza interrupção (não forçar rerun)
if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.playing = False
    st.success("Prática interrompida. Aguarde a atualização da interface.")

# fluxo principal (apenas práticas guiadas por contagem ou instrução)
if start_btn:
    st.session_state.stop_flag = False

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

# -------------------------
# Player: renderiza player manual com esfera + fallback st.audio
# -------------------------
if session_path.exists():
    # se o usuário clicou em Start e a intenção for a que usa áudio, marque playing
    if start_btn:
        st.session_state.playing = True

    # renderizar player quando marcado como playing (ou sempre renderizar se preferir)
    if st.session_state.playing:
        url = f"/static/audio/sessions/{session_path.name}"

        # renderiza o player customizado (requere clique do usuário para evitar bloqueio de autoplay)
        html = build_synced_html_from_url(url, color=CHAKRAS[chakra]["color"], label_prefix=f"{chakra} — ")
        st.components.v1.html(html, height=260)

        # fallback robusto: use st.audio apenas para arquivos pequenos (evita MediaFileStorageError)
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
    # se não existir arquivo de sessão, não renderiza player; opcionalmente exibe aviso
    pass

# -------------------------
# Rodapé: instruções rápidas, segurança e saúde
# -------------------------
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