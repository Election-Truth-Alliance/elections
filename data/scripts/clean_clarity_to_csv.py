 #!/usr/bin/env python3
"""Compile precinct-level vote totals for a contest identified by choice key."""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from xml.etree import ElementTree as ET


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a CSV of precinct results for the contest containing the given choice key."
        )
    )
    parser.add_argument("xml", type=Path, help="Path to the detail XML file")
    parser.add_argument(
        "--choice-key",
        required=False,
        help="Choice key that identifies the contest to export",
    )
    parser.add_argument(
        "--contest-key",
        required=False,
        help="Contest key identifying the contest to export",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output CSV path (defaults to stdout)",
    )
    args = parser.parse_args(argv)
    if not args.choice_key and not args.contest_key:
        parser.error("You must provide --contest-key or --choice-key.")
    return args


def load_precinct_metadata(root: ET.Element) -> tuple[Dict[str, int], Dict[str, int]]:
    """Return registered voters and ballots cast keyed by precinct id."""
    precincts_parent = root.find("./VoterTurnout/Precincts")
    registered: Dict[str, int] = {}
    ballots_cast: Dict[str, int] = {}
    if precincts_parent is None:
        return registered, ballots_cast
    for precinct in precincts_parent.findall("Precinct"):
        name = precinct.get("name")
        if not name:
            continue
        total_voters = precinct.get("totalVoters")
        ballots = precinct.get("ballotsCast")
        try:
            registered[name] = int(total_voters) if total_voters is not None else 0
        except ValueError:
            registered[name] = 0
        try:
            ballots_cast[name] = int(ballots) if ballots is not None else 0
        except ValueError:
            ballots_cast[name] = 0
    return registered, ballots_cast


def find_contest(
    root: ET.Element, choice_key: str | None, contest_key: str | None
) -> ET.Element:
    if contest_key:
        contest = root.find(f"Contest[@key='{contest_key}']")
        if contest is None:
            raise ValueError(f"No contest found with key '{contest_key}'.")
        if choice_key and contest.find(f"Choice[@key='{choice_key}']") is None:
            raise ValueError(
                f"Contest '{contest_key}' does not contain choice key '{choice_key}'."
            )
        return contest

    if not choice_key:
        raise ValueError("You must provide either --contest-key or --choice-key.")

    matches = []
    for contest in root.findall("Contest"):
        if contest.find(f"Choice[@key='{choice_key}']") is not None:
            matches.append(contest)
    if not matches:
        raise ValueError(f"No contest contains a choice with key '{choice_key}'.")
    if len(matches) > 1:
        contest_names = ', '.join(
            sorted({c.get('text') or c.get('key') or 'unknown contest' for c in matches})
        )
        raise ValueError(
            f"Choice key '{choice_key}' found in multiple contests: {contest_names}. Use --contest-key to disambiguate."
        )
    return matches[0]


def collect_vote_types(choices: Iterable[ET.Element]) -> List[str]:
    vote_types: List[str] = []
    seen = set()
    for choice in choices:
        for vote_type in choice.findall("VoteType"):
            name = vote_type.get("name")
            if name and name not in seen:
                seen.add(name)
                vote_types.append(name)
    return vote_types


def build_precinct_rows(
    choices: List[ET.Element],
    registered_lookup: Dict[str, int],
    ballots_cast_lookup: Dict[str, int],
    vote_types: List[str],
) -> Tuple[List[str], List[List[str]]]:
    precinct_data: Dict[str, Dict[str, Dict[str, int]]] = {}
    precinct_order: List[str] = []
    candidate_names = [choice.get("text", f"Choice {choice.get('key', '')}") for choice in choices]

    for choice, candidate_name in zip(choices, candidate_names):
        for vote_type in choice.findall("VoteType"):
            vt_name = vote_type.get("name")
            if vt_name is None:
                continue
            for precinct in vote_type.findall("Precinct"):
                precinct_id = precinct.get("name")
                if precinct_id is None:
                    continue
                try:
                    votes = int(precinct.get("votes", "0"))
                except ValueError:
                    votes = 0

                if precinct_id not in precinct_data:
                    precinct_data[precinct_id] = defaultdict(lambda: defaultdict(int))  # type: ignore[assignment]
                    precinct_order.append(precinct_id)
                precinct_entry = precinct_data[precinct_id]
                precinct_entry[candidate_name][vt_name] += votes

    header = ["precinct_id", "registered_voters", "contest_name", "total_votes_cast"]
    for candidate_name in candidate_names:
        for vt_name in vote_types:
            header.append(f"{candidate_name} - {vt_name}")

    rows: List[List[str]] = []
    for precinct_id in precinct_order:
        precinct_entry = precinct_data[precinct_id]
        registered = registered_lookup.get(precinct_id, "")
        total_votes = ballots_cast_lookup.get(precinct_id, "")

        row: List[str] = [
            precinct_id,
            str(registered),
            "",  # placeholder; actual contest name applied later
            str(total_votes),
        ]

        for candidate_name in candidate_names:
            candidate_votes = precinct_entry.get(candidate_name, {})
            for vt_name in vote_types:
                row.append(str(candidate_votes.get(vt_name, 0)))
        rows.append(row)

    return header, rows


def write_rows(
    header: List[str],
    rows: List[List[str]],
    contest_name: str,
    output_path: Path | None,
) -> None:
    for row in rows:
        row[2] = contest_name

    if output_path is None:
        writer = csv.writer(sys.stdout)
        writer.writerow(header)
        writer.writerows(rows)
        return

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(header)
        writer.writerows(rows)


def main(argv: Iterable[str]) -> int:
    args = parse_args(argv)
    try:
        tree = ET.parse(args.xml)
    except (ET.ParseError, OSError) as exc:
        print(f"Failed to read XML file: {exc}", file=sys.stderr)
        return 1

    root = tree.getroot()
    try:
        contest = find_contest(root, args.choice_key, args.contest_key)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    registered_lookup, ballots_lookup = load_precinct_metadata(root)
    choices = contest.findall("Choice")
    if not choices:
        print("Contest contains no choices.", file=sys.stderr)
        return 3

    vote_types = collect_vote_types(choices)
    if not vote_types:
        print("Contest contains no vote type data.", file=sys.stderr)
        return 4

    header, rows = build_precinct_rows(
        choices, registered_lookup, ballots_lookup, vote_types
    )
    write_rows(header, rows, contest.get("text", ""), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
