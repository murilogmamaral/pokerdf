"""Unit tests for the star schema modeling functions.

The input of the modeling functions is produced by converting the real hand
history fixture and saving it as .parquet, exactly like the convert command
does, so the whole pipeline convert -> parquet -> star schema is exercised.
"""

from pathlib import Path

import pandas as pd
import pytest

from pokerdf.modeling.star_schema import (
    _combination,
    _roman_to_int,
    build_dim_final_rank,
    build_dim_hand,
    build_dim_tournament,
    build_fact_player_action,
    build_star_schema,
)

FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250516 T99999 No Limit Hold_em US$ 1,84 + US$ 0,16.txt"
)


# The converted_dir, source_df and fact fixtures live in conftest.py, since
# the anonymization tests build on the same pipeline


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
# fact_player_action
# ---------------------------------------------------------------------------
def test_fact_has_expected_structure(fact: pd.DataFrame) -> None:
    assert list(fact.columns) == [
        "Owner",
        "TournID",
        "HandID",
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
        "OwnerCombination",
        "OwnerCombinationScore",
        "RevealedShowDownC1",
        "RevealedShowDownC2",
        "RevealedShowDownCombination",
        "RevealedShowDownCombinationScore",
        "RevealedShowDownPokerHand",
        "Result",
        "Balance",
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


def test_fact_carries_the_owner_on_every_row(fact: pd.DataFrame) -> None:
    # Owner completes the key of dim_hand (TournID, HandID, Owner), where
    # the constant context of the hand lives
    rows = fact[fact["HandID"] == 11111]
    assert (rows["Owner"] == "garciamurilo").all()


def test_fact_owner_cards_and_combination_on_every_row(fact: pd.DataFrame) -> None:
    # Hand 11111: the owner was dealt 3s Jh. The owner's holding is hand
    # context, like the board: it fills every row of the hand — also the
    # opponents' — so any behavior can be analyzed against it without joins
    rows = fact[fact["HandID"] == 11111]
    assert (rows["OwnerC1"] == "3s").all()
    assert (rows["OwnerC2"] == "Jh").all()
    assert (rows["OwnerCombination"] == "High Card").all()
    assert (rows["OwnerCombinationScore"] == 1).all()


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


def test_fact_broadcasts_the_opponents_showdown_cards(fact: pd.DataFrame) -> None:
    # Hand 219269866589: VillainB lost and mucked [7h Td]. The muck happens
    # at the end of the hand, but it reveals what was held from the first
    # action, so every row of the player carries the cards — the preflop
    # post included
    rows = fact[(fact["HandID"] == 219269866589) & (fact["Player"] == "VillainB")]
    assert len(rows) > 1
    assert (rows["RevealedShowDownC1"] == "7h").all()
    assert (rows["RevealedShowDownC2"] == "Td").all()


def test_fact_showdown_columns_include_the_owner(fact: pd.DataFrame) -> None:
    # Hand 219269866589: garciamurilo (the owner) showed [8h Kh]. OwnerC1
    # and OwnerC2 describe what was dealt; the showdown columns describe
    # what was revealed at the table, whoever the player is — so on the
    # owner's rows the two families coincide, and the revealed combination
    # matches the dealt one
    rows = fact[(fact["HandID"] == 219269866589) & (fact["Player"] == "garciamurilo")]
    assert (rows["OwnerC1"] == "8h").all()
    assert (rows["OwnerC2"] == "Kh").all()
    assert (rows["RevealedShowDownC1"] == "8h").all()
    assert (rows["RevealedShowDownC2"] == "Kh").all()
    assert (rows["RevealedShowDownCombination"] == rows["OwnerCombination"]).all()
    assert (
        rows["RevealedShowDownCombinationScore"] == rows["OwnerCombinationScore"]
    ).all()


def test_fact_showdown_columns_are_null_without_a_show(fact: pd.DataFrame) -> None:
    # Hand 11111: everyone folded to the big blind, so nobody revealed cards
    rows = fact[fact["HandID"] == 11111]
    assert rows["RevealedShowDownC1"].isna().all()
    assert rows["RevealedShowDownC2"].isna().all()
    assert rows["RevealedShowDownCombination"].isna().all()


def test_fact_infers_the_owner_combination_at_each_moment(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269866589: the owner holds 8h Kh and the board runs
    # Jh 5s 4s / Jc / 2h — a high card until the turn pairs the jacks.
    # The combination follows the round, on every row of the round
    rows = fact[fact["HandID"] == 219269866589]
    by_round = {
        round_name: group for round_name, group in rows.groupby("Round", sort=False)
    }
    for round_name, expected_name, expected_score in [
        ("preflop", "High Card", 1),
        ("flop", "High Card", 1),
        ("turn", "One Pair", 2),
        ("river", "One Pair", 2),
    ]:
        assert (by_round[round_name]["OwnerCombination"] == expected_name).all()
        assert (by_round[round_name]["OwnerCombinationScore"] == expected_score).all()


def test_fact_infers_the_combination_of_the_shown_opponent(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269866589: VillainB mucked 7h Td, so his combination at each
    # moment is known — on his own rows
    villain = fact[(fact["HandID"] == 219269866589) & (fact["Player"] == "VillainB")]
    assert villain[
        ["Round", "RevealedShowDownCombination", "RevealedShowDownCombinationScore"]
    ].values.tolist() == [
        ["preflop", "High Card", 1],  # posts big blind
        ["preflop", "High Card", 1],  # checks
        ["flop", "High Card", 1],
        ["turn", "One Pair", 2],
        ["river", "One Pair", 2],
    ]
    # And his rows also carry the owner's holding, which is hand context
    assert (villain["OwnerC1"] == "8h").all()
    assert villain["OwnerCombination"].notna().all()


def test_combination_requires_both_hole_cards() -> None:
    # A single revealed card cannot say what the hand was: the cards are
    # kept, but no combination is inferred
    assert _combination("Ah", None, ("Jh", "5s", "4s")) == (None, None)
    assert _combination(None, None, ()) == (None, None)
    assert _combination("Ah", "Ad", ()) == ("One Pair", 2)


def test_fact_registers_the_outcome_on_every_row_of_the_player(
    fact: pd.DataFrame,
) -> None:
    # Hand 219269866589: the outcome of each player — result, amount
    # collected and the combination the platform named at showdown — is a
    # future event of the hand, registered on every row of the player.
    # garciamurilo won 40 showing a pair of Jacks; VillainB mucked and
    # collected nothing
    rows = fact[fact["HandID"] == 219269866589]
    owner = rows[rows["Player"] == "garciamurilo"]
    assert (owner["Result"] == "won").all()
    assert (owner["Balance"] == 40.0).all()
    assert (owner["RevealedShowDownPokerHand"] == "a pair of Jacks").all()
    villain = rows[rows["Player"] == "VillainB"]
    assert (villain["Result"] == "mucked").all()
    assert villain["Balance"].isna().all()
    assert villain["RevealedShowDownPokerHand"].isna().all()


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
# dim_tournament
# ---------------------------------------------------------------------------
def test_dim_tournament(source_df: pd.DataFrame) -> None:
    # One row per tournament per owner: each owner can start the tournament
    # at a different time, so Owner is part of the key
    dim = build_dim_tournament(source_df)
    assert len(dim) == 1
    assert list(dim.columns) == [
        "Owner",
        "TournID",
        "TournStartTimeCET",
        "TournStartTimeLocal",
        "Modality",
        "BuyIn",
    ]
    row = dim.iloc[0]
    assert row["TournID"] == 99999
    assert row["Owner"] == "garciamurilo"
    assert row["TournStartTimeCET"] == pd.Timestamp("2020-10-11 07:22:15")
    assert row["Modality"] == "USD Hold'em No Limit"
    assert row["BuyIn"] == "$1.84+$0.16"
    # TableSize belongs to the fact table
    assert "TableSize" not in dim.columns


# ---------------------------------------------------------------------------
# dim_hand
# ---------------------------------------------------------------------------
def test_dim_hand_has_one_row_per_hand_per_owner(source_df: pd.DataFrame) -> None:
    dim = build_dim_hand(source_df)
    hands = source_df.drop_duplicates(subset=["TournID", "HandID", "Owner"])
    assert len(dim) == len(hands)
    assert not dim.duplicated(subset=["TournID", "HandID", "Owner"]).any()


def test_dim_hand_carries_the_hand_context(source_df: pd.DataFrame) -> None:
    # Hand 11111: 3-max at level I (blinds 10/20), 3 players, no ante,
    # logged by the archive of garciamurilo
    dim = build_dim_hand(source_df)
    assert list(dim.columns) == [
        "Owner",
        "TournID",
        "HandID",
        "HandStartTimeCET",
        "HandStartTimeLocal",
        "HandTimezone",
        "TableSize",
        "Playing",
        "Level",
        "Ante",
        "SmallBlind",
        "BigBlind",
    ]
    row = dim[dim["HandID"] == 11111].iloc[0]
    assert row["Owner"] == "garciamurilo"
    assert row["HandStartTimeCET"] == pd.Timestamp("2020-10-11 07:22:15")
    assert row["TableSize"] == 3
    assert row["Playing"] == 3
    assert row["Level"] == 1
    assert pd.isna(row["Ante"])
    assert row["SmallBlind"] == 10.0
    assert row["BigBlind"] == 20.0


# ---------------------------------------------------------------------------
# dim_final_rank
# ---------------------------------------------------------------------------
def test_dim_final_rank(source_df: pd.DataFrame) -> None:
    # One row per player per tournament per owner: the ranks are as
    # observed by the owner's archive, and an owner eliminated early does
    # not see the final rank of everyone
    dim = build_dim_final_rank(source_df)
    assert len(dim) == 3
    assert list(dim.columns) == ["Owner", "TournID", "Player", "FinalRank", "Prize"]
    assert (dim["Owner"] == "garciamurilo").all()
    ranks = dim.set_index("Player")
    assert ranks.loc["garciamurilo", "FinalRank"] == 1
    assert ranks.loc["garciamurilo", "Prize"] == 6.0
    assert ranks.loc["VillainB", "FinalRank"] == 2
    assert ranks.loc["VillainA", "FinalRank"] == 3
    assert pd.isna(ranks.loc["VillainA", "Prize"])


# ---------------------------------------------------------------------------
# build_star_schema
# ---------------------------------------------------------------------------
def test_build_star_schema_saves_the_four_tables(
    converted_dir: Path, tmp_path: Path
) -> None:
    number_of_rows = build_star_schema(str(converted_dir), str(tmp_path))

    expected_tables = [
        "fact_player_action",
        "dim_tournament",
        "dim_hand",
        "dim_final_rank",
    ]
    assert list(number_of_rows.keys()) == expected_tables
    for name in expected_tables:
        table = pd.read_parquet(tmp_path / f"{name}.parquet")
        assert len(table) == number_of_rows[name]
        assert len(table) > 0


def test_build_star_schema_gdpr_saves_everything_but_the_final_rank(
    converted_dir: Path, tmp_path: Path
) -> None:
    number_of_rows = build_star_schema(str(converted_dir), str(tmp_path), gdpr="full")

    # Only the final-rank dimension is left out (it mirrors public
    # tournament results), and the report sits next to the data
    assert list(number_of_rows.keys()) == [
        "fact_player_action",
        "dim_tournament",
        "dim_hand",
    ]
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "anonymization.txt",
        "dim_hand.parquet",
        "dim_tournament.parquet",
        "fact_player_action.parquet",
    ]

    table = pd.read_parquet(tmp_path / "fact_player_action.parquet")
    assert len(table) == number_of_rows["fact_player_action"]
    # The owner's nickname must not survive, but their cards always do
    assert "garciamurilo" not in set(table["Player"])
    assert "OwnerC1" in table.columns

    # The hand dimension loses its timestamp and joins the fact through
    # the pseudonyms, since the salt is shared
    dim = pd.read_parquet(tmp_path / "dim_hand.parquet")
    assert "HandStartTimeCET" not in dim.columns
    assert "garciamurilo" not in set(dim["Owner"])
    assert set(dim["HandID"]) == set(table["HandID"])
    assert set(dim["Owner"]) == set(table["Owner"])

    # The tournament dimension is blurred the same way, without its
    # start time
    tourn = pd.read_parquet(tmp_path / "dim_tournament.parquet")
    assert "garciamurilo" not in set(tourn["Owner"])
    assert set(tourn["TournID"]) == set(table["TournID"])
    assert "TournStartTimeCET" not in tourn.columns


def test_build_star_schema_gdpr_keep_owner_spares_only_the_owner(
    converted_dir: Path, tmp_path: Path
) -> None:
    build_star_schema(str(converted_dir), str(tmp_path), gdpr="keep-owner")

    table = pd.read_parquet(tmp_path / "fact_player_action.parquet")
    # The owner keeps their nickname and their hole cards; every third
    # party is pseudonymized
    players = set(table["Player"])
    assert "garciamurilo" in players
    assert players.isdisjoint({"VillainA", "VillainB"})
    assert "OwnerC1" in table.columns
    assert (table["Owner"] == "garciamurilo").all()


def test_build_star_schema_rejects_an_unknown_gdpr_mode(
    converted_dir: Path, tmp_path: Path
) -> None:
    # Library callers skip the argparse validation, so the mode is checked
    # before any work is done, with the accepted values in the message
    with pytest.raises(ValueError, match="expected one of full, keep-owner"):
        build_star_schema(str(converted_dir), str(tmp_path), gdpr="rgpd")


def test_build_star_schema_gdpr_honors_a_given_salt(
    converted_dir: Path, tmp_path: Path
) -> None:
    first, second, third = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    for folder in (first, second, third):
        folder.mkdir()

    build_star_schema(str(converted_dir), str(first), gdpr="full", salt="fixed")
    build_star_schema(str(converted_dir), str(second), gdpr="full", salt="fixed")
    build_star_schema(str(converted_dir), str(third), gdpr="full")

    players = [
        pd.read_parquet(folder / "fact_player_action.parquet")["Player"]
        for folder in (first, second, third)
    ]
    # The same salt gives the same pseudonyms, so sessions can be appended
    assert players[0].equals(players[1])
    # A random salt does not, which is what makes it irreversible
    assert not players[0].equals(players[2])


def test_fact_ordering_anchors_on_players_that_did_not_act() -> None:
    # A big blind all-in on the blind post has no action rows, but still
    # anchors who acts first: the seat after the big blind opens the preflop
    placeholder = [[("", "")]]
    synthetic = pd.DataFrame(
        {
            "TournID": ["1"] * 4,
            "HandID": ["100"] * 4,
            "HandStartTimeCET": [pd.Timestamp("2020-01-01 12:00:00")] * 4,
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
            "Owner": ["utg"] * 4,
            "OwnersHand": [["Ah", "Kh"]] * 4,
            "ShowDown": [[None, None]] * 4,
            "CardCombination": [None] * 4,
            "Result": ["folded", "folded", "won", "folded"],
            "Balance": [None, None, 50.0, None],
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

    fact = build_fact_player_action(synthetic)

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
