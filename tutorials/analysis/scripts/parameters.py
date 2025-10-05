default_candidate_a_color = "#e63946"
default_candidate_b_color = "#4287f5"

params = {
    "2024_general_north_carolina_wake": {
        "president": {
            "file": "../files/2024_G_NC_President.xlsx",
            "candidate_a_column": "Trump",
            "candidate_b_column": "Harris",
            "total_column": "total_votes",
            "registration_column": "registered_voters",
            "candidate_a_color": default_candidate_a_color,
            "candidate_b_color": default_candidate_b_color,
            "scatter_plot": {
                "title": "North Carolina - Wake - 2024 - Presidential - Election Day Votes\nCandidate Vote Share by Precinct Vote Total",
                "x_axis_label": "Total Votes",
                "y_axis_label": "Candidate Vote Share (%)",
            },
            "turnout_scatter_plot": {
                "title": "North Carolina - Wake - 2024 - Presidential - Election Day Votes\nCandidate Vote Share by Turnout Percentage",
                "x_axis_label": "Voter Turnout Percentage",
                "y_axis_label": "Candidate Vote Share (%)",
            }
        },
        "attorney_general": {
            "file": "../files/2024_G_NC_Attorney_General.xlsx",
            "candidate_a_column": "Bishop",
            "candidate_b_column": "Jackson",
            "total_column": "Total Votes",
            "registration_column": "Registered",
            "candidate_a_color": default_candidate_a_color,
            "candidate_b_color": default_candidate_b_color,
            "scatter_plot": {
                "title": "North Carolina - Wake - 2024 - Attorney General - Election Day Votes\nCandidate Vote Share by Precinct Vote Total",
                "x_axis_label": "Total Votes",
                "y_axis_label": "Candidate Vote Share (%)",
            },
            "turnout_scatter_plot": {
                "title": "North Carolina - Wake - 2024 - Attorney General - Election Day Votes\nCandidate Vote Share by Turnout Percentage",
                "x_axis_label": "Voter Turnout Percentage",
                "y_axis_label": "Candidate Vote Share (%)",
            }
        }
    }
}
