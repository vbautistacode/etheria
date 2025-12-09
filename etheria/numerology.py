#etheria/numerology.py

"""
Numerologia Pitagórica e Cabalística (atualizado)
- cálculos principais: Life Path, Expression, Soul Urge, Personality, Maturity
- Pinnacles / Períodos (4 picos) (método baseado em data de nascimento)
- A, Mês Pessoal, Dia Pessoal
- Influência Anual (calculada pela quantidade de letras do nome completo)
- suporte a mapeamentos Pitagórico e Cabalístico
"""

import unicodedata
import re
from typing import Dict, Tuple, Optional, Any, List
from datetime import date, datetime
from collections.abc import Iterable

#INTERPRETAÇÃO CABALÍSTICA BÁSICA PARA NÚMEROS 1-22
NUM_TEMPLATES: Dict[int, Dict[str, str]] = {
    1: {"short":"Início, liderança, iniciativa.", "medium":"Muitas inteligências ou uma inteligência mal aplicada", "long":"Ação direta; foco em concretizar; energia física e prática.", "chakra":"Muladhara"},
    2: {"short":"Parcerias, sensibilidade.", "medium":"Número de revelação ou ocultar verdade", "long":"Cooperação, diplomacia; trabalho em dupla e receptividade.", "chakra":"Muladhara"},
    3: {"short":"Criatividade aplicada; expressão.", "medium":"Força muito grande de plasmação ou falta de vontade muito grande", "long":"Comunicação criativa; colocar ideias em prática; sociabilidade.", "chakra":"Muladhara"},
    4: {"short":"Estrutura, trabalho consistente.", "medium":"O poder da decisão ou uma tirania absoluta", "long":"Organização e disciplina; construir bases sólidas.", "chakra":"Svadhishthana"},
    5: {"short":"Mudança com propósito.", "medium":"Grande espiritualidade e aberturas espirituais ou um fanatismo muito grande", "long":"Movimento e adaptação; usar energia para oportunidades que importam.", "chakra":"Svadhishthana"},
    6: {"short":"Responsabilidade e cuidado.", "medium":"Poder de decisão seguindo o coração ou momento de grande indecisão", "long":"Cuidar do que importa; equilíbrio entre ação e serviço.", "chakra":"Svadhishthana"},
    7: {"short":"Busca interior; estudo.", "medium":"Direcionamento bacana das energias ou um direcionamento errado das mesmas", "long":"Refinamento espiritual e intelectual; atrair possibilidades positivas.", "chakra":"Manipura"},
    8: {"short":"Poder pessoal e prosperidade.", "medium":"Éticas, bons valores, moral ou falta de ética e imoralidade", "long":"Manifestação prática de recursos; foco em resultados.", "chakra":"Manipura"},
    9: {"short":"Conclusões e compaixão.", "medium":"Ter um pouco de isolamento, quietude, para achar a luz interior ou imprudência e não saber aquietar a alma", "long":"Fechamento de ciclos; visão ampla e serviço ao coletivo.", "chakra":"Manipura"},
    10: {"short":"Racionalidade aplicada.", "medium":"Viver os caminhos que o destino demonstra, observar através do Karma ou correr do destino", "long":"Organizar conhecimento; base para intuições futuras.", "chakra":"Anahata"},
    11: {"short":"Intuição ampliada (mestre).", "medium":"Equilíbrio grande entre as energias espirituais e terrenas ou não colocar em prática as duas energias juntas", "long":"Porta para insights profundos; atenção ao equilíbrio emocional.", "chakra":"Anahata"},
    12: {"short":"Aprendizado e síntese.", "medium":"Comprometimento. Aprender a se comprometer com o que é sério para você ou irresponsabilidade, fugir do dever", "long":"Integração de saberes; preparar terreno para intuições maiores.", "chakra":"Anahata"},
    13: {"short":"Abstração criativa.", "medium":"Aceitar as grandes transformações que o mundo oferece ou não aceitar e ser judiado pelas transformações", "long":"Mente criativa; trabalhar com símbolos e ideias não-lineares.", "chakra":"Vishuddha"},
    14: {"short":"Experimentação mental.", "medium":"Equilíbrio entre passado e futuro. Aprenda com as experiências que passou para que no presente elas se tornem potencialidades futuras ou viver aprisionado no passado e futuro", "long":"Explorar novas formas de pensar; liberdade criativa.", "chakra":"Vishuddha"},
    15: {"short":"Expressão do 5º princípio.", "medium":"Aceitar as sombras e com elas transformar em potencialidades ou luzes ou ser conduzido por sombras e não perceber", "long":"Criatividade aplicada a ideias; inovação comunicativa.", "chakra":"Vishuddha"},
    16: {"short":"Intuição prática.", "medium":"A luz é o poder de desconstruir as coisas falsas para construir as verdadeiras ou a pessoa que aposta em coisas desgastadas que já deveriam ser desconstruídas", "long":"Escolhas guiadas pela intuição; confiar no sentir.", "chakra":"Ajna"},
    17: {"short":"Visão e decisão.", "medium":"Aprender a ter fé, acreditar, pensamento otimista, espiritualidade à coisas maiores ou falta de fé, otimismo cego", "long":"Poder de escolha alinhado com percepção interior.", "chakra":"Ajna"},
    18: {"short":"Sabedoria intuitiva.", "medium":"Aprender a ter força, através dos medos e provações ou ter muita confiança, achar que está com tudo", "long":"Integração entre sentir e agir; liderança intuitiva.", "chakra":"Ajna"},
    19: {"short":"Pronto para o novo.", "medium":"Aceitar o brilho do sol que está dentro de você, aprender a trabalhar a verdadeira gratidão ou trabalhar a gratidão falsa", "long":"Abertura para experiências maiores; preparação para arquétipos.", "chakra":"Sahasrara"},
    20: {"short":"Transcender limites.", "medium":"Representa a libertação verdadeira ou estar preso de luz para morrer", "long":"Momento de expansão; contato com padrões universais.", "chakra":"Sahasrara"},
    21: {"short":"Conexão arquetípica.", "medium":"Posicionamento, saber aonde está e qual experiência está passando ou mal conectado, em experiências erradas", "long":"Porta para arquétipos universais; experiências transformadoras.", "chakra":"Sahasrara"},
    22: {"short":"Manifestação em grande escala.", "medium":"Finalização de ciclo muito importante para abertura de um novo ciclo ou não saber finalizar ciclos, estar preso", "long":"Capacidade de estruturar e materializar projetos de grande impacto (mestre).", "chakra":"Sahasrara"},
}

QUADRANTS = {
    "1-3": {"range": range(1,4), "chakra":"Muladhara", "theme":"Consciência Física"},
    "4-6": {"range": range(4,7), "chakra":"Svadhishthana", "theme":"Energia Vital"},
    "7-9": {"range": range(7,10), "chakra":"Manipura", "theme":"Energias Astrais"},
    "10-12": {"range": range(10,13), "chakra":"Anahata", "theme":"Energias Mentais"},
    "13-15": {"range": range(13,16), "chakra":"Vishuddha", "theme":"Idéias"},
    "16-18": {"range": range(16,19), "chakra":"Ajna", "theme":"Intuição"},
    "19-20-21": {"range": range(19,22), "chakra":"Sahasrara", "theme":"Conexão com os Arquétipos Universais"},
}

_MASTER_NUMBERS = (11, 22, 33)

def reduce_pythagorean_from_date(day: int, month: int, year: int) -> int:
    """
    Reduz a data (DDMMYYYY) até um número 1-22 ou mestre (11,22,33).
    Preserva mestres definidos em _MASTER_NUMBERS.
    """
    total = sum(int(d) for d in f"{day:02d}{month:02d}{year:04d}")
    while True:
        if total in _MASTER_NUMBERS:
            return total
        if total <= 22:
            return total
        total = sum(int(d) for d in str(total))

def quadrant_for_number(n: int) -> dict:
    if n == 22:
        return {"quadrant": "22 (mestre)", "chakra": "Sahasrara", "theme": "Manifestação em grande escala"}
    for key, info in QUADRANTS.items():
        if n in info["range"]:
            return {"quadrant": key, "chakra": info["chakra"], "theme": info["theme"]}
    return {"quadrant": "desconhecido", "chakra": "—", "theme": None}

def analyze_date_str(date_str: str) -> dict:
    s = str(date_str).strip()
    try:
        if "/" in s:
            parts = [p.strip() for p in s.split("/")]
            if len(parts) != 3:
                raise ValueError
            d, m, y = [int(x) for x in parts]
        elif "-" in s:
            # aceita YYYY-MM-DD e YYYY-MM-DDTHH:MM:SS
            iso = s.split("T")[0]
            dt = datetime.fromisoformat(iso)
            d, m, y = dt.day, dt.month, dt.year
        else:
            raise ValueError("Formato inválido")
    except Exception:
        raise ValueError("Formato de data inválido. Use DD/MM/YYYY ou YYYY-MM-DD")

    # validação simples de dia/mês
    if not (1 <= m <= 12 and 1 <= d <= 31):
        raise ValueError("Dia ou mês fora do intervalo esperado")

    num = reduce_pythagorean_from_date(d, m, y)
    quad = quadrant_for_number(num)
    template = NUM_TEMPLATES.get(num, {"short":"—","medium":"—","long":"—","chakra": quad.get("chakra") or "—"})
    return {
        "date": f"{d:02d}/{m:02d}/{y}",
        "reduced_number": num,
        "quadrant": quad["quadrant"],
        "chakra": template.get("chakra") or quad.get("chakra"),
        "theme": quad.get("theme"),
        "short": template.get("short"),
        "medium": template.get("medium"),
        "long": template.get("long")
    }

# opcional: função para gerar anos pessoais até max_age
# def personal_year(dob: datetime, year: int) -> int:
#     dm = sum(int(d) for d in f"{dob.day:02d}{dob.month:02d}")
#     py = sum(int(d) for d in str(year))
#     return reduce_pythagorean_from_date(int(str(dm)), 0, int(str(py))) if False else reduce_pythagorean_from_date(dob.day, dob.month, year)

# mapa pitagórico básico (A=1, B=2, ..., I=9, J=1, etc.)
PYTHAG_MAP = {ch: (i % 9) or 9 for i, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", start=1)}

def _normalize_name(name: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", name.upper())
        if c.isalpha()
    )

def name_value_pythag(full_name: str, keep_master: bool = False):
    norm = _normalize_name(full_name)
    total = sum(PYTHAG_MAP.get(ch, 0) for ch in norm)
    reduced = reduce_number(total, keep_masters=keep_master)
    return reduced, total

# -------------------------
# Mapeamentos básicos
# -------------------------
# Mapa Pitagórico (A=1..I=9, J=1..R=9, S=1..Z=8) — ciclo 1..9
PYTHAGOREAN_MAP: Dict[str, int] = {
    **{c: ((i % 9) + 1) for i, c in enumerate(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))}
}

# Mapa Cabalístico personalizado (conforme tabela fornecida)
CABALISTIC_MAP: Dict[str, int] = {
    "A": 1, "B": 2, "C": 3, "D": 4, "E": 5, "F": 8, "G": 3, "H": 5, "I": 1,
    "J": 1, "K": 2, "L": 3, "M": 4, "N": 5, "O": 7, "P": 8, "Q": 1, "R": 2,
    "S": 3, "T": 4, "U": 6, "V": 6, "W": 6, "X": 6, "Y": 1, "Z": 7
}

VOWELS = set(list("AEIOU"))

# -------------------------
# Normalização
# -------------------------
def _normalize_text(s: Optional[str]) -> str:
    if s is None:
        return ""
    s = str(s).strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # manter apenas letras e espaços
    s = "".join(ch for ch in s if ch.isalpha() or ch.isspace())
    return s

def _letters_only(s: str) -> str:
    return "".join(ch for ch in _normalize_text(s) if ch.isalpha())

# -------------------------
# Valores por letra
# -------------------------
def pythagorean_letter_value(letter: str) -> int:
    ch = _normalize_text(letter)[:1]
    return PYTHAGOREAN_MAP.get(ch, 0)

def cabalistic_letter_value(letter: str) -> int:
    ch = _normalize_text(letter)[:1]
    return CABALISTIC_MAP.get(ch, 0)

# -------------------------
# Componentes do nome
# -------------------------
def expression_number(full_name: str, method: str = "pythagorean", keep_masters: bool = True, master_min: int = 11) -> int:
    name = _letters_only(full_name)
    total = 0
    for ch in name:
        total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return reduce_number(total, keep_masters=keep_masters, master_min=master_min)

def soul_urge_number(full_name: str, method: str = "pythagorean", keep_masters: bool = True, master_min: int = 11) -> int:
    name = _normalize_text(full_name)
    total = 0
    for ch in name:
        if ch in VOWELS:
            total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return reduce_number(total, keep_masters=keep_masters, master_min=master_min)

def personality_number(full_name: str, method: str = "pythagorean", keep_masters: bool = True, master_min: int = 11) -> int:
    name = _normalize_text(full_name)
    total = 0
    for ch in name:
        if ch.isalpha() and ch not in VOWELS:
            total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return reduce_number(total, keep_masters=keep_masters, master_min=master_min)

# Substitua a definição atual de reduce_number por esta

# lista de mestres conhecidos (ordem crescente)
_MASTER_NUMBERS = (11, 22, 33)

def _flatten(seq):
    for item in seq:
        if isinstance(item, (str, bytes)):
            yield item
        elif isinstance(item, Iterable):
            for sub in _flatten(item):
                yield sub
        else:
            yield item

def _ints_from_token(tok):
    if tok is None:
        return []
    if isinstance(tok, (int, float)) and not isinstance(tok, bool):
        return [int(tok)]
    if isinstance(tok, (str, bytes)):
        s = str(tok).strip()
        if s == "":
            return []
        try:
            return [int(s)]
        except ValueError:
            found = re.findall(r"\d+", s)
            return [int(x) for x in found] if found else []
    try:
        return [int(tok)]
    except Exception:
        return []

def _to_digit_list(mixed):
    """
    Converte entrada possivelmente aninhada em lista plana de dígitos.
    Ex.: 12 -> [1,2]; "12 3" -> [1,2,3]; [12, [3,4]] -> [1,2,3,4]
    """
    if not isinstance(mixed, Iterable) or isinstance(mixed, (str, bytes)):
        mixed = (mixed,)
    out = []
    for token in _flatten(mixed):
        ints = _ints_from_token(token)
        for n in ints:
            for ch in str(abs(int(n))):
                if ch.isdigit():
                    out.append(int(ch))
    return out

def reduce_number(values, keep_masters: bool = False, master_min: int = 11) -> Optional[int]:
    # tentar extrair um total bruto primeiro (se values for um número simples)
    # se values for um iterável complexo, _to_digit_list continuará funcionando
    # mas queremos preservar mestres quando o total bruto for exatamente 11/22/33
    # obter lista de dígitos
    digits = _to_digit_list(values)
    if not digits:
        raise ValueError("Entrada vazia para reduce_number; nenhum dígito válido encontrado")

    total = sum(digits)

    # Se a entrada original for um único número inteiro (ex.: 11) e queremos preservar mestres,
    # precisamos checar o total bruto antes de reduzir por dígitos. Uma forma simples:
    # - se values é int/str representando um inteiro e esse inteiro é mestre, preserva.
    try:
        # tentar extrair um inteiro bruto do argumento original
        if isinstance(values, (int,)) or (isinstance(values, str) and values.isdigit()):
            raw_int = int(values)
            if keep_masters and raw_int in _MASTER_NUMBERS and raw_int >= master_min:
                return raw_int
    except Exception:
        pass

    # função auxiliar para verificar se total é um mestre a preservar
    def _is_preserved_master(x):
        if not keep_masters:
            return False
        for m in _MASTER_NUMBERS:
            if x == m and m >= master_min:
                return True
        return False

    while True:
        if _is_preserved_master(total):
            return total
        if total < 10:
            return total
        total = sum(int(ch) for ch in str(abs(int(total))))

def maturity_number(life_path, expression, keep_masters: bool = False, master_min: int = 11):
    """
    Normaliza life_path e expression, achata estruturas aninhadas e chama reduce_number.
    master_min controla a menor referência de mestre a preservar.
    """
    return reduce_number((life_path, expression), keep_masters=keep_masters, master_min=master_min)

def power_number_from_dob(dob: date, keep_masters: bool = True, master_min: int = 11) -> Dict[str, Optional[int]]:
    try:
        d = getattr(dob, "day", None)
        m = getattr(dob, "month", None)
        if d is None or m is None:
            raise ValueError("Data inválida para cálculo do Número de Poder")
        raw_digits = _to_digit_list((d, m))
        if not raw_digits:
            raise ValueError("Nenhum dígito válido extraído de dia/mês")
        raw_sum = sum(raw_digits)

        # preservação explícita de mestres: se raw_sum é um mestre e atende master_min, mantê-lo
        if keep_masters and raw_sum in _MASTER_NUMBERS and raw_sum >= master_min:
            reduced = raw_sum
        else:
            reduced = reduce_number(raw_sum, keep_masters=keep_masters, master_min=master_min)

        return {"value": reduced, "raw": raw_sum}
    except Exception:
        try:
            s = f"{getattr(dob, 'day', '')}{getattr(dob, 'month', '')}"
            digits = _to_digit_list(s)
            raw_sum = sum(digits) if digits else None
            if raw_sum is None:
                return {"value": None, "raw": None}
            if keep_masters and raw_sum in _MASTER_NUMBERS and raw_sum >= master_min:
                reduced = raw_sum
            else:
                reduced = reduce_number(raw_sum, keep_masters=keep_masters, master_min=master_min)
            return {"value": reduced, "raw": raw_sum}
        except Exception:
            return {"value": None, "raw": None}

# Adicione funções de total bruto e breakdown (cole após as funções de letra/valor)
def expression_total(full_name: str, method: str = "pythagorean") -> int:
    """Retorna o total bruto (soma das letras) antes da redução."""
    name = _letters_only(full_name)
    total = 0
    for ch in name:
        total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return total

def soul_urge_total(full_name: str, method: str = "pythagorean") -> int:
    name = _normalize_text(full_name)
    total = 0
    for ch in name:
        if ch in VOWELS:
            total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return total

def personality_total(full_name: str, method: str = "pythagorean") -> int:
    name = _normalize_text(full_name)
    total = 0
    for ch in name:
        if ch.isalpha() and ch not in VOWELS:
            total += pythagorean_letter_value(ch) if method == "pythagorean" else cabalistic_letter_value(ch)
    return total

def letter_value_breakdown(full_name: str):
    """Retorna lista de tuplas (letra, pythag_val, cabal_val) e totais brutos."""
    name = _letters_only(full_name)
    rows = []
    total_p = 0
    total_c = 0
    for ch in name:
        v_p = pythagorean_letter_value(ch)
        v_c = cabalistic_letter_value(ch)
        total_p += v_p
        total_c += v_c
        rows.append((ch, v_p, v_c))
    return {"rows": rows, "total_pythagorean": total_p, "total_cabalistic": total_c}

# -------------------------
# Life Path (Caminho de Vida)
# -------------------------

def sum_digits_of_date(d: date) -> int:
    s = f"{d.year:04d}{d.month:02d}{d.day:02d}"
    return sum(int(ch) for ch in s if ch.isdigit())

def life_path_from_dob(dob: date, keep_masters: bool = True, keep_master: Optional[bool] = None):
    # compatibilidade com keep_master (singular)
    if keep_master is not None:
        keep_masters = keep_master

    total = sum_digits_of_date(dob)  # soma dos dígitos da data (raw)
    reduced = reduce_number(total, keep_masters=keep_masters)
    return reduced, total

# -------------------------
# Pinnacles / Períodos (4 picos) - método simples baseado em data
# Método adotado (variante comum):
# P1 = reduce(month + day)
# P2 = reduce(day + year)
# P3 = reduce(P1 + P2)
# P4 = reduce(month + year)
# -------------------------

def pinnacles_from_dob(dob: date, keep_masters: bool = True) -> Dict[str, int]:
    m = dob.month
    d = dob.day
    y = dob.year
    p1 = reduce_number(m + d, keep_masters=keep_masters)
    p2 = reduce_number(d + sum(int(ch) for ch in str(y)), keep_masters=keep_masters)
    p3 = reduce_number(p1 + p2, keep_masters=keep_masters)
    p4 = reduce_number(m + sum(int(ch) for ch in str(y)), keep_masters=keep_masters)
    return {"pinnacle_1": p1, "pinnacle_2": p2, "pinnacle_3": p3, "pinnacle_4": p4}

# -------------------------
# A, Mês Pessoal, Dia Pessoal
# Convenção usada:
# - Personal Year = reduce(life_path + current_year_digits)
# - Personal Month = reduce(personal_year + month_number)
# - Personal Day = reduce(personal_month + day_number)
# (variações existem; esta é uma abordagem prática e consistente)
# -------------------------

def personal_year(life_path: int, year: int = None, keep_masters: bool = True) -> int:
    if year is None:
        year = datetime.now().year
    year_sum = sum(int(ch) for ch in str(year))
    return reduce_number(life_path + year_sum, keep_masters=keep_masters)

def personal_month(personal_year_value: int, month: int, keep_masters: bool = True) -> int:
    return reduce_number(personal_year_value + month, keep_masters=keep_masters)

def personal_day(personal_month_value: int, day: int, keep_masters: bool = True) -> int:
    return reduce_number(personal_month_value + day, keep_masters=keep_masters)

# -------------------------
# Influência Anual (solicitada)
# - calculada pela quantidade de letras do nome completo (somente letras A-Z)
# - reduzida numericamente (preservando mestres se solicitado)
# -------------------------

# nova assinatura: mode pode ser "default" ou "cabalistic"
def annual_influence_by_name(full_name: str, keep_masters: bool = True, master_min: int = 11, mode: str = "default") -> Dict[str, int]:
    """
    Retorna:
      - raw: contagem de letras (A-Z) do nome (não reduzida)
      - value: valor a ser usado como 'influência' (reduzido ou não, dependendo do mode)
    mode:
      - "default": reduz a contagem normalmente (preservando mestres conforme keep_masters)
      - "cabalistic": política especial para numerologia cabalística:
           * se raw <= 22 -> aplicar redução normal (preservando mestres)
           * se raw > 22  -> manter raw como value (não reduzir além de 22)
    """
    letters = _letters_only(full_name)
    count = len(letters)

    # modo cabalístico: não reduzir números maiores que 22 (mantém o bruto)
    if mode == "cabalistic":
        if count > 22:
            # manter bruto como value para cabalística
            return {"raw": count, "value": count}
        # caso contrário, reduzir normalmente (preservando mestres)
        try:
            reduced = reduce_number(count, keep_masters=keep_masters, master_min=master_min)
        except Exception:
            # fallback seguro
            total = count
            while total > 9 and total not in (11, 22, 33):
                total = sum(int(d) for d in str(total))
            reduced = total
        return {"raw": count, "value": reduced}

    # modo default: reduzir normalmente
    try:
        reduced = reduce_number(count, keep_masters=keep_masters, master_min=master_min)
    except Exception:
        total = count
        while total > 9 and total not in (11, 22, 33):
            total = sum(int(d) for d in str(total))
        reduced = total
    return {"raw": count, "value": reduced}

# -------------------------
# Interpretações básicas (curtas e médias) — reutiliza dicionários anteriores
# (mantém os textos já definidos no módulo principal; aqui usamos versões simples)
# -------------------------

NUM_INTERPRETATIONS_SHORT: Dict[str, str] = {
    "1": "Liderança, iniciativa, independência.",
    "2": "Cooperação, sensibilidade, parceria.",
    "3": "Expressão, criatividade, sociabilidade.",
    "4": "Trabalho, disciplina, estrutura.",
    "5": "Mudança, liberdade, aventura.",
    "6": "Responsabilidade, família, serviço.",
    "7": "Reflexão, estudo, espiritualidade.",
    "8": "Poder, realização material, administração.",
    "9": "Compaixão, idealismo, conclusão.",
    "11": "Intuição elevada, inspiração (mestre).",
    "22": "Construtor mestre, visão prática (mestre).",
    "33": "Mestre do serviço e amor (mestre).",
    "44": "Estrutura ampliada e liderança prática.",
    "55": "Transformação em grande escala; liberdade responsável.",
    "66": "Serviço ampliado e cura comunitária.",
    "77": "Sabedoria profunda e investigação espiritual.",
    "88": "Poder material e manifestação em larga escala.",
    "99": "Conclusão coletiva e compaixão universal."
}

NUM_INTERPRETATIONS_MEDIUM: Dict[str, str] = {
    "1": "Indivíduo com forte impulso para liderar e iniciar projetos; precisa cultivar paciência e delegar.",
    "2": "Sensível e diplomático; talento para mediar e trabalhar em parceria; cuidado com indecisão.",
    "3": "Talento para comunicação e arte; tendência à dispersão se não houver disciplina.",
    "4": "Construtor confiável; prospera com rotina e planejamento; evitar rigidez excessiva.",
    "5": "Busca liberdade e variedade; prospera em mudanças; atenção a excessos.",
    "6": "Forte senso de dever e cuidado com família; tendência a assumir responsabilidades alheias.",
    "7": "Buscador do conhecimento; precisa de solidão para aprofundar; cuidado com isolamento.",
    "8": "Habilidade para negócios e administração; foco em resultados; ética é crucial.",
    "9": "Idealista e compassivo; chamado a servir causas maiores; evitar desilusão.",
    "11": "Canal de inspiração e visão; exige equilíbrio emocional para manifestar potencial.",
    "22": "Capacidade de materializar grandes ideais; requer disciplina e integridade.",
    "33": "Chamado ao serviço altruísta; grande responsabilidade emocional e espiritual.",
    "44": "Capacidade de organizar e liderar projetos de grande escala com responsabilidade; pode carregar peso excessivo se não houver delegação.",
    "55": "Força para promover mudanças profundas e inovadoras; precisa equilibrar impulso por liberdade com responsabilidade prática.",
    "66": "Chamado ao cuidado coletivo, liderança afetiva e responsabilidade social; pode sobrecarcar-se ao assumir demais pelos outros.",
    "77": "Aptidão para estudo, pesquisa e desenvolvimento de insights espirituais; exige disciplina interior para não se isolar.",
    "88": "Grande capacidade de gerir recursos, negócios e estruturas econômicas; responsabilidade ética essencial para evitar abuso de poder.",
    "99": "Chamado a servir causas globais, liderar transformações humanitárias e encerrar ciclos em benefício do coletivo."
}

NUM_INTERPRETATIONS_LONG: Dict[str, str] = {
    "1": "Pessoa com forte impulso para iniciar e liderar. Tem energia para transformar ideias em ação e tende a assumir responsabilidades naturalmente; precisa cultivar paciência, delegar quando necessário e aprender a ouvir para não impor soluções sem consenso. Quando equilibrado, manifesta autonomia criativa e capacidade de inspirar outros.",
    "2": "Indivíduo sensível e cooperativo, com talento para mediar e construir parcerias duradouras. Sua força está na diplomacia, empatia e capacidade de criar ambientes harmoniosos; deve trabalhar a assertividade para evitar que a indecisão ou a dependência emocional limitem seu potencial. Em contextos de equipe, atua como ponte e estabilizador.",
    "3": "Pessoa criativa e comunicativa, com facilidade para expressão artística e socialização. Tem imaginação fértil e carisma, mas precisa de disciplina para transformar ideias em resultados concretos; quando dispersa, perde oportunidades, e quando estruturada, brilha em projetos que exigem inovação e comunicação. A alegria e a leveza são suas marcas mais atraentes.",
    "4": "Perfil orientado à estrutura, trabalho consistente e construção de bases sólidas. Valoriza rotina, planejamento e responsabilidade; tende a prosperar em ambientes que exigem organização e perseverança, mas deve evitar rigidez que impeça adaptação. Sua força é a confiabilidade e a capacidade de materializar projetos a longo prazo.",
    "5": "Espírito livre e adaptável, atraído por mudança, variedade e experiências novas. Tem coragem para romper padrões e explorar oportunidades, mas precisa de foco para não dispersar energia em excessos; quando bem canalizado, transforma liberdade em inovação prática e movimento com propósito. A versatilidade é seu maior trunfo.",
    "6": "Pessoa com forte senso de responsabilidade, cuidado e serviço ao próximo. Tem inclinação para proteger e sustentar relações familiares e comunitárias; deve cuidar para não assumir responsabilidades alheias em excesso. Quando equilibrado, manifesta liderança afetiva e capacidade de criar ambientes seguros e nutritivos.",
    "7": "Indivíduo introspectivo e buscador do conhecimento, com inclinação para estudo, análise e desenvolvimento interior. Valoriza profundidade e reflexão; precisa de períodos de solitude para se renovar e integrar insights. Em equilíbrio, combina rigor intelectual com sensibilidade espiritual, atraindo oportunidades de crescimento interno.",
    "8": "Perfil orientado ao poder pessoal, gestão e realização material. Tem habilidade para administrar recursos, estruturar negócios e alcançar metas ambiciosas; exige ética e equilíbrio para que o foco em resultados não se sobreponha a valores humanos. Quando bem conduzido, traduz autoridade em prosperidade sustentável.",
    "9": "Pessoa voltada para conclusão de ciclos, compaixão e serviço coletivo. Tem visão ampla e tendência a atuar em causas que beneficiem grupos; precisa cuidar da própria energia para não se esgotar em altruísmo. Em sua melhor expressão, combina idealismo com ação prática em prol do bem comum.",
    "11": "Número mestre ligado à intuição ampliada, sensibilidade e inspiração profunda. Indica potencial para insights transformadores e conexão com níveis sutis de percepção; exige maturidade emocional para canalizar a sensibilidade sem se perder em instabilidade. Quando integrado, abre portas para liderança visionária baseada em intuição e empatia.",
    "22": "Número mestre associado à capacidade de manifestar grandes projetos e estruturar visões em escala prática. Representa habilidade para combinar visão ampla com competência técnica e disciplina; requer integridade e responsabilidade para que o poder de realização gere impacto positivo. Em equilíbrio, é a força de construção de legados duradouros.",
    "33": "Número mestre do serviço e do amor aplicado, indicando chamado para atuação altruísta e cura coletiva. Traz grande sensibilidade emocional e responsabilidade espiritual; exige equilíbrio pessoal para sustentar o peso da missão. Quando vivido com consciência, manifesta liderança compassiva e transformação social através do exemplo.",
    "44": "44 indica uma energia de construção em grande escala aplicada ao mundo material e social. Pessoas com 44 têm talento para estruturar sistemas, criar organizações sólidas e transformar visões em realidades duradouras; exigem disciplina, ética e habilidade para delegar para evitar sobrecarga. Quando desequilibrado, manifesta rigidez e autoritarismo.",
    "55": "55 amplia o arquétipo do 5: movimento, mudança e adaptação, mas em escala ampliada. Traz coragem para romper estruturas obsoletas e criar novas possibilidades sociais e pessoais. Requer discernimento para não cair em impulsividade ou fanatismo; quando bem canalizado, gera revoluções construtivas.",
    "66": "66 representa um amor e serviço ampliados, com foco em cura, proteção e criação de ambientes seguros para grupos. Indica habilidade para liderar iniciativas de suporte social, educação e bem-estar. Em desequilíbrio, tende a codependência e sacrifício excessivo.",
    "77": "77 intensifica o 7, trazendo uma busca por conhecimento esotérico e compreensão profunda dos padrões sutis. Favorece pesquisadores, místicos e pensadores que trabalham com síntese de saberes. Pode levar ao isolamento se não houver integração prática.",
    "88": "88 é um número de grande potência material e organizacional, indicando habilidade para criar sistemas de prosperidade e impacto financeiro amplo. Requer equilíbrio entre ambição e valores; quando bem usado, gera prosperidade sustentável e legado; quando mal usado, pode gerar exploração.",
    "99": "99 simboliza o fim de ciclos em escala coletiva e o chamado para agir com compaixão universal. Indica vocação para trabalho humanitário, arte transformadora e liderança ética que beneficia grandes grupos. Exige desapego pessoal e maturidade para sustentar a missão."
}

def name_value_cabal(full_name: str, letter_map_df=None, keep_master: bool = True):
    """Calcula valor cabalístico do nome usando CABALISTIC_MAP."""
    name = _letters_only(full_name)
    total = sum(cabalistic_letter_value(ch) for ch in name)
    return {"value": reduce_number(total, keep_masters=keep_master), "raw": total}

def quantics_from_dob(dob: date, keep_master: bool = True):
    """Calcula três números quânticos a partir da data de nascimento."""
    d, m, y = dob.day, dob.month, dob.year
    q1 = reduce_number(d + m, keep_masters=keep_master)
    q2 = reduce_number(d + y, keep_masters=keep_master)
    q3 = reduce_number(m + y, keep_masters=keep_master)
    return [q1, q2, q3]

# -------------------------
# Relatório completo (agora com pinnacles, personal year/month/day e influência anual)
# -------------------------
def full_numerology_report(full_name: str, dob: date, method: str = "pythagorean", keep_masters: bool = True,
                          reference_date: Optional[date] = None) -> Dict[str, Any]:
    if reference_date is None:
        reference_date = date.today()

    # life_path: desempacotar se necessário
    lp_value, lp_raw = life_path_from_dob(dob, keep_masters=keep_masters)

    # Pitagórica: master_min padrão 11
    expr = expression_number(full_name, method=method, keep_masters=keep_masters, master_min=11)
    expr_raw = expression_total(full_name, method=method)
    soul = soul_urge_number(full_name, method=method, keep_masters=keep_masters, master_min=11)
    soul_raw = soul_urge_total(full_name, method=method)
    pers = personality_number(full_name, method=method, keep_masters=keep_masters, master_min=11)
    pers_raw = personality_total(full_name, method=method)

    power_num = power_number_from_dob(dob, keep_masters=keep_masters, master_min=11)

    mat = maturity_number(lp_value, expr, keep_masters=keep_masters, master_min=11)

    pinnacles = pinnacles_from_dob(dob, keep_masters=keep_masters)

    py = personal_year(lp_value, year=reference_date.year, keep_masters=keep_masters)
    pm = personal_month(py, reference_date.month, keep_masters=keep_masters)
    pd = personal_day(pm, reference_date.day, keep_masters=keep_masters)

    annual_infl = annual_influence_by_name(full_name, keep_masters=keep_masters)

    def _get_text(n):
        key = str(n) if n is not None else ""
        short = NUM_INTERPRETATIONS_SHORT.get(key, "")
        medium = NUM_INTERPRETATIONS_MEDIUM.get(key, "")
        long_text = ""
        if key:
            long_text = NUM_INTERPRETATIONS_LONG.get(key, "") if 'NUM_INTERPRETATIONS_LONG' in globals() else ""
            if not long_text:
                try:
                    long_text = NUM_TEMPLATES.get(int(key), {}).get("long", "")
                except Exception:
                    long_text = ""
        return {"number": n, "short": short, "medium": medium, "long": long_text}

    # calcular Número de Poder (dia + mês)
    report = {
        "method": method,
        "full_name": full_name,
        "dob": dob.isoformat(),
        "reference_date": reference_date.isoformat(),
        "life_path": {"value": lp_value, "raw": lp_raw, **_get_text(lp_value)},
        "expression": {"value": expr, **_get_text(expr)},
        "soul_urge": {"value": soul, **_get_text(soul)},
        "personality": {"value": pers, **_get_text(pers)},
        "maturity": {"value": mat, **_get_text(mat)},
        "power_number": {"value": power_num.get("value"), "raw": power_num.get("raw"), **_get_text(power_num.get("value"))},
        "pinnacles": pinnacles,
        "personal": {
            "year": {"value": py, "description": NUM_INTERPRETATIONS_SHORT.get(str(py), "")},
            "month": {"value": pm, "description": NUM_INTERPRETATIONS_SHORT.get(str(pm), "")},
            "day": {"value": pd, "description": NUM_INTERPRETATIONS_SHORT.get(str(pd), "")}
        },
        "annual_influence_by_name": {"letters_count": len(_letters_only(full_name)), "value": annual_infl},
    }
    return report

# -------------------------
# Cabalistic wrapper (usa mapeamento cabalístico para componentes do nome)
# -------------------------
def full_cabalistic_report(full_name: str, dob: date, keep_masters: bool = True, reference_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Relatório completo usando mapeamento cabalístico.
    Prioriza textos vindos de NUM_TEMPLATES (short/medium/long) quando disponíveis.
    Não inclui 'pinnacles' no relatório (removido por solicitação).
    """
    if reference_date is None:
        reference_date = date.today()

    # life_path: desempacotar se necessário
    lp_value, lp_raw = life_path_from_dob(dob, keep_masters=keep_masters)

    # componentes do nome (cabalístico) — master_min=22 para cabalística
    expr = expression_number(full_name, method="cabalistic", keep_masters=keep_masters, master_min=22)
    expr_raw = expression_total(full_name, method="cabalistic")
    soul = soul_urge_number(full_name, method="cabalistic", keep_masters=keep_masters, master_min=22)
    soul_raw = soul_urge_total(full_name, method="cabalistic")
    pers = personality_number(full_name, method="cabalistic", keep_masters=keep_masters, master_min=22)
    pers_raw = personality_total(full_name, method="cabalistic")

    # maturidade
    mat = maturity_number(lp_value, expr, keep_masters=keep_masters, master_min=22)

    # anos/mês/dia pessoais (usar convenção do módulo)
    py = personal_year(lp_value, year=reference_date.year, keep_masters=keep_masters)
    pm = personal_month(py, reference_date.month, keep_masters=keep_masters)
    pd = personal_day(pm, reference_date.day, keep_masters=keep_masters)

    # influência anual
    annual_infl = annual_influence_by_name(full_name, keep_masters=keep_masters, mode="cabalistic")

    # no report:
    

    # auxiliar: prioriza NUM_TEMPLATES[int] -> NUM_INTERPRETATIONS_* (string keys) -> fallback vazio
    def _get_text_cabalistic(n):
        key = str(n) if n is not None else ""
        short = ""
        medium = ""
        long_text = ""

        # 1) tentar NUM_TEMPLATES por inteiro (prioridade cabalística)
        if key and key.isdigit():
            try:
                ik = int(key)
                tmpl = NUM_TEMPLATES.get(ik, {}) or {}
                short = tmpl.get("short", "") or ""
                medium = tmpl.get("medium", "") or ""
                long_text = tmpl.get("long", "") or ""
            except Exception:
                short = short or ""
                medium = medium or ""
                long_text = long_text or ""

        # # 2) fallback para os mapas de interpretação (se NUM_TEMPLATES não tiver)
        # if not short:
        #     short = NUM_INTERPRETATIONS_SHORT.get(key, "")
        # if not medium:
        #     medium = NUM_INTERPRETATIONS_MEDIUM.get(key, "")
        # if not long_text:
        #     long_text = NUM_INTERPRETATIONS_LONG.get(key, "") if 'NUM_INTERPRETATIONS_LONG' in globals() else ""

        return {"number": n, "short": short, "medium": medium, "long": long_text}

    # calcular Número de Poder (dia + mês) para cabalística (master_min=22)
    power_num = power_number_from_dob(dob, keep_masters=keep_masters, master_min=22) or {"value": None, "raw": None}

    # construir relatório (sem 'pinnacles')
    report = {
        "method": "cabalistic",
        "full_name": full_name,
        "dob": dob.isoformat(),
        "reference_date": reference_date.isoformat(),
        "life_path": {"value": lp_value, "raw": lp_raw, **_get_text_cabalistic(lp_value)},
        "expression": {"value": expr, "raw": expr_raw, **_get_text_cabalistic(expr)},
        "soul_urge": {"value": soul, "raw": soul_raw, **_get_text_cabalistic(soul)},
        "personality": {"value": pers, "raw": pers_raw, **_get_text_cabalistic(pers)},
        "maturity": {"value": mat, **_get_text_cabalistic(mat)},
        "power_number": {
            "value": power_num.get("value"),
            "raw": power_num.get("raw"),
            **_get_text_cabalistic(power_num.get("value"))
        },
        "personal": {
            "year": {"value": py, "description": NUM_INTERPRETATIONS_SHORT.get(str(py), "")},
            "month": {"value": pm, "description": NUM_INTERPRETATIONS_SHORT.get(str(pm), "")},
            "day": {"value": pd, "description": NUM_INTERPRETATIONS_SHORT.get(str(pd), "")}
        },
        "annual_influence_by_name": {"letters_count": annual_infl.get("raw"),"value": annual_infl.get("value")}
    }

    return report