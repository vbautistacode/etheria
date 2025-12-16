# pages/mapa_astral.py
def main():

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
    def render_wheel_plotly(
        planets: dict,
        cusps: list,
        *,
        highlight_groups: dict = None,
        house_label_position: str = "inner",  # "inner", "mid", "outer"
        marker_scale: float = 1.4,
        text_scale: float = 1.2,
        cusp_colors_by_quadrant: list = None,
        export_png: bool = False,
        export_size: tuple = (2400, 2400)
    ):
        """
        Renderiza roda astrológica com recursos avançados.

        Args:
        planets: dict nome -> (float | str | dict{lon, sign, house})
        cusps: list de longitudes (preferencialmente 12)
        highlight_groups: dict nome_grupo -> list[nomes_de_planetas]
            Ex.: {"pessoais":["Sun","Moon","Mercury","Venus","Mars"], "sociais":["Jupiter","Saturn","Uranus","Neptune","Pluto"]}
        house_label_position: "inner"|"mid"|"outer" define r para números das casas
        marker_scale: multiplicador para tamanhos dos marcadores
        text_scale: multiplicador para textos
        cusp_colors_by_quadrant: lista de 4 cores para quadrantes (se None usa padrão)
        export_png: se True retorna (fig, png_bytes) em vez de só fig
        export_size: (width, height) em pixels para export PNG
        Returns:
        fig ou (fig, png_bytes) se export_png True.
        """
        if not PLOTLY_AVAILABLE:
            logger.warning("Plotly não disponível; render_wheel_plotly retornará None")
            return None

        try:
            import plotly.graph_objects as go
        except Exception:
            return None

        import math, logging, unicodedata
        logger = logging.getLogger("render_wheel_plotly")

        # defaults
        if cusp_colors_by_quadrant is None:
            cusp_colors_by_quadrant = ["#6E6E6E52", "#6E6E6E52", "#6E6E6E52", "#6E6E6E52"]  # 4 tons distintos

        # helper: extrair longitude
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

        def lon_to_theta(lon_deg):
            return (360.0 - float(lon_deg)) % 360.0

        # símbolos
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
            "Asc": "ASC", "ASCENDANT": "ASC", "ASCENDENTE": "ASC",
            "MC": "MC", "Medium Coeli": "MC", "Meio do Céu": "MC"
        }

        # destacar grupos
        groups = highlight_groups or {
            "pessoais": ["Sun", "Moon", "Mercury", "Venus", "Mars"],
            "sociais": ["Jupiter", "Saturn"],
            "geracionais": ["Uranus", "Neptune", "Pluto"]
        }
        # cores por grupo (padrão)
        group_colors = {
            "pessoais": "#ffcfa4",
            "sociais": "#83a1b6",
            "geracionais": "#886eb3"
        }

        # ordenar por longitude
        ordered = sorted(valid_planets.items(), key=lambda kv: kv[1])
        names = []
        thetas = []
        hover_texts = []
        symbol_texts = []
        lon_values = []
        marker_sizes = []
        text_sizes = []
        marker_colors = []

        for name, lon in ordered:
            try:
                theta = lon_to_theta(lon)
            except Exception:
                logger.warning("Falha ao converter longitude para theta: %s -> %s", name, lon)
                continue

            lname = str(name).lower()
            is_asc = lname in ("asc", "ascendant", "ascendente")
            is_mc = lname in ("mc", "medium coeli", "meio do ceu", "meio do céu")

            sign_index = int(float(lon) // 30) % 12
            degree_in_sign = float(lon) % 30

            meta = planet_meta.get(name, {}) or {}
            meta_sign = meta.get("sign")
            meta_house = meta.get("house")

            hover_parts = [f"<b>{name}</b>", f"{lon:.2f}° eclíptico", f"{degree_in_sign:.1f}° no signo"]
            if meta_sign:
                hover_parts.append(f"Signo (meta): {meta_sign}")
            sign_names_short = ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]
            hover_parts.append(f"Signo (calc): {sign_names_short[sign_index]}")
            if meta_house:
                hover_parts.append(f"Casa (meta): {meta_house}")
            hover_text = "<br>".join(hover_parts)

            symbol = planet_symbols.get(name, planet_symbols.get(name.capitalize(), name))
            # base sizes aumentadas e escaláveis
            base_marker = 26 * marker_scale
            base_text = 16 * text_scale
            size = base_marker * (1.6 if is_asc or is_mc else 1.0)
            text_size = base_text * (1.4 if is_asc or is_mc else 1.0)

            # cor por grupo se aplicável
            color = "#888"  # default neutro
            for gname, members in groups.items():
                if name in members:
                    color = group_colors.get(gname, "#ff7f0e")
                    break
            # destaque Asc/MC
            if is_asc:
                color = "#d62728"
            if is_mc:
                color = "#9467bd"

            names.append(name)
            thetas.append(theta)
            lon_values.append(float(lon))
            hover_texts.append(hover_text)
            symbol_texts.append(symbol)
            marker_sizes.append(size)
            text_sizes.append(text_size)
            marker_colors.append(color)

        fig = go.Figure()

        # marcadores com tamanhos individuais
        fig.add_trace(go.Scatterpolar(
            r=[1.0]*len(thetas),
            theta=thetas,
            mode="markers+text",
            marker=dict(size=marker_sizes, color=marker_colors, line=dict(color="#222", width=1.5)),
            text=symbol_texts,
            textfont=dict(size=int(14 * text_scale), family="DejaVu Sans, Arial"),
            hovertext=hover_texts,
            hovertemplate="%{hovertext}<extra></extra>",
            customdata=names,
            name="Planetas"
        ))

        # nomes dos planetas (mais afastados)
        fig.add_trace(go.Scatterpolar(
            r=[1.18]*len(thetas),
            theta=thetas,
            mode="text",
            text=names,
            textfont=dict(size=int(12 * text_scale), color="#111"),
            hoverinfo="none",
            showlegend=False
        ))

        # desenhar linhas das cúspides com cores por quadrante
        if valid_cusps:
            # garantir 12 cusps: se menos, usar fallback
            cusps12 = valid_cusps if len(valid_cusps) >= 12 else [(i*30.0) for i in range(12)]
            for i, cusp in enumerate(cusps12, start=1):
                theta_cusp = lon_to_theta(cusp)
                # cor por quadrante (cada 3 casas)
                quadrant = ((i-1) // 3) % 4
                color = cusp_colors_by_quadrant[quadrant]
                fig.add_trace(go.Scatterpolar(
                    r=[0.12, 1.0],
                    theta=[theta_cusp, theta_cusp],
                    mode="lines",
                    line=dict(color=color, width=2.0, dash="solid"),
                    hoverinfo="none",
                    showlegend=False
                ))

            # numerar casas no meio entre cúspides com posição configurável
            if len(cusps12) >= 12:
                for i in range(12):
                    c1 = cusps12[i]
                    c2 = cusps12[(i+1) % 12]
                    # meio angular
                    mid = ( (c1 + ((c2 - c1) % 360) / 2) ) % 360
                    theta_mid = lon_to_theta(mid)
                    # escolher r para label
                    if house_label_position == "inner":
                        r_label = 0.6
                    elif house_label_position == "mid":
                        r_label = 0.9
                    else:
                        r_label = 1.03
                    fig.add_trace(go.Scatterpolar(
                        r=[r_label],
                        theta=[theta_mid],
                        mode="text",
                        text=[str(i+1)],
                        textfont=dict(size=int(12 * text_scale), color="#222"),
                        hoverinfo="none",
                        showlegend=False
                    ))
            else:
                # fallback: posições padrão
                for i in range(12):
                    mid = (i * 30 + 15) % 360
                    theta_mid = lon_to_theta(mid)
                    r_label = 1.03 if house_label_position == "outer" else (0.9 if house_label_position == "mid" else 0.6)
                    fig.add_trace(go.Scatterpolar(
                        r=[r_label],
                        theta=[theta_mid],
                        mode="text",
                        text=[str(i+1)],
                        textfont=dict(size=int(12 * text_scale), color="#222"),
                        hoverinfo="none",
                        showlegend=False
                    ))

        # aspectos (mesma lógica, mantendo visual aumentado)
        if len(lon_values) >= 2:
            ASPECTS = [
                ("Conjunção", 0, 8, "#222222", 3.0),
                ("Sextil", 60, 6, "#2ca02c", 2.0),
                ("Quadratura", 90, 7, "#e05353", 2.4),
                ("Trígono", 120, 7, "#1f77b4", 2.4),
                ("Oposição", 180, 8, "#ff0000", 2.8),
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
                                opacity=0.65,
                                hoverinfo="none",
                                showlegend=False
                            ))
                            break

        # ticks e labels dos signos
        sign_names = ["Áries","Touro","Gêmeos","Câncer","Leão","Virgem","Libra","Escorpião","Sagitário","Capricórnio","Aquário","Peixes"]
        sign_symbols = ["♈","♉","♊","♋","♌","♍","♎","♏","♐","♑","♒","♓"]
        tickvals = [(360.0 - (i * 30 + 15)) % 360.0 for i in range(12)]
        ticktext = [f"{sign_symbols[i]} {sign_names[i]}" for i in range(12)]

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=False),
                angularaxis=dict(direction="clockwise", rotation=90,
                                tickmode="array", tickvals=tickvals, ticktext=ticktext,
                                tickfont=dict(size=int(12 * text_scale)), gridcolor="#eee")
            ),
            showlegend=False,
            margin=dict(l=10, r=10, t=30, b=10),
            height=export_size[1] if export_png else int(700 * (export_size[1]/1200 if export_png else 1)),
            width=export_size[0] if export_png else None
        )
        fig.update_traces(textfont=dict(size=int(14 * text_scale)))

        # export opcional em alta resolução (requer kaleido)
        if export_png:
            try:
                img_bytes = fig.to_image(format="png", width=export_size[0], height=export_size[1], scale=1)
                return fig, img_bytes
            except Exception as e:
                logger.exception("Falha ao exportar PNG: %s", e)
                return fig

        return fig

    st.markdown("<h1 style='text-align:left'>Astrologia ♎ </h1>", unsafe_allow_html=True)
    st.caption("Preencha os dados de nascimento no formulário lateral e clique em 'Gerar Mapa'.")

    st.markdown(
        """
        A Astrologia em *Etheria* é vista como a linguagem silenciosa do cosmos que pulsa em sintonia com nossa 
        própria existência. Mais do que previsões, os astros oferecem um **mapa de potencialidades**: a posição 
        dos planetas no momento do seu nascimento atua como uma bússola vibracional, influenciando temperamentos, 
        desafios e o florescer de talentos únicos.

        Ao compreender as energias arquetípicas que regem seu mapa, você deixa de apenas reagir ao destino e passa 
        a **cocriar com o universo**. Cada trânsito e aspecto é um convite para o autoconhecimento, revelando que 
        o que está em cima, nos céus, reflete diretamente o que vibra dentro de você.
        """
    )
    # -------------------- UI --------------------
    
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
    PAGE_ID = "mapa_astral"  # identifique a página; troque se necessário

    st.sidebar.header("Entrada do Consulente")
    with st.sidebar:
        form_key = f"birth_form_sidebar_{PAGE_ID}"
        with st.form(key=form_key, border=False):
            name = st.text_input("Nome", value="")
            place = st.text_input(
                "Cidade de nascimento (ex: São Paulo, Brasil)",
                value="São Paulo, São Paulo, Brasil"
            )
            bdate = st.date_input(
                "Data de nascimento",
                value=date(1990, 4, 25),
                min_value=date(1900, 1, 1),
                max_value=date(2100, 12, 31)
            )
            btime_free = st.text_input(
                "Hora de nascimento (hora local) (ex.: 14:30, 2:30 PM)",
                value=""
            )
            source = "swisseph"
            # Sistema de casas fixo: Placidus (código P)
            st.session_state["house_system"] = "P"

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

    # --- Substituir chamadas automáticas por preparação e delegação ao botão de IA ---
    # após salvar st.session_state["map_summary"] e st.session_state["map_ready"] = True
    # NÃO chamar generate_analysis aqui. Apenas preparar e salvar summary.

    # preparar preview_positions para o sidebar (usar normalize do generator_service)
    try:
        from etheria.services import generator_service as gs
    except Exception:
        gs = None

        # botão único para gerar interpretação IA (usa rotina centralizada com validação e timeout)
        if st.sidebar.button("Gerar interpretação IA"):
            if not gs or not hasattr(gs, "generate_interpretation_from_summary"):
                st.error("Serviço de geração não disponível. Verifique generator_service.")
            else:
                # chamar rotina que normaliza, valida, mostra prompt preview e executa com timeout
                res = gs.generate_interpretation_from_summary(st.session_state["map_summary"], generate_analysis, timeout_seconds=60)
                if res.get("error"):
                    st.error(res["error"])
                else:
                    analysis_text = res.get("analysis_text") or res.get("text") or ""
                    if analysis_text:
                        st.markdown("### Interpretação gerada")
                        st.markdown(analysis_text)
                    else:
                        st.info("Nenhuma interpretação retornada pelo serviço.")

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
            "Usar IA para interpretações astrológicas",
            value=False,
            help="Gera texto via IA Generativa proprietária."
        )

        st.markdown("### Posições")
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

                st.markdown(f"**{reading.get('planet') or label}**")
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
        st.subheader("Mapa Astral")
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

    # UI: geração IA com proteção e envio controlado
    if use_ai:
        st.markdown("#### Interpretação IA Etheria")

        # importar generator_service de forma resiliente
        try:
            from etheria.services import generator_service as gs
        except Exception:
            gs = None

        if not gs:
            st.info("Serviço de geração não disponível.")
        else:
            # flag para evitar cliques repetidos
            if "generating" not in st.session_state:
                st.session_state["generating"] = False

            # botão de geração
            if st.session_state["generating"]:
                st.button("Gerando... (aguarde)", disabled=True)
            else:
                if st.button("Gerar interpretação IA", key="gen_ai_button"):
                    st.session_state["generating"] = True

                    # chamada ao serviço (defensiva)
                    try:
                        with st.spinner("Gerando sua interpretação personalizada com IA Etheria"):
                            if hasattr(gs, "generate_interpretation_from_summary"):
                                res = gs.generate_interpretation_from_summary(summary, generate_analysis, timeout_seconds=60)
                            elif hasattr(gs, "generate_analysis"):
                                res = gs.generate_analysis(summary, prefer="auto", text_only=True, model="gemini-2.5-flash")
                            else:
                                res = {"error": "Serviço indisponível"}
                    except Exception as e:
                        logger.exception("Erro ao chamar serviço de geração: %s", e)
                        res = {"error": str(e)}

                    # garantir que res é dict e normalizar campos esperados
                    if not isinstance(res, dict):
                        logger.warning("Resposta do serviço não é dict: %r — normalizando para dict", res)
                        res = {"error": "Resposta inválida do serviço", "raw_response": str(res)}

                    # garantir chaves mínimas para evitar AttributeError e fallback silencioso
                    res.setdefault("error", None)
                    res.setdefault("analysis_text", "")
                    res.setdefault("analysis_json", None)
                    res.setdefault("svg", "")
                    res.setdefault("source", "unknown")
                    res.setdefault("raw_text", res.get("raw_text") or "")

                    # agora é seguro usar res.get(...)
                    if res.get("error"):
                        with st.expander("Detalhes do erro"):
                            st.warning("Não foi possível gerar a interpretação via serviço.")
                            st.write(res.get("error"))
                    else:
                        ai_text = (res.get("analysis_text") or res.get("text") or res.get("raw_text") or "").strip()
                        parsed = res.get("analysis_json") or res.get("analysis") or None

                        # fallback legível para o usuário (sempre preencher algo)
                        if not ai_text:
                            ai_text = f"{summary.get('name','Interpretação')}: interpretação não disponível no momento. Verifique a configuração de IA ou tente novamente."

                        # exibir
                        if res.get("error"):
                            with st.expander("Detalhes do erro"):
                                st.warning("Não foi possível gerar a interpretação via serviço.")
                                st.write(res.get("error"))
                        else:
                            st.success("Interpretação IA gerada" if ai_text else "Interpretação IA (fallback)")
                            st.markdown("#### Interpretação IA")
                            st.write(ai_text)

                        if ai_text:
                            st.success("Interpretação IA gerada")
                            st.markdown("#### Interpretação IA")
                            st.write(ai_text)
                            st.download_button(
                                "Exportar interpretação(.txt)",
                                data=ai_text,
                                file_name=f"interpretacao_ia.txt",
                                mime="text/plain"
                            )
                        if parsed:
                            with st.expander("Ver JSON estruturado (expandir)"):
                                st.json(parsed)
                                st.download_button(
                                    "Baixar JSON",
                                    data=json.dumps(parsed, ensure_ascii=False, indent=2),
                                    file_name=f"interpretacao_ia.json",
                                    mime="application/json"
                                )
                        if not ai_text and not parsed:
                            st.info("Geração concluída, mas não houve texto de interpretação. Verifique configuração de IA ou use templates locais.")

    # RIGHT: painel de análise
    with right_col:
        st.subheader("Interpretação dos Arcanos")
        st.caption("Cada elemento do mapa possui uma relação com os Arcanos Maiores. " \
        "A partir da posição dos planetas, veja abaixo, quais signos são influenciados:")

        # criar duas abas: 0 = Interpretação via Arcanos (leitura ou geração),
        # 1 = Influência Arcano x Signo (geração via interpretations.arcano_for_planet)
        tabs = st.tabs(["Planeta", "Signo"])

        # dados selecionados
        selected_raw = st.session_state.get("selected_planet")
        canonical_selected, label_selected = _canonical_and_label(selected_raw) if selected_raw else (None, None)

        # preparar leitura existente (se houver)
        reading = summary.get("readings", {}).get(canonical_selected) if summary else None

        # -------------------------
        # Aba 0: Interpretação via Arcanos (usar leitura já gerada quando disponível)
        # -------------------------
        with tabs[0]:
            if reading:
                st.markdown(
                    f"#### {influences.CANONICAL_TO_PT.get(canonical_selected, canonical_selected)} "
                    f"em {reading.get('sign')} {reading.get('degree')}°"
                )
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
                with st.expander("Interpretação completa"):
                    st.write(reading.get("interpretation_long") or "Interpretação completa não disponível.")
                st.markdown("**Sugestões práticas**")
                kw = (arc.get("keywords") if isinstance(arc, dict) else []) if arc else []
                if kw:
                    for k in kw:
                        st.write(f"- {k}")
                else:
                    st.write("Nenhuma sugestão prática disponível.")
            else:
                # sem leitura pré-gerada: instruir usuário ou gerar via arcano_for_planet (opcional)
                if not (canonical_selected and summary):
                    st.info("Selecione um planeta (na tabela ou na roda) e gere o resumo do mapa para ver a análise por arcanos.")
                else:
                    st.info("Nenhuma leitura pré-gerada encontrada. Vá para a aba 'Influencia Arcano x Signo' para gerar a interpretação automática.")

        # -------------------------
        # Aba 1: Influencia Arcano x Signo (gerar via interpretations.arcano_for_planet)
        # -------------------------
            with tabs[1]:
                # obter nome do consulente (priorizar campo do sidebar)
                client_name = st.session_state.get("client_name") or summary.get("name") if summary else "Consulente"

                if not summary:
                    st.info("Resumo do mapa não disponível. Gere o mapa antes de ver a influência por signo.")
                else:
                    table = summary.get("table", []) or []

                    # construir mapa norm -> primeiro raw encontrado (preserva forma original)
                    sign_map: Dict[str, str] = {}
                    for row in table:
                        raw = row.get("sign") or row.get("zodiac")
                        if not raw:
                            continue
                        norm = interpretations._normalize_sign(raw)
                        if not norm:
                            continue
                        if norm not in sign_map:
                            sign_map[norm] = raw

                    if not sign_map:
                        st.info("Nenhum signo detectado no mapa.")
                    else:
                        # iterar em ordem de aparição
                        for norm, raw_sign in sign_map.items():
                            display_sign = str(raw_sign).strip()
                            # criar expander por signo (abre/fecha)
                            with st.expander(f"**{display_sign}**"):
                                # gerar interpretação (arcano_for_sign normaliza internamente)
                                arc_res = interpretations.arcano_for_sign(raw_sign, name=client_name)

                                # título com arcano (se disponível)
                                arcano_label = arc_res.get("arcano") or "—"
                                #st.markdown(f"**Arcano: {arcano_label}**")

                                # erro ou texto
                                if arc_res.get("error"):
                                    st.warning("Não foi possível gerar interpretação por signo: " + str(arc_res["error"]))
                                    # opção de debug por expander
                                    if st.checkbox(f"Mostrar debug para {display_sign}", key=f"dbg_{norm}"):
                                        st.write(arc_res)
                                else:
                                    text = arc_res.get("text") or ""
                                    if not text.strip():
                                        st.write("Interpretação não disponível para este signo no momento.")
                                    else:
                                        st.write(text)
                                        
# permite executar diretamente para desenvolvimento
if __name__ == "__main__":
    main()