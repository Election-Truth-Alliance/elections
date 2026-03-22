import math
import numpy as np
import utils
import parameters
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter, FuncFormatter


def create_turnout_histogram(df,
                              candidate_a_column,
                              candidate_b_column,
                              title,
                              x_axis_label,
                              y_axis_label,
                              candidate_a_color,
                              candidate_b_color,
                              bin_size=5,
                              show_curves=False):

    turnout = df['turnout_percent'].values

    # Determine turnout range with buffer, clamped to [0, 1]
    min_turnout = max(0, turnout.min() - 0.02)
    max_turnout = min(1, turnout.max() + 0.02)

    # Calculate bins
    bin_count = math.ceil(100 / bin_size)
    full_range = max_turnout - min_turnout
    actual_bin_size = full_range / bin_count

    bin_edges = [min_turnout + i * actual_bin_size for i in range(bin_count + 1)]

    # Build histogram data - sum of candidate votes per turnout bin (NOT precinct count)
    votes_a = []
    votes_b = []
    for i in range(bin_count):
        bin_start = bin_edges[i]
        bin_end = bin_edges[i + 1]
        mask = (turnout >= bin_start) & (turnout < bin_end)
        precincts = df[mask]
        total_a = precincts[candidate_a_column].sum()
        total_b = precincts[candidate_b_column].sum()
        votes_a.append(total_a)
        votes_b.append(total_b)

    votes_a = np.array(votes_a, dtype=float)
    votes_b = np.array(votes_b, dtype=float)

    # Y-axis max with 10% padding
    y_max = max(votes_a.max(), votes_b.max()) * 1.1

    fig, ax = plt.subplots(figsize=(12, 7))

    # Bar width in data coordinates
    bar_width = actual_bin_size

    # Draw candidate B bars first (blue, behind)
    bin_starts = [bin_edges[i] for i in range(bin_count)]
    ax.bar(bin_starts, votes_b, width=bar_width, align='edge',
           color='#4682B4', alpha=0.5, edgecolor='black', linewidth=1.5,
           label=f'{candidate_b_column} Votes')

    # Draw candidate A bars (red, on top)
    ax.bar(bin_starts, votes_a, width=bar_width, align='edge',
           color='#B22222', alpha=0.5, edgecolor='black', linewidth=1.5,
           label=f'{candidate_a_column} Votes')

    # Normal distribution curves
    if show_curves:
        x_curve = np.linspace(0, 1, 101)

        # Candidate A curve - weighted by votes
        mean_a, std_a = _calc_weighted_stats(bin_edges, votes_a, bin_count, actual_bin_size)
        if std_a > 0:
            peak_a = 1 / (std_a * math.sqrt(2 * math.pi))
            scale_a = votes_a.max() / peak_a
            y_curve_a = [scale_a * (1 / (std_a * math.sqrt(2 * math.pi))) *
                         math.exp(-0.5 * ((x - mean_a) / std_a) ** 2) for x in x_curve]
            ax.plot(x_curve, y_curve_a, color='#990000', linewidth=3.5,
                    label=f'{candidate_a_column} Best Fit')

        # Candidate B curve - weighted by votes
        mean_b, std_b = _calc_weighted_stats(bin_edges, votes_b, bin_count, actual_bin_size)
        if std_b > 0:
            peak_b = 1 / (std_b * math.sqrt(2 * math.pi))
            scale_b = votes_b.max() / peak_b
            y_curve_b = [scale_b * (1 / (std_b * math.sqrt(2 * math.pi))) *
                         math.exp(-0.5 * ((x - mean_b) / std_b) ** 2) for x in x_curve]
            ax.plot(x_curve, y_curve_b, color='#003399', linewidth=3.5,
                    label=f'{candidate_b_column} Best Fit')

    # Axes formatting
    ax.set_xlim(min_turnout, max_turnout)
    ax.set_ylim(0, y_max)
    ax.xaxis.set_major_formatter(PercentFormatter(1))
    # Y-axis: comma-formatted vote counts
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax.set_xlabel(x_axis_label, fontsize=16, fontweight='bold')
    ax.set_ylabel(y_axis_label, fontsize=16, fontweight='bold')
    ax.set_title(title)

    # Grid lines (dashed)
    ax.grid(True, linestyle='--', alpha=0.3)

    # Compute and display weighted skewness
    skew_a = _weighted_pearson_skew(df, candidate_a_column, 'turnout_percent')
    skew_b = _weighted_pearson_skew(df, candidate_b_column, 'turnout_percent')

    extra_text = f'{candidate_a_column} Skew = {skew_a:.3f}\n{candidate_b_column} Skew = {skew_b:.3f}'
    ax.annotate(extra_text, xy=(0.02, 0.98), xycoords='axes fraction',
                verticalalignment='top', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='wheat', alpha=0.5))

    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


def _calc_weighted_stats(bin_edges, vote_counts, bin_count, actual_bin_size):
    """Calculate weighted mean and std dev from histogram bins."""
    total_votes = vote_counts.sum()
    if total_votes == 0:
        return 0, 0

    # Weighted mean using bin centers
    bin_centers = [bin_edges[i] + actual_bin_size / 2 for i in range(bin_count)]
    mean = sum(c * v for c, v in zip(bin_centers, vote_counts)) / total_votes

    # Weighted variance
    variance = sum(((c - mean) ** 2) * v for c, v in zip(bin_centers, vote_counts)) / total_votes
    std = math.sqrt(variance)

    return mean, std


def _weighted_pearson_skew(df, candidate_column, turnout_column):
    """Calculate Pearson's skewness using logarithmic vote weights (matching TypeScript)."""
    votes = df[candidate_column].values
    turnout = df[turnout_column].values

    weighted_turnouts = []
    for v, t in zip(votes, turnout):
        if v > 0:
            weight = max(1, round(math.log10(v) * 2))
            weighted_turnouts.extend([t] * weight)

    if len(weighted_turnouts) < 3:
        return 0.0

    arr = np.array(weighted_turnouts)
    mean = np.mean(arr)
    median = np.median(arr)
    std = np.std(arr)

    if std == 0:
        return 0.0
    return 3 * (mean - median) / std


if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params, chart_key="turnout_histogram")
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

    chart_cfg = race_cfg["turnout_histogram"]

    create_turnout_histogram(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        chart_cfg["title"],
        chart_cfg["x_axis_label"],
        chart_cfg["y_axis_label"],
        race_cfg["candidate_a_color"],
        race_cfg["candidate_b_color"],
        bin_size=chart_cfg.get("bin_size", 5),
        show_curves=False)
