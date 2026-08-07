"""Shared fixtures for the test suite.

All fixtures are built from the hand history files in tests/input (a real
anonymized tournament and a synthetic knockout tournament), processed exactly
like the package does: the raw text is split into hands by the platform
marker, and each hand is split into stages by "\n*** ".
"""

from pathlib import Path
from typing import Callable

import pytest

from pokerdf.utils.strings import PLATFORM

FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250516 T99999 No Limit Hold_em US$ 1,84 + US$ 0,16.txt"
)


@pytest.fixture(scope="session")
def tournament_text() -> str:
    """Raw text of the tournament hand history file."""
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def hands(tournament_text: str) -> list[str]:
    """List of hands as text, split the same way apply_regex does."""
    chunks = tournament_text.split(f"{PLATFORM} ")
    return [chunk for chunk in chunks if chunk]


@pytest.fixture(scope="session")
def get_hand(hands: list[str]) -> Callable[[str], list[str]]:
    """Return a helper that finds a hand by ID and splits it into stages."""

    def _get_hand(hand_id: str) -> list[str]:
        hand = next(h for h in hands if h.startswith(f"Hand #{hand_id}:"))
        return hand.split("\n*** ")

    return _get_hand


@pytest.fixture(scope="session")
def first_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """First hand of the tournament: 3 players, everyone folds preflop."""
    return get_hand("11111")


@pytest.fixture(scope="session")
def flop_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """Hand that reaches the flop: VillainB raises preflop and bets the flop."""
    return get_hand("219269851097")


@pytest.fixture(scope="session")
def showdown_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """Hand that reaches showdown: garciamurilo wins with a pair of Jacks."""
    return get_hand("219269866589")


@pytest.fixture(scope="session")
def allin_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """Hand where VillainA goes all-in preflop."""
    return get_hand("219269873773")


@pytest.fixture(scope="session")
def elimination_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """Hand where VillainA is eliminated in 3rd place."""
    return get_hand("219269879108")


@pytest.fixture(scope="session")
def final_hand(get_hand: Callable[[str], list[str]]) -> list[str]:
    """Last hand: garciamurilo wins the tournament and receives the prize."""
    return get_hand("219269977250")


KO_FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250517 T88888 Bounty Hold_em US$ 0,98 + US$ 0,25 + US$ 0,16.txt"
)


@pytest.fixture(scope="session")
def ko_tournament_text() -> str:
    """Raw text of the knockout tournament hand history file."""
    return KO_FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def get_ko_hand(ko_tournament_text: str) -> Callable[[str], list[str]]:
    """Return a helper that finds a knockout hand by ID and splits it into stages."""

    def _get_ko_hand(hand_id: str) -> list[str]:
        chunks = ko_tournament_text.split(f"{PLATFORM} ")
        hand = next(h for h in chunks if h.startswith(f"Hand #{hand_id}:"))
        return hand.split("\n*** ")

    return _get_ko_hand


@pytest.fixture(scope="session")
def single_card_show_hand(get_ko_hand: Callable[[str], list[str]]) -> list[str]:
    """VillainB wins uncontested and voluntarily shows a single card."""
    return get_ko_hand("22219")


@pytest.fixture(scope="session")
def side_pot_hand(get_ko_hand: Callable[[str], list[str]]) -> list[str]:
    """Side pot: VillainA is all-in, the others keep betting a side pot."""
    return get_ko_hand("22220")


@pytest.fixture(scope="session")
def pko_elimination_hand(get_ko_hand: Callable[[str], list[str]]) -> list[str]:
    """Progressive knockout: garciamurilo eliminates VillainA, partial bounty."""
    return get_ko_hand("22221")


@pytest.fixture(scope="session")
def ko_final_hand(get_ko_hand: Callable[[str], list[str]]) -> list[str]:
    """Regular knockout finale: garciamurilo wins VillainB's whole bounty."""
    return get_ko_hand("22222")


SATELLITE_FIXTURE_PATH = (
    Path(__file__).parent
    / "input"
    / "HH20250518 T77777 Satellite Hold_em US$ 0,89 + US$ 0,11.txt"
)


@pytest.fixture(scope="session")
def satellite_tournament_text() -> str:
    """Raw text of the satellite tournament hand history file."""
    return SATELLITE_FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def satellite_final_hand(satellite_tournament_text: str) -> list[str]:
    """Satellite finale: a ticket prize, a 2nd place and a placeless finish."""
    chunks = satellite_tournament_text.split(f"{PLATFORM} ")
    hand = next(h for h in chunks if h.startswith("Hand #33333:"))
    return hand.split("\n*** ")


@pytest.fixture(scope="session")
def no_showdown_elimination_hand(satellite_tournament_text: str) -> list[str]:
    """VillainF folds an all-in blind post and is eliminated with no showdown."""
    chunks = satellite_tournament_text.split(f"{PLATFORM} ")
    hand = next(h for h in chunks if h.startswith("Hand #33332:"))
    return hand.split("\n*** ")
