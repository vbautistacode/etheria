# 08_pranaterapia.py (integração: st.audio controla esfera e ciclo no cliente)
import time
from pathlib import Path
from html import escape

import streamlit as st

# ---------------------------------------------------------
# Configuração inicial
# ---------------------------------------------------------
st.title("Pranaterapia 🌬️")
st.markdown(
    "Pranaterapia: práticas guiadas de respiração e meditação centradas no prana (energia vital). "
    "Sessões curtas por intenção (calma, foco, sono) e exercícios para integrar respiração e presença."
)
st.caption(
    "Escolha um chakra; se a prática for 'Respiração guiada' o áudio correspondente será carregado. "
    "Use o player nativo para iniciar, pausar ou parar — a esfera e a contagem responderão automaticamente."
)

# ---------------------------------------------------------
# Presets por chakra
# ---------------------------------------------------------
CHAKRAS = {
    "Muladhara": {"color": "#CC0700", "preset": {"inhale": 3, "hold1": 0, "exhale": 4, "hold2": 0, "cycles": 6}, "affirmation": "Estou seguro e enraizado."},
    "Svadhisthana": {"color": "#6A0F60", "preset": {"inhale": 3, "hold1": 0, "exhale": 3, "hold2": 0, "cycles": 6}, "affirmation": "Minha criatividade flui."},
    "Manipura": {"color": "#F17C0F", "preset": {"inhale": 2.5, "hold1": 0, "exhale": 2.5, "hold2": 0, "cycles": 8}, "affirmation": "Ação com clareza."},
    "Anahata": {"color": "#3DAE27", "preset": {"inhale": 4, "hold1": 0, "exhale": 6, "hold2": 0, "cycles": 6}, "affirmation": "Abro meu coração."},
    "Vishuddha": {"color": "#346CDB", "preset": {"inhale": 4, "hold1": 1, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Comunico com verdade."},
    "Ajna": {"color": "#F4E922", "preset": {"inhale": 4, "hold1": 2, "exhale": 4, "hold2": 0, "cycles": 5}, "affirmation": "Minha percepção se afina."},
    "Sahasrara": {"color": "#DF27C3", "preset": {"inhale": 5, "hold1": 0, "exhale": 7, "hold2": 0, "cycles": 4}, "affirmation": "Conecto-me ao silêncio."},
}

# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
BASE_DIR = Path(__file__).parent
PROJECT_ROOT = BASE_DIR.parent
STATIC_ROOT = PROJECT_ROOT / "static"
SESSIONS_DIR = STATIC_ROOT / "audio" / "sessions"

# ---------------------------------------------------------
# Sidebar e controles (sem autoplay exposto)
# ---------------------------------------------------------
st.sidebar.header("Configurações da sessão")
chakra = st.sidebar.selectbox("Chakra", options=list(CHAKRAS.keys()))
theme = CHAKRAS[chakra]

preset = theme["preset"]
inhale = st.sidebar.number_input("Inspire", value=float(preset["inhale"]), min_value=1.0, max_value=60.0, step=0.5)
hold1 = st.sidebar.number_input("Segure após inspirar", value=float(preset["hold1"]), min_value=0.0, max_value=60.0, step=0.5)
exhale = st.sidebar.number_input("Expire", value=float(preset["exhale"]), min_value=1.0, max_value=120.0, step=0.5)
hold2 = st.sidebar.number_input("Segure após expirar", value=float(preset["hold2"]), min_value=0.0, max_value=60.0, step=0.5)
cycles = st.sidebar.number_input("Ciclos", value=int(preset["cycles"]), min_value=1, max_value=200, step=1)

# ---------------------------------------------------------
# Session state
# ---------------------------------------------------------
if "playing" not in st.session_state:
    st.session_state.playing = False
if "stop_flag" not in st.session_state:
    st.session_state.stop_flag = False

# ---------------------------------------------------------
# Interface principal
# ---------------------------------------------------------
st.subheader(f"{chakra} — Foco: {theme['affirmation']}")
st.markdown(f"<div style='height:8px;background:{theme['color']};border-radius:6px;margin-bottom:8px'></div>", unsafe_allow_html=True)

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
# Função de ciclo de respiração (servidor) — mantém comportamento atual
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# Quando o usuário clica em Start (servidor) mantemos a flag
# ---------------------------------------------------------
if start_btn:
    st.session_state.stop_flag = False
    st.session_state.playing = True

    if intent == "Respiração guiada":
        # opcional: não iniciar contagem server-side automaticamente; a contagem cliente será a principal
        # manter a chamada server-side caso queira registro ou fallback
        pass
    elif intent == "Respiração quadrada (Box Breathing)":
        st.subheader("🫁 Respiração quadrada (Box Breathing)")
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
        # não forçar reprodução do áudio aqui; o usuário usará o player nativo
    elif intent == "Respiração alternada (Nadi Shodhana)":
        st.subheader("🫁🔀 Respiração alternada (Nadi Shodhana)")
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
             Repita por 6 ciclos. """ 
        )

# ---------------------------------------------------------
# Localizar e renderizar o áudio (st.audio) e sincronizar com esfera e ciclo no cliente
# ---------------------------------------------------------
session_filename = f"{chakra.lower()}_session.wav"
session_path = SESSIONS_DIR / session_filename

if session_path.exists() and intent == "Respiração guiada":
    # 1) Renderiza st.audio (Streamlit serve internamente)
    try:
        st.audio(str(session_path))
    except Exception as e:
        st.error(f"Erro ao renderizar st.audio: {e}")
        st.stop()

    # 2) Injeta componente que encontra o <audio> criado por st.audio e sincroniza esfera + contagem cliente
    escaped_fname = escape(session_path.name)
    color = theme["color"]

    # HTML/JS que:
    # - localiza o <audio> do st.audio (por currentSrc / source.src / fallback)
    # - anexa listeners play/pause/ended
    # - anima a esfera com requestAnimationFrame
    # - executa a contagem de respiração no cliente (respeitando pausas do áudio)
    # Cole este trecho imediatamente após st.audio(str(session_path))
    # variáveis já presentes no seu contexto: session_path, theme, inhale, hold1, exhale, hold2, cycles

    html_visual_control = f""" <div id="prana_control_wrap_{escaped_fname}" style="display:flex;flex-direction:column;align-items:center;margin-top:12px;"> <button id="prana_visual_play_{escaped_fname}" style="padding:12px 18px;border-radius:10px;border:none;background:#fff;cursor:pointer;font-weight:700;"> ▶️ Iniciar / Pausar </button> <div id="prana_circle_{escaped_fname}" style="width:160px;height:160px;border-radius:50%;margin-top:12px; background:radial-gradient(circle at 30% 30%, #fff8, {color}); box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;animation:prana_pulse_{escaped_fname} 2000ms ease-in-out infinite;"> </div> <div id="prana_status_{escaped_fname}" style="margin-top:8px;font-weight:600;color:#222">Pronto</div> <div id="prana_breath_log_{escaped_fname}" style="min-height:36px;color:#333;font-weight:600;margin-top:8px;"></div> </div> <style> @keyframes prana_pulse_{escaped_fname} {{ 0%{{transform:scale(1)}}50%{{transform:scale(1.04)}}100%{{transform:scale(1)}} }} </style> <script> (function(){{ const filename = "{escaped_fname}"; const playBtn = document.getElementById('prana_visual_play_' + filename); const circle = document.getElementById('prana_circle_' + filename); const statusEl = document.getElementById('prana_status_' + filename); const logEl = document.getElementById('prana_breath_log_' + filename); // parâmetros vindos do servidor (usados apenas para exibir/registrar no cliente) const inhale = {inhale}; const hold1 = {hold1}; const exhale = {exhale}; const hold2 = {hold2}; const cycles = {int(cycles)}; function setStatus(t){{ if (statusEl) statusEl.textContent = t; }} function setLog(t){{ if (logEl) logEl.textContent = t; console.log('[prana]', t); }} function findAudioByFilename(fname){{ const audios = Array.from(document.querySelectorAll('audio')); for (const a of audios){{ try{{ if (a.currentSrc && a.currentSrc.indexOf(fname) !== -1) return a; }}catch(e){{}} }} for (const a of audios){{ try{{ const s = a.querySelector && a.querySelector('source') && a.querySelector('source').src; if (s && s.indexOf(fname) !== -1) return a; }}catch(e){{}} }} for (const a of audios){{ try{{ const src = a.currentSrc || a.src || (a.querySelector && a.querySelector('source') && a.querySelector('source').src); if (src && src.endsWith(fname)) return a; }}catch(e){{}} }} if (audios.length === 1) return audios[0]; return null; }} let audio = findAudioByFilename(filename); function attachListeners(a){{ if (!a) return; a.addEventListener('play', () => {{ circle.style.animation = 'none'; setStatus('Tocando'); playBtn.textContent = '⏸️ Pausar'; setLog('Áudio: play'); startClientBreathing(); // inicia contagem cliente (respeita pausas) requestAnimationFrame(animateFrame); }}); a.addEventListener('pause', () => {{ circle.style.animation = 'prana_pulse_{escaped_fname} 2000ms ease-in-out infinite'; setStatus('Pausado'); playBtn.textContent = '▶️ Iniciar / Pausar'; setLog('Áudio: pause'); pauseClientBreathing(); }}); a.addEventListener('ended', () => {{ circle.style.animation = 'prana_pulse_{escaped_fname} 2000ms ease-in-out infinite'; setStatus('Concluído'); playBtn.textContent = '▶️ Iniciar / Pausar'; setLog('Áudio: ended'); stopClientBreathing(); }}); a.addEventListener('error', () => {{ setStatus('Erro no áudio'); console.warn('audio error', a.error); }}); }} // animação da esfera baseada no tempo do áudio let raf = null; function animateFrame(){{ if (!audio || audio.paused) {{ if (raf) cancelAnimationFrame(raf); raf = null; return; }} const t = audio.currentTime || 0; const scale = 1 + 0.25 * Math.sin((t / 4.0) * Math.PI * 2); circle.style.transform = 'scale(' + scale + ')'; raf = requestAnimationFrame(animateFrame); }} // contagem de respiração no cliente (respeita pausas do áudio) let breathingRunning = false; function startClientBreathing(){{ if (breathingRunning) return; breathingRunning = true; let cycleIndex = 0; function runCycle(){{ if (!breathingRunning) return; if (cycleIndex >= cycles) {{ setLog('Prática concluída'); breathingRunning = false; return; }} cycleIndex++; const seq = [ {{label: 'Inspire', t: inhale}}, {{label: 'Segure', t: hold1}}, {{label: 'Expire', t: exhale}}, {{label: 'Segure', t: hold2}} ]; let segIndex = 0; function nextSegment(){{ if (!breathingRunning) return; if (segIndex >= seq.length) {{ setTimeout(runCycle, 200); return; }} const seg = seq[segIndex++]; if (seg.t <= 0) {{ nextSegment(); return; }} setLog('Ciclo ' + cycleIndex + '/' + cycles + ' — ' + seg.label + ' ' + seg.t + 's'); const start = performance.now(); function waitLoop(){{ if (!breathingRunning) return; if (audio && audio.paused) {{ setTimeout(waitLoop, 200); return; }} const elapsed = (performance.now() - start) / 1000; if (elapsed >= seg.t) {{ nextSegment(); }} else {{ requestAnimationFrame(waitLoop); }} }} waitLoop(); }} nextSegment(); }} runCycle(); }} function pauseClientBreathing(){{ breathingRunning = false; }} function stopClientBreathing(){{ breathingRunning = false; setLog(''); }} // ação do botão visual: play/pause do <audio> playBtn.addEventListener('click', async () => {{ try {{ if (!audio) {{ audio = findAudioByFilename(filename); if (audio) attachListeners(audio); }} if (!audio) {{ setStatus('Áudio não encontrado'); return; }} if (audio.paused) {{ await audio.play(); setStatus('Tocando'); }} else {{ audio.pause(); setStatus('Pausado'); }} }} catch (err) {{ console.warn('play failed', err); setStatus('Clique no player nativo se bloqueado'); }} }}); // se o audio ainda não existir, observar o DOM e anexar quando aparecer if (audio) {{ attachListeners(audio); }} else {{ const obs = new MutationObserver((mutations, observer) => {{ audio = findAudioByFilename(filename); if (audio) {{ attachListeners(audio); observer.disconnect(); }} }}); obs.observe(document.body, {{ childList: true, subtree: true }}); // fallback: após 3s, se houver apenas 1 audio, anexa a ele setTimeout(() => {{ if (!audio) {{ const fallback = document.querySelector('audio'); if (fallback) {{ audio = fallback; attachListeners(audio); console.warn('Fallback: anexado ao primeiro <audio>'); }} }} }}, 3000); }} }})(); </script> """ 
  
    st.components.v1.html(html_sync, height=460)

else:
    # se não houver áudio para a prática selecionada, apenas mostra instruções
    if intent != "Respiração guiada":
        st.info("Esta prática não possui áudio associado. Use as instruções na tela para guiar a respiração.")
    else:
        st.warning(f"Áudio de sessão não encontrado: {session_path}")

# ---------------------------------------------------------
# Rodapé: instruções rápidas, segurança e saúde
# ---------------------------------------------------------
st.markdown("---")
st.caption(
    """
**Aviso de segurança e saúde:**  
- Este conteúdo é apenas para fins informativos e de bem‑estar geral; não substitui orientação médica ou terapêutica profissional.  
- Interrompa a prática imediatamente se sentir tontura, dor no peito, falta de ar intensa, náusea, desorientação ou qualquer desconforto significativo.  
- Ajuste os tempos de respiração conforme seu conforto; não force retenções ou respirações além do que é confortável para você.
"""
)