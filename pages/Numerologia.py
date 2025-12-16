# pages/Numerologia.py
import os, sys
ROOT = os.path.dirname(os.path.dirname(__file__))  # pasta raiz do projeto
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
    
from src.app_core import main_numerologia
main_numerologia()
