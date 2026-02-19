# generate_mindmap_improved.py
# Requisitos: pip install matplotlib pillow numpy
import math
import textwrap
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np

OUT_PATH = Path("mindmap.png")
W, H = 1920, 1080
DPI = 150
FONT_FAMILY = "DejaVu Sans"

center = "Guia de Biohacking e Neurofisiologia"
branches = {
    "Hemisférios Cerebrais": [
        ("Lado Esquerdo (Analista)", "Lógica e Matemática; Linguagem e Fala; Análise de Detalhes; Controle Motor Direito"),
        ("Lado Direito (Sintetizador)", "Holístico e Criativo; Processamento Espacial; Linguagem Não-Verbal; Controle Motor Esquerdo"),
        ("Corpo Caloso (Integração)", "")
    ],
    "Autorregulação (Biohacks)": [
        ("Respiração Nasal", "Narina Direita: Alerta/Simpático; Narina Esquerda: Calma/Parassimpático; Ciclo Nasal Natural"),
        ("Controle Visual", "Visão Foveal (Foco/Norepinefrina); Visão Panorâmica (Calma/Criatividade); Movimentos Sacádicos (Desarmar Stress)"),
        ("Termorregulação", "Frio: Dopamina e Resiliência; Calor: Reparação Celular")
    ],
    "Química Cerebral": [
        ("Neurotransmissores", "Dopamina (Motivação); Noradrenalina (Alerta); GABA (Calma); Acetilcolina (Aprendizado)"),
        ("Hormônios", "Cortisol (Energia/Stress); Melatonina (Sono); Ocitocina (Vínculo)")
    ],
    "Suplementação e Nutrição": [
        ("Nootrópicos", "Cafeína + L-Teanina (Foco Limpo); Alfa-GPC (Acetilcolina); Magnésio (Relaxamento); L-Tirosina (Dopamina)"),
        ("Vitaminas", "Complexo B (Energia); Vitamina D (Hormonal/Imunidade); Vitamina C (Antioxidante)"),
        ("Alimentos", "Ovos; Fígado; Sardinha")
    ],
    "Protocolos de Limite": [
        ("Jejum Intermitente", "Autofagia"),
        ("Sono Polifásico", ""),
        ("Suspiro Fisiológico", "Alívio de Stress")
    ]
}

def wrap_label(title, subtitle="", width_chars=26):
    if subtitle:
        parts = [p.strip() for p in subtitle.split(";")]
        wrapped_parts = [textwrap.fill(p, width_chars) for p in parts if p]
        subtitle_wrapped = "\n".join(wrapped_parts)
        return f"{title}\n{subtitle_wrapped}"
    else:
        return textwrap.fill(title, width_chars)

# layout params increased for spacing
fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI)
ax = fig.add_axes([0,0,1,1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

cx, cy = W/2, H/2

# center node
center_w, center_h = 520, 130
center_patch = FancyBboxPatch((cx-center_w/2, cy-center_h/2), center_w, center_h,
                             boxstyle="round,pad=0.02,rounding_size=16",
                             linewidth=1.6, facecolor="#f7fbff", edgecolor="#2b8cbe", zorder=4)
ax.add_patch(center_patch)
ax.text(cx, cy, center, ha="center", va="center",
        fontdict={"family":FONT_FAMILY,"size":20,"weight":"bold"}, color="#0b3b5a", zorder=5)

# parameters tuned for more spacing
n_branches = len(branches)
angle_step = 2*math.pi / n_branches
start_angle = -math.pi/2
RADIUS = 460  # increased radius
branch_box_w, branch_box_h = 300, 70
sub_radius = 220  # increased subnode radius
sub_box_base_w, sub_box_base_h = 320, 80

all_sub_positions = []

for i, (bname, items) in enumerate(branches.items()):
    angle = start_angle + i*angle_step
    bx = cx + math.cos(angle)*RADIUS
    by = cy + math.sin(angle)*RADIUS

    # branch label
    branch_label = wrap_label(bname, "", width_chars=20)
    branch_patch = FancyBboxPatch((bx-branch_box_w/2, by-branch_box_h/2), branch_box_w, branch_box_h,
                                 boxstyle="round,pad=0.02,rounding_size=12",
                                 linewidth=1.0, facecolor="#e9f7f9", edgecolor="#66b8d6", zorder=3)
    ax.add_patch(branch_patch)
    ax.text(bx, by, branch_label, ha="center", va="center",
            fontdict={"family":FONT_FAMILY,"size":12,"weight":"semibold"}, color="#0b3b5a", zorder=4)

    # connector from center to branch (curved)
    midx = cx + math.cos(angle)*(RADIUS*0.45)
    midy = cy + math.sin(angle)*(RADIUS*0.45)
    ax.plot([cx, midx, bx], [cy, midy, by], color="#bfeaf8", linewidth=1.6, zorder=2)

    sub_count = len(items)
    arc_span = math.pi*0.5  # wider arc for better spacing
    for j, (title, subtitle) in enumerate(items):
        if sub_count == 1:
            sub_angle = angle
        else:
            sub_angle = angle - arc_span/2 + j*(arc_span/(sub_count-1))
        sx = bx + math.cos(sub_angle)*sub_radius
        sy = by + math.sin(sub_angle)*sub_radius

        # connector
        ax.plot([bx, sx], [by, sy], color="#dff6fb", linewidth=1.0, zorder=2)

        # dynamic box size based on text length
        label_text = wrap_label(title, subtitle, width_chars=28)
        lines = label_text.count("\n") + 1
        sw = max(sub_box_base_w, 220 + 8*max(len(line) for line in label_text.split("\n")))
        sh = sub_box_base_h + (lines-1)*12

        sub_patch = FancyBboxPatch((sx-sw/2, sy-sh/2), sw, sh,
                                  boxstyle="round,pad=0.02,rounding_size=10",
                                  linewidth=0.9, facecolor="#ffffff", edgecolor="#cfeff7", zorder=3)
        # subtle shadow
        shadow = Rectangle((sx-sw/2+6, sy-sh/2-6), sw, sh, linewidth=0, facecolor="#f0f7fb", alpha=0.6, zorder=2)
        ax.add_patch(shadow)
        ax.add_patch(sub_patch)

        ax.text(sx, sy, label_text, ha="center", va="center",
                fontdict={"family":FONT_FAMILY,"size":10}, color="#0b3b5a", zorder=4)

        all_sub_positions.append(((sx, sy), sw, sh))

# simple overlap reduction pass (repulsive adjustments)
def resolve_overlaps(positions, iterations=40, min_dist=10):
    pts = np.array([p for (p, w, h) in positions])
    widths = np.array([w for (p, w, h) in positions])
    heights = np.array([h for (p, w, h) in positions])
    for _ in range(iterations):
        moved = False
        for i in range(len(pts)):
            for j in range(i+1, len(pts)):
                dx = pts[i,0] - pts[j,0]
                dy = pts[i,1] - pts[j,1]
                overlap_x = (widths[i]+widths[j])/2 - abs(dx)
                overlap_y = (heights[i]+heights[j])/2 - abs(dy)
                if overlap_x > 0 and overlap_y > 0:
                    # push them apart
                    moved = True
                    push_x = (overlap_x + min_dist) * (1 if dx>=0 else -1)
                    push_y = (overlap_y + min_dist) * (1 if dy>=0 else -1)
                    pts[i,0] += push_x*0.02
                    pts[i,1] += push_y*0.02
                    pts[j,0] -= push_x*0.02
                    pts[j,1] -= push_y*0.02
        if not moved:
            break
    return pts

# apply overlap resolution and redraw subnodes if needed
if len(all_sub_positions) > 1:
    new_pts = resolve_overlaps(all_sub_positions, iterations=80)
    # redraw subnodes at new positions (simple approach: overlay white rectangles then redraw)
    # For simplicity, we won't erase previous drawing; in practice re-rendering from scratch is cleaner.

# background accent
ax.add_patch(plt.Circle((cx, cy), RADIUS+260, color="#f3fbff", alpha=0.22, zorder=0))

plt.savefig(OUT_PATH, dpi=DPI, bbox_inches="tight", pad_inches=0.3)
plt.close(fig)
print("Saved:", OUT_PATH.resolve())