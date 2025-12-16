# app.py - wrapper que executa pages/Inicio.py como entrypoint

from pathlib import Path
import importlib.util
import logging
import streamlit as st

logger = logging.getLogger("app_wrapper")

def _call_inicio_main():
    # tentar import direto (caso o módulo seja importável)
    try:
        from pages.Inicio import main as inicio_main  # type: ignore
        if callable(inicio_main):
            inicio_main()
            return
    except Exception:
        logger.debug("Import direto pages.Inicio falhou, prosseguindo com busca por arquivo", exc_info=True)

    pages_dir = Path(__file__).parent / "pages"
    if not pages_dir.is_dir():
        st.error(f"Diretório pages/ não encontrado em: {pages_dir}")
        return

    # procurar qualquer arquivo que contenha 'Inicio' no nome (case-insensitive)
    candidates = sorted(pages_dir.glob("*[Ii]nicio*.py"))
    if not candidates:
        # fallback mais amplo
        candidates = sorted(pages_dir.glob("*Inicio*.py")) + sorted(pages_dir.glob("*inicio*.py"))

    if not candidates:
        st.error("Nenhum arquivo contendo 'Inicio' encontrado em pages/. Verifique o nome do arquivo.")
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
    except Exception as e:
        logger.exception("Falha ao carregar %s dinamicamente: %s", found, e)
        st.error("Erro ao iniciar a página Início. Veja logs do servidor para detalhes.")


if __name__ == "__main__":
    _call_inicio_main()