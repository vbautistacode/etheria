# src/app_core.py
import logging
from datetime import date, datetime
from typing import Any, Dict, Optional

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

def _load_config_from_secrets() -> Dict[str, Optional[str]]:
    """Ler secrets do Streamlit dentro de função (não no import)."""
    return {
        "sa_json": st.secrets.get("GCP_SA_JSON"),
        "project_id": st.secrets.get("GCP_PROJECT_ID", "etheria-480312"),
        "location": st.secrets.get("GENAI_LOCATION", "us-central1"),
        "model_name": st.secrets.get("GENAI_MODEL", "gemini-2.5-flash"),
    }

def load_data() -> Dict[str, Any]:
    """Função de carregamento de dados; decore com @st.cache_data se desejar."""
    # implementar leitura de CSVs e transformações aqui
    return {}

def main_inicio():
    """Renderiza a página Início. Coloque aqui todo o código que usa st.*."""
    cfg = _load_config_from_secrets()
    st.set_page_config(page_title="Etheria", layout="wide", initial_sidebar_state="expanded")
    st.title("Etheria | Painel Esotérico")
    st.markdown("Conteúdo de boas-vindas...")

    # Exemplo: carregar dados quando necessário
    data = load_data()

    # TODO: mover aqui widgets do sidebar, inicialização de session_state, tabelas, colunas etc.

def main_numerologia():
    """Renderiza a página Numerologia."""
    st.title("Numerologia")
    # TODO: mover aqui a lógica da aba Numerologia do antigo app.py

if __name__ == "__main__":
    main_inicio()
