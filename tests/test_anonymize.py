"""Unit tests for the GDPR anonymization of the modeled data.

The tests pin both halves of the contract: what must no longer be there
(identifiers, timestamps, private cards) and what must survive untouched,
since an anonymized dataset that cannot be analyzed is useless.
"""

import pandas as pd

from pokerdf.modeling.anonymize import (
    DROPPED_COLUMNS,
    OWNER_CARD_COLUMNS,
    PSEUDONYMIZED_COLUMNS,
    GdprMode,
    anonymize_table,
    describe,
    generate_salt,
    pseudonymize,
)
from pokerdf.modeling.star_schema import build_dim_hand, build_dim_tournament

# The owner of the fixture, as written in the Player column of the fact
OWNER = "garciamurilo"


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


def test_pseudonymize_spares_the_kept_values() -> None:
    values = pd.Series(["garciamurilo", "VillainA"])

    result = pseudonymize(values, "salt", keep={"garciamurilo"})

    assert result[0] == "garciamurilo"
    assert result[1] != "VillainA"


def test_generate_salt_is_random() -> None:
    assert generate_salt() != generate_salt()


# ---------------------------------------------------------------------------
# anonymize_table: full mode
# ---------------------------------------------------------------------------
def test_full_mode_keeps_the_owner_cards(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.FULL)

    # The hole cards of the owner carry the analytical value of the dataset,
    # so they survive every mode
    for column in OWNER_CARD_COLUMNS:
        assert column in result.columns
        pd.testing.assert_series_equal(result[column], fact[column])


def test_full_mode_pseudonymizes_the_identifiers(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.FULL)

    for column in PSEUDONYMIZED_COLUMNS:
        # No original value survives
        assert set(result[column]).isdisjoint(set(fact[column]))
        # And the cardinality is preserved, so nothing was merged
        assert result[column].nunique() == fact[column].nunique()


def test_full_mode_pseudonymizes_the_owner_column(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.FULL)

    # The Owner column no longer carries the nickname, and the owner
    # receives the same pseudonym there and in the Player column
    assert OWNER not in set(result["Owner"])
    owner_rows = fact["Player"] == OWNER
    assert (result.loc[owner_rows, "Player"] == result.loc[owner_rows, "Owner"]).all()


def test_full_mode_gives_the_owner_matching_pseudonyms() -> None:
    # Both columns hold the nickname exactly as the platform wrote it, so
    # the same person receives the same pseudonym in both — also when the
    # nickname contains characters that are special to a regex
    fact = pd.DataFrame(
        {
            "TournID": ["1", "1"],
            "HandID": ["2", "2"],
            "Player": ["Villain.One", "VillainTwo"],
            "Owner": ["Villain.One", "Villain.One"],
        }
    )

    result = anonymize_table(fact, "salt", GdprMode.FULL)

    assert result["Player"][0] == result["Owner"][0]
    assert result["Player"][1] != result["Owner"][1]


def test_full_mode_anonymizes_the_hand_dimension_consistently(
    fact: pd.DataFrame, source_df: pd.DataFrame
) -> None:
    dim = build_dim_hand(source_df)

    anonymized_fact = anonymize_table(fact, "salt", GdprMode.FULL)
    anonymized_dim = anonymize_table(dim, "salt", GdprMode.FULL)

    # The identifiers are pseudonymized, and the same salt keeps the
    # dimension joining with the fact
    assert set(anonymized_dim["TournID"]) == set(anonymized_fact["TournID"])
    assert set(anonymized_dim["HandID"]) == set(anonymized_fact["HandID"])
    assert set(anonymized_dim["Owner"]) == set(anonymized_fact["Owner"])
    # The timestamp is removed; every other attribute survives whole
    assert "LocalTime" not in anonymized_dim.columns
    for column in ["TableSize", "Playing", "Level", "Ante", "SmallBlind", "BigBlind"]:
        pd.testing.assert_series_equal(anonymized_dim[column], dim[column])


def test_time_columns_are_removed_from_every_table(source_df: pd.DataFrame) -> None:
    # Any column of time identifies the tournament when matched against
    # public schedules: LocalTime leaves dim_hand, LocalStartTime leaves
    # dim_tournament
    hand = anonymize_table(build_dim_hand(source_df), "salt", GdprMode.FULL)
    tournament = anonymize_table(build_dim_tournament(source_df), "salt", GdprMode.FULL)

    for column in DROPPED_COLUMNS:
        assert column not in hand.columns
        assert column not in tournament.columns


def test_full_mode_keeps_the_hand_reconstruction(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.FULL)

    # Everything that makes the dataset analytically useful is untouched
    preserved = [
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


def test_full_mode_keeps_rows_of_a_hand_together(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.FULL)

    # The pseudonym must be stable inside a hand, otherwise the rows of the
    # same hand would no longer group together
    original_sizes = sorted(fact.groupby("HandID").size())
    anonymized_sizes = sorted(result.groupby("HandID").size())
    assert original_sizes == anonymized_sizes


def test_full_mode_does_not_mutate_the_input(fact: pd.DataFrame) -> None:
    before = fact.copy()

    anonymize_table(fact, "salt", GdprMode.FULL)

    pd.testing.assert_frame_equal(fact, before)


# ---------------------------------------------------------------------------
# anonymize_table: keep-owner mode
# ---------------------------------------------------------------------------
def test_keep_owner_mode_spares_the_owner(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.KEEP_OWNER, owners={OWNER})

    # The owner keeps their nickname; every third party is pseudonymized
    players = set(result["Player"])
    assert OWNER in players
    assert players - {OWNER} == set(
        pseudonymize(fact["Player"], "salt", keep={OWNER})
    ) - {OWNER}
    assert set(fact["Player"]) - {OWNER} == {"VillainA", "VillainB"}
    assert players.isdisjoint({"VillainA", "VillainB"})


def test_keep_owner_mode_keeps_the_owner_column(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.KEEP_OWNER, owners={OWNER})

    # The owner is identified by choice of the mode, in both columns
    assert (result["Owner"] == OWNER).all()


def test_keep_owner_mode_keeps_the_owner_cards(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.KEEP_OWNER, owners={OWNER})

    for column in OWNER_CARD_COLUMNS:
        assert column in result.columns
        pd.testing.assert_series_equal(result[column], fact[column])


def test_keep_owner_mode_still_protects_third_parties(fact: pd.DataFrame) -> None:
    result = anonymize_table(fact, "salt", GdprMode.KEEP_OWNER, owners={OWNER})

    # Identifiers are treated exactly like in full mode
    assert set(result["TournID"]).isdisjoint(set(fact["TournID"]))
    assert set(result["HandID"]).isdisjoint(set(fact["HandID"]))


# ---------------------------------------------------------------------------
# describe
# ---------------------------------------------------------------------------
def test_describe_reports_the_transformations() -> None:
    report = describe(GdprMode.FULL, reused_salt=False)

    assert "full" in report
    for column in [*PSEUDONYMIZED_COLUMNS, *DROPPED_COLUMNS, *OWNER_CARD_COLUMNS]:
        assert str(column) in report
    assert "Residual risks" in report


def test_describe_distinguishes_the_modes() -> None:
    full = describe(GdprMode.FULL, reused_salt=False)
    keep_owner = describe(GdprMode.KEEP_OWNER, reused_salt=False)

    assert "the pseudonym that appears in all of them is the owner" in full
    assert "the owner is identified in this dataset" in keep_owner


def test_describe_distinguishes_a_reused_salt() -> None:
    random_salt = describe(GdprMode.FULL, reused_salt=False)
    given_salt = describe(GdprMode.FULL, reused_salt=True)

    assert "irreversible" in random_salt
    assert "reproducible" in given_salt


def test_gdpr_mode_lists_the_available_modes() -> None:
    assert [mode.value for mode in GdprMode] == ["full", "keep-owner"]
