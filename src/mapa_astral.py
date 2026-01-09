# mapa_astral.py — Versão refatorada (limpa, sem debug UI)
from __future__ import annotations
import importlib
import sys
import csv
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
from datetime import datetime, date, time as dt_time, timezone

import streamlit as st

from etheria.services.api_client import fetch_natal_chart_api
from etheria.services.generator_service import generate_analysis
# import defensivo do serviço que contém a lógica de correlação e geração
try:
    from etheria.services import analysis as services_analysis
except Exception:
    try:
        # caso o módulo esteja em services/analysis.py relativo
        import services.analysis as services_analysis  # type: ignore
    except Exception:
        services_analysis = None

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional project imports (defensive)
try:
    from etheria import astrology, influences, rules, interpretations
except Exception:
    astrology = influences = rules = interpretations = None

# If there's an external natal_positions implementation, prefer it; otherwise fallback to local stub defined below
try:
    from services.swisseph_client import natal_positions as external_natal_positions  # type: ignore
except Exception:
    external_natal_positions = None

# Optional libs detection
try:
    import pytz  # type: ignore
except Exception:
    pytz = None  # type: ignore

# Plotly detection
try:
    import plotly.graph_objects as go  # type: ignore
    PLOTLY_AVAILABLE = True
except Exception:
    go = None
    PLOTLY_AVAILABLE = False

# Geocoding/timezone optional libs
try:
    from dateutil import parser as dateutil_parser  # type: ignore
    DATEUTIL_AVAILABLE = True
except Exception:
    dateutil_parser = None
    DATEUTIL_AVAILABLE = False

try:
    from timezonefinder import TimezoneFinder  # type: ignore
    TZF_AVAILABLE = True
except Exception:
    TimezoneFinder = None
    TZF_AVAILABLE = False

try:
    from geopy.geocoders import Nominatim  # type: ignore
    from geopy.extra.rate_limiter import RateLimiter  # type: ignore
    GEOPY_AVAILABLE = True
except Exception:
    Nominatim = None
    RateLimiter = None
    GEOPY_AVAILABLE = False

try:
    from geopy.geocoders import GoogleV3  # type: ignore
    GEOPY_GOOGLE_AVAILABLE = True
except Exception:
    GoogleV3 = None
    GEOPY_GOOGLE_AVAILABLE = False

# rapidfuzz optional
try:
    from rapidfuzz import process as rf_process  # type: ignore
    RAPIDFUZZ = True
except Exception:
    RAPIDFUZZ = False

# -------------------------
# Helpers: timezone, parsing, geocoding
# -------------------------
def normalize_tz_name(tz_name: Optional[str]) -> Optional[str]:
    if not tz_name:
        return None
    tz = str(tz_name).strip().replace(" ", "_")
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
        return tz
    except Exception:
        pass
    try:
        import pytz as _pytz
        if tz in getattr(_pytz, "all_timezones", []):
            return tz
    except Exception:
        pass
    try:
        from dateutil import tz as dateutil_tz
        if dateutil_tz.gettz(tz):
            return tz
    except Exception:
        pass
    return None

def make_datetime_with_tz(bdate: date, btime: dt_time, tz_name: Optional[str]) -> Optional[datetime]:
    if not bdate or not btime or not tz_name:
        return None
    dt_naive = datetime.combine(bdate, btime)
    try:
        from zoneinfo import ZoneInfo
        return dt_naive.replace(tzinfo=ZoneInfo(tz_name))
    except Exception:
        pass
    try:
        import pytz as _pytz
        tz = _pytz.timezone(tz_name)
        return tz.localize(dt_naive)
    except Exception:
        pass
    try:
        from dateutil import tz as dateutil_tz
        tz = dateutil_tz.gettz(tz_name)
        if tz:
            return dt_naive.replace(tzinfo=tz)
    except Exception:
        pass
    return None

def parse_time_string(t: Optional[str]) -> Optional[dt_time]:
    if not t or not str(t).strip():
        return None
    s = str(t).strip()
    s = " ".join(s.split())
    fmts = ["%H:%M:%S", "%H:%M", "%H.%M", "%H%M", "%H", "%I:%M %p", "%I:%M%p", "%I %p", "%I%p"]
    for f in fmts:
        try:
            dt = datetime.strptime(s, f)
            return dt.time()
        except Exception:
            continue
    if DATEUTIL_AVAILABLE:
        try:
            dt = dateutil_parser.parse(s, fuzzy=True, default=datetime(1900, 1, 1))
            return dt.time()
        except Exception:
            pass
    low = s.lower().replace(".", "").strip()
    try:
        if low.endswith("am") or low.endswith("pm"):
            ampm = low[-2:]
            num = low[:-2].strip()
            if ":" in num:
                parts = num.split(":")
                h = int(parts[0]); m = int(parts[1]) if len(parts) > 1 else 0
            elif num.isdigit():
                h = int(num); m = 0
            else:
                return None
            if ampm == "pm" and h < 12:
                h += 12
            if ampm == "am" and h == 12:
                h = 0
            if 0 <= h < 24 and 0 <= m < 60:
                return dt_time(hour=h, minute=m)
        digits = "".join(ch for ch in low if ch.isdigit())
        if digits:
            if len(digits) <= 2:
                h = int(digits); m = 0
            elif len(digits) == 3:
                h = int(digits[0]); m = int(digits[1:])
            else:
                h = int(digits[:-2]); m = int(digits[-2:])
            if 0 <= h < 24 and 0 <= m < 60:
                return dt_time(hour=h, minute=m)
    except Exception:
        pass
    return None

def tz_from_latlon_cached(lat: float, lon: float) -> Optional[str]:
    if not TZF_AVAILABLE:
        return None
    try:
        tf = TimezoneFinder()
        return tf.timezone_at(lng=lon, lat=lat)
    except Exception as e:
        logger.warning("tz_from_latlon_cached exception: %s", e)
        return None

@st.cache_data(show_spinner=False)
def geocode_place_nominatim_cached(place_text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    if not GEOPY_AVAILABLE:
        return None, None, None
    try:
        geolocator = Nominatim(user_agent="mapa_astral_app")
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
        loc = geocode(place_text, addressdetails=True, language="pt", timeout=10)
        if not loc:
            return None, None, None
        return float(loc.latitude), float(loc.longitude), loc.address
    except Exception as e:
        logger.warning("geocode_place_nominatim_cached exception: %s", e)
        return None, None, None

@st.cache_data(show_spinner=False)
def geocode_place_google_cached(place_text: str) -> Tuple[Optional[float], Optional[float], Optional[str]]:
    api_key = None
    try:
        api_key = st.secrets.get("GEOCODE_API_KEY") if hasattr(st, "secrets") else None
    except Exception:
        api_key = None
    if not api_key:
        api_key = os.environ.get("GEOCODE_API_KEY")
    if not api_key or not GEOPY_GOOGLE_AVAILABLE:
        return None, None, None
    try:
        geolocator = GoogleV3(api_key=api_key, timeout=10)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=0.2)
        loc = geocode(place_text)
        if not loc:
            return None, None, None
        return float(loc.latitude), float(loc.longitude), loc.address
    except Exception as e:
        logger.warning("geocode_place_google_cached exception: %s", e)
        return None, None, None

def geocode_place_safe(place_text: str) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
    lat, lon, addr = geocode_place_google_cached(place_text)
    if lat is not None and lon is not None:
        tz = tz_from_latlon_cached(lat, lon) or "UTC"
        return lat, lon, tz, addr
    lat, lon, addr = geocode_place_nominatim_cached(place_text)
    if lat is not None and lon is not None:
        tz = tz_from_latlon_cached(lat, lon) or "UTC"
        return lat, lon, tz, addr
    try:
        import requests
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place_text, "format": "json", "limit": 1, "addressdetails": 1}
        headers = {"User-Agent": "mapa_astral_app"}
        resp = requests.get(url, params=params, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return None, None, None, None
        item = data[0]
        lat = float(item["lat"]); lon = float(item["lon"])
        display_name = item.get("display_name", place_text)
        tz = tz_from_latlon_cached(lat, lon) or "UTC"
        return lat, lon, tz, display_name
    except Exception as e:
        logger.warning("geocode_place_safe fallback requests failed: %s", e)
        return None, None, None, None

# -------------------------
# City map loader and fuzzy autocomplete
# -------------------------
from functools import lru_cache
import difflib

@st.cache_data
def load_city_names_and_meta(csv_path: str = "data/cities.csv"):
    names = []
    meta = {}
    if not os.path.exists(csv_path):
        try:
            for k, v in globals().get("CITY_MAP", {}).items():
                names.append(k)
                meta[k] = {"lat": v.get("lat"), "lon": v.get("lon"), "tz": v.get("tz")}
        except Exception:
            return [], {}
        return names, meta

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or "").strip()
            if not name:
                continue
            names.append(name)
            try:
                lat_val = float(r["lat"]) if r.get("lat") else None
            except Exception:
                lat_val = None
            try:
                lon_val = float(r["lon"]) if r.get("lon") else None
            except Exception:
                lon_val = None
            meta[name] = {"lat": lat_val, "lon": lon_val, "tz": r.get("tz") or None}
    return names, meta

def suggest_cities(query: str, names: list, limit: int = 12):
    if not query:
        return names[:limit]
    q = query.strip()
    prefix = [n for n in names if n.lower().startswith(q.lower())]
    if prefix:
        return prefix[:limit]
    if RAPIDFUZZ:
        matches = rf_process.extract(q, names, limit=limit)
        return [m[0] for m in matches]
    else:
        return difflib.get_close_matches(q, names, n=limit, cutoff=0.45)

# -------------------------
# Safe wrappers and stubs
# -------------------------
def resolve_place_and_tz(place: str):
    lat = lon = None
    tz_name = None
    address = None
    if place:
        meta = (globals().get("CITY_MAP") or {}).get(place)
        if meta:
            lat = meta.get("lat")
            lon = meta.get("lon")
            tz_name = meta.get("tz")
        if (lat is None or lon is None or not tz_name):
            try:
                lat_g, lon_g, tz_guess, address = geocode_place_safe(place)
                lat = lat or lat_g
                lon = lon or lon_g
                tz_name = tz_name or tz_guess
            except Exception:
                pass
    return lat, lon, tz_name, address

def to_local_datetime_wrapper(bdate: date, btime_obj: dt_time, tz_name: Optional[str]) -> Tuple[Optional[datetime], Optional[str]]:
    tz_ok = normalize_tz_name(tz_name)
    if not tz_ok:
        return None, None
    dt_local = make_datetime_with_tz(bdate, btime_obj, tz_ok)
    return dt_local, tz_ok

# -------------------------
# Aspects helper
# -------------------------
_aspects_cache: Dict[str, dict] = {}

def ensure_aspects(summary_obj):
    if not summary_obj:
        return None
    if summary_obj.get("aspects"):
        return summary_obj.get("aspects")
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
            compute_fn = getattr(astrology, "compute_aspects", None) or globals().get("compute_aspects")
            if callable(compute_fn):
                aspects = compute_fn(positions, orb=6.0) if compute_fn.__code__.co_argcount >= 2 else compute_fn(positions)
                try:
                    key = str(hash(json.dumps(summary_obj, sort_keys=True, default=str)))
                    _aspects_cache[key] = aspects
                except Exception:
                    pass
                return aspects
        except Exception:
            return None
    return None

# -------------------------
# Render wheel (Plotly) - defensive
# -------------------------
def render_wheel_plotly(
    planets: dict,
    cusps: list,
    *,
    highlight_groups: dict = None,
    house_label_position: str = "inner",
    marker_scale: float = 1.0,
    text_scale: float = 1.0,
    cusp_colors_by_quadrant: list = None,
    export_png: bool = False,
    export_size: tuple = (2400, 2400)
):
    logger = logging.getLogger("render_wheel_plotly")
    if not PLOTLY_AVAILABLE:
        logger.warning("Plotly não disponível; render_wheel_plotly retornará None")
        return None
    try:
        import math
        import plotly.graph_objects as go  # reimport safe
    except Exception as e:
        logger.exception("Plotly import failed: %s", e)
        return None

    colors = globals().get("GROUP_COLORS") or {
        "Sun": "#FF8800", "Moon": "#3e54d4", "Mercury": "#e7d912",
        "Venus": "#2fbdf5", "Mars": "#d62728", "Jupiter": "#9467bd",
        "Saturn": "#53c232", "Uranus": "#ffd900", "Neptune": "#00a2ff",
        "Pluto": "#ff0000", "default": "#888888"
    }

    def _color_for_group(gname):
        if not gname:
            return colors.get("default")
        try:
            key = getattr(influences, "to_canonical", lambda x: x)(gname) or str(gname)
        except Exception:
            key = str(gname)
        return colors.get(key, colors.get("default"))

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

    def extract_meta(pdata):
        if not isinstance(pdata, dict):
            return {}
        return {
            "sign": pdata.get("sign") or pdata.get("zodiac") or pdata.get("sign_name"),
            "house": pdata.get("house") or pdata.get("casa") or pdata.get("house_number")
        }

    valid_planets = {}
    planet_meta = {}
    invalid_planets = []
    for name, pdata in (planets or {}).items():
        lon = extract_lon(pdata)
        if lon is None:
            invalid_planets.append((name, pdata))
        else:
            valid_planets[name] = float(lon) % 360.0
            planet_meta[name] = extract_meta(pdata) if isinstance(pdata, dict) else {}

    valid_cusps = []
    invalid_cusps = []
    if cusps:
        for i, c in enumerate(cusps):
            try:
                if c is None:
                    raise ValueError("None cusp")
                valid_cusps.append(float(c) % 360.0)
            except Exception:
                invalid_cusps.append((i, c))

    if invalid_planets:
        logger.warning("Planetas inválidos (sem longitude): %s", invalid_planets)
    if invalid_cusps:
        logger.warning("Cusps inválidos: %s", invalid_cusps)

    if len(valid_planets) == 0:
        logger.error("Nenhum planeta válido para desenhar. valid_planets=%s", valid_planets)
        return None

    def lon_to_theta(lon_deg: float) -> float:
        return (360.0 - float(lon_deg)) % 360.0

    planet_symbols = {
        "Sun": "☉", "Sol": "☉", "Moon": "☾", "Lua": "☾", "Mercury": "☿", "Mercúrio": "☿",
        "Venus": "♀", "Vênus": "♀", "Mars": "♂", "Marte": "♂", "Jupiter": "♃", "Júpiter": "♃",
        "Saturn": "♄", "Saturno": "♄", "Uranus": "♅", "Urano": "♅", "Neptune": "♆", "Netuno": "♆",
        "Pluto": "♇", "Plutão": "♇", "Asc": "ASC", "ASCENDANT": "ASC", "ASCENDENTE": "ASC",
        "MC": "MC", "Medium Coeli": "MC", "Meio do Céu": "MC"
    }

    groups = highlight_groups or {
        "pessoais": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
        "sociais": ["Jupiter", "Saturn"],
        "geracionais": ["Uranus", "Neptune", "Pluto"]
    }

    ordered = sorted(valid_planets.items(), key=lambda kv: kv[1])

    try:
        canonical_signs = influences.CANONICAL_SIGNS if influences and hasattr(influences, "CANONICAL_SIGNS") else getattr(influences, "SIGNS", None)
    except Exception:
        canonical_signs = None
    if not canonical_signs:
        canonical_signs = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

    sign_names = []
    for s in canonical_signs:
        try:
            sign_names.append(influences.sign_label_pt(s) or s)
        except Exception:
            sign_names.append(s)

    # símbolos dos signos (agora usados)
    sign_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]

    _normalized_groups: Dict[str, List[str]] = {}
    for gname, members in (groups or {}).items():
        members_can = []
        for m in members:
            try:
                m_can = influences.to_canonical(m) if influences and hasattr(influences, "to_canonical") else m
                members_can.append(m_can)
            except Exception:
                members_can.append(m)
        _normalized_groups[gname] = members_can

    # preparar rótulos PT dos signos
    try:
        sign_labels_pt = [influences.sign_label_pt(s) if influences and hasattr(influences, "sign_label_pt") else s for s in canonical_signs]
    except Exception:
        sign_labels_pt = canonical_signs

    # detectar signos interceptados: contar quantas cúspides caem dentro de cada signo
    sign_cusp_counts = [0] * 12
    for c in valid_cusps:
        try:
            idx = int(c // 30) % 12
            sign_cusp_counts[idx] += 1
        except Exception:
            continue
    intercepted_signs = [i for i, cnt in enumerate(sign_cusp_counts) if cnt == 0]

    # parâmetros visuais
    inner_r = 0.56          # planetas mais internos (antes 0.60)
    outer_r = 1.00
    label_r = 1.12
    # raio onde os planetas serão desenhados (mais interno que outer_r)
    planet_r = inner_r + (outer_r - inner_r) * 0.28  # ~0.64
    # rótulo das casas (um pouco mais interno para evitar sobreposição com símbolos)
    house_label_r = outer_r - 0.16 if house_label_position == "inner" else outer_r + 0.06
    cusp_r0 = inner_r
    cusp_r1 = outer_r + 0.05

    fig = go.Figure()

    base_sign_colors = ["#e7edff", "#eff9ff"]
    intercepted_fill = "rgba(255,200,200,0.25)"

    # desenhar setores de signo (refatorado)
    def draw_sign_sectors(fig, inner_r, outer_r, intercepted_signs, base_sign_colors,
                        intercepted_fill, lon_to_theta, sign_labels_pt, text_scale,
                        sign_label_r=None, steps=24):
        """
        Desenha 12 setores de signo em fig (Scatterpolar).
        - inner_r, outer_r: raios interno/externo do anel de signos
        - intercepted_signs: lista de índices (0..11) de signos interceptados
        - base_sign_colors: lista de cores alternadas
        - intercepted_fill: cor de preenchimento para interceptados
        - lon_to_theta: função que converte longitude (0..360) em theta para Plotly
        - sign_labels_pt: lista de 12 rótulos de signo em PT
        - sign_label_r: raio para posicionar rótulos de signo (se None, calculado automaticamente)
        - steps: resolução do arco (mais alto = mais suave)
        """
        if sign_label_r is None:
            sign_label_r = inner_r + (outer_r - inner_r) * 0.12  # rótulo mais para o lado interno

        for s_idx in range(12):
            sign_start = (s_idx * 30.0) % 360.0
            sign_end = (sign_start + 30.0) % 360.0
            # construir pontos do arco externo (start -> end) e interno (end -> start)
            thetas = []
            rs = []

            # arco externo do setor
            for k in range(steps + 1):
                frac = k / steps
                lon = (sign_start + frac * 30.0) % 360.0
                thetas.append(lon_to_theta(lon))
                rs.append(outer_r)

            # arco interno (volta) do setor
            for k in range(steps, -1, -1):
                frac = k / steps
                lon = (sign_start + frac * 30.0) % 360.0
                thetas.append(lon_to_theta(lon))
                rs.append(inner_r)

            # escolher cor de preenchimento
            fillcolor = intercepted_fill if s_idx in (intercepted_signs or []) else base_sign_colors[s_idx % len(base_sign_colors)]

            fig.add_trace(go.Scatterpolar(
                r=rs,
                theta=thetas,
                mode="lines",
                fill="toself",
                fillcolor=fillcolor,
                line=dict(color="rgba(0,0,0,0)"),
                hoverinfo="none",
                showlegend=False
            ))

            # rótulo do signo: centro do setor (start + 15°), posicionado mais internamente
            center_lon = (sign_start + 15.0) % 360.0
            theta_center = lon_to_theta(center_lon)
            label = sign_labels_pt[s_idx] if sign_labels_pt and len(sign_labels_pt) == 12 else f"Signo {s_idx+1}"
            fig.add_trace(go.Scatterpolar(
                r=[sign_label_r],
                theta=[theta_center],
                mode="text",
                #text=[label],
                textfont=dict(size=int(12 * text_scale), color="#222222"),
                hoverinfo="none",
                showlegend=False
            ))

    # chamada (exemplo) — ajuste variáveis conforme seu contexto
    draw_sign_sectors(
        fig=fig,
        inner_r=inner_r,
        outer_r=outer_r,
        intercepted_signs=intercepted_signs,
        base_sign_colors=base_sign_colors,
        intercepted_fill=intercepted_fill,
        lon_to_theta=lon_to_theta,
        sign_labels_pt=sign_labels_pt,  # sua lista de rótulos em PT
        text_scale=text_scale,
        sign_label_r=inner_r + (outer_r - inner_r) * 0.08,  # rótulos ainda mais internos se desejar
        steps=24
    )

    # --- REMOVIDA a demarcação por linhas de cúspide ---
    # Em vez de desenhar apenas as linhas de cusp, desenhamos setores de casa
    # (áreas entre cada cusp) e colocamos rótulos de número da casa no centro do setor.
    # Mantemos todas as demais funções e layout conforme solicitado.

    # destacar casas como setores (entre cada cusp)
    if valid_cusps and len(valid_cusps) >= 12:
        # garantir que temos 12 cusps e convertê-los para float 0..360
        raw_cusps = [float(c) % 360.0 for c in valid_cusps[:12]]

        # Se os cusps vierem fora de ordem, tentar ordenar circularmente mantendo a sequência de casas.
        # Assumimos que a lista representa casas 1..12 em ordem; se não for o caso, ordenamos por ângulo.
        # Preferimos manter a ordem original quando ela já é circular crescente.
        def is_circular_increasing(arr):
            diffs = []
            for i in range(len(arr)):
                a = arr[i]
                b = arr[(i + 1) % len(arr)]
                diffs.append((b - a) % 360.0)
            # se todos os spans forem > 0 e soma ~360, consideramos circular crescente
            return all(d > 0 for d in diffs)

        if not is_circular_increasing(raw_cusps):
            cusps_sorted = sorted(raw_cusps)
        else:
            cusps_sorted = raw_cusps

            # opções visuais para casas
            house_fill_colors = ["rgba(220,230,255,0.14)", "rgba(230,245,230,0.10)"]
            house_border_color = "rgba(80,80,80,0.18)"

            for i in range(len(cusps_sorted)):
                try:
                    start = float(cusps_sorted[i]) % 360.0 
                    end = float(cusps_sorted[(i + 1) % 12]) % 360.0
                    # calcular arco span corretamente (considerando wrap)
                    span = (end - start) % 360.0
                    # pular spans muito pequenos (evita demarcações estranhas)
                    if span < 0.5:  # threshold em graus
                        logger.debug("Pulando setor degenerado da casa %s (span muito pequeno: %s°)", i + 1, span)
                        continue

                    # construir anel (outer_r .. inner_r) para o setor da casa
                    steps = 18
                    thetas = []
                    rs = []
                    # arco externo
                    for k in range(steps + 1):
                        frac = k / steps
                        lon = (start + frac * span) % 360.0
                        thetas.append(lon_to_theta(lon))
                        rs.append(outer_r)
                    # arco interno (volta)
                    for k in range(steps, -1, -1):
                        frac = k / steps
                        lon = (start + frac * span) % 360.0
                        thetas.append(lon_to_theta(lon))
                        rs.append(inner_r)

                    # evitar desenhar borda visível entre casa 12 e 1: se i == 11 (última casa),
                    # usar linha width 0 para suavizar a junção
                    line_width = 0.6
                    if i == len(cusps_sorted) - 1:
                        line_width = 0.10

                    fillcolor = house_fill_colors[i % len(house_fill_colors)]
                    fig.add_trace(go.Scatterpolar(
                        r=rs,
                        theta=thetas,
                        mode="lines",
                        fill="toself",
                        fillcolor=fillcolor,
                        line=dict(color=house_border_color, width=line_width),
                        hoverinfo="none",
                        showlegend=False
                    ))

                    # rótulo do número da casa no meio do setor (midpoint calculado com wrap seguro)
                    mid = (start + span / 0.98) % 360.0 #label das casas um pouco deslocado para evitar sobreposição
                    theta_mid = lon_to_theta(mid)
                    house_label = str(i + 1)
                    fig.add_trace(go.Scatterpolar(
                        r=[house_label_r],
                        theta=[theta_mid],
                        mode="text",
                        text=[house_label],
                        textfont=dict(size=11 * text_scale, color="#222222"),
                        hoverinfo="none",
                        showlegend=False
                    ))
                except Exception:
                    logger.exception("Erro ao desenhar setor da casa %s", i + 1)
                    continue

    else:
        # se não houver cusps válidos, manter comportamento anterior (sem setores)
        logger.debug("Nenhum cusp válido para desenhar setores de casa: %s", valid_cusps)

    # rótulos dos signos no anel externo (com símbolo)
    for s_idx in range(12):
        try:
            sign_mid_lon = (s_idx * 30.0 + 15.0) % 360.0
            theta = lon_to_theta(sign_mid_lon)
            label = sign_labels_pt[s_idx] if s_idx < len(sign_labels_pt) else canonical_signs[s_idx]
            symbol = sign_symbols[s_idx] if s_idx < len(sign_symbols) else ""
            label_suffix = " (Int)" if s_idx in intercepted_signs else ""
            text_label = f"{symbol} {label}{label_suffix}"
            fig.add_trace(go.Scatterpolar(
                r=[label_r],
                theta=[theta],
                mode="text",
                text=[text_label],
                textfont=dict(size=12 * text_scale, color="#333333"),
                hoverinfo="none",
                showlegend=False
            ))
        except Exception:
            continue

    # adicionar planetas
    ordered = sorted(valid_planets.items(), key=lambda kv: kv[1])
    names = []
    thetas = []
    hover_texts = []
    symbol_texts = []
    lon_values = []
    marker_sizes = []
    marker_colors = []
    text_colors = []

    for name, lon in ordered:
        try:
            theta = lon_to_theta(lon)
        except Exception:
            continue
        try:
            display_planet = influences.planet_label_pt(influences.to_canonical(name)) if influences and hasattr(influences, "planet_label_pt") else name
        except Exception:
            display_planet = name
        meta = planet_meta.get(name, {}) or {}
        degree_in_sign = (lon % 30.0)
        sign_index = int(lon // 30) % 12
        sign_label = sign_labels_pt[sign_index] if 0 <= sign_index < len(sign_labels_pt) else canonical_signs[sign_index % 12]
        sign_symbol = sign_symbols[sign_index] if 0 <= sign_index < len(sign_symbols) else ""
        hover = f"<b>{display_planet}</b><br>{float(lon):.2f}° eclíptico<br>{degree_in_sign:.1f}° no signo {sign_symbol} {sign_label}"
        if meta.get("house"):
            hover += f"<br>Casa: {meta.get('house')}"
        symbol = planet_symbols.get(name) or planet_symbols.get(name.capitalize()) or (display_planet[:2] if display_planet else name)
        try:
            name_can = influences.to_canonical(name) if influences and hasattr(influences, "to_canonical") else name
            color = colors.get(name_can, colors.get("default"))
        except Exception:
            color = colors.get("default")
        size = int(max(8, 18 * marker_scale))
        names.append(display_planet)
        thetas.append(theta)
        hover_texts.append(hover)
        symbol_texts.append(symbol)
        lon_values.append(float(lon))
        marker_sizes.append(size)
        marker_colors.append(color)
        text_colors.append(color)

        # adicionar planetas (usar planet_r para posicionamento radial)
        try:
            fig.add_trace(go.Scatterpolar(
                r=[planet_r] * len(thetas),
                theta=thetas,
                mode="markers+text",
                marker=dict(size=[max(6, int(ms)) for ms in marker_sizes], color=marker_colors, line=dict(color="#222", width=1)),
                text=symbol_texts,
                textposition="middle center",
                hovertext=hover_texts,
                hoverinfo="text",
                showlegend=False
            ))
        except Exception as e:
            logger.exception("Erro ao adicionar trace de planetas: %s", e)

    try:
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=False),
                angularaxis=dict(direction="clockwise", rotation=90, showticklabels=False)
            ),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_white"
        )
    except Exception:
        pass

    if export_png:
        try:
            img_bytes = fig.to_image(format="png", width=export_size[0], height=export_size[1])
        except Exception as e:
            logger.warning("Falha ao exportar PNG: %s", e)

    return fig

# -------------------------
# Fallback implementations (mantidas conforme solicitado)
# -------------------------
# If an external natal_positions exists, use it; otherwise use the internal robust implementation below.
try:
    if external_natal_positions:
        natal_positions = external_natal_positions  # type: ignore
except Exception:
    pass

# Internal robust natal_positions (kept and used if external not available)
try:
    import swisseph as swe  # type: ignore
    _SWE_AVAILABLE = True
except Exception:
    swe = None
    _SWE_AVAILABLE = False

PLANET_IDS = {
    "Sun": getattr(swe, "SUN", 0) if _SWE_AVAILABLE else 0,
    "Moon": getattr(swe, "MOON", 1) if _SWE_AVAILABLE else 1,
    "Mercury": getattr(swe, "MERCURY", 2) if _SWE_AVAILABLE else 2,
    "Venus": getattr(swe, "VENUS", 3) if _SWE_AVAILABLE else 3,
    "Mars": getattr(swe, "MARS", 4) if _SWE_AVAILABLE else 4,
    "Jupiter": getattr(swe, "JUPITER", 5) if _SWE_AVAILABLE else 5,
    "Saturn": getattr(swe, "SATURN", 6) if _SWE_AVAILABLE else 6,
    "Uranus": getattr(swe, "URANUS", 7) if _SWE_AVAILABLE else 7,
    "Neptune": getattr(swe, "NEPTUNE", 8) if _SWE_AVAILABLE else 8,
    "Pluto": getattr(swe, "PLUTO", 9) if _SWE_AVAILABLE else 9
}

def natal_positions_internal(dt_local, lat, lon, house_system="P"):
    """
    Internal implementation using swisseph. Returns consistent dict:
      {"planets": {...}, "cusps": [...], "jd_ut": ...}
    """
    if not _SWE_AVAILABLE:
        return {"planets": {}, "cusps": [], "error": "swisseph not available"}
    try:
        if dt_local is None:
            raise ValueError("dt_local is None")
        if dt_local.tzinfo is None:
            dt_utc = dt_local.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt_local.astimezone(timezone.utc)
        hour_decimal = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3_600_000_000.0
        jd_ut = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hour_decimal)

        planets = {}
        for name, pid in PLANET_IDS.items():
            try:
                res, flag = swe.calc_ut(jd_ut, pid)
                planets[name] = {
                    "longitude": float(res[0]) if len(res) > 0 else None,
                    "latitude": float(res[1]) if len(res) > 1 else None,
                    "distance": float(res[2]) if len(res) > 2 else None,
                    "speed_long": float(res[3]) if len(res) > 3 else None,
                    "raw": list(res) if hasattr(res, "__iter__") else res,
                    "flag": flag
                }
            except Exception as e:
                logger.exception("Erro ao calcular planeta %s: %s", name, e)
                planets[name] = {"error": str(e)}

        cusps = []
        try:
            cusps_res, ascmc = swe.houses(jd_ut, float(lat), float(lon), house_system)
            cusps = [float(c) for c in cusps_res] if cusps_res else []
        except Exception as e:
            logger.exception("Erro ao calcular casas/cusps: %s", e)
            # fallback attempt with Placidus
            try:
                if house_system != "P":
                    cusps_res, ascmc = swe.houses(jd_ut, float(lat), float(lon), "P")
                    cusps = [float(c) for c in cusps_res] if cusps_res else []
            except Exception:
                cusps = []

        return {"planets": planets, "cusps": cusps, "jd_ut": jd_ut}
    except Exception as e:
        logger.exception("Erro em natal_positions_internal: %s", e)
        return {"planets": {}, "cusps": [], "error": str(e)}

# Ensure natal_positions points to a working implementation
if not callable(globals().get("natal_positions")) or globals().get("natal_positions") is None:
    natal_positions = natal_positions_internal
else:
    # if natal_positions was defined earlier as stub, replace with internal if swisseph available
    try:
        if globals().get("natal_positions") in (None, fetch_natal_chart_api):
            natal_positions = natal_positions_internal
    except Exception:
        natal_positions = natal_positions_internal

# -------------------------
# Utility: convert planets dict to table rows and longitudes
# -------------------------
def planets_to_table_and_longitudes(planets_dict: Dict[str, Any]):
    table_rows = []
    longitudes = []
    sign_names = ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]
    for name, info in (planets_dict or {}).items():
        if not isinstance(info, dict) or info.get("error"):
            continue
        lon = info.get("longitude")
        lat = info.get("latitude")
        speed = info.get("speed_long") or info.get("speed")
        if lon is None:
            continue
        try:
            lon = float(lon) % 360.0
        except Exception:
            continue
        longitudes.append(lon)
        deg = int(lon)
        minute = int((lon - deg) * 60)
        sign_index = (deg // 30) % 12
        sign = sign_names[sign_index]
        row = {
            "planet": name,
            "longitude": lon,
            "latitude": lat,
            "degree": deg % 30,
            "minute": minute,
            "sign": sign,
            "speed": speed
        }
        table_rows.append(row)
    return table_rows, longitudes

# -------------------------
# Safe stubs for other functions (kept as requested)
# -------------------------
def fetch_natal_chart(name, dt_local, lat, lon, tz_name):
    return {"planets": {}, "cusps": []}

def positions_table(planets):
    # default conversion if no project-specific implementation
    if callable(globals().get("positions_table")) and globals().get("positions_table") is not positions_table:
        return globals().get("positions_table")(planets)
    table_rows, _ = planets_to_table_and_longitudes(planets)
    return table_rows

def compute_aspects(planets):
    compute_fn = getattr(astrology, "compute_aspects", None) or globals().get("compute_aspects")
    if callable(compute_fn):
        try:
            return compute_fn(planets)
        except Exception:
            logger.exception("compute_aspects failed")
            return []
    return []

def generate_chart_summary(planets, name, bdate):
    return {"planets": planets}

def enrich_summary_with_astrology(summary):
    return summary

def find_or_generate_and_save_reading(summary: dict, selected_raw: str) -> tuple:
    """
    Busca uma leitura existente em summary['readings'] para selected_raw.
    Se não existir, tenta gerar uma leitura robusta (arcano do planeta, texto e keywords),
    persiste em summary['readings'] e atualiza st.session_state['map_summary'].

    Retorna uma tupla (reading_dict, save_key) quando bem-sucedido, ou (None, None).
    """
    try:
        logger = logging.getLogger("find_or_generate_and_save_reading")
    except Exception:
        logger = None

    if not summary or not selected_raw:
        return None, None

    # helpers internos
    def _safe_key_variants(name):
        """Retorna lista de chaves candidatas: canônico, raw, lower-case raw."""
        keys = []
        try:
            if influences and hasattr(influences, "to_canonical"):
                can = influences.to_canonical(name)
                if can:
                    keys.append(can)
        except Exception:
            pass
        try:
            keys.append(name)
        except Exception:
            pass
        try:
            keys.append(str(name).lower())
        except Exception:
            pass
        return [k for k in keys if k is not None]

    def _find_reading(summary_obj, name):
        readings = (summary_obj.get("readings") or {}) if isinstance(summary_obj, dict) else {}
        if not isinstance(readings, dict):
            return None, None
        # tentar variantes diretas
        for cand in _safe_key_variants(name):
            if cand in readings:
                return cand, readings[cand]
        # busca case-insensitive entre chaves existentes
        for k, v in readings.items():
            try:
                if str(k).lower() == str(name).lower():
                    return k, v
            except Exception:
                continue
        # procurar por campo planet/name dentro das leituras
        for k, v in readings.items():
            try:
                if isinstance(v, dict):
                    p = (v.get("planet") or v.get("name") or "")
                    if p and str(p).lower() == str(name).lower():
                        return k, v
            except Exception:
                continue
        return None, None

    # 1) procurar leitura existente
    try:
        key_found, reading = _find_reading(summary, selected_raw)
        if reading:
            return reading, key_found
    except Exception:
        if logger:
            logger.exception("Erro ao procurar leitura existente")

    # 2) tentar gerar e normalizar leitura (fallbacks defensivos)
    generated = {}
    arc_info = None
    try:
        # extrair dados posicionais básicos (longitude, sign, degree, house) do summary
        planet_lon = None
        sign = None
        degree = None
        house = None
        try:
            # procurar na tabela primeiro
            for row in (summary.get("table") or []):
                try:
                    pname = (row.get("planet") or row.get("name") or "").strip()
                    if pname and str(pname).lower() == str(selected_raw).lower():
                        planet_lon = row.get("longitude") or row.get("lon") or row.get("degree") or row.get("deg")
                        sign = row.get("sign") or row.get("zodiac")
                        degree = row.get("degree") or row.get("deg")
                        house = row.get("house")
                        break
                except Exception:
                    continue
        except Exception:
            pass

        # fallback para summary['planets']
        if planet_lon is None:
            try:
                pmap = summary.get("planets") or {}
                for k, v in pmap.items():
                    if str(k).lower() == str(selected_raw).lower():
                        if isinstance(v, dict):
                            planet_lon = v.get("longitude") or v.get("lon") or v.get("long")
                            sign = sign or v.get("sign") or v.get("zodiac") or v.get("sign_name")
                            degree = degree or v.get("degree") or v.get("deg")
                            house = house or v.get("house") or v.get("casa")
                        else:
                            try:
                                planet_lon = float(v)
                            except Exception:
                                planet_lon = None
                        break
            except Exception:
                pass

        # 2a) tentar obter arcano via interpretations.safe_arcano_for_planet (wrapper defensivo)
        try:
            if 'interpretations' in globals() and interpretations and hasattr(interpretations, "safe_arcano_for_planet"):
                arc_info = interpretations.safe_arcano_for_planet(summary, selected_raw) or {}
        except Exception:
            arc_info = None

        # 2b) se não houver arc_info suficiente, tentar services_analysis.generate_planet_reading
        if (not arc_info or not isinstance(arc_info, dict) or (not arc_info.get("arcano") and not arc_info.get("text"))):
            try:
                if 'services_analysis' in globals() and services_analysis and hasattr(services_analysis, "generate_planet_reading") and planet_lon is not None:
                    # extrair nome e birthdate para numerology
                    person_name = (summary.get("name") or "Consulente") if isinstance(summary, dict) else "Consulente"
                    bdate = summary.get("birthdate") or summary.get("bdate") or summary.get("date")
                    # tentar normalizar bdate para date
                    from datetime import date as _date
                    if not isinstance(bdate, _date):
                        try:
                            import dateutil.parser as _dp
                            bdate = _dp.parse(str(bdate)).date()
                        except Exception:
                            bdate = _date.today()
                    sa_reading = services_analysis.generate_planet_reading(selected_raw, float(planet_lon), person_name, bdate)
                    if isinstance(sa_reading, dict):
                        # services_analysis coloca arcano em sa_reading['arcano'] (dict) e texto em interpretation_long
                        arc_info = sa_reading.get("arcano") or sa_reading.get("arcano_info") or sa_reading.get("arcano") or {}
                        # garantir interpretation_long/short se fornecidos
                        if sa_reading.get("interpretation_long"):
                            generated["interpretation_long"] = sa_reading.get("interpretation_long")
                        if sa_reading.get("interpretation_short"):
                            generated["interpretation_short"] = sa_reading.get("interpretation_short")
                        # extrair keywords se houver
                        kw = None
                        if isinstance(arc_info, dict):
                            kw = arc_info.get("keywords") or arc_info.get("tags") or arc_info.get("practical")
                        if not kw:
                            kw = sa_reading.get("arcano", {}).get("keywords") if isinstance(sa_reading.get("arcano"), dict) else None
                        if kw:
                            generated["suggestions"] = kw
            except Exception:
                # não falhar a geração por causa deste serviço
                if logger:
                    logger.debug("services_analysis.generate_planet_reading falhou ou indisponível", exc_info=True)

        # 2c) fallback: se ainda nada, tentar interpretations.arcano_for_planet
        if (not arc_info or not isinstance(arc_info, dict) or (not arc_info.get("arcano") and not arc_info.get("text"))):
            try:
                if 'interpretations' in globals() and interpretations and hasattr(interpretations, "arcano_for_planet"):
                    arc_info = interpretations.arcano_for_planet(summary, selected_raw) or {}
            except Exception:
                arc_info = arc_info or {}

        # 2d) se ainda nada e houver signo, tentar arcano por signo
        if (not arc_info or not isinstance(arc_info, dict) or (not arc_info.get("arcano") and not arc_info.get("text"))) and sign:
            try:
                if 'interpretations' in globals() and interpretations and hasattr(interpretations, "arcano_for_sign"):
                    arc_sign = interpretations.arcano_for_sign(sign, name=summary.get("name"))
                    if arc_sign and not arc_sign.get("error"):
                        # arc_sign tem keys: arcano, text, template_key...
                        arc_info = {
                            "arcano": arc_sign.get("arcano"),
                            "name": None,
                            "text": arc_sign.get("text") or arc_sign.get("long") or arc_sign.get("short") or "",
                            "keywords": []
                        }
            except Exception:
                pass

        # 2e) fallback posicional via astrology.interpret_planet_position
        if (not arc_info or not isinstance(arc_info, dict) or (not arc_info.get("arcano") and not arc_info.get("text"))) and astrology and hasattr(astrology, "interpret_planet_position"):
            try:
                interp = astrology.interpret_planet_position(
                    planet=_safe_key_variants(selected_raw)[0] if _safe_key_variants(selected_raw) else selected_raw,
                    sign=sign,
                    degree=degree,
                    house=house,
                    aspects=summary.get("aspects"),
                    context_name=summary.get("name")
                ) or {}
                if interp:
                    # interp pode ter 'short'/'long'
                    generated["interpretation_short"] = generated.get("interpretation_short") or interp.get("short") or ""
                    generated["interpretation_long"] = generated.get("interpretation_long") or interp.get("long") or interp.get("text") or ""
            except Exception:
                if logger:
                    logger.debug("astrology.interpret_planet_position falhou", exc_info=True)

        # 3) normalizar arc_info e popular generated
        if isinstance(arc_info, dict) and arc_info:
            arc_num = arc_info.get("arcano") or arc_info.get("value") or arc_info.get("id")
            arc_name = arc_info.get("name") or (f"Arcano {arc_num}" if arc_num is not None else None)
            arc_text = arc_info.get("text") or arc_info.get("interpretation") or arc_info.get("description") or ""
            arc_keywords = arc_info.get("keywords") or arc_info.get("tags") or arc_info.get("practical") or []

            generated["planet"] = selected_raw
            if sign:
                generated["sign"] = sign
            if degree is not None:
                generated["degree"] = degree
            if house is not None:
                generated["house"] = house

            generated["arcano_planeta"] = {
                "arcano": str(arc_num) if arc_num is not None else None,
                "name": arc_name,
                "text": arc_text,
                "keywords": arc_keywords,
                "confidence": arc_info.get("confidence")
            }
            # campo simples para compatibilidade
            try:
                if arc_num is not None:
                    generated["arcano"] = int(arc_num) if str(arc_num).isdigit() else str(arc_num)
            except Exception:
                generated["arcano"] = arc_num
            # persistir sugestões práticas extraídas do arcano
            if arc_keywords and not generated.get("suggestions"):
                generated["suggestions"] = arc_keywords

        # 4) se ainda não houver interpretation_long, tentar gerar via interpretations.generate_interpretation
        if not generated.get("interpretation_long"):
            try:
                if ('interpretations' in globals()) and interpretations and hasattr(interpretations, "generate_interpretation"):
                    arc_key = None
                    if isinstance(generated.get("arcano_planeta"), dict):
                        arc_key = generated["arcano_planeta"].get("arcano") or generated["arcano_planeta"].get("value")
                    elif generated.get("arcano"):
                        arc_key = generated.get("arcano")
                    gen_text = interpretations.generate_interpretation(generated, arcano_key=arc_key, length="long")
                    if gen_text:
                        generated["interpretation_long"] = gen_text
            except Exception:
                if logger:
                    logger.debug("interpretations.generate_interpretation falhou", exc_info=True)

        # 5) heurística de sugestões se ainda não houver
        if not generated.get("suggestions"):
            try:
                txt = (generated.get("arcano_planeta", {}).get("text") or generated.get("interpretation_long") or "")
                if txt:
                    words = [w.strip(".,;:()[]") for w in txt.split() if len(w) > 4]
                    seen = []
                    for w in words:
                        lw = w.lower()
                        if lw not in seen:
                            seen.append(lw)
                        if len(seen) >= 6:
                            break
                    if seen:
                        generated["suggestions"] = seen
            except Exception:
                if logger:
                    logger.debug("Heurística de sugestões falhou", exc_info=True)

    except Exception:
        if logger:
            logger.exception("Erro geral ao tentar gerar leitura fallback")

    # 3) persistir se gerado (normalizar chave e salvar)
    if generated:
        try:
            readings = summary.get("readings") or {}
            if not isinstance(readings, dict):
                readings = {}
            # escolher chave para salvar: canônico se possível, senão raw
            save_key = None
            try:
                if influences and hasattr(influences, "to_canonical"):
                    can = influences.to_canonical(selected_raw)
                    if can:
                        save_key = can
            except Exception:
                save_key = None
            if not save_key:
                save_key = selected_raw

            # garantir campos mínimos
            generated.setdefault("planet", selected_raw)
            generated.setdefault("interpretation_short", generated.get("interpretation_short") or "")
            generated.setdefault("interpretation_long", generated.get("interpretation_long") or "")
            # persistir
            readings[save_key] = generated
            # também manter sob selected_raw para compatibilidade
            try:
                readings[selected_raw] = generated
            except Exception:
                pass
            summary["readings"] = readings

            # atualizar session_state para UI
            try:
                st.session_state["map_summary"] = summary
            except Exception:
                if logger:
                    logger.exception("Falha ao atualizar st.session_state['map_summary'] após salvar leitura")

            if logger:
                logger.debug("Leitura gerada e salva para %s (save_key=%s)", selected_raw, save_key)
            return generated, save_key
        except Exception:
            if logger:
                logger.exception("Falha ao persistir leitura gerada")
            return generated, None

    # nada encontrado nem gerado
    return None, None

def normalize_degree_sign(reading):
    raise NotImplementedError

def resolve_house(reading, summary, canonical, sel_planet):
    raise NotImplementedError

# -------------------------
# Main UI flow (refatorado, sem debug UI)
# -------------------------
def main():
    # session defaults
    st.session_state.setdefault("house_system", "P")
    st.session_state.setdefault("map_ready", False)
    st.session_state.setdefault("map_summary", None)
    st.session_state.setdefault("map_fig", None)
    st.session_state.setdefault("selected_planet", None)
    st.session_state.setdefault("use_ai", False)

    PAGE_ID = "mapa_astral"
    st.sidebar.header("Entrada do Consulente")

    # carregar nomes (cached) - mover para fora do form para não interromper renderização
    try:
        CITY_NAMES, CITY_META = load_city_names_and_meta("data/cities.csv")
    except Exception as e:
        logger.exception("Erro ao carregar cities.csv: %s", e)
        CITY_NAMES, CITY_META = [], {}

    # Formulário lateral (apenas selectbox para Local de nascimento + campo Nome do consulente)
    with st.sidebar:
        form_key = f"birth_form_sidebar_{PAGE_ID}"
        with st.form(key=form_key, clear_on_submit=False):
            # Selectbox único para Local de Nascimento (query implícita; sem campo de digitação)
            default_place = st.session_state.get("place_input", "")
            options = CITY_NAMES or []
            if default_place and default_place not in options:
                options = [default_place] + options

            if not options:
                options = ["Nenhuma correspondência"]

            place_selected = st.selectbox("Local de Nascimento", options, index=0, key="place_selectbox")
            place = (place_selected or "").strip()
            if place == "Nenhuma correspondência":
                place = ""

            # manter valor anterior se nada selecionado
            if not place:
                place = st.session_state.get("place_input", "")

            # Extrair meta se existir
            meta = CITY_META.get(place) or (globals().get("CITY_MAP") or {}).get(place) or {}
            lat = meta.get("lat")
            lon = meta.get("lon")
            tz_name = meta.get("tz")

            # Campo para Nome do consulente
            consulente_name = st.text_input("Nome do consulente", value=st.session_state.get("name", ""), key="name_input")

            source = "swisseph"
            st.session_state["source"] = source
            # Campos para Data e Hora de nascimento
            bdate = st.date_input(
                "Data de nascimento",
                value=st.session_state.get("bdate", date(1990, 1, 1)),
                min_value=date(1900, 1, 1),
                max_value=date(2100, 12, 31)
            )
            btime_free = st.text_input("Hora de nascimento (ex.: 14:30)", value=st.session_state.get("btime_text", ""))
            st.session_state["house_system"] = st.session_state.get("house_system", "P")
            #use_ai = st.checkbox("Usar IA para interpretações?", value=st.session_state.get("use_ai", False))
            #st.session_state["use_ai"] = use_ai
            submitted = st.form_submit_button("Gerar Mapa")

    # --- tratamento do submit ---
    if submitted:
        st.session_state["place_input"] = place
        st.session_state["name"] = st.session_state.get("name_input", "")  # ou consulente_name se usar variável local
        st.session_state["bdate"] = bdate
        st.session_state["btime_text"] = btime_free
        st.session_state["source"] = source
        #st.session_state["use_ai"] = use_ai

        parsed_time = parse_time_string(btime_free or st.session_state.get("btime_text", ""))
        if parsed_time is None:
            st.error("Hora de nascimento inválida ou não informada. Use formatos como '14:30' ou '2:30 PM'.")
            st.session_state["map_ready"] = False
            return
        btime = parsed_time

        meta = CITY_META.get(place) or (globals().get("CITY_MAP") or {}).get(place) or {}
        lat = meta.get("lat")
        lon = meta.get("lon")
        tz_name = meta.get("tz")

        if (lat is None or lon is None) and place:
            try:
                lat_res, lon_res, tz_guess, address = resolve_place_and_tz(place)
            except Exception as e:
                logger.exception("Erro em resolve_place_and_tz: %s", e)
                lat_res = lon_res = tz_guess = address = None
            lat = lat or lat_res
            lon = lon or lon_res
            tz_name = tz_name or tz_guess
            if address:
                st.session_state["address"] = address

        try:
            lat = float(lat) if lat is not None else None
            lon = float(lon) if lon is not None else None
        except Exception:
            lat = None
            lon = None

        st.session_state.update({"lat": lat, "lon": lon, "tz_name": tz_name})

        if lat is None or lon is None:
            st.warning("Latitude/Longitude não resolvidas automaticamente. Informe um local diferente ou corrija o nome da cidade.")
            st.session_state["map_ready"] = False
            return
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            st.error("Latitude/Longitude inválidas. Corrija os valores antes de gerar o mapa.")
            st.session_state["map_ready"] = False
            return

        dt_local, tz_ok = to_local_datetime_wrapper(bdate, btime, tz_name)
        if dt_local is None:
            tz_from_coords = tz_from_latlon_cached(lat, lon)
            tz_ok = normalize_tz_name(tz_from_coords) or tz_ok or normalize_tz_name(tz_name)
            if tz_ok:
                dt_local = make_datetime_with_tz(bdate, btime, tz_ok)

        st.session_state["tz_name"] = tz_ok
        st.session_state["dt_local"] = dt_local

        if dt_local is None:
            st.error("Não foi possível criar um datetime timezone-aware. Informe o timezone manualmente (IANA) no campo de local ou corrija o nome da cidade.")
            st.session_state["map_ready"] = False
            return

        #st.success(f"Datetime local: {dt_local.isoformat()} (tz: {tz_ok})")

        # --- chamar natal_positions de forma defensiva ---
        planets = {}
        cusps = []
        logger.info("Iniciando obtenção de posições natales; source=%s", source)
        logger.info("Entrada para cálculo: place=%r, dt_local=%r, lat=%r, lon=%r, tz=%r", place, dt_local, lat, lon, tz_ok)

        try:
            data = natal_positions(dt_local, lat, lon, house_system=st.session_state.get("house_system", "P"))
            if isinstance(data, dict):
                planets = data.get("planets", {}) or {}
                cusps = data.get("cusps", []) or []
            elif isinstance(data, (list, tuple)) and len(data) >= 1:
                planets = data[0] or {}
                cusps = data[1] if len(data) > 1 else []
            else:
                logger.warning("natal_positions retornou tipo inesperado: %s", type(data))
        except Exception as e:
            logger.exception("Erro ao obter posições natales: %s", e)
            st.error("Erro ao calcular posições natales. Verifique os logs do servidor.")
            st.session_state["map_ready"] = False
            return

        if not planets:
            st.warning("Não foi possível obter posições natales. Verifique as entradas e tente novamente.")
            st.session_state["map_ready"] = False
            return

        try:
            table = positions_table(planets) if callable(globals().get("positions_table")) else planets_to_table_and_longitudes(planets)[0]
            aspects = compute_aspects(planets) if callable(globals().get("compute_aspects")) else []
            summary = generate_chart_summary(planets, st.session_state.get("name") or "Consulente", bdate) if callable(globals().get("generate_chart_summary")) else {"planets": planets}
            summary["table"] = table
            summary["cusps"] = cusps
            summary["aspects"] = aspects
            summary.setdefault("place", place)
            summary.setdefault("bdate", bdate)
            summary.setdefault("btime", btime)
            summary.setdefault("lat", lat)
            summary.setdefault("lon", lon)
            summary.setdefault("timezone", tz_ok)
            summary = enrich_summary_with_astrology(summary) if callable(globals().get("enrich_summary_with_astrology")) else summary

            _, longitudes = planets_to_table_and_longitudes(planets)
            fig = None
            if callable(globals().get("render_wheel_plotly")):
                try:
                    fig = render_wheel_plotly(summary.get("planets", {}), cusps or [], marker_scale=1.0, text_scale=1.0)
                except Exception:
                    logger.exception("Erro ao renderizar figura com cusps; tentando com longitudes")
                    try:
                        fig = render_wheel_plotly(summary.get("planets", {}), [], marker_scale=1.0, text_scale=1.0)
                    except Exception:
                        logger.exception("Render fallback também falhou")
                        fig = None

            # -------------------------
            # Patch: gerar table com casas de forma unificada e persistir em summary
            # -------------------------
            # Compatibilidade: garantir que _normalize_cusps exista
            def _normalize_cusps(cusps_raw):
                """
                Wrapper compatível para normalizar cusps.
                Se existir _normalize_cusps_for_positions, delega para ela; caso contrário,
                aplica a normalização mínima (aceita 12 ou 13 valores e retorna 12 floats).
                """
                try:
                    # delegar se a função mais explícita existir
                    if "_normalize_cusps_for_positions" in globals() and callable(globals().get("_normalize_cusps_for_positions")):
                        return globals().get("_normalize_cusps_for_positions")(cusps_raw)
                    # fallback local: aceitar 12 ou 13 valores (remover índice 0 se houver 13)
                    if not cusps_raw:
                        return []
                    cusps = list(cusps_raw)
                    if len(cusps) == 13:
                        cusps = cusps[1:13]
                    if len(cusps) < 12:
                        return []
                    return [float(c) % 360.0 for c in cusps[:12]]
                except Exception:
                    logger.exception("Falha em _normalize_cusps; retornando lista vazia")
                    return []

            # -------------------------
            # Helpers de normalização (reutilizáveis)
            # -------------------------
            def _normalize_cusps_for_positions(cusps_raw):
                """
                Normaliza cusps para lista de 12 floats (0..360).
                - aceita listas com 12 ou 13 elementos (remove índice 0 se houver 13)
                - retorna [] se não for possível normalizar
                """
                try:
                    if not cusps_raw:
                        return []
                    cusps = list(cusps_raw)
                    # remover placeholder comum (índice 0) quando houver 13 valores
                    if len(cusps) == 13:
                        cusps = cusps[1:13]
                    # garantir pelo menos 12 valores
                    if len(cusps) < 12:
                        return []
                    cusps = cusps[:12]
                    out = []
                    for c in cusps:
                        out.append(float(c) % 360.0)
                    return out
                except Exception:
                    logger.exception("Falha em _normalize_cusps_for_positions")
                    return []

            def _normalize_house_index(h):
                """
                Normaliza índice de casa para 1..12.
                - aceita int/float/str
                - mapeia 13 -> 1, 0 -> 12, valores fora do intervalo são normalizados via módulo
                - retorna None se inválido
                """
                try:
                    if h is None:
                        return None
                    hi = int(float(h))
                    return ((hi - 1) % 12) + 1
                except Exception:
                    return None

            def _normalize_lon(val):
                try:
                    if val is None:
                        return None
                    return float(val) % 360.0
                except Exception:
                    return None

            # -------------------------
            # Patch: gerar table com casas de forma unificada e persistir em summary
            # -------------------------
            # normalizar cusps (aceita 12 ou 13 elementos)
            raw_cusps = summary.get("cusps", []) if isinstance(summary, dict) else []
            norm_cusps = _normalize_cusps_for_positions(raw_cusps)
            # opcional: sobrescrever summary['cusps'] com a versão normalizada para consistência
            if isinstance(summary, dict):
                try:
                    summary["cusps"] = norm_cusps
                except Exception:
                    pass

            # gerar tabela usando astrology.positions_table quando disponível
            table = None
            try:
                if astrology and hasattr(astrology, "positions_table"):
                    # positions_table aceita cusps e já tenta calcular house quando compute_house_if_missing=True
                    table = astrology.positions_table(summary.get("planets", {}) or {}, cusps=norm_cusps, compute_house_if_missing=True)
                else:
                    # fallback: usar função local planets_to_table_and_longitudes e aplicar casas manualmente
                    table = planets_to_table_and_longitudes(summary.get("planets", {}) or {})[0]
                    if norm_cusps:
                        # preferir get_house_for_longitude do módulo astrology, senão usar global
                        get_house_fn = None
                        try:
                            if hasattr(astrology, "get_house_for_longitude"):
                                get_house_fn = getattr(astrology, "get_house_for_longitude")
                        except Exception:
                            get_house_fn = None
                        if not get_house_fn and "get_house_for_longitude" in globals():
                            get_house_fn = globals().get("get_house_for_longitude")

                        for r in table:
                            try:
                                lon = None
                                if isinstance(r, dict):
                                    for k in ("longitude", "lon", "long", "ecl_lon", "ecliptic_longitude", "deg", "degree"):
                                        if r.get(k) not in (None, ""):
                                            lon = r.get(k)
                                            break
                                lon_norm = _normalize_lon(lon)
                                if lon_norm is not None and get_house_fn:
                                    h_raw = get_house_fn(lon_norm, norm_cusps)
                                    r["house"] = _normalize_house_index(h_raw)
                                else:
                                    r.setdefault("house", None)
                            except Exception:
                                logger.exception("Erro ao calcular casa para linha da tabela: %s", r)
            except Exception:
                logger.exception("Erro ao gerar tabela de posições com casas; usando fallback simples")
                try:
                    table = planets_to_table_and_longitudes(summary.get("planets", {}) or {})[0]
                except Exception:
                    table = summary.get("table", []) or []

            # garantir formato consistente e renomeações mínimas
            try:
                if isinstance(table, list):
                    normalized_table = []
                    for r in table:
                        if not isinstance(r, dict):
                            normalized_table.append({"planet": str(r)})
                            continue
                        # garantir longitude numérica
                        if r.get("longitude") is None:
                            for k in ("lon", "long", "deg", "degree"):
                                if r.get(k) not in (None, ""):
                                    try:
                                        r["longitude"] = float(r.get(k))
                                        break
                                    except Exception:
                                        continue
                        # normalizar house para 1..12 ou None
                        if "house" in r and r["house"] not in (None, ""):
                            try:
                                r["house"] = _normalize_house_index(r["house"])
                            except Exception:
                                r["house"] = None
                        else:
                            r.setdefault("house", None)
                        normalized_table.append(r)
                    table = normalized_table
            except Exception:
                logger.exception("Erro ao normalizar table rows")

            # atualizar summary com a tabela e propagar casas para summary['planets']
            summary["table"] = table

            def _apply_house_to_planets_from_table(summary_obj, table_rows):
                """Propaga house calculada na tabela para summary['planets'] quando possível."""
                try:
                    planets_map = summary_obj.get("planets", {}) or {}
                    for row in table_rows:
                        try:
                            if not isinstance(row, dict):
                                continue
                            pname = row.get("planet")
                            if not pname:
                                continue
                            h = row.get("house")
                            if h is None:
                                continue
                            if pname in planets_map and isinstance(planets_map[pname], dict):
                                planets_map[pname]["house"] = int(h)
                        except Exception:
                            logger.exception("Erro ao processar linha para propagar casa: %s", row)
                            continue
                    summary_obj["planets"] = planets_map
                except Exception:
                    logger.exception("Erro ao propagar casas para summary['planets']")
                return summary_obj

            summary = _apply_house_to_planets_from_table(summary, table)

            # persistir summary atualizado para que a UI veja as casas imediatamente
            try:
                st.session_state["map_summary"] = summary
            except Exception:
                logger.exception("Falha ao persistir map_summary após cálculo de casas")

            def _house_for_longitude(lon_deg: float, cusps: List[float]) -> Optional[int]:
                """
                Retorna número da casa (1..12) para uma longitude e lista de cusps normalizada.
                """
                try:
                    if not cusps:
                        return None
                    lon = float(lon_deg) % 360.0
                    # percorre intervalos [cusps[i], cusps[i+1])
                    for i in range(12):
                        start = cusps[i]
                        end = cusps[(i + 1) % 12]
                        if start <= end:
                            if start <= lon < end:
                                return i + 1
                        else:
                            # wrap-around (ex.: start=300, end=30)
                            if lon >= start or lon < end:
                                return i + 1
                    return None
                except Exception:
                    logger.exception("Erro em _house_for_longitude")
                    return None

            # aplicar ao summary.table (se existir) e também enriquecer cada linha
            cusps_norm = _normalize_cusps(summary.get("cusps", []) or [])
            if cusps_norm:
                try:
                    table_rows = summary.get("table", []) or []
                    # se table_rows for lista de dicts com 'longitude', calcular casa
                    updated_rows = []
                    for row in table_rows:
                        try:
                            # suportar várias chaves possíveis para longitude
                            lon = None
                            for k in ("longitude", "lon", "long", "ecl_lon", "ecliptic_longitude", "deg"):
                                if isinstance(row, dict) and row.get(k) is not None:
                                    lon = row.get(k)
                                    break
                            house_num = _house_for_longitude(lon, cusps_norm) if lon is not None else None
                            # preservar formato original e adicionar/atualizar chave 'house'
                            if isinstance(row, dict):
                                new_row = dict(row)
                                new_row["house"] = int(house_num) if house_num is not None else None
                            else:
                                # se row não for dict (caso raro), criar dict mínimo
                                new_row = {"planet": str(row), "house": int(house_num) if house_num is not None else None}
                            updated_rows.append(new_row)
                        except Exception:
                            logger.exception("Erro ao processar linha da tabela para casas: %s", row)
                            updated_rows.append(row)
                    # atualizar summary.table com as casas
                    summary["table"] = updated_rows
                    # também, se summary["planets"] existir como dict, adicionar house por planeta (opcional)
                    try:
                        planets_map = summary.get("planets", {}) or {}
                        for pname, pdata in planets_map.items():
                            try:
                                lon = None
                                if isinstance(pdata, dict):
                                    for k in ("longitude", "lon", "long", "ecl_lon", "ecliptic_longitude", "deg"):
                                        if pdata.get(k) is not None:
                                            lon = pdata.get(k)
                                            break
                                if lon is not None:
                                    h = _house_for_longitude(lon, cusps_norm)
                                    if isinstance(pdata, dict):
                                        pdata["house"] = int(h) if h is not None else None
                                    planets_map[pname] = pdata
                            except Exception:
                                continue
                        summary["planets"] = planets_map
                    except Exception:
                        logger.exception("Erro ao adicionar casas em summary['planets']")
                except Exception:
                    logger.exception("Erro ao calcular casas para summary.table")
            else:
                # se não houver cusps, não alteramos a tabela; opcionalmente logar
                logger.info("Cusps ausentes ou inválidos; pulando cálculo de casas automáticas.")

            st.session_state["map_fig"] = fig
            st.session_state["map_summary"] = summary
            st.session_state["map_ready"] = True
            st.sidebar.success("Mapa gerado com sucesso!")
        except Exception as e:
            logger.exception("Erro ao gerar summary/figura: %s", e)
            st.error("Erro ao processar dados astrológicos.")
            st.session_state["map_ready"] = False

    # Render main UI (positions, map, interpretations) - refatorado e corrigido
    # -------------------------
    st.markdown("<h1 style='text-align:left'>Astrologia ♎</h1>", unsafe_allow_html=True)
    st.caption("Preencha os dados de nascimento no formulário lateral e clique em 'Gerar Mapa'.")

    # Retrieve summary and fig
    summary = st.session_state.get("map_summary")
    fig_saved = st.session_state.get("map_fig")
    map_ready = st.session_state.get("map_ready", False)

    left_col, center_col, right_col = st.columns([0.7, 2.0, 0.8])

    # Helper local: safe canonicalizer and label formatter
    def _safe_canonical(name: Optional[str]) -> Optional[str]:
        try:
            if not name:
                return None
            if influences and hasattr(influences, "_to_canonical"):
                return influences._to_canonical(name)
            return str(name)
        except Exception:
            return str(name) if name else None

    def _planet_label_for_display(p):
        try:
            if influences and hasattr(influences, "planet_label_pt") and hasattr(influences, "_to_canonical"):
                return influences.planet_label_pt(influences._to_canonical(p))
            if influences and hasattr(influences, "_to_canonical"):
                return influences._to_canonical(p) or p
            return p or "—"
        except Exception:
            return p or "—"

    def _sign_label_for_display(s):
        try:
            if not s:
                return "—"
            if influences and hasattr(influences, "sign_to_canonical") and hasattr(influences, "sign_label_pt"):
                can = influences.sign_to_canonical(s)
                return influences.sign_label_pt(can) if can else (s or "—")
            return s or "—"
        except Exception:
            return s or "—"
    
    # -------------------------
    # Helper robusto para obter/gerar leitura (usar em UI)
    # -------------------------
    def _safe_selected_variants(name: Optional[str]) -> List[str]:
        """Retorna lista de variantes a tentar: canônico, bruto, lower-case."""
        variants = []
        try:
            if not name:
                return variants
            # canônico quando possível
            try:
                can = influences._to_canonical(name) if influences and hasattr(influences, "_to_canonical") else None
            except Exception:
                can = None
            if can:
                variants.append(can)
            variants.append(name)
            # lower-case fallback
            variants.append(str(name).lower())
            # unique preserve order
            seen = set()
            out = []
            for v in variants:
                if v is None:
                    continue
                if v not in seen:
                    seen.add(v)
                    out.append(v)
            return out
        except Exception:
            return [name] if name else []

    def get_or_generate_reading(summary: Dict[str, Any], selected_raw: Optional[str]):
        try:
            if not summary or not selected_raw:
                return None, None, None

            # garantir estrutura readings
            readings = summary.get("readings", {}) or {}

            # variantes a tentar (canônico, raw, lower-case)
            variants = _safe_selected_variants(selected_raw)
            found_key = None
            found_reading = None

            # procurar leitura existente (direta e case-insensitive)
            for v in variants:
                if v in readings:
                    found_key = v
                    found_reading = readings[v]
                    break
                for k in readings.keys():
                    try:
                        if str(k).lower() == str(v).lower():
                            found_key = k
                            found_reading = readings[k]
                            break
                    except Exception:
                        continue
                if found_reading:
                    break

            if found_reading:
                canonical = variants[0] if variants else selected_raw
                label = found_reading.get("planet") or selected_raw
                return canonical, label, found_reading

            # não encontrou: tentar usar helper centralizado se existir
            try:
                if callable(globals().get("find_or_generate_and_save_reading")):
                    generated = globals().get("find_or_generate_and_save_reading")(summary, selected_raw)
                    if generated:
                        canonical = variants[0] if variants else selected_raw
                        label = generated.get("planet") or selected_raw
                        try:
                            st.session_state["map_summary"] = summary
                        except Exception:
                            logger.exception("Falha ao persistir map_summary após gerar leitura")
                        return canonical, label, generated
            except Exception:
                logger.exception("Erro ao chamar find_or_generate_and_save_reading")

            # se helper não existir ou não gerou, tentar gerar localmente:
            # 1) tentar arcano por signo via interpretations.arcano_for_sign
            generated = None
            sign_candidate = None
            try:
                # procurar signo na tabela (summary['table']) ou em summary['planets']
                for row in (summary.get("table", []) or []):
                    try:
                        if not isinstance(row, dict):
                            continue
                        pname = row.get("planet") or row.get("planet_label") or row.get("planet_label_pt")
                        if not pname:
                            continue
                        if _safe_selected_variants(pname) and _safe_selected_variants(selected_raw):
                            if _safe_selected_variants(pname)[0] == _safe_selected_variants(selected_raw)[0] or str(pname).lower() == str(selected_raw).lower():
                                sign_candidate = row.get("sign") or row.get("zodiac") or row.get("sign_label") or row.get("sign_label_pt")
                                break
                        else:
                            if str(pname).lower() == str(selected_raw).lower():
                                sign_candidate = row.get("sign") or row.get("zodiac") or row.get("sign_label") or row.get("sign_label_pt")
                                break
                    except Exception:
                        continue
                # fallback: procurar em summary['planets']
                if not sign_candidate:
                    planets_map = summary.get("planets", {}) or {}
                    key_can = _safe_selected_variants(selected_raw)[0] if _safe_selected_variants(selected_raw) else None
                    if key_can and key_can in planets_map:
                        pdata = planets_map.get(key_can) or {}
                        sign_candidate = pdata.get("sign") or pdata.get("zodiac")
            except Exception:
                logger.exception("Erro ao extrair signo candidato para geração de leitura")

            # gerar via interpretations.arcano_for_sign se disponível
            if sign_candidate and interpretations and hasattr(interpretations, "arcano_for_sign"):
                try:
                    client_name = st.session_state.get("client_name") or st.session_state.get("name") or summary.get("name")
                    arc_res = interpretations.arcano_for_sign(sign_candidate, name=client_name)
                    if isinstance(arc_res, dict) and not arc_res.get("error"):
                        generated = {
                            "planet": selected_raw,
                            "sign": sign_candidate,
                            "interpretation_short": arc_res.get("text") or arc_res.get("short") or "",
                            "interpretation_long": arc_res.get("long") or arc_res.get("text") or "",
                            "arcano_info": arc_res.get("arcano_info") or arc_res.get("arcano") or None,
                            "source": "arcano_for_sign"
                        }
                except Exception:
                    logger.exception("Erro ao gerar arcano_for_sign para %s", sign_candidate)

            # se ainda nada, usar fallback via astrology.interpret_planet_position
            if generated is None:
                try:
                    # tentar extrair sign/degree/house para passar ao interpretador
                    sign = None
                    degree = None
                    house = None
                    planets_map = summary.get("planets", {}) or {}
                    key_can = _safe_selected_variants(selected_raw)[0] if _safe_selected_variants(selected_raw) else None
                    if key_can and key_can in planets_map:
                        pdata = planets_map.get(key_can) or {}
                        sign = pdata.get("sign") or sign
                        degree = pdata.get("degree") or pdata.get("deg") or degree
                        house = pdata.get("house") or house
                    if not sign:
                        for row in (summary.get("table", []) or []):
                            try:
                                if not isinstance(row, dict):
                                    continue
                                pname = row.get("planet") or row.get("planet_label") or row.get("planet_label_pt")
                                if not pname:
                                    continue
                                if (key_can and _safe_selected_variants(pname) and _safe_selected_variants(pname)[0] == key_can) or str(pname).lower() == str(selected_raw).lower():
                                    sign = row.get("sign") or row.get("zodiac") or row.get("sign_label") or row.get("sign_label_pt")
                                    degree = row.get("degree") or row.get("deg") or degree
                                    house = row.get("house") or house
                                    break
                            except Exception:
                                continue

                    interp = None
                    if astrology and hasattr(astrology, "interpret_planet_position"):
                        try:
                            interp = astrology.interpret_planet_position(
                                planet=key_can or selected_raw,
                                sign=sign,
                                degree=degree,
                                house=house,
                                aspects=summary.get("aspects"),
                                context_name=summary.get("name")
                            )
                        except Exception:
                            logger.exception("Erro ao chamar interpret_planet_position fallback")
                    generated = {
                        "planet": selected_raw,
                        "sign": sign,
                        "degree": degree,
                        "house": house,
                        "interpretation_short": (interp.get("short") if isinstance(interp, dict) else "") or "",
                        "interpretation_long": (interp.get("long") if isinstance(interp, dict) else "") or "",
                        "source": "astrology_fallback"
                    }
                except Exception:
                    logger.exception("Erro ao gerar leitura sintética para %s", selected_raw)
                    generated = None

            # salvar gerado em summary['readings'] sob chave canônica preferencial
            if generated:
                try:
                    key_to_save = _safe_selected_variants(selected_raw)[0] if _safe_selected_variants(selected_raw) else selected_raw
                    readings = summary.get("readings", {}) or {}
                    readings[key_to_save] = generated
                    summary["readings"] = readings
                    try:
                        st.session_state["map_summary"] = summary
                    except Exception:
                        logger.exception("Falha ao persistir map_summary após salvar leitura gerada")
                    canonical = key_to_save
                    label = generated.get("planet") or selected_raw
                    return canonical, label, generated
                except Exception:
                    logger.exception("Erro ao salvar leitura gerada para %s", selected_raw)
                    # mesmo que salvar falhe, retornar o gerado para exibição temporária
                    return None, None, generated

            # nada encontrado/gerado
            return None, None, None

        except Exception:
            logger.exception("Erro em get_or_generate_reading")
            return None, None, None

    def _get_position_for_ui(summary: Dict[str, Any], selected_raw: Optional[str]) -> Dict[str, Any]:
    #Retorna dict com keys: planet, sign, degree, longitude, house, source
    #Procura em summary['table'] (prioridade) e em summary['planets'] (fallback).
    #selected_raw pode ser nome raw (pt) ou canônico.
        out = {"planet": selected_raw, "sign": None, "degree": None, "longitude": None, "house": None, "source": None}
        if not summary or not selected_raw:
            return out

        # helpers locais
        def _match_name(a, b):
            try:
                if a is None or b is None:
                    return False
                if str(a).lower() == str(b).lower():
                    return True
                # tentar variantes canônicas se influences disponível
                try:
                    if influences and hasattr(influences, "to_canonical"):
                        return influences.to_canonical(a) == influences.to_canonical(b)
                except Exception:
                    pass
                return False
            except Exception:
                return False

        # 1) procurar na tabela (mais provável)
        table = summary.get("table") or []
        if isinstance(table, list):
            for row in table:
                try:
                    if not isinstance(row, dict):
                        continue
                    pname = row.get("planet") or row.get("planet_label") or row.get("planet_label_pt")
                    if _match_name(pname, selected_raw):
                        out["planet"] = pname
                        out["sign"] = row.get("sign") or row.get("sign_label") or row.get("sign_label_pt")
                        out["degree"] = row.get("degree") if row.get("degree") not in (None, "") else row.get("deg") or row.get("degree")
                        out["longitude"] = row.get("longitude")
                        out["house"] = row.get("house") or row.get("Casa") or row.get("house_number")
                        out["source"] = "table"
                        return out
                except Exception:
                    continue

        # 2) fallback para summary['planets']
        planets_map = summary.get("planets") or {}
        # tentar chave canônica primeiro
        try:
            key_can = None
            if influences and hasattr(influences, "to_canonical"):
                key_can = influences.to_canonical(selected_raw)
        except Exception:
            key_can = None

        # checar por key_can
        if key_can and key_can in planets_map:
            pdata = planets_map.get(key_can) or {}
            out["planet"] = key_can
            out["sign"] = pdata.get("sign") or pdata.get("zodiac")
            out["degree"] = pdata.get("degree") or pdata.get("deg")
            out["longitude"] = pdata.get("longitude")
            out["house"] = pdata.get("house")
            out["source"] = "planets_map_key"
            return out

        # checar por nome raw (case-insensitive)
        for pname, pdata in planets_map.items():
            try:
                if _match_name(pname, selected_raw):
                    out["planet"] = pname
                    if isinstance(pdata, dict):
                        out["sign"] = pdata.get("sign") or pdata.get("zodiac")
                        out["degree"] = pdata.get("degree") or pdata.get("deg")
                        out["longitude"] = pdata.get("longitude")
                        out["house"] = pdata.get("house")
                    else:
                        out["longitude"] = float(pdata) if isinstance(pdata, (int, float, str)) else None
                    out["source"] = "planets_map_iter"
                    return out
            except Exception:
                continue

        return out

    # LEFT: positions table and planet selector
    with left_col:
        st.markdown("### Posições")
        import pandas as _pd  # local import for optional dependency

        if summary:
            df = _pd.DataFrame(summary.get("table", []))
            # ensure df exists and has expected columns
            if df is None:
                df = _pd.DataFrame([])
        else:
            df = _pd.DataFrame([])

        # Build display dataframe with planet_label and sign_label
        if not df.empty and "planet" in df.columns:
            df_display = df.copy()
            df_display["planet_label"] = df_display["planet"].apply(_planet_label_for_display)
            if "sign" in df_display.columns:
                df_display["sign_label"] = df_display["sign"].apply(_sign_label_for_display)
        else:
            df_display = df.copy()
            if "planet" in df_display.columns and "planet_label" not in df_display.columns:
                df_display["planet_label"] = df_display["planet"]
            if "sign" in df_display.columns and "sign_label" not in df_display.columns:
                df_display["sign_label"] = df_display["sign"]

        if df_display.empty:
            st.info("Nenhuma posição disponível. Gere o mapa primeiro.")
        else:
            df_to_show = df_display.copy()
            if "planet_label" in df_to_show.columns:
                df_to_show = df_to_show.drop(columns=["planet"], errors="ignore")
                df_to_show = df_to_show.rename(columns={"planet_label": "Planeta"})
            if "sign_label" in df_to_show.columns:
                df_to_show = df_to_show.drop(columns=["sign"], errors="ignore")
                df_to_show = df_to_show.rename(columns={"sign_label": "Signo"})
            if "degree" in df_to_show.columns and "Graus" not in df_to_show.columns:
                df_to_show = df_to_show.rename(columns={"degree": "Graus"})
            if "house" in df_to_show.columns and "Casa" not in df_to_show.columns:
                df_to_show = df_to_show.rename(columns={"house": "Casa"})

            cols_to_show = [c for c in ["Planeta", "Signo", "Casa", "Graus"] if c in df_to_show.columns]
            df_exp = df_to_show[cols_to_show].copy() if cols_to_show else df_to_show.copy()
            with st.expander("Tabela de posições", expanded=False):
                st.dataframe(df_exp, use_container_width=True, height=300)

    # CENTER: map + interpretation
    with center_col:
        st.subheader("Mapa Astral")
        if not map_ready or fig_saved is None:
            st.info("Nenhum mapa gerado. Preencha os parâmetros e clique em 'Gerar Mapa'.")
        else:
            try:
                fig_dict = fig_saved.to_dict()
                fig = go.Figure(fig_dict)
            except Exception:
                fig = fig_saved

            sel_name = st.session_state.get("selected_planet")
            if sel_name and summary:
                try:
                    sel_lon = None
                    canonical_sel = _safe_canonical(sel_name)
                    planets_map = summary.get("planets", {}) or {}
                    if canonical_sel and planets_map.get(canonical_sel):
                        sel_lon = planets_map[canonical_sel].get("longitude")
                    elif planets_map.get(sel_name):
                        sel_lon = planets_map[sel_name].get("longitude")
                    if sel_lon is not None:
                        theta_sel = (360.0 - float(sel_lon)) % 360.0
                        display_text = None
                        try:
                            display_text = influences.CANONICAL_TO_PT.get(canonical_sel) if influences and hasattr(influences, "CANONICAL_TO_PT") else None
                        except Exception:
                            display_text = None
                        display_text = display_text or sel_name
                        fig.add_trace(go.Scatterpolar(
                            r=[1.0],
                            theta=[theta_sel],
                            mode="markers+text",
                            marker=dict(size=22, color="#b45b1f", line=dict(color="#000", width=0.5)),
                            text=[display_text],
                            textfont=dict(size=12, color="#000"),
                            hoverinfo="none",
                            showlegend=False
                        ))
                except Exception:
                    logger.exception("Erro ao adicionar marcador de seleção no gráfico")

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
                try:
                    clicked_planet = str(clicked_planet)
                    canonical_clicked = _safe_canonical(clicked_planet)
                    if st.session_state.get("selected_planet") != canonical_clicked:
                        st.session_state["selected_planet"] = canonical_clicked
                except Exception:
                    logger.exception("Erro ao processar clique no gráfico")

            # build label list and mapping to raw/canonical names
            # --- construir label_list e mapeamentos (garantir inicialização)
            label_list = []
            label_to_raw = {}
            label_to_canonical = {}

            # preencher label_list a partir do DataFrame (ajuste conforme suas colunas)
            if df_display is not None and not df_display.empty:
                # preferir coluna 'planet_label' para exibição
                if "planet_label" in df_display.columns:
                    for raw, plab in zip(df_display["planet"].values, df_display["planet_label"].values):
                        lab = f"{plab}"
                        label_list.append(lab)
                        label_to_raw[lab] = raw
                        label_to_canonical[lab] = _safe_canonical(raw) or raw
                else:
                    for raw in df_display["planet"].values:
                        lab = str(raw)
                        label_list.append(lab)
                        label_to_raw[lab] = raw
                        label_to_canonical[lab] = _safe_canonical(raw) or raw

            # garantir chaves no session_state
            st.session_state.setdefault("selected_planet", None)
            st.session_state.setdefault("planet_selectbox", None)

            # se houver opções, inicializar o valor do selectbox no session_state antes de criar o widget
            if label_list:
                # determinar label padrão (priorizar selected_planet se já definido)
                current_raw = st.session_state.get("selected_planet")
                default_label = None

                if current_raw:
                    for lab, raw in label_to_raw.items():
                        try:
                            # comparar variantes normalizadas quando disponível
                            if raw == current_raw or _safe_selected_variants(raw)[0] == _safe_selected_variants(current_raw)[0]:
                                default_label = lab
                                break
                        except Exception:
                            if str(raw).lower() == str(current_raw).lower():
                                default_label = lab
                                break

                if not default_label:
                    default_label = label_list[0]

                # setar session_state antes do widget se valor atual for inválido
                if st.session_state.get("planet_selectbox") not in label_list:
                    st.session_state["planet_selectbox"] = default_label

                # callback para sincronizar selected_planet quando selectbox muda
                def _on_select_planet():
                    sel_label = st.session_state.get("planet_selectbox")
                    sel_raw = label_to_raw.get(sel_label, sel_label)
                    st.session_state["selected_planet"] = sel_raw

                # criar selectbox usando o valor já presente em session_state (evita conflito)
                # preparar índice inicial com segurança
                try:
                    current_label = st.session_state.get("planet_selectbox")
                    idx = label_list.index(current_label) if (current_label in label_list) else 0
                except Exception:
                    idx = 0

                # criar selectbox (on_change continua útil para interações do usuário)
                st.selectbox(
                    "Selecionar planeta",
                    label_list,
                    index=idx,
                    key="planet_selectbox",
                    on_change=_on_select_planet
                )

                # --- garantir que a leitura do planeta selecionado exista logo na carga ---
                try:
                    # rótulo atualmente selecionado no selectbox (pode vir do session_state)
                    selected_label = st.session_state.get("planet_selectbox") or label_list[idx]

                    # mapear label para a chave "raw" usada nas leituras (ajuste conforme seu mapping)
                    try:
                        # se você tem um helper para canonicalizar
                        selected_raw = influences.to_canonical(selected_label) if influences and hasattr(influences, "to_canonical") else selected_label
                    except Exception:
                        selected_raw = selected_label

                    # checar se já existe leitura persistida
                    readings_map = (summary.get("readings") or {}) if isinstance(summary, dict) else {}
                    has_reading = False
                    # verificar por várias formas (canônico, label, case-insensitive)
                    if selected_raw in readings_map:
                        has_reading = True
                    else:
                        # tentar label literal
                        if selected_label in readings_map:
                            has_reading = True
                            selected_raw = selected_label
                        else:
                            # case-insensitive
                            try:
                                key_map = {str(k).lower(): k for k in readings_map.keys()}
                                k = key_map.get(str(selected_raw).lower())
                                if k:
                                    has_reading = True
                                    selected_raw = k
                            except Exception:
                                pass

                    # se não houver leitura, gerar agora (mesma lógica do on_change)
                    if not has_reading:
                        try:
                            # chamar a função que gera e persiste a leitura
                            result = find_or_generate_and_save_reading(summary, selected_raw)
                            # se a função retornar (reading, save_key) ou apenas reading, normalizar
                            if isinstance(result, tuple) and len(result) == 2:
                                generated, save_key = result
                            else:
                                generated = result
                                save_key = None
                            # garantir persistência no summary e session_state
                            if isinstance(generated, dict):
                                try:
                                    save_key = save_key or selected_raw
                                    if not isinstance(summary.get("readings"), dict):
                                        summary["readings"] = {}
                                    summary["readings"].setdefault(save_key, {}).update(generated)
                                    # também manter sob selected_label para compatibilidade
                                    summary["readings"].setdefault(selected_label, {}).update(generated)
                                    st.session_state["map_summary"] = summary
                                except Exception:
                                    logger.exception("Falha ao persistir leitura gerada automaticamente")
                        except Exception:
                            logger.exception("Erro ao gerar leitura inicial para o planeta selecionado")
                except Exception:
                    logger.exception("Erro ao inicializar seleção de planeta")

                    
    # RIGHT: interpretations and arcanos (refatorado)
    with right_col:
        st.subheader("Interpretação dos Arcanos")
        st.caption("Cada elemento do mapa possui uma relação com os Arcanos Maiores.")

        # criar tabs e desempacotar para evitar ambiguidade
        tab_planeta, tab_signo = st.tabs(["Planeta", "Signo"])

        # garantir selected_raw
        selected_raw = st.session_state.get("selected_planet")
        canonical_selected, label_selected = (None, None)
        try:
            if selected_raw:
                canonical_selected = _safe_canonical(selected_raw)
                label_selected = _planet_label_for_display(selected_raw)
        except Exception:
            canonical_selected, label_selected = (selected_raw, selected_raw)

        # helper: revalidar leitura persistida no summary['readings']
        def _get_persisted_reading(summary_obj, key):
            if not isinstance(summary_obj, dict):
                return None, None
            readings_map = summary_obj.get("readings") or {}
            # 1) literal
            if key in readings_map:
                return readings_map.get(key), key
            # 2) case-insensitive
            try:
                key_map = {str(k).lower(): k for k in readings_map.keys()}
                k = key_map.get(str(key).lower())
                if k:
                    return readings_map.get(k), k
            except Exception:
                pass
            # 3) procurar por campo planet/name dentro das leituras
            try:
                for k, v in readings_map.items():
                    if isinstance(v, dict):
                        p = (v.get("planet") or v.get("name") or "")
                        if p and str(p).lower() == str(key).lower():
                            return v, k
            except Exception:
                pass
            return None, None

        # obter leitura (compatível com retorno (generated, save_key) ou apenas generated)
        reading = None
        save_key = None
        if summary and selected_raw:
            try:
                result = find_or_generate_and_save_reading(summary, selected_raw)
                # função pode retornar (generated, save_key) ou apenas generated
                if isinstance(result, tuple) and len(result) == 2:
                    generated, save_key = result
                    reading = (summary.get("readings") or {}).get(save_key) or generated
                    logger.debug("find_or_generate returned save_key=%r; readings keys=%s", save_key, list((summary.get("readings") or {}).keys()))
                else:
                    generated = result
                    persisted, persisted_key = _get_persisted_reading(summary, selected_raw)
                    reading = persisted or generated
                    if persisted_key:
                        save_key = persisted_key
            except Exception:
                logger.exception("Erro ao buscar/gerar leitura para o planeta selecionado")
                reading = None

        # utilitário: extrair arcano e sugestões de forma robusta
        def _extract_arcano_and_suggestions(reading_obj):
            if not isinstance(reading_obj, dict):
                return None, []
            # priorizar arcano_planeta
            arc = reading_obj.get("arcano_planeta") or reading_obj.get("arcano_info") or reading_obj.get("arcano")
            # se arc for dict
            if isinstance(arc, dict):
                name = arc.get("name") or (f"Arcano {arc.get('arcano')}" if arc.get("arcano") else None)
                keywords = arc.get("keywords") or arc.get("practical") or arc.get("tags") or []
                text = arc.get("text") or arc.get("interpretation") or ""
                return {"name": name, "arcano": arc.get("arcano"), "text": text}, keywords
            # arc pode ser int/str
            if arc is not None:
                try:
                    num = int(arc)
                    label = interpretations.arcano_label(num) if interpretations and hasattr(interpretations, "arcano_label") else f"Arcano {num}"
                    return {"name": label, "arcano": str(num), "text": ""}, reading_obj.get("suggestions") or reading_obj.get("keywords") or []
                except Exception:
                    return {"name": str(arc), "arcano": str(arc), "text": ""}, reading_obj.get("suggestions") or reading_obj.get("keywords") or []
            # fallback: tentar usar reading['arcano_info'] ou reading['arcano']
            return None, reading_obj.get("suggestions") or reading_obj.get("keywords") or []

        # Planeta (refatorado para usar client_name e persistir o nome)
        with tab_planeta:
            st.caption("Interpretação associada ao planeta selecionado.")
            # resolver client_name do mesmo modo que na aba Signo
            client_name = st.session_state.get("name") or (summary.get("name") if summary else None) or "Consulente"
            # garantir que o session_state tenha a chave canonical "name"
            try:
                if not st.session_state.get("name"):
                    st.session_state["name"] = client_name
            except Exception:
                pass

            if not summary:
                st.info("Resumo do mapa não disponível. Gere o mapa antes de ver a análise por planeta.")
            elif not selected_raw:
                st.info("Selecione um planeta para ver a interpretação por arcanos.")
            else:
                # obter leitura (compatível com retorno (reading, save_key) ou apenas reading)
                reading = None
                save_key = None
                try:
                    result = find_or_generate_and_save_reading(summary, selected_raw)
                    if isinstance(result, tuple) and len(result) == 2:
                        generated, save_key = result
                        reading = (summary.get("readings") or {}).get(save_key) or generated
                    else:
                        generated = result
                        # revalidar persistido
                        readings_map = summary.get("readings") or {}
                        reading = readings_map.get(selected_raw)
                        if not reading:
                            key_map = {str(k).lower(): k for k in readings_map.keys()}
                            k = key_map.get(str(selected_raw).lower())
                            if k:
                                reading = readings_map.get(k)
                        if not reading:
                            # procurar por campo planet/name
                            for v in readings_map.values():
                                if isinstance(v, dict):
                                    p = (v.get("planet") or v.get("name") or "")
                                    if p and str(p).lower() == str(selected_raw).lower():
                                        reading = v
                                        break
                        if not reading:
                            reading = generated
                except Exception:
                    logger.exception("Erro ao buscar/gerar leitura para o planeta selecionado")
                    reading = None

                # se não houver leitura, avisar
                if not reading:
                    st.info("Nenhuma leitura encontrada para o planeta selecionado.")
                else:
                    # garantir que reading contenha o nome do consulente para geradores/templates
                    try:
                        if isinstance(reading, dict):
                            if not reading.get("name"):
                                reading["name"] = client_name
                            # persistir o name na estrutura summary['readings'] quando possível
                            try:
                                if save_key:
                                    if not isinstance(summary.get("readings"), dict):
                                        summary["readings"] = {}
                                    summary["readings"].setdefault(save_key, {}).update({"name": client_name})
                                    # também manter sob selected_raw para compatibilidade
                                    summary["readings"].setdefault(selected_raw, {}).update({"name": client_name})
                                    # atualizar session_state para UI
                                    try:
                                        st.session_state["map_summary"] = summary
                                    except Exception:
                                        pass
                            except Exception:
                                logger.debug("Não foi possível persistir name em summary['readings']", exc_info=True)
                    except Exception:
                        pass

                    # rótulos
                    planet_label = (
                        influences.CANONICAL_TO_PT.get(canonical_selected)
                        if influences and hasattr(influences, "CANONICAL_TO_PT")
                        else canonical_selected
                    ) or (label_selected or "—")

                    raw_sign = reading.get("sign")
                    try:
                        sign_canonical = (
                            influences.sign_to_canonical(raw_sign)
                            if influences and hasattr(influences, "sign_to_canonical")
                            else raw_sign
                        )
                    except Exception:
                        sign_canonical = raw_sign

                    sign_label = (
                        influences.sign_label_pt(sign_canonical)
                        if influences and hasattr(influences, "sign_label_pt")
                        else (sign_canonical or raw_sign or "—")
                    )

                    st.markdown(f"#### {planet_label} em {sign_label}")
                    st.markdown("**Arcano correspondente ao planeta:**")
                    # exibir resumo curto (formatar com nome quando aplicável)
                    short_text = reading.get("interpretation_short") or ""
                    try:
                        if isinstance(short_text, str) and "{name}" in short_text:
                            short_text = short_text.format(name=client_name)
                    except Exception:
                        pass
                    st.write(short_text or "Resumo não disponível.")

                    # EXPANDER: interpretação completa
                    with st.expander("Interpretação", expanded=False):
                        # extrair arcano e sugestões (robusto)
                        def _extract_arcano_and_suggestions(reading_obj):
                            if not isinstance(reading_obj, dict):
                                return None, []
                            arc = reading_obj.get("arcano_planeta") or reading_obj.get("arcano_info") or reading_obj.get("arcano")
                            if isinstance(arc, dict):
                                name = arc.get("name") or (f"Arcano {arc.get('arcano')}" if arc.get("arcano") else None)
                                keywords = arc.get("keywords") or arc.get("practical") or arc.get("tags") or []
                                text = arc.get("text") or arc.get("interpretation") or ""
                                return {"name": name, "arcano": arc.get("arcano"), "text": text}, keywords
                            if arc is not None:
                                try:
                                    num = int(arc)
                                    label = interpretations.arcano_label(num) if interpretations and hasattr(interpretations, "arcano_label") else f"Arcano {num}"
                                    return {"name": label, "arcano": str(num), "text": ""}, reading_obj.get("suggestions") or reading_obj.get("keywords") or []
                                except Exception:
                                    return {"name": str(arc), "arcano": str(arc), "text": ""}, reading_obj.get("suggestions") or reading_obj.get("keywords") or []
                            return None, reading_obj.get("suggestions") or reading_obj.get("keywords") or []

                        # tentar extrair do reading persistido
                        arc_struct, suggestions = _extract_arcano_and_suggestions(reading)

                        # se arc_struct ausente ou sem texto, tentar gerar texto dinâmico passando client_name
                        if (not arc_struct or not arc_struct.get("text")) and interpretations and hasattr(interpretations, "arcano_for_planet"):
                            try:
                                # chamar wrapper seguro quando disponível; passar name defensivamente
                                arc_res = None
                                if hasattr(interpretations, "safe_arcano_for_planet"):
                                    arc_res = interpretations.safe_arcano_for_planet(summary, selected_raw)
                                else:
                                    try:
                                        arc_res = interpretations.arcano_for_planet(summary, selected_raw, name=client_name)
                                    except TypeError:
                                        arc_res = interpretations.arcano_for_planet(summary, selected_raw)
                                if isinstance(arc_res, dict):
                                    text = arc_res.get("text") or arc_res.get("interpretation") or ""
                                    # formatar templates que contenham {name}
                                    try:
                                        if isinstance(text, str) and "{name}" in text:
                                            text = text.format(name=client_name)
                                    except Exception:
                                        pass
                                    arc_struct = {
                                        "name": arc_res.get("name") or (arc_struct.get("name") if arc_struct else None),
                                        "arcano": arc_res.get("arcano") or (arc_struct.get("arcano") if arc_struct else None),
                                        "text": text
                                    }
                                    kw = arc_res.get("keywords") or arc_res.get("tags") or []
                                    if kw and not suggestions:
                                        suggestions = kw
                            except Exception:
                                logger.debug("Gerador de arcano dinâmico falhou", exc_info=True)

                        # exibir arcano legível
                        if arc_struct and arc_struct.get("name"):
                            st.write(arc_struct["name"])
                        elif arc_struct and arc_struct.get("arcano"):
                            try:
                                num = int(arc_struct["arcano"])
                                if interpretations and hasattr(interpretations, "arcano_label"):
                                    st.write(interpretations.arcano_label(num))
                                else:
                                    st.write(f"Arcano {num}")
                            except Exception:
                                st.write(str(arc_struct.get("arcano")))
                        else:
                            st.write("— Nenhum arcano associado ao planeta —")

                        # Interpretação longa / texto do arcano (preferir reading, depois arc_struct.text)
                        long_text = reading.get("interpretation_long") or (arc_struct.get("text") if arc_struct else "")
                        # formatar com client_name quando aplicável
                        try:
                            if isinstance(long_text, str) and "{name}" in long_text:
                                long_text = long_text.format(name=client_name)
                        except Exception:
                            pass
                        st.write(long_text or "Interpretação não disponível.")

                        # Sugestões práticas
                        st.markdown("**Sugestões práticas**")
                        if not suggestions:
                            suggestions = reading.get("suggestions") or reading.get("keywords") or []
                        if suggestions:
                            for k in suggestions:
                                st.write(f"- {k}")
                        else:
                            st.write("Nenhuma sugestão prática disponível.")

        # Signo (atualizado: mostra keyword no título e interpretation_short)
        with tab_signo:
            st.caption("Interpretação associada ao signo onde o planeta está posicionado. Se não há planeta no signo, não há influência direta.")
            client_name = st.session_state.get("name") or (summary.get("name") if summary else "Consulente")

            if not summary:
                st.info("Resumo do mapa não disponível. Gere o mapa antes de ver a influência por signo.")
            else:
                table = summary.get("table", []) or []
                sign_map: Dict[str, str] = {}
                for row in table:
                    raw = row.get("sign") or row.get("zodiac")
                    if not raw:
                        continue
                    try:
                        norm = interpretations._normalize_sign(raw) if interpretations and hasattr(interpretations, "_normalize_sign") else raw
                    except Exception:
                        norm = raw
                    if not norm:
                        continue
                    if norm not in sign_map:
                        sign_map[norm] = raw

                if not sign_map:
                    st.info("Nenhum signo detectado no mapa.")
                else:
                    # dentro de with tab_signo: substitua o loop existente por este
                    for norm, raw_sign in sign_map.items():
                        display_sign = str(raw_sign).strip()

                        # tentar obter até duas keywords representativas (defensivo)
                        keyword_labels: List[str] = []
                        try:
                            # 1) services_analysis (mapa estático)
                            if 'services_analysis' in globals() and services_analysis and hasattr(services_analysis, "PLANET_ARCANO"):
                                sa_map = getattr(services_analysis, "PLANET_ARCANO", {}) or {}
                                candidates = [display_sign, str(norm), str(norm).capitalize()]
                                for c in candidates:
                                    entry = sa_map.get(c)
                                    if isinstance(entry, dict):
                                        kws = entry.get("keywords") or []
                                        for kw in kws:
                                            if kw and kw not in keyword_labels:
                                                keyword_labels.append(kw)
                                            if len(keyword_labels) >= 2:
                                                break
                                    if len(keyword_labels) >= 2:
                                        break

                            # 2) fallback: pedir ao generator por um preview curto que contenha keywords
                            if len(keyword_labels) < 2 and interpretations and hasattr(interpretations, "arcano_for_sign"):
                                try:
                                    preview = interpretations.arcano_for_sign(raw_sign, name=client_name, length="short")
                                    if isinstance(preview, dict):
                                        # algumas implementações retornam 'keywords' ou 'tags'
                                        kws = preview.get("keywords") or preview.get("tags") or []
                                        for kw in kws:
                                            if kw and kw not in keyword_labels:
                                                keyword_labels.append(kw)
                                            if len(keyword_labels) >= 2:
                                                break
                                except Exception:
                                    pass
                        except Exception:
                            # não falhar por causa da extração de keywords
                            keyword_labels = keyword_labels[:2]

                        # montar sufixo com até duas expressões
                        kw_suffix = ""
                        if keyword_labels:
                            kw_suffix = " : " + " - ".join(keyword_labels[:2])

                        expander_title = f"**{display_sign}{kw_suffix}**"

                        with st.expander(expander_title):
                            try:
                                # gerar interpretação longa e curta (defensivo)
                                if interpretations and hasattr(interpretations, "arcano_for_sign"):
                                    try:
                                        arc_long = interpretations.arcano_for_sign(raw_sign, name=client_name, length="long")
                                    except TypeError:
                                        arc_long = interpretations.arcano_for_sign(raw_sign, name=client_name)
                                    try:
                                        arc_short = interpretations.arcano_for_sign(raw_sign, name=client_name, length="short")
                                    except TypeError:
                                        arc_short = arc_long or {}
                                else:
                                    arc_long = {"error": "serviço de arcano não disponível"}
                                    arc_short = {"error": "serviço de arcano não disponível"}
                            except Exception as e:
                                arc_long = {"error": str(e)}
                                arc_short = {"error": str(e)}

                            if arc_long.get("error"):
                                st.warning("Não foi possível gerar interpretação por signo: " + str(arc_long.get("error")))
                                continue

                            # exibir resumo curto (interpretation_short) quando disponível
                            short_text = arc_short.get("text") or arc_short.get("short") or arc_short.get("interpretation_short") or ""
                            if short_text and short_text.strip():
                                st.markdown("**Resumo**")
                                # formatar com nome do consulente se necessário
                                try:
                                    if "{name}" in short_text:
                                        short_text = short_text.format(name=client_name)
                                except Exception:
                                    pass
                                st.write(short_text)

                            # exibir texto longo
                            long_text = arc_long.get("text") or arc_long.get("long") or arc_long.get("interpretation") or ""
                            if long_text and long_text.strip():
                                st.markdown("**Interpretação**")
                                try:
                                    if "{name}" in long_text:
                                        long_text = long_text.format(name=client_name)
                                except Exception:
                                    pass
                                st.write(long_text)
                            else:
                                st.write("Interpretação não disponível para este signo no momento.")

    # -------------------------
    # Integração: Leitura Sintética (painel esquerdo) e Interpretação Astrológica (painel central)
    # Inserir ao final do bloco de UI já existente, após a construção das colunas
    # -------------------------

    # LEITURA SINTÉTICA (inserida no painel esquerdo, abaixo da tabela de posições)
    with left_col:
        st.markdown("#### Leitura Sintética")

        sel_planet = st.session_state.get("selected_planet")
        if not sel_planet or not summary:
            st.info("Selecione um planeta na tabela para ver a leitura sintética.")
        else:
            # tentar obter leitura persistida (se existir)
            canonical = label = reading = None
            try:
                if callable(globals().get("get_or_generate_reading")):
                    canonical, label, reading = get_or_generate_reading(summary, sel_planet)
            except Exception:
                logger.exception("get_or_generate_reading falhou na Leitura Sintética")
                canonical, label, reading = None, None, None

            # helper defensivo para extrair sign/degree/house a partir de reading ou summary
            def _extract_position(reading_obj, summary_obj, sel):
                sign = degree = house = None
                # 1) tentar a leitura persistida
                try:
                    if isinstance(reading_obj, dict):
                        sign = reading_obj.get("sign") or reading_obj.get("sign_label")
                        degree = reading_obj.get("degree") or reading_obj.get("deg")
                        house = reading_obj.get("house")
                except Exception:
                    pass
                # 2) fallback para summary.table / summary.planets
                if (not sign or degree in (None, "", "None") or house in (None, "", "None")) and isinstance(summary_obj, dict):
                    try:
                        # procurar na tabela
                        for row in (summary_obj.get("table") or []):
                            try:
                                pname = (row.get("planet") or row.get("planet_label") or "").strip()
                                if pname and str(pname).lower() == str(sel).lower():
                                    sign = sign or row.get("sign") or row.get("sign_label") or row.get("sign_label_pt")
                                    degree = degree or row.get("degree") or row.get("deg")
                                    house = house or row.get("house")
                                    break
                            except Exception:
                                continue
                    except Exception:
                        logger.debug("Erro ao buscar na tabela para fallback de posição")
                    # fallback para summary['planets']
                    try:
                        planets_map = summary_obj.get("planets") or {}
                        # tentar chave canônica se influences disponível
                        key_can = None
                        try:
                            if influences and hasattr(influences, "to_canonical"):
                                key_can = influences.to_canonical(sel)
                        except Exception:
                            key_can = None
                        if key_can and key_can in planets_map:
                            pdata = planets_map.get(key_can) or {}
                            sign = sign or pdata.get("sign") or pdata.get("zodiac")
                            degree = degree or pdata.get("degree") or pdata.get("deg")
                            house = house or pdata.get("house")
                        else:
                            for pname, pdata in planets_map.items():
                                try:
                                    if str(pname).lower() == str(sel).lower():
                                        if isinstance(pdata, dict):
                                            sign = sign or pdata.get("sign") or pdata.get("zodiac")
                                            degree = degree or pdata.get("degree") or pdata.get("deg")
                                            house = house or pdata.get("house")
                                        break
                                except Exception:
                                    continue
                    except Exception:
                        logger.debug("Erro ao buscar em summary['planets'] para fallback de posição")
                return sign, degree, house

            sign, degree, house = _extract_position(reading, summary, sel_planet)

            # construir leitura sintética curta (verb, sign noun, house noun)
            try:
                planet_verb, planet_core = astrology.PLANET_CORE.get(canonical or sel_planet, ("", ""))
            except Exception:
                planet_verb, planet_core = "", ""
            try:
                sign_noun, sign_quality = astrology.SIGN_DESCRIPTIONS.get(sign, ("", ""))
            except Exception:
                sign_noun, sign_quality = "", ""
            try:
                house_noun, house_theme = (astrology.HOUSE_DESCRIPTIONS.get(int(house), ("", "")) if house not in (None, "", "None") else ("", ""))
            except Exception:
                house_noun, house_theme = "", ""

            parts = [p for p in (planet_verb, sign_noun, house_noun) if p]
            synthetic_line = " — ".join(parts) if parts else ""

            # palavras-chave curtas (únicas, limitadas)
            keywords = []
            if planet_core:
                keywords += [k.strip() for k in str(planet_core).split(",") if k.strip()]
            if sign_quality:
                keywords += [k.strip() for k in str(sign_quality).split(",") if k.strip()]
            if house_theme:
                keywords += [k.strip() for k in str(house_theme).split(",") if k.strip()]
            seen = []
            for k in keywords:
                if k not in seen:
                    seen.append(k)
            keywords_line = ", ".join(seen[:8]) if seen else None

            # rótulo do planeta para exibição
            try:
                display_name = (reading.get("planet") if isinstance(reading, dict) and reading.get("planet") else label) or (canonical or sel_planet)
            except Exception:
                display_name = label or (canonical or sel_planet)

            #st.markdown(f"**{display_name}**")
            st.write(f"Planeta: **{display_name or '—'}**  •  Signo: **{sign or '—'}**  •  Casa: **{house or '—'}**")

            if synthetic_line:
                st.write(f"Significado: {synthetic_line}")

            # interpretar localmente (defensivo)
            try:
                interp_local = astrology.interpret_planet_position(
                    planet=canonical or sel_planet,
                    sign=sign,
                    degree=degree,
                    house=house,
                    aspects=summary.get("aspects"),
                    context_name=(reading.get("name") if isinstance(reading, dict) else None) or summary.get("name")
                ) or {"short": ""}
            except Exception:
                logger.exception("interpret_planet_position falhou na Leitura Sintética")
                interp_local = {"short": ""}

            short_local = (interp_local.get("short") or "").strip()
            with st.expander("Interpretação"):
                if short_local:
                    st.write(short_local)
                elif keywords_line:
                    st.write(f"Palavras-chave: {keywords_line}")
                else:
                    st.write("—")

    # INTERPRETAÇÃO ASTROLÓGICA (painel central, integrado com o mapa)
    with center_col:
            st.markdown("### Interpretação Astrológica")

            sel_planet = st.session_state.get("selected_planet")
            canonical, label, reading = None, None, None
            try:
                canonical, label, reading = get_or_generate_reading(summary, sel_planet) if callable(globals().get("get_or_generate_reading")) else (None, None, None)
            except Exception:
                logger.exception("get_or_generate_reading falhou")
                canonical, label, reading = None, None, None

            # tentar extrair aspectos uma vez
            aspects = ensure_aspects(summary)

            if reading:
                # se houver leitura persistida, usar como antes
                sign = reading.get("sign")
                degree = reading.get("degree") or reading.get("deg")
                house = reading.get("house")
                try:
                    interp = astrology.interpret_planet_position(
                        planet=canonical or sel_planet,
                        sign=sign,
                        degree=degree,
                        house=house,
                        aspects=aspects,
                        context_name=reading.get("name") or summary.get("name")
                    ) or {"short": "", "long": ""}
                except Exception:
                    logger.exception("interpret_planet_position falhou com reading")
                    interp = {"short": "", "long": ""}
            else:
                # fallback imediato: extrair posição do summary e chamar interpret_planet_position
                sign = None
                degree = None
                house = None
                # Extrair tabela de posições de forma segura
                try:
                    if not isinstance(summary, dict):
                        logger.warning("Resumo do mapa (summary) ausente ou inválido ao tentar extrair posição para fallback")
                        table_rows = []
                    else:
                        table_rows = summary.get("table") or []
                except Exception:
                    logger.exception("Erro ao acessar summary para extrair table")
                    table_rows = []

                # iterar sobre table_rows (seguro mesmo se summary for None)
                for row in table_rows:
                    try:
                        # seu processamento existente aqui, por exemplo:
                        pname = row.get("planet") or row.get("name")
                        # ... resto do código que usa row ...
                    except Exception:
                        logger.exception("Erro ao processar linha da tabela de fallback: %r", row)
                        continue

                    # fallback para summary['planets']
                    if not sign or degree is None or house is None:
                        planets_map = summary.get("planets", {}) or {}
                        # tentar por chave canônica
                        key_can = None
                        try:
                            key_can = _safe_selected_variants(sel_planet)[0] if sel_planet else None
                        except Exception:
                            key_can = None
                        if key_can and key_can in planets_map:
                            pdata = planets_map.get(key_can) or {}
                            sign = sign or pdata.get("sign")
                            degree = degree or pdata.get("degree") or pdata.get("deg")
                            house = house or pdata.get("house")
                        else:
                            # tentar por nome raw
                            for pname, pdata in planets_map.items():
                                try:
                                    if str(pname).lower() == str(sel_planet).lower():
                                        sign = sign or pdata.get("sign")
                                        degree = degree or pdata.get("degree") or pdata.get("deg")
                                        house = house or pdata.get("house")
                                        break
                                except Exception:
                                    continue

                # preparar valores seguros (conforme já feito)
                sel_planet_safe = _safe_selected_variants(sel_planet)[0] if sel_planet else None
                context_name = summary.get("name") if isinstance(summary, dict) else None

                # chamar interpretador apenas quando houver dados suficientes
                if sel_planet_safe and isinstance(summary, dict):
                    try:
                        interp = astrology.interpret_planet_position(
                            planet=sel_planet_safe,
                            sign=sign,
                            degree=degree,
                            house=house,
                            aspects=aspects,
                            context_name=context_name
                        ) or {"short": "", "long": ""}
                    except Exception:
                        logger.exception("interpret_planet_position falhou no fallback")
                        interp = {"short": "", "long": ""}

                    long_text = (interp.get("long") or "").strip()
                    with st.expander("Interpretação"):
                        st.write(long_text or "—")
                else:
                    st.info("Selecione um planeta na tabela e gere o resumo do mapa para ver a interpretação astrológica.")

    # Botão robusto para gerar interpretação IA
    if st.sidebar.button("Gerar interpretação IA Etheria"):
        if not st.session_state.get("map_ready"):
            st.error("Gere o mapa primeiro antes de pedir a interpretação.")
        else:
            summary = st.session_state.get("map_summary")
            if not summary:
                st.error("Resumo do mapa ausente.")
            else:
                gs_mod = None
                gs_fn = None

                # tentativa 1: import do pacote principal do projeto
                try:
                    gs_mod = importlib.import_module("etheria.services.generator_service")
                except Exception:
                    gs_mod = None
                    logger.debug("etheria.services.generator_service não importável", exc_info=True)

                # tentativa 2: import alternativo (deploys menores)
                if gs_mod is None:
                    try:
                        gs_mod = importlib.import_module("services.generator_service")
                    except Exception:
                        gs_mod = None
                        logger.debug("services.generator_service não importável", exc_info=True)

                # identificar função disponível (vários nomes possíveis)
                if gs_mod:
                    for candidate in ("generate_interpretation_from_summary", "generate_analysis", "generate_ai_text_from_chart"):
                        try:
                            fn = getattr(gs_mod, candidate, None)
                            if callable(fn):
                                gs_fn = fn
                                break
                        except Exception:
                            continue

                # se não encontrou, informar e logar
                if not gs_mod or not gs_fn:
                    logger.warning("Generator service indisponível ou função não encontrada. gs_mod=%s, gs_fn=%s", bool(gs_mod), bool(gs_fn))
                    st.error("Serviço de geração não disponível. Verifique generator_service e os nomes das funções exportadas.")
                else:
                    # executar geração com tratamento de exceções
                    with st.spinner("Gerando interpretação IA Etheria..."):
                        res = None
                        try:
                            # alguns serviços aceitam (summary, generate_analysis, timeout_seconds)
                            # tentamos chamar de forma compatível com várias assinaturas
                            try:
                                res = gs_fn(summary, generate_analysis, timeout_seconds=60)
                            except TypeError:
                                try:
                                    res = gs_fn(summary, timeout_seconds=60)
                                except TypeError:
                                    res = gs_fn(summary)
                        except Exception as e:
                            logger.exception("Erro ao chamar função de geração IA: %s", e)
                            st.error("Erro ao gerar interpretação IA Etheria. Verifique os logs do servidor.")
                            return
                        finally:
                            pass

                        # normalizar retorno
                        if not isinstance(res, dict):
                            res = {"error": "Resposta inválida do serviço", "raw_response": str(res)}
                        res.setdefault("error", None)
                        res.setdefault("analysis_text", "")

                        if res.get("error"):
                            st.error(res["error"])
                        else:
                            ai_text = (res.get("analysis_text") or res.get("text") or res.get("raw_text") or "").strip()
                            if not ai_text:
                                ai_text = f"{summary.get('name','Interpretação')}: interpretação não disponível no momento."
                            st.success("Interpretação IA Etheria gerada")
                            st.write(ai_text)
                            st.download_button("Exportar interpretação (.txt)", data=ai_text, file_name="interpretacao_ia.txt", mime="text/plain")

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Erro ao executar main() diretamente")