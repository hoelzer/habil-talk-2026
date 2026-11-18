"""Zoom-ins for dense paper figures: crop the panel that carries the message.

Inputs are figures extracted from papers (private, see extract_paper_figs.sh and
crops.py); outputs go to figures/crops/zoom_*.png (git-ignored).
Pixel boxes refer to the extracted images; check them if a source image is replaced.

Run: .venv/bin/python scripts/zooms.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "figures/candidates/papers"
C = ROOT / "figures/crops"
R = ROOT / "figures/received"
OUT = C


def crop(src, box):
    return Image.open(src).convert("RGB").crop(box)


def side_by_side(a, b, gap=20, valign="top"):
    h = max(a.height, b.height)
    im = Image.new("RGB", (a.width + gap + b.width, h), "white")
    im.paste(a, (0, 0 if valign == "top" else (h - a.height) // 2))
    im.paste(b, (a.width + gap, 0 if valign == "top" else (h - b.height) // 2))
    return im


def stacked(a, b, gap=20, halign="right"):
    w = max(a.width, b.width)
    im = Image.new("RGB", (w, a.height + gap + b.height), "white")
    im.paste(a, (0, 0))
    im.paste(b, (w - b.width if halign == "right" else 0, a.height + gap))
    return im


def save(im, name):
    im.save(OUT / f"{name}.png", optimize=True)
    print(f"{name}: {im.size}")


# s12 — JCM 2024 Fig. 3: K. pneumoniae panel (with lab legend) only
save(crop(P / "p3_multicenter_jcm2024/img-007.png", (576, 0, 1184, 318)), "zoom_jcm_kp")

# s14 — BMC Genomics 2025 polishing bar plot: bottom two rows (with x labels + legend)
save(crop(P / "p4_assembly_bmc2025/img-005.png", (42, 405, 1946, 977)), "zoom_polish_rows34")

# s16 — alpaqa Fig. 1: Salmonella enterica panel + legend
sal = crop(C / "alpaqa_fig1.png", (0, 372, 432, 772))
leg = crop(C / "alpaqa_fig1.png", (1535, 20, 1862, 175))
save(side_by_side(sal, leg), "zoom_alpaqa_salmonella")

# s16 — alpaqa Fig. 2A: consensus quality dip at the modified motif
save(crop(P / "o_alpaqa_biorxiv2026/img-002.png", (0, 0, 1500, 190)), "zoom_alpaqa_qdip")

# s16 — Suppl. Fig. S3: the ten species with the highest dnd/dpd prevalence + legend
top = crop(R / "urban-supp3-dnd.png", (0, 0, 905, 455))
leg = crop(R / "urban-supp3-dnd.png", (1430, 1120, 1770, 1248))
save(stacked(top, leg), "zoom_urban_top10")
