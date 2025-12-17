# services/astro_service.py
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from dateutil import parser as dateparser
from datetime import datetime, date, time
import pytz
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

# import de i18n
from utils.i18n import t, normalize_planet, normalize_sign, get_all_planets, get_all_signs

geolocator = Nominatim(user_agent="etheria_geocoder")
tzfinder = TimezoneFinder()

# --- funções existentes (geocode_place, get_timezone_from_coords, parse_birth_time) ---
# (mantém exatamente como você já tem)

def compute_chart_positions(lat: float, lon: float, local_dt: datetime, house_system: str = "Placidus"):
    """
    Usa flatlib para calcular posições de planetas e casas.
    Retorna dict { 'Sol': '12° Touro, Casa 7', ... } com nomes em português.
    Se local_dt for None (hora desconhecida), calcula posições por signo apenas (sem casas).
    """
    positions = {}

    if local_dt is None:
        dt = Datetime(datetime.utcnow().strftime("%Y/%m/%d"), "12:00", "UTC")
        chart = Chart(dt, GeoPos(lat, lon))
    else:
        iso = local_dt.strftime("%Y/%m/%d")
        hhmm = local_dt.strftime("%H:%M")
        tzname = local_dt.tzinfo.zone
        dt = Datetime(iso, hhmm, tzname)
        # flatlib espera hsys como letra em alguns casos; aqui usamos a primeira letra maiúscula
        chart = Chart(dt, GeoPos(lat, lon), hsys=house_system[0].upper())

    # bodies flatlib -> chave canônica do locale (minúscula)
    # mapeamento simples: SUN -> sun, MERCURY -> mercury, etc.
    FLATLIB_TO_KEY = {
        'SUN': 'sun', 'MOON': 'moon', 'MERCURY': 'mercury', 'VENUS': 'venus',
        'MARS': 'mars', 'JUPITER': 'jupiter', 'SATURN': 'saturn',
        'URANUS': 'uranus', 'NEPTUNE': 'neptune', 'PLUTO': 'pluto'
    }

    # flatlib pode retornar obj.sign como abreviação (ex: 'Ta') ou nome em inglês.
    # Criamos um mapeamento de abreviações/nomes para a chave canônica do signo.
    SIGN_MAP = {
        # abreviações comuns flatlib -> chave canônica
        'Ar': 'aries', 'Ta': 'taurus', 'Ge': 'gemini', 'Cn': 'cancer',
        'Le': 'leo', 'Vi': 'virgo', 'Li': 'libra', 'Sc': 'scorpio',
        'Sg': 'sagittarius', 'Cp': 'capricorn', 'Aq': 'aquarius', 'Pi': 'pisces',
        # nomes em inglês (caso flatlib retorne 'Taurus' etc.)
        'aries': 'aries', 'taurus': 'taurus', 'gemini': 'gemini', 'cancer': 'cancer',
        'leo': 'leo', 'virgo': 'virgo', 'libra': 'libra', 'scorpio': 'scorpio',
        'sagittarius': 'sagittarius', 'capricorn': 'capricorn', 'aquarius': 'aquarius', 'pisces': 'pisces'
    }

    bodies = list(FLATLIB_TO_KEY.keys())
    for b in bodies:
        try:
            obj = chart.get(b)
        except Exception:
            continue

        # extrai signo e longitude
        raw_sign = getattr(obj, "sign", "")
        lon = getattr(obj, "lon", None)

        # tenta mapear o signo para chave canônica
        sign_key = None
        if raw_sign:
            # normaliza: remove acentos e lower para comparar
            rs = raw_sign.strip()
            # checar mapeamentos diretos (abreviações)
            sign_key = SIGN_MAP.get(rs)
            if not sign_key:
                # tentar versão lower (ex: 'Taurus')
                sign_key = SIGN_MAP.get(rs.lower())
            if not sign_key:
                # fallback: tentar normalize_sign (caso raw_sign seja 'Touro' ou 'Taurus')
                sign_key = normalize_sign(rs)

        # monta representação legível do grau: ex "12.34°"
        pos = f"{lon:.2f}°" if lon is not None else ""

        # nome do planeta em pt
        planet_key = FLATLIB_TO_KEY.get(b)
        planet_name_pt = t(f"planet.{planet_key}") if planet_key else b.capitalize()

        # nome do signo em pt (se reconhecido)
        sign_name_pt = t(f"sign.{sign_key}") if sign_key else raw_sign

        # tenta obter casa (se houver hora)
        try:
            house = chart.getHouse(obj.lon)
            # formata: "Sol — 12.34° Touro, Casa 7"
            if sign_name_pt:
                positions[planet_name_pt] = f"{pos} {sign_name_pt}, Casa {house.number}"
            else:
                positions[planet_name_pt] = f"{pos}, Casa {house.number}"
        except Exception:
            # sem casas: apenas grau + signo
            if sign_name_pt:
                positions[planet_name_pt] = f"{pos} {sign_name_pt}"
            else:
                positions[planet_name_pt] = pos

    # Ascendente
    try:
        asc = chart.get('ASC')
        asc_sign = getattr(asc, "sign", "")
        asc_lon = getattr(asc, "lon", None)
        asc_key = SIGN_MAP.get(asc_sign) or normalize_sign(asc_sign) or asc_sign
        asc_name = t(f"sign.{asc_key}") if asc_key else asc_sign
        positions['Ascendente'] = f"{asc_lon:.2f}° {asc_name}" if asc_lon is not None else asc_name
    except Exception:
        pass

    # Parte da Fortuna (se disponível)
    try:
        fortune = chart.get('PART_OF_FORTUNE')
        f_sign = getattr(fortune, "sign", "")
        f_lon = getattr(fortune, "lon", None)
        f_key = SIGN_MAP.get(f_sign) or normalize_sign(f_sign) or f_sign
        f_name = t(f"sign.{f_key}") if f_key else f_sign
        positions['Parte da Fortuna'] = f"{f_lon:.2f}° {f_name}" if f_lon is not None else f_name
    except Exception:
        pass

    return positions