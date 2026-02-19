# pages/11_Biohacking.py
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Biohacking", layout="wide")
st.title("Biohacking — 🧬")

st.markdown(
    """
**O que é Biohacking**

Biohacking é o conjunto de práticas, ferramentas e experimentos pessoais usados para **otimizar saúde, desempenho cognitivo e longevidade** — do simples (sono, alimentação, rastreio com wearables) ao experimental (peptídeos, implantes, biologia DIY).  
Priorize sempre intervenções não invasivas e baseadas em evidência; intervenções médicas, hormônios, peptídeos e procedimentos invasivos exigem supervisão clínica.
"""
)

# Include two short sentences taken from the provided dossier to enrich the page:
st.markdown(
    "> O corpo alterna o fluxo para permitir que os tecidos de uma narina se recuperem enquanto a outra trabalha.\n\n"
    "> A respiração é a única função do sistema nervoso autônomo que você controla conscientemente."
)

st.markdown("---")

# Quick profile
st.header("Perfil rápido (opcional)")
colp1 = st.columns([1])
with colp1[0]:
    consent = st.checkbox("Li o aviso: este conteúdo é informativo e não substitui avaliação médica", value=False)

if not consent:
    st.warning("Marque a caixa de consentimento para desbloquear ferramentas práticas.")
    st.stop()

st.markdown(
    """
## Como usar esta página
1. **Leia a explicação** e escolha 1–2 intervenções simples para testar por 1–4 semanas.  
2. **Meça**: registre sono, energia e observações diárias.  
3. **Avalie**: compare antes/depois; pare se houver sinais adversos.  
4. **Consulte um profissional** antes de suplementos fortes, hormônios ou procedimentos invasivos.
"""
)

st.markdown("---")

# Section: Core concepts (enriched from attached document)
st.header("Conceitos centrais e por que funcionam")
st.markdown(
    """
- **Hemisférios e integração**: o cérebro funciona como uma rede integrada; cada hemisfério tem especialidades (lógico/analítico vs. holístico/criativo), mas ambos trabalham juntos via corpo caloso.  
- **Narina e estado autonômico**: técnicas simples de respiração nasal podem modular o sistema nervoso (narina direita → alerta/simpático; narina esquerda → relaxamento/parassimpático).  
- **Nervos e reflexos**: práticas como expiração prolongada e exposição ao frio ativam vias (ex.: nervo vago, reflexo de mergulho) que alteram ritmo cardíaco e sensação de segurança.
"""
)

st.markdown("---")

# Section: Planner / experiments (N-of-1)
st.header("Planejador de experimentos pessoais")
st.markdown("Crie um experimento simples, defina métricas e duração. Comece pequeno (1–4 semanas).")

with st.form("experiment_form"):
    exp_name = st.text_input("Nome do experimento", value="Melhorar sono")
    exp_hypothesis = st.text_area("Hipótese (o que você espera mudar?)", value="Aumentar sono para 8h reduzirá fadiga diurna")
    metric = st.selectbox("Métrica principal", ["Horas de sono", "Qualidade do sono (0-10)", "Energia diurna (0-10)", "HRV"])
    duration_days = st.number_input("Duração (dias)", min_value=3, max_value=90, value=14)
    submit_exp = st.form_submit_button("Criar experimento")
if submit_exp:
    exp = {
        "name": exp_name,
        "hypothesis": exp_hypothesis,
        "metric": metric,
        "duration_days": int(duration_days),
        "start": datetime.utcnow().isoformat()
    }
    st.session_state.setdefault("experiments", []).append(exp)
    st.success("Experimento criado. Use o registro diário para anotar métricas.")

st.markdown("---")

# Section: Daily tracker
st.header("Registro diário / tracker rápido")
today = st.date_input("Data", value=datetime.utcnow().date())
col1, col2, col3 = st.columns(3)
with col1:
    sleep_today = st.number_input("Horas de sono (ontem)", min_value=0.0, max_value=24.0, value=7.0)
with col2:
    energy = st.slider("Energia hoje (0-10)", 0, 10, 6)
with col3:
    notes = st.text_input("Observações rápidas (medicação, treino, jejum)")

if st.button("Salvar registro diário"):
    rec = {"date": str(today), "sleep": float(sleep_today), "energy": int(energy), "notes": notes}
    st.session_state.setdefault("daily_logs", []).append(rec)
    st.success("Registro salvo.")

if st.session_state.get("daily_logs"):
    st.subheader("Últimos registros")
    df_logs = pd.DataFrame(st.session_state["daily_logs"])[["date", "sleep", "energy", "notes"]].tail(10)
    st.table(df_logs)

st.markdown("---")

# Section: Practical toolbox (enriched with content from the attached document)
st.header("Ferramentas práticas e protocolos rápidos")
st.markdown(
    """
Abaixo estão técnicas de autorregulação organizadas por objetivo. Todas são **não invasivas** e podem ser testadas de forma segura; pare se sentir mal.

**Foco imediato**
- Tape a narina esquerda e respire pela direita por 60–120 segundos; combine com olhar fixo em um ponto por 30–60s.
- Suplemento opcional: cafeína + L-teanina (uso pontual).

**Calma imediata**
- Suspiro fisiológico: duas inspirações curtas pelo nariz + expiração longa pela boca (repita 2–3x).
- Técnica de vago: expiração prolongada 1:2 (ex.: inspire 4s, expire 8s).

**Criatividade / insight**
- Caminhada ao ar livre com fluxo óptico (olhar para o horizonte, não para o celular) por 10–20 min.
- Respiração narina esquerda (2 min) para ativar parassimpático.

**Sono**
- Luz solar matinal 5–10 min; evitar luz azul 60–90 min antes de dormir; magnésio 1h antes (se indicado).
"""
)

st.markdown("---")

# Section: SOS 1 minuto (quick actions)
st.header("SOS 1 minuto — o que fazer agora")
st.markdown(
    """
- **Focar rápido**: tape a narina esquerda, respire vigorosamente pela direita por 60s + fixe o olhar.  
- **Acalmar rápido**: Suspiro fisiológico (2 inspirações curtas + expiração longa) + movimentos oculares laterais.  
- **Criatividade rápida**: tape a narina direita e respire pela esquerda por 2 minutos; relaxe o olhar.
"""
)

st.markdown("---")

# Section: Supplement guide (concise, safety-first)
st.header("Suplementação estratégica (resumo e segurança)")
st.markdown(
    """
**Para foco/energia**: L‑Tirosina, cafeína (uso pontual), creatina.  
**Para calma/sono**: Magnésio (bisglicinato/treonato), inositol, L‑teanina.  
**Para memória/fluxo**: Alfa‑GPC (colina biodisponível).  

**Regras de segurança**: ciclagem; não combinar sem supervisão; cheque interações com medicações; consulte um profissional antes de iniciar.
"""
)

st.markdown("---")

# Section: Risk assessment
st.header("Avaliação de risco antes de qualquer intervenção")
st.markdown("Responda para avaliar risco geral (orientativo, não substitui avaliação clínica).")
rq1 = st.radio("Tem condição médica crônica?", ["Não", "Sim"])
rq2 = st.radio("Usa medicação prescrita?", ["Não", "Sim"])
rq3 = st.radio("Tem acompanhamento médico disponível?", ["Sim", "Não"])

risk_score = 0
if rq1 == "Sim": risk_score += 2
if rq2 == "Sim": risk_score += 2
if rq3 == "No" or rq3 == "Não": risk_score += 2

if risk_score >= 3:
    st.warning("Risco aumentado: consulte um profissional antes de intervenções médicas ou experimentos invasivos.")
else:
    st.info("Risco baixo-moderado: priorize intervenções não invasivas e monitoramento.")

st.markdown("---")

# Section: Education — myths and cautions (use content from attached doc)
st.header("Educação e mitos comuns")
st.markdown(
    """
- **Mito**: "Sou cérebro esquerdo ou direito." A verdade: usamos ambos; há inclinações, não rótulos fixos.  
- **Cuidado**: implantes, edição genética e auto-injeções são experimentais e de alto risco; evite fora de ambientes regulados.  
- **Privacidade**: dados de wearables e testes são sensíveis — verifique políticas de armazenamento e compartilhamento.
"""
)

st.markdown("---")

# Section: Export data
st.header("Exportar seus dados (local)")
if st.session_state.get("daily_logs") or st.session_state.get("experiments"):
    export = {
        "profile": {"name": name, "age": age},
        "experiments": st.session_state.get("experiments", []),
        "daily_logs": st.session_state.get("daily_logs", [])
    }
    st.download_button("Baixar dados (JSON)", data=pd.io.json.dumps(export, ensure_ascii=False, indent=2), file_name="biohacking_data.json", mime="application/json")
else:
    st.info("Nenhum dado registrado ainda. Use o registro diário e o planejador de experimentos.")

st.markdown("---")

# Footer: references and next steps
st.header("Próximos passos sugeridos")
st.markdown(
    """
1. Escolha um experimento simples (sono ou energia) e registre por 2 semanas.  
2. Use apenas 1 intervenção por vez para saber o que funciona.  
3. Documente reações adversas e pare imediatamente se ocorrerem.  
4. Se quiser, eu posso:  
   - gerar um protocolo N-of-1 formatado (cronograma semanal),  
   - criar um checklist imprimível para levar ao clínico, ou  
   - integrar um CSV de sono/HRV para gráficos (se você enviar os dados).
"""
)