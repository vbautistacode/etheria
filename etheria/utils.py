# etheria/utils.py
"""
Utilitários compartilhados:
- redução numérica (com opção de preservar master numbers)
- normalização de nomes (remoção de acentos, uppercase)
- cálculo de idade (aceita date ou ISO string)
- formatação de graus, filename seguro, validações mínimas de tabelas
- soma de dígitos a partir de data
"""

from datetime import date, datetime
import unicodedata
import re
from typing import Optional, Any


def reduce_number(n: Any, keep_master: bool = False) -> int:
    """
    Reduz um número somando seus dígitos até obter 1..9.
    Se keep_master=True, preserva 11 e 22 como master numbers.
    Aceita int ou string numérica.
    """
    try:
        n = abs(int(n))
    except Exception:
        return 0
    if n <= 9:
        return n
    while True:
        s = sum(int(d) for d in str(n))
        if keep_master and s in (11, 22):
            return s
        if s <= 9:
            return s
        n = s


def normalize_name(name: Optional[str]) -> str:
    """
    Remove acentos, converte para maiúsculas e normaliza espaços.
    Retorna string vazia para entradas não-texto.
    """
    if not isinstance(name, str):
        return ""
    s = unicodedata.normalize("NFKD", name)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = " ".join(s.split())
    return s.upper()


def _parse_date_like(d: Any) -> date:
    """
    Converte date ou ISO string para datetime.date.
    Lança ValueError se não for possível.
    """
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        # aceita ISO (YYYY-MM-DD) e variantes compatíveis com fromisoformat
        return datetime.fromisoformat(d).date()
    raise ValueError("Valor de data inválido; forneça date ou ISO string")


def age_from_dob(dob: Any, ref_date: Optional[date] = None) -> int:
    """
    Calcula idade em anos completos a partir da data de nascimento.
    Aceita date ou ISO string. ref_date pode ser fornecida para testes.
    """
    dob_date = _parse_date_like(dob)
    if ref_date is None:
        ref_date = date.today()
    years = ref_date.year - dob_date.year
    if (ref_date.month, ref_date.day) < (dob_date.month, dob_date.day):
        years -= 1
    return years


def digits_sum_from_date(d: Any) -> int:
    """
    Soma todos os dígitos da data no formato DDMMYYYY.
    Aceita date ou ISO string.
    """
    d_date = _parse_date_like(d)
    s = d_date.strftime("%d%m%Y")
    return sum(int(ch) for ch in s if ch.isdigit())


def format_degree(deg: Optional[float]) -> str:
    """
    Formata grau como string com duas casas e símbolo de grau.
    Ex.: 12.345 -> '12.35°'
    """
    try:
        return f"{float(deg):.2f}°"
    except Exception:
        return "0.00°"


def safe_filename(name: str) -> str:
    """
    Gera nome de arquivo seguro substituindo caracteres inválidos.
    """
    s = re.sub(r"[^a-zA-Z0-9_\-\.]", "_", str(name))
    return s


# Placeholders de validação (mantidos para compatibilidade)
def validate_cycle35(df: Any) -> None:
    """
    Validação mínima para a tabela cycle_35.
    Lance ValueError se inválido; implementar validações mais estritas conforme necessário.
    """
    if df is None:
        raise ValueError("cycle_35 inválido")


def validate_cycle1(df: Any) -> None:
    """
    Validação mínima para a tabela cycle_1year.
    """
    if df is None:
        raise ValueError("cycle_1 inválido")