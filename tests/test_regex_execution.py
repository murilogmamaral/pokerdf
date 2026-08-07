"""Unit tests for the capture functions of regex_execution.

These functions orchestrate the RegexPatterns methods, so the tests focus on
the composition: expected keys, expected values and pydantic compatibility.
"""

import pandas as pd

from pokerdf.regex.regex_execution import (
    capture_common_data,
    capture_general_data_of_the_hand,
    capture_specific_data_of_the_player,
)
from pokerdf.validation.pydantic_modules import ValidateInput


def test_capture_common_data(first_hand: list[str]) -> None:
    result = capture_common_data(first_hand)
    assert result == {
        "Modality": ["USD Hold'em No Limit"],
        "TableSize": [3],
        "BuyIn": ["$1.84+$0.16"],
        "TournID": ["99999"],
        "Owner": ["garciamurilo"],
    }


def test_capture_general_data_of_the_hand(first_hand: list[str]) -> None:
    result = capture_general_data_of_the_hand(first_hand)
    assert result == {
        "HandID": ["11111"],
        "TableID": ["1"],
        "LocalTime": [pd.Timestamp("2020-10-11 03:22:15")],
        "Level": ["I"],
        "Ante": [None],
        "Blinds": [[10.0, 20.0]],
        "OwnersHand": [("3s", "Jh")],
        "Playing": [3],
        "BoardFlop": [()],
        "BoardTurn": [()],
        "BoardRiver": [()],
    }


def test_capture_specific_data_of_the_player(showdown_hand: list[str]) -> None:
    result = capture_specific_data_of_the_player(showdown_hand, "garciamurilo")
    assert result["Player"] == ["garciamurilo"]
    assert result["Seat"] == [2]
    assert result["Position"] == ["small blind"]
    assert result["Stack"] == [560.0]
    assert result["Bounty"] == [None]
    assert result["PostedBlind"] == [10.0]
    assert result["PostedAnte"] == [None]
    assert result["PreflopAction"] == [[("calls", "10")]]
    assert result["FlopAction"] == [[("checks", "")]]
    assert result["TurnAction"] == [[("checks", "")]]
    assert result["RiverAction"] == [[("checks", "")]]
    assert result["AnteAllIn"] == [False]
    assert result["PreflopAllIn"] == [False]
    assert result["FlopAllIn"] == [False]
    assert result["TurnAllIn"] == [False]
    assert result["RiverAllIn"] == [False]
    assert result["ShowDown"] == [("8h", "Kh")]
    assert result["CardCombination"] == ["a pair of Jacks"]
    assert result["Result"] == ["won"]
    assert result["Balance"] == [40.0]
    assert result["UncalledReturned"] == [None]
    assert result["BountyWon"] == [None]
    assert result["FinalRank"] == [-1]
    assert result["Prize"] == [None]


def test_captured_data_is_compatible_with_pydantic_validation(
    first_hand: list[str],
) -> None:
    # The three capture functions together must produce exactly the fields
    # expected by ValidateInput, with types that pass validation
    common = capture_common_data(first_hand)
    general = capture_general_data_of_the_hand(first_hand)
    specific = capture_specific_data_of_the_player(first_hand, "garciamurilo")
    collected_data = {**common, **general, **specific}
    assert set(collected_data.keys()) == set(ValidateInput.model_fields.keys())
    ValidateInput(**collected_data)
