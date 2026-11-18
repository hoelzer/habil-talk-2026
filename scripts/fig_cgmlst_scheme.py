"""Simple cgMLST explainer for slide 3 (half-slide, portrait-ish).

Three steps:
  1  core genome: the same ~2,500 genes in every isolate of the species
  2  each gene sequence gets an allele number (new variant = new number)
  3  allele profiles are compared: number of differing genes = allele distance
     -> tree of minimal distances (minimum spanning tree)

Outputs: figures/generated/fig_cgmlst_scheme.{png,svg,pdf}
Run: .venv/bin/python scripts/fig_cgmlst_scheme.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Rectangle, Wedge

OUT = Path(__file__).resolve().parents[1] / "figures" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

DARK = "#173047"
BLUE = "#3E6E9B"
LIGHT = "#DCE6F0"
GREY = "#8A8F98"
RED = "#C0392B"
REDBG = "#F6DAD6"
plt.rcParams.update({"font.family": ["Helvetica", "Arial Unicode MS", "DejaVu Sans"],
                     "font.size": 12, "savefig.dpi": 300})

fig = plt.figure(figsize=(5.0, 4.6))
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100)
ax.set_ylim(0, 92)
ax.axis("off")


def step(n, y, text):
    ax.add_patch(Circle((3.2, y), 2.3, color=DARK))
    ax.text(3.2, y, str(n), color="white", ha="center", va="center", fontsize=11,
            weight="bold")
    ax.text(7.5, y, text, ha="left", va="center", fontsize=12.5, color=DARK, weight="bold")


# ---------------------------------------------------------------- step 1
step(1, 88, "Core genome: the same ~2,500 genes in every isolate")
cx, cy, r = 14, 74, 8.5
ax.add_patch(Circle((cx, cy), r, fill=False, lw=2.2, color=GREY))
rng = np.random.default_rng(3)
angles = np.sort(rng.uniform(0, 360, 26))
for k, a in enumerate(angles):
    col = BLUE if k in (2, 9, 17) else "#9DB4CC"
    ax.add_patch(Wedge((cx, cy), r + 1.6, a, a + 6, width=3.2, color=col, lw=0))
ax.text(cx, cy, "genome", ha="center", va="center", fontsize=9, color=GREY)
# gene labels to the right
ax.text(28, 79, "gene 1, gene 2, … gene 2,513", fontsize=11, color=DARK, va="center")
ax.text(28, 73.5, "(scheme for E. coli / EHEC)", fontsize=10, color=GREY, va="center",
        style="italic")

# ---------------------------------------------------------------- step 2
step(2, 60, "Each gene variant gets a number (allele)")
seqs = [("ATGCTAGCTTACG", None, "allele 1"),
        ("ATGCTGGCTTACG", 5, "allele 2")]
for i, (s, diff, lab) in enumerate(seqs):
    y = 52 - i * 6.5
    ax.text(7.5, y, "gene 2", fontsize=10, color=GREY, va="center")
    for j, ch in enumerate(s):
        x = 20 + j * 3.3
        if diff == j:
            ax.add_patch(Rectangle((x - 1.5, y - 2.4), 3.0, 4.8, color=REDBG, lw=0))
        ax.text(x, y, ch, family="Menlo", fontsize=11, ha="center", va="center",
                color=RED if diff == j else DARK, weight="bold" if diff == j else None)
    ax.annotate("", xy=(68, y), xytext=(63.5, y),
                arrowprops=dict(arrowstyle="->", color=GREY, lw=1.4))
    ax.add_patch(FancyBboxPatch((70, y - 2.4), 15, 4.8, boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc=REDBG if diff else LIGHT, ec="none"))
    ax.text(77.5, y, lab, fontsize=10.5, ha="center", va="center",
            color=RED if diff else DARK, weight="bold")
ax.text(77.5, 41.2, "1 different base = new allele", fontsize=9.5, color=RED, ha="center", va="center")

# ---------------------------------------------------------------- step 3
step(3, 35, "Compare profiles: count genes with different alleles")
cols = ["gene 1", "gene 2", "gene 3", "…", "gene 2,513"]
rows = [("isolate A", [3, 1, 7, "…", 4]),
        ("isolate B", [3, 2, 7, "…", 4]),
        ("isolate C", [3, 2, 9, "…", 5])]
x0, dx, y0, dy = 23, 10.5, 28.5, 5.6
for j, c in enumerate(cols):
    ax.text(x0 + j * dx, y0, c, fontsize=9, ha="center", va="center", color=GREY)
for i, (name, vals) in enumerate(rows):
    y = y0 - (i + 1) * dy
    ax.text(7.5, y, name, fontsize=10.5, va="center", color=DARK)
    for j, v in enumerate(vals):
        differs = v != rows[0][1][j] and v != "…"
        if differs:
            ax.add_patch(Rectangle((x0 + j * dx - 3.6, y - 2.3), 7.2, 4.6, color=REDBG, lw=0))
        ax.text(x0 + j * dx, y, str(v), fontsize=11, ha="center", va="center",
                color=RED if differs else DARK, weight="bold" if differs else None)

# mini minimum spanning tree
nodes = {"A": (80, 24), "B": (88, 14), "C": (96, 4.5)}
for (a, b, d) in [("A", "B", 1), ("B", "C", 2)]:
    (xa, ya), (xb, yb) = nodes[a], nodes[b]
    ax.plot([xa, xb], [ya, yb], color=GREY, lw=1.8, zorder=1)
    ax.text((xa + xb) / 2 - 2.6, (ya + yb) / 2 - 1.6, str(d), fontsize=11, color=RED,
            weight="bold", ha="center", va="center")
for n, (x, y) in nodes.items():
    ax.add_patch(Circle((x, y), 2.6, color=BLUE, zorder=2))
    ax.text(x, y, n, color="white", ha="center", va="center", fontsize=10, weight="bold",
            zorder=3)
ax.text(66, 4, "allele distances\n→ tree", fontsize=9.5, color=GREY, ha="center",
        va="center")

for ext in ("png", "svg", "pdf"):
    fig.savefig(OUT / f"fig_cgmlst_scheme.{ext}", facecolor="white")
print("written", OUT / "fig_cgmlst_scheme.png")
