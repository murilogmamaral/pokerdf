"""Unit tests for the centralized column and table names.

These tests pin the contract between the enums and the rest of the package:
the literals here are intentional, so any accidental rename is caught.
"""

from pokerdf.core.read_and_convert import compose_dataframe
from pokerdf.utils.columns import Column, ModelTable, Round
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


def test_model_table_lists_the_three_tables_of_the_star_schema() -> None:
    assert [table.value for table in ModelTable] == [
        "fact_player_actions",
        "dim_tourn_summary",
        "dim_final_rank",
    ]
