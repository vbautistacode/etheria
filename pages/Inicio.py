# pages/Inicio.py
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app_core import main_inicio
main_inicio()
