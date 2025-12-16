# app.py - wrapper que executa pages/Inicio.py como entrypoint
from pathlib import Path
import importlib.util
import logging
import streamlit as st

logger = logging.getLogger("app_wrapper")

def _call_inicio_main():
    # tentativa direta de import (se houver module importável)
    try:
        from pages.Inicio import main as inicio_main  # type: ignore
        if callable(inicio_main):
            inicio_main()
            return
    except Exception:
        logger.debug("Import direto pages.Inicio falhou, prosseguindo com busca por arquivo", exc_info=True)

    # localizar diretório pages relativo a este arquivo e ao cwd
    base_dirs = [
        Path(__file__).parent,  # onde app.py está
        Path.cwd()               # diretório atual de execução
    ]
    pages_dir = None
    for bd in base_dirs:
        candidate = bd / "pages"
        if candidate.is_dir():
            pages_dir = candidate
            break

    if pages_dir is None:
        st.error("Diretório pages/ não encontrado. Execute o app a partir da raiz do projeto.")
        logger.error("pages/ não encontrado em %s ou %s", Path(__file__).parent, Path.cwd())
        return

    # procurar arquivos que contenham 'inicio' no nome (case-insensitive)
    candidates = sorted(pages_dir.glob("*[Ii]nicio*.py")) + sorted(pages_dir.glob("*Inicio*.py")) + sorted(pages_dir.glob("*inicio*.py"))
    if not candidates:
        st.error("Nenhum arquivo contendo 'Inicio' encontrado em pages/. Verifique o nome do arquivo.")
        logger.error("Nenhum arquivo Inicio encontrado em %s", pages_dir)
        return

    found = candidates[0]
    logger.info("Carregando dinamicamente %s", found)
    try:
        spec = importlib.util.spec_from_file_location("pages_inicio_dynamic", str(found))
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        spec.loader.exec_module(module)
        if hasattr(module, "main") and callable(module.main):
            module.main()
        else:
            st.error(f"{found.name} não define uma função pública 'main()'.")
            logger.error("%s não define main()", found)
    except Exception as e:
        logger.exception("Falha ao carregar %s dinamicamente: %s", found, e)
        st.error("Erro ao iniciar a página Início. Veja logs do servidor para detalhes.")

if __name__ == "__main__":
    _call_inicio_main()
