# 08_pranaterapia.py
import streamlit as st
import time
import base64
from pathlib import Path

st.set_page_config(page_title="Pranaterapia", page_icon="🌬️", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
    """
Pranaterapia: práticas guiadas de respiração com áudio pré‑gravado (voz feminina, delicada).
Faça upload dos WAVs gerados pela IA (voz feminina) para cada chakra e reproduza sessões sincronizadas.
"""
)
st.caption("Carregue arquivos de áudio (WAV) para cada chakra ou um arquivo de sessão por chakra.")

# -------------------------
# Presets por chakra (nomes em sânscrito)
# -------------------------
CHAKRAS = {
    "Muladhara": {"color": "#D9534F", "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Estou seguro e enraizado."},
    "Svadhisthana": {"color": "#F39C12", "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6}, "affirmation": "Minha criatividade flui."},
    "Manipura": {"color": "#F1C40F", "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8}, "affirmation": "Ação com clareza."},
    "Anahata": {"color": "#27AE60", "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Abro meu coração."},
    "Vishuddha": {"color": "#3498DB", "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Comunico com verdade."},
    "Ajna": {"color": "#5B2C6F", "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Minha percepção se afina."},
    "Sahasrara": {"color": "#8E44AD", "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4}, "affirmation": "Conecto-me ao silêncio."},
}

st.subheader("1. Selecione o chakra e carregue o áudio")
chakra = st.selectbox("Chakra (sânscrito)", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]
st.markdown(f"**Foco:** {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# -------------------------
# Uploads: sessão única ou fases
# -------------------------
st.markdown("**Carregue os arquivos WAV** (voz feminina, delicada). Pode enviar um arquivo de sessão completo ou dois arquivos por fase (inhale/exhale).")
col1, col2 = st.columns(2)
with col1:
    session_file = st.file_uploader("Arquivo de sessão (opcional) — WAV", type=["wav"], key=f"session_{chakra}")
with col2:
    inhale_file = st.file_uploader("Inhale (opcional) — WAV", type=["wav"], key=f"inhale_{chakra}")
    exhale_file = st.file_uploader("Exhale (opcional) — WAV", type=["wav"], key=f"exhale_{chakra}")

# -------------------------
# Modo de reprodução
# -------------------------
st.subheader("2. Modo de reprodução")
mode = st.radio("Modo", ["Sessão única (arquivo)", "Sino + voz por fase (arquivos separados)", "Visual apenas"], index=0)
use_bell = st.checkbox("Usar sino suave antes de cada fala", value=True)
# controles manuais (inicializados com preset)
preset = theme["preset"]
inhale = st.number_input("Inspire (s)", value=float(preset["inhale"]), min_value=1.0, max_value=30.0, step=0.5)
hold1 = st.number_input("Segure após inspirar (s)", value=float(preset["hold1"]), min_value=0.0, max_value=30.0, step=0.5)
exhale = st.number_input("Expire (s)", value=float(preset["exhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold2 = st.number_input("Segure após expirar (s)", value=float(preset["hold2"]), min_value=0.0, max_value=30.0, step=0.5)
cycles = st.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# -------------------------
# Cache loader para bytes
# -------------------------
@st.cache_data
def load_bytes(uploaded_file):
    if uploaded_file is None:
        return None
    return uploaded_file.read()

# carregar bytes
session_bytes = load_bytes(session_file)
inhale_bytes = load_bytes(inhale_file)
exhale_bytes = load_bytes(exhale_file)

# -------------------------
# Função utilitária: base64 para embutir áudio no HTML
# -------------------------
def wav_bytes_to_base64(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

# -------------------------
# Função que monta HTML sincronizado (usa <audio> e JS)
# -------------------------
def build_synced_html(wav_b64: str, total_time: float, color: str, label_prefix: str = "") -> str:
    """
    Retorna HTML que cria um player <audio> com o WAV embutido e inicia animação sincronizada.
    Use para reproduzir um arquivo de sessão único.
    """
    html = f"""
<div style="display:flex;flex-direction:column;align-items:center;">
  <audio id="sessionAudio" src="data:audio/wav;base64,{wav_b64}" preload="auto" controls></audio>
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

  // Exemplo simples: enquanto o áudio toca, animar o círculo com base no tempo atual.
  // Para sessões geradas com marcas de tempo, você pode mapear audio.currentTime para fases.
  audio.onplay = () => setLabel("Sessão em andamento");
  audio.onended = () => setLabel("Concluído");

  // animação contínua suave enquanto o áudio toca
  let animId = null;
  function animate() {{
    if (audio.paused) {{
      if (animId) cancelAnimationFrame(animId);
      animId = null;
      return;
    }}
    const t = audio.currentTime % 2.0; // ciclo visual simples
    const scale = 1 + 0.25 * Math.sin((t / 2.0) * Math.PI * 2);
    circle.style.transform = `scale(${scale})`;
    animId = requestAnimationFrame(animate);
  }}

  audio.onplay = () => animate();
  audio.onpause = () => {{ if (animId) cancelAnimationFrame(animId); animId = null; }};
  audio.onended = () => {{ if (animId) cancelAnimationFrame(animId); animId = null; }};
}})();
</script>
"""
    return html

# -------------------------
# Função que monta HTML para tocar inhale/exhale sequencialmente (sino + voz por fase)
# -------------------------
def build_phase_player_html(inhale_b64: str, exhale_b64: str, inhale_s: float, exhale_s: float, cycles: int, color: str, use_bell: bool, label_prefix: str = "") -> str:
    """
    Cria HTML que toca inhale/exhale em sequência usando elementos <audio> e sincroniza animação.
    Recomendado quando você tem arquivos separados por fase.
    """
    bell_script = ""
    if use_bell:
        # bell: WebAudio simple ping
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

      if ({int(theme['preset']['hold1']>0)}) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, {int(hold1*1000)}));
      }}

      setLabel("Expire");
      if ({str(use_bell).lower()}) playBell(420,0.08,0.04);
      exhaleAudio.currentTime = 0;
      exhaleAudio.play();
      await new Promise(r => setTimeout(r, Math.max(500, {int(exhale_s*1000)})));

      if ({int(theme['preset']['hold2']>0)}) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, {int(hold2*1000)}));
      }}
    }}
    setLabel("Concluído");
  }}

  // iniciar automaticamente quando o HTML for renderizado
  runSequence();
}})();
</script>
"""
    return html

# -------------------------
# Ações: iniciar prática
# -------------------------
st.subheader("3. Iniciar prática")
start = st.button("▶️ Iniciar prática")
if start:
    if mode == "Sessão única (arquivo)":
        if session_bytes is None:
            st.error("Nenhum arquivo de sessão carregado. Faça upload de um WAV de sessão para este chakra.")
        else:
            b64 = wav_bytes_to_base64(session_bytes)
            html = build_synced_html(b64, total_time=(inhale+hold1+exhale+hold2)*cycles, color=theme["color"], label_prefix=chakra + " — ")
            st.components.v1.html(html, height=420)
    elif mode == "Sino + voz por fase (arquivos separados)":
        if inhale_bytes is None or exhale_bytes is None:
            st.error("Envie os arquivos de inhale e exhale para usar este modo.")
        else:
            b64_in = wav_bytes_to_base64(inhale_bytes)
            b64_ex = wav_bytes_to_base64(exhale_bytes)
            html = build_phase_player_html(b64_in, b64_ex, inhale, exhale, cycles, theme["color"], use_bell, label_prefix=chakra + " — ")
            st.components.v1.html(html, height=420)
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
# Segurança e instruções finais
# -------------------------
st.markdown("---")
st.subheader("Notas práticas e segurança")
st.markdown(
    """
- **Como preparar os WAVs:** gere clipes com voz feminina e delicada (frases curtas: "Inspire devagar e profundamente", "Expire devagar e completamente") e aplique fade in/out curto e normalização leve.  
- **Formato recomendado:** WAV mono, 22050–44100 Hz, 16‑bit.  
- **Sincronização:** para melhor sincronização use um arquivo de sessão único que já contenha todas as falas e pings na ordem correta. O app reproduz esse arquivo e a animação cliente‑lado é iniciada junto.  
- **Privacidade e custos:** se os WAVs foram gerados por um serviço de IA, verifique termos de uso e licenças.  
- **Contraindicações:** se tiver problemas respiratórios, cardíacos, pressão alta, gravidez ou qualquer condição médica, consulte um profissional antes de praticar.
"""
)
st.caption("Pranaterapia — práticas guiadas com áudio pré‑gravado (voz feminina, delicada).")