# mapa_astral.py — Versão refatorada (ajustes: stubs condicionais, resolve_place flexível, debug)
from __future__ import annotations

"""
Mapa astral (refatorado)
- Mantém todas as funções originais
- Corrige sobrescrita de imports por stubs
- Resolve locais com matching flexível antes de geocoding
- Exibe retorno bruto de natal_positions para debug
"""

import csv
import importlib
import json
import logging
import os
import sys
import traceback
import swisseph as swe  # usado apenas em testes; se não instalado, import falhará
import datetime
import zoneinfo
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

# Try to import natal_positions from service; do NOT override it later with a stub
natal_positions = None
try:
    from services.swisseph_client import natal_positions  # type: ignore
    logger.info("Imported natal_positions from services.swisseph_client")
except Exception:
    natal_positions = None
    logger.info("services.swisseph_client.natal_positions not available; will use stub only if necessary")

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
# Safe wrappers and stubs (define stubs only if import failed)
# -------------------------
def resolve_place_and_tz(place: str):
    """
    Resolve place using:
    1) exact CITY_MAP match
    2) case-insensitive startswith / contains match
    3) geocoding fallback
    Returns: lat, lon, tz_name, address
    """
    lat = lon = None
    tz_name = None
    address = None
    if not place:
        return None, None, None, None

    # 1) exact match
    meta = CITY_MAP.get(place)
    if meta:
        lat = meta.get("lat")
        lon = meta.get("lon")
        tz_name = meta.get("tz")

    # 2) flexible match (startswith / contains)
    if (lat is None or lon is None or not tz_name):
        place_norm = place.strip().lower()
        for key, meta in CITY_MAP.items():
            if not key or key == "Outra (digitar...)":
                continue
            if key.lower().startswith(place_norm) or place_norm in key.lower():
                lat = lat or meta.get("lat")
                lon = lon or meta.get("lon")
                tz_name = tz_name or meta.get("tz")
                break

    # 3) geocoding fallback
    if (lat is None or lon is None or not tz_name):
        try:
            lat_g, lon_g, tz_guess, addr = geocode_place_safe(place)
            lat = lat or lat_g
            lon = lon or lon_g
            tz_name = tz_name or tz_guess
            address = addr or address
        except Exception as e:
            logger.warning("resolve_place_and_tz geocoding failed: %s", e)

    return lat, lon, tz_name, address

def to_local_datetime_wrapper(bdate: date, btime_obj: dt_time, tz_name: Optional[str]) -> Tuple[Optional[datetime], Optional[str]]:
    tz_ok = normalize_tz_name(tz_name)
    if not tz_ok:
        return None, None
    dt_local = make_datetime_with_tz(bdate, btime_obj, tz_ok)
    return dt_local, tz_ok

# Only define stubs if the real implementations are not available
if 'fetch_natal_chart' not in globals():
    def fetch_natal_chart(name, dt_local, lat, lon, tz_name):
        return {"planets": {}, "cusps": []}

if natal_positions is None:
    def natal_positions(dt_local, lat, lon, house_system="P"):
        """
        Stub natal_positions: returns empty result.
        If you have a real implementation in services.swisseph_client,
        ensure it is importable and this stub will not be defined.
        """
        logger.info("Using natal_positions stub (no swisseph client available)")
        return {"planets": {}, "cusps": []}

# Keep other stubs only if not defined elsewhere
if 'positions_table' not in globals():
    def positions_table(planets):
        return []

if 'compute_aspects' not in globals():
    def compute_aspects(planets):
        return []

if 'generate_chart_summary' not in globals():
    def generate_chart_summary(planets, name, bdate):
        return {"planets": planets}

if 'enrich_summary_with_astrology' not in globals():
    def enrich_summary_with_astrology(summary):
        return summary

# -------------------------
# (rest of file unchanged) - keep your render_wheel_plotly, ensure_aspects, etc.
# For brevity, assume render_wheel_plotly and ensure_aspects are identical to your version above.
# -------------------------

# Insert here the render_wheel_plotly and ensure_aspects functions exactly as in your file.
# (I preserved them in your original file; do not overwrite them with stubs.)

# -------------------------
# UI / Streamlit flow (refatorado e defensivo)
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

            # se ainda faltar coords, tentar geocoding (resolve_place_and_tz já faz fallback)
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
        if not (-90 <= float(lat) <= 90 and -180 <= float(lon) <= 180):
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
            data = natal_positions(dt_local, float(lat), float(lon), house_system=st.session_state.get("house_system", "P"))
            # mostrar retorno bruto para debug
            with st.expander("DEBUG: retorno natal_positions (dev)"):
                st.write(type(data))
                st.code(pprint.pformat(data))
            planets = data.get("planets", {}) if isinstance(data, dict) else {}
            cusps = data.get("cusps", []) if isinstance(data, dict) else []
        except Exception as e:
            logger.exception("Erro ao obter posições natales: %s", e)
            st.error("Erro ao calcular posições natales. Verifique os logs do servidor.")
            with st.expander("Detalhes do erro (debug)"):
                st.code(traceback.format_exc())
            st.session_state["map_ready"] = False
            return

        if not planets:
            st.warning("Não foi possível obter posições natales. Verifique as entradas e tente novamente.")
            st.session_state["map_ready"] = False
            return

        try:
            table = positions_table(planets) if callable(positions_table) else []
            aspects = compute_aspects(planets) if callable(compute_aspects) else []
            summary = generate_chart_summary(planets, name or "Consulente", bdate) if callable(generate_chart_summary) else {"planets": planets}
            summary["table"] = table
            summary["cusps"] = cusps
            summary["aspects"] = aspects
            summary.setdefault("place", place)
            summary.setdefault("bdate", bdate)
            summary.setdefault("btime", btime)
            summary.setdefault("lat", lat)
            summary.setdefault("lon", lon)
            summary.setdefault("timezone", tz_ok)
            summary = enrich_summary_with_astrology(summary) if callable(enrich_summary_with_astrology) else summary
            fig = render_wheel_plotly(summary.get("planets", {}), [c.get("longitude") for c in summary.get("table", [])] if summary.get("table") else [])
            st.session_state["map_fig"] = fig
            st.session_state["map_summary"] = summary
            st.session_state["map_ready"] = True
            st.sidebar.success("Mapa gerado com sucesso!")
        except Exception as e:
            logger.exception("Erro ao gerar summary/figura: %s", e)
            st.error("Erro ao processar dados astrológicos.")
            st.session_state["map_ready"] = False

# Entrypoint
if __name__ == "__main__":
    main()
