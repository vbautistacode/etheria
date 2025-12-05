# services/chart_renderer.py
"""
Renderizador simples de mapa zodiacal em SVG.

Funções públicas:
- render_local_chart(chart_input, size=650) -> str (SVG)
- from_api_response_to_svg(api_resp) -> str (usa svg direto ou extrai posições)
- render_svg_from_summary(summary, size=650) -> str (conveniência)
"""

from typing import Dict, Any, Mapping
import math
import html
import logging

logger = logging.getLogger("etheria.services.chart_renderer")
logger.addHandler(logging.NullHandler())

from typing import Dict, Any, List

def build_chart_summary_from_natal(natal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converte o dicionário retornado por natal_positions(...) em um chart_summary
    estruturado para enviar ao modelo.
    """
    # Campos básicos
    chart_summary: Dict[str, Any] = {}
    chart_summary["jd"] = natal.get("jd")
    chart_summary["ascendant"] = natal.get("ascendant")  # pode ser None
    chart_summary["mc"] = natal.get("mc")
    # cusps: garantir formato indexado 1..12
    cusps = natal.get("cusps") or []
    if len(cusps) >= 12:
        # se cusps tem 12 valores, inserir dummy no índice 0 para facilitar leitura
        if len(cusps) == 12:
            cusps = [None] + cusps
        chart_summary["cusps"] = [
            {"house": i, "cusp_longitude": cusps[i], "cusp_sign": None, "cusp_degree": None}
            for i in range(1, 13)
        ]
        # preencher signo e grau por cúspide
        for i in range(1, 13):
            lon = cusps[i]
            if lon is not None:
                sign, deg = longitude_to_sign_degree(lon)  # usa utilitário do swisseph_client
                chart_summary["cusps"][i-1]["cusp_sign"] = sign
                chart_summary["cusps"][i-1]["cusp_degree"] = round(deg, 4)
    else:
        chart_summary["cusps"] = None

    # Planetas: transformar em lista com campos úteis
    planets = natal.get("planets", {})
    planets_list: List[Dict[str, Any]] = []
    for pname, pdata in planets.items():
        planets_list.append({
            "name": pname,
            "longitude": pdata.get("longitude"),
            "sign": pdata.get("sign"),
            "degree_in_sign": pdata.get("degree_in_sign"),
            "house": pdata.get("house"),
            "latitude": pdata.get("latitude"),
            "distance": pdata.get("distance"),
            "flag": pdata.get("flag"),
        })
    chart_summary["planets"] = planets_list

    # nodes, retrogrades, outros (se disponíveis no natal)
    if "nodes" in natal:
        chart_summary["nodes"] = natal["nodes"]
    if "retrogrades" in natal:
        chart_summary["retrogrades"] = natal["retrogrades"]

    return chart_summary

def build_prompt_from_chart_summary(chart_summary: Dict[str, Any], prompt_template: str | None = None) -> str:
    """
    Gera um prompt textual claro que inclui ASC, cúspides e planetas.
    Se ASC ou casas estiverem ausentes, inclui aviso explícito.
    """
    parts: List[str] = []
    # Ascendente
    asc = chart_summary.get("ascendant")
    if asc:
        parts.append(f"ASCENDENTE: {asc.get('sign')} {asc.get('degree_in_sign')}°")
    else:
        parts.append("ASCENDENTE: não calculado (hora de nascimento ausente ou inválida)")

    # Cúspides
    cusps = chart_summary.get("cusps")
    if cusps:
        cusps_lines = []
        for c in cusps:
            cusps_lines.append(f"{c['house']}: {c['cusp_sign']} {c['cusp_degree']}°")
        parts.append("CÚSPIDES (1–12): " + "; ".join(cusps_lines))
    else:
        parts.append("CÚSPIDES: não calculadas (hora de nascimento ausente ou inválida)")

    # Planetas
    planet_lines = []
    for p in chart_summary.get("planets", []):
        house = p.get("house") if p.get("house") is not None else "—"
        degree = p.get("degree_in_sign") if p.get("degree_in_sign") is not None else "—"
        sign = p.get("sign") or "—"
        planet_lines.append(f"- {p['name']}: {sign} {degree}° casa {house}")
    parts.append("PLANETAS:\n" + "\n".join(planet_lines))

    # Mensagem de instrução clara ao modelo
    instructions = (
        "Use os dados acima para interpretar o mapa. Inclua o Ascendente e a casa de cada planeta quando disponíveis.\n"
        "Se algum dado estiver ausente, explique claramente que não foi possível calcular e por quê.\n"
        "Siga a numeração das seções: 1) Analogia ao teatro; 2) Primeira tríade (ASC, Sol, Lua); "
        "3) Segunda tríade (Marte, Mercúrio, Vênus); 4) Tríade social (Júpiter, Saturno); "
        "5) Tríade geracional (Urano, Netuno, Plutão); 6) Elementos; 7) Astrologia cármica."
    )

    body = "\n\n".join(parts)
    if prompt_template:
        return prompt_template.format(chart_summary=body)
    return body + "\n\n" + instructions

def _circle_point(cx: float, cy: float, radius: float, angle_deg: float):
    """Retorna coordenadas x,y para ângulo em graus (0° no topo, sentido horário)."""
    theta = math.radians(angle_deg - 90.0)
    x = cx + radius * math.cos(theta)
    y = cy + radius * math.sin(theta)
    return x, y

def render_local_chart(chart_input: Mapping[str, Any], size: int = 650) -> str:
    """
    Gera um SVG simples do mapa zodiacal a partir de posições (longitudes) em chart_input.
    Espera chart_input['positions'] = {"Sun": 123.4, "Moon": 45.6, ...}
    Retorna string SVG.
    """
    positions = {}
    try:
        if isinstance(chart_input, dict):
            if "positions" in chart_input and isinstance(chart_input["positions"], dict):
                positions = chart_input["positions"]
            elif "summary" in chart_input and isinstance(chart_input["summary"], dict):
                planets_map = chart_input["summary"].get("planets") or chart_input["summary"].get("readings") or {}
                for pname, pdata in planets_map.items():
                    try:
                        if isinstance(pdata, dict) and pdata.get("longitude") is not None:
                            positions[pname] = float(pdata.get("longitude"))
                        elif isinstance(pdata, (int, float)):
                            positions[pname] = float(pdata)
                    except Exception:
                        continue
    except Exception:
        logger.exception("Erro ao extrair posições para render_local_chart")

    cx = cy = size / 2
    outer_r = size * 0.45
    inner_r = outer_r * 0.85
    svg_parts = []
    svg_parts.append(f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">')
    svg_parts.append(f'<rect width="100%" height="100%" fill="white"/>')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="#fffaf0" stroke="#333" stroke-width="2"/>')

    for i in range(12):
        angle = i * 30.0
        x1, y1 = _circle_point(cx, cy, inner_r, angle)
        x2, y2 = _circle_point(cx, cy, outer_r, angle)
        svg_parts.append(f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" stroke="#bbb" stroke-width="1"/>')

    for pname, lon in positions.items():
        try:
            lon = float(lon)
            theta = (360.0 - lon) % 360.0
            px, py = _circle_point(cx, cy, (inner_r + outer_r) / 2.0, theta)
            label = html.escape(str(pname))
            svg_parts.append(f'<g class="planet" data-planet="{label}">')
            svg_parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="8" fill="#1f77b4" stroke="#000" stroke-width="1.2"/>')
            svg_parts.append(f'<text x="{px + 12:.2f}" y="{py + 4:.2f}" font-family="Arial" font-size="12" fill="#000">{label}</text>')
            svg_parts.append('</g>')
        except Exception:
            logger.exception("Erro ao desenhar planeta %s", pname)
            continue
    svg_parts.append('</svg>')
    return "\n".join(svg_parts)

def from_api_response_to_svg(api_resp: Mapping[str, Any]) -> str:
    """
    Converte resposta da API em SVG. Se a API já retornar 'svg' ou 'chart_svg', usa direto.
    Caso contrário, tenta extrair posições e delega para render_local_chart.
    """
    try:
        if not api_resp:
            return render_local_chart({})
        if isinstance(api_resp, dict):
            if api_resp.get("svg"):
                return api_resp.get("svg")
            if api_resp.get("chart_svg"):
                return api_resp.get("chart_svg")
            positions = {}
            if api_resp.get("positions") and isinstance(api_resp.get("positions"), dict):
                positions = api_resp.get("positions")
            elif api_resp.get("planets") and isinstance(api_resp.get("planets"), dict):
                for k, v in api_resp.get("planets").items():
                    try:
                        if isinstance(v, dict) and v.get("longitude") is not None:
                            positions[k] = float(v.get("longitude"))
                    except Exception:
                        continue
            if positions:
                return render_local_chart({"positions": positions})
    except Exception:
        logger.exception("Erro em from_api_response_to_svg")
    return render_local_chart({})

def render_svg_from_summary(summary: Mapping[str, Any], size: int = 650) -> str:
    """Convenience wrapper que aceita summary e delega para render_local_chart."""
    return render_local_chart({"summary": summary}, size=size)

if __name__ == "__main__":
    # teste rápido
    sample = {"positions": {"Sun": 10.0, "Moon": 120.0, "Mercury": 200.0}}
    print(render_local_chart(sample)[:200])