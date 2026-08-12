"""GDPR anonymization of the modeled data, so a dataset can be shared.

A hand history carries personal data of third parties as defined by
Article 4(1) of the GDPR: the nicknames of the other players at the table
are online identifiers of natural persons, the tournament and hand
identifiers link each row back to the records of the platform, and the
timestamps allow a hand to be correlated with publicly available
tournament results.

Two GDPR principles guide what is done here:

- Data minimisation (Article 5(1)(c)): what identifies without helping the
  analysis is not produced — the final-rank dimension, which mirrors
  publicly available tournament results, is not generated.
- Pseudonymisation (Article 4(5)): the identifiers that structure the data
  are replaced by salted digests, which keep the dataset consistent without
  pointing back to a person.

The transformations are applied to each generated table after it is built,
with the same salt, so the reconstruction of the hand (order of the
actions, amounts, pot, stacks and the context they are read against) is
unaffected and the tables keep joining: what changes is only what allows a
person to be identified.
"""

import hashlib
import secrets
from collections.abc import Iterable
from enum import StrEnum

import pandas as pd

from pokerdf.utils.columns import Column, ModelColumn


class GdprMode(StrEnum):
    """GDPR anonymization modes accepted by the modeling command."""

    # Everyone is anonymized, including the owner of the logs
    FULL = "full"

    # Third parties are anonymized; the owner keeps their nickname and their
    # own hole cards, for datasets where the owner's game is the subject
    KEEP_OWNER = "keep-owner"


# Size of the pseudonym digest. Eight bytes (16 hexadecimal characters) keep
# the chance of a collision negligible for the cardinalities involved here
DIGEST_SIZE = 8

# Columns whose value is replaced by a pseudonym. They keep every join and
# every group by inside the dataset working, while no longer pointing back
# to a person or to a hand that can be looked up on the platform
PSEUDONYMIZED_COLUMNS = [Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]

# Removed in every mode, from whichever table carries them. A timestamp
# matched against publicly available tournament schedules and results
# identifies the tournament, re-identifying the players in it; the time
# zone of the player is a rough statement of where they live
DROPPED_COLUMNS: list[StrEnum] = [
    Column.HAND_START_TIME_CET,
    Column.HAND_START_TIME_LOCAL,
    Column.HAND_TIMEZONE,
    ModelColumn.TOURN_FIRST_HAND_TIME_CET,
    ModelColumn.TOURN_FIRST_HAND_TIME_LOCAL,
    ModelColumn.TOURN_TIMEZONE,
]

# The private cards of the owner, repeated on every row of the hand. They
# are kept in every mode: the decisions in the dataset can only be studied
# against the holding they were made with, so removing them would strip the
# analytical value the dataset exists for. Named here for the report
OWNER_CARD_COLUMNS = [ModelColumn.OWNER_C1, ModelColumn.OWNER_C2]


def generate_salt() -> str:
    """
    Generate a random salt for the pseudonyms.

    A salt that is not stored anywhere makes the pseudonyms irreversible:
    without it, a nickname cannot be confirmed by hashing a guess and
    comparing the result, which is exactly what a dictionary attack does.

    Returns:
        str: Cryptographically secure random salt, as a hexadecimal string.
    """
    return secrets.token_hex(16)


def pseudonymize(values: pd.Series, salt: str, keep: Iterable[str] = ()) -> pd.Series:
    """
    Replace each value by a salted digest, keeping equal values equal.

    Args:
        values (pd.Series): Values to pseudonymize. Nulls are preserved.
        salt (str): Salt prepended to every value before hashing.
        keep (Iterable[str]): Values left untouched (for example, the owner
            of the logs in keep-owner mode).

    Returns:
        pd.Series: Series of digests, where the same input always produces
            the same output for a given salt.
    """
    kept = set(keep)

    # Only the distinct values are hashed: a player appears in thousands of
    # rows, and hashing each row would repeat the same work
    mapping = {
        value: hashlib.blake2b(
            f"{salt}{value}".encode(), digest_size=DIGEST_SIZE
        ).hexdigest()
        for value in values.dropna().unique()
        if value not in kept
    }

    # Values without a digest (nulls and the kept ones) stay as they are
    digests = values.map(mapping)
    return digests.where(digests.notna(), values)


def anonymize_table(
    table: pd.DataFrame,
    salt: str,
    mode: GdprMode,
    owners: Iterable[str] = (),
) -> pd.DataFrame:
    """
    Apply the GDPR transformations of a mode to a table of the star schema.

    The same function anonymizes every table that leaves: each
    transformation applies to the columns the table happens to have, and
    the same salt gives the same pseudonyms in all of them, so they keep
    joining.

    Args:
        table (pd.DataFrame): Any table of the star schema.
        salt (str): Salt used to derive the pseudonyms.
        mode (GdprMode): In FULL mode the nickname of the owner is
            pseudonymized like everyone else's, in the Player and Owner
            columns alike; in KEEP_OWNER mode the owner keeps it in both.
            The hole cards of the owner are kept in every mode.
        owners (Iterable[str]): Names of the owners of the logs, as they
            appear in the Player column. Only used in KEEP_OWNER mode.

    Returns:
        pd.DataFrame: The same table with the identifying columns replaced
            by pseudonyms, and the moments and the time zone removed.
            Every other attribute survives whole.
    """
    anonymized = table.copy()
    keep_owner = mode == GdprMode.KEEP_OWNER

    # Replace the identifiers by pseudonyms, sparing the owner when kept
    for column in PSEUDONYMIZED_COLUMNS:
        if column not in anonymized.columns:
            continue
        keep = set(owners) if keep_owner and column == Column.PLAYER else set()
        anonymized[column] = pseudonymize(anonymized[column], salt, keep=keep)

    # The Owner column names whose archive logged the hand. It stays in
    # keep-owner mode; in full mode it is pseudonymized like any other
    # nickname, so the owner receives the same pseudonym here and in the
    # Player column
    if not keep_owner and Column.OWNER in anonymized.columns:
        anonymized[Column.OWNER] = pseudonymize(anonymized[Column.OWNER], salt)

    # Remove the moments and the time zone: neither can be pseudonymized
    # without losing its meaning, and kept they point at the tournament and
    # at where the owner lives
    return anonymized.drop(
        columns=[column for column in DROPPED_COLUMNS if column in anonymized.columns]
    )


def describe(mode: GdprMode, reused_salt: bool) -> str:
    """
    Describe the applied transformations, to be saved next to the data.

    Being able to show what was removed, what was replaced and what remains
    is part of complying with a data protection regulation, and it also
    tells whoever receives the dataset what they can and cannot expect
    from it.

    Args:
        mode (GdprMode): GDPR mode that was applied.
        reused_salt (bool): Whether the salt was informed by the user
            instead of randomly generated for this session.

    Returns:
        str: Report of the transformations and of the residual risks.
    """
    keep_owner = mode == GdprMode.KEEP_OWNER
    pseudonymized = ", ".join(str(column) for column in PSEUDONYMIZED_COLUMNS)
    owner_cards = ", ".join(str(column) for column in OWNER_CARD_COLUMNS)

    # One column per line: the report is plain text and the names are long
    dropped = "\n".join(f"    {column}" for column in DROPPED_COLUMNS)

    owner_line = (
        f"- Kept in every mode: the hole cards of the owner ({owner_cards}),\n"
        f"  which carry the analytical value of the dataset. Kept by choice of\n"
        f"  the keep-owner mode: the nickname of the owner, in the Owner column\n"
        f"  and in the Player column. The GDPR restricts what is shared\n"
        f"  about third parties, not what the owner shares about themselves:\n"
        f"  the owner is identified in this dataset."
        if keep_owner
        else f"- Kept in every mode: the hole cards of the owner ({owner_cards}),\n"
        f"  which carry the analytical value of the dataset. The nickname of\n"
        f"  the owner is pseudonymized like everyone else's, receiving the\n"
        f"  same pseudonym in the Owner column and in the Player column."
    )
    owner_risk = (
        "- The owner of the logs is identified by design, and every hand of\n"
        "  the archive is a hand the owner played."
        if keep_owner
        else "- The owner of the logs plays in every hand of their own archive, so\n"
        "  the pseudonym that appears in all of them is the owner. Pseudonymizing\n"
        "  does not hide this - and since the hole cards of the owner are kept\n"
        "  on every row, that pseudonym is linked to the holdings it played.\n"
        "  The same frequency reasoning applies to any player who stands out."
    )
    salt_line = (
        "Salt: informed by the user, so the pseudonyms are reproducible across\n"
        "sessions. Under Recital 26 of the GDPR the result remains pseudonymized\n"
        "personal data, not anonymous data: anyone holding the salt can confirm\n"
        "a nickname by hashing it, so the salt must be kept as securely as the\n"
        "original files."
        if reused_salt
        else "Salt: randomly generated for this session and not stored, so the\n"
        "pseudonyms are irreversible and cannot be reproduced in another run."
    )

    return f"""GDPR anonymization report
=========================

Mode: {mode}

Applied
-------
- The final-rank dimension was not generated (data minimisation, Article
  5(1)(c)): the nickname, final rank and prize of every player mirror
  publicly available tournament results, the easiest re-identification
  path there is.
- The fact table, the hand dimension and the tournament dimension leave
  with their identifiers pseudonymized with a salted BLAKE2b digest
  (Article 4(5)): {pseudonymized}. The same salt is used in every
  table, so the pseudonyms keep joining across them.
- Removed from every table that carries them:

{dropped}

  A timestamp matched against publicly available tournament schedules and
  results identifies the tournament, and the time zone of the player says
  roughly where they live. Every other attribute leaves whole.
- Kept in every mode: the cards the players revealed, at showdown or
  voluntarily (RevealedC1, RevealedC2), the combinations derived from the
  cards and the board (OwnerCombination, RevealedCombination and their
  scores) and the combination the platform named at showdown
  (RevealedPokerHand). They were shown at the table, and once the
  player holding them is pseudonymized they describe the game, not a
  person.
{owner_line}

{salt_line}

Residual risks
--------------
{owner_risk}
- A hand is still described by its board and by the exact sequence and size
  of the bets, which is close to unique. Someone holding another copy of the
  same hand can match it and recover the identifiers from there.
- The values in chips, the levels, the size of the table, the modality and
  the buy-in are preserved, as removing them would leave the dataset
  without analytical value.

Nothing here replaces assessing, for your own case, whether sharing this
data is lawful.
"""
