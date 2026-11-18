"""Build the habilitation deck from Martin's original pptx (never modified).

Output: build/2026-FU-Habil-Hoelzer-Talk_vXX.pptx   (VERSION below)

Strategy
- Start from a copy of the original deck; keep Martin's slides 1-9 as they are
  (only typo/date fixes), fill the ChatGPT placeholder slides, add new slides by
  duplicating a slide of the same part (keeps the coloured part bar + labels),
  reorder, and move spare figure slides to the appendix.
- All figures come from figures/generated, figures/crops, figures/candidates.
- Speaker notes = draft talk script with timing.

Run: .venv/bin/python scripts/build_deck.py
"""
import copy
from pathlib import Path

from lxml import etree
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

VERSION = "v02"
REPO = "github.com/hoelzer/habil-talk-2026"   # TODO Martin: final repository URL
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "2026-FU-Habil-Hoelzer-Talk.pptx"
OUT = ROOT / "build" / f"2026-FU-Habil-Hoelzer-Talk_{VERSION}.pptx"
CACHE = ROOT / "build" / "img_cache"
CACHE.mkdir(parents=True, exist_ok=True)

G = ROOT / "figures/generated"
C = ROOT / "figures/crops"
K = ROOT / "figures/candidates"
P = K / "papers"

DATE = "December 2, 2026"
DARK = RGBColor(0x17, 0x30, 0x47)
GREY = RGBColor(0x6B, 0x72, 0x7B)
ACCENT = {"I": RGBColor(0x3E, 0x6E, 0x9B), "II": RGBColor(0x3B, 0x7D, 0x23),
          "III": RGBColor(0x15, 0x60, 0x82), "IV": RGBColor(0xA0, 0x2B, 0x93),
          "INTRO": DARK, "CLOSE": DARK, "APP": DARK}

prs = Presentation(SRC)
ORIG = list(prs.slides)          # ORIG[i-1] == original slide i


def O(i):
    return ORIG[i - 1]


# ---------------------------------------------------------------- helpers
def img(path, max_px=2200):
    """Downscale large images into a cache to keep the pptx small."""
    path = Path(path)
    out = CACHE / (path.parent.name + "__" + path.stem + ".png")
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        im = Image.open(path)
        if im.mode in ("P", "LA", "RGBA"):
            bg = Image.new("RGB", im.size, "white")
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg
        im = im.convert("RGB")
        if max(im.size) > max_px:
            im.thumbnail((max_px, max_px), Image.LANCZOS)
        im.save(out, optimize=True)
    return out


def add_fig(slide, path, l, t, w, h, align="center"):
    """Fit picture into box (inches), keep aspect ratio."""
    p = img(path)
    iw, ih = Image.open(p).size
    box_ar, im_ar = w / h, iw / ih
    if im_ar > box_ar:
        pw, ph = w, w / im_ar
    else:
        pw, ph = h * im_ar, h
    pl = l + (w - pw) / 2 if align == "center" else l
    pt = t + (h - ph) / 2
    return slide.shapes.add_picture(str(p), Inches(pl), Inches(pt), Inches(pw), Inches(ph))


def _bullet(par, char="•"):
    pPr = par._p.get_or_add_pPr()
    pPr.set("marL", str(Emu(Inches(0.18))))
    pPr.set("indent", str(-Emu(Inches(0.18))))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def add_text(slide, lines, l, t, w, h, size=14, color=DARK, bold=False, bullets=False,
             align=PP_ALIGN.LEFT, space=6, italic=False):
    """lines: list of str or (str, dict(size,bold,color,italic)) tuples. '**x**' not parsed."""
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    for m in ("margin_left", "margin_right", "margin_top", "margin_bottom"):
        setattr(tf, m, Inches(0.02))
    if isinstance(lines, str):
        lines = [lines]
    for k, line in enumerate(lines):
        opts = {}
        if isinstance(line, tuple):
            line, opts = line
        par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        par.alignment = align
        par.space_after = Pt(space)
        if bullets and not opts.get("nobullet"):
            _bullet(par)
        r = par.add_run()
        r.text = line
        f = r.font
        f.size = Pt(opts.get("size", size))
        f.bold = opts.get("bold", bold)
        f.italic = opts.get("italic", italic)
        f.color.rgb = opts.get("color", color)
    return tb


def cite(slide, text, l=0.3, t=5.02, w=9.2):
    return add_text(slide, text, l, t, w, 0.28, size=8, color=GREY)


def takeaway(slide, text, part, t=4.62):
    """Bottom key message with a small coloured marker (Martin's slide-3 style)."""
    bar = slide.shapes.add_shape(1, Inches(0.3), Inches(t + 0.05), Inches(0.06), Inches(0.3))
    bar.fill.solid()
    bar.fill.fore_color.rgb = ACCENT[part]
    bar.line.fill.background()
    return add_text(slide, text, 0.45, t, 9.1, 0.42, size=15, bold=True, color=DARK)


def set_title(slide, text):
    for sh in slide.shapes:
        if sh.is_placeholder and sh.placeholder_format.type == 1:   # TITLE
            sh.text_frame.text = text
            return sh
    raise ValueError("no title placeholder")


def set_section(slide, text):
    for sh in slide.shapes:
        if sh.name == "TextBox 5" and sh.has_text_frame:
            runs = [r for p in sh.text_frame.paragraphs for r in p.runs]
            runs[0].text = text
            for r in runs[1:]:
                r.text = ""
            return


def remove_shapes(slide, names=("Shape 4", "Text 5", "Text 6")):
    for sh in list(slide.shapes):
        if sh.name in names and not sh.is_placeholder:
            sh._element.getparent().remove(sh._element)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text.strip()


def duplicate(src):
    """Duplicate a slide (shapes + picture rels) and append it to the deck."""
    new = prs.slides.add_slide(src.slide_layout)
    for sh in list(new.shapes):
        sh._element.getparent().remove(sh._element)
    rid_map = {}
    for rId, rel in src.part.rels.items():
        if rel.reltype in (RT.NOTES_SLIDE, RT.SLIDE_LAYOUT):
            continue
        if rel.is_external:
            rid_map[rId] = new.part.relate_to(rel.target_ref, rel.reltype, is_external=True)
        else:
            rid_map[rId] = new.part.relate_to(rel.target_part, rel.reltype)
    tree = new.shapes._spTree
    ext = tree.find(qn("p:extLst"))
    for el in src.shapes._spTree.iterchildren():
        if el.tag in (qn("p:nvGrpSpPr"), qn("p:grpSpPr"), qn("p:extLst")):
            continue
        ne = copy.deepcopy(el)
        for node in ne.iter():
            for a in list(node.attrib):
                if a.startswith("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"):
                    if node.attrib[a] in rid_map:
                        node.attrib[a] = rid_map[node.attrib[a]]
        if ext is not None:
            ext.addprevious(ne)
        else:
            tree.append(ne)
    return new


def strip_content(slide):
    """For duplicated slides: drop everything except title, part bar, labels, footer."""
    keep_names = {"Shape 0", "Date Placeholder 2", "Footer Placeholder 3",
                  "Slide Number Placeholder 4", "Title 1"}
    for sh in list(slide.shapes):
        if sh.name not in keep_names:
            sh._element.getparent().remove(sh._element)


def new_from(src, title):
    s = duplicate(src)
    strip_content(s)
    set_title(s, title)
    return s


# Layout constants (inches) — slide is 10 x 5.625
FL, FT, FW, FH = 0.3, 0.78, 6.15, 3.8        # figure box (left part)
TL, TT, TW, TH = 6.65, 0.95, 3.1, 3.6         # text box (right part)
WIDE = (0.3, 0.78, 9.4, 3.8)                  # full-width figure box

S = {}   # final slides by key

# ================================================================ INTRO
S["title"] = O(1)
notes(O(1), """
[0:00, 0.5 min] Thank the committee. Title. One sentence on the plan:
from errors in nanopore data, to methylation as a signal, to methylation-aware computation.
""")
S["outbreaks"] = O(2)
notes(O(2), """
[0.5 min, 1 min] Two outbreaks the RKI was involved in: EHEC O45:H2 in 2025 (foodborne,
severe infections) and Ralstonia mannitolilytica in 2026 (contaminated prefilled syringes,
several hospitals). Different pathogens, same question: are these isolates one outbreak?
We will come back to both at the end.
""")
S["mst"] = O(3)
notes(O(3), """
[1.5 min, 1 min] cgMLST: compare ~2,500 genes, count genes with different alleles.
For EHEC, <= 10 allele differences = same cluster. Ten differences in 2.5 million bases.
Ask: what if some of these differences are sequencing errors?
""")
S["technical"] = O(4)
notes(O(4), """
[2.5 min, 1 min] A single wrong base creates a new allele, and can move an isolate in or
out of a cluster. That is why, in outbreak typing, every nucleotide counts.
""")
S["contrib"] = O(5)
notes(O(5), """
[3.5 min, 1.5 min] Three lines of work: (1) genome accuracy for outbreak typing,
(2) methylation analysis from raw signals, (3) methylation-aware machine learning.
Most of the methylation work is the PhD project of Valentina Galeone.
'Genome Med · ongoing' = the submitted FLI 2026 ring trial (Linde et al.).
""")
S["promise"] = O(6)
notes(O(6), """
[5 min, 1.5 min] Why nanopore: long reads (complete genomes), real time, portable,
native DNA (modifications). Challenge: we never read bases directly; we infer them from
a noisy electrical signal.
""")

# ================================================================ PART I
S["sec1"] = O(7)
notes(O(7), "[6.5 min] Part I: what is actually measured, and what accuracy outbreak typing needs.")
S["howworks"] = O(8)
for sh in list(O(8).shapes):          # Martin's reminder note on the slide
    if sh.name == "TextBox 9":
        sh._element.getparent().remove(sh._element)
notes(O(8), """
[7 min, 1.5 min] DNA passes through a protein pore; the current depends on ~9 bases
inside the pore at once (k-mer). So the signal for one base depends on its neighbours,
and on chemical changes such as methylation.
""")
S["basecalling"] = O(9)
notes(O(9), """
[8.5 min, 1 min] Basecalling = sequence labelling: a neural network turns signal chunks
into bases plus a confidence. It learns from training data; whatever is not in the
training data (rare modifications) it cannot interpret.
""")

s = new_from(O(10), "How accurate must a genome be for outbreak typing?")
add_fig(s, G / "fig_sim_allele_diffs.png", FL, 0.75, FW, 3.85)
add_text(s, [("Simple model", {"bold": True, "size": 13, "color": ACCENT["I"]}),
             "2,513 cgMLST genes, ~1 kb each",
             "Two genomes of the same strain",
             "Each base error → new allele",
             ("", {"size": 6}),
             ("≤ 10 alleles needs ~Q57", {"bold": True}),
             "≈ 5 errors in 2.5 Mb"],
         TL, TT, TW, TH, size=14, space=5)
takeaway(s, "Outbreak typing needs near-perfect genomes: 99.99% is far from enough.", "I")
cite(s, "Own simulation (analytical + Monte Carlo); scheme size: EnteroBase E. coli cgMLST. Code: " + REPO)
notes(s, """
[9.5 min, 1.5 min] Own back-of-the-envelope model. Expected false allele differences
E = N * (1 - (1 - e)^(2L)), N = 2,513 loci, L = 1 kb, e = consensus error rate.
Q40 (99.99%) gives ~450 false differences, Q50 ~50, Q60 ~5. To stay below the EHEC
threshold of 10, we need about Q57: at most ~5 errors in the whole typed genome.
Dots = Monte-Carlo simulation, line = formula.
""")
S["sim1"] = s

s = O(10)
remove_shapes(s)
set_title(s, "Random errors average out, systematic errors do not")
add_fig(s, G / "fig_sim_majority_vote.png", FL, 0.75, FW, 3.85)
add_text(s, [("Consensus = majority vote", {"bold": True, "size": 13, "color": ACCENT["I"]}),
             "Random errors vanish with coverage",
             "Same error in ~50% of reads: a coin flip",
             "More coverage does not help",
             ("", {"size": 6}),
             ("Reads 99% accurate, genome can still be wrong", {"bold": True})],
         TL, TT, TW, TH, size=14, space=5)
takeaway(s, "Systematic errors decide whether typing is reproducible.", "I")
cite(s, "Binomial majority vote; worst case: all erroneous reads agree on the same wrong base.")
notes(s, """
[11 min, 1.5 min] Why raw read accuracy is the wrong metric: at 50x, a 1% random error
is outvoted (P ~ 1e-70). But if a modification makes ~half of the reads wrong at the same
position, the consensus becomes a coin flip — and small changes in read frequency decide
the allele. This is exactly what we saw in the multicenter study (next part).
""")
S["sim2"] = s

# ================================================================ PART II
S["sec2"] = O(11)
notes(O(11), """
[12.5 min] Part II: from reads to reliable genomes. Four studies, 2023 to 2026.
Questions: Is ONT accurate enough? Is it reproducible? Can computation fix the rest?
""")

s = O(12)
remove_shapes(s)
set_title(s, "2023: accuracy depends on the species")
add_fig(s, P / "p6_linde_bmc2023/img-005.png", 0.3, 0.85, 3.0, 3.6)
add_fig(s, P / "p6_linde_bmc2023/img-006.png", 3.45, 0.75, 3.3, 3.85)
add_text(s, ["Illumina vs ONT R9 / R10",
             "3 highly pathogenic species, 6 strains each",
             ("F. tularensis: ONT ≈ Illumina", {"bold": True}),
             ("B. anthracis: only with R10", {"bold": True}),
             ("Brucella suis: still differences", {"bold": True})],
         7.0, TT, 2.8, TH, size=13, bullets=True, space=6)
takeaway(s, "Early ONT typing worked for some species, not for all.", "II")
cite(s, "Linde, Brangsch, Hölzer et al. BMC Genomics 2023, 24:258")
notes(s, """
[13 min, 1 min] First benchmark with FLI Jena: Bacillus anthracis, Brucella suis,
Francisella tularensis; Illumina vs ONT R9.4.1 and R10.4. Trees: cgMLST minimum spanning
trees. Message: it depends on the species.
""")
S["p2023"] = s

s = O(13)
remove_shapes(s)
set_title(s, "2024: five labs, same strains, different allele calls")
add_fig(s, P / "p3_multicenter_jcm2024/img-004.png", 0.3, 0.8, 2.6, 1.3)
add_fig(s, P / "p3_multicenter_jcm2024/img-007.png", 0.3, 2.15, 6.4, 2.45)
add_text(s, ["5 labs · 4 species · > 500 datasets",
             "R10.4.1, same chemistry everywhere",
             ("Errors are strain-specific", {"bold": True}),
             ("… and occur in every lab", {"bold": True}),
             "Some strains far above the cluster threshold"],
         7.0, TT, 2.8, TH, size=13, bullets=True, space=6)
takeaway(s, "Same chemistry, same strain: the genotype is not always reproducible.", "II")
cite(s, "Dabernig-Heinz, Lohde, Hölzer et al. J Clin Microbiol 2024, 62:e00628-24")
notes(s, """
[14 min, 1.5 min] Multicenter study (Graz, Jena, Greifswald, Vienna, RKI). Each lab
sequenced the same strains. Plot: allele differences to the Illumina reference, per lab;
line = cluster threshold. Most strains fine, a few strains wrong in every lab.
""")
S["p2024"] = s

s = O(15)
remove_shapes(s)
set_title(s, "Errors sit at the same motifs in every lab")
add_fig(s, P / "p3_multicenter_jcm2024/img-008.png", 0.3, 0.8, 4.4, 3.75)
add_fig(s, C / "orig_raw_native_pcr.png", 4.85, 0.8, 4.85, 3.0)
add_text(s, "PCR copy (no methylation): error gone", 5.0, 3.85, 4.6, 0.3, size=12, color=GREY)
takeaway(s, "Errors follow methylation motifs. Masking (MPOA) or PCR removes them.", "II")
cite(s, "Dabernig-Heinz et al. JCM 2024 (sequence logos, 5 labs); Lohde et al. Genome Res 2024 (raw signal, K. pneumoniae; MPOA)")
notes(s, """
[15.5 min, 1.5 min] Left: sequence context of ambiguous positions — the same motifs in
all five labs (e.g. GAAGAC in Listeria, RACC in E. faecium). Right: raw signal at such a
position, native DNA vs PCR-amplified DNA. PCR removes methylation; the signal shift
disappears. Computational fix by Lohde et al.: MPOA finds positions with mixed base calls
and masks them — reference-free.
""")
S["motifs"] = s

s = O(16)
remove_shapes(s)
set_title(s, "Assembly and polishing are computational choices")
add_fig(s, P / "p4_assembly_bmc2025/img-003.png", 0.3, 0.8, 4.3, 2.0)
add_fig(s, P / "p4_assembly_bmc2025/img-005.png", 0.3, 2.85, 4.3, 1.75)
add_fig(s, P / "p4_assembly_bmc2025/img-007.png", 4.75, 0.8, 2.5, 3.75)
add_text(s, [("Perfect genomes are possible", {"bold": True}),
             "Polishing can add errors",
             "Newer model not always better",
             "81% of errors in genes",
             "6.5% caused by methylation"],
         7.35, TT, 2.45, TH, size=13, bullets=True, space=6)
takeaway(s, "More polishing is not always better: validate every pipeline.", "II")
cite(s, "Thomas, …, Hölzer, Linde. BMC Genomics 2025, 26:783")
notes(s, """
[17 min, 1.5 min] Benchmark of basecallers, assemblers and polishers against Sanger-based
references. Several combinations give perfect genomes (B. anthracis, Listeria, S. aureus …),
but polishing can also introduce errors, and for Brucella abortus an older model was
better. 81% of remaining errors are in coding genes — exactly where cgMLST looks.
6.5% are methylation-related; the methylation-aware Medaka model reduces them.
""")
S["assembly"] = s

s = O(18)
remove_shapes(s)
set_title(s, "2026: ten labs, routine workflows, reproducible typing")
add_fig(s, K / "papers/fli_linde_wip/Figure3.png", FL, 0.78, FW, 3.8)
add_text(s, ["10 labs: veterinary, food, public health",
             "Own routine lab and analysis workflows",
             ("cgMLST: mostly < 5 alleles", {"bold": True}),
             ("Resistance genes: fully reproducible", {"bold": True}),
             "Few strain-specific outliers"],
         TL, TT, TW, TH, size=13, bullets=True, space=6)
takeaway(s, "Today, ONT typing is reproducible — with few, specific exceptions.", "II")
cite(s, "Linde, Galeone, …, Hölzer, …, Abdel-Glil. Under review (2026)")
notes(s, """
[18.5 min, 1.5 min] Most recent: interlaboratory study led by FLI. Ten labs, three
strains each of C. difficile, K. pneumoniae, Salmonella, Yersinia; everyone used their
own routine workflow. cgMLST between labs mostly below five alleles; AMR genes identical.
So technology and computation have caught up. What remains?
""")
S["p2026"] = s

s = new_from(O(18), "97.3% correct: what causes the remaining errors?")
add_fig(s, C / "alpaqa_fig1.png", 0.3, 0.78, 5.5, 2.55)
add_fig(s, P / "o_alpaqa_biorxiv2026/img-002.png", 0.3, 3.35, 5.5, 1.25)
add_fig(s, ROOT / "figures/received/urban-supp3-dnd.png", 5.95, 0.75, 3.8, 3.85)
takeaway(s, "The remaining errors are not random: they are rare DNA modifications.", "II")
cite(s, "Biggel, …, Urban. bioRxiv 2026, doi:10.64898/2026.03.20.713089, Fig. 1, 2, Suppl. Fig. S3 (CC BY 4.0)")
notes(s, """
[20 min, 1.5 min] Independent study (Biggel, Urban et al., Zurich/CDC). 294 isolates:
97.3% near-identical to the hybrid reference. The outliers (red/purple) carry dnd
(phosphorothioate) or dpd (7-deazaguanine) systems — modifications that the basecaller
was never trained on. Bottom: consensus quality drops exactly at the modified motif.
alpaqa uses these quality dips to flag unreliable assemblies — no reference needed.
Right: how common such systems are in public genomes (dnd red, dpd purple). Top of the
list: Mycobacterium abscessus, 22.5% — which brings us to our own example.
""")
S["alpaqa"] = s

s = new_from(O(18), "M. abscessus: a modification the basecaller never learned")
add_fig(s, C / "phd_mabs_plot.png", 0.3, 0.78, 3.4, 3.8)
add_fig(s, C / "phd_pt_vs_methyl.png", 3.85, 0.78, 5.9, 2.3)
add_text(s, ["Calls at GGCC change between basecaller models",
             ("Not methylation: phosphorothioate", {"bold": True}),
             "Sulfur in the DNA backbone, added by Dnd proteins",
             "Rare, so missing from training data"],
         4.05, 3.15, 5.6, 1.45, size=13, bullets=True, space=3)
takeaway(s, "What the model has not seen, it calls wrong — but the signal is there.", "II")
cite(s, "Galeone et al., ongoing; with A. Lewin (RKI). Cf. Biggel et al. bioRxiv 2026")
notes(s, """
[21.5 min, 1.5 min] Our own example. In Mycobacterium abscessus, Valentina saw unstable
calls at GGCC: they changed between Dorado models and between native and PCR DNA.
After Lara Urban's talk it became clear: phosphorothioate, a sulfur instead of an oxygen
in the backbone. Not in the training data, so the model mislabels it.
Fix the title: italic M. abscessus in PowerPoint if wanted.
""")
S["mabs"] = s

s = O(20)
remove_shapes(s)
add_fig(s, K / "val_phd/s03_1_2460x1410.png", 0.4, 0.85, 4.4, 2.55)
add_fig(s, K / "val_phd/s03_2_2460x1410.png", 5.2, 0.85, 4.4, 2.55)
add_text(s, "unmodified", 0.4, 3.42, 4.4, 0.3, size=12, color=GREY, align=PP_ALIGN.CENTER)
add_text(s, "modified base: the current shifts", 5.2, 3.42, 4.4, 0.3, size=12, color=GREY,
         align=PP_ALIGN.CENTER)
add_text(s, "Not everything that complicates the signal is noise. Some of it is biology.",
         0.4, 3.95, 9.2, 0.5, size=18, bold=True, color=ACCENT["II"], align=PP_ALIGN.CENTER)
cite(s, "Illustration: V. Galeone")
notes(s, """
[23 min, 0.5 min] The turning point. The signal shift that causes basecalling errors is a
measurement of a chemical modification. Instead of masking it, we can read it.
""")
S["twist"] = s

# ================================================================ PART III
S["sec3"] = O(21)
set_section(O(21), "From sequencing errors to epigenetic information")
notes(O(21), "[23.5 min] Part III: reading bacterial methylation — computationally and reproducibly.")

s = new_from(O(22), "Keep the raw signal: it holds more than the sequence")
add_fig(s, C / "phd_scidata_squidbase.png", 0.3, 0.78, 4.4, 3.8)
add_text(s, ["79 isolates · 6 species · 3 labs",
             "~1.4 TB of raw signal (POD5)",
             ("Re-basecall with future models", {"bold": True}),
             ("Call modifications later", {"bold": True}),
             "Benchmark new methods",
             "Raw signal is still rarely shared: new repositories (SquiDBase)"],
         5.0, TT, 4.6, TH, size=14, bullets=True, space=7)
takeaway(s, "Sequences are an interpretation. The raw signal is the measurement.", "III")
cite(s, "Dabernig-Heinz, Galeone, …, Hölzer, Wagner. Sci Data 2025; Cuypers et al. NAR Genom Bioinform 2026 (SquiDBase)")
notes(s, """
[24 min, 1 min] Basecalled FASTQ files are shared routinely, raw signal almost never
(large files, few repositories). We published 1.4 TB of raw signal from the multicenter
study. Our own later re-analyses and the methylation work depend on it.
""")
S["rawdata"] = s

s = O(22)
remove_shapes(s)
set_title(s, "Bacterial methylation: a defence system with a fingerprint")
add_fig(s, ROOT / "figures/received/ecosalplus.esp-0014-2022.f002-cropped.png", 0.3, 0.78, 5.6, 2.6)
add_fig(s, K / "val_kitasato/s05_1_1200x510.png", 0.5, 3.4, 2.9, 1.2)
add_fig(s, C / "phd_motifs.png", 6.1, 0.85, 3.6, 2.4)
add_text(s, ["Methyltransferase marks own DNA at a motif",
             "Unmarked foreign DNA (phage) is cut",
             ("Motif sets differ between strains", {"bold": True})],
         3.6, 3.45, 6.1, 1.2, size=13, bullets=True, space=3)
cite(s, "Anton et al. EcoSal Plus 2025, Fig. 2A (CC BY 4.0); motif sketches: V. Galeone")
notes(s, """
[25 min, 1.5 min] Bacteria methylate adenine (6mA) or cytosine (4mC, 5mC) at short
motifs, e.g. GATC. Restriction-modification: own DNA is methylated and protected; phage
DNA is not, and gets cut. Unlike humans, nearly every motif occurrence is methylated.
Each strain carries its own set of systems — an epigenetic fingerprint.
""")
S["rm"] = s

s = O(23)
remove_shapes(s)
set_title(s, "From probabilistic calls to motifs")
add_fig(s, G / "fig_calls_to_motif.png", 0.3, 0.78, 9.4, 3.75)
takeaway(s, "Choices matter: probability threshold, coverage, partially methylated sites.", "III")
cite(s, "Schematic (toy data). Threshold 0.7 as in Galeone et al. BMC Genomics 2025")
notes(s, """
[26.5 min, 1.5 min] The computational chain. (1) The basecaller reports, per read and per
base, a probability that the base is modified. (2) We threshold (0.7, from our 2025
benchmark). (3) Per genome position: fraction of reads called modified. (4) Motif search:
which short sequences are (almost) always modified? Partial methylation and low coverage
make steps 2-4 uncertain.
""")
S["calls"] = s

s = O(24)
remove_shapes(s)
set_title(s, "ont-methylation: a reproducible workflow for bacterial methylomes")
add_fig(s, ROOT / "figures/received/valentina-workflow.png", 0.3, 0.75, 6.4, 3.85)
add_text(s, ["Basecalling with modification models (Dorado)",
             "Alignment to the assembly",
             "Per-site methylation and motif search (modkit)",
             "Reports per sample",
             ("Nextflow; proposed to nf-core (ontbmod)", {"bold": True})],
         6.9, TT, 2.85, TH, size=13, bullets=True, space=6)
cite(s, "github.com/rki-mf1/ont-methylation · Galeone et al. BMC Genomics 2025")
notes(s, """
[28 min, 1 min] Valentina's pipeline: basecalling with modification models, alignment,
modkit pileup and motif discovery, reports. Now restructured as a modular Nextflow
pipeline and proposed to nf-core.
""")
S["pipeline"] = s

s = O(25)
remove_shapes(s)
add_fig(s, C / "phd_methyl_table.png", 0.3, 0.78, 9.4, 3.8)
takeaway(s, "Each strain has its own motif set — known and new motifs.", "III")
cite(s, "Galeone, Dabernig-Heinz, Lohde, Brandt, Kohler, Wagner, Hölzer. BMC Genomics 2025, 26:394")
notes(s, """
[29 min, 1.5 min] Four public-health species, two isolates each. Blue = methylated base,
orange = methylated on the opposite strand. Even two isolates of the same species carry
different motifs (e.g. the two K. pneumoniae). We found known motifs and new ones.
""")
S["profiles"] = s

s = O(26)
remove_shapes(s)
set_title(s, "Methylation calls are reproducible across labs")
add_fig(s, P / "p5_methylome_bmc2025/img-003.png", 0.3, 0.78, 3.6, 3.8)
add_fig(s, K / "papers/fli_linde_wip/Figure5.png", 4.05, 0.78, 3.4, 3.8)
add_text(s, ["Same motifs in 3 labs (2025) …",
             "… and in 5 labs (2026)",
             ("Differences: partially methylated motifs", {"bold": True})],
         7.6, TT, 2.2, TH, size=12, bullets=True, space=6)
takeaway(s, "Reliable enough to use methylation as a feature.", "III")
cite(s, "Galeone et al. BMC Genomics 2025 (left); Linde, Galeone et al., under review (right)")
notes(s, """
[30.5 min, 1.5 min] Before using methylation for anything else, it must be reproducible.
Left: methylated fraction per motif in three labs. Right: the 2026 ten-lab study,
methylation sub-study in five labs. Fully methylated motifs agree; differences only for
partially methylated motifs.
""")
S["repro"] = s

s = new_from(O(26), "Back to the outbreak: methylomes of EHEC O45:H2")
add_fig(s, C / "phd_ehec_outbreak.png", 0.3, 0.78, 9.4, 3.8)
takeaway(s, "The pipeline runs on outbreak genomes, not only on reference strains.", "III")
cite(s, "Lang, Fruth, Sedaghatjoo, Galeone, Flieger. Microbiol Resour Announc 2026, 15(10):e00231-26; with RKI FG11")
notes(s, """
[32 min, 1 min] Back to the first outbreak of the talk. For the 2025 EHEC O45:H2 genomes,
our pipeline added methylation profiles (here: GATC methylation along the genome).
""")
S["ehec"] = s

# ================================================================ PART IV
S["sec4"] = O(28)
notes(O(28), "[33 min] Part IV: using methylation as information for classification — ongoing work.")

s = O(29)
remove_shapes(s)
set_title(s, "Can methylation tell near-identical strains apart?")
add_fig(s, C / "kit_methyl_same_dna.png", 0.3, 0.78, 5.7, 2.4)
add_fig(s, K / "val_draft/image9.png", 0.6, 3.2, 3.6, 1.4)
add_text(s, [("Metagenome binning (CAMI):", {"bold": True}),
             "98% of genomes recovered …",
             "… but only 23% for strains with ≥ 95% identity",
             ("", {"size": 6}),
             ("Our strain pairs:", {"bold": True}),
             "97.7–99.6% identical DNA",
             "share only 1–2 methyltransferases"],
         6.3, TT, 3.4, TH, size=13, space=4)
takeaway(s, "Sequence changes slowly; methylation systems change fast.", "IV")
cite(s, "Sczyrba et al. Nat Methods 2017 (CAMI); Galeone, Akiyama, Sakakibara, Hölzer, in preparation")
notes(s, """
[33.5 min, 1.5 min] Close relatives are the hard case in metagenomics: in CAMI, binners
recovered 98% of genomes without relatives but only 23% of strains with a close relative.
Methylation is driven by restriction-modification systems, which are often gained and lost.
In our strain pairs: almost identical DNA, but only one or two shared methyltransferases.
""")
S["question"] = s

s = O(30)
remove_shapes(s)
add_fig(s, K / "val_kitasato/s03_3_900x474.jpg", 0.3, 0.85, 1.9, 1.15)
add_fig(s, K / "val_kitasato/s03_4_900x473.jpg", 2.3, 0.85, 1.9, 1.15)
add_fig(s, K / "val_kitasato/s03_5_948x750.png", 0.3, 2.25, 1.9, 1.5)
add_fig(s, K / "val_kitasato/s03_6_948x750.png", 2.3, 2.25, 1.9, 1.5)
add_text(s, "content", 0.3, 2.0, 1.9, 0.25, size=10, color=GREY, align=PP_ALIGN.CENTER)
add_text(s, "style", 2.3, 2.0, 1.9, 0.25, size=10, color=GREY, align=PP_ALIGN.CENTER)
add_text(s, "sequence", 0.3, 3.75, 1.9, 0.25, size=10, color=GREY, align=PP_ALIGN.CENTER)
add_text(s, "genomic style", 2.3, 3.75, 1.9, 0.25, size=10, color=GREY, align=PP_ALIGN.CENTER)
add_fig(s, K / "val_draft/image2.png", 4.5, 0.75, 2.6, 3.85)
add_text(s, [("CNN on a DNA read", {"bold": True, "color": ACCENT["IV"]}),
             "Feature maps F (filters × positions)",
             ("Gram matrix G = F Fᵀ", {"bold": True}),
             "Which features co-occur — not where",
             "→ position-free “style” vector per read"],
         7.25, TT, 2.5, TH, size=12, space=6)
takeaway(s, "Style, not content: a learned fingerprint of a genome.", "IV")
cite(s, "Yoshimura, Hamada, Augey, Akiyama, Sakakibara. Bioinform Adv 2021 (genomic style); architecture: Galeone et al., in prep.")
notes(s, """
[35 min, 1.5 min] Idea from Sakakibara's lab (Kitasato University): borrowed from image
style transfer. A CNN separates what is drawn (content) from how (style). For DNA:
the Gram matrix of the feature maps, G = F F^T, sums over positions, so it captures which
patterns co-occur, independent of where. This gives a fixed-size style vector per read.
Algorithmic point for the committee: Gram matrix = second-order statistics of learned
features; alignment-free.
""")
S["style"] = s

s = O(31)
remove_shapes(s)
add_fig(s, K / "val_phd/s18_1_1902x972.png", 0.3, 0.8, 4.4, 2.25)
add_fig(s, K / "val_phd/s18_2_1902x972.png", 5.0, 0.8, 4.4, 2.25)
add_text(s, "4 channels: A, C, G, T", 0.3, 3.05, 4.4, 0.3, size=12, color=GREY, align=PP_ALIGN.CENTER)
add_text(s, "7 channels: + 6mA, 4mC, 5mC (per-base calls)", 5.0, 3.05, 4.4, 0.3, size=12,
         color=GREY, align=PP_ALIGN.CENTER)
add_text(s, ["Only the first layer changes: 4 → 7 inputs",
             "Filters learn base and modification together",
             "Baseline: k-mer counts over a 7-letter alphabet"],
         0.6, 3.45, 8.8, 1.1, size=13, bullets=True, space=3)
cite(s, "Galeone, Akiyama, Sakakibara, Hölzer, in preparation")
notes(s, """
[36.5 min, 1 min] Our extension, developed during Valentina's research stay in Japan
(DAAD). Each read becomes a 7 x L matrix. The network is unchanged except for the first
layer. As a simple, interpretable baseline we count k-mers over a 7-letter alphabet
(A, C, G, T, 6mA, 4mC, 5mC).
""")
S["seven"] = s

s = O(32)
remove_shapes(s)
set_title(s, "Methylation separates strains that sequence cannot")
add_fig(s, C / "kit_tsne_circled.png", FL, 0.75, 6.2, 3.85)
add_text(s, [("Accuracy 0.66 → 0.80", {"bold": True}), "(CNN and k-mers)",
             ("", {"size": 6}),
             ("R. pickettii strains", {"bold": True, "italic": True}),
             "F1 0.5 → 0.95",
             ("", {"size": 6}),
             "Top k-mers = known motifs",
             "(GATC, CCWGG, CamA motif)"],
         6.75, TT, 3.0, TH, size=13, space=2)
takeaway(s, "Ralstonia again: two populations hidden behind one name.", "IV")
cite(s, "Galeone, Akiyama, Sakakibara, Hölzer, in preparation")
notes(s, """
[37.5 min, 1.5 min] t-SNE of the style vectors. Left: DNA only — strain pairs overlap
(circled). Right: with methylation — they separate. Overall accuracy rises from ~0.66 to
~0.80 for both CNN and k-mers. Largest gain: Ralstonia pickettii, F1 from ~0.5 to 0.95.
Back to slide 2: Ralstonia isolates from clinical diagnostics can belong to different
species; methylation flags such hidden structure. Feature importance recovers known
motifs: GATC (Dam), CCWGG (Dcm), CAAAAA (CamA, C. difficile).
""")
S["strains"] = s

s = new_from(O(32), "Unseen species: the learned representation profits most")
add_fig(s, C / "kit_unseen_species.png", 0.3, 0.75, 9.4, 3.85)
takeaway(s, "Generalises beyond the training data — strongest for Klebsiella.", "IV")
cite(s, "External data: SquiDBase (Hall et al. 2024); Galeone et al., in preparation")
notes(s, """
[39 min, 1 min] Independent public data, six of nine species never seen in training.
kNN purity: how many of a read's 30 nearest neighbours share its species. CNN style gains
most with methylation (0.49 → 0.61); K. pneumoniae vs K. variicola 0.5 → 0.75.
""")
S["unseen"] = s

s = O(33)
remove_shapes(s)
set_title(s, "Host DNA is recognised by methylation alone")
add_fig(s, K / "val_draft/image8.png", FL, 0.78, 6.2, 3.75)
add_text(s, ["Mammals: dense CpG methylation",
             ("Trained on human, works on grey seal", {"bold": True}),
             "No host reference needed",
             "Limit: mitochondrial DNA is barely methylated"],
         6.75, TT, 3.0, TH, size=13, bullets=True, space=6)
takeaway(s, "Towards reference-free host decontamination.", "IV")
cite(s, "Galeone, Akiyama, Sakakibara, Hölzer, in preparation; seal data: MARRES project")
notes(s, """
[40 min, 1.5 min] Metagenomic samples contain host DNA. Third column: k-mers that contain
at least one methylated base — sequence information mostly removed — still separate host
from bacteria, and the model trained on human recognises grey seal reads. Mitochondria
fail (0.31): almost no methylation. Useful for non-model hosts without a reference.
""")
S["host"] = s

s = new_from(O(33), "Outlook: separating lineages by their methylation")
add_fig(s, G / "fig_methyl_haplotyping.png", 0.3, 0.78, 6.4, 3.8)
add_text(s, ["Mixed sample, near-identical sequence",
             "Reads × motif sites, like haplotype phasing",
             ("Re-use ideas from phasing algorithms (e.g. MethPhaser)", {"bold": True}),
             "Co-existing lineages, plasmid–host links"],
         6.9, TT, 2.85, TH, size=13, bullets=True, space=6)
takeaway(s, "Methylation as a second, fast-evolving genome for metagenomics.", "IV")
cite(s, "Schematic (toy data). Cf. Fu et al. MethPhaser (2024); Beaulaurier et al. Nat Biotechnol 2018")
notes(s, """
[41.5 min, 1 min] Outlook with Valentina: in a metagenome, reads from co-existing lineages
of one species are almost identical in sequence but may differ in methylation. A reads x
sites matrix is the same object as in haplotype phasing — so ideas from MethPhaser
(methylation-assisted phasing of human haplotypes) or minimum-error-correction formulations
could carry over. Not directly: those methods assume a diploid genome (exactly two
haplotypes); a metagenome has an unknown number of lineages at unknown abundances.
Our read clustering is already a simple form of this.
""")
S["outlook"] = s

# ================================================================ CLOSE
s = O(36)
remove_shapes(s)
set_title(s, "From noisy squiggles to richer microbial genomics")
for k, (head, body) in enumerate([
        ("Every nucleotide counts", "Typing needs near-perfect genomes; systematic errors, not average accuracy, decide."),
        ("Errors can be biology", "Many remaining errors are DNA modifications — measurable and reproducible."),
        ("Beyond sequence", "Methylation-aware models separate strains and host reads that sequence alone cannot.")]):
    add_text(s, [(head, {"bold": True, "size": 15}), (body, {"size": 13, "color": GREY})],
             0.55 + k * 3.1, 2.25, 2.8, 1.8, align=PP_ALIGN.CENTER, space=6)
add_text(s, "Not everything that complicates the signal is noise. Some of it is biology.",
         0.4, 4.3, 9.2, 0.45, size=17, bold=True, color=DARK, align=PP_ALIGN.CENTER)
add_text(s, "All simulations, figures and the slide build are reproducible: " + REPO,
         0.4, 4.8, 9.2, 0.3, size=10, color=GREY, align=PP_ALIGN.CENTER)
notes(s, """
[42.5 min, 2 min] Three lessons, one per part. Close with the sentence at the bottom.
Mention: all scripts behind the simulations, figures and the slides themselves are on GitHub.
""")
S["lessons"] = s

s = O(37)
add_text(s, [("Valentina Galeone", {"bold": True}),
             "BTR team & MF1 Genome Competence Center, RKI (Stephan Fuchs, Hugues Richard)",
             "Kitasato University: Yasubumi Sakakibara, Manato Akiyama",
             "Med. Univ. Graz: Gabriel E. Wagner, Johanna Dabernig-Heinz, Ivo Steinmetz",
             "Jena University Hospital: Christian Brandt, Mara Lohde",
             "Univ. Medicine Greifswald: Christian Kohler",
             "FLI Jena: Jörg Linde, Mostafa Abdel-Glil",
             "RKI FG11 (EHEC), FG16 (Astrid Lewin)",
             ("Funding: DAAD (research stay) · TODO", {"color": GREY})],
         0.4, 0.95, 6.0, 3.8, size=12, space=4)
notes(s, "[44.5 min, 0.5 min] Thank you. TODO Martin: complete names and funding.")
S["ack"] = s

# ================================================================ APPENDIX
S["app"] = O(45)

s = new_from(O(45), "Appendix: error model for cgMLST typing")
add_text(s, [("Expected false allele differences (two genomes, same strain)", {"bold": True}),
             "E[D] = N · (1 − (1 − ε)^(2L))",
             "N = 2,513 loci, L = 1,000 bp, ε = consensus error rate per base",
             "Q = −10 log₁₀ ε;  E[D] ≤ 10  ⇔  Q ≳ 57",
             ("", {"size": 6}),
             ("Majority-vote consensus at one position", {"bold": True}),
             "X ~ Binomial(n, p): reads with the same wrong base",
             "P(wrong) = P(X > n/2) (+ ½ P(X = n/2))",
             "p = 0.01, n = 30:  P ≈ 10⁻²⁴      p = 0.45, n = 30:  P ≈ 0.23",
             ("", {"size": 6}),
             ("Assumptions", {"bold": True}),
             "Independent errors; any error in a locus → new allele;",
             "worst case: erroneous reads agree. Code: " + REPO + " (scripts/sim_cgmlst_errors.py)"],
         0.5, 0.9, 9.0, 4.1, size=13, space=3)
S["app_model"] = s

s = new_from(O(45), "Appendix: genome assembly as a graph problem")
add_fig(s, C / "lp_debruijn.png", 0.3, 0.8, 6.0, 3.9)
add_text(s, ["k-mers → de Bruijn graph",
             "Assembly = Eulerian path (polynomial)",
             "Overlap graph: Hamiltonian path (NP-hard)",
             "Long reads span repeats: simpler graphs, complete genomes"],
         6.5, 1.0, 3.2, 3.5, size=13, bullets=True, space=6)
cite(s, "From M. Hölzer, teaching lecture 2024")
S["app_graph"] = s

s = new_from(O(45), "Appendix: genomic-style data preparation and evaluation")
add_fig(s, K / "val_draft/image1.png", 0.3, 0.8, 5.6, 2.7)
add_text(s, ["Reads clustered with CD-HIT (80% identity); whole clusters assigned to train or test → no near-duplicates across the split",
             "Random forest (200 trees) on style vectors or k-mer profiles",
             "kNN purity (k = 30): fraction of neighbours with the same label",
             "Unseen species: agglomerative clustering (Ward), ARI, homogeneity, completeness"],
         6.1, 0.9, 3.6, 3.8, size=12, bullets=True, space=6)
cite(s, "Galeone, Akiyama, Sakakibara, Hölzer, in preparation")
S["app_eval"] = s

s = new_from(O(45), "Appendix: genomic-style results in detail")
add_fig(s, K / "val_draft/image3.png", 0.3, 0.75, 5.0, 4.2)
add_fig(s, K / "val_draft/image7.png", 5.45, 0.9, 4.3, 2.5)
cite(s, "Galeone, Akiyama, Sakakibara, Hölzer, in preparation")
S["app_results"] = s

# remaining spare slides of Martin go to the appendix unchanged
SPARE = [O(i) for i in (38, 40, 41, 42, 43, 44, 46, 47, 48, 49, 50)]

ORDER = ["title", "outbreaks", "mst", "technical", "contrib", "promise",
         "sec1", "howworks", "basecalling", "sim1", "sim2",
         "sec2", "p2023", "p2024", "motifs", "assembly", "p2026", "alpaqa", "mabs", "twist",
         "sec3", "rawdata", "rm", "calls", "pipeline", "profiles", "repro", "ehec",
         "sec4", "question", "style", "seven", "strains", "unseen", "host", "outlook",
         "lessons", "ack",
         "app", "app_model", "app_graph", "app_eval", "app_results"]
final = [S[k] for k in ORDER] + SPARE

# ---------------------------------------------------------------- reorder / delete
sldIdLst = prs.slides._sldIdLst
id_of = {id(sl): el for sl, el in zip(prs.slides, list(sldIdLst))}
keep = {id(sl) for sl in final}
for sl, el in zip(list(prs.slides), list(sldIdLst)):
    if id(sl) not in keep:
        prs.part.drop_rel(el.rId)
        sldIdLst.remove(el)
for el in list(sldIdLst):
    sldIdLst.remove(el)
for sl in final:
    sldIdLst.append(id_of[id(sl)])

# ---------------------------------------------------------------- global text fixes
FIX = {"XXXXXXX YY, 2026": DATE, "Foodboren": "Foodborne", "epigentic": "epigenetic",
       "lessens": "lessons", "abseccus": "abscessus"}
for n, sl in enumerate(prs.slides, 1):
    for t in sl._element.iter(qn("a:t")):
        if t.text:
            for a, b in FIX.items():
                t.text = t.text.replace(a, b)
    for fld in sl._element.iter(qn("a:fld")):
        if fld.get("type") == "slidenum":
            t = fld.find(qn("a:t"))
            if t is not None:
                t.text = str(n)

OUT.parent.mkdir(exist_ok=True)
prs.save(OUT)
print(f"saved {OUT.relative_to(ROOT)}: {len(prs.slides)} slides "
      f"({len(ORDER) - 5} main incl. sections, {5 + len(SPARE)} appendix)")
