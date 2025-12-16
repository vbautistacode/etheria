# app.py - wrapper que executa pages/Inicio.py como entrypoint
import streamlit as st
from pathlib import Path
import importlib.util
import logging

# set_page_config deve ser a primeira chamada st.* neste arquivo
st.set_page_config(page_title="Início", layout="wide")

logger = logging.getLogger("app_wrapper")

def _call_inicio_main():
    # tentativa direta de import (quando pages é um pacote importável)
    try:
        from pages.Inicio import main as inicio_main  # type: ignore
        if callable(inicio_main):
            inicio_main()
            return
    except Exception:
        logger.debug("Import direto pages.Inicio falhou, tentando import dinâmico", exc_info=True)

    # fallback: localizar o arquivo pages/Inicio.py e carregar dinamicamente
    candidates = [
        Path(__file__).parent / "pages" / "Inicio.py",
        Path.cwd() / "pages" / "Inicio.py",
    ]
    found = next((p for p in candidates if p.is_file()), None)
    if not found:
        st.error("Arquivo pages/Inicio.py não encontrado. Verifique a estrutura do projeto.")
        return

    try:
        spec = importlib.util.spec_from_file_location("pages_inicio_dynamic", str(found))
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        if hasattr(module, "main") and callable(module.main):
            module.main()
        else:
            st.error("pages/Inicio.py não define uma função pública 'main()'.")
    except Exception as e:
        logger.exception("Falha ao carregar pages/Inicio.py dinamicamente: %s", e)
        st.error("Erro ao iniciar a página Início. Veja logs do servidor para detalhes.")

if __name__ == "__main__":
    _call_inicio_main()
