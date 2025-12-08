# pages/mapa_astral.py

import os
import sys
import logging
import importlib
import traceback
import json
import pytz
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, date, time as dtime
from typing import Tuple, Optional, Dict, Any, List
from etheria.services.generator_service import generate_ai_text_from_chart as generate_interpretation
from pathlib import Path

# Ajuste: pages/mapa_astral.py -> parents[1] aponta para a pasta 'etheria' que contém 'services'
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
from datetime import datetime, date, time as dt_time
from typing import Optional, Tuple, Dict, Any
# Imports do projeto (ajuste caminhos se necessário)
from etheria.services.generator_service import generate_analysis, generate_ai_text_from_chart
from services.swisseph_client import natal_positions  # se disponível
# Funções utilitárias do projeto (assumidas existentes)
# geocode_place_safe, geocode_place_nominatim, to_local_datetime, fetch_natal_chart,
# generate_chart_summary, positions_table, compute_aspects, render_wheel_plotly,
# interpretations, rules, influences, astrology
from etheria.services.astro_service import geocode_place, get_timezone_from_coords, parse_birth_time, compute_chart_positions
# Substituição para usar services.astro_service (não precisa de services.timezone_utils)
from etheria.services.astro_service import parse_birth_time, get_timezone_from_coords

# logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# variáveis de fallback para o generator service
generator_service = None
generator_import_error = None

# tentar importar generator_service de forma robusta:
# 1) preferir import como pacote (etheria.services.generator_service)
# 2) fallback para 'services.generator_service' adicionando a raiz do projeto ao sys.path
try:
    # tente como pacote instalado/visível
    generator_service = importlib.import_module("etheria.services.generator_service")
except Exception:
    try:
        # se não estiver instalado, tente importar pelo caminho relativo
        # garantindo que a raiz do projeto esteja no sys.path
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        generator_service = importlib.import_module("services.generator_service")
    except Exception:
        generator_service = None
        generator_import_error = traceback.format_exc()

# armazenar erro de import para exibir no UI sem quebrar a execução
st.session_state.setdefault("generator_import_error", generator_import_error)

# imports locais (após garantir streamlit e generator_service)
from etheria import rules, interpretations, influences, astrology
from etheria.utils import safe_filename

# serviços auxiliares (use importlib/fallbacks se necessário)
try:
    from services.analysis import generate_chart_summary, generate_planet_reading, generate_ai_interpretation_cached
except Exception:
    # fallback: tentar via pacote etheria.services.analysis
    try:
        analysis_mod = importlib.import_module("etheria.services.analysis")
        generate_chart_summary = getattr(analysis_mod, "generate_chart_summary", None)
        generate_planet_reading = getattr(analysis_mod, "generate_planet_reading", None)
        generate_ai_interpretation_cached = getattr(analysis_mod, "generate_ai_interpretation_cached", None)
    except Exception:
        generate_chart_summary = generate_planet_reading = generate_ai_interpretation_cached = None

# expor funções do generator_service se disponíveis
generate_analysis = None
generate_ai_text_from_chart = None
if generator_service:
    generate_analysis = getattr(generator_service, "generate_analysis", None)
    generate_ai_text_from_chart = getattr(generator_service, "generate_ai_text_from_chart", None)

# Exportar o que for necessário
__all__ = [
    "generate_analysis",
    "generate_ai_text_from_chart",
    "generator_service",
]

# cache local
_aspects_cache: Dict[str, dict] = {}

# Page config
st.set_page_config(page_title="Etheria — Painel Esotérico", layout="wide")

# Inicialização segura de session_state
_defaults = {
    "house_system": "P",
    "map_ready": False,
    "map_fig": None,
    "map_summary": None,
    "lat": None,
    "lon": None,
    "tz_name": None,
    "address": None,
    "lat_manual": -23.6636,
    "lon_manual": -46.5381,
    "tz_manual": "America/Sao_Paulo",
    "selected_planet": None,
    "_last_selected_planet": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v
del _defaults

# Tentativa de importar geocoding/timezone libs com fallback
try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
    GEOCODE_AVAILABLE = True
    logger.info("geopy disponível")
except Exception as e:
    GEOCODE_AVAILABLE = False
    logger.warning("geopy não disponível: %s", e)

# timezone libs: tentamos pytz, zoneinfo (stdlib) e dateutil
TZ_SUPPORT = {}
try:
    import pytz
    TZ_SUPPORT["pytz"] = pytz
    logger.info("pytz disponível")
except Exception:
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        TZ_SUPPORT["zoneinfo"] = ZoneInfo
        logger.info("zoneinfo disponível (stdlib)")
    except Exception:
        try:
            from dateutil import tz as dateutil_tz
            TZ_SUPPORT["dateutil"] = dateutil_tz
            logger.info("dateutil.tz disponível")
        except Exception:
            TZ_SUPPORT = {}
            logger.warning("Nenhuma biblioteca de timezone disponível (pytz/zoneinfo/dateutil)")

# plotly detection
try:
    import plotly.graph_objects as go  # type: ignore
    PLOTLY_AVAILABLE = True
    logger.info("plotly disponível")
except Exception as e:
    PLOTLY_AVAILABLE = False
    logger.warning("plotly não disponível: %s", e)

# Importações do projeto (ajuste conforme sua estrutura)
from services.swisseph_client import natal_positions
import importlib, os, sys, traceback

fetch_natal_chart = None
APIClientError = None
_api_client_import_error = None

try:
    # preferir import via pacote instalado
    mod = importlib.import_module("etheria.services.api_client")
except Exception:
    try:
        # fallback: garantir raiz do projeto no sys.path e importar services.api_client
        project_root = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        mod = importlib.import_module("services.api_client")
    except Exception:
        mod = None
        _api_client_import_error = traceback.format_exc()

if mod:
    fetch_natal_chart = getattr(mod, "fetch_natal_chart_api", None)
    APIClientError = getattr(mod, "APIClientError", None)
from etheria.astrology import positions_table, compute_aspects
from components.chart_svg import render_wheel_svg

# -------------------- Helpers --------------------

def _get_canonical_and_label(sel: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        return _canonical_and_label(sel)
    except Exception:
        try:
            return influences._to_canonical(sel), sel
        except Exception:
            return None, sel

def get_reading(summary_obj, sel_planet):
    """Retorna (canonical, label, reading_dict) ou (None, None, None)."""
    if not summary_obj or not sel_planet:
        return None, None, None
    canonical, label = _get_canonical_and_label(sel_planet)
    reading = None
    try:
        reading = summary_obj.get("readings", {}).get(canonical) or summary_obj.get("readings", {}).get(sel_planet)
    except Exception:
        reading = None
    return canonical, label, reading

def normalize_degree_sign(reading):
    """Garante sign e degree consistentes, usando longitude se necessário."""
    if not reading:
        return None, None
    sign = reading.get("sign")
    degree = reading.get("degree") or reading.get("deg") or None
    try:
        if (degree is None or sign is None) and reading.get("longitude") is not None:
            sign_calc, deg_calc, _ = astrology.lon_to_sign_degree(float(reading.get("longitude")))
            sign = sign or sign_calc
            degree = degree or round(float(deg_calc), 4)
    except Exception:
        pass
    return sign, degree

def resolve_house(reading, summary_obj, canonical, sel_planet, house_system=None):
    """
    Resolve a casa com prioridade:
      1) reading['house']
      2) summary['planets'][canonical]['house'] ou summary['table']
      3) calcular a partir de cusps (se disponíveis)
      4) calcular para sistemas simples (Equal, Whole Sign) a partir do Ascendente
    Retorna int 1..12 ou None.
    """
    # 0) helper interno: normalizar cusps para lista de 12 floats (índices 1..12 ou 0..11)
    def _normalize_cusps(raw):
        if not raw:
            return None
        # aceitar dict {1:deg,...} ou list [deg1,...] ou list com 13 itens (0 unused)
        try:
            if isinstance(raw, dict):
                # ordenar por chave numérica e extrair 1..12
                vals = []
                for i in range(1, 13):
                    v = raw.get(i) or raw.get(str(i))
                    if v is None:
                        return None
                    vals.append(float(v) % 360.0)
                return vals
            if isinstance(raw, (list, tuple)):
                arr = list(raw)
                # caso comum: 13 itens com índice 0 vazio
                if len(arr) == 13:
                    vals = [float(x) % 360.0 for x in arr[1:13]]
                    return vals
                # caso comum: 12 itens 0..11
                if len(arr) == 12:
                    vals = [float(x) % 360.0 for x in arr]
                    return vals
        except Exception:
            return None
        return None

    # helper: determina casa a partir de cusps normalizados (list de 12 degs)
    def _house_from_cusps(lon_deg, cusps_list):
        lon = float(lon_deg) % 360.0
        # cusps_list assumed ordered for houses 1..12
        for i in range(12):
            a = cusps_list[i]
            b = cusps_list[(i + 1) % 12]
            if a < b:
                if a <= lon < b:
                    return i + 1
            else:
                # wrap-around
                if lon >= a or lon < b:
                    return i + 1
        return None

    # helper: obter ascendente (longitude) de summary
    def _get_ascendant(summary_obj):
        # tentar chaves comuns
        candidates = [
            summary_obj.get("ascendant"),
            summary_obj.get("asc"),
            summary_obj.get("ascendant_longitude"),
            summary_obj.get("ascendant_deg"),
            # summary['planets']['ASC'] ou 'Asc' ou 'AC'
            None
        ]
        # tentar planets map
        try:
            planets_map = summary_obj.get("planets") or {}
            for key in ("ASC", "Asc", "Ascendant", "AC"):
                if planets_map.get(key):
                    p = planets_map.get(key)
                    if isinstance(p, dict) and p.get("longitude") is not None:
                        candidates.append(p.get("longitude"))
        except Exception:
            pass
        for c in candidates:
            if c is None:
                continue
            try:
                return float(c) % 360.0
            except Exception:
                continue
        return None

    # 1) direto do reading
    try:
        house = reading.get("house") if reading else None
    except Exception:
        house = None

    # se house já válido, normalizar e retornar
    try:
        if house not in (None, "", "None"):
            return int(float(house))
    except Exception:
        house = None

    # 2) tentar summary['planets'] por canonical/sel_planet
    if summary_obj:
        try:
            planets_map = summary_obj.get("planets", {}) or {}
            planet_entry = planets_map.get(canonical) or planets_map.get(sel_planet)
            if planet_entry and isinstance(planet_entry, dict):
                candidate = planet_entry.get("house")
                if candidate not in (None, "", "None"):
                    try:
                        return int(float(candidate))
                    except Exception:
                        pass
        except Exception:
            pass

    # 3) tentar summary['table']
    if summary_obj:
        try:
            table = summary_obj.get("table") or []
            for row in table:
                try:
                    if row.get("planet") == canonical or row.get("planet") == sel_planet:
                        if row.get("house") not in (None, "", "None"):
                            return int(float(row.get("house")))
                except Exception:
                    continue
        except Exception:
            pass

    # 4) tentar calcular a partir de cusps (várias formas aceitas)
    if summary_obj:
        raw_cusps = summary_obj.get("cusps") or summary_obj.get("house_cusps") or summary_obj.get("cusps_degrees")
        cusps = _normalize_cusps(raw_cusps)
        if cusps:
            # obter longitude do planeta
            try:
                lon = None
                if reading and reading.get("longitude") is not None:
                    lon = float(reading.get("longitude"))
                else:
                    # tentar summary['planets'] longitude
                    planets_map = summary_obj.get("planets") or {}
                    p = planets_map.get(canonical) or planets_map.get(sel_planet)
                    if isinstance(p, dict) and p.get("longitude") is not None:
                        lon = float(p.get("longitude"))
                    else:
                        # tentar summary['table']
                        table = summary_obj.get("table") or []
                        for row in table:
                            try:
                                if row.get("planet") == canonical or row.get("planet") == sel_planet:
                                    lon = row.get("longitude") or row.get("deg") or row.get("degree")
                                    if lon is not None:
                                        lon = float(lon)
                                        break
                            except Exception:
                                continue
                if lon is not None:
                    h = _house_from_cusps(lon, cusps)
                    if h:
                        return int(h)
            except Exception:
                pass

    # 5) se não há cusps, tentar sistemas simples a partir do Ascendente (Whole Sign, Equal)
    hs = house_system or (st.session_state.get("house_system") if "st" in globals() and hasattr(st, "session_state") else None)
    try:
        lon = None
        if reading and reading.get("longitude") is not None:
            lon = float(reading.get("longitude")) % 360.0
        else:
            # tentar obter longitude do planets map/table
            if summary_obj:
                planets_map = summary_obj.get("planets") or {}
                p = planets_map.get(canonical) or planets_map.get(sel_planet)
                if isinstance(p, dict) and p.get("longitude") is not None:
                    lon = float(p.get("longitude")) % 360.0
                else:
                    table = summary_obj.get("table") or []
                    for row in table:
                        try:
                            if row.get("planet") == canonical or row.get("planet") == sel_planet:
                                lon = row.get("longitude") or row.get("deg") or row.get("degree")
                                if lon is not None:
                                    lon = float(lon) % 360.0
                                    break
                        except Exception:
                            continue
    except Exception:
        lon = None

    if lon is None:
        return None

    asc = _get_ascendant(summary_obj)

    # Whole Sign: casa = floor((lon - asc)/30) + 1
    if hs and hs.upper() in ("W", "WHOLE", "WHOLE SIGN", "WHOLE_SIGN"):
        if asc is None:
            # fallback: se não há ascendente, usar 0 como referência (menos ideal)
            asc = 0.0
        try:
            offset = (lon - asc) % 360.0
            return int(offset // 30) + 1
        except Exception:
            return None

    # Equal houses (a partir do Ascendant)
    if hs and hs.upper() in ("E", "EQUAL"):
        if asc is None:
            asc = 0.0
        try:
            offset = (lon - asc) % 360.0
            return int(offset // 30) + 1
        except Exception:
            return None

    # Se chegou aqui, não foi possível resolver
    return None

def ensure_aspects(summary_obj):
    """Retorna aspects (já calculados ou computados) ou None. Usa cache simples."""
    if not summary_obj:
        return None
    if summary_obj.get("aspects"):
        return summary_obj.get("aspects")
    try:
        key = str(hash(json.dumps(summary_obj, sort_keys=True, default=str)))
    except Exception:
        key = None
    if key and key in _aspects_cache:
        return _aspects_cache[key]

    positions = {}
    planets_map = summary_obj.get("planets") or {}
    if isinstance(planets_map, dict) and planets_map:
        for pname, pdata in planets_map.items():
            try:
                if isinstance(pdata, dict) and pdata.get("longitude") is not None:
                    positions[pname] = float(pdata.get("longitude"))
                elif isinstance(pdata, (int, float)):
                    positions[pname] = float(pdata)
            except Exception:
                continue

    if not positions:
        readings_map = summary_obj.get("readings") or {}
        if isinstance(readings_map, dict) and readings_map:
            for pname, rdata in readings_map.items():
                try:
                    lon = None
                    if isinstance(rdata, dict):
                        lon = rdata.get("longitude") or rdata.get("lon") or rdata.get("deg") or rdata.get("degree")
                    if lon is not None:
                        positions[pname] = float(lon)
                except Exception:
                    continue

    if not positions:
        table = summary_obj.get("table") or []
        if isinstance(table, list):
            for row in table:
                try:
                    pname = row.get("planet")
                    lon = row.get("longitude") or row.get("deg") or row.get("degree")
                    if pname and lon is not None:
                        positions[pname] = float(lon)
                except Exception:
                    continue

    if positions:
        try:
            aspects = astrology.compute_aspects(positions, orb=6.0)
            if key:
                _aspects_cache[key] = aspects
            return aspects
        except Exception:
            return None
    return None

def geocode_place_safe(place_query: str) -> Tuple[float, float, str, str]:
    """
    Usa Nominatim via geopy para obter latitude, longitude e inferir timezone.
    Só chama se GEOCODE_AVAILABLE for True.
    """
    if not GEOCODE_AVAILABLE:
        raise RuntimeError("Geocoding não disponível no ambiente atual")

    geolocator = Nominatim(user_agent="etheria-app/0.1 (contato: vitor)")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, swallow_exceptions=False)
    location = geocode(place_query, language="pt", addressdetails=True, timeout=10)
    if not location:
        raise ValueError("Local não encontrado")

    lat = float(location.latitude)
    lon = float(location.longitude)

    # timezonefinder import só se disponível
    try:
        from timezonefinder import TimezoneFinder
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=lat, lng=lon) or "UTC"
    except Exception:
        tz_name = "UTC"

    return lat, lon, tz_name, location.address

# Fallback geocode via requests/Nominatim (não depende de geopy)
import requests
def geocode_place_nominatim(place: str, user_agent: str = "etheria-app/0.1 (contato: vitor)"):
    url = "https://nominatim.openstreetmap.org/search"
    params = {"q": place, "format": "json", "limit": 1, "addressdetails": 1}
    headers = {"User-Agent": user_agent}
    resp = requests.get(url, params=params, headers=headers, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError("Nenhum resultado encontrado para o local informado.")
    item = data[0]
    lat = float(item["lat"])
    lon = float(item["lon"])
    display_name = item.get("display_name", place)
    return lat, lon, display_name

def parse_time_input(free_text: str) -> Optional[dtime]:
    """
    Tenta parsear strings de hora comuns: "14:30", "14:30:15", "2:30 PM".
    Retorna objeto datetime.time ou None se inválido.
    """
    if not free_text or free_text.strip() == "":
        return None
    s = free_text.strip()
    for fmt in ("%H:%M:%S", "%H:%M", "%I:%M %p", "%I:%M:%S %p"):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.time()
        except Exception:
            continue
    try:
        from dateutil import parser as dateutil_parser  # type: ignore
        dt = dateutil_parser.parse(s)
        return dt.time()
    except Exception:
        return None

def to_local_datetime(bdate: date, btime: dtime, tz_name: str) -> datetime:
    """
    Converte data/hora local (sem tzinfo) para datetime timezone-aware.
    """
    naive = datetime.combine(bdate, btime)
    if "pytz" in TZ_SUPPORT:
        tz = TZ_SUPPORT["pytz"].timezone(tz_name)
        return tz.localize(naive)
    if "zoneinfo" in TZ_SUPPORT:
        ZoneInfo = TZ_SUPPORT["zoneinfo"]
        return naive.replace(tzinfo=ZoneInfo(tz_name))
    if "dateutil" in TZ_SUPPORT:
        return naive.replace(tzinfo=TZ_SUPPORT["dateutil"].gettz(tz_name))
    return naive

# render_wheel_plotly: manter sua implementação robusta (trecho completo)
def render_wheel_plotly(planets: dict, cusps: list):
    if not PLOTLY_AVAILABLE:
        logger.warning("Plotly não disponível; render_wheel_plotly retornará None")
        return None

    try:
        import plotly.graph_objects as go
    except Exception:
        return None

    import math, logging
    logger = logging.getLogger("render_wheel_plotly")

    def extract_lon(pdata):
        if pdata is None:
            return None
        if isinstance(pdata, (int, float)):
            return float(pdata)
        if isinstance(pdata, str):
            try:
                return float(pdata)
            except Exception:
                return None
        if isinstance(pdata, dict):
            for key in ("lon", "longitude", "long", "ecl_lon", "ecliptic_longitude"):
                if key in pdata and pdata[key] is not None:
                    try:
                        return float(pdata[key])
                    except Exception:
                        return None
        return None

    valid_planets = {}
    invalid_planets = []
    for name, pdata in (planets or {}).items():
        lon = extract_lon(pdata)
        if lon is None:
            invalid_planets.append((name, pdata))
        else:
            valid_planets[name] = lon

    valid_cusps = []
    invalid_cusps = []
    if cusps:
        for i, c in enumerate(cusps):
            try:
                if c is None:
                    raise ValueError("None cusp")
                valid_cusps.append(float(c))
            except Exception:
                invalid_cusps.append((i, c))

    if invalid_planets:
        logger.warning("Planetas inválidos (sem longitude): %s", invalid_planets)
    if invalid_cusps:
        logger.warning("Cusps inválidos: %s", invalid_cusps)

    if len(valid_planets) == 0:
        logger.error("Nenhum planeta válido para desenhar. valid_planets=%s", valid_planets)
        return None

    def lon_to_theta(lon_deg):
        return (360.0 - float(lon_deg)) % 360.0

    planet_symbols = {
        "Sun": "☉", "Sol": "☉",
        "Moon": "☾", "Lua": "☾",
        "Mercury": "☿", "Mercúrio": "☿",
        "Venus": "♀", "Vênus": "♀",
        "Mars": "♂", "Marte": "♂",
        "Jupiter": "♃", "Júpiter": "♃",
        "Saturn": "♄", "Saturno": "♄",
        "Uranus": "♅", "Urano": "♅",
        "Neptune": "♆", "Netuno": "♆",
        "Pluto": "♇", "Plutão": "♇",
        "Asc": "ASC", "ASCENDANT": "ASC"
    }

    names = []
    thetas = []
    hover_texts = []
    symbol_texts = []
    lon_values = []

    for name, lon in valid_planets.items():
        try:
            theta = lon_to_theta(lon)
        except Exception:
            logger.warning("Falha ao converter longitude para theta: %s -> %s", name, lon)
            continue
        sign_index = int(float(lon) // 30) % 12
        degree_in_sign = float(lon) % 30
        names.append(name)
        thetas.append(theta)
        lon_values.append(float(lon))
        hover_texts.append(f"{name}<br>{lon:.2f}° eclíptico<br>{degree_in_sign:.1f}°")
        symbol_texts.append(planet_symbols.get(name, name))

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=[1.0]*len(thetas),
        theta=thetas,
        mode="markers+text",
        marker=dict(size=14, color="#ff7f0e", line=dict(color="#333", width=1)),
        text=symbol_texts,
        textfont=dict(size=14, family="DejaVu Sans, Arial"),
        hovertext=hover_texts,
        hovertemplate="%{hovertext}<extra></extra>",
        customdata=names,
        name="Planetas"
    ))

    fig.add_trace(go.Scatterpolar(
        r=[1.08]*len(thetas),
        theta=thetas,
        mode="text",
        text=names,
        textfont=dict(size=11, color="#111"),
        hoverinfo="none",
        showlegend=False
    ))

    if valid_cusps:
        for i, cusp in enumerate(valid_cusps, start=1):
            theta_cusp = lon_to_theta(cusp)
            fig.add_trace(go.Scatterpolar(
                r=[0.15, 1.0],
                theta=[theta_cusp, theta_cusp],
                mode="lines",
                line=dict(color="#888", width=1.2, dash="dot"),
                hoverinfo="none",
                showlegend=False
            ))
            fig.add_trace(go.Scatterpolar(
                r=[0.08],
                theta=[theta_cusp],
                mode="text",
                text=[f"C{i}"],
                textfont=dict(size=10, color="#444"),
                hoverinfo="none",
                showlegend=False
            ))

    if len(lon_values) >= 2:
        ASPECTS = [
            ("Conjunção", 0, 8, "#222222", 2.5),
            ("Sextil", 60, 6, "#2ca02c", 1.5),
            ("Quadratura", 90, 7, "#d62728", 1.8),
            ("Trígono", 120, 7, "#1f77b4", 1.8),
            ("Oposição", 180, 8, "#9467bd", 2.0),
        ]
        n = len(names)
        for i in range(n):
            for j in range(i+1, n):
                lon_i = lon_values[i]
                lon_j = lon_values[j]
                diff = abs((lon_i - lon_j + 180) % 360 - 180)
                for asp_name, asp_angle, asp_orb, asp_color, asp_width in ASPECTS:
                    if abs(diff - asp_angle) <= asp_orb:
                        theta_i = math.radians(lon_to_theta(lon_i))
                        theta_j = math.radians(lon_to_theta(lon_j))
                        xi = math.cos(theta_i); yi = math.sin(theta_i)
                        xj = math.cos(theta_j); yj = math.sin(theta_j)
                        xm = (xi + xj) / 2 * 0.75
                        ym = (yi + yj) / 2 * 0.75
                        def cart_to_polar(x, y):
                            ang = (360.0 - (math.degrees(math.atan2(y, x)) % 360.0)) % 360.0
                            rad = math.hypot(x, y)
                            return rad, ang
                        r1, t1 = cart_to_polar(xi, yi)
                        r2, t2 = cart_to_polar(xm, ym)
                        r3, t3 = cart_to_polar(xj, yj)
                        fig.add_trace(go.Scatterpolar(
                            r=[r1, r2, r3],
                            theta=[t1, t2, t3],
                            mode="lines",
                            line=dict(color=asp_color, width=asp_width),
                            opacity=0.6,
                            hoverinfo="none",
                            showlegend=False
                        ))
                        break

    sign_names = ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]
    sign_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
    tickvals = [(360.0 - (i * 30 + 15)) % 360.0 for i in range(12)]
    ticktext = [f"{sign_symbols[i]} {sign_names[i]}" for i in range(12)]

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False),
            angularaxis=dict(direction="clockwise", rotation=90,
                            tickmode="array", tickvals=tickvals, ticktext=ticktext,
                            tickfont=dict(size=11), gridcolor="#eee")
        ),
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10),
        height=700
    )
    fig.update_traces(textfont=dict(size=12))
    return fig

st.markdown("<h1 style='text-align:left'>Mapa Astral ♎ </h1>", unsafe_allow_html=True)
st.markdown("Preencha os dados de nascimento no formulário lateral e clique em 'Gerar Mapa'.")

# -------------------- UI --------------------
# mapa_astral.py

# Interface de captura do mapa natal e integração com generator_service.
# - Valida e normaliza inputs do usuário.
# - Resolve geocode e timezone com fallback.
# - Calcula posições (swisseph ou API) e gera summary.
# - Reaproveita summary para chamar generator_service (texto/AI).
# - Mantém estado em st.session_state e fornece mensagens claras ao usuário.

def to_local_datetime(bdate: date, btime: dt_time | str, timezone_str: str):
    """
    Converte data (bdate) e hora (btime) para datetime timezone-aware.
    - btime pode ser datetime.time ou string (ex.: '14:30' ou '2:30 PM').
    - timezone_str é algo como 'America/Sao_Paulo' (pode ser None).
    Retorna datetime aware ou None se não for possível.
    """
    # Se timezone não informado, tentar resolver via get_timezone_from_coords foi feito antes;
    if not timezone_str:
        logger.debug("to_local_datetime: timezone_str ausente")
        return None

    # Se btime for string, delegar ao parse_birth_time (que já localiza)
    try:
        if isinstance(btime, str):
            # parse_birth_time espera string, date e timezone
            local_dt = parse_birth_time(btime, bdate, timezone_str)
            return local_dt
        elif isinstance(btime, dt_time):
            try:
                tz = pytz.timezone(timezone_str)
            except Exception:
                logger.exception("Timezone inválido em to_local_datetime: %s", timezone_str)
                return None
            naive = datetime.combine(bdate, btime)
            return tz.localize(naive)
        else:
            logger.debug("to_local_datetime: tipo de btime inesperado: %s", type(btime))
            return None
    except Exception as e:
        logger.exception("Erro em to_local_datetime: %s", e)
        return None

logger = logging.getLogger(__name__)

# -------------------------
# Utilitários locais
# -------------------------
def _is_arcano_text_block(text: str) -> bool:
    """Heurística simples para detectar texto de arcano já presente."""
    if not text:
        return False
    t = text.lower()
    return "arcano" in t or "o arcano" in t or "a arcano" in t

def enrich_summary_with_astrology(summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Garante que summary['readings'] tenha interpretações astrológicas por planeta.
    - Normaliza chaves para canonical (via influences._to_canonical)
    - Preenche sign/degree/longitude usando summary['planets'] quando disponível
    - Gera interpretation_short/interpretation_long via interpretations.classic_for_planet
    quando ausentes ou quando os textos existentes parecem ser apenas o arcano
    Retorna o summary modificado.
    """
    if not summary or not isinstance(summary.get("readings"), dict):
        return summary

    readings = summary.get("readings", {})
    planets_map = summary.get("planets", {}) or {}
    normalized: Dict[str, Any] = {}

    for raw_key, r in readings.items():
        if not r:
            continue
        canonical = influences._to_canonical(raw_key)
        rd = dict(r)  # cópia rasa

        # preencher posição a partir de summary['planets'] por canonical ou raw_key
        planet_entry = None
        if planets_map.get(canonical):
            planet_entry = planets_map.get(canonical)
        elif planets_map.get(raw_key):
            planet_entry = planets_map.get(raw_key)

        if planet_entry:
            lon_val = planet_entry.get("longitude") if isinstance(planet_entry, dict) else planet_entry
            try:
                lon = float(lon_val)
                rd.setdefault("longitude", round(lon, 4))
                # usar astrology.lon_to_sign_degree para preencher sign/degree/sign_index
                try:
                    sign, degree, sign_index = astrology.lon_to_sign_degree(lon)
                    rd.setdefault("sign", sign)
                    rd.setdefault("degree", round(degree, 4))
                    rd.setdefault("sign_index", sign_index)
                except Exception:
                    rd.setdefault("degree", rd.get("degree"))
            except Exception:
                pass

        # garantir campos de interpretação mínimos
        short_text = rd.get("interpretation_short") or ""
        long_text = rd.get("interpretation_long") or ""

        arcano_present = bool(rd.get("arcano_info") or rd.get("arcano"))
        arcano_like = _is_arcano_text_block(short_text) or _is_arcano_text_block(long_text)

        need_astrology = False
        if not short_text and not long_text:
            need_astrology = True
        elif arcano_present and arcano_like:
            need_astrology = True

        if need_astrology:
            try:
                classic = interpretations.classic_for_planet(summary, canonical)
                rd["interpretation_short"] = rd.get("interpretation_short") or classic.get("short") or ""
                rd["interpretation_long"] = rd.get("interpretation_long") or classic.get("long") or rd["interpretation_short"]
            except Exception:
                try:
                    rd["interpretation_short"] = rd.get("interpretation_short") or rules.synthesize_export_text(summary, canonical, summary.get("name", "Consulente"))
                    rd["interpretation_long"] = rd.get("interpretation_long") or rd["interpretation_short"]
                except Exception:
                    rd.setdefault("interpretation_short", "")
                    rd.setdefault("interpretation_long", "")

        normalized[canonical] = rd

    summary["readings"] = normalized
    return summary

def _parse_time_string(t: str) -> Optional[dt_time]:
    """
    Normaliza a hora informada pelo usuário para datetime.time.
    Aceita formatos: '14:30', '2:30 PM', '02:30pm', '1430', '2 PM', '2pm', '14', etc.
    Retorna datetime.time ou None se não conseguir parsear.
    """
    if not t or not str(t).strip():
        return None
    s = str(t).strip()
    s = " ".join(s.split())
    fmts = [
        "%H:%M", "%H.%M", "%H%M",
        "%I:%M %p", "%I:%M%p", "%I %p", "%I%p",
        "%I.%M %p", "%I.%M%p"
    ]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return dt.time()
        except Exception:
            continue
    # tentativa manual
    try:
        low = s.lower().replace(".", "")
        if low.endswith("am") or low.endswith("pm"):
            num = low[:-2].strip()
            ampm = low[-2:]
            h = int(num)
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            return dt_time(hour=h, minute=0)
        if low.isdigit():
            h = int(low)
            if 0 <= h < 24:
                return dt_time(hour=h, minute=0)
    except Exception:
        pass
    return None

def _resolve_place_and_tz(place: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    """
    Tenta resolver lat/lon/timezone/address usando múltiplos provedores.
    Retorna (lat, lon, tz_name, address). Pode retornar None para cada item se não resolvido.
    """
    lat = st.session_state.get("lat_manual")
    lon = st.session_state.get("lon_manual")
    tz_name = st.session_state.get("tz_manual")
    address = None

    if place and place.strip():
        # Primeiro: geocode seguro (ex.: provider com API key)
        try:
            lat_r, lon_r, tz_r, address_r = geocode_place_safe(place)
            if lat_r is not None and lon_r is not None:
                return lat_r, lon_r, tz_r, address_r
        except Exception as e:
            logger.warning("geocode_place_safe falhou: %s", e)

        # Fallback: Nominatim
        try:
            lat_r, lon_r, address_r = geocode_place_nominatim(place)
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                tz_r = tf.timezone_at(lat=lat_r, lng=lon_r) or st.session_state.get("tz_manual")
            except Exception:
                tz_r = st.session_state.get("tz_manual")
            if lat_r is not None and lon_r is not None:
                return lat_r, lon_r, tz_r, address_r
        except Exception as e:
            logger.warning("geocode_place_nominatim falhou: %s", e)

    # Se não conseguiu, retornar valores manuais (podem ser None)
    return lat, lon, tz_name, address

# -------------------------
# UI: formulário lateral
# -------------------------
HOUSE_CHOICES = [
    ("Placidus", "P"),
    ("Koch", "K"),
    ("Campanus", "C"),
    ("Porphyry", "O"),
    ("Equal", "E"),
    ("Whole Sign", "W"),
    ("Regiomontanus", "R")
]
house_labels = [f"{name} ({code})" for name, code in HOUSE_CHOICES]
HOUSE_NAME_MAP = {code: name for name, code in HOUSE_CHOICES}

with st.sidebar:
    with st.form("birth_form_sidebar", border=False):
        name = st.text_input("Nome", value="")
        place = st.text_input("Cidade de nascimento (ex: São Paulo, Brasil)", value="São Paulo, São Paulo, Brasil")
        bdate = st.date_input("Data de nascimento",
            value=date(1990, 4, 25),
            min_value=date(1900, 1, 1),
            max_value=date(2100, 12, 31))
        btime_free = st.text_input("Hora de nascimento (hora local) (ex.: 14:30, 2:30 PM)", value="")
        source = st.radio("Fonte de cálculo", ["swisseph", "api"], index=0)

        default_code = st.session_state.get("house_system", "P")
        default_index = next((i for i, (_, code) in enumerate(HOUSE_CHOICES) if code == default_code), 0)
        selected_label = st.selectbox("Sistema de casas", house_labels, index=default_index, help="Escolha o sistema de casas.")
        selected_code = selected_label.split("(")[-1].strip(")")
        st.session_state["house_system"] = selected_code
        st.write("Sistema selecionado:", HOUSE_NAME_MAP.get(selected_code, selected_code))

        submitted = st.form_submit_button("Gerar Mapa")

# -------------------------
# Processamento após submit
# -------------------------
if submitted:
    st.sidebar.success("Mapa gerado com sucesso!")
    # 1) Normalizar e validar hora (obrigatória)
    parsed_time = _parse_time_string(btime_free)
    if parsed_time is None:
        st.error("Hora de nascimento inválida ou não informada. Por favor informe no formato 'HH:MM' ou '2:30 PM'.")
    else:
        btime = parsed_time  # datetime.time

        # 2) Resolver local/coords/timezone
        lat, lon, tz_name, address = _resolve_place_and_tz(place)
        # salvar valores resolvidos na sessão para reutilização
        if lat is not None:
            st.session_state["lat"] = lat
        if lon is not None:
            st.session_state["lon"] = lon
        if tz_name:
            st.session_state["tz_name"] = tz_name
        if address:
            st.session_state["address"] = address

        # 3) Validar lat/lon
        if lat is None or lon is None:
            st.warning("Latitude/Longitude não resolvidas automaticamente. Informe manualmente ou corrija o local.")
            # não prosseguir com cálculo local; permitir que usuário corrija
        elif not (-90 <= lat <= 90 and -180 <= lon <= 180):
            st.error("Latitude/Longitude inválidas. Corrija os valores antes de gerar o mapa.")
        else:
            # 4) Construir datetime local (timezone-aware preferencialmente)
            try:
                dt_local = to_local_datetime(bdate, btime, tz_name)
                if dt_local is None:
                    raise ValueError("to_local_datetime retornou None")
            except Exception as e:
                logger.warning("to_local_datetime falhou: %s", e)
                st.warning(f"Falha ao aplicar timezone '{tz_name}'. Verifique o timezone. Não será possível calcular posições precisas sem timezone.")
                dt_local = None

            # 5) Obter posições (swisseph ou API)
            planets = {}
            cusps = []
            data = None
            try:
                if source == "api":
                    if dt_local is None:
                        st.error("Não é possível usar a fonte 'api' sem um datetime local válido com timezone.")
                    else:
                        with st.spinner("Buscando mapa via API..."):
                            data = fetch_natal_chart(name, dt_local, lat, lon, tz_name)
                            planets = data.get("planets") or {}
                            cusps = data.get("cusps") or []
                else:
                    if dt_local is None:
                        st.error("Não é possível calcular localmente sem datetime timezone-aware. Ajuste o timezone.")
                    else:
                        with st.spinner("Calculando mapa local (swisseph)..."):
                            data = natal_positions(dt_local, lat, lon, house_system=st.session_state.get("house_system", "P"))
                            planets = data.get("planets", {})
                            cusps = data.get("cusps", [])
            except Exception as e:
                logger.exception("Erro ao obter posições natales: %s", e)
                st.error("Erro ao calcular posições natales. Verifique dependências (pyswisseph) ou tente a opção 'api'.")

            # 6) Se obtivemos planets, gerar summary e enriquecer
            if planets:
                try:
                    table = positions_table(planets)
                    aspects = compute_aspects(planets)
                    summary = generate_chart_summary(planets, name or "Consulente", bdate)
                    summary["table"] = table
                    summary["cusps"] = cusps
                    summary["aspects"] = aspects
                    # preencher campos úteis no summary
                    summary.setdefault("place", place)
                    summary.setdefault("bdate", bdate)
                    summary.setdefault("btime", btime)
                    summary.setdefault("lat", lat)
                    summary.setdefault("lon", lon)
                    summary.setdefault("timezone", tz_name)
                    # enriquecer leituras se necessário
                    summary = enrich_summary_with_astrology(summary)
                except Exception as e:
                    logger.exception("Erro ao gerar summary: %s", e)
                    st.error("Erro ao processar dados astrológicos.")
                    summary = None

                # 7) Renderizar figura e salvar em session_state
                if summary:
                    try:
                        fig = render_wheel_plotly(summary.get("planets", {}), [c.get("longitude") for c in summary.get("table", [])] if summary.get("table") else [])
                        st.session_state["map_fig"] = fig
                        st.session_state["map_summary"] = summary
                        st.session_state["map_ready"] = True
                        
                    except Exception as e:
                        logger.exception("Erro ao renderizar figura: %s", e)
                        st.error("Falha ao desenhar o mapa. Verifique se o Plotly está disponível.")
                        st.session_state["map_ready"] = False
                        st.session_state["map_fig"] = None

                    # 8) Montar chart_input e chamar generator_service (texto)
                    chart_input = {
                        "name": name,
                        "place": summary.get("place") or place,
                        "bdate": bdate,
                        "btime": btime,
                        "lat": lat,
                        "lon": lon,
                        "timezone": tz_name,
                        "summary": summary,
                        "house_system": st.session_state.get("house_system", "P"),
                    }
                    res = generate_analysis(chart_input, prefer="auto", text_only=True)

                    try:
                        with st.spinner("Gerando interpretação astrológica..."):
                            res = generate_analysis(chart_input, prefer="auto", text_only=True)
                    except Exception as e:
                        logger.exception("Erro ao chamar generate_analysis: %s", e)
                        st.error(f"Erro ao gerar interpretação: {e}")
                    else:
                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            analysis_text = res.get("analysis_text", "")
                            if analysis_text:
                                st.markdown("### Interpretação gerada")
                                st.markdown(analysis_text)
                            else:
                                st.info("Nenhuma interpretação retornada pelo serviço.")
                else:
                    st.warning("Resumo do mapa não pôde ser gerado; verifique logs.")
            else:
                st.warning("Não foi possível obter posições planetárias. Verifique timezone, lat/lon e hora informada.")

# -------------------- Renderização central + seleção de planeta (Parte 4) --------------------

# Recuperar summary e fig da sessão
summary = st.session_state.get("map_summary")
fig_saved = st.session_state.get("map_fig")
map_ready = st.session_state.get("map_ready", False)

from etheria import rules, interpretations, influences
from etheria.utils import safe_filename
from typing import Optional

def _canonical_and_label(name: Optional[str]):
    """
    Retorna (canonical_name, label_pt).
    Aceita 'Lua' ou 'Moon' e devolve ('Moon', 'Lua').
    """
    canonical = influences._to_canonical(name)
    label_pt = influences.CANONICAL_TO_PT.get(canonical, canonical)
    return canonical, label_pt

# LEFT / CENTER / RIGHT layout (após geração)
left_col, center_col, right_col = st.columns([0.8, 2.0, 1.0])

# LEFT: controles e tabela (se houver summary)
with left_col:
    st.markdown("### Controles")
    # show_aspects = st.checkbox("Mostrar aspectos", value=True)
    # show_houses = st.checkbox("Mostrar casas", value=True)
    # numerology_toggle = st.checkbox("Mostrar numerologia", value=True)
    use_ai = st.checkbox(
        "Usar IA para interpretações",
        value=False,
        help="Gera texto via IA Generativa proprietária."
    )

    st.markdown("### Positions")
    import pandas as _pd

    if summary:
        df = _pd.DataFrame(summary.get("table", []))
        if not df.empty and "planet" in df.columns:
            df_display = df.copy()
            df_display["planet"] = df_display["planet"].apply(
                lambda p: influences.CANONICAL_TO_PT.get(influences._to_canonical(p), p)
            )
        else:
            df_display = df
    else:
        df = _pd.DataFrame([])
        df_display = df

    if df_display.empty:
        st.info("Nenhuma posição disponível. Gere o mapa primeiro.")
    else:
        st.dataframe(df_display, use_container_width=True, height=300)
        planet_names = list(df["planet"].values)

        if not st.session_state.get("selected_planet") and planet_names:
            st.session_state["selected_planet"] = planet_names[0]

        def _on_select_planet():
            sel = st.session_state.get("planet_selectbox")
            st.session_state["selected_planet"] = sel

        default_index = 0
        current_sel = st.session_state.get("selected_planet")
        if current_sel in planet_names:
            default_index = planet_names.index(current_sel)
        st.selectbox(
            "Selecionar planeta",
            planet_names,
            index=default_index,
            key="planet_selectbox",
            on_change=_on_select_planet
        )

    st.divider()
    st.markdown("#### Leitura Sintética")

    sel_planet = st.session_state.get("selected_planet")
    if not sel_planet or not summary:
        st.info("Selecione um planeta na tabela para ver a leitura sintética.")
    else:
        canonical, label, reading = get_reading(summary, sel_planet)
        if not reading:
            st.info("Leitura ainda não gerada para este planeta; gere o mapa ou a interpretação.")
        else:
            sign, degree = normalize_degree_sign(reading)
            house = resolve_house(reading, summary, canonical, sel_planet)

            # construir leitura sintética curta
            planet_verb, planet_core = astrology.PLANET_CORE.get(canonical or sel_planet, ("", ""))
            sign_noun, sign_quality = astrology.SIGN_DESCRIPTIONS.get(sign, ("", ""))
            house_noun, house_theme = astrology.HOUSE_DESCRIPTIONS.get(int(house), ("", "")) if house else ("", "")

            parts = [p for p in (planet_verb, sign_noun, house_noun) if p]
            synthetic_line = " — ".join(parts) if parts else ""

            # palavras-chave curtas
            keywords = []
            if planet_core:
                keywords += [k.strip() for k in planet_core.split(",") if k.strip()]
            if sign_quality:
                keywords += [k.strip() for k in sign_quality.split(",") if k.strip()]
            if house_theme:
                keywords += [k.strip() for k in house_theme.split(",") if k.strip()]
            seen = []
            for k in keywords:
                if k not in seen:
                    seen.append(k)
            keywords_line = ", ".join(seen[:8]) if seen else None

            st.markdown(f"**{reading.get('name','Consulente')} — {reading.get('planet') or label}**")
            st.write(f"Signo: **{sign or '—'}**  •  Grau: **{degree or '—'}°**  •  Casa: **{house or '—'}**")

            if synthetic_line:
                
                st.write(synthetic_line)

            interp_local = astrology.interpret_planet_position(
                planet=canonical or sel_planet,
                sign=sign,
                degree=degree,
                house=house,
                aspects=summary.get("aspects"),
                context_name=reading.get("name") or summary.get("name")
            ) or {"short": ""}

            short_local = interp_local.get("short") or ""
            if short_local:
                st.write(short_local)
            elif keywords_line:
                st.write(f"Palavras-chave: {keywords_line}")
            else:
                st.write("—")

# CENTER: mapa + IA + interpretação
with center_col:
    st.subheader("Mapa Zodiacal")
    if not map_ready or fig_saved is None:
        st.info("Nenhum mapa gerado. Preencha os parâmetros e clique em 'Gerar Mapa'.")
    else:
        try:
            fig_dict = fig_saved.to_dict()
            fig = go.Figure(fig_dict)
        except Exception:
            fig = fig_saved

        # destacar seleção no mapa
        sel_name = st.session_state.get("selected_planet")
        if sel_name and summary:
            try:
                sel_lon = None
                canonical_sel = influences._to_canonical(sel_name)
                if summary.get("planets", {}).get(canonical_sel):
                    sel_lon = summary["planets"][canonical_sel].get("longitude")
                elif summary.get("planets", {}).get(sel_name):
                    sel_lon = summary["planets"][sel_name].get("longitude")
                if sel_lon is not None:
                    theta_sel = (360.0 - float(sel_lon)) % 360.0
                    fig.add_trace(go.Scatterpolar(
                        r=[1.0],
                        theta=[theta_sel],
                        mode="markers+text",
                        marker=dict(size=22, color="#1f77b4", line=dict(color="#000", width=1.5)),
                        text=[influences.CANONICAL_TO_PT.get(influences._to_canonical(sel_name), sel_name)],
                        textfont=dict(size=12, color="#000"),
                        hoverinfo="none",
                        showlegend=False
                    ))
            except Exception:
                pass

        # plot e captura de clique
        try:
            from streamlit_plotly_events import plotly_events
            plotly_events_available = True
        except Exception:
            plotly_events_available = False

        clicked_planet = None
        if plotly_events_available:
            events = plotly_events(fig, click_event=True, hover_event=False, select_event=False, key="plotly_events")
            if events:
                ev = events[0]
                cd = ev.get("customdata")
                if isinstance(cd, (list, tuple)) and len(cd) > 0:
                    clicked_planet = cd[0]
                elif isinstance(cd, str):
                    clicked_planet = cd
                if not clicked_planet:
                    clicked_planet = ev.get("text") or ev.get("pointNumber")
        else:
            st.plotly_chart(fig, use_container_width=True)

        if clicked_planet:
            clicked_planet = str(clicked_planet)
            canonical_clicked = influences._to_canonical(clicked_planet)
            if st.session_state.get("selected_planet") != canonical_clicked:
                st.session_state["selected_planet"] = canonical_clicked

        # interpretação curta + expander para completa
        st.markdown("### Interpretação Astrológica")

        sel_planet = st.session_state.get("selected_planet")
        canonical, label, reading = get_reading(summary, sel_planet)

        if reading:
            sign, degree = normalize_degree_sign(reading)
            house = resolve_house(reading, summary, canonical, sel_planet)
            aspects = ensure_aspects(summary)

            interp = astrology.interpret_planet_position(
                planet=canonical or sel_planet,
                sign=sign,
                degree=degree,
                house=house,
                aspects=aspects,
                context_name=reading.get("name") or summary.get("name")
            ) or {"short": "", "long": ""}

            # exibir curta e manter expander para completa
            # st.write(interp.get("short", ""))
            with st.expander("Ver interpretação completa"):
                st.write(interp.get("long", ""))
        else:
            # fallback: classic or general message
            if sel_planet and summary:
                canonical_fallback = influences._to_canonical(sel_planet)
                classic = {}
                try:
                    classic = interpretations.classic_for_planet(summary, canonical_fallback) if hasattr(interpretations, "classic_for_planet") else {}
                except Exception:
                    classic = {}
                st.write(classic.get("short", "") or "Interpretação não disponível.")
                with st.expander("Ver interpretação completa"):
                    st.write(classic.get("long", "") or "—")
            else:
                general = (summary.get("chart_interpretation") if summary else None) or "Selecione um planeta para ver a interpretação contextual. Para gerar uma interpretação geral, habilite 'Usar IA' e clique em 'Gerar interpretação IA'."
                st.write(general)

# UI: geração IA com proteção contra cliques repetidos e preview (refatorado)
if use_ai:
    st.markdown("#### Interpretação IA Etheria")
        
    # import resiliente do serviço
    try:
        from etheria.services import generator_service
    except Exception:
        generator_service = None

    if not generator_service:
        st.info("Serviço de geração não disponível.")
    else:
        # opções do usuário
        model_choice = "gemini-2.5-flash"

        def build_chart_input(summary_obj):
            ci = {}
            ci["name"] = (
                (summary_obj.get("name") if summary_obj and isinstance(summary_obj, dict) else None)
                or st.session_state.get("chart_name") or ""
            )
            ci["summary"] = summary_obj if summary_obj and isinstance(summary_obj, dict) else None

            # extrair posições de forma segura
            positions = {}
            if summary_obj and isinstance(summary_obj, dict):
                planets_map = summary_obj.get("planets") or summary_obj.get("readings") or {}
                if isinstance(planets_map, dict):
                    for pname, pdata in planets_map.items():
                        try:
                            if isinstance(pdata, dict) and pdata.get("longitude") is not None:
                                positions[pname] = float(pdata.get("longitude"))
                            elif isinstance(pdata, (int, float)):
                                positions[pname] = float(pdata)
                        except Exception:
                            continue
            if positions:
                ci["positions"] = positions

            # datetime seguro
            try:
                ci["dt"] = summary_obj.get("datetime") if summary_obj and isinstance(summary_obj, dict) else None
            except Exception:
                ci["dt"] = None

            # opcional: manter svg já presente na UI (não será re-renderizado pelo serviço)
            if "svg" in st.session_state:
                ci["svg"] = st.session_state.get("svg")

            return ci

        # inicializar flag de geração
        if "generating" not in st.session_state:
            st.session_state["generating"] = False

        # botão e fluxo de geração
        if st.session_state["generating"]:
            st.button("Gerando... (aguarde)", disabled=True)
        else:
            if st.button("Gerar interpretação", key="gen_ai_button"):
                st.session_state["generating"] = True
                chart_input = build_chart_input(summary)

                # chamada com spinner; usar text_only=True para NÃO re-renderizar o mapa
                with st.spinner("Gerando sua interpretação personalizada com IA Etheria..."):
                    try:
                        res = generator_service.generate_analysis(
                            chart_input,
                            prefer="auto",
                            text_only=True,
                            model=model_choice
                        )
                    except Exception as e:
                        res = {
                            "svg": "",
                            "analysis_text": "",
                            "analysis_json": None,
                            "source": "none",
                            "error": str(e)
                        }

                # liberar flag
                st.session_state["generating"] = False

                # preparar label para downloads (definir antes de usar)
                try:
                    label_selected = (
                        influences.CANONICAL_TO_PT.get(canonical_selected, canonical_selected)
                        if canonical_selected else "mapa"
                    )
                except Exception:
                    label_selected = "mapa"

                # exibir resultado: priorizar erros claros
                if res.get("error") and not (res.get("analysis_text") or res.get("analysis_json")):
                    with st.expander("Detalhes do erro"):
                        st.warning("Não foi possível gerar a interpretação via serviço.")
                        st.write(res.get("error"))
                else:
                    # NÃO replotar o mapa aqui; UI já mostra o mapa
                    ai_text = res.get("analysis_text") or ""
                    parsed = res.get("analysis_json")

                    if ai_text:
                        st.success("Interpretação IA gerada")
                        st.markdown("#### Interpretação IA")
                        st.write(ai_text)
                        # download do texto
                        st.download_button(
                            "Exportar interpretação(.txt)",
                            data=ai_text,
                            file_name=f"interpretacao_ia_{label_selected}.txt",
                            mime="text/plain"
                        )

                    if parsed:
                        with st.expander("Ver JSON estruturado (expandir)"):
                            st.json(parsed)
                            st.download_button(
                                "Baixar JSON",
                                data=json.dumps(parsed, ensure_ascii=False, indent=2),
                                file_name=f"interpretacao_ia_{label_selected}.json",
                                mime="application/json"
                            )

                    # se não houve texto nem JSON, mostrar aviso ou info
                    if not ai_text and not parsed:
                        if res.get("error"):
                            st.warning("Geração concluída com problemas: " + str(res.get("error")))
                        else:
                            st.info("Geração concluída, mas não houve texto de interpretação. Verifique configuração de IA ou use templates locais.")


# RIGHT: painel de análise e numerologia
with right_col:
    st.subheader("Painel de Análise")
    tabs = st.tabs(["Interpretação via Arcanos"])

    with tabs[0]:
        selected_raw = st.session_state.get("selected_planet")
        canonical_selected, label_selected = _canonical_and_label(selected_raw) if selected_raw else (None, None)

        # preferir leitura já gerada no summary (canonical), senão usar interpretations.arcano_for_planet
        reading = summary.get("readings", {}).get(canonical_selected) if summary else None
        if reading:
            st.markdown(f"### {influences.CANONICAL_TO_PT.get(canonical_selected, canonical_selected)} em {reading.get('sign')} {reading.get('degree')}°")
            st.markdown("**Arcano Correspondente**")
            arc = reading.get("arcano_info") or reading.get("arcano")
            if arc:
                if isinstance(arc, dict):
                    arc_name = arc.get("name") or f"Arcano {arc.get('arcano') or arc.get('value')}"
                    arc_num = arc.get("arcano") or arc.get("value")
                    arc_conf = arc.get("confidence")
                    st.write(f"{arc_name} (#{arc_num}) — confiança {arc_conf}")
                else:
                    st.write(f"Arcano {arc}")
            st.markdown("**Resumo**")
            st.write(reading.get("interpretation_short"))
            with st.expander("Interpretação completa"):
                st.write(reading.get("interpretation_long"))
            st.markdown("**Sugestões práticas**")
            kw = (arc.get("keywords") if isinstance(arc, dict) else []) if arc else []
            for k in kw:
                st.write(f"- {k}")
        else:
            # gerar via interpretations.arcano_for_planet (usa rules + influences internamente)
            if canonical_selected and summary:
                arc_block = interpretations.arcano_for_planet(summary, canonical_selected)
                st.markdown(f"### {influences.CANONICAL_TO_PT.get(canonical_selected, canonical_selected)}")
                st.markdown("**Arcano Correspondente**")
                arc_obj = arc_block.get("arcano")
                if isinstance(arc_obj, dict):
                    arc_name = arc_obj.get("name") or f"Arcano {arc_obj.get('arcano') or arc_obj.get('value')}"
                    arc_num = arc_obj.get("arcano") or arc_obj.get("value")
                    st.write(f"{arc_name} (#{arc_num})")
                else:
                    st.write(f"Arcano {arc_obj}")
                st.markdown("**Interpretação do Arcano e influência na casa**")
                st.write(arc_block.get("text", ""))
            else:
                st.info("Selecione um planeta (na tabela ou na roda) para ver a análise.")