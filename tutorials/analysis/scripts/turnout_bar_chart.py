import math
import numpy as np
import utils
import parameters
import matplotlib
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def create_turnout_bar_chart(df,
                              candidate_a_column,
                              candidate_b_column,
                              title,
                              x_axis_label,
                              y_axis_label,
                              candidate_a_color,
                              candidate_b_color,
                              bin_size=1):

    a_share_col = f'{candidate_a_column}_share'
    b_share_col = f'{candidate_b_column}_share'
    turnout = df['turnout_percent'].values

    # Calculate increment percentage (matches TypeScript: Math.max(0.01, binSize / 100))
    increment_pct = max(0.01, bin_size / 100)

    # Create turnout ranges
    num_ranges = math.ceil(1 / increment_pct)
    ranges = []
    for i in range(num_ranges):
        r_min = i * increment_pct
        r_max = min((i + 1) * increment_pct, 1)
        label = f"{round(r_min * 100)}%"
        ranges.append((r_min, r_max, label))

    # Calculate average support by turnout range
    range_data = []
    for r_min, r_max, label in ranges:
        mask = (turnout >= r_min) & (turnout < r_max)
        precincts = df[mask]
        count = len(precincts)
        if count == 0:
            continue
        avg_a = precincts[a_share_col].mean()
        avg_b = precincts[b_share_col].mean()
        range_data.append({
            'label': label,
            'min': r_min,
            'max': r_max,
            'avg_a': avg_a,
            'avg_b': avg_b,
            'count': count,
        })

    if not range_data:
        print("No data to plot.")
        return

    labels = [d['label'] for d in range_data]
    avg_a_vals = np.array([d['avg_a'] for d in range_data])
    avg_b_vals = np.array([d['avg_b'] for d in range_data])

    n = len(labels)
    x = np.arange(n)

    # Match TypeScript d3.scaleBand padding(0.1) for outer, padding(0.02) for inner
    # scaleBand with padding=0.1 means 10% of the step is padding on each side
    # The bar group takes 90% of a step, and each candidate bar takes ~49% of the group
    group_width = 0.9          # 1 - 2*0.05 outer padding per band
    bar_width = group_width / 2 * 0.98   # 2% inner padding between the two bars

    fig, ax = plt.subplots(figsize=(14, 7))

    # Candidate B bars (blue) - drawn first, on the left within each group
    # (matches TypeScript groupScale domain: [candidateB, candidateA])
    b_offset = (group_width / 2 - bar_width) / 2   # center the pair
    ax.bar(x - group_width / 4, avg_b_vals, bar_width,
           color='#4287f5', alpha=0.65,
           edgecolor='#cccccc', linewidth=0.5,
           label=candidate_b_column)

    # Candidate A bars (red) - drawn second, on the right
    ax.bar(x + group_width / 4, avg_a_vals, bar_width,
           color='#e63946', alpha=0.65,
           edgecolor='#cccccc', linewidth=0.5,
           label=candidate_a_column)

    # 50% reference line (matches TypeScript: stroke=#888, dashed 3,3)
    ax.axhline(y=0.5, color='#888888', linestyle='--', linewidth=1, zorder=3)
    ax.text(-0.8, 0.5, '50%', va='center', ha='right', fontsize=10, color='#888888')

    # X-axis: set ticks at every position but only show every 10th label
    # (matches TypeScript: tickFormat shows every 10th on desktop)
    ax.set_xticks(x)
    tick_labels = []
    for i, lbl in enumerate(labels):
        if i % 10 == 0:
            tick_labels.append(lbl)
        else:
            tick_labels.append('')
    ax.set_xticklabels(tick_labels, rotation=-45, ha='left', fontsize=10)

    # Y-axis formatting: 0-100%
    ax.set_ylim(0, 1)
    ax.yaxis.set_major_formatter(PercentFormatter(1))

    # Labels and title
    ax.set_xlabel(x_axis_label, fontsize=16, fontweight='bold')
    ax.set_ylabel(y_axis_label, fontsize=16, fontweight='bold')
    ax.set_title(title)

    # Grid lines (matches TypeScript: stroke-opacity 0.1)
    ax.yaxis.grid(True, alpha=0.1)
    ax.set_axisbelow(True)

    ax.legend(loc='upper right')

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params, chart_key="turnout_bar_chart")
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

    chart_cfg = race_cfg["turnout_bar_chart"]

    create_turnout_bar_chart(
        clean_df,
        race_cfg["candidate_a_column"],
        race_cfg["candidate_b_column"],
        chart_cfg["title"],
        chart_cfg["x_axis_label"],
        chart_cfg["y_axis_label"],
        race_cfg["candidate_a_color"],
        race_cfg["candidate_b_color"],
        bin_size=chart_cfg.get("bin_size", 1))
