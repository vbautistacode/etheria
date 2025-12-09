# services/chakra_panel.py
import os
from typing import Optional, Dict
from PIL import Image
import io
from pathlib import Path

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

def render_chakra_panel(st, report: Dict = None, annual: Dict = None, assets_dir: Optional[str] = None):
    """
    Renderiza painel com texto (esquerda) e imagem do chakra (direita).
    Prioridade de dados: annual (se passado) -> report['annual_influence_by_name'] -> {}.
    """
    # prioridade: usar annual passado explicitamente
    if annual is None:
        annual = (report or {}).get("annual_influence_by_name", {}) or {}

    # resolver assets_dir
    assets_path = Path(assets_dir) if assets_dir else DEFAULT_CHAKRA_DIR

    # obter chakra diretamente do annual (sem recalcular)
    chakra_raw = annual.get("chakra") or annual.get("chakra_name")
    chakra_key = _normalize_chakra_name(chakra_raw)
    img_path = _find_chakra_image(chakra_key, assets_dir=assets_path) if chakra_key else None

    # textos
    letters_count = annual.get("letters_count") or annual.get("raw") or "—"
    value = annual.get("value") or annual.get("reduced_number") or "—"
    short = annual.get("short") or ""
    medium = annual.get("medium") or annual.get("definition") or ""
    long = annual.get("long") or ""

    # layout
    col_text, col_img = st.columns([2, 1])

    with col_text:
        st.markdown("**Influência** - Ciclo da Vida")
        st.write(f"A cada **{letters_count} anos** você passará por um novo ciclo.",
                 help="Acontecimentos importantes ou mudanças na trajetória de vida.")
        st.markdown(f"**Número usado:** {value}")
        st.markdown(f"**Chakra:** {chakra_raw or '—'}")
        if short:
            st.markdown("**Qualidade:**")
            st.write(short)
        if medium:
            st.markdown("**Definição:**")
            st.write(medium)
        if long:
            st.markdown("**Detalhe:**")
            st.write(long)

    with col_img:
        if img_path and img_path.exists():
            try:
                st.image(str(img_path), use_container_width=True, caption=chakra_raw)
            except Exception:
                # fallback com PIL
                try:
                    with open(img_path, "rb") as f:
                        img = Image.open(io.BytesIO(f.read()))
                        st.image(img, use_container_width=True, caption=chakra_raw)
                except Exception:
                    st.warning("Erro ao abrir a imagem do chakra. Verifique o arquivo em assets.")
                    if st.session_state.get("debug_influences"):
                        st.exception("Erro ao abrir imagem do chakra")
        else:
            st.info("Imagem do chakra não encontrada. Verifique assets/chakras/ e nomes dos arquivos.")
            # debug: listar arquivos detectados
            try:
                if assets_path.exists():
                    files = sorted([p.name for p in assets_path.iterdir() if p.is_file()])
                    st.write("Arquivos detectados:", files)
                else:
                    st.write(f"Pasta de assets não encontrada: {assets_path}")
            except Exception:
                pass