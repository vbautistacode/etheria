# pages/Numerologia.py
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import main_numerologia
main_numerologia()