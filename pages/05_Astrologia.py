# pages/Astrologia.py
import streamlit as st
from pathlib import Path
import importlib.util

# set_page_config deve ser a primeira chamada Streamlit neste arquivo
st.set_page_config(page_title="Astrologia", layout="wide")

# caminhos candidatos
candidates = [
    Path(__file__).parent / "mapa_astral.py",
    Path(__file__).parent / "_src" / "mapa_astral.py",
    Path(__file__).parent.parent / "src" / "mapa_astral.py",
]

found = next((p for p in candidates if p.is_file()), None)
if not found:
    st.error("Arquivo mapa_astral.py não encontrado. Verifique o caminho.")
else:
    spec = importlib.util.spec_from_file_location("mapa_astral_dynamic", str(found))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # preferir chamar uma função pública do módulo
    if hasattr(module, "main") and callable(module.main):
        module.main()
    elif hasattr(module, "main_inicio") and callable(module.main_inicio):
        module.main_inicio()
    else:
        st.error("mapa_astral.py não define uma função pública 'main' ou 'main_inicio'.")