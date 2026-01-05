# services/swisseph_client.py
from __future__ import annotations
import os
import logging
import swisseph as swe
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Caminho padrão relativo ao projeto (pasta services/ephe)
DEFAULT_EPHE_DIR = os.path.join(os.path.dirname(__file__), "ephe")
EPHE_PATH = os.getenv("EPHE_PATH", DEFAULT_EPHE_DIR)

if not os.path.isdir(EPHE_PATH):
    logger.warning("EPHE_PATH não existe: %s. Verifique se os arquivos de efemérides estão em services/ephe", EPHE_PATH)

try:
    swe.set_ephe_path(EPHE_PATH)
    logger.info("SwissEphemeris: set_ephe_path('%s')", EPHE_PATH)
except Exception as e:
    os.environ.setdefault("SWEPH", EPHE_PATH)
    os.environ.setdefault("SWE_DATA", EPHE_PATH)
    logger.warning("Falha ao chamar swe.set_ephe_path: %s. Definido SWEPH/SWE_DATA=%s como fallback.", e, EPHE_PATH)

# IDs de planetas conforme convenção Swiss Ephemeris
# Nomes de planetas em português (códigos inteiros)
# logo após import swisseph as swe
PLANET_CODES = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mercury": swe.MERCURY, "Venus": swe.VENUS,
    "Mars": swe.MARS, "Jupiter": swe.JUPITER, "Saturn": swe.SATURN,
    "Uranus": swe.URANUS, "Neptune": swe.NEPTUNE, "Pluto": swe.PLUTO
}
PLANETS = list(PLANET_CODES.values())
PLANET_NAMES = {code: name for name, code in PLANET_CODES.items()}

# Signos em português
ZODIAC_SIGNS = [
    "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem",
    "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"
]

def julian_day_utc(dt: datetime) -> float:
    """
    Converte um datetime para Julian Day UT.
    Se dt.tzinfo for None, assume UTC; se tiver tzinfo, converte para UTC.
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt deve ser datetime")
    if dt.tzinfo is None:
        dt_utc = dt.replace(tzinfo=timezone.utc)
    else:
        dt_utc = dt.astimezone(timezone.utc)
    hours = dt_utc.hour + dt_utc.minute / 60.0 + dt_utc.second / 3600.0 + dt_utc.microsecond / 3_600_000_000.0
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day, hours)

def normalize_longitude(lon: float) -> float:
    """Normaliza longitude para [0, 360)."""
    return lon % 360.0

def longitude_to_sign_degree(lon: float) -> Tuple[str, float]:
    """
    Converte longitude eclíptica (0..360) para (sign_name, degree_in_sign).
    Ex.: 34.5 -> ("Taurus", 4.5) porque 30..60 é Touro.
    """
    lon = normalize_longitude(lon)
    sign_index = int(lon // 30)  # 0..11
    degree_in_sign = lon - (sign_index * 30)
    sign_name = ZODIAC_SIGNS[sign_index]
    return sign_name, degree_in_sign

def _normalize_calc_result(res) -> Tuple[List[float], Optional[int]]:
    if isinstance(res, (tuple, list)) and len(res) == 2 and isinstance(res[0], (list, tuple)):
        vals = list(res[0]); flag = res[1]
    else:
        vals = list(res); flag = None
    vals = [float(v) for v in vals]
    return vals, flag

def _prepare_house_system(house_system: str | bytes) -> str:
    if isinstance(house_system, (bytes, bytearray)):
        house_system = house_system.decode("ascii")
    if not isinstance(house_system, str) or len(house_system) != 1:
        raise ValueError("house_system deve ser um caractere único, ex.: 'P'")
    return house_system

def _find_planet_house(planet_lon: float, cusps: List[float]) -> int:
    """
    Determina a casa (1..12) de um planeta dado sua longitude e a lista de cúspides.
    A lista 'cusps' deve conter 13 elementos onde index 1..12 são as cúspides das casas.
    Retorna 1..12. Usa lógica circular para cúspides que cruzam 0°.
    """
    lon = normalize_longitude(planet_lon)
    # cusps expected as list-like with 13 entries (0 unused or 1..12)
    # Some swe.houses returns 13 items with index 1..12 meaningful.
    # We'll build intervals [cusp[i], cusp[i+1]) modulo 360
    n = len(cusps)
    if n < 12:
        raise ValueError("cusps deve conter pelo menos 12 valores")
    # ensure we have 13 entries with dummy at index 0 if necessary
    if len(cusps) == 12:
        # convert to 1-based by inserting dummy at start
        cusps = [0.0] + list(cusps)
    # build intervals
    for i in range(1, 13):
        start = normalize_longitude(cusps[i])
        end = normalize_longitude(cusps[1] if i == 12 else cusps[i+1])
        if start <= end:
            if start <= lon < end:
                return i
        else:
            # interval wraps around 360
            if lon >= start or lon < end:
                return i
    # fallback: if not found, return 12
    return 12

def natal_positions(dt: datetime, lat: float, lon: float, house_system: str | bytes = 'P') -> Dict[str, Any]:
    """
    Calcula posições planetárias, signos, graus e cúspides.

    Args:
      dt: datetime em UTC (ou com tzinfo; será convertido para UTC)
      lat, lon: coordenadas em graus decimais (lat positivo norte, lon positivo leste)
      house_system: caractere único indicando sistema de casas (ex.: 'P' Placidus)

    Returns:
      dict com:
        - jd: julian day UT
        - planets: dict por planeta com keys: longitude, latitude, distance, flag, sign, degree_in_sign, house
        - cusps: lista de 13 valores (index 1..12 úteis)
        - asc_mc: [ascendant_deg, mc_deg]
    """
    if not isinstance(dt, datetime):
        raise TypeError("dt deve ser datetime")

    jd = julian_day_utc(dt)
    planets: Dict[str, Dict[str, Any]] = {}

    for p in PLANETS:
        try:
            raw = swe.calc_ut(jd, p)
        except Exception as exc:
            logger.exception("Erro ao calcular posição do planeta %s: %s", p, exc)
            raise

        vals, flag = _normalize_calc_result(raw)
        if len(vals) < 3:
            logger.error("Resultado inesperado de swe.calc_ut para %s: %r", p, raw)
            raise RuntimeError(f"Resultado inesperado de swe.calc_ut para {p}")

        lon_deg = normalize_longitude(vals[0])
        lat_deg = vals[1]
        dist = vals[2]

        sign_name, deg_in_sign = longitude_to_sign_degree(lon_deg)

        planets[PLANET_NAMES.get(p, str(p))] = {
            "longitude": lon_deg,
            "latitude": lat_deg,
            "distance": dist,
            "flag": flag,
            "sign": sign_name,
            "degree_in_sign": round(deg_in_sign, 4),
            # house will be filled after cusps are computed
            "house": None
        }

    # casas e ascendente/MC
    try:
        hsys = _prepare_house_system(house_system)
        cusps_res, ascmc = swe.houses(jd, lat, lon, hsys)
        # swe.houses normalmente retorna (cusps, ascmc) onde cusps é lista index 1..12
        cusps = list(cusps_res)
        asc_mc = list(ascmc)
    except Exception as exc:
        logger.exception("Erro ao calcular casas: %s", exc)
        raise

    # Normalizar cusps para ter índice 1..12 (inserir dummy 0 se necessário)
    if len(cusps) == 12:
        cusps = [0.0] + cusps
    elif len(cusps) > 13:
        # reduzir para 13 se houver extras
        cusps = cusps[:13]

    # Preencher casa de cada planeta
    for pname, pdata in planets.items():
        try:
            house_num = _find_planet_house(pdata["longitude"], cusps)
            planets[pname]["house"] = house_num
        except Exception as exc:
            logger.exception("Erro ao determinar casa para %s: %s", pname, exc)
            planets[pname]["house"] = None

    # Também expor ascendente e MC em formato legível
    asc_deg = normalize_longitude(asc_mc[0]) if len(asc_mc) > 0 else None
    mc_deg = normalize_longitude(asc_mc[1]) if len(asc_mc) > 1 else None
    asc_sign, asc_deg_in_sign = (None, None)
    if asc_deg is not None:
        asc_sign, asc_deg_in_sign = longitude_to_sign_degree(asc_deg)

    return {
        "jd": jd,
        "planets": planets,
        "cusps": cusps,          # index 1..12 úteis
        "asc_mc": asc_mc,        # raw asc/MC degrees
        "ascendant": {
            "longitude": asc_deg,
            "sign": asc_sign,
            "degree_in_sign": round(asc_deg_in_sign, 4) if asc_deg_in_sign is not None else None
        } if asc_deg is not None else None,
        "mc": {
            "longitude": mc_deg,
            "sign": longitude_to_sign_degree(mc_deg)[0] if mc_deg is not None else None,
            "degree_in_sign": round(longitude_to_sign_degree(mc_deg)[1], 4) if mc_deg is not None else None
        } if mc_deg is not None else None
    }