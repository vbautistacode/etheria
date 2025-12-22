# 08_pranaterapia.py
import streamlit as st
import time

st.set_page_config(page_title="Pranaterapia", page_icon="🌬️", layout="centered")
st.title("🌬️ Pranaterapia")
st.markdown(
    """
    Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital).
    Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença.
    """
)
st.caption(
    """
Nossa pranaterapia integra respiração, som (voz do navegador) e visual para harmonizar o seu ser.
Escolha um chakra para aplicar um preset prático e iniciar a prática.
"""
)

# -------------------------
# Presets práticos por chakra (foco em resultados)
# -------------------------
CHAKRA_PRESETS = {
    "Muladhara": {  # Root
        "color": "#D9534F",
        "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6},
        "cue": "double",
        "affirmation": "Estou seguro e enraizado."
    },
    "Svadhisthana": {  # Sacral
        "color": "#F39C12",
        "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6},
        "cue": "single",
        "affirmation": "Minha criatividade flui."
    },
    "Manipura": {  # Solar Plexus
        "color": "#F1C40F",
        "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8},
        "cue": "double",
        "affirmation": "Ação com clareza."
    },
    "Anahata": {  # Heart
        "color": "#27AE60",
        "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6},
        "cue": "soft",
        "affirmation": "Abro meu coração."
    },
    "Vishuddha": {  # Throat
        "color": "#3498DB",
        "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5},
        "cue": "single",
        "affirmation": "Comunico com verdade."
    },
    "Ajna": {  # Third Eye
        "color": "#5B2C6F",
        "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5},
        "cue": "soft",
        "affirmation": "Minha percepção se afina."
    },
    "Sahasrara": {  # Crown
        "color": "#8E44AD",
        "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4},
        "cue": "soft",
        "affirmation": "Conecto-me ao silêncio."
    },
}

# -------------------------
# UI: seleção de chakra e controles
# -------------------------
st.subheader("🎯 Escolha o chakra a trabalhar (preset prático)")
chakra = st.selectbox("Chakra", options=list(CHAKRA_PRESETS.keys()))
theme = CHAKRA_PRESETS[chakra]
st.markdown(f"**Foco:** {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

# controles manuais (inicializados com preset do chakra)
preset = theme["preset"]
inhale = st.number_input("Inspire (s)", value=float(preset["inhale"]), min_value=1.0, max_value=30.0, step=0.5)
hold1 = st.number_input("Segure após inspirar (s)", value=float(preset["hold1"]), min_value=0.0, max_value=30.0, step=0.5)
exhale = st.number_input("Expire (s)", value=float(preset["exhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold2 = st.number_input("Segure após expirar (s)", value=float(preset["hold2"]), min_value=0.0, max_value=30.0, step=0.5)
cycles = st.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

if st.button("Aplicar preset do chakra"):
    st.session_state["inhale"] = float(preset["inhale"])
    st.session_state["hold1"] = float(preset["hold1"])
    st.session_state["exhale"] = float(preset["exhale"])
    st.session_state["hold2"] = float(preset["hold2"])
    st.session_state["cycles"] = int(preset["cycles"])
    st.success("Preset aplicado. Ajuste os valores se desejar e inicie a prática.")

# acessibilidade e opções
st.sidebar.subheader("Opções")
no_audio = st.sidebar.checkbox("Sem áudio (visual apenas)", value=False)
speak_enabled = st.sidebar.checkbox("Voz do navegador (Inspire/Expire)", value=True)
visual_only = st.sidebar.checkbox("Modo visual simplificado", value=False)
adaptive_rhythm = st.sidebar.checkbox("Variação adaptativa leve (±5%)", value=True)

# -------------------------
# Função que injeta HTML/JS com Web Speech API
# -------------------------
def breathing_animation_html_with_voice(
    inhale: float, exhale: float, hold1: float, hold2: float, cycles: int,
    color: str, label_prefix: str = "", speak_enabled: bool = True, voice_lang: str = "pt-BR", cue_pattern: str = "single",
    use_bell: bool = True
) -> str:
    inh_ms = int(inhale * 1000)
    h1_ms = int(hold1 * 1000)
    exh_ms = int(exhale * 1000)
    h2_ms = int(hold2 * 1000)
    cycles_js = int(cycles)
    speak_flag = "true" if speak_enabled else "false"
    bell_flag = "true" if use_bell else "false"

    html = f"""
<style>
  .breath-wrap {{ display:flex; align-items:center; justify-content:center; flex-direction:column; }}
  .circle {{ width:160px; height:160px; border-radius:50%; background: radial-gradient(circle at 30% 30%, #fff8, {color}); box-shadow: 0 12px 36px rgba(0,0,0,0.08); transform-origin:center; }}
  .label {{ margin-top:12px; font-size:18px; font-weight:600; color:#222; }}
</style>
<div class="breath-wrap">
  <div id="circle" class="circle" aria-hidden="true"></div>
  <div id="label" class="label">{label_prefix}Prepare-se...</div>
</div>
<script>
(function(){{ 
  const circle = document.getElementById("circle");
  const label = document.getElementById("label");
  const inhale = {inh_ms};
  const hold1 = {h1_ms};
  const exhale = {exh_ms};
  const hold2 = {h2_ms};
  const cycles = {cycles_js};
  const speakEnabled = {speak_flag};
  const voiceLang = "{voice_lang}";
  const cuePattern = "{cue_pattern}";
  const useBell = {bell_flag};

  function setLabel(text){{ label.textContent = text; }}

  // WebAudio bell (soft ping) com envelope
  function playBell(freq=440, duration=0.12, volume=0.06) {{
    try {{
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.type = 'sine';
      o.frequency.value = freq;
      g.gain.value = 0.0;
      o.connect(g);
      g.connect(ctx.destination);
      const now = ctx.currentTime;
      // envelope suave
      g.gain.linearRampToValueAtTime(volume, now + 0.01);
      g.gain.linearRampToValueAtTime(0.0, now + duration);
      o.start(now);
      o.stop(now + duration + 0.02);
      // fechar contexto após curto delay para liberar recursos
      setTimeout(()=>{{ try{{ ctx.close(); }}catch(e){{}} }}, (duration+0.1)*1000);
    }} catch(e){{ /* falha silenciosa */ }}
  }}

  // Seleciona voz preferencial (prioriza pt-BR e vozes de qualidade)
  function pickVoice() {{
    const voices = window.speechSynthesis.getVoices() || [];
    if (voices.length === 0) return null;
    let candidates = voices.filter(v => v.lang && v.lang.toLowerCase().startsWith(voiceLang.toLowerCase()));
    if (candidates.length === 0) candidates = voices;
    let preferred = candidates.find(v => /google|microsoft|amazon|neural|wave/i.test(v.name));
    if (!preferred) preferred = candidates[0];
    return preferred;
  }}

  // Fala assíncrona que resolve quando termina; não cancela fala anterior imediatamente
  function speakAsync(text, voice, opts) {{
    return new Promise(resolve => {{
      if (!speakEnabled || !window.speechSynthesis) return resolve();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = voiceLang;
      u.rate = opts.rate || 0.92;    // mais lento por padrão
      u.pitch = opts.pitch || 0.92;  // pitch levemente reduzido
      u.volume = opts.volume || 0.75; // volume moderado
      if (voice) u.voice = voice;
      u.onend = () => resolve();
      u.onerror = () => resolve();
      try {{ window.speechSynthesis.speak(u); }} catch(e){{ resolve(); }}
    }});
  }}

  async function ensureVoicesLoaded() {{
    return new Promise(r => {{
      const v = window.speechSynthesis.getVoices();
      if (v.length > 0) return r();
      window.speechSynthesis.onvoiceschanged = function(){{ r(); }};
      setTimeout(r, 800);
    }});
  }}

  async function runCycle() {{
    if (speakEnabled && window.speechSynthesis) {{
      await ensureVoicesLoaded();
    }}
    const voice = pickVoice();

    // preparação curta e suave
    setLabel("Prepare-se");
    if (useBell) playBell(520, 0.12, 0.04);
    if (speakEnabled) await speakAsync("Prepare-se, com calma", voice, {{rate:0.92, pitch:0.95, volume:0.75}});
    await new Promise(r => setTimeout(r, 400));

    for (let cycle = 0; cycle < cycles; cycle++) {{
      // INHALE
      setLabel("Inspire devagar e profundamente");
      circle.style.transition = "transform " + (inhale/1000) + "s ease-in-out";
      circle.style.transform = "scale(1.35)";
      if (useBell) playBell(520, 0.08, 0.04);
      if (speakEnabled) {{
        // frases mais longas e suaves
        if (cuePattern === "double") speakAsync("Inspire devagar e profundamente", voice, {{rate:0.96, pitch:0.98, volume:0.78}});
        else if (cuePattern === "soft") speakAsync("Inspire devagar e profundamente", voice, {{rate:0.9, pitch:0.9, volume:0.7}});
        else speakAsync("Inspire devagar e profundamente", voice, {{rate:0.92, pitch:0.92, volume:0.75}});
      }}
      await new Promise(r => setTimeout(r, inhale));

      // HOLD1
      if (hold1 > 0) {{
        setLabel("Segure");
        await new Promise(r => setTimeout(r, hold1));
      }}

      // EXHALE
      setLabel("Expire devagar e completamente");
      circle.style.transition = "transform " + (exhale/1000) + "s ease-in-out";
      circle.style.transform = "scale(0.75)";
      if (useBell) playBell(420, 0.08, 0.04); // tom ligeiramente mais grave
      if (speakEnabled) {{
        if (cuePattern === "double") speakAsync("Expire devagar e completamente", voice, {{rate:0.94, pitch:0.9, volume:0.78}});
        else if (cuePattern === "soft") speakAsync("Expire devagar e completamente", voice, {{rate:0.88, pitch:0.88, volume:0.7}});
        else speakAsync("Expire devagar e completamente", voice, {{rate:0.92, pitch:0.9, volume:0.75}});
      }}
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

  runCycle();
}})();
</script>
"""
    return html

# -------------------------
# Controles principais
# -------------------------
col1, col2 = st.columns([1, 1])
with col1:
    start_btn = st.button("▶️ Iniciar prática")
with col2:
    stop_btn = st.button("⏹️ Parar (interrompe visual)")

# exibir afirmação do chakra
st.markdown("**Afirmação**")
st.info(theme["affirmation"])

# -------------------------
# Execução: injetar HTML/JS com voz (cliente)
# -------------------------
if start_btn:
    # carregar valores possivelmente atualizados na sessão
    inhale = float(st.session_state.get("inhale", inhale))
    hold1 = float(st.session_state.get("hold1", hold1))
    exhale = float(st.session_state.get("exhale", exhale))
    hold2 = float(st.session_state.get("hold2", hold2))
    cycles = int(st.session_state.get("cycles", cycles))

    # montar HTML/JS e renderizar (voz roda no navegador)
    html = breathing_animation_html_with_voice(
        inhale=inhale,
        exhale=exhale,
        hold1=hold1,
        hold2=hold2,
        cycles=cycles,
        color=theme["color"],
        label_prefix=theme["label"] + " — " if "label" in theme else "",
        speak_enabled=(speak_enabled and not no_audio),
        voice_lang="pt-BR",
        cue_pattern=theme.get("cue", "single")
    )
    st.components.v1.html(html, height=360)

    # visual fallback/placeholder para acompanhar (servidor)
    placeholder = st.empty()
    total_time = (inhale + hold1 + exhale + hold2) * cycles
    elapsed = 0.0
    progress = st.progress(0)
    for c in range(int(cycles)):
        if stop_btn:
            placeholder.markdown("### ⏹️ Sessão interrompida.")
            break
        # aplicar variação adaptativa leve
        if adaptive_rhythm:
            inh = max(0.5, round(inhale * (1.0 + 0.05 * (0.5 - (time.time() % 1)))), 2)
            exh = max(0.5, round(exhale * (1.0 + 0.05 * (0.5 - ((time.time()+0.3) % 1)))), 2)
        else:
            inh = inhale
            exh = exhale

        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inh}s**")
        if not visual_only:
            time.sleep(inh)
        else:
            time.sleep(max(0.2, inh * 0.2))
        elapsed += inh
        progress.progress(min(1.0, elapsed / total_time))

        if hold1 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1}s**")
            if not visual_only:
                time.sleep(hold1)
            else:
                time.sleep(max(0.2, hold1 * 0.2))
            elapsed += hold1
            progress.progress(min(1.0, elapsed / total_time))

        placeholder.markdown(f"### 💨 Expire por **{exh}s**")
        if not visual_only:
            time.sleep(exh)
        else:
            time.sleep(max(0.2, exh * 0.2))
        elapsed += exh
        progress.progress(min(1.0, elapsed / total_time))

        if hold2 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2}s**")
            if not visual_only:
                time.sleep(hold2)
            else:
                time.sleep(max(0.2, hold2 * 0.2))
            elapsed += hold2
            progress.progress(min(1.0, elapsed / total_time))

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")
    progress.progress(1.0)

# -------------------------
# Segurança e notas finais
# -------------------------
st.markdown("---")
st.subheader("Recursos e segurança")
st.markdown(
    """
- **Contraindicações:** se tiver problemas respiratórios, cardíacos, pressão alta, gravidez ou qualquer condição médica, consulte um profissional antes de praticar.
- **Dica:** pratique sentado com coluna ereta e ombros relaxados. Evite prender a respiração de forma forçada.
- **Nota técnica:** a voz é gerada pelo navegador (Web Speech API). Em alguns navegadores a voz pt-BR pode não estar disponível; nesses casos a fala pode usar outra voz instalada.
"""
)
st.caption("Pranaterapia — práticas guiadas para integrar respiração, presença e intenção.")