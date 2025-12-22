# 08_pranaterapia.py
import streamlit as st
import time

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
# Seleção de intenção
# -------------------------
st.subheader("🎯 Escolha sua intenção")

intent = st.selectbox(
    "Selecione uma prática:",
    [
        "Calma imediata",
        "Foco e clareza",
        "Sono e desaceleração",
        "Energia suave",
        "Respiração completa (Pranayama básico)",
        "Respiração quadrada (Box Breathing)",
        "Respiração alternada (Nadi Shodhana)",
    ],
)

st.divider()

# -------------------------
# Funções auxiliares
# -------------------------
def breathing_cycle(inhale, hold1, exhale, hold2, cycles=5, label="Respire"):
    """
    Pequeno guia visual de respiração com contagem.
    """
    placeholder = st.empty()
    for _ in range(cycles):
        placeholder.markdown(f"### 🌿 Inspire por **{inhale}s**")
        time.sleep(inhale)

        if hold1 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold1}s**")
            time.sleep(hold1)

        placeholder.markdown(f"### 💨 Expire por **{exhale}s**")
        time.sleep(exhale)

        if hold2 > 0:
            placeholder.markdown(f"### ⏸️ Segure por **{hold2}s**")
            time.sleep(hold2)

    placeholder.markdown("### ✔️ Prática concluída. Observe como você se sente.")


# -------------------------
# Conteúdo por intenção
# -------------------------

if intent == "Calma imediata":
    st.subheader("🌿 Calma imediata")
    st.markdown(
        """
Respiração simples para reduzir tensão e ativar o sistema parassimpático.

**Ciclo sugerido:**  
- Inspire: 4s  
- Expire: 6s  
- Sem retenção  
- 6 ciclos
"""
    )
    if st.button("Iniciar prática"):
        breathing_cycle(4, 0, 6, 0, cycles=6)

elif intent == "Foco e clareza":
    st.subheader("🎯 Foco e clareza")
    st.markdown(
        """
Respiração energizante e estável para clarear a mente.

**Ciclo sugerido:**  
- Inspire: 4s  
- Segure: 2s  
- Expire: 4s  
- Segure: 2s  
- 5 ciclos
"""
    )
    if st.button("Iniciar prática"):
        breathing_cycle(4, 2, 4, 2, cycles=5)

elif intent == "Sono e desaceleração":
    st.subheader("🌙 Sono e desaceleração")
    st.markdown(
        """
Respiração longa e suave para induzir relaxamento profundo.

**Ciclo sugerido:**  
- Inspire: 4s  
- Expire: 8s  
- 8 ciclos
"""
    )
    if st.button("Iniciar prática"):
        breathing_cycle(4, 0, 8, 0, cycles=8)

elif intent == "Energia suave":
    st.subheader("🔥 Energia suave")
    st.markdown(
        """
Respiração ritmada para despertar o corpo sem agitação.

**Ciclo sugerido:**  
- Inspire: 3s  
- Segure: 1s  
- Expire: 3s  
- Segure: 1s  
- 6 ciclos
"""
    )
    if st.button("Iniciar prática"):
        breathing_cycle(3, 1, 3, 1, cycles=6)

elif intent == "Respiração completa (Pranayama básico)":
    st.subheader("🌬️ Respiração completa")
    st.markdown(
        """
A respiração completa envolve abdômen, costelas e peito — enchendo os pulmões de forma natural e fluida.

**Ciclo sugerido:**  
- Inspire: 5s  
- Segure: 2s  
- Expire: 7s  
- 5 ciclos
"""
    )
    if st.button("Iniciar prática"):
        breathing_cycle(5, 2, 7, 0, cycles=5)

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
    if st.button("Iniciar prática"):
        breathing_cycle(4, 4, 4, 4, cycles=5)

elif intent == "Respiração alternada (Nadi Shodhana)":
    st.subheader("🔄 Respiração alternada (Nadi Shodhana)")
    st.markdown(
        """
Técnica tradicional para equilibrar os canais energéticos (nadis) e acalmar a mente.

**Instruções:**  
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
    st.info("Esta técnica é guiada por instruções, não por contagem automática.")