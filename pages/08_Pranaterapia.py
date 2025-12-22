# 08_pranaterapia.py
import streamlit as st
import time
import math
import io
import wave
import struct
from typing import Optional, Tuple, Dict, List

# -------------------------
# Configuração da página
# -------------------------
st.set_page_config(page_title="Pranaterapia", page_icon="🌬️", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
    """
A pranaterapia integra respiração, som e visual para harmonizar o prana (energia vital).
Use os controles abaixo para escolher um tema, aplicar presets, ativar drone harmônico, e executar práticas guiadas.
"""
)

# -------------------------
# Temas e presets
# -------------------------
PLANET_THEME: Dict[str, Dict[str, object]] = {
    "Default": {"label": "Padrão", "color": "#6C8EBF", "tone_freq": 440, "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Presença e equilíbrio."},
    "Sun": {"label": "Sol — Vitalidade", "color": "#F2C94C", "tone_freq": 523, "preset": {"inhale": 4, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Sinto minha vitalidade crescer."},
    "Moon": {"label": "Lua — Calma", "color": "#7FB3D5", "tone_freq": 392, "preset": {"inhale": 4, "hold1": 0, "exhale": 8, "hold2": 0, "cycles": 8}, "affirmation": "Acalmo e integro."},
    "Mercury": {"label": "Mercúrio — Clareza", "color": "#9AD3BC", "tone_freq": 660, "preset": {"inhale": 3, "hold1": 1, "exhale": 3, "hold2": 1, "cycles": 6}, "affirmation": "Minha mente clareia."},
    "Venus": {"label": "Vênus — Afeição", "color": "#F7A8B8", "tone_freq": 587, "preset": {"inhale": 4, "hold1": 1, "exhale": 5, "hold2": 0, "cycles": 6}, "affirmation": "Cultivo afeto e beleza."},
    "Mars": {"label": "Marte — Energia", "color": "#E76F51", "tone_freq": 330, "preset": {"inhale": 2, "hold1": 0, "exhale": 2, "hold2": 0, "cycles": 8}, "affirmation": "Ação com coragem."},
    "Jupiter": {"label": "Júpiter — Expansão", "color": "#B59F3B", "tone_freq": 294, "preset": {"inhale": 5, "hold1": 2, "exhale": 7, "hold2": 0, "cycles": 5}, "affirmation": "Expando com confiança."},
    "Saturn": {"label": "Saturno — Estrutura", "color": "#8D99AE", "tone_freq": 220, "preset": {"inhale": 4, "hold1": 3, "exhale": 6, "hold2": 0, "cycles": 5}, "affirmation": "Disciplina e presença."},
}

st.sidebar.header("Configurações da sessão")
planet_choice = st.sidebar.selectbox(
    "Tema (inspiração)",
    options=list(PLANET_THEME.keys()),
    format_func=lambda k: PLANET_THEME[k]["label"]
)

# -------------------------
# Presets e controles
# -------------------------
st.subheader("Prática e presets")
theme = PLANET_THEME.get(planet_choice, PLANET_THEME["Default"])
st.markdown(f"**Tema:** {theme['label']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px'></div>", unsafe_allow_html=True)

# controles manuais (inicializados com preset do tema)
preset = theme.get("preset", {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6})
inhale = st.number_input("Inspire (s)", value=int(preset["inhale"]), min_value=1, max_value=30, step=1)
hold1 = st.number_input("Segure após inspirar (s)", value=int(preset["hold1"]), min_value=0, max_value=30, step=1)
exhale = st.number_input("Expire (s)", value=int(preset["exhale"]), min_value=1, max_value=60, step=1)
hold2 = st.number_input("Segure após expirar (s)", value=int(preset["hold2"]), min_value=0, max_value=30, step=1)
cycles = st.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=500, step=1)

# aplicar preset do tema
if st.button("Aplicar preset do tema"):
    inhale = st.session_state.setdefault("inhale", int(preset["inhale"]))
    hold1 = st.session_state.setdefault("hold1", int(preset["hold1"]))
    exhale = st.session_state.setdefault("exhale", int(preset["exhale"]))
    hold2 = st.session_state.setdefault("hold2", int(preset["hold2"]))
    cycles = st.session_state.setdefault("cycles", int(preset["cycles"]))
    # atualizar inputs (Streamlit não atualiza inputs automaticamente; informar usuário)
    st.success("Preset do tema aplicado. Ajuste os valores se desejar e inicie a prática.")

# -------------------------
# Acessibilidade e opções
# -------------------------
st.sidebar.subheader("Acessibilidade")
no_audio = st.sidebar.checkbox("Sem áudio (visual apenas)", value=False)
visual_only = st.sidebar.checkbox("Modo visual simplificado", value=False)
adaptive_rhythm = st.sidebar.checkbox("Variação adaptativa do ritmo (±10%)", value=True)
drone_enabled = st.sidebar.checkbox("Drone harmônico de fundo (sutil)", value=False)
drone_volume = st.sidebar.slider("Volume do drone", min_value=0.0, max_value=1.0, value=0.12, step=0.01)

# -------------------------
# Funções de áudio (tons e drone)
# -------------------------
def generate_tone_wav(freq: float = 440.0, duration: float = 0.25, volume: float = 0.5, sr: int = 22050) -> bytes:
    """Gera um tom senoidal simples e retorna bytes WAV."""
    n_samples = int(sr * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        max_amp = int(32767 * volume)
        for i in range(n_samples):
            t = i / sr
            sample = int(max_amp * math.sin(2 * math.pi * freq * t))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()

def generate_drone_wav(base_freq: float = 220.0, duration: float = 10.0, volume: float = 0.08, sr: int = 22050) -> bytes:
    """Gera um drone harmônico simples (seno + 2ª harmônica leve)."""
    n_samples = int(sr * duration)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        max_amp = int(32767 * volume)
        for i in range(n_samples):
            t = i / sr
            # base + small harmonic
            sample = int(max_amp * (0.7 * math.sin(2 * math.pi * base_freq * t) + 0.3 * math.sin(2 * math.pi * base_freq * 2 * t)))
            wf.writeframes(struct.pack("<h", sample))
    return buf.getvalue()

# -------------------------
# Cue patterns por tema
# -------------------------
CUE_PATTERNS: Dict[str, str] = {
    "single": "single",   # um tom no início de cada fase
    "double": "double",   # dois toques rápidos no início
    "soft": "soft",       # tom suave e longo
}

theme_cue = {
    "Default": "single",
    "Sun": "double",
    "Moon": "soft",
    "Mercury": "single",
    "Venus": "soft",
    "Mars": "double",
    "Jupiter": "soft",
    "Saturn": "single",
}
cue_pattern = theme_cue.get(planet_choice, "single")

# -------------------------
# Animação HTML/CSS/JS
# -------------------------
def breathing_animation_html(inhale: int, exhale: int, hold1: int, hold2: int, cycles: int, color: str, label_prefix: str = "") -> str:
    total = inhale + hold1 + exhale + hold2
    def pct(x): return (x / total) * 100 if total > 0 else 0
    inhale_pct = pct(inhale)
    hold1_pct = pct(hold1)
    exhale_pct = pct(exhale)
    hold2_pct = pct(hold2)
    html = f"""
<style>
  .breath-wrap {{ display:flex; align-items:center; justify-content:center; flex-direction:column; }}
  .circle {{
    width:160px; height:160px; border-radius:50%;
    background: radial-gradient(circle at 30% 30%, #fff8, {color});
    box-shadow: 0 12px 36px rgba(0,0,0,0.12);
    transform-origin:center;
  }}
  .label {{ margin-top:12px; font-size:18px; font-weight:600; color:#222; }}
</style>
<div class="breath-wrap">
  <div id="circle" class="circle" aria-hidden="true"></div>
  <div id="label" class="label">{label_prefix}Preparar...</div>
</div>
<script>
const circle = document.getElementById("circle");
const label = document.getElementById("label");
const inhale = {inhale} * 1000;
const hold1 = {hold1} * 1000;
const exhale = {exhale} * 1000;
const hold2 = {hold2} * 1000;
const cycles = {cycles};

function setLabel(text){{ label.textContent = text; }}

async function runCycle(){{
  for(let cycle=0; cycle<cycles; cycle++){{
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
# Utilitários
# -------------------------
def apply_adaptive(value: float, adaptive: bool) -> float:
    """Aplica variação aleatória pequena (±10%) se adaptive True."""
    if not adaptive:
        return value
    # variação até ±10%
    factor = 1.0 + (0.1 * (2 * (math.sin(time.time()) * 0.5)))  # leve variação determinística por tempo
    return max(0.5, round(value * factor, 2))

def play_cue(freq: float, pattern: str, volume: float = 0.5):
    """Toca um cue de acordo com o padrão: single, double, soft."""
    if no_audio:
        return
    if pattern == "single":
        st.audio(generate_tone_wav(freq=freq, duration=0.12, volume=volume), format="audio/wav")
    elif pattern == "double":
        st.audio(generate_tone_wav(freq=freq, duration=0.08, volume=volume), format="audio/wav")
        time.sleep(0.12)
        st.audio(generate_tone_wav(freq=freq, duration=0.08, volume=volume), format="audio/wav")
    elif pattern == "soft":
        st.audio(generate_tone_wav(freq=freq, duration=0.28, volume=volume * 0.7), format="audio/wav")

# -------------------------
# Controles principais
# -------------------------
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    start_btn = st.button("▶️ Iniciar prática")
with col2:
    stop_btn = st.button("⏹️ Parar")
with col3:
    apply_theme_btn = st.button("Aplicar preset do tema (rápido)")

if apply_theme_btn:
    # aplicar preset do tema diretamente nos inputs (informa o usuário)
    p = theme.get("preset", {})
    st.session_state["inhale"] = int(p.get("inhale", inhale))
    st.session_state["hold1"] = int(p.get("hold1", hold1))
    st.session_state["exhale"] = int(p.get("exhale", exhale))
    st.session_state["hold2"] = int(p.get("hold2", hold2))
    st.session_state["cycles"] = int(p.get("cycles", cycles))
    st.success("Preset do tema aplicado. Clique em Iniciar prática para começar.")

# -------------------------
# Afirmação temática
# -------------------------
st.markdown("**Afirmação do tema**")
st.info(theme.get("affirmation", ""))

# -------------------------
# Execução da prática guiada
# -------------------------
if start_btn:
    # carregar valores possivelmente atualizados na sessão
    inhale = int(st.session_state.get("inhale", inhale))
    hold1 = int(st.session_state.get("hold1", hold1))
    exhale = int(st.session_state.get("exhale", exhale))
    hold2 = int(st.session_state.get("hold2", hold2))
    cycles = int(st.session_state.get("cycles", cycles))

    # animação
    html = breathing_animation_html(inhale=inhale, exhale=exhale, hold1=hold1, hold2=hold2, cycles=cycles, color=theme["color"], label_prefix=theme["label"] + " — ")
    st.components.v1.html(html, height=320)

    # drone de fundo (opcional)
    drone_bytes = None
    if drone_enabled and not no_audio:
        drone_bytes = generate_drone_wav(base_freq=theme["tone_freq"] * 0.25, duration=max(10, (inhale + hold1 + exhale + hold2) * cycles + 2), volume=drone_volume)
        st.audio(drone_bytes, format="audio/wav")

    placeholder = st.empty()
    progress = st.progress(0)
    total_time = (inhale + hold1 + exhale + hold2) * cycles
    elapsed = 0.0

    for c in range(int(cycles)):
        if stop_btn:
            placeholder.markdown("### ⏹️ Sessão interrompida.")
            break

        # aplicar variação adaptativa leve
        inh = apply_adaptive(inhale, adaptive_rhythm)
        h1 = apply_adaptive(hold1, adaptive_rhythm)
        exh = apply_adaptive(exhale, adaptive_rhythm)
        h2 = apply_adaptive(hold2, adaptive_rhythm)

        # inhale
        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inh}s**")
        play_cue(freq=theme["tone_freq"], pattern=cue_pattern, volume=0.5)
        if not visual_only:
            time.sleep(inh)
        else:
            time.sleep(inh * 0.2)  # visual-only speeds up waiting for UX

        elapsed += inh
        progress.progress(min(1.0, elapsed / total_time))

        # hold1
        if h1 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{h1}s**")
            if not visual_only:
                time.sleep(h1)
            else:
                time.sleep(h1 * 0.2)
            elapsed += h1
            progress.progress(min(1.0, elapsed / total_time))

        # exhale
        placeholder.markdown(f"### 💨 Expire por **{exh}s**")
        play_cue(freq=theme["tone_freq"] * 0.85, pattern=cue_pattern, volume=0.45)
        if not visual_only:
            time.sleep(exh)
        else:
            time.sleep(exh * 0.2)
        elapsed += exh
        progress.progress(min(1.0, elapsed / total_time))

        # hold2
        if h2 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{h2}s**")
            if not visual_only:
                time.sleep(h2)
            else:
                time.sleep(h2 * 0.2)
            elapsed += h2
            progress.progress(min(1.0, elapsed / total_time))

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
    progress.progress(1.0)

# -------------------------
# Sessão longa (opcional)
# -------------------------
st.markdown("---")
st.subheader("Sessão longa (blocos)")
long_mode = st.checkbox("Ativar sessão longa (10–30 min)", value=False)
if long_mode:
    long_minutes = st.slider("Duração (minutos)", min_value=10, max_value=60, value=20, step=5)
    if st.button("▶️ Iniciar sessão longa"):
        total_seconds = long_minutes * 60
        block_seconds = (inhale + hold1 + exhale + hold2) * cycles
        if block_seconds <= 0:
            st.warning("Configuração de respiração inválida.")
        else:
            blocks = max(1, int(total_seconds // block_seconds))
            st.info(f"Executando ~{blocks} blocos de {cycles} ciclos.")
            long_progress = st.progress(0)
            start_time = time.time()
            for b in range(blocks):
                st.write(f"🔁 Bloco {b+1}/{blocks}")
                for c in range(int(cycles)):
                    st.write(f"   • Ciclo {c+1}/{cycles}: Inspire {inhale}s — Expire {exhale}s")
                    if not no_audio:
                        st.audio(generate_tone_wav(freq=theme["tone_freq"], duration=0.08), format="audio/wav")
                    time.sleep(inhale)
                    if hold1 > 0:
                        time.sleep(hold1)
                    if not no_audio:
                        st.audio(generate_tone_wav(freq=theme["tone_freq"] * 0.85, duration=0.08), format="audio/wav")
                    time.sleep(exhale)
                    if hold2 > 0:
                        time.sleep(hold2)
                elapsed = time.time() - start_time
                long_progress.progress(min(1.0, elapsed / total_seconds))
            st.success("Sessão longa concluída. Reserve alguns minutos para integração.")

# -------------------------
# Recursos e segurança
# -------------------------
st.markdown("---")
st.subheader("Recursos e segurança")
st.markdown(
    """
- **Contraindicações:** se tiver problemas respiratórios, cardíacos, pressão alta, gravidez ou qualquer condição médica, consulte um profissional antes de praticar.
- **Dica:** pratique sentado com coluna ereta e ombros relaxados. Evite prender a respiração de forma forçada.
- **Acessibilidade:** ative 'Sem áudio' ou 'Modo visual simplificado' conforme necessário.
"""
)

st.caption("Pranaterapia — práticas guiadas para integrar respiração, presença e intenção.")