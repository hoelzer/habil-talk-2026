"""Speech-recognition analogy (idea: M. Hölzer) — opening figure and a small callback icon.

fig_analogy_opening.png
    Row 1: noisy voice recording -> speech recognition -> transcript with one misheard word;
           the speaker's voice is in the recording, not in the transcript.
    Row 2: nanopore signal -> basecaller -> sequence with one wrong base;
           the methylation is in the signal, not in the sequence.
fig_analogy_icon.png
    Small waveform -> text icon, used on the callback slides.

Run: .venv/bin/python scripts/fig_analogy.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parents[1] / "figures" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(3)

C_DARK = "#173047"
C_TEAL = "#156082"
C_RED = "#C0392B"
C_ORANGE = "#D9822B"
C_GREY = "#8A929B"
plt.rcParams.update({"font.family": ["Helvetica", "Arial Unicode MS", "DejaVu Sans"],
                     "font.size": 13, "savefig.dpi": 300})


def speech_wave(n=1400):
    t = np.linspace(0, 1, n)
    env = np.zeros(n)
    for c, w, a in [(0.1, 0.05, 0.8), (0.24, 0.06, 1.0), (0.4, 0.05, 0.6), (0.55, 0.07, 0.95),
                    (0.72, 0.05, 0.7), (0.88, 0.06, 0.85)]:
        env += a * np.exp(-((t - c) / w) ** 2)
    carrier = np.sin(2 * np.pi * 90 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 7 * t))
    return t, env * carrier + 0.08 * rng.normal(size=n)


def squiggle(n=26):
    levels = rng.uniform(60, 120, n)
    levels[15] += 18                                     # modified base: the current shifts
    x, y = [], []
    for i, lv in enumerate(levels):
        k = rng.integers(25, 45)
        x.extend(np.linspace(i, i + 1, k, endpoint=False))
        y.extend(lv + rng.normal(0, 4, k))
    return np.array(x) / n, np.array(y), (15 / n, 16 / n)


def box(ax, xy, w, h, text, fc="#EEF3F7", ec=C_TEAL):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle="round,pad=0.01,rounding_size=0.02",
                                fc=fc, ec=ec, lw=1.6, transform=ax.transAxes))
    ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha="center", va="center", fontsize=17,
            color=C_DARK, transform=ax.transAxes)


def arrow(ax, x0, x1, y):
    ax.add_patch(FancyArrowPatch((x0, y), (x1, y), arrowstyle="-|>", mutation_scale=18,
                                 color="#555", lw=1.8, transform=ax.transAxes))


def speaker(fig, x, y, size=0.12, color=C_ORANGE):
    """Head-and-shoulders silhouette in its own square axes (figure coordinates)."""
    w = size * fig.get_figheight() / fig.get_figwidth()
    sa = fig.add_axes([x - w / 2, y - size / 2, w, size])
    sa.set_xlim(-1, 1)
    sa.set_ylim(-1, 1)
    sa.set_aspect("equal")
    sa.axis("off")
    sa.add_patch(Ellipse((0, -0.75), 1.7, 1.2, color=color))
    sa.add_patch(Circle((0, 0.35), 0.45, color=color))


fig = plt.figure(figsize=(12, 5.2))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")

# ---------------- row 1: speech
Y1 = 0.70
ax.text(0.01, Y1 + 0.2, "Voice recording", fontsize=20, weight="bold", color=C_DARK,
        transform=ax.transAxes)
w_ax = fig.add_axes([0.01, Y1 - 0.13, 0.25, 0.26])
t, w = speech_wave()
w_ax.plot(t, w, color=C_DARK, lw=0.6)
w_ax.axis("off")
arrow(ax, 0.275, 0.325, Y1)
box(ax, (0.33, Y1 - 0.08), 0.17, 0.16, "speech\nrecognition (AI)")
arrow(ax, 0.505, 0.555, Y1)
words = [("the outbreak strain was", C_DARK), ("found in the ", C_DARK)]
ax.text(0.565, Y1 + 0.045, words[0][0], fontsize=21, color=C_DARK, transform=ax.transAxes,
        family="Georgia", va="center")
ax.text(0.565, Y1 - 0.045, "found in the", fontsize=21, color=C_DARK, transform=ax.transAxes,
        family="Georgia", va="center")
ax.text(0.700, Y1 - 0.045, "chicken", fontsize=21, color=C_RED, transform=ax.transAxes,
        family="Georgia", va="center", weight="bold")
ax.text(0.700, Y1 - 0.14, "(kitchen?)", fontsize=16, color=C_RED, transform=ax.transAxes,
        va="center")
speaker(fig, 0.90, Y1 + 0.01)
ax.text(0.90, Y1 - 0.13, "who is speaking?", fontsize=16, color=C_ORANGE, ha="center",
        transform=ax.transAxes, va="center")
ax.add_patch(FancyArrowPatch((0.2, Y1 + 0.135), (0.86, Y1 + 0.10), connectionstyle="arc3,rad=-0.12",
                             arrowstyle="-|>", mutation_scale=14, color=C_ORANGE, lw=1.4,
                             ls="--", transform=ax.transAxes))
ax.text(0.53, Y1 + 0.235, "only in the recording, not in the text", fontsize=14,
        color=C_ORANGE, ha="center", transform=ax.transAxes)

ax.plot([0.01, 0.99], [0.45, 0.45], color="#D5DAE0", lw=1, transform=ax.transAxes)

# ---------------- row 2: nanopore
Y2 = 0.22
ax.text(0.01, Y2 + 0.18, "Nanopore signal", fontsize=20, weight="bold", color=C_DARK,
        transform=ax.transAxes)
s_ax = fig.add_axes([0.01, Y2 - 0.12, 0.25, 0.24])
x, y, (m0, m1) = squiggle()
s_ax.plot(x, y, color=C_DARK, lw=0.7)
s_ax.axvspan(m0, m1, color=C_ORANGE, alpha=0.25, lw=0)
s_ax.axis("off")
arrow(ax, 0.275, 0.325, Y2)
box(ax, (0.33, Y2 - 0.08), 0.17, 0.16, "basecaller (AI)")
arrow(ax, 0.505, 0.555, Y2)
seq, WRONG, DX = "GATCAAGCGATC", 7, 0.022
x0 = 0.565
for i, ch in enumerate(seq):
    col = C_RED if i == WRONG else C_DARK
    ax.text(x0 + i * DX, Y2, ch, fontsize=21, family="Menlo", color=col, va="center",
            weight="bold" if i == WRONG else "normal", transform=ax.transAxes)
ax.text(x0 + WRONG * DX + 0.007, Y2 - 0.10, "wrong base", fontsize=16, color=C_RED,
        ha="center", transform=ax.transAxes, va="center")
ax.text(0.90, Y2 + 0.01, "CH₃", fontsize=26, color=C_ORANGE, ha="center", va="center",
        weight="bold", transform=ax.transAxes)
ax.text(0.90, Y2 - 0.09, "which base is\nmethylated?", fontsize=16, color=C_ORANGE, ha="center",
        transform=ax.transAxes, va="center")
ax.add_patch(FancyArrowPatch((0.17, Y2 + 0.13), (0.87, Y2 + 0.07), connectionstyle="arc3,rad=-0.12",
                             arrowstyle="-|>", mutation_scale=14, color=C_ORANGE, lw=1.4,
                             ls="--", transform=ax.transAxes))
fig.savefig(OUT / "fig_analogy_opening.png", facecolor="white", bbox_inches="tight")
plt.close(fig)

# ---------------- icon: waveform -> text
fig = plt.figure(figsize=(1.6, 0.5))
ax = fig.add_axes([0, 0, 1, 1])
ax.axis("off")
ax.set_xlim(0, 1.6)
ax.set_ylim(0, 0.5)
t, w = speech_wave(600)
ax.plot(0.05 + 0.6 * t, 0.25 + 0.17 * w / np.abs(w).max(), color=C_TEAL, lw=0.8)
ax.add_patch(FancyArrowPatch((0.72, 0.25), (0.95, 0.25), arrowstyle="-|>", mutation_scale=10,
                             color="#555", lw=1.4))
for k, (yy, ln) in enumerate([(0.36, 0.5), (0.25, 0.55), (0.14, 0.38)]):
    ax.plot([1.02, 1.02 + ln], [yy, yy], color=C_DARK, lw=3, solid_capstyle="round")
fig.savefig(OUT / "fig_analogy_icon.png", facecolor="white", transparent=False)
plt.close(fig)
print("written to", OUT)
