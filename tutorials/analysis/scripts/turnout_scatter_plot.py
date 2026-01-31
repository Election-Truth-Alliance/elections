"""
Turnout Scatter Plot: Candidate Vote Share (%) vs Voter Turnout (%).

Visual style matches the React/D3 TurnoutScatterPlot.tsx component:
  - Hollow circles (white fill, colored stroke)
  - Stroke colour gradient light→dark based on total votes
  - Dot size scales 0.4× – 2.0× of base radius (3 pt) with total votes
  - Segmented trend lines (5 % turnout segments, min 5 points per segment)
  - Legend at top with square colour swatches
  - Clean white background
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
from matplotlib.ticker import PercentFormatter
import numpy as np

import utils
import parameters


# ── colour / size helpers (shared logic with scatter_plot.py) ───────────
def _lerp_color(c1_hex: str, c2_hex: str, t: float) -> str:
    c1 = np.array(mcolors.hex2color(c1_hex))
    c2 = np.array(mcolors.hex2color(c2_hex))
    return mcolors.rgb2hex(c1 + (c2 - c1) * np.clip(t, 0, 1))


def _build_color_array(total_votes: np.ndarray, light: str, dark: str) -> list:
    mn, mx = total_votes.min(), total_votes.max()
    if mx == mn:
        return [dark] * len(total_votes)
    t = (total_votes - mn) / (mx - mn)
    return [_lerp_color(light, dark, ti) for ti in t]


def _build_sizes(total_votes: np.ndarray, base: float = 3.0) -> np.ndarray:
    mn, mx = total_votes.min(), total_votes.max()
    if mx == mn:
        factor = np.ones_like(total_votes) * 1.2
    else:
        factor = 0.4 + (total_votes - mn) / (mx - mn) * (2.0 - 0.4)
    radii = base * factor
    return np.pi * radii ** 2


# ── segmented trend lines (by 5 % turnout buckets) ─────────────────────
def _segmented_trend_turnout(turnout: np.ndarray, share: np.ndarray,
                              seg_pct: float = 0.05):
    """Return (seg_x, seg_y) averages in 5 % turnout segments."""
    seg_xs, seg_ys = [], []
    lo = 0.0
    while lo < 1.0:
        hi = lo + seg_pct
        mask = (turnout >= lo) & (turnout < hi)
        if mask.sum() >= 5:
            seg_xs.append(float(turnout[mask].mean()))
            seg_ys.append(float(share[mask].mean()))
        lo = hi
    return np.array(seg_xs), np.array(seg_ys)


# ── main chart ──────────────────────────────────────────────────────────
def create_turnout_scatter_plot(df,
                                 candidate_a_column,
                                 candidate_b_column,
                                 total_column,
                                 title,
                                 candidate_a_color_unused,
                                 candidate_b_color_unused):

    turnout = df["turnout_percent"].values.astype(float)
    total   = df[total_column].values.astype(float)
    share_a = df[f'{candidate_a_column}_share'].values.astype(float)
    share_b = df[f'{candidate_b_column}_share'].values.astype(float)

    colors_a = _build_color_array(total, "#ffa6a9", "#63000c")
    colors_b = _build_color_array(total, "#80b3ff", "#002d75")
    sizes    = _build_sizes(total, base=3.0)

    fig, ax = plt.subplots(figsize=(12, 7), facecolor="white")
    ax.set_facecolor("white")

    # Hollow circles
    ax.scatter(turnout, share_b, s=sizes,
               facecolors="white", edgecolors=colors_b, linewidths=1.5,
               zorder=2)
    ax.scatter(turnout, share_a, s=sizes,
               facecolors="white", edgecolors=colors_a, linewidths=1.5,
               zorder=2)

    # Trend lines (5 % turnout segments)
    tx_b, ty_b = _segmented_trend_turnout(turnout, share_b)
    tx_a, ty_a = _segmented_trend_turnout(turnout, share_a)

    if len(tx_b) >= 2:
        ax.plot(tx_b, ty_b, color="#1e40af", linewidth=3, zorder=3)
        ax.plot(tx_b, ty_b, 'o', color="#1e40af", markersize=5, zorder=4)
    if len(tx_a) >= 2:
        ax.plot(tx_a, ty_a, color="#9f1239", linewidth=3, zorder=3)
        ax.plot(tx_a, ty_a, 'o', color="#9f1239", markersize=5, zorder=4)

    # Axes
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Voter Turnout (%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Candidate Vote Share (%)", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    ax.tick_params(labelsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Legend
    swatch_b = mpatches.Patch(facecolor="#4287f5", edgecolor="#333",
                              label=candidate_b_column)
    swatch_a = mpatches.Patch(facecolor="#e63946", edgecolor="#333",
                              label=candidate_a_column)
    trend_b = plt.Line2D([], [], color="#1e40af", linewidth=3,
                         marker='o', markersize=5,
                         label=f"{candidate_b_column} Trend")
    trend_a = plt.Line2D([], [], color="#9f1239", linewidth=3,
                         marker='o', markersize=5,
                         label=f"{candidate_a_column} Trend")
    ax.legend(handles=[swatch_b, swatch_a, trend_b, trend_a],
              loc="upper center", bbox_to_anchor=(0.5, 1.0),
              ncol=4, frameon=False, fontsize=11,
              handlelength=1.5, handleheight=1.2)

    fig.tight_layout()
    return fig


# ── entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params,
                                       chart_key="turnout_scatter_plot")
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

    fig = create_turnout_scatter_plot(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
        race_cfg["turnout_scatter_plot"]["title"],
        race_cfg["candidate_a_color"],
        race_cfg["candidate_b_color"],
    )

    out_dir = utils.ensure_output_dir()
    out_path = out_dir / f"{election_key}_{race_key}_turnout_scatter.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved → {out_path}")
