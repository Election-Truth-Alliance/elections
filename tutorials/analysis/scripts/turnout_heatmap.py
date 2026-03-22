import numpy as np
import utils
import parameters
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.patches import Patch
from scipy.ndimage import gaussian_filter


def create_turnout_heatmap(df,
                            candidate_a_column,
                            candidate_b_column,
                            title,
                            x_axis_label,
                            y_axis_label,
                            candidate_a_color,
                            candidate_b_color,
                            bins=80,
                            candidate="a",
                            density_resolution=20,
                            bandwidth=20):

    turnout = df['turnout_percent'].values

    if candidate == "a":
        vote_share = df[f'{candidate_a_column}_share'].values
        active_color = '#e63946'
        inactive_color = '#cccccc'
    else:
        vote_share = df[f'{candidate_b_column}_share'].values
        active_color = '#4287f5'
        inactive_color = '#cccccc'

    # Build 2D histogram on a fine grid, then smooth with Gaussian filter.
    # This replicates D3's contourDensity() which uses Gaussian KDE.
    # bandwidth controls the Gaussian sigma on the internal grid
    # (default 20 on a 500-cell grid ≈ D3 bandwidth=6 on a ~150px chart).
    grid_size = 500
    hist, _, _ = np.histogram2d(turnout, vote_share,
                                bins=grid_size,
                                range=[[0, 1], [0, 1]])

    # Transpose so rows=y, cols=x for correct orientation with contourf
    smoothed = gaussian_filter(hist.T, sigma=bandwidth)

    fig, ax = plt.subplots(figsize=(10, 10))

    # Dark blue background matching DensityHeatmapByTurnout.tsx (#000091)
    ax.set_facecolor('#000091')

    # Filled contours with turbo colormap (matches d3.interpolateTurbo)
    xi = np.linspace(0, 1, grid_size)
    yi = np.linspace(0, 1, grid_size)
    ax.contourf(xi, yi, smoothed, levels=density_resolution,
                cmap='turbo', alpha=0.8)

    # Axes formatting
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel(x_axis_label, fontsize=16, fontweight='bold')
    ax.set_ylabel(y_axis_label, fontsize=16, fontweight='bold')
    ax.set_title(title)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect('equal')

    # Legend showing both candidates with active/inactive state
    if candidate == "a":
        legend_handles = [
            Patch(facecolor=active_color, edgecolor='black', linewidth=1.5,
                  label=candidate_a_column),
            Patch(facecolor=inactive_color, edgecolor=inactive_color, linewidth=0.5,
                  label=candidate_b_column),
        ]
    else:
        legend_handles = [
            Patch(facecolor=inactive_color, edgecolor=inactive_color, linewidth=0.5,
                  label=candidate_a_column),
            Patch(facecolor=active_color, edgecolor='black', linewidth=1.5,
                  label=candidate_b_column),
        ]
    ax.legend(handles=legend_handles, loc='upper right', fontsize=11)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params, chart_key="turnout_heatmap")
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
        min_registered_voters=race_cfg.get("min_registered_voters", 0)
    )

    chart_cfg = race_cfg["turnout_heatmap"]

    create_turnout_heatmap(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        chart_cfg["title"],
        chart_cfg["x_axis_label"],
        chart_cfg["y_axis_label"],
        race_cfg["candidate_a_color"],
        race_cfg["candidate_b_color"],
        bins=chart_cfg.get("bins", 80),
        candidate=chart_cfg.get("candidate", "a"),
        density_resolution=chart_cfg.get("density_resolution", 20),
        bandwidth=chart_cfg.get("bandwidth", 20))
