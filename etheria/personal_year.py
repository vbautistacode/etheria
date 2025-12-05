# services/personal_year.py
from __future__ import annotations
from datetime import date, datetime
from typing import Dict, Any, Tuple

# Significados básicos por número (conforme sua especificação)
NUM_ANOESSOAL = {
    1: "Novos começos, independência, iniciativa e coragem. É o momento de plantar sementes para projetos futuros.",
    2: "Cooperação, diplomacia, desenvolvimento de relacionamentos e parcerias; fase de paciência e equilíbrio.",
    3: "Criatividade, expressão, sociabilidade e comunicação; ideal para desenvolver talentos pessoais.",
    4: "Planejamento, disciplina, estabilidade e foco em bases sólidas; bom para metas estruturadas.",
    5: "Mudança, liberdade, exploração e adaptação; período dinâmico e propício a novas experiências.",
    6: "Responsabilidade, família, comunidade e cuidado com o próximo; busca por harmonia e equilíbrio doméstico.",
    7: "Introspecção, autoconhecimento, estudo e desenvolvimento espiritual; momento para reflexão.",
    8: "Poder, conquistas materiais, sucesso e lideranças; exige trabalho intenso e foco na realização.",
    9: "Fechamento de ciclos, desapego, compaixão e preparação para novos recomeços; fase de transformação.",
}

# Templates de texto (curto e longo com aplicações práticas)
_NUM_TEMPLATES = {
    1: {
        "short": "Ano de inícios e iniciativa. Plante intenções e comece projetos com coragem.",
        "long": (
            "Este é um ano para assumir a liderança da sua vida. Priorize metas que exijam iniciativa e autonomia. "
            "Aplicações práticas: defina um projeto prioritário, estabeleça pequenos marcos semanais e tome decisões que reforcem sua independência. "
            "Evite esperar por permissão; aja com responsabilidade e coragem."
        ),
    },
    2: {
        "short": "Ano de cooperação e construção de parcerias.",
        "long": (
            "Foque em relações, diplomacia e trabalho em equipe. Este é um período para cultivar alianças e ouvir mais. "
            "Aplicações práticas: negocie com calma, invista tempo em conversas importantes, e busque compromissos que fortaleçam vínculos. "
            "Paciência e sensibilidade trarão melhores resultados do que ações impulsivas."
        ),
    },
    3: {
        "short": "Ano de expressão criativa e sociabilidade.",
        "long": (
            "A criatividade e a comunicação florescem. Aproveite para mostrar talentos e ampliar sua rede social. "
            "Aplicações práticas: participe de eventos, publique trabalhos, pratique apresentações curtas e dedique tempo a hobbies que expressem sua voz. "
            "Evite dispersão; canalize a energia criativa em projetos concretos."
        ),
    },
    4: {
        "short": "Ano de estrutura, disciplina e trabalho consistente.",
        "long": (
            "Construa bases sólidas: planejamento e rotina são seus aliados. Este é um ano para consolidar e organizar. "
            "Aplicações práticas: crie um plano de 90 dias com tarefas diárias, organize finanças e documente processos. "
            "Evite atalhos; o progresso vem com disciplina e atenção aos detalhes."
        ),
    },
    5: {
        "short": "Ano de mudanças, liberdade e experimentação.",
        "long": (
            "Mudanças e oportunidades inesperadas aparecem. Abrace a flexibilidade e explore novas direções. "
            "Aplicações práticas: teste ideias em pequena escala, viaje ou mude rotinas, e esteja aberto a aprender com o improviso. "
            "Evite compromissos rígidos demais; mantenha opções abertas."
        ),
    },
    6: {
        "short": "Ano de responsabilidade, cuidado e foco no lar.",
        "long": (
            "Priorize família, comunidade e responsabilidades afetivas. Este é um ano para cuidar e equilibrar relações. "
            "Aplicações práticas: organize compromissos domésticos, ofereça apoio prático a quem precisa e trabalhe em projetos que tragam estabilidade emocional. "
            "Evite negligenciar suas próprias necessidades ao cuidar dos outros."
        ),
    },
    7: {
        "short": "Ano de introspecção, estudo e desenvolvimento interior.",
        "long": (
            "Tempo de reflexão, pesquisa e aprofundamento espiritual ou intelectual. Reduza o ruído externo para ouvir sua intuição. "
            "Aplicações práticas: reserve períodos de estudo, meditação ou escrita reflexiva; faça cursos que aprofundem seu conhecimento. "
            "Evite decisões impulsivas; prefira observar e integrar antes de agir."
        ),
    },
    8: {
        "short": "Ano de poder, realizações materiais e liderança.",
        "long": (
            "Foco em resultados concretos, carreira e autoridade. Este ano pede ambição e trabalho estratégico. "
            "Aplicações práticas: estabeleça metas financeiras claras, negocie com confiança e delegue quando necessário. "
            "Evite atalhos éticos; o sucesso exige disciplina e responsabilidade."
        ),
    },
    9: {
        "short": "Ano de encerramentos, desapego e transformação.",
        "long": (
            "Fechamentos e liberação do que não serve mais. Prepare-se para concluir ciclos e abrir espaço para o novo. "
            "Aplicações práticas: revise projetos pendentes, faça limpezas físicas e emocionais, e planeje transições conscientes. "
            "Evite resistir às mudanças; desapegar facilita o recomeço."
        ),
    },
}


def _reduce_to_digit(n: int) -> int:
    """Reduz um número inteiro à soma dos dígitos até obter 1..9 (não considera 11/22 como mestres)."""
    s = abs(n)
    while s > 9:
        s = sum(int(d) for d in str(s))
    return s if s != 0 else 0


def personal_year_date_for_year(dob: date, year: int) -> date:
    """
    Retorna a data do aniversário no ano especificado.
    Ex.: para dob 1980-05-10 e year=2025 -> 2025-05-10
    """
    return date(year, dob.month, dob.day)


def analyze_personal_year_from_dob(dob: date, target_year: int | None = None) -> Dict[str, Any]:
    """
    Calcula e interpreta o Número Anual Pessoal para o ano target_year (por padrão, ano corrente).
    Retorna dicionário com:
      - date: data do aniversário no ano
      - reduced_number: 1..9
      - short: resumo curto
      - long: interpretação detalhada com aplicações práticas
      - base_meaning: texto do NUM_ANOESSOAL
    """
    if target_year is None:
        target_year = datetime.now().year

    ann_date = personal_year_date_for_year(dob, target_year)
    # construir número bruto: dia + mês + ano (ex.: 10/05/2025 -> 10+5+2025 = 2040)
    raw_sum = ann_date.day + ann_date.month + ann_date.year
    reduced = _reduce_to_digit(raw_sum)

    base = NUM_ANOESSOAL.get(reduced, "—")
    template = _NUM_TEMPLATES.get(reduced, {"short": base, "long": base})

    return {
        "date": ann_date.strftime("%d/%m/%Y"),
        "raw_sum": raw_sum,
        "reduced_number": reduced,
        "base_meaning": base,
        "short": template.get("short"),
        "long": template.get("long"),
    }


def interpretation_for_number(num: int) -> Dict[str, str]:
    """
    Retorna short/long/base para um número 1..9 (útil para exibir ciclos).
    """
    num = int(num)
    base = NUM_ANOESSOAL.get(num, "—")
    template = _NUM_TEMPLATES.get(num, {"short": base, "long": base})
    return {"number": num, "base": base, "short": template["short"], "long": template["long"]}