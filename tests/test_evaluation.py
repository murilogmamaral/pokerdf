"""Unit tests for the poker hand evaluator."""

import pytest

from pokerdf.modeling.evaluation import (
    COMBINATION_SCORES,
    Combination,
    evaluate_hand,
)


# ---------------------------------------------------------------------------
# Scores
# ---------------------------------------------------------------------------
def test_scores_grow_with_the_strength_of_the_combination() -> None:
    assert COMBINATION_SCORES[Combination.HIGH_CARD] == 1
    assert COMBINATION_SCORES[Combination.ONE_PAIR] == 2
    assert COMBINATION_SCORES[Combination.TWO_PAIR] == 3
    assert COMBINATION_SCORES[Combination.THREE_OF_A_KIND] == 4
    assert COMBINATION_SCORES[Combination.STRAIGHT] == 5
    assert COMBINATION_SCORES[Combination.FLUSH] == 6
    assert COMBINATION_SCORES[Combination.FULL_HOUSE] == 7
    assert COMBINATION_SCORES[Combination.FOUR_OF_A_KIND] == 8
    assert COMBINATION_SCORES[Combination.STRAIGHT_FLUSH] == 9
    assert COMBINATION_SCORES[Combination.ROYAL_FLUSH] == 10


# ---------------------------------------------------------------------------
# Each category, on a full seven-card river
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "cards, expected",
    [
        # Nothing connects: ace-high
        (["Ah", "9d", "2c", "5s", "7h", "Jc", "Kd"], Combination.HIGH_CARD),
        # A pair of aces
        (["Ah", "Ad", "2c", "5s", "7h", "Jc", "Kd"], Combination.ONE_PAIR),
        # Aces and fives
        (["Ah", "Ad", "5c", "5s", "7h", "Jc", "Kd"], Combination.TWO_PAIR),
        # Three aces
        (["Ah", "Ad", "Ac", "5s", "7h", "Jc", "Kd"], Combination.THREE_OF_A_KIND),
        # Nine to king
        (["9h", "Td", "Jc", "Qs", "Kh", "2c", "7d"], Combination.STRAIGHT),
        # Five hearts
        (["Ah", "9h", "2h", "5h", "7h", "Jc", "Kd"], Combination.FLUSH),
        # Aces full of fives
        (["Ah", "Ad", "Ac", "5s", "5h", "Jc", "Kd"], Combination.FULL_HOUSE),
        # Four aces
        (["Ah", "Ad", "Ac", "As", "7h", "Jc", "Kd"], Combination.FOUR_OF_A_KIND),
        # Five to nine, all hearts
        (["5h", "6h", "7h", "8h", "9h", "Ac", "Ad"], Combination.STRAIGHT_FLUSH),
        # Ten to ace, all spades
        (["Ts", "Js", "Qs", "Ks", "As", "2c", "7d"], Combination.ROYAL_FLUSH),
    ],
)
def test_each_category_is_recognized(cards: list[str], expected: Combination) -> None:
    assert evaluate_hand(cards) == expected


# ---------------------------------------------------------------------------
# Straight corner cases
# ---------------------------------------------------------------------------
def test_the_wheel_counts_as_a_straight() -> None:
    # A-2-3-4-5: the ace plays low
    assert evaluate_hand(["Ah", "2d", "3c", "4s", "5h", "9c", "Kd"]) == (
        Combination.STRAIGHT
    )


def test_four_in_a_row_with_a_gap_is_not_a_straight() -> None:
    # A-2-3-4-6 must not be mistaken for the wheel
    assert evaluate_hand(["Ah", "2d", "3c", "4s", "6h"]) == Combination.HIGH_CARD


def test_duplicated_values_do_not_break_the_straight() -> None:
    # The pair inside the sequence must not hide the straight
    assert evaluate_hand(["9h", "9d", "Tc", "Js", "Qh", "Kc", "8d"]) == (
        Combination.STRAIGHT
    )


def test_the_steel_wheel_is_a_straight_flush() -> None:
    # A-2-3-4-5 of the same suit
    assert evaluate_hand(["Ah", "2h", "3h", "4h", "5h", "Kc", "Kd"]) == (
        Combination.STRAIGHT_FLUSH
    )


def test_a_straight_and_a_flush_of_different_suits_is_not_a_straight_flush() -> None:
    # The straight uses the diamond ten: flush, the better of the two
    assert evaluate_hand(["6h", "7h", "8h", "9h", "Td", "2h", "3c"]) == (
        Combination.FLUSH
    )


# ---------------------------------------------------------------------------
# Repetition corner cases on seven cards
# ---------------------------------------------------------------------------
def test_two_trips_make_a_full_house() -> None:
    assert evaluate_hand(["Ah", "Ad", "Ac", "5s", "5h", "5c", "Kd"]) == (
        Combination.FULL_HOUSE
    )


def test_trips_and_a_lower_pair_make_a_full_house() -> None:
    assert evaluate_hand(["5s", "5h", "5c", "2d", "2h", "Jc", "Kd"]) == (
        Combination.FULL_HOUSE
    )


def test_three_pairs_are_still_a_two_pair() -> None:
    assert evaluate_hand(["Ah", "Ad", "5c", "5s", "2h", "2c", "Kd"]) == (
        Combination.TWO_PAIR
    )


def test_quads_beat_the_flush_on_the_same_board() -> None:
    assert evaluate_hand(["Ah", "Ad", "Ac", "As", "7h", "Jh", "Kh"]) == (
        Combination.FOUR_OF_A_KIND
    )


# ---------------------------------------------------------------------------
# Fewer cards: preflop and flop moments
# ---------------------------------------------------------------------------
def test_a_pocket_pair_is_one_pair_on_preflop() -> None:
    assert evaluate_hand(["Qh", "Qd"]) == Combination.ONE_PAIR


def test_unpaired_hole_cards_are_a_high_card_on_preflop() -> None:
    assert evaluate_hand(["Ah", "Kd"]) == Combination.HIGH_CARD


def test_five_cards_are_enough_for_every_category() -> None:
    assert evaluate_hand(["Ts", "Js", "Qs", "Ks", "As"]) == Combination.ROYAL_FLUSH
    assert evaluate_hand(["9h", "Td", "Jc", "Qs", "Kh"]) == Combination.STRAIGHT


def test_six_cards_pick_the_best_five() -> None:
    # The sixth card completes the flush over the two pair
    assert evaluate_hand(["Ah", "Ad", "5h", "5s", "7h", "Jh"]) == Combination.TWO_PAIR
    assert evaluate_hand(["Ah", "Ad", "5h", "6h", "7h", "Jh"]) == Combination.FLUSH


# ---------------------------------------------------------------------------
# Canonicalization
# ---------------------------------------------------------------------------
def test_the_order_of_the_cards_does_not_matter() -> None:
    assert evaluate_hand(["Kd", "7h", "Ah", "Jc", "9d", "5s", "2c"]) == (
        evaluate_hand(["Ah", "9d", "2c", "5s", "7h", "Jc", "Kd"])
    )
