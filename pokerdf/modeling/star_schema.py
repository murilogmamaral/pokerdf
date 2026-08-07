import os
from glob import glob
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.dataset

# Unified schema of the .parquet files produced by the convert command.
# Reading with an explicit schema is required because columns that are entirely
# empty in a tournament (for example, Prize) are saved with the "null" type,
# and the type must be unified before concatenating all files.
_ACTIONS = pa.list_(pa.list_(pa.string()))
_CARDS = pa.list_(pa.string())
SOURCE_SCHEMA = pa.schema(
    [
        ("Modality", pa.string()),
        ("TableSize", pa.int64()),
        ("BuyIn", pa.string()),
        ("TournID", pa.string()),
        ("TableID", pa.string()),
        ("HandID", pa.string()),
        ("LocalTime", pa.timestamp("ns")),
        ("Level", pa.string()),
        ("Ante", pa.float64()),
        ("Blinds", pa.list_(pa.float64())),
        ("Owner", pa.string()),
        ("OwnersHand", _CARDS),
        ("Playing", pa.int64()),
        ("Player", pa.string()),
        ("Seat", pa.int64()),
        ("PostedAnte", pa.float64()),
        ("Position", pa.string()),
        ("PostedBlind", pa.float64()),
        ("Stack", pa.float64()),
        ("PreflopAction", _ACTIONS),
        ("FlopAction", _ACTIONS),
        ("TurnAction", _ACTIONS),
        ("RiverAction", _ACTIONS),
        ("AnteAllIn", pa.bool_()),
        ("PreflopAllIn", pa.bool_()),
        ("FlopAllIn", pa.bool_()),
        ("TurnAllIn", pa.bool_()),
        ("RiverAllIn", pa.bool_()),
        ("BoardFlop", _CARDS),
        ("BoardTurn", _CARDS),
        ("BoardRiver", _CARDS),
        ("ShowDown", _CARDS),
        ("CardCombination", pa.string()),
        ("Result", pa.string()),
        ("Balance", pa.float64()),
        ("FinalRank", pa.int64()),
        ("Prize", pa.float64()),
    ]
)

# Mapping between the action columns of the converted data and the round names
ROUNDS = {
    "PreflopAction": "preflop",
    "FlopAction": "flop",
    "TurnAction": "turn",
    "RiverAction": "river",
}


def _roman_to_int(level: str | None) -> int | None:
    """
    Convert a tournament level to an integer (for example, "XXIX" -> 29).

    Args:
        level (str | None): Level as captured from the hand history, usually a
            roman numeral. Plain numeric strings are also accepted.

    Returns:
        int | None: The level as an integer, or None if it cannot be parsed.
    """
    if level is None:
        return None

    # Plain numeric levels are converted directly
    if level.isdigit():
        return int(level)

    # Parse roman numerals, subtracting when a smaller symbol precedes a larger one
    symbols = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    previous = 0
    for char in reversed(level.upper()):
        if char not in symbols:
            return None
        value = symbols[char]
        if value < previous:
            total -= value
        else:
            total += value
            previous = value

    return total if total > 0 else None


def _get_element(sequence: Any, index: int) -> Any:
    """
    Get an element of a list-like value, or None if it is out of bounds.

    Args:
        sequence (Any): List-like value (or None) coming from a parquet column.
        index (int): Position of the desired element.

    Returns:
        Any: The element at the given position, or None.
    """
    if sequence is None or len(sequence) <= index:
        return None

    return sequence[index]


def load_converted_data(path: str) -> pd.DataFrame:
    """
    Load and concatenate all .parquet files produced by the convert command.

    Args:
        path (str): Directory containing the .parquet files.

    Returns:
        pd.DataFrame: All files concatenated, with the unified schema.
    """
    # List all .parquet files of the folder
    files = sorted(glob(os.path.join(path, "*.parquet")))

    # Read everything as a single table, casting each file to the unified schema
    dataset = pa.dataset.dataset(files, schema=SOURCE_SCHEMA)
    df = dataset.to_table().to_pandas()

    return df


def build_dim_tourn_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the tournament dimension, with one row per tournament.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, LocalStartTime, Modality, TableSize,
            BuyIn and Owner.
    """
    # One row per tournament: the start time is the time of its first hand
    dim = (
        df.groupby("TournID", as_index=False)
        .agg(
            LocalStartTime=("LocalTime", "min"),
            Modality=("Modality", "first"),
            TableSize=("TableSize", "first"),
            BuyIn=("BuyIn", "first"),
            Owner=("Owner", "first"),
        )
        .astype({"TournID": "int64"})
        .sort_values("LocalStartTime", ignore_index=True)
    )

    return dim


def build_dim_hand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the hand dimension, with one row per hand of each tournament.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, LocalTime, Level, Playing, Ante,
            SmallBlind, BigBlind, OwnerC1, OwnerC2 and BoardC1 to BoardC5.
    """
    # One row per hand
    hands = df.drop_duplicates(subset=["TournID", "HandID"], ignore_index=True)

    # The most complete view of the board: river, else turn, else flop
    boards = [
        river if len(river) > 0 else (turn if len(turn) > 0 else flop)
        for flop, turn, river in zip(
            hands["BoardFlop"], hands["BoardTurn"], hands["BoardRiver"]
        )
    ]

    # Flatten the hierarchical columns into one column per card / blind
    dim = pd.DataFrame(
        {
            "TournID": hands["TournID"].astype("int64"),
            "HandID": hands["HandID"].astype("int64"),
            "LocalTime": hands["LocalTime"],
            "Level": hands["Level"].map(_roman_to_int).astype("Int64"),
            "Playing": hands["Playing"],
            "Ante": hands["Ante"],
            "SmallBlind": [_get_element(x, 0) for x in hands["Blinds"]],
            "BigBlind": [_get_element(x, 1) for x in hands["Blinds"]],
            "OwnerC1": [_get_element(x, 0) for x in hands["OwnersHand"]],
            "OwnerC2": [_get_element(x, 1) for x in hands["OwnersHand"]],
            "BoardC1": [_get_element(x, 0) for x in boards],
            "BoardC2": [_get_element(x, 1) for x in boards],
            "BoardC3": [_get_element(x, 2) for x in boards],
            "BoardC4": [_get_element(x, 3) for x in boards],
            "BoardC5": [_get_element(x, 4) for x in boards],
        }
    )

    return dim.sort_values(["TournID", "HandID"], ignore_index=True)


def build_dim_player_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the player dimension, with one row per player in each hand.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, Player, Seat, Position, Stack,
            PostedAnte, PostedBlind, Result, Balance, ShowDownC1, ShowDownC2
            and PokerHand.
    """
    # One row per player per hand
    players = df.drop_duplicates(
        subset=["TournID", "HandID", "Player"], ignore_index=True
    )

    dim = pd.DataFrame(
        {
            "TournID": players["TournID"].astype("int64"),
            "HandID": players["HandID"].astype("int64"),
            "Player": players["Player"],
            "Seat": players["Seat"],
            "Position": players["Position"],
            "Stack": players["Stack"],
            "PostedAnte": players["PostedAnte"],
            "PostedBlind": players["PostedBlind"],
            "Result": players["Result"],
            "Balance": players["Balance"],
            "ShowDownC1": [_get_element(x, 0) for x in players["ShowDown"]],
            "ShowDownC2": [_get_element(x, 1) for x in players["ShowDown"]],
            "PokerHand": players["CardCombination"],
        }
    )

    return dim.sort_values(["TournID", "HandID", "Player"], ignore_index=True)


def build_dim_final_rank(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the final rank dimension, with one row per player in each tournament.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, Player, FinalRank and Prize. FinalRank
            is -1 when the rank was not registered in the hand history (for
            example, players still active when the owner's logs end).
    """
    # The rank and prize of a player appear only in the hand of the elimination
    # or victory, with -1 / null everywhere else, so the maximum aggregates it
    dim = (
        df.groupby(["TournID", "Player"], as_index=False)
        .agg(FinalRank=("FinalRank", "max"), Prize=("Prize", "max"))
        .astype({"TournID": "int64"})
        .sort_values(["TournID", "Player"], ignore_index=True)
    )

    return dim


def build_fact_player_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the fact table, with one row per action taken by a player in a hand.

    The hierarchical action columns (PreflopAction, FlopAction, TurnAction and
    RiverAction) hold a list of [action, amount] pairs per player per round.
    They are exploded so that each row of the fact represents one single
    action, identified by the round and by the order in which it was taken.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, Player, Round, ActionIndex,
            Action and Value. ActionIndex restarts at 1 for each player/round,
            preserving the order of the actions. Value is null for actions
            without an amount (for example, checks and folds).
    """
    # One row per player per hand, with the four hierarchical action columns
    base = df.drop_duplicates(subset=["TournID", "HandID", "Player"]).loc[
        :, ["TournID", "HandID", "Player", *ROUNDS.keys()]
    ]

    # Turn the four action columns into rows, one per round
    melted = base.melt(
        id_vars=["TournID", "HandID", "Player"],
        value_vars=list(ROUNDS.keys()),
        var_name="Round",
        value_name="Pair",
    )
    melted["Round"] = melted["Round"].map(ROUNDS)

    # Explode the list of [action, amount] pairs: one row per action taken,
    # preserving the order in which the actions happened within the round
    fact = melted.explode("Pair", ignore_index=True)

    # Split each pair into the action and its amount
    fact["Action"] = [_get_element(x, 0) for x in fact["Pair"]]
    fact["Value"] = pd.to_numeric(
        pd.Series([_get_element(x, 1) for x in fact["Pair"]]), errors="coerce"
    )

    # Discard placeholders of rounds in which the player did not act
    fact = fact[fact["Action"].notna() & (fact["Action"] != "")]

    # Order of the action within its player/round, following the exploded order
    fact["ActionIndex"] = (
        fact.groupby(["TournID", "HandID", "Player", "Round"]).cumcount() + 1
    )

    # Final structure of the fact table
    fact = fact.astype({"TournID": "int64", "HandID": "int64"}).loc[
        :, ["TournID", "HandID", "Player", "Round", "ActionIndex", "Action", "Value"]
    ]

    # Sort by tournament, hand, player and chronological order of the rounds
    round_order = {"preflop": 0, "flop": 1, "turn": 2, "river": 3}
    fact = (
        fact.assign(_round_order=fact["Round"].map(round_order))
        .sort_values(
            ["TournID", "HandID", "Player", "_round_order", "ActionIndex"],
            ignore_index=True,
        )
        .drop(columns="_round_order")
    )

    return fact


def build_star_schema(source: str, destination: str) -> dict[str, int]:
    """
    Build the star schema from converted data and save it as .parquet files.

    Reads all .parquet files produced by the convert command, concatenates
    them and splits the result into one fact table and four dimensions:
    fact_player_actions, dim_tourn_summary, dim_hand_summary,
    dim_player_summary and dim_final_rank.

    Args:
        source (str): Directory containing the converted .parquet files.
        destination (str): Directory where the five tables will be saved.

    Returns:
        dict[str, int]: Number of rows of each generated table.
    """
    # Load all converted files as a single DataFrame
    df = load_converted_data(source)

    # Build the five tables of the star schema
    tables = {
        "fact_player_actions": build_fact_player_actions(df),
        "dim_tourn_summary": build_dim_tourn_summary(df),
        "dim_hand_summary": build_dim_hand_summary(df),
        "dim_player_summary": build_dim_player_summary(df),
        "dim_final_rank": build_dim_final_rank(df),
    }

    # Save each table and collect its number of rows
    number_of_rows = {}
    for name, table in tables.items():
        table.to_parquet(os.path.join(destination, f"{name}.parquet"), index=False)
        number_of_rows[name] = len(table)

    return number_of_rows
