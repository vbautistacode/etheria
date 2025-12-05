# exceções customizadas.
# exceptions.py

class DataValidationError(Exception):
    """Erro ao validar planilha ou dados de entrada."""
    pass

class MissingTableError(Exception):
    """Erro quando uma tabela esperada não foi carregada."""
    pass