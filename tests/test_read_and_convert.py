"""Unit tests for the transformation functions of read_and_convert."""

import shutil
from pathlib import Path

import pandas as pd

from pokerdf.core.read_and_convert import (
    DataProcessing,
    _save_log,
    apply_regex,
    compose_dataframe,
    convert_txt_to_tabular_data,
    execute_in_parallel,
    get_files_paths,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250516 T99999 No Limit Hold_em US$ 1,84 + US$ 0,16.txt"
)

EXPECTED_COLUMNS = [
    "Modality",
    "TableSize",
    "BuyIn",
    "TournID",
    "TableID",
    "HandID",
    "HandStartTimeCET",
    "HandStartTimeLocal",
    "HandTimezone",
    "Level",
    "Ante",
    "Blinds",
    "Owner",
    "OwnersHand",
    "Playing",
    "Player",
    "Seat",
    "PostedAnte",
    "Position",
    "PostedBlind",
    "Stack",
    "Bounty",
    "PreflopAction",
    "FlopAction",
    "TurnAction",
    "RiverAction",
    "AnteAllIn",
    "PreflopAllIn",
    "FlopAllIn",
    "TurnAllIn",
    "RiverAllIn",
    "BoardFlop",
    "BoardTurn",
    "BoardRiver",
    "ShowDown",
    "CardCombination",
    "Result",
    "Balance",
    "UncalledReturned",
    "BountyWon",
    "TotalPotLog",
    "Rake",
    "PotBreakdown",
    "FinalRank",
    "Prize",
]


# ---------------------------------------------------------------------------
# get_files_paths
# ---------------------------------------------------------------------------
def test_get_files_paths_keeps_only_hand_history_files(tmp_path: Path) -> None:
    # Relevant files: start with "HH" and end with ".txt"
    (tmp_path / "HH20200607 T111.txt").touch()
    (tmp_path / "HH20200608 T222.txt").touch()
    # Irrelevant files: wrong prefix or wrong extension
    (tmp_path / "notes.txt").touch()
    (tmp_path / "HH20200609 T333.log").touch()

    result = get_files_paths(str(tmp_path))

    assert result == [
        str(tmp_path / "HH20200607 T111.txt"),
        str(tmp_path / "HH20200608 T222.txt"),
    ]


def test_get_files_paths_returns_sorted_paths(tmp_path: Path) -> None:
    (tmp_path / "HH20200608 T222.txt").touch()
    (tmp_path / "HH20200607 T111.txt").touch()

    result = get_files_paths(str(tmp_path))

    assert result == sorted(result)


def test_get_files_paths_returns_empty_list_for_empty_directory(
    tmp_path: Path,
) -> None:
    assert get_files_paths(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# compose_dataframe
# ---------------------------------------------------------------------------
def test_compose_dataframe_is_empty() -> None:
    df = compose_dataframe()
    assert len(df) == 0


def test_compose_dataframe_has_expected_columns_in_order() -> None:
    df = compose_dataframe()
    assert list(df.columns) == EXPECTED_COLUMNS


def test_compose_dataframe_has_expected_dtypes() -> None:
    df = compose_dataframe()
    assert df["TableSize"].dtype == "int64"
    assert df["HandStartTimeCET"].dtype == "datetime64[ns]"
    assert df["Ante"].dtype == "float64"
    assert df["AnteAllIn"].dtype == "bool"
    assert df["Modality"].dtype == "object"


# ---------------------------------------------------------------------------
# apply_regex
# ---------------------------------------------------------------------------
def test_apply_regex_returns_one_row_per_player_per_hand(
    tournament_text: str,
) -> None:
    df = apply_regex(tournament_text)
    # 3-max tournament: hands have at most 3 players, at least 2 (heads-up)
    number_of_hands = tournament_text.count("PokerStars Hand #")
    assert df["HandID"].nunique() == number_of_hands
    rows_per_hand = df.groupby("HandID").size()
    assert rows_per_hand.between(2, 3).all()


def test_apply_regex_keeps_the_output_schema(tournament_text: str) -> None:
    df = apply_regex(tournament_text)
    assert list(df.columns) == EXPECTED_COLUMNS


def test_apply_regex_deduplicates_repeated_hands(tournament_text: str) -> None:
    # Client reconnections can write the same hand more than once in the
    # file: only the first occurrence must be converted
    first_hand = "PokerStars " + tournament_text.split("PokerStars ")[1]
    df = apply_regex(tournament_text + "\n\n" + first_hand)
    assert not df.duplicated(subset=["HandID", "Player"]).any()
    assert df["HandID"].nunique() == tournament_text.count("PokerStars Hand #")


def test_apply_regex_captures_tournament_wide_values(tournament_text: str) -> None:
    df = apply_regex(tournament_text)
    assert set(df["TournID"]) == {"99999"}
    assert set(df["Owner"]) == {"garciamurilo"}
    assert set(df["Modality"]) == {"USD Hold'em No Limit"}


def test_apply_regex_captures_bounties(ko_tournament_text: str) -> None:
    df = apply_regex(ko_tournament_text)
    hand = df[df["HandID"] == "22221"].set_index("Player")
    # Every player has a bounty on their head in a knockout tournament
    assert hand["Bounty"].tolist() == [0.5, 0.5, 0.5]
    # garciamurilo eliminated VillainA and won the cash part of the bounty
    assert hand.loc["garciamurilo", "BountyWon"] == 0.25
    assert pd.isna(hand.loc["VillainB", "BountyWon"])


def test_apply_regex_captures_single_card_shows(ko_tournament_text: str) -> None:
    df = apply_regex(ko_tournament_text)
    hand = df[df["HandID"] == "22219"].set_index("Player")
    assert hand.loc["VillainB", "ShowDown"] == ("Qs", None)


def test_apply_regex_captures_the_pot_decomposition(ko_tournament_text: str) -> None:
    df = apply_regex(ko_tournament_text)
    hand = df[df["HandID"] == "22220"]
    # Main and side pots are decomposed, and the breakdown sums to the total
    assert hand["PotBreakdown"].iloc[0] == (300.0, 400.0)
    assert hand["TotalPotLog"].iloc[0] == 700.0


def test_apply_regex_captures_satellite_finishes(
    satellite_tournament_text: str,
) -> None:
    df = apply_regex(satellite_tournament_text)
    final = df[df["HandID"] == "33333"].set_index("Player")
    assert final.loc["garciamurilo", "FinalRank"] == 1
    # The ticket face value is the prize
    assert final.loc["garciamurilo", "Prize"] == 1.0
    assert final.loc["VillainB", "FinalRank"] == 2
    # VillainC finished without a reported place
    assert final.loc["VillainC", "FinalRank"] == 0
    # Elimination with no SHOW DOWN section (all-in blind post, all fold)
    no_showdown = df[df["HandID"] == "33332"].set_index("Player")
    assert no_showdown.loc["VillainF", "FinalRank"] == 4


# ---------------------------------------------------------------------------
# convert_txt_to_tabular_data
# ---------------------------------------------------------------------------
def test_convert_txt_to_tabular_data_matches_expected_parquet() -> None:
    df_converted = convert_txt_to_tabular_data(str(FIXTURE_PATH)).reset_index(drop=True)
    df_expected = pd.read_parquet(
        Path(__file__).parent / "output" / "20250516-T99999.parquet"
    )
    pd.testing.assert_frame_equal(
        df_converted, df_expected, check_like=True, check_column_type=True
    )


# ---------------------------------------------------------------------------
# _save_log
# ---------------------------------------------------------------------------
def test_save_log_creates_file_and_appends_messages(tmp_path: Path) -> None:
    _save_log("first message", str(tmp_path), "success.txt")
    _save_log("second message", str(tmp_path), "success.txt")

    content = (tmp_path / "success.txt").read_text()

    assert content == "first message\nsecond message\n"


# ---------------------------------------------------------------------------
# DataProcessing
# ---------------------------------------------------------------------------
def test_data_processing_run_saves_parquet_and_logs_success(
    tmp_path: Path,
) -> None:
    source = tmp_path / FIXTURE_PATH.name
    shutil.copy(FIXTURE_PATH, source)
    destination = tmp_path / "output"
    destination.mkdir()

    DataProcessing(str(source), str(destination)).run()

    # File name comes from the first hand's date and the tournament ID
    parquet_path = destination / "20201011-T99999.parquet"
    assert parquet_path.exists()
    df = pd.read_parquet(parquet_path)
    assert len(df) > 0
    success_log = (destination / "success.txt").read_text()
    assert "DONE" in success_log
    assert FIXTURE_PATH.name in success_log


def test_data_processing_run_logs_failure_without_raising(tmp_path: Path) -> None:
    destination = tmp_path / "output"
    destination.mkdir()

    DataProcessing(str(tmp_path / "HHmissing.txt"), str(destination)).run()

    fail_log = (destination / "fail.txt").read_text()
    assert "FAIL" in fail_log
    assert "HHmissing.txt" in fail_log
    assert list(destination.glob("*.parquet")) == []


def test_data_processing_run_refuses_to_overwrite_an_existing_output(
    tmp_path: Path,
) -> None:
    # Two inputs of the same tournament map to the same output name: the
    # second conversion must fail loudly instead of silently overwriting
    source_a = tmp_path / "HH20250516 T99999 original.txt"
    source_b = tmp_path / "HH20250516 T99999 copy.txt"
    shutil.copy(FIXTURE_PATH, source_a)
    shutil.copy(FIXTURE_PATH, source_b)
    destination = tmp_path / "output"
    destination.mkdir()

    DataProcessing(str(source_a), str(destination)).run()
    DataProcessing(str(source_b), str(destination)).run()

    assert "HH20250516 T99999 original.txt" in (destination / "success.txt").read_text()
    fail_log = (destination / "fail.txt").read_text()
    assert "HH20250516 T99999 copy.txt" in fail_log
    assert "refusing to overwrite" in fail_log
    # The parquet from the first conversion is intact
    assert len(pd.read_parquet(destination / "20201011-T99999.parquet")) > 0


# ---------------------------------------------------------------------------
# execute_in_parallel
# ---------------------------------------------------------------------------
def test_execute_in_parallel_processes_all_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    shutil.copy(FIXTURE_PATH, source / FIXTURE_PATH.name)
    destination = tmp_path / "output"
    destination.mkdir()

    execute_in_parallel(source=str(source), destination=str(destination))

    assert (destination / "20201011-T99999.parquet").exists()
    assert (destination / "success.txt").exists()
