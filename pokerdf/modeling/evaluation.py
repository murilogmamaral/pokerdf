"""Evaluation of poker hands: the best combination a set of cards makes.

The evaluator answers one question: given the cards a player can use — the
hole cards plus the community cards visible at a given moment — what is the
best made hand among them? On preflop that is at most a pair (two cards), on
the flop a five-card hand, and on the turn and river the best five out of
six or seven cards.

Only the category of the combination is ranked (a flush beats a straight),
not the kickers inside a category: the goal is a feature that describes the
strength of a holding at each moment of the hand, not a showdown referee —
the winner of each pot is already in the converted data.

Every classification looks at the same two summaries of the cards: how many
times each value repeats (pairs, trips, quads and full houses) and how many
cards share a suit (flushes), plus the search for five consecutive values
(straights, where the ace also plays low in A-2-3-4-5). The evaluation is
cached on the sorted cards, so a combination that repeats across rows — the
same holding evaluated on every action of a round — is only computed once.
"""

from collections import Counter
from collections.abc import Iterable
from enum import StrEnum
from functools import lru_cache

# Value of each rank character, as used in the hand histories ("T" is ten)
_CARD_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 11,
    "Q": 12,
    "K": 13,
    "A": 14,
}


class Combination(StrEnum):
    """Card combinations, declared from the weakest to the strongest."""

    HIGH_CARD = "High Card"
    ONE_PAIR = "One Pair"
    TWO_PAIR = "Two Pair"
    THREE_OF_A_KIND = "Three of a Kind"
    STRAIGHT = "Straight"
    FLUSH = "Flush"
    FULL_HOUSE = "Full House"
    FOUR_OF_A_KIND = "Four of a Kind"
    STRAIGHT_FLUSH = "Straight Flush"
    ROYAL_FLUSH = "Royal Flush"


# Score of each combination: its position in the declaration order, so
# 1 is a high card, 10 is a royal flush, and higher is always better
COMBINATION_SCORES = {
    combination: score for score, combination in enumerate(Combination, start=1)
}


def _straight_high(values: set[int]) -> int | None:
    """
    Find the highest card of the best straight among the values.

    Args:
        values (set[int]): Distinct card values available.

    Returns:
        int | None: Value of the highest card of the straight (5 for the
            wheel, where the ace plays low), or None if there is no straight.
    """
    # The ace also plays low in A-2-3-4-5
    if 14 in values:
        values = values | {1}

    # From the highest possible straight down, so the first hit is the best
    for high in range(14, 4, -1):
        if all(value in values for value in range(high - 4, high + 1)):
            return high

    return None


@lru_cache(maxsize=None)
def _evaluate(cards: tuple[str, ...]) -> Combination:
    """
    Classify the best combination of an already-canonical tuple of cards.

    Args:
        cards (tuple[str, ...]): Sorted cards like ("Ah", "Kd", ...), each one
            a rank character followed by a suit character. Sorting is what
            makes the cache key canonical: evaluate_hand takes care of it.

    Returns:
        Combination: The best combination the cards make.
    """
    values = [_CARD_VALUES[card[0]] for card in cards]
    suits = [card[1] for card in cards]

    # How many times the most repeated values repeat (4 = quads, 3 = trips,
    # 2 = a pair; a second group >= 2 completes a full house or a two pair)
    groups = sorted(Counter(values).values(), reverse=True)
    largest = groups[0]
    second = groups[1] if len(groups) > 1 else 0

    # The suit with five or more cards, when there is one
    flush_suit, flush_count = Counter(suits).most_common(1)[0]

    # A straight among the cards of the flush suit is a straight flush,
    # royal when it is ace-high
    if flush_count >= 5:
        flush_values = {
            value for value, suit in zip(values, suits) if suit == flush_suit
        }
        straight_flush_high = _straight_high(flush_values)
        if straight_flush_high == 14:
            return Combination.ROYAL_FLUSH
        if straight_flush_high is not None:
            return Combination.STRAIGHT_FLUSH

    # From the strongest category down, so the first match is the best hand
    if largest == 4:
        return Combination.FOUR_OF_A_KIND
    if largest == 3 and second >= 2:
        return Combination.FULL_HOUSE
    if flush_count >= 5:
        return Combination.FLUSH
    if _straight_high(set(values)) is not None:
        return Combination.STRAIGHT
    if largest == 3:
        return Combination.THREE_OF_A_KIND
    if largest == 2 and second == 2:
        return Combination.TWO_PAIR
    if largest == 2:
        return Combination.ONE_PAIR

    return Combination.HIGH_CARD


def evaluate_hand(cards: Iterable[str]) -> Combination:
    """
    Classify the best combination a player's available cards make.

    Args:
        cards (Iterable[str]): The cards the player can use — the hole cards
            plus the community cards visible at the moment (none on preflop,
            three on the flop, four on the turn, five on the river). Each
            card is a rank character followed by a suit character ("Ah").

    Returns:
        Combination: The best combination the cards make. With fewer than
            five cards, only a pair or a high card is possible.
    """
    # Sorting canonicalizes the cache key: the same cards in any order are
    # the same hand
    return _evaluate(tuple(sorted(cards)))
