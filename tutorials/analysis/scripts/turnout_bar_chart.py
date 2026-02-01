"""
Turnout Bar Chart: average candidate vote share by turnout-percentage bins.

Visual style matches the React/D3 BarChart.tsx component:
  - X-axis: Voter Turnout (%)   Y-axis: Candidate Vote Share (%)  0-100 %
  - Grouped side-by-side bars: blue (#4287f5) for candidate B,
    red (#e63946) for candidate A
  - 50 % dashed reference line
  - Optional smoothed trend lines (dark blue / dark red)
  - Legend at top with square swatches
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import PercentFormatter
import numpy as np

import utils
import parameters


# ── React-matching colours ──────────────────────────────────────────────
COLOR_A = "#e63946"          # candidate A bars (red)
COLOR_B = "#4287f5"          # candidate B bars (blue)
COLOR_TREND_A = "#9f1239"    # darker red for trend line
COLOR_TREND_B = "#1e40af"    # darker blue for trend line
BAR_ALPHA = 0.85


# ── adaptive bin sizing (mirrors React desktop logic) ───────────────────
def _adaptive_bin_pct(n: int) -> float:
    """Return turnout bin size (percentage points) matching React."""
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


# ── running average (matches React windowSize=5) ───────────────────────
def _running_average(values: np.ndarray, window: int = 5) -> np.ndarray:
    """Centered running average over *window* elements."""
    out = np.empty_like(values)
    half = window // 2
    for i in range(len(values)):
        lo = max(0, i - half)
        hi = min(len(values), i + half + 1)
        out[i] = values[lo:hi].mean()
    return out


# ── main chart ──────────────────────────────────────────────────────────
def create_turnout_bar_chart(df,
                              candidate_a_column,
                              candidate_b_column,
                              total_column,
                              title,
                              show_trend: bool = True,
                              bin_pct_override: float = None,
                              min_precincts: int = 3):

    turnout = df["turnout_percent"].values.astype(float)
    share_a = df[f"{candidate_a_column}_share"].values.astype(float)
    share_b = df[f"{candidate_b_column}_share"].values.astype(float)

    # ── bin precincts by turnout ────────────────────────────────────────
    n = len(turnout)
    bin_pct = bin_pct_override if bin_pct_override is not None else _adaptive_bin_pct(n)
    increment = bin_pct / 100.0
    n_bins = int(np.ceil(1.0 / increment))

    # Collect all bins that have data (skip empty bins, matching React
    # ``rangesWithData.filter(d => d.count > 0)`` behaviour)
    bin_labels = []
    avg_a = []
    avg_b = []
    counts = []

    for i in range(n_bins):
        lo = i * increment
        hi = min((i + 1) * increment, 1.0)
        mask = (turnout >= lo) & (turnout < hi)
        cnt = mask.sum()
        if cnt == 0:
            continue
        bin_labels.append(f"{int(round(lo * 100))}%")
        avg_a.append(float(share_a[mask].mean()))
        avg_b.append(float(share_b[mask].mean()))
        counts.append(cnt)

    avg_a = np.array(avg_a)
    avg_b = np.array(avg_b)
    x_pos = np.arange(len(bin_labels))
    bar_width = 0.38

    # ── figure ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(14, 7), facecolor="white")
    ax.set_facecolor("white")

    # Grouped bars
    ax.bar(x_pos - bar_width / 2, avg_b, width=bar_width,
           color=COLOR_B, alpha=BAR_ALPHA, edgecolor="#333",
           linewidth=0.8, zorder=2, label=candidate_b_column)

    ax.bar(x_pos + bar_width / 2, avg_a, width=bar_width,
           color=COLOR_A, alpha=BAR_ALPHA, edgecolor="#333",
           linewidth=0.8, zorder=2, label=candidate_a_column)

    # ── 50 % dashed reference line ──────────────────────────────────────
    ax.axhline(y=0.5, color="#888", linewidth=1, linestyle="--", zorder=1)
    ax.text(-0.6, 0.5, "50%", va="center", ha="right",
            fontsize=10, color="#888")

    # ── trend lines ─────────────────────────────────────────────────────
    if show_trend and len(avg_a) >= 3:
        smooth_a = _running_average(avg_a, window=5)
        smooth_b = _running_average(avg_b, window=5)
        ax.plot(x_pos, smooth_b, color=COLOR_TREND_B, linewidth=3.5,
                marker="o", markersize=4, zorder=4)
        ax.plot(x_pos, smooth_a, color=COLOR_TREND_A, linewidth=3.5,
                marker="o", markersize=4, zorder=4)

    # ── axes ────────────────────────────────────────────────────────────
    ax.set_xticks(x_pos)
    # Auto-thin labels when there are many bins
    if len(bin_labels) > 20:
        step = max(1, len(bin_labels) // 20)
        visible_labels = [l if i % step == 0 else "" for i, l in enumerate(bin_labels)]
        ax.set_xticklabels(visible_labels, rotation=-45, ha="left", fontsize=9)
    else:
        ax.set_xticklabels(bin_labels, rotation=-45, ha="left", fontsize=9)
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Voter Turnout (%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Candidate Vote Share (%)", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    ax.tick_params(labelsize=12)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Subtle grid
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.3)

    # ── legend ──────────────────────────────────────────────────────────
    swatch_b = mpatches.Patch(facecolor=COLOR_B, edgecolor="#333",
                              label=candidate_b_column)
    swatch_a = mpatches.Patch(facecolor=COLOR_A, edgecolor="#333",
                              label=candidate_a_column)
    handles = [swatch_b, swatch_a]

    if show_trend and len(avg_a) >= 3:
        trend_handle = plt.Line2D([], [], color="#555", linewidth=3,
                                  marker="o", markersize=4,
                                  label="Trend Lines")
        handles.append(trend_handle)

    ax.legend(handles=handles,
              loc="upper center", bbox_to_anchor=(0.5, 1.0),
              ncol=len(handles), frameon=False, fontsize=11,
              handlelength=1.5, handleheight=1.2)

    fig.tight_layout()
    return fig


# ── entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params,
                                       chart_key="turnout_bar_chart")
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

    chart_cfg = race_cfg["turnout_bar_chart"]
    fig = create_turnout_bar_chart(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
        chart_cfg["title"],
        show_trend=True,
        bin_pct_override=chart_cfg.get("bin_pct", None),
        min_precincts=chart_cfg.get("min_precincts", 3),
    )

    out_dir = utils.ensure_output_dir()
    out_path = out_dir / f"{election_key}_{race_key}_turnout_bar_chart.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved → {out_path}")
