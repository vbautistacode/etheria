# services/temperamento_prompt.py
from typing import Optional, Callable, Dict, Any
from datetime import datetime

def build_prompt_from_result(result: Dict[str, Any]) -> str:
    """
    Constrói o prompt a partir do dicionário `result` (conforme salvo em st.session_state).
    Prompt solicitado pelo usuário:
    "Conservando o texto da fonte, crie um relatório particular, como se fosse um diagnóstico médico,
     sobre o(s) temperamento(s) em questão, destacando a dieta, exercicios e suplementação para cada temperamento encontrado"
    Observação: o prompt inclui instrução explícita para NÃO emitir diagnóstico médico real e para
    inserir um disclaimer recomendando consulta a profissional de saúde.
    """
    ts = result.get("timestamp", datetime.utcnow().isoformat())
    scores = result.get("scores", {})
    dominant = result.get("dominant", "")
    dominant_score = result.get("dominant_score", "")
    secondary = result.get("secondary", None)
    secondary_score = result.get("secondary_score", None)

    dominant_rec = result.get("dominant_rec") or {}
    secondary_rec = result.get("secondary_rec") or {}

    parts = []
    parts.append(f"Source: Autoestudo — Temperamentos (generated at {ts}).")
    parts.append("Conserve o texto da fonte ao máximo; use-o como base para o relatório.")
    parts.append("")
    parts.append("Scores por temperamento:")
    for k, v in scores.items():
        parts.append(f"- {k.replace('_',' ')}: {v}")
    parts.append("")
    parts.append(f"Temperamento dominante: {dominant} — {dominant_score}")
    if secondary:
        parts.append(f"Temperamento secundário: {secondary} — {secondary_score}")
    parts.append("")

    def append_rec(label: str, rec: Dict[str, Any]):
        if not rec:
            return
        parts.append(f"--- {label} ---")
        if rec.get("resumo"):
            parts.append(f"Resumo: {rec.get('resumo')}")
        if rec.get("pedras"):
            parts.append(f"Pedras sugeridas: {', '.join(rec.get('pedras'))}")
        if rec.get("cor"):
            parts.append(f"Cromoterapia (cor): {rec.get('cor')}")
        if rec.get("oleo"):
            parts.append(f"Aromaterapia (óleo): {rec.get('oleo')}")
        if rec.get("dicas"):
            parts.append("Dicas práticas:")
            for d in rec.get("dicas", []):
                parts.append(f"- {d}")
        if rec.get("alimentacao"):
            parts.append("Alimentação (detalhe):")
            parts.append(rec.get("alimentacao"))
        parts.append("")

    append_rec("Dominant", dominant_rec)
    append_rec("Secondary", secondary_rec)

    # Instrução principal: estilo clínico, mas sem diagnóstico médico
    instruction = (
        "INSTRUCTION:\n"
        "Conserving the source text above, create a private-style diagnostic report as if written by a medical consultant. "
        "Important: DO NOT provide a medical diagnosis. Include a clear disclaimer near the top: "
        "'This is not a medical diagnosis. Consult a qualified health professional before making clinical changes.'\n\n"
        "For each temperamento present (dominant and, if applicable, secondary) produce the following sections:\n"
        "  1) Diagnostic-style summary (2–4 short paragraphs) that preserves the source wording where relevant.\n"
        "  2) Diet (Diet): specific, practical guidance (foods to prefer and avoid; meal-level suggestions).\n"
        "  3) Exercise (Exercise): recommended types, frequency and intensity, with practical examples.\n"
        "  4) Supplementation (Supplementation): suggested supplements with rationale and safety cautions; include 'consult a clinician' note.\n"
        "  5) A short personalized 30-day action plan (3–5 numbered steps).\n\n"
        "Tone: professional, compassionate, non-alarmist. Use bullet lists for Diet/Exercise/Supplementation and a short numbered plan. "
        "Avoid inventing clinical diagnoses or prescribing medications. If suggesting supplements, include common safe dosage ranges when appropriate and always add a caution to consult a clinician.\n\n"
        "Return the report as plain text suitable for direct display in the UI and for inclusion in a PDF."
    )
    
    prompt = "\n".join(parts) + "\n\n" + instruction
    return prompt


def generate_diagnostic_report(
    result: Dict[str, Any],
    generator: Optional[Callable[[Dict[str, Any], Optional[str]], Any]] = None,
    prompt_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gera o relatório diagnóstico (estilo clínico, não diagnóstico) usando o `generator` fornecido.
    - result: dicionário salvo em session_state (deve conter dominant_rec/secondary_rec idealmente).
    - generator: função que recebe (chart_summary, prompt_template) e retorna dict ou str com texto.
                 Se None, a função retorna apenas o prompt (útil para testes).
    - prompt_override: se fornecido, usa esse prompt em vez do gerado automaticamente.

    Retorna um dict com:
      { "prompt": <str>, "model_text": <str or None>, "raw_model_result": <raw return from generator> }
    """
    prompt = prompt_override or build_prompt_from_result(result)

    # se não houver generator, devolve apenas o prompt (útil para debug/unit tests)
    if generator is None:
        return {"prompt": prompt, "model_text": None, "raw_model_result": None}

    # montar chart_summary mínimo compatível com generate_ai_text_from_chart
    chart_summary = {
        "place": result.get("dominant", ""),
        "bdate": result.get("timestamp", ""),
        "btime": "",
        "lat": "",
        "lon": "",
        "focus": "Diagnostic report",
        "instruction": prompt
    }

    # chamar o gerador e extrair texto
    model_result = generator(chart_summary, prompt)
    model_text = None
    if isinstance(model_result, dict):
        model_text = model_result.get("analysis_text") or model_result.get("raw_text") or model_result.get("text") or model_result.get("output")
    elif isinstance(model_result, str):
        model_text = model_result

    return {"prompt": prompt, "model_text": model_text, "raw_model_result": model_result}