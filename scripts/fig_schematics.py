"""Schematic figures (toy data, clearly illustrative) for the talk.

fig_calls_to_motif.png
    Part III algorithmic slide: per-read modification probabilities ->
    threshold -> per-site methylated fraction -> motif.
fig_methyl_haplotyping.png
    Outlook slide: reads x motif-site matrix from a mixed sample; sequence is
    identical, methylation differs; clustering the reads (cf. haplotype phasing,
    e.g. minimum-error-correction / MethPhaser) recovers two lineages.

Run: .venv/bin/python scripts/fig_schematics.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parents[1] / "figures" / "generated"
OUT.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)

C_DARK = "#173047"
C_TEAL = "#156082"
C_ORANGE = "#D9822B"
C_PURPLE = "#A02B93"
C_GREY = "#B8BEC6"
plt.rcParams.update({"font.family": ["Helvetica", "Arial Unicode MS", "DejaVu Sans"], "font.size": 13, "savefig.dpi": 300})
cmap = LinearSegmentedColormap.from_list("m", ["#F4F6F8", "#9CC3DA", C_TEAL, C_DARK])

# ------------------------------------------------------------------ figure A
seq = "TTGATCAAGCGATCTTCCAGGATCAAT"
L = len(seq)
gatc_a = [i + 1 for i in range(L - 3) if seq[i:i + 4] == "GATC"]  # A in GATC
n_reads = 12
prob = rng.beta(1.2, 12, size=(n_reads, L))              # background noise
for j in gatc_a:
    prob[:, j] = np.clip(rng.beta(14, 1.6, size=n_reads), 0, 1)
prob[3, gatc_a[1]] = 0.42                                 # an uncertain call
prob[8, gatc_a[0]] = 0.55
for j in range(L):                                        # mod calls only on A/C
    if seq[j] not in "AC":
        prob[:, j] = np.nan

fig = plt.figure(figsize=(12, 4.6))
gs = fig.add_gridspec(2, 3, width_ratios=[3.2, 3.2, 1.6], height_ratios=[4, 1.1],
                      wspace=0.32, hspace=0.12)

ax1 = fig.add_subplot(gs[0, 0])
im = ax1.imshow(prob, cmap=cmap, vmin=0, vmax=1, aspect="auto")
ax1.set_xticks(range(L))
ax1.set_xticklabels(list(seq), fontsize=8, family="Menlo")
ax1.set_yticks([])
ax1.set_ylabel("reads")
ax1.set_title("1  per-read probability\n    P(base is modified)", loc="left", fontsize=13)
for s in ax1.spines.values():
    s.set_visible(False)
cb = fig.colorbar(im, ax=ax1, fraction=0.03, pad=0.02)
cb.set_ticks([0, 0.7, 1])
cb.ax.tick_params(labelsize=9)

thr = 0.7
calls = np.where(np.isnan(prob), np.nan, (prob >= thr).astype(float))
ax2 = fig.add_subplot(gs[0, 1])
ax2.imshow(calls, cmap=LinearSegmentedColormap.from_list("b", ["#F4F6F8", C_TEAL]),
           vmin=0, vmax=1, aspect="auto")
ax2.set_xticks(range(L))
ax2.set_xticklabels(list(seq), fontsize=8, family="Menlo")
ax2.set_yticks([])
ax2.set_title(f"2  threshold (p ≥ {thr})\n    modified / not modified", loc="left", fontsize=13)
for s in ax2.spines.values():
    s.set_visible(False)

frac = np.nanmean(calls, axis=0)
ax3 = fig.add_subplot(gs[1, 1], sharex=ax2)
cols = [C_ORANGE if j in gatc_a else C_GREY for j in range(L)]
ax3.bar(range(L), np.nan_to_num(frac), color=cols, width=0.8)
ax3.set_ylim(0, 1.05)
ax3.set_yticks([0, 1])
ax3.set_ylabel("fraction", fontsize=10)
ax3.tick_params(labelsize=9)
ax3.set_xticks([])
for s in ("top", "right"):
    ax3.spines[s].set_visible(False)

ax4 = fig.add_subplot(gs[:, 2])
ax4.axis("off")
ax4.set_title("3  motif\n    enrichment", loc="left", fontsize=13)
ax4.text(0.05, 0.62, "G", fontsize=34, family="Menlo", color="#666", transform=ax4.transAxes)
ax4.text(0.27, 0.62, "A", fontsize=34, family="Menlo", color=C_ORANGE, weight="bold",
         transform=ax4.transAxes)
ax4.text(0.49, 0.62, "T", fontsize=34, family="Menlo", color="#666", transform=ax4.transAxes)
ax4.text(0.71, 0.62, "C", fontsize=34, family="Menlo", color="#666", transform=ax4.transAxes)
ax4.text(0.05, 0.47, "6mA on the A of GATC", fontsize=12, transform=ax4.transAxes)
ax4.text(0.05, 0.30, "nearly all GATC sites\nmethylated:\nDam-like MTase", fontsize=11,
         color="#444", transform=ax4.transAxes, va="top")
fig.savefig(OUT / "fig_calls_to_motif.png", bbox_inches="tight", facecolor="white")
plt.close(fig)

# ------------------------------------------------------------------ figure B
n_sites = 16
n_a, n_b = 14, 10
pattern_a = (rng.random(n_sites) < 0.5).astype(float)
pattern_b = pattern_a.copy()
flip = rng.choice(n_sites, 7, replace=False)
pattern_b[flip] = 1 - pattern_b[flip]


def reads(pattern, n):
    m = np.tile(pattern, (n, 1))
    noise = rng.random(m.shape) < 0.08                    # call errors
    m[noise] = 1 - m[noise]
    miss = rng.random(m.shape) < 0.15                     # read does not cover site
    m[miss] = np.nan
    return m


ra, rb = reads(pattern_a, n_a), reads(pattern_b, n_b)
mixed = np.vstack([ra, rb])
order = rng.permutation(len(mixed))
shuffled = mixed[order]
lab = np.array([0] * n_a + [1] * n_b)[order]

cm2 = LinearSegmentedColormap.from_list("b", ["#EEF1F4", C_DARK])
fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), gridspec_kw={"wspace": 0.35})
for ax, mat, title in [(axes[0], shuffled, "mixed sample: reads as they come"),
                       (axes[1], np.vstack([ra, rb]), "clustered by methylation pattern")]:
    show = np.where(np.isnan(mat), 0.5, mat)
    ax.imshow(show, cmap=LinearSegmentedColormap.from_list(
        "t", ["#EEF1F4", "#FFFFFF", C_DARK]), vmin=0, vmax=1, aspect="auto")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("motif sites along the genome (same sequence)")
    ax.set_ylabel("reads")
    ax.set_title(title, loc="left", fontsize=13)
    for s in ax.spines.values():
        s.set_visible(False)
axes[1].axhline(n_a - 0.5, color=C_ORANGE, lw=2.5)
axes[1].text(n_sites - 0.3, n_a / 2, "lineage A", color=C_ORANGE, va="center",
             fontsize=12, weight="bold")
axes[1].text(n_sites - 0.3, n_a + n_b / 2, "lineage B", color=C_PURPLE, va="center",
             fontsize=12, weight="bold")
axes[1].add_patch(Rectangle((-0.5, n_a - 0.5), n_sites, n_b, fill=False,
                            ec=C_PURPLE, lw=2.5))
axes[1].add_patch(Rectangle((-0.5, -0.5), n_sites, n_a, fill=False, ec=C_ORANGE, lw=2.5))
fig.text(0.5, 0.5, "→", fontsize=38, ha="center", va="center", color="#555")
fig.text(0.13, 0.01, "dark: methylated    light grey: unmethylated    white: not covered    (illustration)",
         fontsize=10, color="#555")
fig.savefig(OUT / "fig_methyl_haplotyping.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("written to", OUT)
