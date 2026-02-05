# services/daily_prompt.py
"""
Template e builder para o prompt do 'Mapa do Dia' (leitura diária, simbólica).
Este módulo fornece um DEFAULT_DAILY_PROMPT e uma função para montar o prompt
a partir de um chart_summary (mesmo formato usado pelo generator_service).
"""

from typing import Dict, Any, List
from .generator_service import normalize_chart_positions, _positions_block_from_records  # reuso utilitários

DEFAULT_DAILY_PROMPT = (
    "Interprete o 'Mapa do Dia' com foco prático e simbólico, usando a data e hora fornecidas.\n\n"
    "Contexto: este não é um mapa natal; é uma leitura do céu para o dia e hora informados.\n\n"
    "Siga as seções numeradas e responda em português:\n\n"
    "1) Resumo (2-3 frases): o que o dia oferece em termos práticos e energéticos.\n\n"
    "2) Três pontos de atenção (cada um em 1 linha): riscos ou áreas que merecem cuidado.\n\n"
    "3) Prática simples em 3 passos (cada passo curto): uma micro-rotina para aproveitar o dia.\n\n"
    "4) Sugestões simbólicas: indique 2 pedras, 1 cor para cromoterapia e 1 óleo essencial.\n\n"
    "5) Se possível, inclua uma nota curta (1 linha) sobre o tom emocional do dia (ex.: introspectivo, comunicativo, ativo).\n\n"
    "Use linguagem clara, prática e breve. Se não houver efemérides técnicas, baseie-se em sinais simbólicos e orientações úteis para o cotidiano."
)

def build_daily_prompt_from_chart_summary(chart_summary: Dict[str, Any], prompt_template: str = None) -> str:
    """
    Monta o prompt para o Mapa do Dia a partir de chart_summary.
    Reaproveita normalize_chart_positions e _positions_block_from_records quando houver posições.
    """
    if prompt_template is None:
        prompt_template = DEFAULT_DAILY_PROMPT

    header_lines: List[str] = []
    place = chart_summary.get("place") or ""
    bdate = chart_summary.get("bdate") or ""
    btime = chart_summary.get("btime") or ""
    lat = chart_summary.get("lat") or ""
    lon = chart_summary.get("lon") or ""
    focus = chart_summary.get("focus") or "Geral"

    if place:
        header_lines.append(f"Cidade: {place}")
    if bdate:
        header_lines.append(f"Data: {bdate}")
    if btime:
        header_lines.append(f"Hora (cliente): {btime}")
    if lat and lon:
        header_lines.append(f"Coordenadas: {lat}, {lon}")
    header_lines.append(f"Foco: {focus}")

    header = "\n".join(header_lines) + "\n\n"

    # se houver chart_positions, incluir bloco (normaliza se necessário)
    chart_positions = chart_summary.get("chart_positions") or chart_summary.get("positions") or None
    positions_text = ""
    if chart_positions:
        try:
            records = chart_positions if isinstance(chart_positions, list) else list(chart_positions)
            records = normalize_chart_positions(records)
            positions_text = _positions_block_from_records(records) + "\n\n"
        except Exception:
            positions_text = "\nPosições calculadas: indisponíveis.\n\n"

    return header + positions_text + prompt_template