"""How many false cgMLST allele differences do sequencing errors create?

Two figures for the talk (Part I, algorithmic slides):

  fig_sim_allele_diffs.png
      Consensus (assembly) error rate -> expected false allele differences
      between two genomes of the *same* strain. Analytical (Poisson/binomial)
      plus Monte-Carlo check. Threshold: EHEC outbreak cluster <= 10 alleles.

  fig_sim_majority_vote.png
      Why random read errors vanish in the consensus but systematic ones don't:
      P(consensus base wrong) under a majority vote, as a function of the
      per-read error probability at one position, for several coverages.

Model assumptions (state them on the slide notes):
  * cgMLST scheme with N = 2,513 loci (EnteroBase E. coli cgMLST v1),
    mean locus length L = 1,000 bp  -> ~2.5 Mb of typed sequence.
  * Errors are independent, uniform over positions; any error in a locus
    produces a new (wrong) allele.
  * Two isolates of the same strain sequenced independently: a locus differs
    if either genome carries an error in it (errors at identical positions with
    identical base are ignored, negligible).
  * Majority vote: consensus wrong if the wrong base has > n/2 support
    (worst case: all erroneous reads agree on the same wrong base, as for
    systematic errors; for random substitutions spread over 3 bases the
    real probability is even lower).

Run:  .venv/bin/python scripts/sim_cgmlst_errors.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import binom, poisson

OUT = Path(__file__).resolve().parents[1] / "figures" / "generated"
OUT.mkdir(parents=True, exist_ok=True)

N_LOCI = 2513
LOCUS_LEN = 1000
THRESH = 10
RNG = np.random.default_rng(42)

C_DARK = "#173047"
C_BLUE = "#3E6E9B"
C_GREEN = "#4EA72E"
C_RED = "#C0392B"
C_GREY = "#8A8F98"

plt.rcParams.update({
    "font.family": "Helvetica",
    "font.size": 13,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.edgecolor": "#444444",
    "axes.labelcolor": "#222222",
    "xtick.color": "#444444",
    "ytick.color": "#444444",
    "savefig.dpi": 300,
})


def expected_false_alleles(err):
    """Expected number of loci that differ between two same-strain genomes."""
    p_locus_one = 1 - (1 - err) ** LOCUS_LEN          # one genome wrong in locus
    p_locus_pair = 1 - (1 - p_locus_one) ** 2          # either genome wrong
    return N_LOCI * p_locus_pair


def monte_carlo(err, reps=2000):
    """Simulate errors per genome; count loci with >=1 error in either genome."""
    n_err_a = RNG.binomial(LOCUS_LEN, err, size=(reps, N_LOCI))
    n_err_b = RNG.binomial(LOCUS_LEN, err, size=(reps, N_LOCI))
    return ((n_err_a + n_err_b) > 0).sum(axis=1)


# ---------------------------------------------------------------- figure 1
q = np.linspace(30, 70, 400)                 # consensus quality (Phred)
err = 10 ** (-q / 10)
mean = expected_false_alleles(err)
lo = poisson.ppf(0.025, mean)
hi = poisson.ppf(0.975, mean)

fig, ax = plt.subplots(figsize=(7.2, 4.4))
ax.fill_between(q, np.maximum(lo, 0.08), hi, color=C_BLUE, alpha=0.18, lw=0,
                label="95% range")
ax.plot(q, np.maximum(mean, 0.08), color=C_BLUE, lw=2.6, label="expected")

# Monte-Carlo check at a few points
q_mc = np.array([40, 45, 50, 55, 60])
mc = [monte_carlo(10 ** (-x / 10), reps=400) for x in q_mc]
ax.errorbar(q_mc, [m.mean() for m in mc],
            yerr=[[m.mean() - np.percentile(m, 2.5) for m in mc],
                  [np.percentile(m, 97.5) - m.mean() for m in mc]],
            fmt="o", color=C_DARK, ms=5, capsize=3, lw=1.2, label="simulation")

ax.axhline(THRESH, color=C_RED, lw=1.6, ls="--")
ax.text(30.5, THRESH * 0.75, "EHEC cluster threshold: ≤ 10 alleles",
        color=C_RED, ha="left", va="top", fontsize=12)

ax.set_yscale("log")
ax.set_ylim(0.08, 2000)
ax.set_xlim(30, 70)
ax.set_xlabel("Consensus accuracy (Phred Q)")
ax.set_ylabel("False allele differences\n(same strain, two genomes)")

# secondary axis with accuracy in %
def q2acc(x):
    return x
sec = ax.secondary_xaxis("top")
ticks = [30, 40, 50, 60, 70]
sec.set_xticks(ticks)
sec.set_xticklabels(["99.9%", "99.99%", "99.999%", "99.9999%", ""],
                    fontsize=10, color=C_GREY)
sec.spines["top"].set_visible(False)
sec.tick_params(length=0)

# annotate a few points
for qq in (40, 50, 60):
    m = expected_false_alleles(10 ** (-qq / 10))
    ax.annotate(f"≈ {m:.0f}" if m >= 1 else f"≈ {m:.1f}",
                xy=(qq, m), xytext=(qq + 0.8, m * 1.6), fontsize=12, fontweight="bold",
                color=C_DARK)

ax.legend(frameon=False, loc="upper right", fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig_sim_allele_diffs.png", transparent=False, facecolor="white")
plt.close(fig)

# Q needed to stay below threshold on average
q_need = q[np.argmax(mean <= THRESH)]
print(f"[fig1] expected false alleles drops to <= {THRESH} at Q ≈ {q_need:.1f} "
      f"(error rate ≈ {10 ** (-q_need / 10):.1e}, i.e. ≈ "
      f"{10 ** (-q_need / 10) * N_LOCI * LOCUS_LEN:.0f} errors per 2.5 Mb)")
for qq in (30, 40, 50, 60):
    print(f"   Q{qq}: {expected_false_alleles(10 ** (-qq / 10)):.1f}")

# ---------------------------------------------------------------- figure 2
p = np.linspace(0, 1, 501)
fig, ax = plt.subplots(figsize=(7.2, 4.4))
for n, c, lab in [(10, C_GREY, "10×"), (30, C_BLUE, "30×"), (100, C_DARK, "100×")]:
    # wrong consensus if wrong base supported by > n/2 reads; ties = 50%
    k = np.floor(n / 2)
    p_wrong = binom.sf(k, n, p)
    if n % 2 == 0:
        p_wrong += 0.5 * binom.pmf(n // 2, n, p)
    ax.plot(p, p_wrong, lw=2.4, color=c, label=f"coverage {lab}")

ax.axvspan(0.0, 0.05, color=C_GREEN, alpha=0.15, lw=0)
ax.text(0.065, 0.55, "random read errors\n(1–5% per read)", ha="left", va="center",
        fontsize=11, color="#2E6B1A")
ax.axvspan(0.35, 0.65, color=C_RED, alpha=0.10, lw=0)
ax.text(0.36, 0.86, "systematic errors\n(e.g. modified motif)", ha="left",
        va="bottom", fontsize=11, color=C_RED)

ax.set_xlim(0, 1)
ax.set_ylim(-0.02, 1.02)
ax.set_xlabel("Fraction of reads with the same error at a position")
ax.set_ylabel("P(consensus base wrong)")
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0.62, 0.62), fontsize=11)
fig.tight_layout()
fig.savefig(OUT / "fig_sim_majority_vote.png", facecolor="white")
plt.close(fig)

for n in (10, 30, 100):
    print(f"[fig2] n={n}: P(wrong | p=0.01)={binom.sf(n // 2, n, 0.01):.1e}, "
          f"P(wrong | p=0.45)={binom.sf(n // 2, n, 0.45):.2f}, "
          f"P(wrong | p=0.55)={binom.sf(n // 2, n, 0.55):.2f}")
print("written to", OUT)
