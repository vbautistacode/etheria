# services/chart_builder.py
from typing import Dict, Any, List
from services.swisseph_client import longitude_to_sign_degree

def build_chart_summary_from_natal(natal: Dict[str, Any]) -> Dict[str, Any]:
    chart_summary: Dict[str, Any] = {}
    chart_summary["jd"] = natal.get("jd")
    chart_summary["ascendant"] = natal.get("ascendant")
    chart_summary["mc"] = natal.get("mc")

    cusps = natal.get("cusps") or []
    if len(cusps) >= 12:
        if len(cusps) == 12:
            cusps = [None] + cusps
        chart_summary["cusps"] = [
            {"house": i, "cusp_longitude": cusps[i], "cusp_sign": None, "cusp_degree": None}
            for i in range(1, 13)
        ]
        for i in range(1, 13):
            lon = cusps[i]
            if lon is not None:
                sign, deg = longitude_to_sign_degree(lon)
                chart_summary["cusps"][i-1]["cusp_sign"] = sign
                chart_summary["cusps"][i-1]["cusp_degree"] = round(deg, 4)
    else:
        chart_summary["cusps"] = None

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

    if "nodes" in natal:
        chart_summary["nodes"] = natal["nodes"]
    if "retrogrades" in natal:
        chart_summary["retrogrades"] = natal["retrogrades"]

    return chart_summary

def build_prompt_from_chart_summary(chart_summary: Dict[str, Any], prompt_template: str | None = None) -> str:
    parts: List[str] = []
    asc = chart_summary.get("ascendant")
    if asc:
        parts.append(f"ASCENDENTE: {asc.get('sign')} {asc.get('degree_in_sign')}°")
    else:
        parts.append("ASCENDENTE: não calculado (hora de nascimento ausente ou inválida)")

    cusps = chart_summary.get("cusps")
    if cusps:
        cusps_lines = []
        for c in cusps:
            cusps_lines.append(f"{c['house']}: {c['cusp_sign']} {c['cusp_degree']}°")
        parts.append("CÚSPIDES (1–12): " + "; ".join(cusps_lines))
    else:
        parts.append("CÚSPIDES: não calculadas (hora de nascimento ausente ou inválida)")

    planet_lines = []
    for p in chart_summary.get("planets", []):
        house = p.get("house") if p.get("house") is not None else "—"
        degree = p.get("degree_in_sign") if p.get("degree_in_sign") is not None else "—"
        sign = p.get("sign") or "—"
        planet_lines.append(f"- {p['name']}: {sign} {degree}° casa {house}")
    parts.append("PLANETAS:\n" + "\n".join(planet_lines))

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