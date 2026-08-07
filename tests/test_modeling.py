"""Unit tests for the star schema modeling functions.

The input of the modeling functions is produced by converting the real hand
history fixture and saving it as .parquet, exactly like the convert command
does, so the whole pipeline convert -> parquet -> star schema is exercised.
"""

from pathlib import Path

import pandas as pd
import pytest

from pokerdf.core.read_and_convert import convert_txt_to_tabular_data
from pokerdf.modeling.star_schema import (
    _roman_to_int,
    build_dim_final_rank,
    build_dim_hand_summary,
    build_dim_player_summary,
    build_dim_tourn_summary,
    build_fact_player_actions,
    build_star_schema,
    load_converted_data,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250516 T99999 No Limit Hold_em US$ 1,84 + US$ 0,16.txt"
)


@pytest.fixture(scope="module")
def converted_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Directory with the fixture converted to .parquet, like convert does."""
    df = convert_txt_to_tabular_data(str(FIXTURE_PATH)).reset_index(drop=True)
    folder = tmp_path_factory.mktemp("converted")
    df.to_parquet(folder / "20201011-T99999.parquet", index=False)
    return folder


@pytest.fixture(scope="module")
def source_df(converted_dir: Path) -> pd.DataFrame:
    return load_converted_data(str(converted_dir))


@pytest.fixture(scope="module")
def fact(source_df: pd.DataFrame) -> pd.DataFrame:
    return build_fact_player_actions(source_df)


# ---------------------------------------------------------------------------
# _roman_to_int
# ---------------------------------------------------------------------------
def test_roman_to_int_converts_roman_numerals() -> None:
    assert _roman_to_int("I") == 1
    assert _roman_to_int("IV") == 4
    assert _roman_to_int("IX") == 9
    assert _roman_to_int("XIV") == 14
    assert _roman_to_int("XXIX") == 29
    assert _roman_to_int("XL") == 40


def test_roman_to_int_accepts_numeric_strings() -> None:
    assert _roman_to_int("5") == 5


def test_roman_to_int_returns_none_for_invalid_values() -> None:
    assert _roman_to_int(None) is None
    assert _roman_to_int("??") is None


# ---------------------------------------------------------------------------
# load_converted_data
# ---------------------------------------------------------------------------
def test_load_converted_data_loads_all_rows(
    converted_dir: Path, source_df: pd.DataFrame
) -> None:
    df_expected = pd.read_parquet(converted_dir / "20201011-T99999.parquet")
    assert len(source_df) == len(df_expected)


def test_load_converted_data_casts_prize_to_float(source_df: pd.DataFrame) -> None:
    # Prize is captured as text by the converter; the unified schema loads it
    # as float64 so all files can be concatenated
    assert source_df["Prize"].dtype == "float64"
    assert source_df["Prize"].max() == 6.0


# ---------------------------------------------------------------------------
# fact_player_actions
# ---------------------------------------------------------------------------
def test_fact_has_expected_structure(fact: pd.DataFrame) -> None:
    assert list(fact.columns) == [
        "TournID",
        "HandID",
        "TableSize",
        "Playing",
        "Level",
        "Ante",
        "SmallBlind",
        "BigBlind",
        "Round",
        "Player",
        "Seat",
        "Position",
        "Stack",
        "PostedAnte",
        "PostedBlind",
        "Action",
        "ActionIndex",
        "ActionOrder",
        "AddedValue",
        "TotalValue",
        "TotalPot",
        "BoardC1",
        "BoardC2",
        "BoardC3",
        "BoardC4",
        "BoardC5",
        "OwnerC1",
        "OwnerC2",
    ]
    assert set(fact["Round"]) <= {"preflop", "flop", "turn", "river"}
    assert fact["TournID"].dtype == "int64"
    assert fact["HandID"].dtype == "int64"


def test_fact_each_row_is_one_event(fact: pd.DataFrame) -> None:
    # The grain is one event (post or action): ActionOrder identifies it, and
    # there can be no placeholder rows of rounds in which the player did not act
    assert not fact.duplicated(subset=["TournID", "HandID", "ActionOrder"]).any()
    voluntary = fact[fact["ActionIndex"] > 0]
    keys = ["TournID", "HandID", "Player", "Round", "ActionIndex"]
    assert not voluntary.duplicated(subset=keys).any()
    assert (fact["Action"] != "").all()
    assert fact["Action"].notna().all()


def test_fact_explodes_single_action(fact: pd.DataFrame) -> None:
    # Hand 11111: garciamurilo posts the small blind and then only folds
    rows = fact[(fact["HandID"] == 11111) & (fact["Player"] == "garciamurilo")]
    assert rows[["Round", "ActionIndex", "Action", "AddedValue"]].values.tolist() == [
        ["preflop", 0, "posts small blind", 10.0],
        ["preflop", 1, "folds", 0.0],
    ]


def test_fact_carries_hand_context(fact: pd.DataFrame) -> None:
    # Hand 11111: 3-max at level I (blinds 10/20), 3 players, no ante,
    # with the owner holding 3s Jh
    row = fact[fact["HandID"] == 11111].iloc[0]
    assert row["TableSize"] == 3
    assert row["Level"] == 1
    assert row["Playing"] == 3
    assert pd.isna(row["Ante"])
    assert row["SmallBlind"] == 10.0
    assert row["BigBlind"] == 20.0
    assert row["OwnerC1"] == "3s"
    assert row["OwnerC2"] == "Jh"


def test_fact_carries_seat_and_position(fact: pd.DataFrame) -> None:
    # Hand 11111: garciamurilo was the small blind on seat 2
    row = fact[(fact["HandID"] == 11111) & (fact["Player"] == "garciamurilo")].iloc[0]
    assert row["Seat"] == 2
    assert row["Position"] == "small blind"
    # VillainA was the button on seat 1
    row = fact[(fact["HandID"] == 11111) & (fact["Player"] == "VillainA")].iloc[0]
    assert row["Seat"] == 1
    assert row["Position"] == "button"


def test_fact_materializes_the_posts_as_rows(fact: pd.DataFrame) -> None:
    # Hand 11111: the posts open the hand, small blind first, with the real
    # amounts that left each stack — and the big blind that won the walk
    # without acting still gets his post row
    rows = fact[fact["HandID"] == 11111]
    assert rows[["ActionOrder", "Player", "Action", "AddedValue"]].values.tolist()[
        :2
    ] == [
        [1, "garciamurilo", "posts small blind", 10.0],
        [2, "VillainB", "posts big blind", 20.0],
    ]
    walk_winner = rows[rows["Player"] == "VillainB"]
    assert walk_winner["Action"].tolist() == ["posts big blind"]
    assert walk_winner.iloc[0]["TotalPot"] == 30.0


def test_fact_carries_the_posted_amounts_on_every_row(fact: pd.DataFrame) -> None:
    # Hand 11111: every row of garciamurilo shows his posted small blind,
    # even after the post row itself
    rows = fact[(fact["HandID"] == 11111) & (fact["Player"] == "garciamurilo")]
    assert (rows["PostedBlind"] == 10.0).all()
    assert rows["PostedAnte"].isna().all()


def test_fact_stack_is_dynamic(fact: pd.DataFrame) -> None:
    # Hand 219269903263: garciamurilo starts with 710 and the stack follows
    # every chip that leaves it: small blind, call, call and flop bet
    rows = fact[(fact["HandID"] == 219269903263) & (fact["Player"] == "garciamurilo")]
    assert rows[["Action", "Stack"]].values.tolist() == [
        ["posts small blind", 695.0],
        ["calls", 680.0],
        ["calls", 620.0],
        ["bets", 404.0],
    ]


def test_fact_stack_reaches_zero_on_all_in(fact: pd.DataFrame) -> None:
    # Hand 219269977250: garciamurilo posts the big blind 60, calls 120 and
    # goes all-in betting the remaining 653 on the flop
    rows = fact[(fact["HandID"] == 219269977250) & (fact["Player"] == "garciamurilo")]
    assert rows[rows["Action"] == "bets"].iloc[0]["Stack"] == 0.0


def test_fact_orders_preflop_from_the_seat_after_the_big_blind(
    fact: pd.DataFrame,
) -> None:
    # Hand 11111: after the posts, VillainB (seat 3) is the big blind, so
    # VillainA (seat 1) acts first and garciamurilo (seat 2) is next
    rows = fact[fact["HandID"] == 11111]
    assert rows[["ActionOrder", "Player", "Action"]].values.tolist() == [
        [1, "garciamurilo", "posts small blind"],
        [2, "VillainB", "posts big blind"],
        [3, "VillainA", "folds"],
        [4, "garciamurilo", "folds"],
    ]


def test_fact_orders_postflop_from_the_seat_after_the_button(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269857629 flop: VillainA (small blind) bets, garciamurilo
    # (big blind) raises, and VillainA folds, exactly as in the log
    rows = fact[(fact["HandID"] == 219269857629) & (fact["Round"] == "flop")]
    assert rows[["Player", "Action", "ActionIndex"]].values.tolist() == [
        ["VillainA", "bets", 1],
        ["garciamurilo", "raises", 1],
        ["VillainA", "folds", 2],
    ]


def test_fact_orders_heads_up_preflop_from_the_small_blind(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269883094 (heads-up): VillainB is button and small blind — he
    # posts first and acts first preflop
    rows = fact[(fact["HandID"] == 219269883094) & (fact["Round"] == "preflop")]
    assert rows[["Player", "Action"]].values.tolist() == [
        ["VillainB", "posts small blind"],
        ["garciamurilo", "posts big blind"],
        ["VillainB", "raises"],
        ["garciamurilo", "folds"],
    ]


def test_fact_action_order_is_a_sequence_inside_each_hand(
    fact: pd.DataFrame,
) -> None:
    sequences = fact.groupby(["TournID", "HandID"])["ActionOrder"]
    assert (sequences.min() == 1).all()
    assert (sequences.max() == sequences.count()).all()


def test_fact_explodes_multiple_actions_in_the_same_round(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269903263: garciamurilo calls 15, VillainB raises, and then
    # garciamurilo calls 60 more, all during preflop
    rows = fact[
        (fact["HandID"] == 219269903263)
        & (fact["Player"] == "garciamurilo")
        & (fact["Round"] == "preflop")
    ]
    assert rows[["ActionIndex", "Action", "AddedValue"]].values.tolist() == [
        [0, "posts small blind", 15.0],
        [1, "calls", 15.0],
        [2, "calls", 60.0],
    ]


def test_fact_preserves_actions_across_rounds(fact: pd.DataFrame) -> None:
    # Hand 219269866589: garciamurilo calls preflop and checks on the flop,
    # the turn and the river, all the way to the showdown
    rows = fact[(fact["HandID"] == 219269866589) & (fact["Player"] == "garciamurilo")]
    assert rows[["Round", "Action"]].values.tolist() == [
        ["preflop", "posts small blind"],
        ["preflop", "calls"],
        ["flop", "checks"],
        ["turn", "checks"],
        ["river", "checks"],
    ]


def test_fact_added_value_of_calls_is_the_amount_captured(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269903263 preflop (blinds 15/30): garciamurilo posts the small
    # blind 15, calls 15 more (total 30), VillainB raises to 90, and
    # garciamurilo calls 60 more (total 90)
    rows = fact[
        (fact["HandID"] == 219269903263)
        & (fact["Player"] == "garciamurilo")
        & (fact["Round"] == "preflop")
    ]
    assert rows[["Action", "AddedValue", "TotalValue"]].values.tolist() == [
        ["posts small blind", 15.0, 15.0],
        ["calls", 15.0, 30.0],
        ["calls", 60.0, 90.0],
    ]


def test_fact_total_pot_accumulates_the_whole_hand(fact: pd.DataFrame) -> None:
    # Hand 219269903263 (blinds 15/30, no ante): the pot starts at 45 with
    # the blinds, and grows with every action across the rounds
    rows = fact[fact["HandID"] == 219269903263]
    assert rows[["Round", "Player", "Action", "TotalPot"]].values.tolist() == [
        ["preflop", "garciamurilo", "posts small blind", 15.0],
        ["preflop", "VillainB", "posts big blind", 45.0],
        ["preflop", "garciamurilo", "calls", 60.0],
        ["preflop", "VillainB", "raises", 120.0],
        ["preflop", "garciamurilo", "calls", 180.0],
        ["flop", "VillainB", "checks", 180.0],
        ["flop", "garciamurilo", "bets", 396.0],
        ["flop", "VillainB", "folds", 396.0],
    ]


def test_fact_added_value_of_raises_accounts_for_committed_chips(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269854149 preflop (blinds 10/20): VillainA posted the small
    # blind 10 and "raises 40 to 60": the log captures the increase over the
    # big blind (40), but the player pushed 50 chips to reach 60
    row = fact[
        (fact["HandID"] == 219269854149)
        & (fact["Player"] == "VillainA")
        & (fact["Action"] == "raises")
    ].iloc[0]
    assert row["AddedValue"] == 50.0
    assert row["TotalValue"] == 60.0


def test_fact_added_value_of_reraises(fact: pd.DataFrame) -> None:
    # Hand 219269903263 preflop (blinds 15/30): VillainB posted the big blind
    # 30 and "raises 60 to 90" over garciamurilo's call: pushed 60 to reach 90
    row = fact[
        (fact["HandID"] == 219269903263)
        & (fact["Player"] == "VillainB")
        & (fact["Action"] == "raises")
    ].iloc[0]
    assert row["AddedValue"] == 60.0
    assert row["TotalValue"] == 90.0


def test_fact_big_blind_check_keeps_the_blind_committed(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269857629 preflop (blinds 10/20): garciamurilo is the big blind
    # and checks, adding nothing but keeping the 20 already committed
    row = fact[
        (fact["HandID"] == 219269857629)
        & (fact["Player"] == "garciamurilo")
        & (fact["Action"] == "checks")
    ].iloc[0]
    assert row["AddedValue"] == 0.0
    assert row["TotalValue"] == 20.0


def test_fact_bets_open_the_round_level(fact: pd.DataFrame) -> None:
    # Hand 219269851097 flop: VillainB bets 80 with nothing committed yet
    row = fact[
        (fact["HandID"] == 219269851097)
        & (fact["Player"] == "VillainB")
        & (fact["Round"] == "flop")
    ].iloc[0]
    assert row["Action"] == "bets"
    assert row["AddedValue"] == 80.0
    assert row["TotalValue"] == 80.0


def test_fact_amounts_are_consistent(fact: pd.DataFrame) -> None:
    # The chips pushed by an action can never be negative, the round total
    # can never be smaller than the pushed amount, and passive actions
    # (checks and folds) never push chips
    active = fact[
        fact["Action"].isin(
            [
                "bets",
                "raises",
                "calls",
                "posts ante",
                "posts small blind",
                "posts big blind",
            ]
        )
    ]
    passive = fact[fact["Action"].isin(["checks", "folds"])]
    assert (active["AddedValue"] >= 0).all()
    assert (active["TotalValue"] >= active["AddedValue"]).all()
    assert (passive["AddedValue"] == 0).all()


BOARD_COLUMNS = ["BoardC1", "BoardC2", "BoardC3", "BoardC4", "BoardC5"]


def test_fact_board_is_empty_on_preflop_actions(fact: pd.DataFrame) -> None:
    # Before the flop there are no community cards on the table
    preflop = fact[fact["Round"] == "preflop"]
    assert preflop[BOARD_COLUMNS].isna().all().all()


def test_fact_board_shows_three_cards_on_flop_actions(fact: pd.DataFrame) -> None:
    # Hand 219269851097: VillainB bets the flop with board [4d Tc 7s]
    row = fact[
        (fact["HandID"] == 219269851097)
        & (fact["Player"] == "VillainB")
        & (fact["Round"] == "flop")
    ].iloc[0]
    assert row[BOARD_COLUMNS].tolist() == ["4d", "Tc", "7s", None, None]


def test_fact_board_shows_four_cards_on_turn_actions(fact: pd.DataFrame) -> None:
    # Hand 219269893866: garciamurilo folds on the turn with board [2s Qh 8s 5h]
    row = fact[
        (fact["HandID"] == 219269893866)
        & (fact["Player"] == "garciamurilo")
        & (fact["Round"] == "turn")
    ].iloc[0]
    assert row[BOARD_COLUMNS].tolist() == ["2s", "Qh", "8s", "5h", None]


def test_fact_board_shows_five_cards_on_river_actions(fact: pd.DataFrame) -> None:
    # Hand 219269911437: garciamurilo checks the river with board [Ts 6s Jd 6h 9h]
    row = fact[
        (fact["HandID"] == 219269911437)
        & (fact["Player"] == "garciamurilo")
        & (fact["Round"] == "river")
    ].iloc[0]
    assert row[BOARD_COLUMNS].tolist() == ["Ts", "6s", "Jd", "6h", "9h"]


# ---------------------------------------------------------------------------
# dim_tourn_summary
# ---------------------------------------------------------------------------
def test_dim_tourn_summary(source_df: pd.DataFrame) -> None:
    dim = build_dim_tourn_summary(source_df)
    assert len(dim) == 1
    row = dim.iloc[0]
    assert row["TournID"] == 99999
    assert row["LocalStartTime"] == pd.Timestamp("2020-10-11 03:22:15")
    assert row["Modality"] == "USD Hold'em No Limit"
    assert row["BuyIn"] == "$1.84+$0.16"
    assert row["Owner"] == "garciamurilo"
    # TableSize belongs to the fact table now
    assert "TableSize" not in dim.columns


# ---------------------------------------------------------------------------
# dim_hand_summary
# ---------------------------------------------------------------------------
def test_dim_hand_summary_has_one_row_per_hand(
    source_df: pd.DataFrame, tournament_text: str
) -> None:
    dim = build_dim_hand_summary(source_df)
    assert len(dim) == tournament_text.count("PokerStars Hand #")
    assert not dim.duplicated(subset=["TournID", "HandID"]).any()


def test_dim_hand_summary_carries_only_hand_identity_and_time(
    source_df: pd.DataFrame,
) -> None:
    dim = build_dim_hand_summary(source_df)
    assert list(dim.columns) == ["TournID", "HandID", "LocalTime"]
    row = dim[dim["HandID"] == 219269866589].iloc[0]
    assert row["LocalTime"] == pd.Timestamp("2020-10-11 03:23:44")


# ---------------------------------------------------------------------------
# dim_player_summary
# ---------------------------------------------------------------------------
def test_dim_player_summary_has_one_row_per_player_per_hand(
    source_df: pd.DataFrame,
) -> None:
    dim = build_dim_player_summary(source_df)
    assert len(dim) == len(source_df)
    assert not dim.duplicated(subset=["TournID", "HandID", "Player"]).any()


def test_dim_player_summary_values(source_df: pd.DataFrame) -> None:
    dim = build_dim_player_summary(source_df)
    row = dim[(dim["HandID"] == 11111) & (dim["Player"] == "garciamurilo")].iloc[0]
    assert row["Result"] == "folded"
    # Seat, Position, the dynamic Stack and the posts live in the fact table
    for column in ["Seat", "Position", "Stack", "PostedAnte", "PostedBlind"]:
        assert column not in dim.columns


def test_dim_player_summary_flattens_showdown_cards(
    source_df: pd.DataFrame,
) -> None:
    dim = build_dim_player_summary(source_df)
    row = dim[(dim["HandID"] == 219269866589) & (dim["Player"] == "garciamurilo")].iloc[
        0
    ]
    assert row["Balance"] == 40.0
    assert row["ShowDownC1"] == "8h"
    assert row["ShowDownC2"] == "Kh"
    assert row["PokerHand"] == "a pair of Jacks"


def test_dim_player_summary_keeps_the_losers_revealed_cards(
    source_df: pd.DataFrame,
) -> None:
    # Hand 219269866589: VillainB lost and mucked [7h Td] — the revealed
    # cards of the losers matter for range studies
    dim = build_dim_player_summary(source_df)
    row = dim[(dim["HandID"] == 219269866589) & (dim["Player"] == "VillainB")].iloc[0]
    assert row["ShowDownC1"] == "7h"
    assert row["ShowDownC2"] == "Td"


# ---------------------------------------------------------------------------
# dim_final_rank
# ---------------------------------------------------------------------------
def test_dim_final_rank(source_df: pd.DataFrame) -> None:
    dim = build_dim_final_rank(source_df)
    assert len(dim) == 3
    ranks = dim.set_index("Player")
    assert ranks.loc["garciamurilo", "FinalRank"] == 1
    assert ranks.loc["garciamurilo", "Prize"] == 6.0
    assert ranks.loc["VillainB", "FinalRank"] == 2
    assert ranks.loc["VillainA", "FinalRank"] == 3
    assert pd.isna(ranks.loc["VillainA", "Prize"])


# ---------------------------------------------------------------------------
# build_star_schema
# ---------------------------------------------------------------------------
def test_build_star_schema_saves_the_five_tables(
    converted_dir: Path, tmp_path: Path
) -> None:
    number_of_rows = build_star_schema(str(converted_dir), str(tmp_path))

    expected_tables = [
        "fact_player_actions",
        "dim_tourn_summary",
        "dim_hand_summary",
        "dim_player_summary",
        "dim_final_rank",
    ]
    assert list(number_of_rows.keys()) == expected_tables
    for name in expected_tables:
        table = pd.read_parquet(tmp_path / f"{name}.parquet")
        assert len(table) == number_of_rows[name]
        assert len(table) > 0


def test_fact_ordering_anchors_on_players_that_did_not_act() -> None:
    # A big blind all-in on the blind post has no action rows, but still
    # anchors who acts first: the seat after the big blind opens the preflop
    placeholder = [[("", "")]]
    synthetic = pd.DataFrame(
        {
            "TournID": ["1"] * 4,
            "HandID": ["100"] * 4,
            "Player": ["sb", "bb", "utg", "btn"],
            "Seat": [1, 2, 4, 9],
            "Position": ["small blind", "big blind", None, "button"],
            "PostedBlind": [10.0, 20.0, None, None],
            "PostedAnte": [None] * 4,
            "Stack": [500.0, 500.0, 500.0, 500.0],
            "Blinds": [[10.0, 20.0]] * 4,
            "TableSize": [9] * 4,
            "Level": ["I"] * 4,
            "Playing": [4] * 4,
            "Ante": [None] * 4,
            "OwnersHand": [["Ah", "Kh"]] * 4,
            "PreflopAction": [
                [("folds", "")],
                placeholder[0],
                [("calls", "20")],
                [("folds", "")],
            ],
            "FlopAction": [placeholder[0]] * 4,
            "TurnAction": [placeholder[0]] * 4,
            "RiverAction": [placeholder[0]] * 4,
            "BoardFlop": [[]] * 4,
            "BoardTurn": [[]] * 4,
            "BoardRiver": [[]] * 4,
        }
    )

    fact = build_fact_player_actions(synthetic)

    # The posts open the hand; then utg (seat 4, right after the big blind)
    # acts first, followed by the button (seat 9) and the small blind (seat
    # 1); the big blind posted but never acted voluntarily
    assert fact[["Player", "Action"]].values.tolist() == [
        ["sb", "posts small blind"],
        ["bb", "posts big blind"],
        ["utg", "calls"],
        ["btn", "folds"],
        ["sb", "folds"],
    ]
    assert fact["ActionOrder"].tolist() == [1, 2, 3, 4, 5]
    # And the caller matches the big blind level
    assert fact[fact["Player"] == "utg"].iloc[0]["TotalValue"] == 20.0
