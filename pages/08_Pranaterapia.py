# 08_pranaterapia.py
import streamlit as st
import time 
import base64
from pathlib import Path

st.set_page_config(page_title="Pranaterapia", page_icon="🌬️", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
     """ Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital). Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença. """
)
st.caption(""" Nossa pranaterapia integra respiração, som e visual para harmonizar o seu ser. Escolha um chakra para aplicar um preset prático e iniciar a prática. """)

# -------------------------
# Presets por chakra (nomes em sânscrito)
# -------------------------
CHAKRAS = {
    "Muladhara": {"color": "#D9534F", "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Estou seguro e enraizado."},
    "Svadhisthana": {"color": "#6A0F60", "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6}, "affirmation": "Minha criatividade flui."},
    "Manipura": {"color": "#F17C0F", "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8}, "affirmation": "Ação com clareza."},
    "Anahata": {"color": "#3DAE27", "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Abro meu coração."},
    "Vishuddha": {"color": "#346CDB", "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Comunico com verdade."},
    "Ajna": {"color": "#F4E922", "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Minha percepção se afina."},
    "Sahasrara": {"color": "#DF27C3", "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4}, "affirmation": "Conecto-me ao silêncio."},
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
mode = st.sidebar.radio("Modo", ["Sessão única", "Sino + voz por fase", "Visual apenas"], index=0)
use_bell = st.sidebar.checkbox("Usar sino suave", value=True)
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
# Função que monta HTML sincronizado (usa <audio> e JS)
# -------------------------
def build_synced_html(wav_b64: str, color: str, label_prefix: str = "", autoplay_flag: bool = True) -> str:
    autoplay_attr = "autoplay" if autoplay_flag else ""
    html = f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <audio id="sessionAudio" src="data:audio/wav;base64,{wav_b64}" preload="auto" controls {autoplay_attr}></audio>
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

  audio.onplay = () => setLabel("Sessão em andamento");
  audio.onpause = () => setLabel("Pausado");
  audio.onended = () => setLabel("Concluído");

  let raf = null;
  function animate() {{
    if (audio.paused) {{
      if (raf) cancelAnimationFrame(raf);
      raf = null;
      return;
    }}
    const t = audio.currentTime;
    const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2);
    circle.style.transform = `scale(${scale})`;
    raf = requestAnimationFrame(animate);
  }}

  audio.onplay = () => animate();
  audio.onpause = () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }};
  audio.onended = () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }};
}})();
</script>
"""
    return html

# -------------------------
# Função que monta HTML para tocar inhale/exhale sequencialmente (sino + voz por fase)
# -------------------------
def build_phase_player_html(inhale_b64: str, exhale_b64: str, inhale_s: float, exhale_s: float, cycles: int, color: str, use_bell: bool, label_prefix: str = "") -> str:
    bell_script = ""
    if use_bell:
        bell_script = """
function playBell(freq=520, duration=0.08, volume=0.04) {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.type = 'sine';
    o.frequency.value = freq;
    g.gain.value = 0.0;
    o.connect(g);
    g.connect(ctx.destination);
    const now = ctx.currentTime;
    g.gain.linearRampToValueAtTime(volume, now + 0.01);
    g.gain.linearRampToValueAtTime(0.0, now + duration);
    o.start(now);
    o.stop(now + duration + 0.02);
    setTimeout(()=>{ try{ ctx.close(); }catch(e){} }, (duration+0.1)*1000);
  } catch(e) {}
}
"""
    html = f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <audio id="inhaleAudio" src="data:audio/wav;base64,{inhale_b64}" preload="auto"></audio>
  <audio id="exhaleAudio" src="data:audio/wav;base64,{exhale_b64}" preload="auto"></audio>
  <div id="animWrap" style="margin-top:12px;display:flex;flex-direction:column;align-items:center;">
    <div id="circle" style="width:160px;height:160px;border-radius:50%;background:radial-gradient(circle at 30% 30%, #fff8, {color});box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;"></div>
    <div id="label" style="margin-top:12px;font-size:18px;font-weight:600;color:#222">{label_prefix}Preparar...</div>
  </div>
</div>
<script>
(function(){{
  const inhaleAudio = document.getElementById('inhaleAudio');
  const exhaleAudio = document.getElementById('exhaleAudio');
  const circle = document.getElementById('circle');
  const label = document.getElementById('label');
  {bell_script}

  function setLabel(text){{ label.textContent = text; }}

  async function runSequence() {{
    for (let c=0; c < {cycles}; c++) {{
      setLabel("Inspire");
      if ({str(use_bell).lower()}) playBell(520,0.08,0.04);
      inhaleAudio.currentTime = 0;
      inhaleAudio.play();
      await new Promise(r => setTimeout(r, Math.max(500, {int(inhale_s*1000)})));

      if ({int(preset['hold1']>0)}) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, {int(hold1*1000)}));
      }}

      setLabel("Expire");
      if ({str(use_bell).lower()}) playBell(420,0.08,0.04);
      exhaleAudio.currentTime = 0;
      exhaleAudio.play();
      await new Promise(r => setTimeout(r, Math.max(500, {int(exhale_s*1000)})));

      if ({int(preset['hold2']>0)}) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, {int(hold2*1000)}));
      }}
    }}
    setLabel("Concluído");
  }}

  runSequence();
}})();
</script>
"""
    return html

# -------------------------
# Interface principal (sem upload)
# -------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# localizar arquivos automaticamente
session_path = SESSIONS_DIR / f"{chakra.lower()}_session.wav"
inhale_path = PHASES_DIR / f"{chakra.lower()}_inhale.wav"
exhale_path = PHASES_DIR / f"{chakra.lower()}_exhale.wav"

start = st.button("▶️ Iniciar prática")
if start:
    if mode == "Sessão única (arquivo)":
        wav_bytes = load_wav_from_path(str(session_path))
        if wav_bytes is None:
            st.error(f"Áudio de sessão não encontrado: {session_path}. Coloque o arquivo em static/audio/sessions/ com o nome correto.")
        else:
            b64 = wav_bytes_to_base64(wav_bytes)
            html = build_synced_html(b64, color=theme["color"], label_prefix=chakra + " — ", autoplay_flag=autoplay)
            st.components.v1.html(html, height=460)
    elif mode == "Sino + voz por fase (arquivos separados)":
        inh_bytes = load_wav_from_path(str(inhale_path))
        exh_bytes = load_wav_from_path(str(exhale_path))
        if inh_bytes is None or exh_bytes is None:
            st.error(f"Arquivos de fase não encontrados. Verifique:\n{inhale_path}\n{exhale_path}")
        else:
            b64_in = wav_bytes_to_base64(inh_bytes)
            b64_ex = wav_bytes_to_base64(exh_bytes)
            html = build_phase_player_html(b64_in, b64_ex, inhale, exhale, cycles, theme["color"], use_bell, label_prefix=chakra + " — ")
            st.components.v1.html(html, height=460)
    else:
        # visual only: servidor faz contagem e animação textual
        placeholder = st.empty()
        total_time = (inhale + hold1 + exhale + hold2) * cycles
        elapsed = 0.0
        progress = st.progress(0)
        for c in range(int(cycles)):
            placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inhale}s**")
            time.sleep(inhale)
            elapsed += inhale
            progress.progress(min(1.0, elapsed / total_time))
            if hold1 > 0:
                placeholder.markdown(f"### ⏸️ Segure por **{hold1}s**")
                time.sleep(hold1)
                elapsed += hold1
                progress.progress(min(1.0, elapsed / total_time))
            placeholder.markdown(f"### 💨 Expire por **{exhale}s**")
            time.sleep(exhale)
            elapsed += exhale
            progress.progress(min(1.0, elapsed / total_time))
            if hold2 > 0:
                placeholder.markdown(f"### ⏸️ Segure por **{hold2}s**")
                time.sleep(hold2)
                elapsed += hold2
                progress.progress(min(1.0, elapsed / total_time))
        placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
        progress.progress(1.0)

# -------------------------
# Rodapé: instruções rápidas, segurança e saúde
# -------------------------
st.markdown("---")
st.markdown(
    """
**Aviso de segurança e saúde:**  
- Este conteúdo é apenas para fins informativos e de bem‑estar geral; **não substitui orientação médica ou terapêutica profissional**.  
- Se você tem condições médicas preexistentes (por exemplo, problemas cardíacos, hipertensão, asma, distúrbios respiratórios, epilepsia), está grávida, ou tem qualquer dúvida sobre praticar exercícios respiratórios, **consulte um profissional de saúde antes de usar**.  
- Interrompa a prática imediatamente se sentir tontura, dor no peito, falta de ar intensa, náusea, desorientação ou qualquer desconforto significativo. Procure atendimento médico se os sintomas persistirem.  
- Ajuste os tempos de respiração conforme seu conforto; não force retenções ou respirações além do que é confortável para você.  
- Use fones de ouvido em volume moderado; evite ambientes com risco de queda ou onde seja necessário atenção constante enquanto pratica.  
- Se estiver usando medicação que afete respiração, consciência ou pressão arterial, consulte seu médico antes de praticar.  

Pratique com atenção e cuide de si.
"""
)