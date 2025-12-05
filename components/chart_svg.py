# components/chart_svg.py
from typing import Dict, Any, List
import math

def _planet_symbol(name: str) -> str:
    # simples: retornar abreviação; para glyphs, mapear para entidades SVG/text
    return name[:2].upper()

def render_wheel_svg(planets: Dict[str, Dict[str, float]], cusps: List[float]) -> str:
    """
    Gera SVG simples com roda zodiacal e marcadores de planetas.
    planets: {"Sun": {"longitude": 123.4}, ...}
    cusps: lista de 12 cúspides (graus)
    """
    size = 700
    cx = cy = size // 2
    radius = size * 0.4
    svg_parts = []
    svg_parts.append(f'<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">')
    # círculo externo
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="white" stroke="#333" stroke-width="2"/>')

    # divisões dos signos (12)
    for i in range(12):
        angle = (i * 30) - 90
        x1 = cx + radius * math.cos(math.radians(angle))
        y1 = cy + radius * math.sin(math.radians(angle))
        x2 = cx + (radius - 20) * math.cos(math.radians(angle))
        y2 = cy + (radius - 20) * math.sin(math.radians(angle))
        svg_parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#666" stroke-width="1"/>')

    # planetas
    for name, v in planets.items():
        lon = v["longitude"]
        angle = lon - 90
        px = cx + (radius - 60) * math.cos(math.radians(angle))
        py = cy + (radius - 60) * math.sin(math.radians(angle))
        label = _planet_symbol(name)
        svg_parts.append(f'<text x="{px}" y="{py}" font-size="14" text-anchor="middle" fill="#111">{label}</text>')

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)