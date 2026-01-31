"""
Turnout Heatmap: 2-D kernel density of precincts in
  (voter turnout %) × (candidate vote share %) space.

Visual style matches the React/D3 DensityHeatmapByTurnout.tsx component:
  - X-axis: Voter Turnout (%)   Y-axis: Candidate Vote Share (%)
  - 2-D Gaussian KDE rendered as filled contours (discrete bands)
  - Colormap: matplotlib 'turbo' (matches d3.interpolateTurbo)
  - Candidate-A density shown by default; candidate-B available
  - Legend on the right with square swatches
  - Dark-blue (#000091) background inside the chart area
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.ticker import PercentFormatter
import numpy as np

import utils
import parameters

try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


# ── main chart ──────────────────────────────────────────────────────────
def create_turnout_heatmap(df,
                            candidate_a_column,
                            candidate_b_column,
                            total_column,
                            title,
                            grid_size: int = 200,
                            bandwidth=None):
    """
    Parameters
    ----------
    grid_size : int
        Resolution of the KDE evaluation grid (grid_size × grid_size).
    bandwidth : float or None
        KDE bandwidth (Scott's rule if None).
    """
    if not HAS_SCIPY:
        raise ImportError(
            "scipy is required for the turnout heatmap.  "
            "Install it with:  pip install scipy"
        )

    turnout = df["turnout_percent"].values.astype(float)
    share_a = df[f"{candidate_a_column}_share"].values.astype(float)
    share_b = df[f"{candidate_b_column}_share"].values.astype(float)

    # ── figure ──────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 9), facecolor="white")

    # Dark-blue background inside the chart area (matches React #000091)
    ax.set_facecolor("#000091")

    # ── 2-D KDE for candidate A ────────────────────────────────────────
    xy_a = np.vstack([turnout, share_a])
    bw = bandwidth or "scott"
    kde_a = sp_stats.gaussian_kde(xy_a, bw_method=bw)

    # Evaluation grid (0–1 on both axes)
    xgrid = np.linspace(0, 1, grid_size)
    ygrid = np.linspace(0, 1, grid_size)
    X, Y = np.meshgrid(xgrid, ygrid)
    positions = np.vstack([X.ravel(), Y.ravel()])
    Z_a = kde_a(positions).reshape(grid_size, grid_size)

    # ── filled contours (discrete bands matching React d3.contourDensity) ──
    n_levels = 20   # React default: densityResolution = 20
    levels = np.linspace(Z_a.min(), Z_a.max(), n_levels + 1)
    cf = ax.contourf(
        X, Y, Z_a,
        levels=levels,
        cmap="turbo",       # matches d3.interpolateTurbo
        alpha=0.8,          # matches React opacity: 0.8
        zorder=1,
    )

    # ── axes ────────────────────────────────────────────────────────────
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel("Voter Turnout (%)", fontsize=14, fontweight="bold")
    ax.set_ylabel("Candidate Vote Share (%)", fontsize=14, fontweight="bold")
    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)

    ax.tick_params(labelsize=12, colors="#333")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # ── legend (square swatches at right) ───────────────────────────────
    swatch_a = mpatches.Patch(facecolor="#e63946", edgecolor="#333",
                              label=candidate_a_column)
    swatch_b = mpatches.Patch(facecolor="#888888", edgecolor="#333",
                              label=candidate_b_column)
    ax.legend(handles=[swatch_a, swatch_b],
              loc="upper right", frameon=True, fontsize=11,
              facecolor="white", edgecolor="#ccc",
              handlelength=1.5, handleheight=1.2)

    # ── colorbar ────────────────────────────────────────────────────────
    cbar = fig.colorbar(cf, ax=ax, shrink=0.65, pad=0.02)
    cbar.set_label("Precinct Density", fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    fig.tight_layout()
    return fig


# ── entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params,
                                       chart_key="turnout_heatmap")
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

    fig = create_turnout_heatmap(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        race_cfg["total_column"],
        race_cfg["turnout_heatmap"]["title"],
    )

    out_dir = utils.ensure_output_dir()
    out_path = out_dir / f"{election_key}_{race_key}_turnout_heatmap.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved → {out_path}")
