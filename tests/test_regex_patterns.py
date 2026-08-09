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


def test_get_total_pot_log(first_hand: list[str]) -> None:
    assert r.get_total_pot_log(first_hand) == [20.0]


def test_get_total_pot_log_with_side_pots() -> None:
    # With side pots the summary decomposes the total, but the first number
    # is still the total pot
    hand = [
        "Hand #1: ...",
        "SUMMARY ***\nTotal pot 9136 Main pot 5820. Side pot 3316. | Rake 0",
    ]
    assert r.get_total_pot_log(hand) == [9136.0]


def test_get_rake(first_hand: list[str]) -> None:
    assert r.get_rake(first_hand) == [0.0]


def test_get_pot_breakdown_with_side_pots(side_pot_hand: list[str]) -> None:
    # Main pot first, then each side pot
    assert r.get_pot_breakdown(side_pot_hand) == [(300.0, 400.0)]


def test_get_pot_breakdown_with_a_single_pot(first_hand: list[str]) -> None:
    # Without side pots the breakdown is the total pot itself
    assert r.get_pot_breakdown(first_hand) == [(20.0,)]


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


def test_get_bounty_won_split_elimination() -> None:
    # Two players splitting an elimination each win their share
    hand = [
        "Hand #1: Tournament #2, ...",
        "SHOW DOWN ***\n"
        "VillainA wins $0.34 for splitting the elimination of VillainC "
        "and their own bounty increases by $0.34 to $14.55\n"
        "VillainB wins $0.34 for splitting the elimination of VillainC "
        "and their own bounty increases by $0.33 to $1.20",
    ]
    assert r.get_bounty_won("VillainA", hand) == [0.34]
    assert r.get_bounty_won("VillainB", hand) == [0.34]
    assert r.get_bounty_won("VillainC", hand) == [None]


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


def test_get_showed_card_single_card_show(
    single_card_show_hand: list[str],
) -> None:
    # A voluntary single-card show is not mirrored in the summary, so it is
    # captured from the body of the hand, with None as the second card
    expected: list[Any] = [("Qs", None)]
    assert r.get_showed_card("VillainB", single_card_show_hand) == expected


def test_get_showed_card_single_card_show_ignores_other_players(
    single_card_show_hand: list[str],
) -> None:
    assert r.get_showed_card("garciamurilo", single_card_show_hand) == [[None, None]]


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


def test_get_final_rank_finished_without_a_place(
    satellite_final_hand: list[str],
) -> None:
    # Some logs report the finish without a place: 0 marks it
    assert r.get_final_rank("VillainC", satellite_final_hand) == [0]


def test_get_final_rank_placed_finishes_take_precedence(
    satellite_final_hand: list[str],
) -> None:
    assert r.get_final_rank("VillainB", satellite_final_hand) == [2]
    assert r.get_final_rank("garciamurilo", satellite_final_hand) == [1]


def test_get_final_rank_without_a_showdown(
    no_showdown_elimination_hand: list[str],
) -> None:
    # A player all-in on the blind post is eliminated when everyone folds,
    # so the finish line appears in a hand with no SHOW DOWN section
    assert r.get_final_rank("VillainF", no_showdown_elimination_hand) == [4]
    assert r.get_final_rank("VillainE", no_showdown_elimination_hand) == [-1]


def test_get_final_rank_and_prize_of_a_win_without_a_showdown() -> None:
    # Synthetic hand: the tournament ends with a fold, so the win and the
    # prize are reported without a SHOW DOWN section
    hand = [
        "Hand #1: Tournament #2, ...",
        "HOLE CARDS ***\n"
        "VillainA: folds \n"
        "garciamurilo collected 40 from pot\n"
        "VillainA finished the tournament in 2nd place\n"
        "garciamurilo wins the tournament and receives $0.50 - congratulations!",
        "SUMMARY ***\nTotal pot 40 | Rake 0 ",
    ]
    assert r.get_final_rank("garciamurilo", hand) == [1]
    assert r.get_final_rank("VillainA", hand) == [2]
    expected: list[Any] = [0.5]
    assert r.get_prize("garciamurilo", hand) == expected


def test_get_prize_of_tournament_winner(final_hand: list[str]) -> None:
    expected: list[Any] = [6.0]
    assert r.get_prize("garciamurilo", final_hand) == expected


def test_get_prize_returns_none_when_no_prize_is_awarded(
    final_hand: list[str],
) -> None:
    assert r.get_prize("VillainB", final_hand) == [None]


def test_get_prize_satellite_ticket(satellite_final_hand: list[str]) -> None:
    # The prize of a satellite is a ticket: its face value is captured
    expected: list[Any] = [1.0]
    assert r.get_prize("garciamurilo", satellite_final_hand) == expected


def test_get_prize_ticket_is_not_awarded_to_the_other_players(
    satellite_final_hand: list[str],
) -> None:
    assert r.get_prize("VillainB", satellite_final_hand) == [None]


# ---------------------------------------------------------------------------
# Nicknames with characters that are special to a regex
# ---------------------------------------------------------------------------
# A nickname is arbitrary text and routinely contains ".", "-", "(", ")" or a
# space. It is interpolated into every player-specific pattern, so it has to be
# escaped there - and only there, so the nickname the methods return is the one
# the platform wrote. "VillainXOne" is in the hand on purpose: an unescaped
# "Villain.One" would match it too, silently returning another player's data.
# The nicknames here are invented: real ones are personal data of third
# parties and never belong in the repository.
TRICKY_HAND = [
    # One stage per element, as the converter splits a hand
    "Hand #44401: Tournament #77777, $1.84+$0.16 USD Hold'em No Limit"
    " - Level I (10/20) - 2020/10/11 3:22:15 BRT [2020/10/11 2:22:15 ET]\n"
    "Table '77777 1' 4-max Seat #1 is the button\n"
    "Seat 1: VillainXOne (900 in chips) \n"
    "Seat 2: Villain.One (500 in chips) \n"
    "Seat 3: Villain Two 0 (480 in chips) \n"
    "Seat 4: VillainThree) (520 in chips) \n"
    "Villain Two 0: posts small blind 10\n"
    "VillainThree): posts big blind 20\n",
    "HOLE CARDS ***\n"
    "Dealt to Villain.One [8h Kh]\n"
    "VillainXOne: folds \n"
    "Villain.One: calls 20\n"
    "Villain Two 0: folds \n"
    "VillainThree): checks \n",
    "FLOP *** [Jh 5s 4s]\n" "VillainThree): bets 40\n" "Villain.One: calls 40\n",
    "SHOW DOWN ***\n"
    "VillainThree): shows [7h Td] (a pair of Sevens)\n"
    "Villain.One: shows [8h Kh] (a pair of Jacks)\n"
    "Villain.One collected 130 from pot\n",
    "SUMMARY ***\n"
    "Total pot 130 | Rake 0 \n"
    "Board [Jh 5s 4s]\n"
    "Seat 1: VillainXOne (button) folded before Flop (didn't bet)\n"
    "Seat 2: Villain.One showed [8h Kh] and won (130) with a pair of Jacks\n"
    "Seat 3: Villain Two 0 (small blind) folded before Flop\n"
    "Seat 4: VillainThree) (big blind) showed [7h Td] and lost"
    " with a pair of Sevens\n",
]


def test_get_players_returns_the_nicknames_untouched() -> None:
    assert r.get_players(TRICKY_HAND) == [
        "VillainXOne",
        "Villain.One",
        "Villain Two 0",
        "VillainThree)",
    ]


def test_capture_works_for_nicknames_with_regex_characters() -> None:
    # A closing parenthesis would be a syntax error in an unescaped pattern
    assert r.get_seat("VillainThree)", TRICKY_HAND) == [4]
    assert r.get_stack("VillainThree)", TRICKY_HAND) == [520.0]
    assert r.get_position("VillainThree)", TRICKY_HAND) == ["big blind"]
    assert r.get_posted_blind("VillainThree)", TRICKY_HAND) == [20.0]
    assert r.get_showed_card("VillainThree)", TRICKY_HAND) == [("7h", "Td")]
    assert r.get_result("VillainThree)", TRICKY_HAND) == ["lost"]
    # Spaces and hyphens are escaped by re.escape as well
    assert r.get_seat("Villain Two 0", TRICKY_HAND) == [3]
    assert r.get_position("Villain Two 0", TRICKY_HAND) == ["small blind"]


def test_a_dot_in_a_nickname_does_not_match_another_player() -> None:
    # Unescaped, "Villain.One" would also match the line of "VillainXOne"
    assert r.get_seat("Villain.One", TRICKY_HAND) == [2]
    assert r.get_stack("Villain.One", TRICKY_HAND) == [500.0]
    assert r.get_balance("Villain.One", TRICKY_HAND) == [130.0]
    assert r.get_card_combination("Villain.One", TRICKY_HAND) == ["a pair of Jacks"]
    # And the other player keeps their own data
    assert r.get_seat("VillainXOne", TRICKY_HAND) == [1]
    assert r.get_position("VillainXOne", TRICKY_HAND) == ["button"]
