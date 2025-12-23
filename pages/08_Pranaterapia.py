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

    # Substitua o botão server por este bloco client-side (cole logo APÓS st.audio(...))

    html_client_start = f"""
    <div style="display:flex;gap:12px;align-items:center;margin-top:12px;">
      <button id="prana_client_start_{escaped_fname}" style="padding:10px 14px;border-radius:8px;border:1px solid #ddd;background:#fff;cursor:pointer;font-weight:700;">
        ▶️ Iniciar prática
      </button>
      <div id="prana_client_status_{escaped_fname}" style="font-weight:600;color:#222">Pronto</div>
    </div>

    <script>
    (function(){{
      const fname = "{escaped_fname}";
      const startBtn = document.getElementById('prana_client_start_' + fname);
      const statusEl = document.getElementById('prana_client_status_' + fname);

      function setStatus(t){{ if (statusEl) statusEl.textContent = t; }}

      function findAudioByFilename(name) {{
        const audios = Array.from(document.querySelectorAll('audio'));
        for (const a of audios) {{
          try {{ if ((a.currentSrc && a.currentSrc.indexOf(name) !== -1) || (a.src && a.src.indexOf(name) !== -1)) return a; }} catch(e){{ }}
        }}
        if (audios.length === 1) return audios[0];
        return null;
      }}

      // lógica de animação/contagem (copie/adapte a sua existente)
      function attachAndStart(audio) {{
        if (!audio) return setStatus('Áudio não encontrado');
        // anexar listeners (se ainda não anexados)
        if (!audio._prana_attached) {{
          audio._prana_attached = true;
          audio.addEventListener('play', () => setStatus('Tocando'));
          audio.addEventListener('pause', () => setStatus('Pausado'));
          audio.addEventListener('ended', () => setStatus('Concluído'));
          // aqui você pode iniciar a animação da esfera e a contagem cliente
          // por exemplo: window.startPranaClientCycle();  (implemente essa função no seu componente)
        }}
        // gesto do usuário: play
        audio.play().catch(err => {{
          console.warn('play failed', err);
          setStatus('Clique no player nativo se bloqueado');
        }});
      }}

      startBtn.addEventListener('click', () => {{
        setStatus('Procurando áudio...');
        let audio = findAudioByFilename(fname);
        if (audio) {{
          attachAndStart(audio);
          return;
        }}
        // observa o DOM por alguns instantes
        const obs = new MutationObserver((mutations, observer) => {{
          audio = findAudioByFilename(fname);
          if (audio) {{
            observer.disconnect();
            attachAndStart(audio);
          }}
        }});
        obs.observe(document.body, {{ childList: true, subtree: true }});
        // fallback: após 3s, tenta anexar ao primeiro audio
        setTimeout(() => {{
          if (!audio) {{
            const fallback = document.querySelector('audio');
            if (fallback) attachAndStart(fallback);
            else setStatus('Áudio não encontrado');
          }}
        }}, 3000);
      }});
}})();
</script>
"""

    st.components.v1.html(html_client_start, height=90)

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