# services/astro_service.py
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from dateutil import parser as dateparser
from datetime import datetime, date, time
import pytz
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

geolocator = Nominatim(user_agent="etheria_geocoder")
tzfinder = TimezoneFinder()

def geocode_place(place: str):
    """Retorna (lat, lon, display_name) ou (None, None, None) se falhar."""
    location = geolocator.geocode(place, language="pt")
    if not location:
        return None, None, None
    return location.latitude, location.longitude, location.address

def get_timezone_from_coords(lat: float, lon: float):
    """Retorna timezone string como 'America/Sao_Paulo' ou None."""
    tz = tzfinder.timezone_at(lat=lat, lng=lon)
    return tz

def parse_birth_time(btime_str: str, bdate: date, timezone_str: str):
    """
    Normaliza hora. Se btime_str vazio retorna None.
    Retorna aware datetime em timezone local.
    """
    if not btime_str or not btime_str.strip():
        return None
    # tenta parse flexível
    try:
        dt_time = dateparser.parse(btime_str)
    except Exception:
        return None
    # se parse devolveu date+time, extrai hora
    if isinstance(dt_time, datetime):
        t = dt_time.time()
    else:
        t = time(dt_time.hour, dt_time.minute)
    local_tz = pytz.timezone(timezone_str) if timezone_str else pytz.UTC
    local_dt = datetime.combine(bdate, t)
    local_dt = local_tz.localize(local_dt)
    return local_dt

def compute_chart_positions(lat: float, lon: float, local_dt: datetime, house_system: str = "Placidus"):
    """
    Usa flatlib para calcular posições de planetas e casas.
    Retorna dict { 'Sun': '12° Taurus, House 7', ... }.
    Se local_dt for None (hora desconhecida), calcula posições por signo apenas (sem casas).
    """
    positions = {}
    # se hora desconhecida, calc com 00:00 UTC como fallback sem casas
    if local_dt is None:
        # fallback: use date at noon UTC to get approximate signs
        dt = Datetime(datetime.utcnow().strftime("%Y/%m/%d"), "12:00", "UTC")
        chart = Chart(dt, GeoPos(lat, lon))
    else:
        iso = local_dt.strftime("%Y/%m/%d")
        hhmm = local_dt.strftime("%H:%M")
        tzname = local_dt.tzinfo.zone
        dt = Datetime(iso, hhmm, tzname)
        chart = Chart(dt, GeoPos(lat, lon), hsys=house_system[0].upper())  # flatlib expects single letter sometimes

    # planetas de interesse
    bodies = ['SUN','MOON','MERCURY','VENUS','MARS','JUPITER','SATURN','URANUS','NEPTUNE','PLUTO']
    for b in bodies:
        obj = chart.get(b)
        # flatlib fornece e.g. '12Ta34' — formatamos para algo legível
        pos = f"{obj.sign}{obj.lon:.2f}°"
        # se houver casa disponível
        try:
            house = chart.getHouse(obj.lon)
            positions[b.capitalize()] = f"{pos}, House {house.number}"
        except Exception:
            positions[b.capitalize()] = pos

    # Ascendente e Part of Fortune
    try:
        asc = chart.get('ASC')
        positions['ASC'] = f"{asc.sign}{asc.lon:.2f}°"
    except Exception:
        pass

    try:
        fortune = chart.get('PART_OF_FORTUNE')
        positions['Part of Fortune'] = f"{fortune.sign}{fortune.lon:.2f}°"
    except Exception:
        pass

    return positions