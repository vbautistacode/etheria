# Gere mindmap PNG (1920x1080) — salve como mindmap.png no diretório atual
# Requisitos: pip install matplotlib networkx pillow numpy

import math
import textwrap
from pathlib import Path
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
from PIL import Image

# --- Config
OUT_PATH = Path("mindmap.png")
W, H = 1920, 1080
DPI = 100
FONT = {"family":"DejaVu Sans", "size":12}
NODE_WIDTH = 300
NODE_HEIGHT = 70
RADIUS = 360

# --- Estrutura (use exatamente os rótulos fornecidos)
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

# --- Helpers
def wrap_label(title, subtitle="", width_chars=28):
    if subtitle:
        parts = subtitle.split(";")
        subtitle_wrapped = "\n".join([textwrap.fill(p.strip(), width_chars) for p in parts])
        return f"{title}\n{subtitle_wrapped}"
    else:
        return textwrap.fill(title, width_chars)

# --- Layout: radial placement of branch groups
fig = plt.figure(figsize=(W/DPI, H/DPI), dpi=DPI)
ax = fig.add_axes([0,0,1,1])
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")

cx, cy = W/2, H/2

# draw center node
center_box_w, center_box_h = 420, 110
center_patch = FancyBboxPatch((cx-center_box_w/2, cy-center_box_h/2),
                             center_box_w, center_box_h,
                             boxstyle="round,pad=0.02,rounding_size=14",
                             linewidth=1.2, facecolor="#f7fbff", edgecolor="#2b8cbe", zorder=3)
ax.add_patch(center_patch)
ax.text(cx, cy, center, ha="center", va="center", fontdict={"family":"DejaVu Sans","size":18,"weight":"bold"}, color="#0b3b5a", zorder=4)

# compute angles for main branches
n_branches = len(branches)
angle_step = 2*math.pi / n_branches
start_angle = -math.pi/2  # top

branch_positions = []
for i, (bname, items) in enumerate(branches.items()):
    angle = start_angle + i*angle_step
    bx = cx + math.cos(angle)*RADIUS
    by = cy + math.sin(angle)*RADIUS
    branch_positions.append((bname, bx, by, angle))

    # draw branch label node
    label = wrap_label(bname, "", width_chars=22)
    bw, bh = 260, 60
    patch = FancyBboxPatch((bx-bw/2, by-bh/2), bw, bh,
                          boxstyle="round,pad=0.02,rounding_size=10",
                          linewidth=1.0, facecolor="#e8f6f8", edgecolor="#2b8be0", zorder=3)
    ax.add_patch(patch)
    ax.text(bx, by, label, ha="center", va="center", fontdict={"family":"DejaVu Sans","size":12,"weight":"semibold"}, color="#0b3b5a", zorder=4)

    # draw edge from center to branch
    ax.plot([cx + (center_box_w/2)*math.cos(angle), bx - bw/2*math.cos(angle)],
            [cy + (center_box_h/2)*math.sin(angle), by - bh/2*math.sin(angle)],
            color="#9ecae1", linewidth=1.2, zorder=2)

    # place subnodes around branch label
    sub_count = len(items)
    sub_radius = 160
    # spread subnodes in a small arc centered on branch angle
    arc_span = math.pi/3  # 60 degrees
    for j, (title, subtitle) in enumerate(items):
        if sub_count == 1:
            sub_angle = angle
        else:
            sub_angle = angle - arc_span/2 + j*(arc_span/(sub_count-1))
        sx = bx + math.cos(sub_angle)*sub_radius
        sy = by + math.sin(sub_angle)*sub_radius

        # draw connector
        ax.plot([bx, sx], [by, sy], color="#cfeef8", linewidth=1.0, zorder=2)

        # draw subnode box
        sw, sh = 300, 70
        sub_patch = FancyBboxPatch((sx-sw/2, sy-sh/2), sw, sh,
                                  boxstyle="round,pad=0.02,rounding_size=10",
                                  linewidth=0.9, facecolor="#ffffff", edgecolor="#b3d7e8", zorder=3)
        ax.add_patch(sub_patch)

        label_text = wrap_label(title, subtitle, width_chars=28)
        ax.text(sx, sy, label_text, ha="center", va="center", fontdict={"family":"DejaVu Sans","size":10}, color="#0b3b5a", zorder=4)

# subtle background accents
ax.add_patch(plt.Circle((cx, cy), RADIUS+220, color="#f0fbff", alpha=0.25, zorder=0))

# save figure
plt.savefig(OUT_PATH, dpi=DPI, bbox_inches="tight", pad_inches=0.2)
plt.close(fig)

# confirm file
print("Saved:", OUT_PATH.resolve())