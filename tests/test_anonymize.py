"""Unit tests for the anonymization of the modeled data.

The tests pin both halves of the contract: what must no longer be there
(identifiers, timestamps, private cards) and what must survive untouched,
since an anonymized dataset that cannot be analyzed is useless.
"""

import pandas as pd

from pokerdf.modeling.anonymize import (
    DROPPED_COLUMNS,
    PSEUDONYMIZED_COLUMNS,
    AnonymizationMode,
    anonymize_fact,
    describe,
    generate_salt,
    pseudonymize,
)


# ---------------------------------------------------------------------------
# pseudonymize
# ---------------------------------------------------------------------------
def test_pseudonymize_is_deterministic_for_the_same_salt() -> None:
    values = pd.Series(["garciamurilo", "VillainA", "garciamurilo"])

    result = pseudonymize(values, "salt")

    # The same nickname always becomes the same pseudonym, so the data can
    # still be grouped by player
    assert result[0] == result[2]
    assert result[0] != result[1]
    assert result.equals(pseudonymize(values, "salt"))


def test_pseudonymize_changes_with_the_salt() -> None:
    values = pd.Series(["garciamurilo"])

    assert pseudonymize(values, "one")[0] != pseudonymize(values, "another")[0]


def test_pseudonymize_hides_the_original_value() -> None:
    result = pseudonymize(pd.Series(["garciamurilo"]), "salt")

    assert "garciamurilo" not in result[0]
    # 8 bytes rendered as hexadecimal
    assert len(result[0]) == 16


def test_pseudonymize_preserves_nulls() -> None:
    result = pseudonymize(pd.Series(["VillainA", None]), "salt")

    assert pd.isna(result[1])


def test_generate_salt_is_random() -> None:
    assert generate_salt() != generate_salt()


# ---------------------------------------------------------------------------
# anonymize_fact
# ---------------------------------------------------------------------------
def test_anonymize_fact_removes_the_identifying_columns(fact: pd.DataFrame) -> None:
    result = anonymize_fact(fact, "salt")

    for column in DROPPED_COLUMNS:
        assert column not in result.columns


def test_anonymize_fact_pseudonymizes_the_identifiers(fact: pd.DataFrame) -> None:
    result = anonymize_fact(fact, "salt")

    for column in PSEUDONYMIZED_COLUMNS:
        # No original value survives
        assert set(result[column]).isdisjoint(set(fact[column]))
        # And the cardinality is preserved, so nothing was merged
        assert result[column].nunique() == fact[column].nunique()


def test_anonymize_fact_keeps_the_hand_reconstruction(fact: pd.DataFrame) -> None:
    result = anonymize_fact(fact, "salt")

    # Everything that makes the dataset analytically useful is untouched
    preserved = [
        "TableSize",
        "Playing",
        "Level",
        "Ante",
        "SmallBlind",
        "BigBlind",
        "Round",
        "Seat",
        "Position",
        "Stack",
        "Action",
        "ActionOrder",
        "AddedValue",
        "TotalValue",
        "TotalPot",
        "BoardC1",
    ]
    for column in preserved:
        assert column in result.columns
        pd.testing.assert_series_equal(result[column], fact[column])
    assert len(result) == len(fact)


def test_anonymize_fact_keeps_rows_of_a_hand_together(fact: pd.DataFrame) -> None:
    result = anonymize_fact(fact, "salt")

    # The pseudonym must be stable inside a hand, otherwise the rows of the
    # same hand would no longer group together
    original_sizes = sorted(fact.groupby("HandID").size())
    anonymized_sizes = sorted(result.groupby("HandID").size())
    assert original_sizes == anonymized_sizes


def test_anonymize_fact_does_not_mutate_the_input(fact: pd.DataFrame) -> None:
    before = fact.copy()

    anonymize_fact(fact, "salt")

    pd.testing.assert_frame_equal(fact, before)


# ---------------------------------------------------------------------------
# describe
# ---------------------------------------------------------------------------
def test_describe_reports_the_transformations() -> None:
    report = describe(str(AnonymizationMode.RGPD), reused_salt=False)

    assert "rgpd" in report
    for column in [*PSEUDONYMIZED_COLUMNS, *DROPPED_COLUMNS]:
        assert str(column) in report
    assert "Residual risks" in report


def test_describe_distinguishes_a_reused_salt() -> None:
    random_salt = describe(str(AnonymizationMode.RGPD), reused_salt=False)
    given_salt = describe(str(AnonymizationMode.RGPD), reused_salt=True)

    assert "irreversible" in random_salt
    assert "reproducible" in given_salt


def test_anonymization_mode_lists_the_available_modes() -> None:
    assert [mode.value for mode in AnonymizationMode] == ["rgpd"]
