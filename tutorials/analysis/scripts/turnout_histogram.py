"""
Turnout Histogram: vote distribution by voter turnout percentage.

Visual style matches the React/D3 TurnoutHistogram.tsx component:
  - Overlapping semi-transparent histograms (red for candidate A, blue for B)
  - Overlap region rendered in muted mauve (#B1768C)
  - Optional best-fit curves (Gaussian KDE) overlaid as smooth lines
  - Skew values displayed in the legend
  - X-axis: Voter Turnout (%)   Y-axis: Number of Votes
  - Legend at top with square colour swatches
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import PercentFormatter, FuncFormatter
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
COLOR_A = "#B22222"          # candidate A bars (red / firebrick)
COLOR_B = "#6495ED"          # candidate B bars (cornflower blue)
COLOR_OVERLAP = "#B1768C"    # mauve overlap
COLOR_CURVE_A = "#990000"    # darker red for best-fit curve
COLOR_CURVE_B = "#003399"    # darker blue for best-fit curve
BAR_ALPHA = 0.50
BAR_EDGE = "#000000"


# ── Pearson skew (matches React implementation) ────────────────────────
def _pearson_skew(turnout: np.ndarray, votes: np.ndarray) -> float:
    """Weighted Pearson skew = 3(mean − median) / σ."""
    if len(turnout) < 3 or votes.sum() == 0:
        return 0.0
    # weight by log-scale of votes to avoid enormous arrays
    weights = np.maximum(1, np.round(np.log10(np.maximum(votes, 1)) * 2)).astype(int)
    expanded = np.repeat(turnout, weights)
    if len(expanded) < 3:
        return 0.0
    mean = expanded.mean()
    median = np.median(np.sort(expanded))
    std = expanded.std()
    if std == 0:
        return 0.0
    return float(3 * (mean - median) / std)


# ── histogram binning (per-candidate vote counts per turnout bin) ──────
def _bin_votes(turnout: np.ndarray, votes: np.ndarray,
               bin_edges: np.ndarray) -> np.ndarray:
    """Sum *votes* that fall into each turnout bin."""
    counts = np.zeros(len(bin_edges) - 1)
    for i in range(len(bin_edges) - 1):
        mask = (turnout >= bin_edges[i]) & (turnout < bin_edges[i + 1])
        counts[i] = votes[mask].sum()
    return counts


# ── main chart ──────────────────────────────────────────────────────────
def create_turnout_histogram(df,
                              candidate_a_column,
                              candidate_b_column,
                              total_column,
                              title,
                              show_curves: bool = True):

    turnout = df["turnout_percent"].values.astype(float)
    votes_a = df[candidate_a_column].values.astype(float)
    votes_b = df[candidate_b_column].values.astype(float)

    # ── adaptive bin sizing (mirrors React logic) ───────────────────────
    n = len(turnout)
    if n < 30:
        bin_pct = 16
    elif n < 100:
        bin_pct = 12
    elif n < 300:
        bin_pct = 8
    elif n < 1000:
        bin_pct = 5
    elif n < 3000:
        bin_pct = 3
    else:
        bin_pct = 2

    min_t = max(0, turnout.min() - 0.02)
    max_t = min(1, turnout.max() + 0.02)
    n_bins = max(10, min(100, int(np.ceil(100 / bin_pct))))
    bin_edges = np.linspace(min_t, max_t, n_bins + 1)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    bar_width = bin_edges[1] - bin_edges[0]

    hist_a = _bin_votes(turnout, votes_a, bin_edges)
    hist_b = _bin_votes(turnout, votes_b, bin_edges)

    # ── skew values ─────────────────────────────────────────────────────
    skew_a = _pearson_skew(turnout, votes_a)
    skew_b = _pearson_skew(turnout, votes_b)

    # ── figure ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="white")
    ax.set_facecolor("white")

    # Overlap region (drawn first, behind individual bars)
    overlap = np.minimum(hist_a, hist_b)
    ax.bar(bin_centers, overlap, width=bar_width * 0.98,
           color=COLOR_OVERLAP, alpha=0.7, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=2, label="_overlap")

    # Candidate B bars (blue)
    ax.bar(bin_centers, hist_b, width=bar_width * 0.98,
           color=COLOR_B, alpha=BAR_ALPHA, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=1)

    # Candidate A bars (red) — drawn on top so overlap shows through
    ax.bar(bin_centers, hist_a, width=bar_width * 0.98,
           color=COLOR_A, alpha=BAR_ALPHA, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=1)

    # Re-draw overlap on top so the mauve is clearly visible
    ax.bar(bin_centers, overlap, width=bar_width * 0.98,
           color=COLOR_OVERLAP, alpha=0.7, edgecolor=BAR_EDGE,
           linewidth=0.8, zorder=3)

    # ── best-fit curves (Gaussian KDE) ──────────────────────────────────
    if show_curves and HAS_SCIPY:
        xs = np.linspace(min_t, max_t, 300)

        # Create weighted samples for KDE
        for votes, color, label in [(votes_a, COLOR_CURVE_A, candidate_a_column),
                                     (votes_b, COLOR_CURVE_B, candidate_b_column)]:
            # Expand turnout values by vote weight (capped for performance)
            weights = np.maximum(1, np.round(votes / max(1, votes.mean()) * 10)).astype(int)
            weights = np.minimum(weights, 200)   # cap per-precinct expansion
            expanded = np.repeat(turnout, weights)
            if len(expanded) < 5:
                continue

            try:
                kde = sp_stats.gaussian_kde(expanded, bw_method="scott")
                density = kde(xs)
                # Scale density so the curve peak aligns with the bar peak
                max_bar = hist_a.max() if color == COLOR_CURVE_A else hist_b.max()
                if density.max() > 0:
                    scaled = density / density.max() * max_bar
                    ax.plot(xs, scaled, color=color, linewidth=3.5, zorder=5)
            except Exception:
                pass   # gracefully skip if KDE fails

    elif show_curves and not HAS_SCIPY:
        # Fallback: simple Gaussian fit using numpy only
        for votes, color in [(votes_a, COLOR_CURVE_A), (votes_b, COLOR_CURVE_B)]:
            weights = np.maximum(1, np.round(votes / max(1, votes.mean()) * 10)).astype(int)
            weights = np.minimum(weights, 200)
            expanded = np.repeat(turnout, weights)
            if len(expanded) < 5:
                continue
            mu, sigma = expanded.mean(), expanded.std()
            if sigma == 0:
                continue
            xs = np.linspace(min_t, max_t, 300)
            gauss = np.exp(-0.5 * ((xs - mu) / sigma) ** 2)
            max_bar = hist_a.max() if color == COLOR_CURVE_A else hist_b.max()
            if gauss.max() > 0:
                ax.plot(xs, gauss / gauss.max() * max_bar,
                        color=color, linewidth=3.5, zorder=5)

    # ── axes (add 10% headroom so KDE curves aren't clipped) ───────────
    y_max = max(hist_a.max(), hist_b.max())
    # Check if KDE curves extend higher
    for child in ax.get_children():
        if hasattr(child, 'get_ydata'):
            try:
                ydata = child.get_ydata()
                if len(ydata) > 0:
                    y_max = max(y_max, np.nanmax(ydata))
            except Exception:
                pass
    ax.set_ylim(0, y_max * 1.12)

    ax.set_xlim(min_t, max_t)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v):,}"))
    ax.set_xlabel("Voter Turnout (%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Number of Votes", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    ax.tick_params(labelsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Light grid (matches React dashed grid)
    ax.grid(axis="both", linestyle="--", linewidth=0.5, alpha=0.4)

    # ── legend ──────────────────────────────────────────────────────────
    swatch_a = mpatches.Patch(facecolor=COLOR_A, edgecolor="#333", alpha=0.8,
                              label=f"{candidate_a_column} Votes  (Skew = {skew_a:.3f})")
    swatch_b = mpatches.Patch(facecolor=COLOR_B, edgecolor="#333", alpha=0.8,
                              label=f"{candidate_b_column} Votes  (Skew = {skew_b:.3f})")
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
                                       chart_key="turnout_histogram")
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

    fig = create_turnout_histogram(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
        race_cfg["turnout_histogram"]["title"],
        show_curves=True,
    )

    out_dir = utils.ensure_output_dir()
    out_path = out_dir / f"{election_key}_{race_key}_turnout_histogram.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved → {out_path}")
