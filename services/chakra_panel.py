# services/chakra_panel.py (adicionar)
from pathlib import Path
from typing import Optional, Dict
from PIL import Image
import io

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_CHAKRA_DIR = BASE_DIR / "assets" / "chakras"

def _normalize_chakra_name(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return str(raw).strip().lower().replace(" ", "_")

def _find_chakra_image(chakra_name: str, assets_dir: Path = DEFAULT_CHAKRA_DIR) -> Optional[Path]:
    if not chakra_name:
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = assets_dir / f"{chakra_name}.{ext}"
        if p.exists():
            return p
    return None

def render_chakra_image(st, annual: Dict = None, assets_dir: Optional[str] = None, target_col=None):
    """
    Renderiza apenas a imagem do chakra correspondente ao `annual`.
    - annual: dicionário já calculado (ex.: ann_analysis)
    - target_col: coluna Streamlit onde a imagem deve ser renderizada (opcional)
    """
    if annual is None:
        return

    assets_path = Path(assets_dir) if assets_dir else DEFAULT_CHAKRA_DIR
    chakra_raw = annual.get("chakra") or annual.get("chakra_name")
    chakra_key = _normalize_chakra_name(chakra_raw)
    img_path = _find_chakra_image(chakra_key, assets_dir=assets_path) if chakra_key else None

    draw = target_col if target_col is not None else st

    if img_path and img_path.exists():
        try:
            draw.image(str(img_path), use_container_width=True, caption=chakra_raw)
        except Exception:
            try:
                with open(img_path, "rb") as f:
                    img = Image.open(io.BytesIO(f.read()))
                    draw.image(img, use_container_width=True, caption=chakra_raw)
            except Exception:
                if st.session_state.get("debug_influences"):
                    st.exception("Erro ao abrir imagem do chakra")
                else:
                    draw.warning("Erro ao abrir a imagem do chakra.")
    else:
        draw.info("Imagem do chakra não encontrada. Verifique assets/chakras/ e nomes dos arquivos.")
        # debug opcional: listar arquivos detectados
        try:
            if assets_path.exists():
                files = sorted([p.name for p in assets_path.iterdir() if p.is_file()])
                draw.write("Arquivos detectados:", files)
            else:
                draw.write(f"Pasta de assets não encontrada: {assets_path}")
        except Exception:
            pass