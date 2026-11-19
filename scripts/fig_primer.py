"""Primer figure for a general audience: genome -> reads -> assembly (coverage, consensus) -> compare.

fig_primer.png / .svg
    Four panels with the basic terms of the talk (toy illustration):
    1 Genome   all DNA of a bacterium, ~5 million letters (A, C, G, T)
    2 Reads    DNA pieces read letter by letter; nanopore: long, some errors
    3 Assembly overlapping reads -> genome; coverage; consensus = majority vote
    4 Compare  isolates of one species differ at a few positions -> same outbreak?

Run: .venv/bin/python scripts/fig_primer.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyArrowPatch, FancyBboxPatch, Rectangle

OUT = Path(__file__).resolve().parents[1] / "figures" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11)

C_DARK = "#173047"
C_TEAL = "#156082"
C_LIGHT = "#E3EEF4"
C_READ = "#7FA7C0"
C_RED = "#C0392B"
C_ORANGE = "#D9822B"
C_GREY = "#5B636B"
plt.rcParams.update({"font.family": ["Helvetica", "Arial Unicode MS", "DejaVu Sans"],
                     "font.size": 15, "savefig.dpi": 300})

fig, ax = plt.subplots(figsize=(14, 5.2))
ax.set_xlim(0, 14)
ax.set_ylim(0, 5.2)
ax.set_aspect("equal")
ax.axis("off")

TITLE_Y, SUB_Y = 4.85, 1.25
XS = [0.2, 3.75, 7.3, 10.85]          # left edges of the four panels (width ~3)


def title(x, n, text):
    ax.text(x, TITLE_Y, f"{n}  ", fontsize=19, color=C_TEAL, weight="bold", va="center")
    ax.text(x + 0.38, TITLE_Y, text, fontsize=19, color=C_DARK, weight="bold", va="center")


def sub(x, lines):
    ax.text(x, SUB_Y, "\n".join(lines), fontsize=13, color=C_GREY, va="top", linespacing=1.35)


def arrow(x0, x1, y=3.0, label=""):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=22,
                                 color="#555", lw=2))
    if label:
        ax.text((x0 + x1) / 2, y - 0.3, label, fontsize=10, color="#555", ha="center", va="top")


# ---------------- 1 genome
x = XS[0]
title(x, 1, "Genome")
ax.add_patch(FancyBboxPatch((x + 0.15, 2.35), 2.45, 1.55, boxstyle="round,pad=0.02,rounding_size=0.7",
                            fc=C_LIGHT, ec=C_TEAL, lw=2))
ax.add_patch(Circle((x + 1.2, 3.12), 0.5, fill=False, ec=C_DARK, lw=2.5))
ax.add_patch(Circle((x + 2.05, 3.35), 0.16, fill=False, ec=C_DARK, lw=2))
ax.text(x + 1.2, 3.12, "DNA", fontsize=11, color=C_DARK, ha="center", va="center")
ax.text(x + 0.15, 1.85, "…ATGCTTGACGGA…", fontsize=15, family="Menlo", color=C_DARK, va="center")
sub(x, ["all DNA of a bacterium:", "≈ 5 million letters", "(A, C, G, T)"])

arrow(2.95, 3.65, label="sequencing")

# ---------------- 2 reads
x = XS[1]
title(x, 2, "Reads")
for k in range(7):
    y = 2.0 + k * 0.3
    x0 = x + 0.1 + rng.uniform(0, 0.7)
    ln = rng.uniform(1.3, 1.9)
    ax.add_patch(Rectangle((x0, y), ln, 0.14, color=C_READ, lw=0))
    if k in (1, 4, 6):
        xe = x0 + rng.uniform(0.3, ln - 0.3)
        ax.add_patch(Rectangle((xe, y - 0.02), 0.07, 0.18, color=C_RED, lw=0))
sub(x, ["DNA pieces, read", "letter by letter;", "nanopore: long, some errors"])

arrow(6.55, 7.2, label="assembly")

# ---------------- 3 assembly
x = XS[2]
title(x, 3, "Assembly")
col = x + 1.55
starts = [0.05, 0.35, 0.7, 0.2, 1.0, 0.55, 1.3]
for k, s0 in enumerate(starts):
    y = 2.6 + k * 0.22
    ln = 1.6 if k % 2 else 1.4
    ax.add_patch(Rectangle((x + s0, y), ln, 0.12, color=C_READ, lw=0))
ax.add_patch(Rectangle((col - 0.04, 2.5), 0.08, 1.7, fill=False, ec=C_ORANGE, lw=1.8, ls="--"))
ax.add_patch(Rectangle((x + 0.05, 2.15), 2.85, 0.2, color=C_DARK, lw=0))
ax.text(x + 0.05, 2.0, "genome", fontsize=12, color=C_DARK, va="top")
ax.text(col + 0.12, 4.32, "coverage: 6×", fontsize=12, color=C_ORANGE, va="bottom")
sub(x, ["overlapping reads → genome;", "coverage: reads per letter;", "consensus: majority vote"])

arrow(10.3, 10.8, label="compare")

# ---------------- 4 compare
x = XS[3]
title(x, 4, "Compare")
seqA, seqB = "ACGTTGCAGT", "ACGTCGCAGT"
for row, (lab, sq) in enumerate([("isolate A", seqA), ("isolate B", seqB)]):
    y = 3.55 - row * 0.75
    ax.text(x + 0.05, y + 0.32, lab, fontsize=12, color=C_GREY, va="center")
    for i, ch in enumerate(sq):
        diff = seqA[i] != seqB[i]
        if diff:
            ax.add_patch(Rectangle((x + 0.05 + i * 0.27 - 0.03, y - 0.17), 0.26, 0.34,
                                   color=C_ORANGE, alpha=0.3, lw=0))
        ax.text(x + 0.05 + i * 0.27, y, ch, fontsize=16, family="Menlo",
                color=C_RED if diff else C_DARK, va="center",
                weight="bold" if diff else "normal")
sub(x, ["isolates of one species", "differ at a few letters:", "same outbreak?"])

fig.savefig(OUT / "fig_primer.png", facecolor="white", bbox_inches="tight")
fig.savefig(OUT / "fig_primer.svg", facecolor="white", bbox_inches="tight")
plt.close(fig)
print("written to", OUT)
