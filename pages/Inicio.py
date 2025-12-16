# pages/Inicio.py
import runpy, os
script_path = os.path.join(os.path.dirname(__file__), "..", "src", "app_core.py")
runpy.run_path(os.path.abspath(script_path), run_name="__main__")
