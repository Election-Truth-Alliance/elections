import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

ERROR_TOKENS = {"", "#DIV/0!", "#N/A", "#VALUE!", "#REF!", "#NUM!", "#NAME?", "#NULL!"}

# Small-precinct filtering (disable by setting to None)
MIN_REGISTERED_VOTERS = 100
MIN_TOTAL_VOTES = 50


def load_data_frame(path):
    """Load a dataframe from Excel or CSV depending on the file suffix."""
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in {".xls", ".xlsx", ".xlsm", ".xlsb"}:
        return pd.read_excel(file_path)
    if suffix == ".csv":
        return pd.read_csv(file_path)

    raise ValueError(f"Unsupported file type for '{file_path}'. Expected Excel or CSV.")


def clean_num(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.replace(",", "", regex=False).str.replace("%", "", regex=False)
    return pd.to_numeric(s, errors="coerce")


def get_dot_size(min_size, max_size, data):
    data = data.to_numpy()
    data_min = data.min()
    data_max = data.max()
    # to avoid division by zero if all equal:
    if data_max > data_min:
        norm = (data - data_min) / (data_max - data_min)
    else:
        norm = np.ones_like(data) * 0.5

    # scale into your size range
    sizes = min_size + norm * (max_size - min_size)
    return sizes


def get_voter_stats(df, registration_column, candidate_a_column, candidate_b_column, total_column):
    # coerce to numeric early
    reg = clean_num(df[registration_column])
    tot = clean_num(df[total_column])
    a = clean_num(df[candidate_a_column])
    b = clean_num(df[candidate_b_column])

    clean = pd.DataFrame({
        registration_column: reg,
        total_column: tot,
        candidate_a_column: a,
        candidate_b_column: b,
    })

    # Preserve precinct column if present
    for col in ("precinct", "Precinct", "PRECINCT"):
        if col in df.columns:
            clean["precinct"] = df[col].values[:len(clean)]
            break

    # drop rows with bad/zero totals or registrations
    clean = clean[(clean[registration_column] > 0) & (clean[total_column] > 0)]

    # The dashboard computes:
    #   turnout_pct     = total_votes / registered_voters
    #   candidate_x_pct = candidate_x_votes / total_votes
    # where total_votes = sum of ALL candidates for that election type.
    #
    # If `total_column` accurately represents the total for the election type
    # being analysed, use it directly.  Otherwise (e.g. PA CSV where
    # total_votes_cast spans ALL voting methods while candidate columns are
    # Election Day only), fall back to (A + B) as the best available proxy.
    two_party = clean[candidate_a_column] + clean[candidate_b_column]
    denom = clean[total_column].copy()

    # Detect mismatch: if total >> A+B in most rows, total likely includes
    # other voting methods → use two-party total instead.
    ratio = (two_party / denom).median()
    if ratio < 0.75:
        # total_column includes votes from other methods/types;
        # fall back to (A + B) for both turnout and share.
        denom = two_party

    denom = denom.replace(0, np.nan)

    clean['turnout_percent'] = denom / reg

    clean[f"{candidate_a_column}_share"] = clean[candidate_a_column] / denom
    clean[f"{candidate_b_column}_share"] = clean[candidate_b_column] / denom

    # remove div-by-zero/NaN
    clean = clean.replace([np.inf, -np.inf], np.nan).dropna(
        subset=[f"{candidate_a_column}_share", f"{candidate_b_column}_share"]
    )
    return clean


def ensure_output_dir():
    """Create the output directory if it doesn't exist."""
    output_dir = Path(__file__).resolve().parent.parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def find_races_with_chart(params: Dict[str, Any], chart_key: str) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Return a list of (election_key, race_key, race_config) where race_config has chart_key.
    """
    out = []
    for election_key, races in params.items():
        if not isinstance(races, dict):
            continue
        for race_key, race_cfg in races.items():
            if isinstance(race_cfg, dict) and chart_key in race_cfg:
                out.append((election_key, race_key, race_cfg))
    return out


def prompt_user_to_choose(races: List[Tuple[str, str, Dict[str, Any]]], chart_key: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
    """
    Interactive prompt to choose a race from the list. Returns the chosen tuple or None.
    """
    if not races:
        print(f"No races found with '{chart_key}' defined.")
        return None

    print(f"\nSelect a race for chart '{chart_key}':\n")
    for i, (election_key, race_key, race_cfg) in enumerate(races, start=1):
        title = race_cfg.get(chart_key, {}).get("title") or f"{election_key} / {race_key}"
        print(f"[{i}] {election_key}  ›  {race_key}  —  {title}")

    while True:
        choice = input("\nEnter number (or press Enter to cancel): ").strip()
        if choice == "":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(races):
                return races[idx - 1]
        print(f"Please enter a number between 1 and {len(races)}.")


def choose_race_for_chart(params: Dict[str, Any], chart_key: str, prefer_election: Optional[str] = None):
    # Optionally filter by a specific election if you want:
    subset = params if not prefer_election else {prefer_election: params.get(prefer_election, {})}
    races = find_races_with_chart(subset, chart_key)
    return prompt_user_to_choose(races, chart_key)
