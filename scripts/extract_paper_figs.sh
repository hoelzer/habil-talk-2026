#!/usr/bin/env bash
# Extract raster figures (>=500x300 px) and render pages from paper PDFs (bash 3.2 compatible).
# Output: figures/candidates/papers/<short>/  (raster: img-*.png, pages: page-NN.png)
# Run from repo root:  bash scripts/extract_paper_figs.sh
set -eu
cd "$(dirname "$0")/.."
P=sources/papers
O=figures/candidates/papers
while IFS='|' read -r k f; do
  [ -z "$k" ] && continue
  mkdir -p "$O/$k"
  pdfimages -png "$f" "$O/$k/img" || true
  for i in "$O/$k"/img-*.png; do
    [ -e "$i" ] || continue
    set -- $(magick identify -format '%w %h' "$i")
    if [ "$1" -lt 500 ] || [ "$2" -lt 300 ]; then rm "$i"; fi
  done
  pdftoppm -r 150 -png "$f" "$O/$k/page"
done <<LIST
p3_multicenter_jcm2024|$P/mine/dabernig-heinz-et-al-2024-a-multicenter-study-on-accuracy-and-reproducibility-of-nanopore-sequencing-based-genotyping.pdf
p1_nar2026|$P/mine/gkag023.pdf
p6_linde_bmc2023|$P/mine/s12864-023-09343-z.pdf
p5_methylome_bmc2025|$P/mine/s12864-025-11592-z.pdf
p4_assembly_bmc2025|$P/mine/s12864-025-11793-6.pdf
p2_scidata2025|$P/mine/s41597-025-06319-4.pdf
o_alpaqa_biorxiv2026|$P/others/2026.03.20.713089v2.full.pdf
o_mpoa_genomeres2024|$P/others/Genome Res.-2024-Lohde-2039-47.pdf
LIST
mkdir -p "$O/fli_linde_wip"
for i in 1 2 3 4 5; do
  pdftoppm -r 300 -png -singlefile "$P/mine/wip-fli-paper/Figure$i.pdf" "$O/fli_linde_wip/Figure$i"
done
echo done
