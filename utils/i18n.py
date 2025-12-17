# utils/i18n.py
import json
import unicodedata
from pathlib import Path
from typing import Optional

_LOCALE_PATH = Path(__file__).parent.parent / "locales" / "pt_BR.json"

def _load_locale(path: Path = _LOCALE_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

_LOCALE = _load_locale()

def t(key: str) -> str:
    """
    Retorna a tradução para a chave no formato 'planet.mercury' ou 'sign.aries'.
    Levanta KeyError se a chave não existir.
    """
    parts = key.split(".")
    d = _LOCALE
    for p in parts:
        d = d[p]
    return d

def _normalize_text(s: str) -> str:
    s = s.strip().lower()
    # remove acentos para facilitar matching
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s

# aliases em inglês e variações comuns -> chave canônica do JSON
_PLANET_ALIASES = {
    "sun": "sun", "sol": "sun",
    "moon": "moon", "lua": "moon",
    "mercury": "mercury", "mercurio": "mercury", "mercurío": "mercury",
    "venus": "venus", "venus": "venus", "vênus": "venus", "venus": "venus",
    "mars": "mars", "marte": "mars",
    "jupiter": "jupiter", "jupiter": "jupiter", "jupter": "jupiter", "júpiter": "jupiter",
    "saturn": "saturn", "saturno": "saturn",
    "uranus": "uranus", "urano": "uranus",
    "neptune": "neptune", "netuno": "neptune",
    "pluto": "pluto", "plutao": "pluto", "plutão": "pluto",
    "chiron": "chiron", "quíron": "chiron", "quiron": "chiron",
    "lilith": "lilith", "lilit": "lilith",
    "north node": "north_node", "nodo norte": "north_node", "node north": "north_node",
    "south node": "south_node", "nodo sul": "south_node", "node south": "south_node"
}

_SIGN_ALIASES = {
    "aries": "aries", "áries": "aries", "aries": "aries",
    "taurus": "taurus", "touro": "taurus",
    "gemini": "gemini", "gemeos": "gemini", "gêmeos": "gemini",
    "cancer": "cancer", "cancer": "cancer", "câncer": "cancer",
    "leo": "leo", "leao": "leo", "leão": "leo",
    "virgo": "virgo", "virgem": "virgo",
    "libra": "libra",
    "scorpio": "scorpio", "escorpiao": "scorpio", "escorpião": "scorpio",
    "sagittarius": "sagittarius", "sagitario": "sagittarius", "sagitário": "sagittarius",
    "capricorn": "capricorn", "capricornio": "capricorn", "capricórnio": "capricorn",
    "aquarius": "aquarius", "aquario": "aquarius", "aquário": "aquarius",
    "pisces": "pisces", "peixes": "pisces"
}

def normalize_planet(name: str) -> Optional[str]:
    """
    Recebe um nome de planeta (pt/en/variações) e retorna o nome em português
    conforme o arquivo pt_BR.json. Retorna None se não reconhecer.
    """
    key = _normalize_text(name)
    # tentar aliases
    canonical = _PLANET_ALIASES.get(key)
    if canonical and canonical in _LOCALE["planet"]:
        return _LOCALE["planet"][canonical]
    # tentar match direto nas traduções
    for k, v in _LOCALE["planet"].items():
        if _normalize_text(v) == key:
            return v
    return None

def normalize_sign(name: str) -> Optional[str]:
    """
    Recebe um nome de signo (pt/en/variações) e retorna o nome em português
    conforme o arquivo pt_BR.json. Retorna None se não reconhecer.
    """
    key = _normalize_text(name)
    canonical = _SIGN_ALIASES.get(key)
    if canonical and canonical in _LOCALE["sign"]:
        return _LOCALE["sign"][canonical]
    for k, v in _LOCALE["sign"].items():
        if _normalize_text(v) == key:
            return v
    return None

def get_all_planets() -> dict:
    """Retorna o dicionário de planetas (chave_canônica -> nome_pt)."""
    return _LOCALE["planet"].copy()

def get_all_signs() -> dict:
    """Retorna o dicionário de signos (chave_canônica -> nome_pt)."""
    return _LOCALE["sign"].copy()

# Exemplo rápido de uso (executar como script)
if __name__ == "__main__":
    examples = ["Mercury", "mercurio", "Vênus", "venus", "Sol", "moon", "Plutão"]
    for ex in examples:
        print(f"{ex} -> {normalize_planet(ex)}")
    signs = ["Aries", "áries", "GEMINI", "touro", "Peixes"]
    for s in signs:
        print(f"{s} -> {normalize_sign(s)}")