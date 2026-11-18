"""Extract all embedded pictures from source decks, named by slide number.

Output: figures/candidates/<deck-short>/sNN_<idx>_<w>x<h>.<ext>
Run:    .venv/bin/python scripts/extract_media.py
"""
from pathlib import Path

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

ROOT = Path(__file__).resolve().parents[1]
DECKS = {
    "main": ROOT / "2026-FU-Habil-Hoelzer-Talk.pptx",
    "val_kitasato": ROOT / "sources/slides/2026-11-16-Valentina-Kitasato-genomic-style.pptx",
    "val_phd": ROOT / "sources/slides/2026-11-17-Valentina-Internial-Seminar-PhD-overview-talk.pptx",
    "val_wildau": ROOT / "sources/slides/2024-11-20-Valentina-methylation-talk_wildau.pptx",
    "lehrprobe": ROOT / "sources/slides/2024-12-04-Lehrprobe-Bioinformatics-Nanopore-I-Hoelzer-final.pptx",
}


def pictures(shapes):
    for sh in shapes:
        if sh.shape_type == MSO_SHAPE_TYPE.GROUP:
            yield from pictures(sh.shapes)
        elif sh.shape_type == MSO_SHAPE_TYPE.PICTURE:
            yield sh


for short, path in DECKS.items():
    out = ROOT / "figures/candidates" / short
    out.mkdir(parents=True, exist_ok=True)
    prs = Presentation(path)
    n = 0
    for i, slide in enumerate(prs.slides, 1):
        for j, pic in enumerate(pictures(slide.shapes)):
            try:
                img = pic.image
                w, h = img.size
                ext = img.content_type.split("/")[-1].replace("jpeg", "jpg")
            except Exception:
                continue
            if w * h < 150 * 150:  # skip icons/logos
                continue
            (out / f"s{i:02d}_{j}_{w}x{h}.{ext}").write_bytes(img.blob)
            n += 1
    print(f"{short}: {n} images")
