# etheria/__init__.py
"""
Pacote Etheria - fachada mínima.
Se você manteve o pacote com nome esoteric_rules, mantenha um alias aqui.
"""
try:
    from esoteric_rules.rules import generate_reading  # se o pacote original estiver presente
    from esoteric_rules.interpretations import generate_interpretation
    # expor via etheria namespace
    __all__ = ["generate_reading", "generate_interpretation"]
except Exception:
    # fallback: se o pacote etheria for o real, deixe vazio; o import direto em app.py tenta ambos
    __all__ = []
