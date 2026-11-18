"""Crop figure regions out of high-res slide renders / page renders.

Inputs come from scripts/render_pptx.sh (build/renders/...) and
scripts/extract_paper_figs.sh (figures/candidates/papers/...).
Boxes are fractions (x0, y0, x1, y1) of the source image.

Run: .venv/bin/python scripts/crops.py
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures/crops"
OUT.mkdir(parents=True, exist_ok=True)
R = ROOT / "build/renders"
PP = ROOT / "figures/candidates/papers"

CROPS = {
    # Valentina, Koch-Kitasato symposium 2026
    "kit_methyl_same_dna": (R / "val_kitasato/s-05.png", (0.03, 0.17, 0.97, 0.80)),
    "kit_tsne_circled": (R / "val_kitasato/s-10.png", (0.03, 0.13, 0.97, 0.91)),
    "kit_unseen_species": (R / "val_kitasato/s-12.png", (0.03, 0.12, 0.97, 0.91)),
    "kit_metagenomic_pipeline": (R / "val_kitasato/s-17.png", (0.03, 0.14, 0.97, 0.90)),
    "kit_rm_defense": (R / "val_kitasato/s-16.png", (0.03, 0.12, 0.97, 0.92)),
    # Valentina, PhD overview 2026
    "phd_motifs": (R / "val_phd/s-05.png", (0.0, 0.55, 0.50, 0.93)),
    "phd_own_vs_foreign": (R / "val_phd/s-05.png", (0.48, 0.30, 0.99, 0.93)),
    "phd_methyl_table": (R / "val_phd/s-10.png", (0.03, 0.13, 0.99, 0.92)),
    "phd_ehec_outbreak": (R / "val_phd/s-12.png", (0.0, 0.12, 1.0, 0.92)),
    "phd_mabs_plot": (R / "val_phd/s-14.png", (0.40, 0.12, 0.86, 0.93)),
    "phd_pt_vs_methyl": (R / "val_phd/s-15.png", (0.10, 0.12, 0.95, 0.60)),
    "phd_workflow": (R / "val_phd/s-09.png", (0.0, 0.12, 1.0, 0.80)),
    "phd_nfcore_metro": (R / "val_phd/s-27.png", (0.0, 0.12, 0.52, 0.93)),
    "phd_scidata_squidbase": (R / "val_phd/s-11.png", (0.50, 0.10, 1.0, 0.93)),
    # Martin, teaching lecture 2024 (Lehrprobe)
    "lp_debruijn": (R / "lehrprobe/s-24.png", (0.05, 0.15, 0.62, 0.74)),
    "lp_short_long_assembly": (R / "lehrprobe/s-23.png", (0.0, 0.10, 1.0, 0.98)),
    # Original main deck (Martin's appendix slides)
    "orig_raw_native_pcr": (R / "original/s-50.png", (0.0, 0.10, 1.0, 0.98)),
    "orig_mpoa_igv": (R / "original/s-48.png", (0.0, 0.08, 1.0, 0.98)),
}

for name, (src, (x0, y0, x1, y1)) in CROPS.items():
    if not src.exists():
        print("MISSING", src)
        continue
    im = Image.open(src)
    w, h = im.size
    im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(OUT / f"{name}.png")
    print("ok", name)

# ---- vector figures in PDFs: render page at 300 dpi, then crop
import subprocess  # noqa: E402

PDF_CROPS = {
    # Biggel ... Urban 2026 bioRxiv (alpaqa), Fig 1, page 6, CC-BY 4.0
    "alpaqa_fig1": (ROOT / "sources/papers/others/2026.03.20.713089v2.full.pdf", 6,
                    (0.15, 0.37, 0.88, 0.61)),
}
for name, (pdf, page, (x0, y0, x1, y1)) in PDF_CROPS.items():
    tmp = OUT / f"_{name}_page"
    subprocess.run(["pdftoppm", "-r", "300", "-png", "-singlefile", "-f", str(page),
                    "-l", str(page), str(pdf), str(tmp)], check=True)
    im = Image.open(f"{tmp}.png")
    w, h = im.size
    im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(OUT / f"{name}.png")
    Path(f"{tmp}.png").unlink()
    print("ok", name)
