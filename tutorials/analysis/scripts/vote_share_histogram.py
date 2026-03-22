import math
import numpy as np
import utils
import parameters
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def create_vote_share_histogram(df,
                                 candidate_a_column,
                                 candidate_b_column,
                                 title,
                                 x_axis_label,
                                 y_axis_label,
                                 candidate_a_color,
                                 candidate_b_color,
                                 bin_size=2.5,
                                 show_curves=True):

    a_share_col = f'{candidate_a_column}_share'
    # Match TypeScript: candidate B share = 1 - candidate A share
    candidate_a_shares = df[a_share_col].values
    candidate_b_shares = 1.0 - candidate_a_shares

    # Determine bin range with buffer, clamped to [0, 1]
    all_shares = np.concatenate([candidate_a_shares, candidate_b_shares])
    min_share = max(0, all_shares.min() - 0.02)
    max_share = min(1, all_shares.max() + 0.02)

    # Calculate bins
    bin_count = math.ceil(100 / bin_size)
    full_range = max_share - min_share
    actual_bin_size = full_range / bin_count

    bin_edges = [min_share + i * actual_bin_size for i in range(bin_count + 1)]

    # Build histogram data for candidate A
    counts_a = []
    for i in range(bin_count):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        count = np.sum((candidate_a_shares >= bin_start) & (candidate_a_shares < bin_end))
        counts_a.append(count)

    # Build histogram data for candidate B
    counts_b = []
    for i in range(bin_count):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        count = np.sum((candidate_b_shares >= bin_start) & (candidate_b_shares < bin_end))
        counts_b.append(count)

    counts_a = np.array(counts_a)
    counts_b = np.array(counts_b)

    # Y-axis max with 10% padding
    y_max = max(counts_a.max(), counts_b.max()) * 1.1

    fig, ax = plt.subplots(figsize=(12, 7))

    # Bar width in data coordinates
    bar_width = actual_bin_size

    # Draw candidate B bars first (blue, behind)
    bin_starts = [bin_edges[i] for i in range(bin_count)]
    ax.bar(bin_starts, counts_b, width=bar_width, align='edge',
           color='#4682B4', alpha=0.5, edgecolor='black', linewidth=1.5,
           label=candidate_b_column)

    # Draw candidate A bars (red, on top)
    ax.bar(bin_starts, counts_a, width=bar_width, align='edge',
           color='#B22222', alpha=0.5, edgecolor='black', linewidth=1.5,
           label=candidate_a_column)

    # Normal distribution curves
    if show_curves:
        x_curve = np.linspace(0, 1, 101)

        # Candidate A curve
        mean_a, std_a = _calc_stats(candidate_a_shares)
        if std_a > 0:
            peak_a = 1 / (std_a * math.sqrt(2 * math.pi))
            scale_a = counts_a.max() / peak_a
            y_curve_a = [scale_a * (1 / (std_a * math.sqrt(2 * math.pi))) *
                         math.exp(-0.5 * ((x - mean_a) / std_a) ** 2) for x in x_curve]
            ax.plot(x_curve, y_curve_a, color='#990000', linewidth=3.5,
                    label=f'{candidate_a_column} Best Fit')

        # Candidate B curve
        mean_b, std_b = _calc_stats(candidate_b_shares)
        if std_b > 0:
            peak_b = 1 / (std_b * math.sqrt(2 * math.pi))
            scale_b = counts_b.max() / peak_b
            y_curve_b = [scale_b * (1 / (std_b * math.sqrt(2 * math.pi))) *
                         math.exp(-0.5 * ((x - mean_b) / std_b) ** 2) for x in x_curve]
            ax.plot(x_curve, y_curve_b, color='#003399', linewidth=3.5,
                    label=f'{candidate_b_column} Best Fit')

    # Axes formatting
    ax.set_xlim(0, 1)
    ax.set_ylim(0, y_max)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    ax.set_xlabel(x_axis_label, fontsize=16, fontweight='bold')
    ax.set_ylabel(y_axis_label, fontsize=14, fontweight='bold')
    ax.set_title(title)

    # Grid lines (dashed)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Compute and display skewness in legend
    skew_a = _pearson_skew(candidate_a_shares)
    skew_b = _pearson_skew(candidate_b_shares)

    handles, labels = ax.get_legend_handles_labels()
    extra_text = f'{candidate_a_column} Skew = {skew_a:.3f}\n{candidate_b_column} Skew = {skew_b:.3f}'
    ax.annotate(extra_text, xy=(0.02, 0.98), xycoords='axes fraction',
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.5))

    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


def _calc_stats(values):
    """Calculate mean and std dev from an array of values."""
    mean = np.mean(values)
    std = np.std(values)
    return mean, std


def _pearson_skew(values):
    """Calculate Pearson's skewness coefficient: 3(mean - median) / stdDev."""
    if len(values) < 3:
        return 0.0
    mean = np.mean(values)
    median = np.median(values)
    std = np.std(values)
    if std == 0:
        return 0.0
    return 3 * (mean - median) / std


if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params, chart_key="vote_share_histogram")
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
        race_cfg["total_column"]
    )

    chart_cfg = race_cfg["vote_share_histogram"]

    create_vote_share_histogram(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        chart_cfg["title"],
        chart_cfg["x_axis_label"],
        chart_cfg["y_axis_label"],
        race_cfg["candidate_a_color"],
        race_cfg["candidate_b_color"],
        bin_size=chart_cfg.get("bin_size", 2.5),
        show_curves=False)
