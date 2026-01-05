# mapa_astral.py — Versão refatorada
from __future__ import annotations

"""
Mapa astral (refatorado)
- Imports organizados
- Helpers centrais: parsing, timezone, geocoding
- Fluxo único de submissão (Streamlit)
- Stubs seguros para funções ainda não implementadas
- Renderização Plotly defensiva
"""

import csv
import importlib
import json
import logging
import os
import traceback
import swisseph as swe, datetime, zoneinfo
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

from datetime import datetime, date, time as dt_time

import streamlit as st

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Optional project imports (defensive)
try:
    from etheria import astrology, influences, rules, interpretations  # type: ignore
except Exception:
    astrology = influences = rules = interpretations = None  # type: ignore

# Optional services
try:
    from etheria.services.generator_service import generate_analysis, generate_ai_text_from_chart  # type: ignore
except Exception:
    generate_analysis = generate_ai_text_from_chart = None

try:
    from services.swisseph_client import natal_positions  # type: ignore
except Exception:
    natal_positions = None

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

# Simple in-memory cache for aspects
_aspects_cache: Dict[str, dict] = {}

# -------------------------
# Helpers: timezone, parsing, geocoding
# -------------------------
def normalize_tz_name(tz_name: Optional[str]) -> Optional[str]:
    if not tz_name:
        return None
    tz = str(tz_name).strip().replace(" ", "_")
    # zoneinfo
    try:
        from zoneinfo import ZoneInfo
        ZoneInfo(tz)
        return tz
    except Exception:
        pass
    # pytz
    try:
        import pytz as _pytz
        if tz in getattr(_pytz, "all_timezones", []):
            return tz
    except Exception:
        pass
    # dateutil
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
    # zoneinfo
    try:
        from zoneinfo import ZoneInfo
        return dt_naive.replace(tzinfo=ZoneInfo(tz_name))
    except Exception:
        pass
    # pytz
    try:
        import pytz as _pytz
        tz = _pytz.timezone(tz_name)
        return tz.localize(dt_naive)
    except Exception:
        pass
    # dateutil
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
# City map loader
# -------------------------
@st.cache_data
def load_city_map_csv(path: str = "data/cities.csv") -> Dict[str, dict]:
    city_map: Dict[str, dict] = {}
    p = Path(path)
    if not p.exists():
        return city_map
    with p.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            name = (r.get("name") or r.get("city") or "").strip()
            if not name:
                continue
            try:
                lat = float(r.get("lat")) if r.get("lat") not in (None, "") else None
                lon = float(r.get("lon")) if r.get("lon") not in (None, "") else None
            except Exception:
                lat = lon = None
            tz = (r.get("tz") or "").strip() or None
            city_map[name] = {"lat": lat, "lon": lon, "tz": tz}
    city_map.setdefault("Outra (digitar...)", {})
    return city_map

CITY_MAP = load_city_map_csv("data/cities.csv") or {
    "São Paulo, SP, Brasil": {"lat": -23.550520, "lon": -46.633308, "tz": "America/Sao_Paulo"},
    "Outra (digitar...)": {}
}

# -------------------------
# Safe wrappers and stubs
# -------------------------
def resolve_place_and_tz(place: str):
    lat = lon = None
    tz_name = None
    address = None
    if place:
        meta = CITY_MAP.get(place)
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

# Safe stubs for functions not yet implemented
def fetch_natal_chart(name, dt_local, lat, lon, tz_name):
    return {"planets": {}, "cusps": []}

def natal_positions(dt_local, lat, lon, house_system="P"):
    return {"planets": {}, "cusps": []}

def positions_table(planets):
    return []

def compute_aspects(planets):
    return []

def generate_chart_summary(planets, name, bdate):
    return {"planets": planets}

def enrich_summary_with_astrology(summary):
    return summary

# -------------------------
# Aspects helper
# -------------------------
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
            valid_planets[name] = float(lon)
            planet_meta[name] = extract_meta(pdata) if isinstance(pdata, dict) else {}

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

    names = []
    thetas = []
    hover_texts = []
    symbol_texts = []
    lon_values = []
    marker_sizes = []
    text_sizes = []
    marker_colors = []
    text_colors = []

    # prepare sign names and symbols defensively
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
    sign_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]

    # pre-normalize groups
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

    for name, lon in ordered:
        try:
            if lon is None:
                logger.warning("Longitude ausente para %s; pulando", name)
                continue
            theta = lon_to_theta(lon)
        except Exception:
            logger.warning("Falha ao converter longitude para theta: %s -> %s", name, lon)
            continue

        lname = str(name).lower()
        is_asc = lname in ("asc", "ascendant", "ascendente")
        is_mc = lname in ("mc", "medium coeli", "meio do ceu", "meio do céu")

        try:
            sign_index = int(float(lon) // 30) % 12
            degree_in_sign = float(lon) % 30
        except Exception:
            sign_index = 0
            degree_in_sign = 0.0

        meta = planet_meta.get(name, {}) or {}
        meta_sign = meta.get("sign")
        meta_house = meta.get("house")

        sign_short = sign_names[sign_index] if 0 <= sign_index < len(sign_names) else canonical_signs[sign_index % 12]

        try:
            display_planet = influences.planet_label_pt(influences.to_canonical(name)) if influences and hasattr(influences, "planet_label_pt") else name
        except Exception:
            display_planet = name

        hover_parts = [
            f"<b>{display_planet}</b>",
            f"{float(lon):.2f}° eclíptico",
            f"{degree_in_sign:.1f}° no signo",
            f"Signo (calc): {sign_short}"
        ]
        if meta_sign:
            try:
                meta_sign_can = influences.sign_to_canonical(meta_sign) if influences and hasattr(influences, "sign_to_canonical") else meta_sign
                meta_sign_label = influences.sign_label_pt(meta_sign_can) if influences and hasattr(influences, "sign_label_pt") else (meta_sign)
            except Exception:
                meta_sign_label = meta_sign
            hover_parts.append(f"Signo (meta): {meta_sign_label}")
        if meta_house:
            hover_parts.append(f"Casa (meta): {meta_house}")
        hover_text = "<br>".join(hover_parts)

        try:
            symbol = planet_symbols.get(name) or planet_symbols.get(name.capitalize()) or planet_symbols.get(influences.to_canonical(name) if influences else name, name)
        except Exception:
            symbol = planet_symbols.get(name, name)

        base_marker = 26 * marker_scale
        base_text = 16 * text_scale
        size = base_marker * (1.6 if is_asc or is_mc else 1.0)
        text_size = base_text * (1.4 if is_asc or is_mc else 1.0)

        color = colors.get("default")
        try:
            name_can = influences.to_canonical(name) if influences and hasattr(influences, "to_canonical") else name
            for gname, members_can in _normalized_groups.items():
                if name_can in members_can:
                    color = _color_for_group(gname)
                    break
        except Exception:
            for gname, members in (groups or {}).items():
                if name in members:
                    color = _color_for_group(gname)
                    break

        text_color = color

        names.append(display_planet)
        thetas.append(theta)
        lon_values.append(float(lon))
        hover_texts.append(hover_text)
        symbol_texts.append(symbol)
        marker_sizes.append(size)
        text_sizes.append(text_size)
        marker_colors.append(color)
        text_colors.append(text_color)

    # Build figure
    fig = go.Figure()
    thetas_deg = thetas
    try:
        fig.add_trace(go.Scatterpolar(
            r=[1.0] * len(thetas_deg),
            theta=thetas_deg,
            mode="markers+text",
            marker=dict(size=[max(6, int(ms)) for ms in marker_sizes], color=marker_colors),
            text=[planet_symbols.get(n, n) for n in names],
            textposition="middle center",
            hovertext=hover_texts,
            hoverinfo="text"
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=False),
                angularaxis=dict(direction="clockwise", rotation=90)
            ),
            showlegend=False,
            margin=dict(l=10, r=10, t=10, b=10),
            template="plotly_white"
        )
    except Exception as e:
        logger.exception("Erro ao construir figura Plotly: %s", e)
        return None

    if export_png:
        try:
            img_bytes = fig.to_image(format="png", width=export_size[0], height=export_size[1])
        except Exception as e:
            logger.warning("Falha ao exportar PNG: %s", e)

    return fig

# -------------------------
# UI / Streamlit flow (refatorado)
# -------------------------
def main():
    # session defaults
    st.session_state.setdefault("house_system", "P")
    st.session_state.setdefault("map_ready", False)
    st.session_state.setdefault("lat_manual", -23.6636)
    st.session_state.setdefault("lon_manual", -46.5381)
    st.session_state.setdefault("tz_manual", "America/Sao_Paulo")
    st.session_state.setdefault("btime_text", "")
    st.session_state.setdefault("map_summary", None)
    st.session_state.setdefault("map_fig", None)
    st.session_state.setdefault("selected_planet", None)
    st.session_state.setdefault("use_ai", False)

    PAGE_ID = "mapa_astral"
    st.sidebar.header("Entrada do Consulente")

    # Formulário lateral
    with st.sidebar:
        form_key = f"birth_form_sidebar_{PAGE_ID}"
        with st.form(key=form_key, clear_on_submit=False):
            name = st.text_input("Nome", value=st.session_state.get("name", ""))
            # oferecer selectbox com cidades conhecidas, mas permitir texto livre
            city_options = list(CITY_MAP.keys())
            place_choice = st.selectbox("Local de nascimento (atalho)", city_options, index=0)
            place_free = st.text_input("Ou digite o local (cidade, estado, país)", value=st.session_state.get("place_input", ""))
            # decidir qual usar: texto livre tem prioridade se preenchido
            place = place_free.strip() or place_choice

            # Fonte fixa
            source = "swisseph"
            st.session_state["source"] = source

            # opção de coordenadas manuais
            manual_coords = st.checkbox("Informar latitude/longitude manualmente?", value=False)
            if manual_coords:
                lat = st.number_input("Latitude", value=float(st.session_state.get("lat_manual", -23.6636)), format="%.6f")
                lon = st.number_input("Longitude", value=float(st.session_state.get("lon_manual", -46.5381)), format="%.6f")
            else:
                lat = None
                lon = None

            # opção de timezone manual
            manual_tz = st.checkbox("Escolher timezone manualmente?", value=False)
            if manual_tz:
                tz_name = st.text_input("Timezone (IANA)", value=st.session_state.get("tz_manual", ""))
            else:
                tz_name = None

            bdate = st.date_input(
                "Data de nascimento",
                value=st.session_state.get("bdate", date(1990, 1, 1)),
                min_value=date(1900, 1, 1),
                max_value=date(2100, 12, 31)
            )
            btime_free = st.text_input("Hora de nascimento (ex.: 14:30)", value=st.session_state.get("btime_text", ""))
            st.session_state["house_system"] = st.session_state.get("house_system", "P")
            use_ai = st.checkbox("Usar IA para interpretações?", value=st.session_state.get("use_ai", False))
            st.session_state["use_ai"] = use_ai
            submitted = st.form_submit_button("Gerar Mapa")

    # Single submit flow
    if submitted:
        # persistir entradas
        st.session_state["name"] = name
        st.session_state["place_input"] = place
        st.session_state["bdate"] = bdate
        st.session_state["btime_text"] = btime_free
        st.session_state["source"] = source

        # parse hora
        parsed_time = parse_time_string(btime_free or st.session_state.get("btime_text", ""))
        if parsed_time is None:
            st.error("Hora de nascimento inválida ou não informada. Use formatos como '14:30' ou '2:30 PM'.")
            st.session_state["map_ready"] = False
            return

        btime = parsed_time

        # resolver local: se não houver coords manuais, tentar CITY_MAP / geocoding
        if lat is None or lon is None:
            meta = CITY_MAP.get(place) or {}
            lat_meta = meta.get("lat")
            lon_meta = meta.get("lon")
            tz_meta = meta.get("tz")
            # preferir meta do CITY_MAP
            lat = lat_meta if lat is None else lat
            lon = lon_meta if lon is None else lon
            tz_name = tz_name or tz_meta

            # se ainda faltar coords, tentar geocoding
            if (lat is None or lon is None) and place:
                lat_res, lon_res, tz_guess, address = resolve_place_and_tz(place)
                lat = lat or lat_res
                lon = lon or lon_res
                tz_name = tz_name or tz_guess
                # salvar endereço resolvido
                address = address or st.session_state.get("address")
        else:
            # se coords manuais foram fornecidas, tentar inferir timezone se não informado
            address = st.session_state.get("address")
            if not tz_name and lat is not None and lon is not None:
                tz_guess = tz_from_latlon_cached(lat, lon)
                tz_name = tz_name or tz_guess

        # atualizar session_state com valores atuais
        st.session_state.update({"lat": lat, "lon": lon, "tz_name": tz_name, "address": address})

        # validar coords
        if lat is None or lon is None:
            st.warning("Latitude/Longitude não resolvidas automaticamente. Informe manualmente ou corrija o local.")
            st.session_state["map_ready"] = False
            return
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            st.error("Latitude/Longitude inválidas. Corrija os valores antes de gerar o mapa.")
            st.session_state["map_ready"] = False
            return

        # criar datetime timezone-aware com fallback por coordenadas
        dt_local, tz_ok = to_local_datetime_wrapper(bdate, btime, tz_name)
        if dt_local is None:
            tz_from_coords = tz_from_latlon_cached(lat, lon)
            tz_ok = normalize_tz_name(tz_from_coords) or tz_ok or normalize_tz_name(tz_name)
            if tz_ok:
                dt_local = make_datetime_with_tz(bdate, btime, tz_ok)

        # DEBUG VISÍVEL: sempre executado após tentativa de criar dt_local
        import pprint, traceback
        st.write("DEBUG: snapshot antes do cálculo natal")
        st.write(pprint.pformat(dict(st.session_state)))
        st.write("DEBUG: dt_local:", dt_local)
        st.write("DEBUG: dt_local tzinfo:", getattr(dt_local, "tzinfo", None))
        st.write("DEBUG: lat, lon:", lat, lon)
        st.write("DEBUG: tz_name (input):", tz_name)
        st.write("DEBUG: tz_ok (resolved):", tz_ok)
        st.write("DEBUG: source:", source)
        st.write("DEBUG: natal_positions callable:", callable(natal_positions))

        # persistir dt_local e tz
        st.session_state["tz_name"] = tz_ok
        st.session_state["dt_local"] = dt_local

        if dt_local is None:
            st.error("Não foi possível criar um datetime timezone-aware. Informe o timezone manualmente (IANA) ou corrija as coordenadas.")
            st.session_state["map_ready"] = False
            return

        st.success(f"Datetime local: {dt_local.isoformat()} (tz: {tz_ok})")

        # obter posições natales via swisseph (assumido disponível)
        planets = {}
        cusps = []
        logger.info("Iniciando obtenção de posições natales; source=swisseph")
        logger.info("Entrada para cálculo: name=%r, dt_local=%r, lat=%r, lon=%r, tz=%r", name, dt_local, lat, lon, tz_ok)
        try:
            data = natal_positions(dt_local, lat, lon, house_system=st.session_state.get("house_system", "P"))
            logger.info("natal_positions retornou tipo %s", type(data))
            planets = data.get("planets", {}) if isinstance(data, dict) else {}
            cusps = data.get("cusps", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.exception("Erro ao obter posições natales: %s", e)
            st.error("Erro ao calcular posições natales. Verifique os logs do servidor.")
            with st.expander("Detalhes do erro (debug)"):
                st.code(traceback.format_exc())
            st.session_state["map_ready"] = False
            return


#teste
        import pprint, traceback
        try:
            dt = st.session_state.get("dt_local")
            lat = st.session_state.get("lat")
            lon = st.session_state.get("lon")
            hs = st.session_state.get("house_system", "P")
            st.write("Chamando natal_positions com:", {"dt": dt, "lat": lat, "lon": lon, "house_system": hs})
            res = natal_positions(dt, lat, lon, house_system=hs)
            st.write("Tipo retornado:", type(res))
            st.write("Conteúdo (pprint):")
            st.code(pprint.pformat(res))
            if isinstance(res, dict):
                st.write("Chaves do dict:", list(res.keys()))
                st.write("Tipo de res['planets']:", type(res.get("planets")))
                st.code(pprint.pformat(res.get("planets")))
        except Exception:
            st.error("Erro ao chamar natal_positions; veja logs do servidor")
            st.code(traceback.format_exc())




        # processar resultado
        if not planets:
            st.warning("Não foi possível obter posições natales. Verifique as entradas e tente novamente.")
            st.session_state["map_ready"] = False
            return

        try:
            table = positions_table(planets) if positions_table else []
            aspects = compute_aspects(planets) if compute_aspects else []
            summary = generate_chart_summary(planets, name or "Consulente", bdate) if generate_chart_summary else {"planets": planets}
            summary["table"] = table
            summary["cusps"] = cusps
            summary["aspects"] = aspects
            summary.setdefault("place", place)
            summary.setdefault("bdate", bdate)
            summary.setdefault("btime", btime)
            summary.setdefault("lat", lat)
            summary.setdefault("lon", lon)
            summary.setdefault("timezone", tz_ok)
            summary = enrich_summary_with_astrology(summary) if enrich_summary_with_astrology else summary
            fig = render_wheel_plotly(summary.get("planets", {}), [c.get("longitude") for c in summary.get("table", [])] if summary.get("table") else [])
            st.session_state["map_fig"] = fig
            st.session_state["map_summary"] = summary
            st.session_state["map_ready"] = True
            st.sidebar.success("Mapa gerado com sucesso!")
        except Exception as e:
            logger.exception("Erro ao gerar summary/figura: %s", e)
            st.error("Erro ao processar dados astrológicos.")
            st.session_state["map_ready"] = False


    # Button to generate AI interpretation (separado)
    if st.sidebar.button("Gerar interpretação IA"):
        if not st.session_state.get("map_ready"):
            st.error("Gere o mapa primeiro antes de pedir a interpretação.")
        else:
            summary = st.session_state.get("map_summary")
            if not summary:
                st.error("Resumo do mapa ausente.")
            else:
                gs_mod = None
                try:
                    gs_mod = importlib.import_module("etheria.services.generator_service")
                except Exception:
                    try:
                        gs_mod = importlib.import_module("services.generator_service")
                    except Exception:
                        gs_mod = None
                if not gs_mod or not hasattr(gs_mod, "generate_interpretation_from_summary"):
                    st.error("Serviço de geração não disponível. Verifique generator_service.")
                else:
                    with st.spinner("Gerando interpretação via IA..."):
                        try:
                            res = gs_mod.generate_interpretation_from_summary(summary, generate_analysis, timeout_seconds=60)
                        except Exception as e:
                            logger.exception("Erro ao gerar interpretação IA: %s", e)
                            res = {"error": str(e)}
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

    # Render main UI (positions, map, interpretations)
    st.markdown("<h1 style='text-align:left'>Astrologia ♎</h1>", unsafe_allow_html=True)
    st.caption("Preencha os dados de nascimento no formulário lateral e clique em 'Gerar Mapa'.")

    # Retrieve summary and fig
    summary = st.session_state.get("map_summary")
    fig_saved = st.session_state.get("map_fig")
    map_ready = st.session_state.get("map_ready", False)

    left_col, center_col, right_col = st.columns([0.7, 2.0, 0.8])

    # LEFT: positions table and planet selector
    with left_col:
        st.markdown("### Posições")
        import pandas as _pd  # local import for optional dependency
        if summary:
            df = _pd.DataFrame(summary.get("table", []))
            if not df.empty and "planet" in df.columns:
                df_display = df.copy()
                def _planet_label_for_display(p):
                    try:
                        return influences.planet_label_pt(influences._to_canonical(p)) if influences and hasattr(influences, "planet_label_pt") else (influences._to_canonical(p) or p)
                    except Exception:
                        return p or "—"
                df_display["planet_label"] = df_display["planet"].apply(_planet_label_for_display)
                if "sign" in df_display.columns:
                    def _sign_label_for_display(s):
                        try:
                            can = influences.sign_to_canonical(s) if hasattr(influences, "sign_to_canonical") else s
                            return influences.sign_label_pt(can) if hasattr(influences, "sign_label_pt") else (can or s or "—")
                        except Exception:
                            return s or "—"
                    df_display["sign_label"] = df_display["sign"].apply(_sign_label_for_display)
            else:
                df = _pd.DataFrame([]) if df is None else df
                df_display = df.copy()
                if "planet" in df_display.columns and "planet_label" not in df_display.columns:
                    df_display["planet_label"] = df_display["planet"]
                if "sign" in df_display.columns and "sign_label" not in df_display.columns:
                    df_display["sign_label"] = df_display["sign"]
        else:
            df = _pd.DataFrame([])
            df_display = df

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
            cols_to_show = []
            for c in ["Planeta", "Signo", "Casa", "Graus"]:
                if c in df_to_show.columns:
                    cols_to_show.append(c)
            df_exp = df_to_show[cols_to_show].copy() if cols_to_show else df_to_show.copy()
            with st.expander("Tabela de posições", expanded=False):
                st.dataframe(df_exp, use_container_width=True, height=300)

            label_list = []
            label_to_raw = {}
            if not df_display.empty and "planet_label" in df_display.columns:
                raw_planets = list(df_display["planet"].values)
                planet_labels = list(df_display["planet_label"].values)
                for raw, plab in zip(raw_planets, planet_labels):
                    lab = f"{plab}"
                    label_list.append(lab)
                    label_to_raw[lab] = raw
            elif not df_display.empty and "planet" in df_display.columns:
                label_list = list(df_display["planet"].values)
                label_to_raw = {lab: lab for lab in label_list}
            else:
                label_list = []
                label_to_raw = {}

            if label_list:
                if "selected_planet" not in st.session_state or st.session_state.get("selected_planet") is None:
                    st.session_state["selected_planet"] = label_to_raw.get(label_list[0])
                if "planet_selectbox" not in st.session_state or st.session_state.get("planet_selectbox") is None:
                    current_internal = st.session_state.get("selected_planet")
                    current_label = next((lab for lab, raw in label_to_raw.items() if raw == current_internal), None)
                    st.session_state["planet_selectbox"] = current_label or label_list[0]
            else:
                st.session_state.setdefault("selected_planet", None)
                st.session_state.setdefault("planet_selectbox", None)

            def _on_select_planet():
                sel_label = st.session_state.get("planet_selectbox")
                sel_raw = label_to_raw.get(sel_label, sel_label)
                st.session_state["selected_planet"] = sel_raw
                st.session_state["planet_selectbox"] = sel_label

            st.selectbox(
                "Selecionar planeta",
                label_list,
                index=label_list.index(st.session_state.get("planet_selectbox")) if st.session_state.get("planet_selectbox") in label_list else 0,
                key="planet_selectbox",
                on_change=_on_select_planet
            )

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
                    canonical_sel = influences._to_canonical(sel_name) if influences and hasattr(influences, "_to_canonical") else sel_name
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
                            marker=dict(size=22, color="#b45b1f", line=dict(color="#000", width=0.5)),
                            text=[influences.CANONICAL_TO_PT.get(influences._to_canonical(sel_name), sel_name) if influences else sel_name],
                            textfont=dict(size=12, color="#000"),
                            hoverinfo="none",
                            showlegend=False
                        ))
                except Exception:
                    pass

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
                canonical_clicked = influences._to_canonical(clicked_planet) if influences and hasattr(influences, "_to_canonical") else clicked_planet
                if st.session_state.get("selected_planet") != canonical_clicked:
                    st.session_state["selected_planet"] = canonical_clicked

    # RIGHT: interpretations and arcanos
    with right_col:
        st.subheader("Interpretação dos Arcanos")
        st.caption("Cada elemento do mapa possui uma relação com os Arcanos Maiores.")
        tabs = st.tabs(["Planeta", "Signo"])
        selected_raw = st.session_state.get("selected_planet")
        def _canonical_and_label(name: Optional[str]):
            try:
                canonical = influences._to_canonical(name) if influences and hasattr(influences, "_to_canonical") else name
                label_pt = influences.CANONICAL_TO_PT.get(canonical, canonical) if influences and hasattr(influences, "CANONICAL_TO_PT") else canonical
                return canonical, label_pt
            except Exception:
                return name, name
        canonical_selected, label_selected = _canonical_and_label(selected_raw) if selected_raw else (None, None)
        reading = (summary.get("readings", {}) or {}).get(canonical_selected) if summary else None

        with tabs[0]:
            if reading:
                planet_label = (influences.CANONICAL_TO_PT.get(canonical_selected) if influences and hasattr(influences, "CANONICAL_TO_PT") else canonical_selected) or (label_selected or "—")
                raw_sign = reading.get("sign")
                try:
                    sign_canonical = influences.sign_to_canonical(raw_sign) if influences and hasattr(influences, "sign_to_canonical") else raw_sign
                except Exception:
                    sign_canonical = raw_sign
                sign_label = influences.sign_label_pt(sign_canonical) if influences and hasattr(influences, "sign_label_pt") else (sign_canonical or raw_sign or "—")
                degree = reading.get("degree") or reading.get("deg") or "—"
                st.markdown(f"#### {planet_label} em {sign_label} {degree}°")
                st.markdown("**Arcano Correspondente**")
                arc = reading.get("arcano_info") or reading.get("arcano")
                if arc:
                    if isinstance(arc, dict):
                        arc_name = arc.get("name") or f"Arcano {arc.get('arcano') or arc.get('value')}"
                        arc_num = arc.get("arcano") or arc.get("value")
                        st.write(f"{arc_name} (#{arc_num})")
                    else:
                        st.write(f"Arcano {arc}")
                st.markdown("**Resumo**")
                st.write(reading.get("interpretation_short") or "Resumo não disponível.")
                st.markdown("**Sugestões práticas**")
                kw = (arc.get("keywords") if isinstance(arc, dict) else []) if arc else []
                if kw:
                    for k in kw:
                        st.write(f"- {k}")
                else:
                    st.write("Nenhuma sugestão prática disponível.")
                with st.expander("Interpretação completa"):
                    st.write(reading.get("interpretation_long") or "Interpretação completa não disponível.")
            else:
                if not (canonical_selected and summary):
                    st.info("Selecione um planeta e gere o resumo do mapa para ver a análise por arcanos.")
                else:
                    st.info("Nenhuma leitura pré-gerada encontrada. Vá para a aba 'Signo' para gerar a interpretação automática.")

        with tabs[1]:
            client_name = st.session_state.get("client_name") or (summary.get("name") if summary else "Consulente")
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
                    for norm, raw_sign in sign_map.items():
                        display_sign = str(raw_sign).strip()
                        with st.expander(f"**{display_sign}**"):
                            try:
                                arc_res = interpretations.arcano_for_sign(raw_sign, name=client_name) if interpretations and hasattr(interpretations, "arcano_for_sign") else {"error": "serviço de arcano não disponível"}
                            except Exception as e:
                                arc_res = {"error": str(e)}
                            if arc_res.get("error"):
                                st.warning("Não foi possível gerar interpretação por signo: " + str(arc_res.get("error")))
                                if st.checkbox(f"Mostrar debug para {display_sign}", key=f"dbg_{norm}"):
                                    st.write(arc_res)
                            else:
                                text = arc_res.get("text") or ""
                                if not text.strip():
                                    st.write("Interpretação não disponível para este signo no momento.")
                                else:
                                    st.write(text)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("Erro ao executar main() diretamente")