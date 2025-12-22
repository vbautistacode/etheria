# 08_pranaterapia.py
import streamlit as st
import time
import math
import io
import wave
import struct
from typing import Dict
import numpy as np

# -------------------------
# Configuração da página
# -------------------------
st.title("🌬️ Pranaterapia")
st.markdown(
    """
    Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital).
    Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença.
    """
)
st.caption(
    """
Nossa pranaterapia integra respiração, som e visual para harmonizar o seu ser.
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

preset = theme.get("preset", {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6})
inhale = st.number_input("Inspire (s)", value=int(preset["inhale"]), min_value=1, max_value=30, step=1)
hold1 = st.number_input("Segure após inspirar (s)", value=int(preset["hold1"]), min_value=0, max_value=30, step=1)
exhale = st.number_input("Expire (s)", value=int(preset["exhale"]), min_value=1, max_value=60, step=1)
hold2 = st.number_input("Segure após expirar (s)", value=int(preset["hold2"]), min_value=0, max_value=30, step=1)
cycles = st.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=500, step=1)

if st.button("Aplicar preset do tema"):
    p = theme.get("preset", {})
    st.session_state["inhale"] = int(p.get("inhale", inhale))
    st.session_state["hold1"] = int(p.get("hold1", hold1))
    st.session_state["exhale"] = int(p.get("exhale", exhale))
    st.session_state["hold2"] = int(p.get("hold2", hold2))
    st.session_state["cycles"] = int(p.get("cycles", cycles))
    st.success("Preset do tema aplicado. Clique em Iniciar prática para começar.")

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
# Cue patterns por tema
# -------------------------
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
# Geração de áudio contínuo (cues + drone)
# -------------------------
SR = 22050

def _sine(freq, length, sr=SR):
    t = np.linspace(0, length, int(sr * length), False)
    return np.sin(2 * np.pi * freq * t)

def _apply_envelope(signal: np.ndarray, sr=SR, attack=0.005, release=0.01):
    n = len(signal)
    a = int(sr * attack)
    r = int(sr * release)
    env = np.ones(n, dtype=float)
    if a > 0:
        env[:a] = np.linspace(0.0, 1.0, a)
    if r > 0:
        env[-r:] = np.linspace(1.0, 0.0, r)
    return signal * env

def _mix_and_normalize(signals: list):
    mix = np.sum(signals, axis=0)
    peak = np.max(np.abs(mix)) or 1.0
    return mix / peak * 0.95

def _wav_bytes_from_array(arr: np.ndarray, sr=SR):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        int_data = (arr * 32767).astype(np.int16)
        wf.writeframes(int_data.tobytes())
    return buf.getvalue()

def generate_session_wav(
    inhale, hold1, exhale, hold2, cycles,
    cue_freq=440.0, cue_pattern="single",
    drone_freq=None, drone_volume=0.08, sr=SR
):
    total_time = (inhale + hold1 + exhale + hold2) * cycles
    n_samples = int(total_time * sr)
    signals = []

    # drone
    if drone_freq:
        t = np.linspace(0, total_time, n_samples, False)
        drone = 0.6 * np.sin(2 * np.pi * drone_freq * t)
        drone = _apply_envelope(drone, sr, attack=0.5, release=0.5)
        signals.append(drone * drone_volume)
    else:
        signals.append(np.zeros(n_samples))

    # cues
    cursor = 0.0
    for _ in range(int(cycles)):
        start_inhale = int(cursor * sr)
        # inhale cue
        if cue_pattern == "single":
            tone = _sine(cue_freq, 0.12, sr)
            tone = _apply_envelope(tone, sr, attack=0.005, release=0.01)
            tmp = np.zeros(n_samples)
            end = start_inhale + len(tone)
            if end <= n_samples:
                tmp[start_inhale:end] += tone
            signals.append(tmp)
        elif cue_pattern == "double":
            t1 = _sine(cue_freq, 0.07, sr); t1 = _apply_envelope(t1, sr, 0.003, 0.006)
            t2 = _sine(cue_freq, 0.07, sr); t2 = _apply_envelope(t2, sr, 0.003, 0.006)
            tmp = np.zeros(n_samples)
            tmp[start_inhale:start_inhale+len(t1)] += t1
            off = int(0.12 * sr)
            if start_inhale + off + len(t2) <= n_samples:
                tmp[start_inhale+off:start_inhale+off+len(t2)] += t2
            signals.append(tmp)
        elif cue_pattern == "soft":
            tone = _sine(cue_freq, 0.28, sr)
            tone = _apply_envelope(tone, sr, attack=0.02, release=0.05)
            tmp = np.zeros(n_samples)
            end = start_inhale + len(tone)
            if end <= n_samples:
                tmp[start_inhale:end] += tone
            signals.append(tmp)

        cursor += inhale + hold1
        start_exhale = int(cursor * sr)
        # exhale cue (slightly lower)
        tone = _sine(cue_freq * 0.85, 0.12, sr)
        tone = _apply_envelope(tone, sr, attack=0.005, release=0.01)
        tmp2 = np.zeros(n_samples)
        end2 = start_exhale + len(tone)
        if end2 <= n_samples:
            tmp2[start_exhale:end2] += tone
        signals.append(tmp2)

        cursor += exhale + hold2

    mix = _mix_and_normalize(signals)
    return _wav_bytes_from_array(mix, sr=sr)

# -------------------------
# Animação HTML/CSS/JS
# -------------------------
def breathing_animation_html_with_voice(inhale: int, exhale: int, hold1: int, hold2: int, cycles: int, color: str, label_prefix: str = "", voice_lang: str = "pt-BR", speak_enabled: bool = True) -> str:
    """
    HTML que anima o círculo e usa Web Speech API para falar 'Inspire' e 'Expire' no momento exato.
    - speak_enabled: se False, apenas animação visual.
    - voice_lang: 'pt-BR' para voz em português (navegador escolhe voz disponível).
    """
    # Escapar chaves e inserir valores num f-string seguro
    html = f"""
<style>
  .breath-wrap {{ display:flex; align-items:center; justify-content:center; flex-direction:column; }}
  .circle {{ width:160px; height:160px; border-radius:50%; background: radial-gradient(circle at 30% 30%, #fff8, {color}); box-shadow: 0 12px 36px rgba(0,0,0,0.12); transform-origin:center; }}
  .label {{ margin-top:12px; font-size:18px; font-weight:600; color:#222; }}
</style>
<div class="breath-wrap">
  <div id="circle" class="circle" aria-hidden="true"></div>
  <div id="label" class="label">{label_prefix}Preparar...</div>
</div>
<script>
(function(){{
  const circle = document.getElementById("circle");
  const label = document.getElementById("label");
  const inhale = {inhale} * 1000;
  const hold1 = {hold1} * 1000;
  const exhale = {exhale} * 1000;
  const hold2 = {hold2} * 1000;
  const cycles = {cycles};
  const speakEnabled = {str(speak_enabled).lower()};
  const voiceLang = "{voice_lang}";

  function setLabel(text){{ label.textContent = text; }}

  // Escolher voz disponível que combine com voiceLang
  function pickVoice() {{
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return null;
    // preferir voz que contenha locale
    let v = voices.find(x => x.lang && x.lang.toLowerCase().startsWith(voiceLang.toLowerCase()));
    if (!v) v = voices[0];
    return v;
  }}

  function speak(text, voice, rate=1.0, pitch=1.0, volume=1.0) {{
    if (!speakEnabled || !window.speechSynthesis) return;
    const u = new SpeechSynthesisUtterance(text);
    u.lang = voiceLang;
    u.rate = rate;
    u.pitch = pitch;
    u.volume = volume;
    if (voice) u.voice = voice;
    window.speechSynthesis.speak(u);
  }}

  // Função que executa um ciclo com fala sincronizada
  async function runCycle() {{
    // garantir que as vozes estejam carregadas
    if (speakEnabled && window.speechSynthesis && window.speechSynthesis.getVoices().length === 0) {{
      // algumas implementações carregam vozes assincronamente
      await new Promise(r => {{
        window.speechSynthesis.onvoiceschanged = function(){{ r(); }};
        // timeout de segurança
        setTimeout(r, 500);
      }});
    }}
    const voice = pickVoice();

    for (let cycle = 0; cycle < cycles; cycle++) {{
      // INHALE
      setLabel("Inspire");
      circle.style.transition = "transform " + (inhale/1000) + "s ease-in-out";
      circle.style.transform = "scale(1.35)";
      // falar imediatamente no início da inspiração
      if (speakEnabled) speak("Inspire", voice, 1.0, 1.0, 1.0);
      await new Promise(r => setTimeout(r, inhale));

      // HOLD1
      if (hold1 > 0) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, hold1));
      }}

      // EXHALE
      setLabel("Expire");
      circle.style.transition = "transform " + (exhale/1000) + "s ease-in-out";
      circle.style.transform = "scale(0.75)";
      // falar no início da expiração
      if (speakEnabled) speak("Expire", voice, 1.0, 1.0, 1.0);
      await new Promise(r => setTimeout(r, exhale));

      // HOLD2
      if (hold2 > 0) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, hold2));
      }}
    }}
    setLabel("Concluído");
    circle.style.transform = "scale(1)";
  }}

  // iniciar
  runCycle();
}})();
</script>
"""
    return html

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
    p = theme.get("preset", {})
    st.session_state["inhale"] = int(p.get("inhale", inhale))
    st.session_state["hold1"] = int(p.get("hold1", hold1))
    st.session_state["exhale"] = int(p.get("exhale", exhale))
    st.session_state["hold2"] = int(p.get("hold2", hold2))
    st.session_state["cycles"] = int(p.get("cycles", cycles))
    st.success("Preset do tema aplicado. Clique em Iniciar prática para começar.")

st.markdown("**Afirmação do tema**")
st.info(theme.get("affirmation", ""))

# -------------------------
# Execução da prática guiada (áudio contínuo + visual)
# -------------------------
if start_btn:
    inhale = int(st.session_state.get("inhale", inhale))
    hold1 = int(st.session_state.get("hold1", hold1))
    exhale = int(st.session_state.get("exhale", exhale))
    hold2 = int(st.session_state.get("hold2", hold2))
    cycles = int(st.session_state.get("cycles", cycles))

    # gerar WAV contínuo
    drone_freq = (theme["tone_freq"] * 0.25) if drone_enabled else None
    session_wav = None
    if not no_audio:
        session_wav = generate_session_wav(
            inhale=inhale, hold1=hold1, exhale=exhale, hold2=hold2, cycles=cycles,
            cue_freq=theme["tone_freq"], cue_pattern=cue_pattern,
            drone_freq=drone_freq, drone_volume=drone_volume, sr=SR
        )
        # tocar uma vez (reproduz todo o áudio contínuo)
        st.audio(session_wav, format="audio/wav")

    # animação visual (independente do áudio)
    html = breathing_animation_html(inhale=inhale, exhale=exhale, hold1=hold1, hold2=hold2, cycles=cycles, color=theme["color"], label_prefix=theme["label"] + " — ")
    st.components.v1.html(html, height=320)

    placeholder = st.empty()
    progress = st.progress(0)
    total_time = (inhale + hold1 + exhale + hold2) * cycles
    elapsed = 0.0

    for c in range(int(cycles)):
        if stop_btn:
            placeholder.markdown("### ⏹️ Sessão interrompida.")
            break

        # variação adaptativa leve (determinística)
        inh = inhale if not adaptive_rhythm else max(0.5, round(inhale * (1.0 + 0.05 * math.sin(time.time())), 2))
        h1 = hold1 if not adaptive_rhythm else max(0.0, round(hold1 * (1.0 + 0.05 * math.sin(time.time() + 1)), 2))
        exh = exhale if not adaptive_rhythm else max(0.5, round(exhale * (1.0 + 0.05 * math.sin(time.time() + 2)), 2))
        h2 = hold2 if not adaptive_rhythm else max(0.0, round(hold2 * (1.0 + 0.05 * math.sin(time.time() + 3)), 2))

        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inh}s**")
        if not visual_only:
            time.sleep(inh)
        else:
            time.sleep(max(0.2, inh * 0.2))
        elapsed += inh
        progress.progress(min(1.0, elapsed / total_time))

        if h1 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{h1}s**")
            if not visual_only:
                time.sleep(h1)
            else:
                time.sleep(max(0.2, h1 * 0.2))
            elapsed += h1
            progress.progress(min(1.0, elapsed / total_time))

        placeholder.markdown(f"### 💨 Expire por **{exh}s**")
        if not visual_only:
            time.sleep(exh)
        else:
            time.sleep(max(0.2, exh * 0.2))
        elapsed += exh
        progress.progress(min(1.0, elapsed / total_time))

        if h2 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{h2}s**")
            if not visual_only:
                time.sleep(h2)
            else:
                time.sleep(max(0.2, h2 * 0.2))
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
                # gerar e tocar um WAV por bloco para reduzir memória se necessário
                if not no_audio:
                    block_wav = generate_session_wav(
                        inhale=inhale, hold1=hold1, exhale=exhale, hold2=hold2, cycles=cycles,
                        cue_freq=theme["tone_freq"], cue_pattern=cue_pattern,
                        drone_freq=(theme["tone_freq"] * 0.25) if drone_enabled else None,
                        drone_volume=drone_volume, sr=SR
                    )
                    st.audio(block_wav, format="audio/wav")
                for c in range(int(cycles)):
                    st.write(f"   • Ciclo {c+1}/{cycles}: Inspire {inhale}s — Expire {exhale}s")
                    time.sleep(inhale)
                    if hold1 > 0:
                        time.sleep(hold1)
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