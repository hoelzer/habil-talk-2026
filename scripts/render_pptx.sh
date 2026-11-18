#!/usr/bin/env bash
# Render a pptx to PDF (Keynote) and PNGs. Works on a temp copy; the input is never modified.
# usage: bash scripts/render_pptx.sh in.pptx outdir [dpi]
# NOTE: needs AppleEvents to Keynote (in Claude Code: run with sandbox disabled).
set -eu
in="$1"; out="$2"; dpi="${3:-60}"
mkdir -p "$out"
tmp=$(mktemp -d); cp "$in" "$tmp/deck.pptx"
osascript "$(dirname "$0")/export_pdf.applescript" "$tmp/deck.pptx" "$(cd "$out" && pwd)/deck.pdf"
rm -f "$out"/s-*.png
pdftoppm -r "$dpi" -png "$out/deck.pdf" "$out/s"
rm -rf "$tmp"
echo "rendered $(ls "$out"/s-*.png | wc -l) slides to $out"
