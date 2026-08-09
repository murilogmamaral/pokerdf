"""Anonymization of the modeled data, so a dataset can be shared.

A hand history carries personal data of third parties: the nicknames of the
other players at the table, the identifiers that link a hand back to the
records of the platform, and the timestamps that allow a hand to be
correlated with publicly available tournament results.

The transformations here are applied to the fact table after it is built,
so the reconstruction of the hand (order of the actions, amounts, pot and
stacks) is unaffected: what changes is only what allows a person to be
identified.
"""

import hashlib
import secrets
from enum import StrEnum

import pandas as pd

from pokerdf.utils.columns import Column, ModelColumn


class AnonymizationMode(StrEnum):
    """Anonymization modes accepted by the modeling command."""

    RGPD = "rgpd"


# Size of the pseudonym digest. Eight bytes (16 hexadecimal characters) keep
# the chance of a collision negligible for the cardinalities involved here
DIGEST_SIZE = 8

# Columns whose value is replaced by a pseudonym. They keep every join and
# every group by inside the dataset working, while no longer pointing back
# to a person or to a hand that can be looked up on the platform
PSEUDONYMIZED_COLUMNS = [Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]

# Columns removed entirely. The timestamp allows a hand to be matched against
# public tournament results, and the cards of the owner of the logs are their
# own private holding, repeated on every row of the hand
DROPPED_COLUMNS = [Column.LOCAL_TIME, ModelColumn.OWNER_C1, ModelColumn.OWNER_C2]


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


def pseudonymize(values: pd.Series, salt: str) -> pd.Series:
    """
    Replace each value by a salted digest, keeping equal values equal.

    Args:
        values (pd.Series): Values to pseudonymize. Nulls are preserved.
        salt (str): Salt prepended to every value before hashing.

    Returns:
        pd.Series: Series of digests, where the same input always produces
            the same output for a given salt.
    """
    # Only the distinct values are hashed: a player appears in thousands of
    # rows, and hashing each row would repeat the same work
    mapping = {
        value: hashlib.blake2b(
            f"{salt}{value}".encode(), digest_size=DIGEST_SIZE
        ).hexdigest()
        for value in values.dropna().unique()
    }

    return values.map(mapping)


def anonymize_fact(fact: pd.DataFrame, salt: str) -> pd.DataFrame:
    """
    Apply the RGPD transformations to the fact table.

    Args:
        fact (pd.DataFrame): Fact table built by build_fact_player_actions.
        salt (str): Salt used to derive the pseudonyms.

    Returns:
        pd.DataFrame: The same table with the identifying columns replaced by
            pseudonyms and the columns of DROPPED_COLUMNS removed.
    """
    anonymized = fact.copy()

    # Replace the identifiers by pseudonyms
    for column in PSEUDONYMIZED_COLUMNS:
        anonymized[column] = pseudonymize(anonymized[column], salt)

    # Remove what cannot be pseudonymized without losing its meaning
    return anonymized.drop(
        columns=[column for column in DROPPED_COLUMNS if column in anonymized.columns]
    )


def describe(mode: str, reused_salt: bool) -> str:
    """
    Describe the applied transformations, to be saved next to the data.

    Being able to show what was removed, what was replaced and what remains
    is part of complying with a data protection regulation, and it also
    tells whoever receives the dataset what they can and cannot expect
    from it.

    Args:
        mode (str): Anonymization mode that was applied.
        reused_salt (bool): Whether the salt was informed by the user
            instead of randomly generated for this session.

    Returns:
        str: Report of the transformations and of the residual risks.
    """
    pseudonymized = ", ".join(str(column) for column in PSEUDONYMIZED_COLUMNS)
    dropped = ", ".join(str(column) for column in DROPPED_COLUMNS)
    salt_line = (
        "Salt: informed by the user, so the pseudonyms are reproducible across "
        "sessions.\nAnyone holding the salt can confirm a nickname by hashing "
        "it, so it must be kept as securely as the original data."
        if reused_salt
        else "Salt: randomly generated for this session and not stored, so the "
        "pseudonyms are irreversible and cannot be reproduced in another run."
    )

    return f"""Anonymization report
====================

Mode: {mode}

Applied
-------
- Dimension tables were not generated. They carry the nickname of the owner
  of the logs, the buy-in paid, the cards revealed at showdown, the final
  rank and the prizes received.
- Pseudonymized with a salted BLAKE2b digest: {pseudonymized}.
- Removed: {dropped}.

{salt_line}

Residual risks
--------------
- The owner of the logs plays in every hand of their own archive, so the
  pseudonym that appears in all of them is the owner. Pseudonymizing does
  not hide this, and the same reasoning applies to any player whose
  frequency stands out.
- A hand is still described by its board and by the exact sequence and size
  of the bets, which is close to unique. Someone holding another copy of the
  same hand can match it and recover the identifiers from there.
- The values in chips, the levels and the size of the table are preserved,
  as removing them would leave the dataset without analytical value.

Nothing here replaces assessing, for your own case, whether sharing this
data is lawful.
"""
