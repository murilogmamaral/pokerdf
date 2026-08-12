"""Unit tests for the centralized column and table names.

These tests pin the contract between the enums and the rest of the package:
the literals here are intentional, so any accidental rename is caught.
"""

from pokerdf.core.read_and_convert import compose_dataframe
from pokerdf.utils.columns import Column, HandResult, ModelTable, Round
from pokerdf.validation.pydantic_modules import ValidateInput


def test_column_matches_the_pydantic_validation_fields() -> None:
    # The converted schema and its validation model must mirror each other,
    # field by field and in the same order
    assert [column.value for column in Column] == list(
        ValidateInput.model_fields.keys()
    )


def test_column_matches_the_output_schema_order() -> None:
    assert list(compose_dataframe().columns) == list(Column)


def test_columns_behave_as_plain_strings() -> None:
    # StrEnum members must be usable anywhere a string is expected
    assert isinstance(Column.TOURN_ID, str)
    assert str(Column.TOURN_ID) == "TournID"
    assert f"{Column.TOURN_ID}" == "TournID"
    assert str(Round.PREFLOP) == "preflop"


def test_round_is_in_chronological_order() -> None:
    assert [round.value for round in Round] == ["preflop", "flop", "turn", "river"]


def test_hand_result_lists_the_five_ways_a_hand_can_end() -> None:
    assert [result.value for result in HandResult] == [
        "folded",
        "won without showdown",
        "won at showdown",
        "lost at showdown",
        "mucked at showdown",
    ]


def test_hand_result_keeps_its_two_naming_conventions() -> None:
    # The conventions the documentation promises: every win starts with
    # "won" and every showdown ends with "at showdown", so each of the
    # common filters is a single string predicate
    assert {result for result in HandResult if result.startswith("won")} == {
        HandResult.WON_WITHOUT_SHOWDOWN,
        HandResult.WON_AT_SHOWDOWN,
    }
    assert {result for result in HandResult if result.endswith("at showdown")} == {
        HandResult.WON_AT_SHOWDOWN,
        HandResult.LOST_AT_SHOWDOWN,
        HandResult.MUCKED_AT_SHOWDOWN,
    }


def test_model_table_lists_the_four_tables_of_the_star_schema() -> None:
    assert [table.value for table in ModelTable] == [
        "fact_player_action",
        "dim_tournament",
        "dim_hand",
        "dim_final_rank",
    ]
