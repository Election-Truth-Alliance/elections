import utils
import matplotlib
import parameters
matplotlib.use("MacOSX")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter


def create_turnout_scatter_plot(df,
                                candidate_a_column,
                                candidate_b_column,
                                title,
                                x_axis_label,
                                y_axis_label,
                                candidate_a_color,
                                candidate_b_color,
                                min_dot_size=4,
                                max_dot_size=40):


    plt.scatter(df['turnout_percent'],
                df[f'{candidate_a_column}_share'],
                alpha=0.3,
                s=utils.get_dot_size(min_dot_size, max_dot_size, df[candidate_a_column]),
                color=candidate_a_color,
                edgecolors=candidate_a_color,
                label=candidate_a_column)

    plt.scatter(df['turnout_percent'],
                df[f'{candidate_b_column}_share'],
                s=utils.get_dot_size(min_dot_size, max_dot_size, df[candidate_b_column]),
                alpha=0.3,
                edgecolors=candidate_b_color,
                color=candidate_b_color,
                label=candidate_b_column)

    plt.gca().xaxis.set_major_formatter(PercentFormatter(1))
    plt.gca().yaxis.set_major_formatter(PercentFormatter(1))

    # add labels and title
    plt.xlabel(x_axis_label)
    plt.ylabel(y_axis_label)
    plt.title(title)

    # show it
    plt.show()


if __name__ == "__main__":
    race = utils.choose_race_for_chart(parameters.params, chart_key="turnout_scatter_plot")
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

    create_turnout_scatter_plot(
        clean_df,
        race_cfg['candidate_a_column'],
        race_cfg['candidate_b_column'],
        race_cfg["turnout_scatter_plot"]['title'],
        race_cfg["turnout_scatter_plot"]['x_axis_label'],
        race_cfg["turnout_scatter_plot"]['y_axis_label'],
        race_cfg['candidate_a_color'],
        race_cfg['candidate_b_color'])
