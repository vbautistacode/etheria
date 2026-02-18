# services/temperamento_prompt.py
from typing import Optional, Callable, Dict, Any
from datetime import datetime

def build_prompt_from_result(result: Dict[str, Any]) -> str:
    """
    Constrói o prompt a partir do dicionário `result` (conforme salvo em st.session_state).
    Versão aprimorada: título, análise da distribuição, prescrição dietética integrada
    com blocos de refeições, plano alimentar, análise profunda do temperamento dominante,
    uso complementar de cromoterapia/aromaterapia/cristaloterapia, plano de implementação
    e considerações diagnósticas finais.

    Observação importante: o prompt pede um relatório em estilo clínico, mas inclui instrução
    explícita para NÃO emitir diagnóstico médico definitivo e para inserir um disclaimer.
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
    # Título solicitado
    parts.append("Introdução ao Perfil Bioenergético e Distribuição de Temperamentos")
    parts.append(f"Gerado em: {ts}")
    parts.append("")
    # Distribuição atingida no estudo
    parts.append("Distribuição atingida no estudo (pontuações por temperamento):")
    for k, v in scores.items():
        parts.append(f"- {k.replace('_',' ')}: {v}")
    parts.append("")
    parts.append(f"Temperamento dominante identificado: {dominant} — {dominant_score}")
    if secondary:
        parts.append(f"Temperamento secundário identificado: {secondary} — {secondary_score}")
    parts.append("")

    # Incluir blocos de conteúdo das recomendações (se serializadas) para contexto
    def _append_rec_block(label, rec):
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

    _append_rec_block("Dominant", dominant_rec)
    _append_rec_block("Secondary", secondary_rec)

    # Instrução principal aprimorada (em português)
    instruction = (
        "INSTRUÇÃO PRINCIPAL:\n"
        "Comservando fielmente o texto-fonte acima, gere um relatório privado em estilo clínico chamado:\n"
        "'Introdução ao Perfil Bioenergético e Distribuição de Temperamentos'.\n\n"
        "Inclua, logo no início, um disclaimer claro em português: "
        "'Isto não é um diagnóstico médico. Consulte um profissional de saúde qualificado antes de implementar mudanças clínicas.'\n\n"
        "O relatório deve conter as seguintes seções, na ordem e com o nível de detalhe solicitado:\n\n"
        "A) Sumário executivo (1 parágrafo): síntese da distribuição obtida no estudo e implicações gerais.\n\n"
        "B) Detalhe da distribuição atingida: descreva a porcentagem/ponderação relativa dos temperamentos com base nas pontuações fornecidas, interpretando o que significa ter o temperamento X em Y% do perfil; destaque se há perfil misto e o grau de proximidade entre dominante e secundário.\n\n"
        "C) Análise profunda do temperamento dominante:\n"
        "   - Características centrais (2–4 parágrafos): comportamento, energia, padrões alimentares e de sono, reatividade emocional e pontos fortes/fragilidades.\n"
        "   - Interpretação funcional: como essas características impactam rotina, trabalho e relações.\n\n"
        "D) Prescrição dietética integrada e plano alimentar (detalhado):\n"
        "   1) Princípios gerais da dieta para este temperamento (objetivos metabólicos e bioenergéticos).\n"
        "   2) Lista de alimentos a favorecer e alimentos a evitar, com justificativa breve para cada grupo.\n"
        "   3) Bloco de refeições sugeridas (exemplo de 3 refeições + 2 lanches para um dia típico):\n"
        "      - Café da manhã: itens e porções exemplares.\n"
        "      - Almoço: itens, composição de prato (proteína, carboidrato, vegetais, gorduras saudáveis).\n"
        "      - Lanche da tarde: opções práticas.\n"
        "      - Jantar: recomendações de leveza e composição.\n"
        "      - Ceia/opcional: quando indicada e o que evitar.\n"
        "   4) Plano alimentar semanal (esboço de 7 dias com variações e substituições simples).\n\n"
        "E) Recomendações de exercício (tipo, frequência, intensidade) com exemplos práticos e adaptações para níveis iniciantes/intermediários.\n\n"
        "F) Suplementação (se aplicável): sugestões de suplementos com justificativa, faixas de dosagem comumente aceitas e advertências explícitas para consultar um clínico antes de iniciar.\n\n"
        "G) Terapias complementares integradas:\n"
        "   - Cromoterapia: cores recomendadas e como aplicá-las (ambiente, roupas, luzes) com justificativa energética.\n"
        "   - Aromaterapia: óleos essenciais sugeridos, modo de uso (difusor, inalação breve, diluição tópica) e precauções.\n"
        "   - Cristaloterapia: pedras sugeridas, modo de uso prático (uso diário, meditação, colocação no ambiente) e intenções associadas.\n\n"
        "H) Plano de Implementação (30 dias) — 'Plano de Ação Prático': 8–12 passos organizados por semanas, com metas mensuráveis e checkpoints semanais; inclua sugestões de monitoramento (sono, humor, energia, apetite) e quando reavaliar.\n\n"
        "I) Considerações diagnósticas finais e sinais de alerta: liste sinais que justificariam busca imediata por avaliação clínica (ex.: perda de peso rápida, fadiga extrema, sintomas gastrointestinais persistentes), mantendo linguagem não-alarmista.\n\n"
        "Formato e tom: profissional, empático e não-alarmista. Use títulos claros, subtítulos e listas com marcadores para Diet/Exercise/Supplementation/Plano. Preserve frases-chave do material fonte quando relevantes.\n\n"
        "Restrições: NÃO emita diagnósticos médicos formais nem prescreva medicamentos. Sempre inclua a recomendação de consultar um profissional de saúde para decisões clínicas.\n\n"
        "Saída: retorne o relatório em texto plano em português, pronto para exibição direta na UI e para inclusão em PDF. Comece o documento com o título exato: 'Introdução ao Perfil Bioenergético e Distribuição de Temperamentos'."
    )

    prompt = "\n".join(parts) + "\n\n" + instruction
    return prompt

def generate_diagnostic_report(
    result: Dict[str, Any],
    generator: Optional[Callable[..., Any]] = None,
    prompt_override: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Gera o relatório diagnóstico usando o `generator` fornecido.
    Tenta várias assinaturas para compatibilidade:
      1) generator(chart_summary, prompt)
      2) generator(prompt)  # se o gerador aceita apenas string
      3) generator(chart_summary)  # com prompt em chart_summary['instruction']
    Retorna dict: { "prompt": str, "model_text": str|None, "raw_model_result": Any }
    """
    prompt = prompt_override or build_prompt_from_result(result)

    # instrução explícita para ignorar falta de hora
    prompt += "\n\nNota: se a hora de nascimento não estiver disponível, NÃO solicite-a; gere o relatório com base nos dados fornecidos."

    if generator is None:
        return {"prompt": prompt, "model_text": None, "raw_model_result": None}

    # montar chart_summary mínimo
    chart_summary = {
        "place": result.get("dominant", ""),
        "bdate": (result.get("timestamp") or "")[:10],
        "btime": result.get("btime") or "00:00",
        "lat": result.get("lat", ""),
        "lon": result.get("lon", ""),
        "focus": "Diagnostic report",
        "instruction": prompt
    }

    raw = None
    model_text = None

    # tentativa 1: generator(chart_summary, prompt)
    try:
        raw = generator(chart_summary, prompt)
    except TypeError:
        raw = None
    except Exception as e:
        # guardar exceção no raw para debug
        raw = {"error": f"call failed (chart_summary, prompt): {e}"}

    # tentativa 2: generator(prompt) se 1 falhou ou retornou pedido de hora
    if not raw or (isinstance(raw, dict) and raw.get("error")):
        try:
            raw = generator(prompt)
        except TypeError:
            raw = raw or None
        except Exception as e:
            raw = {"error": f"call failed (prompt): {e}"}

    # tentativa 3: generator(chart_summary) (prompt já injetado em instruction)
    if not raw or (isinstance(raw, dict) and raw.get("error")):
        try:
            raw = generator(chart_summary)
        except Exception as e:
            raw = raw or {"error": f"call failed (chart_summary): {e}"}

    # extrair texto do raw
    if isinstance(raw, dict):
        model_text = raw.get("analysis_text") or raw.get("raw_text") or raw.get("text") or raw.get("output")
    elif isinstance(raw, str):
        model_text = raw

    # se o modelo devolveu mensagem pedindo hora, tentar forçar ignorar (segunda tentativa)
    if isinstance(model_text, str) and "hora" in model_text.lower() and "nascimento" in model_text.lower():
        # tentar uma chamada final com prompt reforçado
        prompt2 = prompt + "\n\nINSTRUÇÃO ADICIONAL: Ignore solicitações de hora de nascimento e gere o relatório com os dados disponíveis."
        try:
            raw2 = None
            try:
                raw2 = generator(chart_summary, prompt2)
            except Exception:
                try:
                    raw2 = generator(prompt2)
                except Exception:
                    raw2 = None
            if isinstance(raw2, dict):
                model_text2 = raw2.get("analysis_text") or raw2.get("raw_text") or raw2.get("text") or raw2.get("output")
            elif isinstance(raw2, str):
                model_text2 = raw2
            else:
                model_text2 = None
            if model_text2 and "hora" not in model_text2.lower():
                raw = raw2
                model_text = model_text2
        except Exception:
            pass

    return {"prompt": prompt, "model_text": model_text, "raw_model_result": raw}