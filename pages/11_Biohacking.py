# pages/10_Biohacking.py
import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="Biohacking — Guia prático", layout="wide")
st.title("Biohacking — 🧬")

st.markdown("""
**Objetivo:** oferecer um espaço educativo e prático para experimentar intervenções de baixo a médio risco, medir respostas e priorizar segurança.
**Aviso:** este conteúdo é informativo. Não substitui avaliação médica. Consulte um profissional antes de intervenções médicas, peptídeos, hormônios ou procedimentos invasivos.
""")

# --- Sidebar: perfil e consentimento
with st.sidebar:
    st.header("Perfil rápido")
    name = st.text_input("Nome (opcional)")
    age = st.number_input("Idade", min_value=0, max_value=120, value=30)
    medical_conditions = st.text_area("Condições médicas relevantes (opcional)")
    consent = st.checkbox("Confirmo que li o aviso e que seguirei práticas seguras", value=False)

# --- Seção 1: Checklist inicial
st.header("1. Checklist inicial (priorize antes de experimentar)")
st.markdown("""
- **Sono**: rotina consistente (hora de dormir/acordar).  
- **Hidratação**: água ao longo do dia.  
- **Exercício**: 3x/semana mínimo (resistência + cardio).  
- **Exames básicos**: hemograma, função renal, perfil lipídico, glicemia (se planeja intervenções).  
- **Backup médico**: contato de um profissional para consultas.
""")

col1, col2, col3 = st.columns(3)
with col1:
    sleep_hours = st.slider("Horas de sono (média última semana)", 0, 12, 7)
with col2:
    steps = st.number_input("Passos médios/dia (estimativa)", min_value=0, max_value=50000, value=6000)
with col3:
    stress = st.slider("Nível de estresse (0-10)", 0, 10, 4)

if not consent:
    st.warning("Marque a caixa de consentimento na barra lateral para desbloquear ferramentas práticas.")
    st.stop()

# --- Seção 2: Planejador de experimentos (N-of-1)
st.header("2. Planejador de experimentos pessoais (N-of-1)")
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
    if "experiments" not in st.session_state:
        st.session_state["experiments"] = []
    st.session_state["experiments"].append(exp)
    st.success("Experimento criado. Use a seção de registro diário para anotar métricas.")

# --- Seção 3: Registro diário / tracker simples
st.header("3. Registro diário (rápido)")
today = st.date_input("Data", value=datetime.utcnow().date())
col_a, col_b, col_c = st.columns(3)
with col_a:
    sleep_today = st.number_input("Horas de sono (ontem)", min_value=0.0, max_value=24.0, value=round(sleep_hours,1))
with col_b:
    energy = st.slider("Energia hoje (0-10)", 0, 10, 6)
with col_c:
    notes = st.text_input("Observações rápidas (medicação, treino, jejum)")

if st.button("Salvar registro diário"):
    rec = {"date": str(today), "sleep": float(sleep_today), "energy": int(energy), "notes": notes}
    if "daily_logs" not in st.session_state:
        st.session_state["daily_logs"] = []
    st.session_state["daily_logs"].append(rec)
    st.success("Registro salvo.")

# Mostrar logs
if st.session_state.get("daily_logs"):
    st.subheader("Últimos registros")
    df_logs = pd.DataFrame(st.session_state["daily_logs"])[["date","sleep","energy","notes"]].tail(10)
    st.table(df_logs)

# --- Seção 4: Ferramentas e recomendações práticas (não médicas)
st.header("4. Ferramentas práticas e recomendações")
st.markdown("""
**Sono**: rotina, exposição à luz natural pela manhã, reduzir luz azul à noite.  
**Treino**: combine força (2x/semana) e cardio; periodize intensidade.  
**Nutrição**: priorize alimentos integrais; experimente jejum intermitente com cautela.  
**Recuperação**: técnicas de respiração, alongamento, banhos frios/quentes com moderação.  
**Medição**: use wearables para HRV, sono e passos; registre sintomas e energia.
""")

# Quick resources links (placeholders)
st.markdown("**Recursos rápidos:**")
st.markdown("- Artigos de revisão sobre sono e performance; - Guias de segurança para implantes e biologia DIY; - Clínicos especializados em medicina funcional e longevidade.")

# --- Seção 5: Avaliação de risco para intervenções (simples)
st.header("5. Avaliação de risco (use antes de qualquer intervenção)")
st.markdown("Responda: você tem histórico de doença crônica? Está grávida? Usa medicação regular? Tem suporte médico?")
risk_q1 = st.radio("Tem condição médica crônica?", ["Não", "Sim"])
risk_q2 = st.radio("Está em uso de medicação prescrita?", ["Não", "Sim"])
risk_q3 = st.radio("Tem acesso a acompanhamento médico se necessário?", ["Sim", "Não"])

risk_score = 0
if risk_q1 == "Sim": risk_score += 2
if risk_q2 == "Sim": risk_score += 2
if risk_q3 == "Não": risk_score += 2

if risk_score >= 3:
    st.warning("Risco aumentado: consulte um profissional antes de intervenções médicas ou experimentos invasivos.")
else:
    st.info("Risco baixo-moderado: priorize intervenções não invasivas e monitoramento.")

# --- Seção 6: Educação — o que evitar e quando procurar ajuda
st.header("6. O que evitar e sinais de alerta")
st.markdown("""
**Evitar**: protocolos de influencers sem evidência, compra de peptídeos sem prescrição, auto-injeção sem supervisão, edição genética DIY.  
**Sinais de alerta** (procure atendimento): febre persistente, dor intensa, perda de função, sangramento, reações alérgicas, perda de peso rápida ou fadiga extrema.
""")

# --- Export simples dos dados do usuário (JSON)
st.markdown("---")
st.subheader("Exportar seus dados (local)")
if st.session_state.get("daily_logs") or st.session_state.get("experiments"):
    export = {
        "profile": {"name": name, "age": age, "medical_conditions": medical_conditions},
        "experiments": st.session_state.get("experiments", []),
        "daily_logs": st.session_state.get("daily_logs", [])
    }
    st.download_button("Baixar dados (JSON)", data=pd.io.json.dumps(export, ensure_ascii=False, indent=2), file_name="biohacking_data.json", mime="application/json")
else:
    st.info("Nenhum dado registrado ainda.")

# Footer / referências
st.markdown("---")
st.markdown("**Referências e leituras recomendadas:** fontes médicas e revisões sobre biohacking, segurança de implantes e uso responsável de tecnologias. Consulte literatura médica e profissionais antes de intervenções avançadas.")