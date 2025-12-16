# pages/Astrologia.py
import os
import importlib.util
import runpy
from pathlib import Path
import streamlit as st

# Lista de caminhos candidatos (ordem de preferência)
candidates = [
    Path(__file__).parent / "mapa_astral.py",
    Path(__file__).parent / "_src" / "mapa_astral.py",
    Path(__file__).parent / "src" / "mapa_astral.py",
    Path(__file__).parent.parent / "pages" / "_src" / "mapa_astral.py",
    Path(__file__).parent.parent / "pages" / "mapa_astral.py",
    Path(__file__).parent.parent / "src" / "mapa_astral.py",
    Path(__file__).parent.parent / "mapa_astral.py",
]

found = None
for p in candidates:
    if p.is_file():
        found = p.resolve()
        break

if not found:
    st.error(
        "Não foi possível localizar `mapa_astral.py` para a página Astrologia.\n\n"
        "Verifique onde o arquivo está no repositório e mova-o para um dos locais esperados.\n\n"
        "Locais verificados:\n" + "\n".join(str(x) for x in candidates)
    )
else:
    # Tentar importar dinamicamente se o arquivo define uma função main() ou similar
    try:
        spec = importlib.util.spec_from_file_location("mapa_astral_dynamic", str(found))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # se existir função pública para rodar a página, chame-a
        if hasattr(module, "main") and callable(module.main):
            module.main()
        elif hasattr(module, "render") and callable(module.render):
            module.render()
        else:
            # fallback: executar como script (preserva comportamento __main__)
            runpy.run_path(str(found), run_name="__main__")
    except Exception as e:
        st.error(f"Erro ao carregar {found.name}: {e}")