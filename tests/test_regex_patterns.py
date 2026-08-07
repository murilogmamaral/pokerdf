"""Unit tests for every extraction method of RegexPatterns.

Each test targets one method, using real hands from the fixture file:
the happy path and the fallback path (stage not reached, value absent, etc.).
"""

from typing import Any

import pandas as pd

from pokerdf.regex.regex_patterns import RegexPatterns

r = RegexPatterns()


# ---------------------------------------------------------------------------
# _guarantee_unicity
# ---------------------------------------------------------------------------
def test_guarantee_unicity_keeps_single_element() -> None:
    assert r._guarantee_unicity(["a"]) == ["a"]


def test_guarantee_unicity_keeps_only_first_element() -> None:
    assert r._guarantee_unicity(["a", "b", "c"]) == ["a"]


def test_guarantee_unicity_fills_empty_list_with_default() -> None:
    assert r._guarantee_unicity([]) == ["Unknown"]


def test_guarantee_unicity_fills_empty_list_with_custom_fill() -> None:
    assert r._guarantee_unicity([], fill=None) == [None]


# ---------------------------------------------------------------------------
# Tournament-wide data
# ---------------------------------------------------------------------------
def test_get_modality(first_hand: list[str]) -> None:
    assert r.get_modality(first_hand) == ["USD Hold'em No Limit"]


def test_get_tourn_id(first_hand: list[str]) -> None:
    assert r.get_tourn_id(first_hand) == ["99999"]


def test_get_buyin(first_hand: list[str]) -> None:
    assert r.get_buyin(first_hand) == ["$1.84+$0.16"]


def test_get_table_size(first_hand: list[str]) -> None:
    assert r.get_table_size(first_hand) == [3]


def test_get_owner(first_hand: list[str]) -> None:
    assert r.get_owner(first_hand) == ["garciamurilo"]


# ---------------------------------------------------------------------------
# Hand-wide data
# ---------------------------------------------------------------------------
def test_get_hand_id(first_hand: list[str]) -> None:
    assert r.get_hand_id(first_hand) == ["11111"]


def test_get_table_id(first_hand: list[str]) -> None:
    assert r.get_table_id(first_hand) == ["1"]


def test_get_time(first_hand: list[str]) -> None:
    assert r.get_time(first_hand) == [pd.Timestamp("2020-10-11 03:22:15")]


def test_get_level(first_hand: list[str]) -> None:
    assert r.get_level(first_hand) == ["I"]


def test_get_blinds(first_hand: list[str]) -> None:
    assert r.get_blinds(first_hand) == [[10.0, 20.0]]


def test_get_ante_returns_none_when_no_ante_is_posted(first_hand: list[str]) -> None:
    assert r.get_ante(first_hand) == [None]


def test_get_owner_cards(first_hand: list[str]) -> None:
    expected: list[Any] = [("3s", "Jh")]
    assert r.get_owner_cards(first_hand) == expected


def test_get_players(first_hand: list[str]) -> None:
    assert r.get_players(first_hand) == ["VillainA", "garciamurilo", "VillainB"]


def test_get_number_of_active_players(first_hand: list[str]) -> None:
    assert r.get_number_of_active_players(first_hand) == [3]


def test_get_board_flop(flop_hand: list[str]) -> None:
    assert r.get_board(flop_hand, stage="FLOP ***") == [("4d", "Tc", "7s")]


def test_get_board_river(final_hand: list[str]) -> None:
    expected = [("6h", "Qs", "Qh", "Jd", "8c")]
    assert r.get_board(final_hand, stage="RIVER ***") == expected


def test_get_board_returns_empty_tuple_when_stage_is_not_reached(
    flop_hand: list[str],
) -> None:
    assert r.get_board(flop_hand, stage="TURN ***") == [()]


# ---------------------------------------------------------------------------
# Player-specific data
# ---------------------------------------------------------------------------
def test_get_seat(first_hand: list[str]) -> None:
    assert r.get_seat("garciamurilo", first_hand) == [2]


def test_get_stack(first_hand: list[str]) -> None:
    assert r.get_stack("garciamurilo", first_hand) == [500.0]


def test_get_position(first_hand: list[str]) -> None:
    assert r.get_position("garciamurilo", first_hand) == ["small blind"]
    assert r.get_position("VillainA", first_hand) == ["button"]


def test_get_position_heads_up_button_is_captured_first(
    final_hand: list[str],
) -> None:
    # In heads-up hands the summary shows "(button) (small blind)"
    assert r.get_position("VillainB", final_hand) == ["button"]


def test_get_posted_blind(first_hand: list[str]) -> None:
    assert r.get_posted_blind("garciamurilo", first_hand) == [10.0]
    assert r.get_posted_blind("VillainB", first_hand) == [20.0]


def test_get_posted_blind_returns_none_when_no_blind_is_posted(
    first_hand: list[str],
) -> None:
    assert r.get_posted_blind("VillainA", first_hand) == [None]


def test_get_posted_ante_returns_none_when_no_ante_is_posted(
    first_hand: list[str],
) -> None:
    assert r.get_posted_ante("garciamurilo", first_hand) == [None]


def test_get_bounty(pko_elimination_hand: list[str]) -> None:
    assert r.get_bounty("VillainA", pko_elimination_hand) == [0.5]
    assert r.get_bounty("garciamurilo", pko_elimination_hand) == [0.5]


def test_get_bounty_returns_none_without_bounties(first_hand: list[str]) -> None:
    assert r.get_bounty("garciamurilo", first_hand) == [None]


def test_get_bounty_won_progressive_knockout(
    pko_elimination_hand: list[str],
) -> None:
    # Progressive knockout: only the cash part of the bounty is won
    assert r.get_bounty_won("garciamurilo", pko_elimination_hand) == [0.25]


def test_get_bounty_won_regular_knockout(ko_final_hand: list[str]) -> None:
    # Regular knockout: the whole bounty of the eliminated player is won
    assert r.get_bounty_won("garciamurilo", ko_final_hand) == [0.5]


def test_get_bounty_won_returns_none_when_no_bounty_is_won(
    pko_elimination_hand: list[str],
) -> None:
    assert r.get_bounty_won("VillainB", pko_elimination_hand) == [None]


def test_get_actions_preflop(first_hand: list[str]) -> None:
    result = r.get_actions("garciamurilo", first_hand, stage="HOLE CARDS ***")
    assert result == [[("folds", "")]]


def test_get_actions_with_amount(flop_hand: list[str]) -> None:
    result = r.get_actions("VillainB", flop_hand, stage="HOLE CARDS ***")
    assert result == [[("raises", "20")]]
    result = r.get_actions("VillainB", flop_hand, stage="FLOP ***")
    assert result == [[("bets", "80")]]


def test_get_actions_returns_empty_when_player_did_not_act(
    flop_hand: list[str],
) -> None:
    result = r.get_actions("garciamurilo", flop_hand, stage="FLOP ***")
    assert result == [[("", "")]]


def test_get_actions_returns_empty_when_stage_is_not_reached(
    first_hand: list[str],
) -> None:
    result = r.get_actions("garciamurilo", first_hand, stage="RIVER ***")
    assert result == [[("", "")]]


def test_get_allin_detects_allin(allin_hand: list[str]) -> None:
    assert r.get_allin("VillainA", allin_hand, stage="HOLE CARDS ***") == [True]


def test_get_allin_returns_false_when_player_is_not_allin(
    allin_hand: list[str],
) -> None:
    assert r.get_allin("garciamurilo", allin_hand, stage="HOLE CARDS ***") == [False]


def test_get_allin_returns_false_when_stage_is_not_reached(
    first_hand: list[str],
) -> None:
    assert r.get_allin("garciamurilo", first_hand, stage="RIVER ***") == [False]


def test_get_showed_card_when_player_shows(showdown_hand: list[str]) -> None:
    expected: list[Any] = [("8h", "Kh")]
    assert r.get_showed_card("garciamurilo", showdown_hand) == expected


def test_get_showed_card_when_player_mucks(showdown_hand: list[str]) -> None:
    expected: list[Any] = [("7h", "Td")]
    assert r.get_showed_card("VillainB", showdown_hand) == expected


def test_get_showed_card_returns_none_when_cards_are_not_revealed(
    showdown_hand: list[str],
) -> None:
    assert r.get_showed_card("VillainA", showdown_hand) == [[None, None]]


def test_get_card_combination(showdown_hand: list[str]) -> None:
    assert r.get_card_combination("garciamurilo", showdown_hand) == ["a pair of Jacks"]


def test_get_card_combination_returns_none_without_showdown(
    showdown_hand: list[str],
) -> None:
    assert r.get_card_combination("VillainA", showdown_hand) == [None]


def test_get_result_won(showdown_hand: list[str]) -> None:
    assert r.get_result("garciamurilo", showdown_hand) == ["won"]


def test_get_result_mucked(showdown_hand: list[str]) -> None:
    assert r.get_result("VillainB", showdown_hand) == ["mucked"]


def test_get_result_folded(showdown_hand: list[str]) -> None:
    assert r.get_result("VillainA", showdown_hand) == ["folded"]


def test_get_result_non_showdown_win(first_hand: list[str]) -> None:
    assert r.get_result("VillainB", first_hand) == ["non-sd win"]


def test_get_balance(showdown_hand: list[str]) -> None:
    assert r.get_balance("garciamurilo", showdown_hand) == [40.0]


def test_get_balance_returns_none_when_nothing_is_collected(
    showdown_hand: list[str],
) -> None:
    assert r.get_balance("VillainA", showdown_hand) == [None]


def test_get_uncalled_returned(first_hand: list[str]) -> None:
    # VillainB's unmatched part of the big blind comes back when everyone folds
    assert r.get_uncalled_returned("VillainB", first_hand) == [10.0]


def test_get_uncalled_returned_returns_none_when_nothing_is_returned(
    first_hand: list[str],
) -> None:
    assert r.get_uncalled_returned("garciamurilo", first_hand) == [None]


def test_get_uncalled_returned_sums_multiple_returns() -> None:
    # Synthetic hand: the excess of a raise over a short all-in is returned
    # preflop, and an uncalled bet is returned on the flop
    hand = [
        "Hand #1: Tournament #2, ...",
        "HOLE CARDS ***\n"
        "VillainA: raises 380 to 400 and is all-in\n"
        "garciamurilo: raises 600 to 1000\n"
        "Uncalled bet (600) returned to garciamurilo",
        "FLOP *** [2c 7d 9h]\n"
        "garciamurilo: bets 200\n"
        "Uncalled bet (200) returned to garciamurilo",
    ]
    assert r.get_uncalled_returned("garciamurilo", hand) == [800.0]


def test_get_uncalled_returned_does_not_match_a_longer_player_name() -> None:
    # "Vill" must not capture the return of "VillainA"
    hand = ["HOLE CARDS ***\nUncalled bet (50) returned to VillainA"]
    assert r.get_uncalled_returned("Vill", hand) == [None]


def test_get_final_rank_of_eliminated_player(elimination_hand: list[str]) -> None:
    assert r.get_final_rank("VillainA", elimination_hand) == [3]


def test_get_final_rank_of_tournament_winner(final_hand: list[str]) -> None:
    assert r.get_final_rank("garciamurilo", final_hand) == [1]
    assert r.get_final_rank("VillainB", final_hand) == [2]


def test_get_final_rank_returns_minus_one_when_not_defined(
    first_hand: list[str],
) -> None:
    assert r.get_final_rank("garciamurilo", first_hand) == [-1]


def test_get_prize_of_tournament_winner(final_hand: list[str]) -> None:
    # The value is captured as text; pydantic coerces it to float downstream
    expected: list[Any] = ["6.00"]
    assert r.get_prize("garciamurilo", final_hand) == expected


def test_get_prize_returns_none_when_no_prize_is_awarded(
    final_hand: list[str],
) -> None:
    assert r.get_prize("VillainB", final_hand) == [None]
