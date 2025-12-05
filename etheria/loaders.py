# etheria/loaders.py
"""
Leitores e transformações de dados para Etheria.

Principais responsabilidades:
- Ler matrix_hour.csv e correlations.csv
- Normalizar nomes de dias para português (Segunda-feira .. Domingo)
- Normalizar horas para formato HH:MM e permitir reordenação iniciando em 06:00
- Construir matrizes por tipo (Hour x Weekday) com colunas em ordem Segunda..Domingo
- Fornecer utilitários de validação
"""

from typing import Dict, Optional, Union, Any, List
from collections import OrderedDict
import pandas as pd
import unicodedata

# -------------------------
# Configurações e mapeamentos
# -------------------------
WEEKDAYS_ORDER = [
    "Segunda-feira", "Terça-feira", "Quarta-feira",
    "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"
]

_weekday_map = {
    "monday": "Segunda-feira", "mon": "Segunda-feira", "segunda": "Segunda-feira", "segunda-feira": "Segunda-feira",
    "tuesday": "Terça-feira", "tue": "Terça-feira", "terça": "Terça-feira", "terça-feira": "Terça-feira",
    "wednesday": "Quarta-feira", "wed": "Quarta-feira", "quarta": "Quarta-feira", "quarta-feira": "Quarta-feira",
    "thursday": "Quinta-feira", "thu": "Quinta-feira", "quinta": "Quinta-feira", "quinta-feira": "Quinta-feira",
    "friday": "Sexta-feira", "fri": "Sexta-feira", "sexta": "Sexta-feira", "sexta-feira": "Sexta-feira",
    "saturday": "Sábado", "sat": "Sábado", "sabado": "Sábado", "sábado": "Sábado",
    "sunday": "Domingo", "sun": "Domingo", "domingo": "Domingo"
}

# -------------------------
# Normalizadores básicos
# -------------------------
def _normalize_text(x: Any) -> str:
    if x is None:
        return ""
    s = str(x).strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s

def _norm_hour(h: Any) -> str:
    """
    Normaliza valores de hora para 'HH:MM'.
    Aceita inteiros (6 -> '06:00'), strings '6', '06:00', '6:00', '06h00', etc.
    Se não for possível converter, retorna a string original normalizada.
    """
    if pd.isna(h):
        return ""
    if isinstance(h, (int, float)) and not isinstance(h, bool):
        return f"{int(h) % 24:02d}:00"
    s = _normalize_text(h).lower().replace("h", ":").replace(".", ":")
    # remover espaços
    s = s.replace(" ", "")
    if ":" in s:
        parts = s.split(":")
        try:
            hh = int(parts[0]) % 24
            mm = int(parts[1]) if len(parts) > 1 and parts[1] != "" else 0
            mm = mm % 60
            return f"{hh:02d}:{mm:02d}"
        except Exception:
            return s
    try:
        n = int(s)
        return f"{n % 24:02d}:00"
    except Exception:
        return s

def _norm_weekday(w: Any) -> str:
    """
    Normaliza nomes de dia para a forma em português 'Segunda-feira', etc.
    Se não reconhecer, capitaliza a string normalizada.
    """
    s = _normalize_text(w).lower()
    return _weekday_map.get(s, s.capitalize())

# -------------------------
# Funções de reordenação e utilitários de horas/dias
# -------------------------
def generate_hours_list(start_hour: int = 6, step: int = 1, count: int = 24) -> List[str]:
    """
    Gera lista de horas no formato 'HH:MM' começando em start_hour.
    Ex.: start_hour=6, count=24 -> ['06:00','07:00',...,'05:00']
    """
    hours = []
    for i in range(count):
        h = (start_hour + i) % 24
        hours.append(f"{h:02d}:00")
    return hours

def reorder_weekday_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normaliza nomes das colunas (dias) para português e reordena para começar em Segunda-feira.
    Colunas extras (não reconhecidas) são mantidas ao final na ordem original.
    """
    df2 = df.copy()
    # normalizar nomes
    new_cols = [ _norm_weekday(c) for c in df2.columns ]
    df2.columns = new_cols
    # construir ordem final
    ordered = [d for d in WEEKDAYS_ORDER if d in df2.columns]
    extras = [c for c in df2.columns if c not in ordered]
    final_cols = ordered + extras
    return df2.reindex(columns=final_cols)

def reorder_hours_index(df: pd.DataFrame, start_hour: int = 6) -> pd.DataFrame:
    """
    Reordena o índice do DataFrame (horas) para começar em start_hour.
    Aceita índices no formato 'HH:MM', inteiros 0..23, ou strings variados.
    Linhas que não coincidirem com a sequência gerada são mantidas após as desejadas.
    """
    df2 = df.copy()
    # converter índice para 'HH:MM' quando possível
    def to_hhmm(x):
        try:
            if isinstance(x, str) and ":" in x:
                hh = int(x.split(":")[0]) % 24
                return f"{hh:02d}:00"
            if isinstance(x, (int, float)) and not isinstance(x, bool):
                return f"{int(x) % 24:02d}:00"
            if hasattr(x, "hour"):
                return f"{x.hour:02d}:00"
        except Exception:
            pass
        return _normalize_text(x)

    new_index = [to_hhmm(i) for i in df2.index]
    df2.index = new_index

    desired = generate_hours_list(start_hour=start_hour, count=len(df2.index))
    # se tamanhos diferentes, gerar desired com mesmo tamanho
    if len(desired) != len(df2.index):
        desired = generate_hours_list(start_hour=start_hour, count=len(df2.index))

    present = [h for h in desired if h in df2.index]
    extras = [h for h in df2.index if h not in present]
    final_index = present + extras
    return df2.reindex(final_index)

# -------------------------
# Leitura e transformação (principal)
# -------------------------
def read_matrix_csv(path: str, sep: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    """
    Lê matrix_hour CSV e retorna DataFrame wide (sem normalizar colunas/índice).
    """
    df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str)
    return df

def wide_matrix_to_long(df_wide: pd.DataFrame, hour_col: Optional[str] = None) -> pd.DataFrame:
    """
    Converte matriz Hour x Weekday (wide) para long: Hour, Weekday, ArcanoNumber.
    Normaliza Hour para 'HH:MM' e Weekday para português.
    """
    if hour_col is None:
        hour_col = df_wide.columns[0]
    df = df_wide.copy()
    if hour_col not in df.columns:
        raise ValueError(f"Coluna de hora '{hour_col}' não encontrada")
    df = df.rename(columns={hour_col: "Hour"})
    day_cols = [c for c in df.columns if c != "Hour"]
    if not day_cols:
        raise ValueError("Nenhuma coluna de dia detectada na matrix wide")
    long = df.melt(id_vars=["Hour"], value_vars=day_cols, var_name="Weekday", value_name="ArcanoNumber")
    long["Hour"] = long["Hour"].apply(_norm_hour)
    long["Weekday"] = long["Weekday"].apply(_norm_weekday)
    long["ArcanoNumber"] = pd.to_numeric(long["ArcanoNumber"], errors="coerce").astype("Int64")
    long = long.dropna(subset=["ArcanoNumber"]).reset_index(drop=True)
    return long

def read_correlations(path: Union[str, pd.DataFrame], sep: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    """
    Lê correlations.csv (ou DataFrame já carregado) e normaliza a coluna Arcano.
    Detecta automaticamente a coluna que representa o arcano.
    """
    if isinstance(path, pd.DataFrame):
        df = path.copy()
    else:
        df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str)

    cols_map = {c.lower(): c for c in df.columns}
    arc_col = None
    for candidate in ("arcano", "arcano_number", "number", "id"):
        if candidate in cols_map:
            arc_col = cols_map[candidate]
            break
    if arc_col is None:
        arc_col = df.columns[0]
    df = df.rename(columns={arc_col: "Arcano"})
    df["Arcano"] = pd.to_numeric(df["Arcano"], errors="coerce").astype("Int64")
    return df

def join_matrix_with_map(df_long: pd.DataFrame, df_map: pd.DataFrame) -> pd.DataFrame:
    """
    Junta df_long (Hour, Weekday, ArcanoNumber) com df_map (Arcano, atributos...).
    """
    merged = df_long.merge(df_map, left_on="ArcanoNumber", right_on="Arcano", how="left")
    return merged

# -------------------------
# Lista autorizada de tipos (ordem preferencial)
# -------------------------
ALLOWED_TYPES = [
    "Arcano",
    "Chacra",
    "Cor",
    "Dhyani Kumara"
    "Elemento",
    "Glândulas",
    "Incenso",
    "Metal",
    "Nota Musical",
    "Pedra",
    "Perfume",
    "Planeta",
    "Tattva",
]

# Mapa de sinônimos/colunas comuns para normalizar cabeçalhos do correlations.csv
COLUMN_SYNONYMS = {
    "arcano": "Arcano",
    "planeta": "Planeta",
    "cor": "Cor",
    "tattva": "Tattva",
    "chakra": "Chacra",
    "chacra": "Chacra",
    "glandulas": "Glândulas",
    "glândulas": "Glândulas",
    "nota musical": "Nota Musical",
    "elemento": "Elemento",
    "metal": "Metal",
    "pedra": "Pedra",
    "perfume": "Perfume",
    "incenso": "Incenso",
    "dhyani kumara": "Dhyani Kumara",
}

# --- normalize_map_columns (substituir/colar) ---
def normalize_map_columns(df: pd.DataFrame) -> pd.DataFrame:
    df2 = df.copy()
    cols_map = {}
    used = {}
    for c in df2.columns:
        key = _normalize_text(c).lower().replace(" ", "_")
        canon = COLUMN_SYNONYMS.get(key, _normalize_text(c))
        if canon in used:
            used[canon] += 1
            new_name = f"{canon}_{used[canon]}"
        else:
            used[canon] = 1
            new_name = canon
        cols_map[c] = new_name
    return df2.rename(columns=cols_map)

# --- read_correlations (substituir/colar) ---
def read_correlations(path: Union[str, pd.DataFrame], sep: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    """
    Lê correlations.csv (ou DataFrame já carregado), normaliza colunas e garante
    que exista a coluna 'Arcano' (Int) e colunas canônicas para ALLOWED_TYPES quando presentes.
    """
    if isinstance(path, pd.DataFrame):
        df = path.copy()
    else:
        df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str)

    # normalizar colunas para nomes canônicos
    df = normalize_map_columns(df)

    # detectar coluna Arcano (já renomeada se possível)
    cols_map = {c.lower(): c for c in df.columns}
    arc_col = None
    for candidate in ("arcano", "arcano_number", "number", "id"):
        if candidate in cols_map:
            arc_col = cols_map[candidate]
            break
    if arc_col is None:
        arc_col = df.columns[0]
    df = df.rename(columns={arc_col: "Arcano"})
    df["Arcano"] = pd.to_numeric(df["Arcano"], errors="coerce").astype("Int64")

    # garantir colunas canônicas presentes (mesmo que vazias)
    for t in ALLOWED_TYPES:
        if t not in df.columns:
            df[t] = pd.NA

    return df

# --- build_type_matrices (substituir/colar) ---
def build_type_matrices(df_merged: pd.DataFrame, start_hour: int = 6) -> Dict[str, pd.DataFrame]:
    """
    Gera dicionário Type -> wide matrix (Hour x Weekday) apenas para os tipos
    permitidos em ALLOWED_TYPES. Reordena colunas para Segunda..Domingo e horas a partir de start_hour.
    Esta versão trata colunas duplicadas e garante checagens escalares.
    """
    # defensive copy
    df_merged = df_merged.copy()

    # 1) Normalizar nomes de colunas usando COLUMN_SYNONYMS (se aplicável)
    map_cols = {}
    for c in df_merged.columns:
        key = _normalize_text(c).lower().replace(" ", "_")
        if key in COLUMN_SYNONYMS:
            map_cols[c] = COLUMN_SYNONYMS[key]
        else:
            map_cols[c] = c
    df_merged = df_merged.rename(columns=map_cols)

    # 2) Detectar e resolver colunas duplicadas (manter a primeira ocorrência)
    if df_merged.columns.duplicated().any():
        # opcional: log para depuração
        dup_cols = [c for i, c in enumerate(df_merged.columns) if df_merged.columns.duplicated()[i]]
        try:
            import streamlit as _st
            _st.sidebar.write("Aviso: colunas duplicadas detectadas e removidas:", dup_cols)
        except Exception:
            print("Aviso: colunas duplicadas detectadas e removidas:", dup_cols)

        # substituir por (remover aviso):
        # (nenhuma chamada de log)
        pass

    # 3) Construir lista de tipos presentes, respeitando a ordem de ALLOWED_TYPES
    present_types = [t for t in ALLOWED_TYPES if t in df_merged.columns]

    matrices: Dict[str, pd.DataFrame] = OrderedDict()
    for t in present_types:
        # pular se coluna inexistente (defensivo) ou totalmente vazia
        if t not in df_merged.columns:
            continue

        col_series = df_merged[t]
        # garantir que temos uma Series (se por algum motivo ainda for DataFrame, pegar a primeira coluna)
        if isinstance(col_series, pd.DataFrame):
            # pegar a primeira coluna do DataFrame resultante
            col_series = col_series.iloc[:, 0]

        # se toda a coluna for NA, pular
        if col_series.isna().all():
            continue

        # pivot usando o DataFrame original (que contém a coluna t)
        pivot = pd.pivot_table(df_merged, index="Hour", columns="Weekday", values=t, aggfunc="first", dropna=False)

        # normalizar colunas e reordenar para Segunda..Domingo
        pivot = reorder_weekday_columns(pivot)

        # ordenar índice de horas numericamente e reindexar para iniciar em start_hour
        def _hour_key(h: str) -> int:
            try:
                return int(str(h).split(":")[0])
            except Exception:
                return 999

        pivot = pivot.reindex(sorted(pivot.index, key=_hour_key))
        pivot = reorder_hours_index(pivot, start_hour=start_hour)
        matrices[t] = pivot

    return matrices

# -------------------------
# Utilitários de leitura de tabelas de ciclo (opcional)
# -------------------------
def read_cycle_table(path: Union[str, pd.DataFrame], sep: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    """
    Lê uma tabela de ciclo (Year, Planet) ou (Index, Planet) e normaliza colunas.
    Retorna DataFrame com colunas ['Year','Planet'] quando possível.
    """
    if isinstance(path, pd.DataFrame):
        df = path.copy()
    else:
        df = pd.read_csv(path, sep=sep, encoding=encoding, dtype=str)
    cols = {c.lower(): c for c in df.columns}
    # detectar coluna de ano/índice
    if "year" in cols:
        ycol = cols["year"]
    elif "ano" in cols:
        ycol = cols["ano"]
    else:
        ycol = df.columns[0]
    # detectar coluna planeta
    if "planet" in cols:
        pcol = cols["planet"]
    elif "planeta" in cols:
        pcol = cols["planeta"]
    else:
        pcol = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    df2 = df.rename(columns={ycol: "Year", pcol: "Planet"})[["Year", "Planet"]].copy()
    # tentar converter Year para int quando possível
    try:
        df2["Year"] = df2["Year"].astype(int)
    except Exception:
        pass
    df2["Planet"] = df2["Planet"].astype(str)
    return df2

# -------------------------
# Validação e relatório
# -------------------------
def validation_report(df_long: pd.DataFrame, df_map: pd.DataFrame) -> Dict[str, object]:
    """
    Retorna um dicionário com informações de validação:
    - arcanos_na_matrix: lista de arcanos presentes na matrix
    - arcanos_no_map: lista de arcanos no mapa
    - missing_arcanos: arcanos presentes na matrix mas ausentes no mapa
    - types_detected: colunas detectadas no mapa (exceto Arcano)
    - coverage_per_type: contagem de valores por tipo (tratando colunas duplicadas)
    """
    def _count_non_na(col):
        """
        Conta valores não-nulos em 'col', onde col pode ser uma Series ou um DataFrame.
        Se for DataFrame (colunas duplicadas), considera a primeira célula não-nula por linha.
        """
        if isinstance(col, pd.Series):
            return int(col.notna().sum())
        if isinstance(col, pd.DataFrame):
            # para cada linha, pegar a primeira ocorrência não-nula entre as colunas duplicadas
            def first_non_na(row):
                non_na = row.dropna()
                return non_na.iloc[0] if not non_na.empty else pd.NA
            combined = col.apply(first_non_na, axis=1)
            return int(combined.notna().sum())
        # fallback defensivo
        try:
            return int(pd.Series(col).notna().sum())
        except Exception:
            return 0

    arcanos_matrix = sorted(df_long["ArcanoNumber"].dropna().unique().tolist())
    arcanos_map = sorted(df_map["Arcano"].dropna().unique().tolist())
    missing = sorted(set(arcanos_matrix) - set(arcanos_map))
    types = [c for c in df_map.columns if c.lower() != "arcano"]
    coverage = {}
    for t in types:
        try:
            coverage[t] = _count_non_na(df_map[t]) if t in df_map.columns else 0
        except Exception:
            # fallback seguro
            coverage[t] = 0
    return {
        "arcanos_na_matrix": arcanos_matrix,
        "arcanos_no_map": arcanos_map,
        "missing_arcanos": missing,
        "types_detected": types,
        "coverage_per_type": coverage
    }

# -------------------------
# Execução rápida (para debug)
# -------------------------
if __name__ == "__main__":
    # teste rápido de normalização
    df = pd.DataFrame({
        "Hora": [6, 7, "08:00", "09h00"],
        "monday": [1, 2, 3, 4],
        "tuesday": [5, 6, 7, 8]
    })
    print("Wide original:")
    print(df)
    long = wide_matrix_to_long(df, hour_col="Hora")
    print("\nLong:")
    print(long)
    matrices = build_type_matrices(join_matrix_with_map(long, pd.DataFrame({"Arcano":[1,2,3,4],"Planeta":["Sol","Lua","Marte","Vênus"]})))
    print("\nMatrizes geradas:")
    for k,v in matrices.items():
        print(k)
        print(v.head())