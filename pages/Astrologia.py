# pages/Astrologia.py
# Wrapper para exibir "Astrologia" no sidebar e reaproveitar mapa_astral.py

import runpy
import os

# caminho relativo ao root do app; ajuste se necessário
script_path = os.path.join(os.path.dirname(__file__), "mapa_astral.py")

# executa o script como se fosse a página principal
runpy.run_path(script_path, run_name="__main__")