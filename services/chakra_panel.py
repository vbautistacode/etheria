# services/chakra_panel.py
import os
from typing import Optional, Dict
from PIL import Image
import io

# Caminho padrão onde as imagens devem estar
DEFAULT_CHAKRA_DIR = os.path.join("assets", "chakras")

def _normalize_chakra_name(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    return str(raw).strip().lower().replace(" ", "_")

def _find_chakra_image(chakra_name: str, assets_dir: str = DEFAULT_CHAKRA_DIR) -> Optional[str]:
    if not chakra_name:
        return None
    for ext in ("png", "jpg", "jpeg", "webp"):
        p = os.path.join(assets_dir, f"{chakra_name}.{ext}")
        if os.path.exists(p):
            return p
    return None

def _resolve_chakra_from_report(annual: Dict, numerology_module=None) -> Optional[str]:
    # tenta usar campo direto
    chakra_raw = annual.get("chakra") or annual.get("chakra_name")
    if chakra_raw:
        return chakra_raw
    # tenta derivar via numerology.quadrant_for_number se fornecido
    try:
        num = annual.get("value") or annual.get("letters_count") or annual.get("raw")
        if num is not None and numerology_module and hasattr(numerology_module, "quadrant_for_number"):
            q = numerology_module.quadrant_for_number(int(num))
            if isinstance(q, dict):
                return q.get("chakra")
    except Exception:
        pass
    return None

def render_chakra_panel(st, report: dict, assets_dir: str = DEFAULT_CHAKRA_DIR, numerology_module=None):
    """
    Renderiza duas colunas:
      - esquerda: texto com Influência Anual, número, resumo e descrição
      - direita: imagem do chakra correspondente (carregada de assets_dir)
    Parâmetros:
      - st: módulo streamlit (passar o objeto st)
      - report: dicionário que contém 'annual_influence_by_name'
      - assets_dir: pasta onde estão as imagens dos chakras
      - numerology_module: módulo numerology (opcional) para derivar chakra se não estiver no report
    """
    annual = (report or {}).get("annual_influence_by_name", {}) or {}

    # obter chakra
    chakra_raw = _resolve_chakra_from_report(annual, numerology_module=numerology_module)
    chakra_key = _normalize_chakra_name(chakra_raw)
    img_path = _find_chakra_image(chakra_key, assets_dir=assets_dir) if chakra_key else None

    # preparar textos
    letters_count = annual.get("letters_count") or annual.get("raw") or "—"
    value = annual.get("value") or "—"
    short = annual.get("short") or ""
    long = annual.get("long") or ""

    # layout em duas colunas
    col_text, col_img = st.columns([2, 1])

    # with col_text:
    #     st.markdown("**Influência** - Ciclo da Vida")
    #     st.write(f"A cada **{letters_count} anos** você passará por um novo ciclo.",
    #              help="Acontecimentos importantes ou mudanças na trajetória de vida.")
    #     st.markdown(f"**Número usado:** {value}")
    #     st.markdown(f"**Chakra:** {chakra_raw or '—'}")
    #     if short:
    #         st.markdown(f"**Resumo:** {short}")
    #     if long:
    #         st.write(long)

    with col_img:
        if img_path:
            try:
                # abrir imagem com PIL para garantir compatibilidade
                with open(img_path, "rb") as f:
                    img = Image.open(io.BytesIO(f.read()))
                    st.image(img, use_conteiner_width=True, caption=chakra_raw)
            except Exception:
                st.warning("Erro ao abrir a imagem do chakra. Verifique o arquivo em assets.")
        else:
            st.info("Imagem do chakra não encontrada. Verifique assets/chakras/ e nomes dos arquivos.")