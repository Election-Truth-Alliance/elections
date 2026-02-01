"""
Vote Share Histogram: precinct count by candidate vote share percentage.

Visual style matches the React/D3 VoteCountHistogram.tsx component:
  - X-axis: Candidate Vote Share (%)  Y-axis: Number of Precincts
  - Overlapping semi-transparent bars (red for candidate A, blue for B)
  - Overlap region rendered in muted mauve (#B1768C)
  - Optional best-fit curves (Gaussian KDE) overlaid as smooth lines
  - Skew values displayed in the legend
  - Legend at top with square colour swatches
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import PercentFormatter
import numpy as np

import utils
import parameters

# Optional – scipy is used for KDE curves and skew calculation
try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ── React-matching colours ──────────────────────────────────────────────
COLOR_A = "#B22222"          # candidate A bars (firebrick red)
COLOR_B = "#6495ED"          # candidate B bars (cornflower blue)
COLOR_OVERLAP = "#B1768C"    # mauve overlap
COLOR_CURVE_A = "#990000"    # darker red for best-fit curve
COLOR_CURVE_B = "#003399"    # darker blue for best-fit curve
BAR_ALPHA = 0.50
BAR_EDGE = "#000000"


# ── Pearson skew ────────────────────────────────────────────────────────
def _pearson_skew(values: np.ndarray) -> float:
    """Pearson skew = 3(mean − median) / σ  on raw vote-share values."""
    if len(values) < 3:
        return 0.0
    mean = values.mean()
    median = float(np.median(np.sort(values)))
    std = values.std()
    if std == 0:
        return 0.0
    return float(3 * (mean - median) / std)


# ── adaptive bin count (mirrors React logic) ────────────────────────────
def _adaptive_bin_pct(n: int) -> float:
    """Return bin-size percentage matching the React desktop logic."""
    if n < 30:
        return 8
    elif n < 100:
        return 6
    elif n < 300:
        return 4
    elif n < 1000:
        return 2.5
    elif n < 3000:
        return 1.5
    else:
        return 1


# ── main chart ──────────────────────────────────────────────────────────
def create_vote_share_histogram(df,
                                 candidate_a_column,
                                 candidate_b_column,
                                 total_column,
                                 title,
                                 show_curves: bool = True):

    share_a = df[f"{candidate_a_column}_share"].values.astype(float)
    share_b = df[f"{candidate_b_column}_share"].values.astype(float)

    # ── adaptive bin sizing ─────────────────────────────────────────────
    n = len(share_a)
    bin_pct = _adaptive_bin_pct(n)
    n_bins = max(10, min(100, int(np.ceil(100 / bin_pct))))

    # Fixed 0-100% range to match React dashboard
    min_share = 0.0
    max_share = 1.0
    bin_edges = np.linspace(min_share, max_share, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bar_width = bin_edges[1] - bin_edges[0]

    # Count precincts in each bin
    hist_a = np.histogram(share_a, bins=bin_edges)[0].astype(float)
    hist_b = np.histogram(share_b, bins=bin_edges)[0].astype(float)

    # ── skew values ─────────────────────────────────────────────────────
    skew_a = _pearson_skew(share_a)
    skew_b = _pearson_skew(share_b)

    # ── figure ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="white")
    ax.set_facecolor("white")

    # Draw bars with explicit overlap region (same approach as turnout_histogram)
    overlap = np.minimum(hist_a, hist_b)

    # Candidate B bars (blue) — drawn first (behind)
    ax.bar(bin_centers, hist_b, width=bar_width * 0.98,
           color=COLOR_B, alpha=BAR_ALPHA, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=1)

    # Candidate A bars (red)
    ax.bar(bin_centers, hist_a, width=bar_width * 0.98,
           color=COLOR_A, alpha=BAR_ALPHA, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=2)

    # Explicit overlap region (mauve) drawn on top for clarity
    ax.bar(bin_centers, overlap, width=bar_width * 0.98,
           color=COLOR_OVERLAP, alpha=0.7, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=3)

    # ── best-fit curves (Gaussian KDE on vote share) ────────────────────
    if show_curves and HAS_SCIPY:
        xs = np.linspace(min_share, max_share, 300)

        for shares, hist, color in [
            (share_a, hist_a, COLOR_CURVE_A),
            (share_b, hist_b, COLOR_CURVE_B),
        ]:
            if len(shares) < 5:
                continue
            try:
                kde = sp_stats.gaussian_kde(shares, bw_method="scott")
                density = kde(xs)
                max_bar = hist.max()
                if density.max() > 0:
                    scaled = density / density.max() * max_bar
                    ax.plot(xs, scaled, color=color, linewidth=3.5, zorder=5)
            except Exception:
                pass

    elif show_curves and not HAS_SCIPY:
        xs = np.linspace(min_share, max_share, 300)
        for shares, hist, color in [
            (share_a, hist_a, COLOR_CURVE_A),
            (share_b, hist_b, COLOR_CURVE_B),
        ]:
            if len(shares) < 5:
                continue
            mu, sigma = shares.mean(), shares.std()
            if sigma == 0:
                continue
            gauss = np.exp(-0.5 * ((xs - mu) / sigma) ** 2)
            max_bar = hist.max()
            if gauss.max() > 0:
                ax.plot(xs, gauss / gauss.max() * max_bar,
                        color=color, linewidth=3.5, zorder=5)

    # ── axes ────────────────────────────────────────────────────────────
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Candidate Vote Share (%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Precincts", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    ax.tick_params(labelsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Light grid (matches React dashed grid)
    ax.grid(axis="both", linestyle="--", linewidth=0.5, alpha=0.4)

    # ── legend ──────────────────────────────────────────────────────────
    swatch_a = mpatches.Patch(facecolor=COLOR_A, edgecolor="#333", alpha=0.8,
                              label=f"{candidate_a_column}  (Skew = {skew_a:.3f})")
    swatch_b = mpatches.Patch(facecolor=COLOR_B, edgecolor="#333", alpha=0.8,
                              label=f"{candidate_b_column}  (Skew = {skew_b:.3f})")
    swatch_o = mpatches.Patch(facecolor=COLOR_OVERLAP, edgecolor="#333",
                              alpha=0.8, label="Overlap")

    handles = [swatch_a, swatch_b, swatch_o]
    if show_curves:
        curve_handle = plt.Line2D([], [], color="#333", linewidth=3,
                                  label="Best-Fit Curves")
        handles.append(curve_handle)

    ax.legend(handles=handles,
              loc="upper center", bbox_to_anchor=(0.5, 1.0),
              ncol=len(handles), frameon=False, fontsize=10,
              handlelength=1.5, handleheight=1.2)

    fig.tight_layout()
    return fig


# ── entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params,
                                       chart_key="vote_share_histogram")
    if not race:
        print("No selection made; exiting.")
        raise SystemExit(0)
    election_key, race_key, race_cfg = race
    print(f"\nUsing: {election_key} / {race_key}\n")

    df = utils.load_data_frame(race_cfg["file"])
    clean_df = utils.get_voter_stats(
        df,
        race_cfg["registration_column"],
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
    )

    fig = create_vote_share_histogram(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
        race_cfg["vote_share_histogram"]["title"],
        show_curves=True,
    )

    out_dir = utils.ensure_output_dir()
    out_path = out_dir / f"{election_key}_{race_key}_vote_share_histogram.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved → {out_path}")
