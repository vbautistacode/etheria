# 08_pranaterapia.py
import streamlit as st
import time
import math
import io
import wave
import struct
from typing import Optional, Tuple, Dict

# -------------------------
# Página: Pranaterapia
# -------------------------
st.set_page_config(page_title="Pranaterapia", page_icon="🌬️", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
    """
A pranaterapia trabalha com práticas guiadas de respiração e presença para harmonizar o **prana** (energia vital).
Esta página oferece: práticas curtas por intenção, sessões longas, animação visual da respiração, áudio de apoio (sinais sonoros),
áudio guiado simples (tons) e integração temática (práticas inspiradas por planetas).
"""
)

# -------------------------
# Temas planetários (integração)
# -------------------------
PLANET_THEME: Dict[str, Dict[str, str]] = {
    "Default": {"label": "Padrão", "color": "#6C8EBF", "tone_freq": 440},
    "Sun": {"label": "Sol — Vitalidade", "color": "#F2C94C", "tone_freq": 523},
    "Moon": {"label": "Lua — Calma", "color": "#7FB3D5", "tone_freq": 392},
    "Mercury": {"label": "Mercúrio — Clareza", "color": "#9AD3BC", "tone_freq": 660},
    "Venus": {"label": "Vênus — Afeição", "color": "#F7A8B8", "tone_freq": 587},
    "Mars": {"label": "Marte — Energia", "color": "#E76F51", "tone_freq": 330},
    "Jupiter": {"label": "Júpiter — Expansão", "color": "#B59F3B", "tone_freq": 294},
    "Saturn": {"label": "Saturno — Estrutura", "color": "#8D99AE", "tone_freq": 220},
}

st.sidebar.header("Configurações da sessão")
planet_choice = st.sidebar.selectbox(
    "Tema (inspiração)",
    options=list(PLANET_THEME.keys()),
    format_func=lambda k: PLANET_THEME[k]["label"]
)

# -------------------------
# Intenções e presets
# -------------------------
PRACTICES = {
    "Calma imediata": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6},
    "Foco e clareza": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 2, "cycles": 5},
    "Sono e desaceleração": {"inhale": 4, "hold1": 0, "exhale": 8, "hold2": 0, "cycles": 8},
    "Energia suave": {"inhale": 3, "hold1": 1, "exhale": 3, "hold2": 1, "cycles": 6},
    "Respiração completa": {"inhale": 5, "hold1": 2, "exhale": 7, "hold2": 0, "cycles": 5},
    "Respiração quadrada": {"inhale": 4, "hold1": 4, "exhale": 4, "hold2": 4, "cycles": 5},
    "Respiração alternada (Nadi Shodhana)": {"inhale": 4, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6},
}

st.subheader("Escolha sua prática")
intent = st.selectbox("Prática", options=list(PRACTICES.keys()))

# -------------------------
# Áudio: gerar tom simples (WAV bytes)
# -------------------------
def generate_tone_wav(freq: float = 440.0, duration: float = 0.35, volume: float = 0.5, sr: int = 22050) -> bytes:
    """
    Gera um tom senoidal simples e retorna bytes WAV.
    Usamos wave + struct para compatibilidade com st.audio.
    """
    n_samples = int(sr * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sr)
        max_amp = 32767 * volume
        for i in range(n_samples):
            t = i / sr
            sample = int(max_amp * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()

def combine_tones_sequence(freq: float, pattern: Tuple[float, ...], sr: int = 22050) -> bytes:
    """
    Gera sequência de tons (pattern = durations em segundos) concatenados.
    Retorna bytes WAV.
    """
    parts = []
    for d in pattern:
        parts.append(generate_tone_wav(freq=freq, duration=d, sr=sr))
    # concatenar WAVs simples: extrair frames e reescrever em um único arquivo
    # Para simplicidade, re-generate a sequência como um único sinal
    total_dur = sum(pattern)
    n_samples = int(sr * total_dur)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        max_amp = 32767 * 0.5
        t_cursor = 0.0
        for i in range(n_samples):
            t = i / sr
            # escolher qual segment we're in
            elapsed = 0.0
            freq_now = freq
            for seg in pattern:
                if elapsed <= t < elapsed + seg:
                    break
                elapsed += seg
            sample = int(max_amp * math.sin(2 * math.pi * freq_now * t))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()

# -------------------------
# Animação: HTML/CSS/JS (círculo que expande/contrai)
# -------------------------
def breathing_animation_html(inhale: int, exhale: int, hold1: int, hold2: int, cycles: int, color: str):
    """
    Retorna HTML que anima um círculo com base nos tempos.
    A animação é controlada por CSS/JS e roda no browser.
    """
    total = inhale + hold1 + exhale + hold2
    # proporção de cada fase em %
    def pct(x): return (x / total) * 100 if total > 0 else 0
    inhale_pct = pct(inhale)
    hold1_pct = pct(hold1)
    exhale_pct = pct(exhale)
    hold2_pct = pct(hold2)
    # JS usa tempos em ms
    cycle_ms = int(total * 1000)
    html = f"""
<style>
  .breath-wrap {{ display:flex; align-items:center; justify-content:center; flex-direction:column; }}
  .circle {{
    width:120px; height:120px; border-radius:50%;
    background: radial-gradient(circle at 30% 30%, #fff8, {color});
    box-shadow: 0 8px 24px rgba(0,0,0,0.12);
    transition: transform {inhale}s ease-in-out;
    transform-origin:center;
  }}
  .label {{ margin-top:12px; font-size:18px; font-weight:600; color:#222; }}
</style>
<div class="breath-wrap">
  <div id="circle" class="circle" aria-hidden="true"></div>
  <div id="label" class="label">Preparar...</div>
</div>
<script>
const circle = document.getElementById("circle");
const label = document.getElementById("label");
const inhale = {inhale} * 1000;
const hold1 = {hold1} * 1000;
const exhale = {exhale} * 1000;
const hold2 = {hold2} * 1000;
const cycles = {cycles};
let cycle = 0;

function setLabel(text){{ label.textContent = text; }}

async function runCycle(){{
  for(cycle=0; cycle<cycles; cycle++){{
    setLabel("Inspire");
    circle.style.transition = `transform ${{inhale/1000}}s ease-in-out`;
    circle.style.transform = "scale(1.35)";
    await new Promise(r=>setTimeout(r, inhale));
    if(hold1>0){{ setLabel("Segure"); await new Promise(r=>setTimeout(r, hold1)); }}
    setLabel("Expire");
    circle.style.transition = `transform ${{exhale/1000}}s ease-in-out`;
    circle.style.transform = "scale(0.75)";
    await new Promise(r=>setTimeout(r, exhale));
    if(hold2>0){{ setLabel("Segure"); await new Promise(r=>setTimeout(r, hold2)); }}
  }}
  setLabel("Concluído");
  circle.style.transform = "scale(1)";
}}

runCycle();
</script>
"""
    return html

# -------------------------
# Sessão longa (modo contínuo)
# -------------------------
st.sidebar.subheader("Sessão longa")
long_mode = st.sidebar.checkbox("Ativar sessão longa (10–30 min)", value=False)
long_minutes = st.sidebar.slider("Duração (minutos)", min_value=10, max_value=30, value=15, step=5) if long_mode else 0

# -------------------------
# Áudio e controles
# -------------------------
theme = PLANET_THEME.get(planet_choice, PLANET_THEME["Default"])
st.markdown(f"**Tema:** {theme['label']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px'></div>", unsafe_allow_html=True)

preset = PRACTICES[intent]
inhale = st.number_input("Inspire (s)", value=preset["inhale"], min_value=1, max_value=20, step=1)
hold1 = st.number_input("Segure após inspirar (s)", value=preset["hold1"], min_value=0, max_value=20, step=1)
exhale = st.number_input("Expire (s)", value=preset["exhale"], min_value=1, max_value=30, step=1)
hold2 = st.number_input("Segure após expirar (s)", value=preset["hold2"], min_value=0, max_value=20, step=1)
cycles = st.number_input("Ciclos", value=preset["cycles"], min_value=1, max_value=200, step=1)

st.markdown("---")

col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_btn = st.button("▶️ Iniciar prática")
with col2:
    stop_btn = st.button("⏹️ Parar")
with col3:
    play_audio_btn = st.button("🔔 Tocar sinal de teste")

# gerar sinal de teste (um tom curto com frequência do tema)
if play_audio_btn:
    tone = generate_tone_wav(freq=theme["tone_freq"], duration=0.25)
    st.audio(tone, format="audio/wav")

# -------------------------
# Sessão guiada: animação + áudio + texto
# -------------------------
session_running = False
if start_btn:
    session_running = True
    # preparar sequência de tons: um tom no início de cada fase (inhale/expire)
    # pattern: for each cycle: inhale tone (short), exhale tone (short)
    freq = theme["tone_freq"]
    # create a short sequence: tone at inhale start and exhale start for each cycle
    pattern_durations = []
    for _ in range(cycles):
        pattern_durations.append(0.05)  # inhale cue
        pattern_durations.append(inhale)  # silence while breathing (we won't use silence durations in tone generator)
        pattern_durations.append(0.05)  # exhale cue
        pattern_durations.append(exhale)
    # For simplicity, create a repeating short cue WAV and play it at each cue using st.audio inside loop

    # show animation
    html = breathing_animation_html(inhale=inhale, exhale=exhale, hold1=hold1, hold2=hold2, cycles=cycles, color=theme["color"])
    st.components.v1.html(html, height=260)

    # guided loop with visual cues and audio cues
    placeholder = st.empty()
    progress = st.progress(0)
    total_steps = cycles * (inhale + hold1 + exhale + hold2)
    elapsed = 0.0
    stop_requested = False

    for c in range(int(cycles)):
        if stop_btn:
            stop_requested = True
            break
        # inhale
        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inhale}s**")
        st.audio(generate_tone_wav(freq=freq, duration=0.12), format="audio/wav")
        time.sleep(inhale)
        elapsed += inhale
        progress.progress(min(1.0, elapsed / (total_steps if total_steps else 1)))

        # hold1
        if hold1 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1}s**")
            time.sleep(hold1)
            elapsed += hold1
            progress.progress(min(1.0, elapsed / (total_steps if total_steps else 1)))

        # exhale
        placeholder.markdown(f"### 💨 Expire por **{exhale}s**")
        st.audio(generate_tone_wav(freq=freq * 0.8, duration=0.12), format="audio/wav")
        time.sleep(exhale)
        elapsed += exhale
        progress.progress(min(1.0, elapsed / (total_steps if total_steps else 1)))

        # hold2
        if hold2 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2}s**")
            time.sleep(hold2)
            elapsed += hold2
            progress.progress(min(1.0, elapsed / (total_steps if total_steps else 1)))

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
    progress.progress(1.0)

# -------------------------
# Sessão longa: cronômetro com ciclos automáticos e música de fundo (tons)
# -------------------------
if long_mode:
    st.markdown("---")
    st.subheader("Sessão longa")
    st.markdown(
        f"Modo sessão longa ativado: **{long_minutes} minutos**. A sessão seguirá o padrão selecionado ({intent}) "
        "com pausas suaves entre blocos."
    )
    if st.button("▶️ Iniciar sessão longa"):
        total_seconds = long_minutes * 60
        block_seconds = (inhale + hold1 + exhale + hold2) * cycles
        # calcular quantos blocos cabem
        if block_seconds <= 0:
            st.warning("Configuração de respiração inválida para sessão longa.")
        else:
            blocks = max(1, int(total_seconds // block_seconds))
            st.info(f"Serão executados aproximadamente {blocks} blocos de {cycles} ciclos.")
            long_progress = st.progress(0)
            start_time = time.time()
            for b in range(blocks):
                st.write(f"🔁 Bloco {b+1}/{blocks}")
                # executar um bloco (reutilizar a lógica acima, mas sem animação HTML para não sobrecarregar)
                for c in range(int(cycles)):
                    st.write(f"   • Ciclo {c+1}/{cycles}: Inspire {inhale}s — Expire {exhale}s")
                    st.audio(generate_tone_wav(freq=theme["tone_freq"], duration=0.08), format="audio/wav")
                    time.sleep(inhale)
                    if hold1 > 0:
                        time.sleep(hold1)
                    st.audio(generate_tone_wav(freq=theme["tone_freq"] * 0.8, duration=0.08), format="audio/wav")
                    time.sleep(exhale)
                    if hold2 > 0:
                        time.sleep(hold2)
                elapsed = time.time() - start_time
                long_progress.progress(min(1.0, elapsed / total_seconds))
            st.success("Sessão longa concluída. Reserve alguns minutos para integração e silêncio.")

# -------------------------
# Recursos e segurança
# -------------------------
st.markdown("---")
st.subheader("Recursos e segurança")
st.markdown(
    """
- **Contraindicações:** se tiver problemas respiratórios, cardíacos, pressão alta, gravidez ou qualquer condição médica, consulte um profissional antes de praticar.
- **Dica:** pratique sentado com coluna ereta e ombros relaxados. Evite prender a respiração de forma forçada.
- **Integração temática:** o tema selecionado altera a cor e a frequência dos sinais sonoros para apoiar a intenção.
"""
)

# -------------------------
# Exportar/Salvar sessão (opcional: instrução)
# -------------------------
st.info("Dica: se quiser registrar como se sentiu, use o bloco de notas do app para salvar observações após a prática.")

# -------------------------
# Fim da página
# -------------------------
st.markdown("—")
st.caption("Pranaterapia — práticas simples para integrar respiração, presença e intenção.")