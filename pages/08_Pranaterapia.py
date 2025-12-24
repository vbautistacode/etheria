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

# defina intent primeiro
intent = st.selectbox(
    "Prática",
    options=[
        "Respiração guiada",
        "Respiração quadrada (Box Breathing)",
        "Respiração alternada (Nadi Shodhana)",
    ],
)

# Renderiza botões apenas quando NÃO for "Respiração guiada"
if intent != "Respiração guiada":
    col_start, col_stop = st.columns([1, 1])
    with col_start:
        start_btn = st.button("▶️ Iniciar prática")
    with col_stop:
        stop_btn = st.button("⏹️ Parar prática")
else:
    # evita NameError em código que verifica start_btn/stop_btn
    start_btn = None
    stop_btn = None

# comportamento do botão Parar (se existir)
if stop_btn:
    st.session_state.stop_flag = True
    st.session_state.playing = False
    st.success("Prática interrompida. Aguarde a atualização da interface.")

# ---------------------------------------------------------
# Função de ciclo de respiração (servidor) — mantém comportamento atual
# ---------------------------------------------------------
def breathing_cycle(inhale_s, hold1_s, exhale_s, hold2_s, cycles=5):
    """
    Executa o ciclo de respiração no servidor e atualiza placeholder/progress.
    Chame esta função diretamente quando o usuário clicar em 'Iniciar prática'.
    Atenção: esta implementação é síncrona e usa time.sleep; durante a execução
    o servidor ficará ocupado com esta função até o término.
    """
    # reset flag caso exista
    st.session_state.stop_flag = False

    placeholder = st.empty()
    total_time = (inhale_s + hold1_s + exhale_s + hold2_s) * cycles
    elapsed = 0.0
    progress = st.progress(0.0)

    for c in range(int(cycles)):
        if st.session_state.get("stop_flag", False):
            placeholder.markdown("### ⏹️ Prática interrompida.")
            return

        # Inspire
        placeholder.markdown(f"### 🌿 Ciclo {c+1}/{cycles} — Inspire por **{inhale_s}s**")
        full = int(inhale_s)
        rem = inhale_s - full
        for _ in range(full):
            if st.session_state.get("stop_flag", False):
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        # Segure 1
        if hold1_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1_s}s**")
            full = int(hold1_s)
            rem = hold1_s - full
            for _ in range(full):
                if st.session_state.get("stop_flag", False):
                    placeholder.markdown("### ⏹️ Prática interrompida.")
                    return
                time.sleep(1)
                elapsed += 1
                progress.progress(min(1.0, elapsed / total_time))
            if rem > 0:
                time.sleep(rem)
                elapsed += rem
                progress.progress(min(1.0, elapsed / total_time))

        # Expire
        placeholder.markdown(f"### 💨 Expire por **{exhale_s}s**")
        full = int(exhale_s)
        rem = exhale_s - full
        for _ in range(full):
            if st.session_state.get("stop_flag", False):
                placeholder.markdown("### ⏹️ Prática interrompida.")
                return
            time.sleep(1)
            elapsed += 1
            progress.progress(min(1.0, elapsed / total_time))
        if rem > 0:
            time.sleep(rem)
            elapsed += rem
            progress.progress(min(1.0, elapsed / total_time))

        # Segure 2
        if hold2_s > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2_s}s**")
            full = int(hold2_s)
            rem = hold2_s - full
            for _ in range(full):
                if st.session_state.get("stop_flag", False):
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
    # Bloco HTML/JS robusto: botão visual aciona o <audio>, espera o elemento aparecer e inicia esfera+contagem
    # Substitua seu bloco html_sync por este. Ele faz a esfera seguir exatamente o script
    # breathing_cycle (inhale / hold1 / exhale / hold2 / cycles) sem depender do st.audio.
    # Cole no lugar do html_sync atual e chame st.components.v1.html(html_sync, height=520).

    html_sync = f"""
<div id="prana_control_wrap_{escaped_fname}" style="display:flex;flex-direction:column;align-items:center;margin-top:12px;">
  <div id="prana_circle_{escaped_fname}" style="width:160px;height:160px;border-radius:50%;margin-top:12px;
      background:radial-gradient(circle at 30% 30%, #fff8, {color});
      box-shadow:0 12px 36px rgba(0,0,0,0.08);transform-origin:center;animation:prana_pulse_{escaped_fname} 2000ms ease-in-out infinite;cursor:pointer;">
  </div>
  <div id="prana_status_{escaped_fname}" style="margin-top:8px;font-weight:600;color:#222">Pronto</div>
  <div id="prana_breath_log_{escaped_fname}" style="min-height:36px;color:#333;font-weight:600;margin-top:8px;"></div>
</div>

<style>
@keyframes prana_pulse_{escaped_fname} {{ 0%{{transform:scale(1)}}50%{{transform:scale(1.04)}}100%{{transform:scale(1)}} }}
</style>

<script>
(function(){{
  const filename = "{escaped_fname}";
  const circle = document.getElementById('prana_circle_' + filename);
  const statusEl = document.getElementById('prana_status_' + filename);
  const logEl = document.getElementById('prana_breath_log_' + filename);

  const inhale = {inhale};
  const hold1 = {hold1};
  const exhale = {exhale};
  const hold2 = {hold2};
  const cycles = {int(cycles)};

  function setStatus(t){{ if (statusEl) statusEl.textContent = t; }}
  function setLog(t){{ if (logEl) logEl.textContent = t; console.log('[prana]', t); }}

  // util: encontra <audio> do st.audio pelo nome do arquivo (robusto)
  function findAudioByFilename(fname) {{
    const audios = Array.from(document.querySelectorAll('audio'));
    for (const a of audios) {{
      try {{
        const src = a.currentSrc || a.src || (a.querySelector && a.querySelector('source') && a.querySelector('source').src);
        if (src && (src.indexOf(fname) !== -1 || src.endsWith(fname))) return a;
      }} catch (e) {{ /* ignore */ }}
    }}
    if (audios.length === 1) return audios[0];
    return null;
  }}

  // mapeia um tempo (s) para ciclo/segmento/progresso
  function mapTimeToSegment(t_seconds, inhale, hold1, exhale, hold2, cycles) {{
    const segDur = [inhale, hold1, exhale, hold2];
    const cycleDuration = segDur.reduce((a,b)=>a+b,0);
    const totalDuration = cycleDuration * cycles;
    if (t_seconds <= 0) return {{ cycle:0, segIndex:0, segProgress:0, finished:false }};
    if (t_seconds >= totalDuration) return {{ cycle: cycles-1, segIndex:3, segProgress:1, finished:true }};
    const timeInTotal = Math.min(t_seconds, totalDuration);
    const cycle = Math.floor(timeInTotal / cycleDuration);
    let timeInCycle = timeInTotal - cycle * cycleDuration;
    let segIndex = 0;
    while (segIndex < 4 && timeInCycle > segDur[segIndex]) {{
      timeInCycle -= segDur[segIndex];
      segIndex++;
    }}
    const segDuration = segDur[segIndex] || 0.0001;
    const segProgress = Math.min(1, segDuration > 0 ? timeInCycle / segDuration : 1);
    return {{ cycle, segIndex, segProgress, finished:false }};
  }}

  // converte segmento/progresso em escala da esfera
  function scaleFor(segIndex, segProgress, prevSegIndex) {{
    const minScale = 1.0, maxScale = 1.25;
    if (segIndex === 0) {{
      const eased = Math.sin(segProgress * Math.PI / 2);
      return minScale + (maxScale - minScale) * eased;
    }} else if (segIndex === 2) {{
      const eased = 1 - Math.cos(segProgress * Math.PI / 2);
      return maxScale - (maxScale - minScale) * eased;
    }} else {{
      return (prevSegIndex === 0) ? maxScale : minScale;
    }}
  }}

  // cria um <audio> fallback embutido (opcional) e retorna o elemento
  function createEmbeddedAudio(dataUrl) {{
    try {{
      const a = document.createElement('audio');
      a.style.display = 'none';
      a.src = dataUrl;
      a.preload = 'auto';
      document.body.appendChild(a);
      return a;
    }} catch (e) {{
      console.warn('Falha ao criar audio embutido', e);
      return null;
    }}
  }}

  // anexa listeners nativos ao audio para refletir estado na UI
  function attachNativeListeners(a) {{
    if (!a || a._prana_native_attached) return;
    a._prana_native_attached = true;
    a.addEventListener('play', () => {{
      setStatus('Tocando (nativo)');
      setLog('Áudio: play');
    }});
    a.addEventListener('pause', () => {{
      setStatus('Pausado (nativo)');
      setLog('Áudio: pause');
    }});
    a.addEventListener('ended', () => {{
      setStatus('Concluído (nativo)');
      setLog('Áudio: ended');
    }});
  }}

  // loop visual que usa audio.currentTime quando disponível; senão usa relógio cliente
  function startVisualLoop(opts) {{
    const {{ audio, circleEl, statusEl, logEl, inhale, hold1, exhale, hold2, cycles }} = opts;
    let raf = null;
    let prevSegIndex = 0;

    function frame() {{
      if (audio && !isNaN(audio.duration) && audio.duration > 0) {{
        // mapeia currentTime do áudio para o tempo do script
        const cycleDuration = (inhale + hold1 + exhale + hold2);
        const totalScriptDuration = cycleDuration * cycles;
        const scaleFactor = (audio.duration > 0) ? (totalScriptDuration / audio.duration) : 1;
        const mappedTime = audio.currentTime * scaleFactor;
        const mapped = mapTimeToSegment(mappedTime, inhale, hold1, exhale, hold2, cycles);
        const segLabel = ['Inspire','Segure','Expire','Segure'][mapped.segIndex];
        const segDur = [inhale, hold1, exhale, hold2][mapped.segIndex] || 0;
        const remaining = Math.max(0, Math.ceil(segDur * (1 - mapped.segProgress)));
        if (logEl) logEl.textContent = 'Ciclo ' + (mapped.cycle+1) + '/' + cycles + ' — ' + segLabel + ' ' + remaining + 's';
        if (statusEl) statusEl.textContent = audio.paused ? 'Pausado (nativo)' : 'Tocando (nativo)';
        const scale = scaleFor(mapped.segIndex, mapped.segProgress, prevSegIndex);
        circleEl.style.transform = 'scale(' + scale + ')';
        prevSegIndex = mapped.segIndex;
        if (!audio.paused) {{
          raf = requestAnimationFrame(frame);
        }} else {{
          if (raf) cancelAnimationFrame(raf);
          raf = null;
        }}
      }} else {{
        // fallback: relógio cliente
        if (!opts._clientState) {{
          opts._clientState = {{ start: performance.now() }};
        }}
        const elapsed = (performance.now() - opts._clientState.start) / 1000;
        const mapped = mapTimeToSegment(elapsed, inhale, hold1, exhale, hold2, cycles);
        const segLabel = ['Inspire','Segure','Expire','Segure'][mapped.segIndex];
        const segDur = [inhale, hold1, exhale, hold2][mapped.segIndex] || 0;
        const remaining = Math.max(0, Math.ceil(segDur * (1 - mapped.segProgress)));
        if (logEl) logEl.textContent = 'Ciclo ' + (mapped.cycle+1) + '/' + cycles + ' — ' + segLabel + ' ' + remaining + 's';
        if (statusEl) statusEl.textContent = 'Executando (cliente)';
        const scale = scaleFor(mapped.segIndex, mapped.segProgress, prevSegIndex);
        circleEl.style.transform = 'scale(' + scale + ')';
        prevSegIndex = mapped.segIndex;
        raf = requestAnimationFrame(frame);
      }}
    }}

    if (!raf) raf = requestAnimationFrame(frame);
    return () => {{ if (raf) cancelAnimationFrame(raf); raf = null; }};
  }}

  // fluxo principal: clique na esfera tenta tocar st.audio; se não houver, cria fallback e usa loop cliente
  let visualStopFn = null;
  let embeddedAudio = null;

  async function tryStartFromSphere() {{
    setLog('Tentando iniciar via player nativo...');
    let audio = findAudioByFilename(filename);

    if (!audio) {{
      setLog('Player nativo não encontrado. Observando DOM por 3s...');
      let handled = false;
      const obs = new MutationObserver((mutations, observer) => {{
        audio = findAudioByFilename(filename);
        if (audio && !handled) {{
          handled = true;
          observer.disconnect();
          attachNativeListeners(audio);
          // start visual loop using this audio
          if (visualStopFn) visualStopFn();
          visualStopFn = startVisualLoop({{ audio, circleEl: circle, statusEl, logEl, inhale, hold1, exhale, hold2, cycles }});
          audio.play().then(() => setStatus('Tocando (nativo)')).catch(err => {{
            console.warn('play rejected after found', err);
            setStatus('Clique no player nativo se bloqueado');
          }});
        }}
      }});
      obs.observe(document.body, {{ childList: true, subtree: true }});

      // fallback: após 3s cria áudio embutido se você tiver data URL disponível (opcional)
      setTimeout(() => {{
        if (!handled) {{
          observer.disconnect && observer.disconnect();
          const fallbackAudio = document.querySelector('audio');
          if (fallbackAudio) {{
            audio = fallbackAudio;
            attachNativeListeners(audio);
            if (visualStopFn) visualStopFn();
            visualStopFn = startVisualLoop({{ audio, circleEl: circle, statusEl, logEl, inhale, hold1, exhale, hold2, cycles }});
            audio.play().then(() => setStatus('Tocando (fallback)')).catch(err => {{
              console.warn('fallback play failed', err);
              setStatus('Clique no player nativo se bloqueado');
            }});
            return;
          }}
          // Se não há nenhum audio no DOM, usar loop cliente (sem som)
          setLog('Nenhum player encontrado — iniciando visual sem áudio (cliente).');
          if (visualStopFn) visualStopFn();
          visualStopFn = startVisualLoop({{ audio: null, circleEl: circle, statusEl, logEl, inhale, hold1, exhale, hold2, cycles }});
        }}
      }}, 3000);

      return;
    }}

    // se encontrou audio imediatamente
    attachNativeListeners(audio);
    if (visualStopFn) visualStopFn();
    visualStopFn = startVisualLoop({{ audio, circleEl: circle, statusEl, logEl, inhale, hold1, exhale, hold2, cycles }});
    try {{
      await audio.play();
      setStatus('Tocando (nativo)');
    }} catch (err) {{
      console.warn('play rejected', err);
      setStatus('Clique no player nativo se bloqueado');
    }}
  }}

  // clique na esfera: inicia/pausa dependendo do estado do audio/visual
  circle.addEventListener('click', async () => {{
    try {{
      // se já existe um audio nativo e está tocando, pause-o
      const audio = findAudioByFilename(filename);
      if (audio) {{
        if (!audio.paused) {{
          audio.pause();
          setStatus('Pausado (nativo)');
          setLog('Pausado pelo clique na esfera');
          return;
        }} else {{
          // se está pausado, tocar
          await audio.play().then(() => setStatus('Tocando (nativo)')).catch(err => {{
            console.warn('play rejected on click', err);
            setStatus('Clique no player nativo se bloqueado');
          }});
          return;
        }}
      }}
      // se não há audio nativo, tenta iniciar via fluxo principal
      await tryStartFromSphere();
    }} catch (err) {{
      console.warn('Erro no clique da esfera', err);
      setStatus('Erro interno');
    }}
  }});

  // duplo clique para parar visual e áudio embutido (se houver)
  circle.addEventListener('dblclick', () => {{
    try {{
      if (visualStopFn) visualStopFn();
      const audio = findAudioByFilename(filename) || embeddedAudio;
      if (audio) {{
        try {{ audio.pause(); audio.currentTime = 0; }} catch(e){{}}
      }}
      setStatus('Parado');
      setLog('');
      circle.style.animation = 'prana_pulse_{escaped_fname} 2000ms ease-in-out infinite';
    }} catch (err) {{
      console.warn('Erro no dblclick', err);
      setStatus('Erro interno');
    }}
  }});

  // inicialização visual
  setStatus('Pronto (cliente)');
  setLog('Clique na esfera para iniciar; ela tentará tocar o player nativo e sincronizar-se ao áudio.');

}})();
</script>
"""

    st.components.v1.html(html_sync, height=520)

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