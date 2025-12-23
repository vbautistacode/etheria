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
BASE_DIR = Path(__file__).parent
SESSIONS_DIR = BASE_DIR / "static" / "audio" / "sessions"
PHASES_DIR = BASE_DIR / "static" / "audio" / "phases"

# -------------------------
# Sidebar: controles (sempre no sidebar)
# -------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra ", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]
# único modo: Sessão única (arquivo)
autoplay = st.sidebar.checkbox("Autoplay ao iniciar", value=True)


# BASE_DIR já definido no topo do arquivo
# BASE_DIR = Path(__file__).parent

# definir STATIC_ROOT apontando para a pasta static na raiz do projeto
STATIC_ROOT = BASE_DIR.parent / "static"

# agora que chakra foi selecionado no sidebar, monte o caminho do arquivo
session_path = STATIC_ROOT / "audio" / "sessions" / f"{chakra.lower()}_session.wav"

# debug seguro (apenas para desenvolvimento)
st.write("DEBUG session_path:", session_path)
st.write("exists:", session_path.exists())

# teste de reprodução robusto
if session_path.exists():
    st.audio(str(session_path))  # fallback confiável para testar reprodução
else:
    st.error("Arquivo não encontrado: " + str(session_path))



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
# Função que monta HTML sincronizado (usa <audio> e JS)
# -------------------------
def build_synced_html_from_url(url: str, color: str, label_prefix: str = "", autoplay_flag: bool = True) -> str:
    autoplay_attr = "autoplay" if autoplay_flag else ""
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <audio id="sessionAudio" src="{url}" preload="auto" controls {autoplay_attr}></audio>
  <div id="animWrap" style="margin-top:12px;display:flex;flex-direction:column;align-items:center;">
    <div id="circle" style="width:160px;height:160px;border-radius:50%;background:radial-gradient(circle at 30% 30%, #fff8, {color});box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;"></div>
    <div id="label" style="margin-top:12px;font-size:18px;font-weight:600;color:#222">{label_prefix}Preparar...</div>
  </div>
</div>
<script>
(function(){{
  const audio = document.getElementById('sessionAudio');
  const circle = document.getElementById('circle');
  const label = document.getElementById('label');

  function setLabel(text){{ label.textContent = text; }}

  audio.addEventListener('play', () => setLabel("Sessão em andamento"));
  audio.addEventListener('pause', () => setLabel("Pausado"));
  audio.addEventListener('ended', () => setLabel("Concluído"));

  let raf = null;
  function animate() {{
    if (audio.paused) {{
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      return;
    }}
    const t = audio.currentTime;
    const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
    // note: use ${{scale}} so Python f-string does not try to interpolate {scale}
    circle.style.transform = `scale(${{scale}})`;
    raf = requestAnimationFrame(animate);
  }}

  audio.addEventListener('play', () => animate());
  audio.addEventListener('pause', () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }});
  audio.addEventListener('ended', () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }});
}})();
</script>
"""

# -------------------------
# Função que monta HTML para tocar inhale/exhale sequencialmente (mantida para compatibilidade)
# -------------------------
def build_synced_html_from_url(url: str, color: str, label_prefix: str = "", autoplay_flag: bool = True) -> str:
    autoplay_attr = "autoplay" if autoplay_flag else ""
    return f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <audio id="sessionAudio" src="{url}" preload="auto" controls {autoplay_attr}></audio>
  <div id="animWrap" style="margin-top:12px;display:flex;flex-direction:column;align-items:center;">
    <div id="circle" style="width:160px;height:160px;border-radius:50%;background:radial-gradient(circle at 30% 30%, #fff8, {color});box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;"></div>
    <div id="label" style="margin-top:12px;font-size:18px;font-weight:600;color:#222">{label_prefix}Preparar...</div>
  </div>
</div>
<script>
(function(){{
  const audio = document.getElementById('sessionAudio');
  const circle = document.getElementById('circle');
  const label = document.getElementById('label');

  function setLabel(text){{ label.textContent = text; }}

  audio.addEventListener('play', () => setLabel("Sessão em andamento"));
  audio.addEventListener('pause', () => setLabel("Pausado"));
  audio.addEventListener('ended', () => setLabel("Concluído"));

  let raf = null;
  function animate() {{
    if (audio.paused) {{
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      return;
    }}
    const t = audio.currentTime;
    const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
    circle.style.transform = `scale(${{scale}})`;
    raf = requestAnimationFrame(animate);
  }}

  audio.addEventListener('play', () => animate());
  audio.addEventListener('pause', () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }});
  audio.addEventListener('ended', () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }});
}})();
</script>
"""
    return html

# -------------------------
# Interface principal
# -------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(
    f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>",
    unsafe_allow_html=True,
)

# localizar arquivos automaticamente
session_path = SESSIONS_DIR / f"{chakra.lower()}_session.wav"
inhale_path = PHASES_DIR / f"{chakra.lower()}_inhale.wav"
exhale_path = PHASES_DIR / f"{chakra.lower()}_exhale.wav"

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
# Session state flags e funções de controle
# -------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# função de ciclo de respiração (servidor)
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
# (removidos: "Sessão única" e modo por fases)
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
    # não chamar st.experimental_rerun() aqui — deixe o app reagir à flag
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

# Se o player estiver marcado como playing (por exemplo após rerun), renderize-o novamente
if st.session_state.playing:
    session_path = SESSIONS_DIR / f"{chakra.lower()}_session.wav"
    if session_path.exists():
        url = f"/static/audio/sessions/{session_path.name}"
        html = build_synced_html_from_url(url, color=CHAKRAS[chakra]["color"], label_prefix=f"{chakra} — ", autoplay_flag=autoplay)
        st.components.v1.html(html, height=460)
    else:
        st.error(f"Áudio de sessão não encontrado: {session_path}")

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