import os
from glob import glob
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.dataset

from pokerdf.utils.columns import Column, ModelColumn, ModelTable, Round
from pokerdf.utils.strings import PARQUET_EXTENSION

# Unified schema of the .parquet files produced by the convert command.
# Reading with an explicit schema is required because columns that are entirely
# empty in a tournament (for example, Prize) are saved with the "null" type,
# and the type must be unified before concatenating all files.
_ACTIONS = pa.list_(pa.list_(pa.string()))
_CARDS = pa.list_(pa.string())
SOURCE_SCHEMA = pa.schema(
    [
        (Column.MODALITY, pa.string()),
        (Column.TABLE_SIZE, pa.int64()),
        (Column.BUY_IN, pa.string()),
        (Column.TOURN_ID, pa.string()),
        (Column.TABLE_ID, pa.string()),
        (Column.HAND_ID, pa.string()),
        (Column.LOCAL_TIME, pa.timestamp("ns")),
        (Column.LEVEL, pa.string()),
        (Column.ANTE, pa.float64()),
        (Column.BLINDS, pa.list_(pa.float64())),
        (Column.OWNER, pa.string()),
        (Column.OWNERS_HAND, _CARDS),
        (Column.PLAYING, pa.int64()),
        (Column.PLAYER, pa.string()),
        (Column.SEAT, pa.int64()),
        (Column.POSTED_ANTE, pa.float64()),
        (Column.POSITION, pa.string()),
        (Column.POSTED_BLIND, pa.float64()),
        (Column.STACK, pa.float64()),
        (Column.PREFLOP_ACTION, _ACTIONS),
        (Column.FLOP_ACTION, _ACTIONS),
        (Column.TURN_ACTION, _ACTIONS),
        (Column.RIVER_ACTION, _ACTIONS),
        (Column.ANTE_ALL_IN, pa.bool_()),
        (Column.PREFLOP_ALL_IN, pa.bool_()),
        (Column.FLOP_ALL_IN, pa.bool_()),
        (Column.TURN_ALL_IN, pa.bool_()),
        (Column.RIVER_ALL_IN, pa.bool_()),
        (Column.BOARD_FLOP, _CARDS),
        (Column.BOARD_TURN, _CARDS),
        (Column.BOARD_RIVER, _CARDS),
        (Column.SHOW_DOWN, _CARDS),
        (Column.CARD_COMBINATION, pa.string()),
        (Column.RESULT, pa.string()),
        (Column.BALANCE, pa.float64()),
        (Column.FINAL_RANK, pa.int64()),
        (Column.PRIZE, pa.float64()),
    ]
)

# Mapping between the action columns of the converted data and the round names
ROUNDS = {
    Column.PREFLOP_ACTION: Round.PREFLOP,
    Column.FLOP_ACTION: Round.FLOP,
    Column.TURN_ACTION: Round.TURN,
    Column.RIVER_ACTION: Round.RIVER,
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
    files = sorted(glob(os.path.join(path, f"*{PARQUET_EXTENSION}")))

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
        df.groupby(Column.TOURN_ID, as_index=False)
        .agg(
            **{
                ModelColumn.LOCAL_START_TIME: (Column.LOCAL_TIME, "min"),
                Column.MODALITY: (Column.MODALITY, "first"),
                Column.TABLE_SIZE: (Column.TABLE_SIZE, "first"),
                Column.BUY_IN: (Column.BUY_IN, "first"),
                Column.OWNER: (Column.OWNER, "first"),
            }
        )
        .astype({Column.TOURN_ID: "int64"})
        .sort_values(ModelColumn.LOCAL_START_TIME, ignore_index=True)
    )

    return dim


def build_dim_hand_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the hand dimension, with one row per hand of each tournament.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, LocalTime, Level, Playing, Ante,
            SmallBlind, BigBlind, OwnerC1 and OwnerC2.
    """
    # One row per hand
    hands = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID], ignore_index=True
    )

    # Flatten the hierarchical columns into one column per card / blind
    dim = pd.DataFrame(
        {
            Column.TOURN_ID: hands[Column.TOURN_ID].astype("int64"),
            Column.HAND_ID: hands[Column.HAND_ID].astype("int64"),
            Column.LOCAL_TIME: hands[Column.LOCAL_TIME],
            Column.LEVEL: hands[Column.LEVEL].map(_roman_to_int).astype("Int64"),
            Column.PLAYING: hands[Column.PLAYING],
            Column.ANTE: hands[Column.ANTE],
            ModelColumn.SMALL_BLIND: [_get_element(x, 0) for x in hands[Column.BLINDS]],
            ModelColumn.BIG_BLIND: [_get_element(x, 1) for x in hands[Column.BLINDS]],
            ModelColumn.OWNER_C1: [
                _get_element(x, 0) for x in hands[Column.OWNERS_HAND]
            ],
            ModelColumn.OWNER_C2: [
                _get_element(x, 1) for x in hands[Column.OWNERS_HAND]
            ],
        }
    )

    return dim.sort_values([Column.TOURN_ID, Column.HAND_ID], ignore_index=True)


def build_dim_player_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the player dimension, with one row per player in each hand.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, Player, Stack, PostedAnte,
            PostedBlind, Result, Balance, ShowDownC1, ShowDownC2 and
            PokerHand. Seat and Position belong to the fact table, where
            they define who acts first in each round.
    """
    # One row per player per hand
    players = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID, Column.PLAYER], ignore_index=True
    )

    dim = pd.DataFrame(
        {
            Column.TOURN_ID: players[Column.TOURN_ID].astype("int64"),
            Column.HAND_ID: players[Column.HAND_ID].astype("int64"),
            Column.PLAYER: players[Column.PLAYER],
            Column.STACK: players[Column.STACK],
            Column.POSTED_ANTE: players[Column.POSTED_ANTE],
            Column.POSTED_BLIND: players[Column.POSTED_BLIND],
            Column.RESULT: players[Column.RESULT],
            Column.BALANCE: players[Column.BALANCE],
            ModelColumn.SHOW_DOWN_C1: [
                _get_element(x, 0) for x in players[Column.SHOW_DOWN]
            ],
            ModelColumn.SHOW_DOWN_C2: [
                _get_element(x, 1) for x in players[Column.SHOW_DOWN]
            ],
            ModelColumn.POKER_HAND: players[Column.CARD_COMBINATION],
        }
    )

    return dim.sort_values(
        [Column.TOURN_ID, Column.HAND_ID, Column.PLAYER], ignore_index=True
    )


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
        df.groupby([Column.TOURN_ID, Column.PLAYER], as_index=False)
        .agg(
            **{
                Column.FINAL_RANK: (Column.FINAL_RANK, "max"),
                Column.PRIZE: (Column.PRIZE, "max"),
            }
        )
        .astype({Column.TOURN_ID: "int64"})
        .sort_values([Column.TOURN_ID, Column.PLAYER], ignore_index=True)
    )

    return dim


def _explode_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode the hierarchical action columns into one row per action.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: One row per action, with the keys, seat, position,
            posted blind, big blind amount, round, action, value, action index
            and the board of each round still attached.
    """
    # One row per player per hand, with the four hierarchical action columns
    # and the context needed downstream (seat, position, blinds and boards)
    base = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]
    ).loc[
        :,
        [
            Column.TOURN_ID,
            Column.HAND_ID,
            Column.PLAYER,
            Column.SEAT,
            Column.POSITION,
            Column.POSTED_BLIND,
            Column.BLINDS,
            *ROUNDS.keys(),
            Column.BOARD_FLOP,
            Column.BOARD_TURN,
            Column.BOARD_RIVER,
        ],
    ]

    # The bet level the preflop actually starts at: the largest blind posted
    # in the hand. It is usually the nominal big blind, but a short-stacked
    # big blind that goes all-in on the post lowers it (and the platform
    # computes every "raises X to Y" of the hand on top of the posted value).
    # Non-acting players matter here, so it is computed before the explosion
    base["_effective_big_blind"] = base.groupby([Column.TOURN_ID, Column.HAND_ID])[
        Column.POSTED_BLIND
    ].transform("max")

    # Turn the four action columns into rows, one per round
    melted = base.melt(
        id_vars=[
            Column.TOURN_ID,
            Column.HAND_ID,
            Column.PLAYER,
            Column.SEAT,
            Column.POSITION,
            Column.POSTED_BLIND,
            Column.BLINDS,
            "_effective_big_blind",
            Column.BOARD_FLOP,
            Column.BOARD_TURN,
            Column.BOARD_RIVER,
        ],
        value_vars=list(ROUNDS.keys()),
        var_name=ModelColumn.ROUND,
        value_name="Pair",
    )
    melted[ModelColumn.ROUND] = melted[ModelColumn.ROUND].map(ROUNDS)

    # Explode the list of [action, amount] pairs: one row per action taken,
    # preserving the order in which the actions happened within the round
    fact = melted.explode("Pair", ignore_index=True)

    # Split each pair into the action and its amount
    fact[ModelColumn.ACTION] = [_get_element(x, 0) for x in fact["Pair"]]
    fact[ModelColumn.VALUE] = pd.to_numeric(
        pd.Series([_get_element(x, 1) for x in fact["Pair"]]), errors="coerce"
    )

    # Discard placeholders of rounds in which the player did not act
    fact = fact[fact[ModelColumn.ACTION].notna() & (fact[ModelColumn.ACTION] != "")]

    # Order of the action within its player/round, following the exploded
    # order. In a betting round the action moves clockwise in orbits, so this
    # index also identifies the orbit in which the action happened
    fact[ModelColumn.ACTION_INDEX] = (
        fact.groupby(
            [Column.TOURN_ID, Column.HAND_ID, Column.PLAYER, ModelColumn.ROUND]
        ).cumcount()
        + 1
    )

    return fact


def _sort_chronologically(fact: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the actions of each hand in the order in which they were taken.

    Inside a betting round the action moves clockwise in orbits: the round
    starts on the seat after the big blind (preflop) or after the button
    (postflop, which also covers heads-up), everyone acts once, and further
    orbits happen when a bet or raise reopens the action. Sorting by round,
    orbit (ActionIndex) and the rotation of the seats from the first seat to
    act reproduces the exact sequence of the hand.

    Args:
        fact (pd.DataFrame): Exploded actions, one row per action.
        players (pd.DataFrame): One row per player per hand, with seat and
            position. This must include every player of the hand — a big
            blind or button that goes all-in on the blind/ante has no action
            rows, but still anchors the order of the others.

    Returns:
        pd.DataFrame: The same rows sorted chronologically, with ActionOrder
            (1..n inside each hand) materialized.
    """
    keys = [Column.TOURN_ID, Column.HAND_ID]

    # Seat of the big blind and of the button in each hand, taken from the
    # full list of players (not only from the ones that acted)
    anchors = (
        players.loc[:, [*keys, Column.SEAT, Column.POSITION]]
        .drop_duplicates(subset=[*keys, Column.SEAT])
        .pivot_table(
            index=keys,
            columns=Column.POSITION,
            values=Column.SEAT,
            aggfunc="first",
        )
        .reset_index()
    )
    anchors = anchors.rename(
        columns={"big blind": "_bb_seat", "button": "_button_seat"}
    )
    for anchor in ["_bb_seat", "_button_seat"]:
        if anchor not in anchors.columns:
            anchors[anchor] = pd.NA
    fact = fact.merge(anchors[[*keys, "_bb_seat", "_button_seat"]], on=keys, how="left")

    # Falling back to seat order when an anchor is missing in the logs
    fact["_bb_seat"] = fact["_bb_seat"].fillna(0)
    fact["_button_seat"] = fact["_button_seat"].fillna(fact["_bb_seat"])

    # Rotation of the seats from the first seat to act: seats are 1 to 9, so
    # the cyclic distance modulo 10 preserves the clockwise order of play
    first_to_act = (
        fact["_bb_seat"].where(
            fact[ModelColumn.ROUND] == Round.PREFLOP, fact["_button_seat"]
        )
        + 1
    )
    fact["_rotation"] = (fact[Column.SEAT] - first_to_act).mod(10)

    # Chronological order: round, orbit, rotation inside the orbit
    round_order = {round_name: order for order, round_name in enumerate(Round)}
    fact = fact.assign(
        _round_order=fact[ModelColumn.ROUND].map(round_order)
    ).sort_values(
        [*keys, "_round_order", ModelColumn.ACTION_INDEX, "_rotation"],
        ignore_index=True,
    )

    # Sequence of the action inside the hand
    fact[ModelColumn.ACTION_ORDER] = fact.groupby(keys).cumcount() + 1

    return fact.drop(columns=["_bb_seat", "_button_seat", "_rotation", "_round_order"])


def _compute_bet_amounts(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Compute AddedValue and TotalValue for each action.

    The Value captured from the logs is ambiguous: "calls X" means X chips
    added, but "raises X to Y" means the bet was increased BY X, and the
    chips the player actually added depend on what was already committed.
    The amounts are reconstructed by replaying each betting round with a
    state machine that follows the arithmetic of the platform:

    - The bet level of a round (amount to match) is the largest total
      committed by any player so far. On preflop it starts at the effective
      posted big blind (a short all-in big blind lowers it) and postflop at
      zero.
    - A player's committed amount starts at the posted blind on preflop and
      at zero postflop.
    - bets/raises reach the new level (TotalValue = level + X); calls add X
      to the committed amount; checks and folds add nothing.
    - Every TotalValue can push the level up. This also covers the short
      all-in big blind: the first caller still pays the nominal big blind,
      and that call becomes the new level for the raises that follow.
    - AddedValue = TotalValue - previously committed amount, i.e. the chips
      the player actually pushed with the action.

    Antes are not part of the round betting and uncalled bets returned at the
    end of the hand are not discounted.

    Args:
        fact (pd.DataFrame): Exploded actions sorted chronologically.

    Returns:
        pd.DataFrame: The same rows with AddedValue and TotalValue attached.
    """
    # Initial bet level of the preflop: the effective posted big blind (a
    # short all-in big blind lowers it), falling back to the nominal value
    nominal_big_blind = pd.Series(
        [_get_element(x, 1) for x in fact[Column.BLINDS]], index=fact.index
    ).astype("float64")
    effective_big_blind = fact["_effective_big_blind"].fillna(nominal_big_blind)

    # Replay the rounds in chronological order (the rows already are)
    added_values: list[float] = []
    total_values: list[float] = []
    levels: dict[tuple[Any, ...], float] = {}
    committed_amounts: dict[tuple[Any, ...], float] = {}
    for tourn_id, hand_id, round_name, player, action, value, posted_blind, bb in zip(
        fact[Column.TOURN_ID],
        fact[Column.HAND_ID],
        fact[ModelColumn.ROUND],
        fact[Column.PLAYER],
        fact[ModelColumn.ACTION],
        fact[ModelColumn.VALUE],
        fact[Column.POSTED_BLIND],
        effective_big_blind,
    ):
        is_preflop = round_name == Round.PREFLOP
        round_key = (tourn_id, hand_id, round_name)
        player_key = (tourn_id, hand_id, round_name, player)

        # Current bet level of the round and committed amount of the player
        if round_key not in levels:
            levels[round_key] = float(bb) if is_preflop and pd.notna(bb) else 0.0
        blind = float(posted_blind) if pd.notna(posted_blind) else 0.0
        committed = committed_amounts.get(player_key, blind if is_preflop else 0.0)

        # The arithmetic of each action type
        if action in ("bets", "raises"):
            total = (
                levels[round_key] + float(value) if pd.notna(value) else float("nan")
            )
        elif action == "calls":
            total = committed + float(value) if pd.notna(value) else float("nan")
        else:
            total = committed

        # Update the state of the round and of the player
        if pd.notna(total):
            levels[round_key] = max(levels[round_key], total)
            committed_amounts[player_key] = total

        added_values.append(total - committed)
        total_values.append(total)

    fact[ModelColumn.ADDED_VALUE] = added_values
    fact[ModelColumn.TOTAL_VALUE] = total_values

    return fact


def build_fact_player_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the fact table, with one row per action taken by a player in a hand.

    The hierarchical action columns (PreflopAction, FlopAction, TurnAction and
    RiverAction) hold a list of [action, amount] pairs per player per round.
    They are exploded so that each row of the fact represents one single
    action, then sorted exactly as the hand unfolded: rounds in chronological
    order, starting from the first seat to act (the seat after the big blind
    on preflop, the seat after the button postflop).

    Each row carries the seat and position of the player, the board visible
    at the moment of the action, and the reconstructed amounts: AddedValue
    (chips pushed by the action) and TotalValue (total committed by the
    player in the round after the action, including the posted blind).

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, ActionOrder, Round,
            ActionIndex, Player, Seat, Position, Action, Value, AddedValue,
            TotalValue and BoardC1 to BoardC5, sorted by ActionOrder inside
            each hand. ActionIndex restarts at 1 for each player/round; Value
            keeps the raw amount captured from the logs (null for actions
            without an amount, like checks and folds).
    """
    # One row per action, sorted as the action unfolded, with the amounts.
    # The full list of players anchors the order even when the big blind or
    # the button had no action (for example, all-in on the blind or ante)
    players = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]
    ).loc[:, [Column.TOURN_ID, Column.HAND_ID, Column.SEAT, Column.POSITION]]
    fact = _explode_actions(df)
    fact = _sort_chronologically(fact, players)
    fact = _compute_bet_amounts(fact)

    # The board visible at the moment of the action, according to the round:
    # no cards on preflop, then the board of the round of the action
    visible_boards = [
        (
            (
                flop
                if round_name == Round.FLOP
                else turn if round_name == Round.TURN else river
            )
            if round_name != Round.PREFLOP
            else None
        )
        for round_name, flop, turn, river in zip(
            fact[ModelColumn.ROUND],
            fact[Column.BOARD_FLOP],
            fact[Column.BOARD_TURN],
            fact[Column.BOARD_RIVER],
        )
    ]
    fact[ModelColumn.BOARD_C1] = [_get_element(x, 0) for x in visible_boards]
    fact[ModelColumn.BOARD_C2] = [_get_element(x, 1) for x in visible_boards]
    fact[ModelColumn.BOARD_C3] = [_get_element(x, 2) for x in visible_boards]
    fact[ModelColumn.BOARD_C4] = [_get_element(x, 3) for x in visible_boards]
    fact[ModelColumn.BOARD_C5] = [_get_element(x, 4) for x in visible_boards]

    # Final structure of the fact table
    fact = fact.astype({Column.TOURN_ID: "int64", Column.HAND_ID: "int64"}).loc[
        :,
        [
            Column.TOURN_ID,
            Column.HAND_ID,
            ModelColumn.ACTION_ORDER,
            ModelColumn.ROUND,
            ModelColumn.ACTION_INDEX,
            Column.PLAYER,
            Column.SEAT,
            Column.POSITION,
            ModelColumn.ACTION,
            ModelColumn.VALUE,
            ModelColumn.ADDED_VALUE,
            ModelColumn.TOTAL_VALUE,
            ModelColumn.BOARD_C1,
            ModelColumn.BOARD_C2,
            ModelColumn.BOARD_C3,
            ModelColumn.BOARD_C4,
            ModelColumn.BOARD_C5,
        ],
    ]

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
        ModelTable.FACT_PLAYER_ACTIONS: build_fact_player_actions(df),
        ModelTable.DIM_TOURN_SUMMARY: build_dim_tourn_summary(df),
        ModelTable.DIM_HAND_SUMMARY: build_dim_hand_summary(df),
        ModelTable.DIM_PLAYER_SUMMARY: build_dim_player_summary(df),
        ModelTable.DIM_FINAL_RANK: build_dim_final_rank(df),
    }

    # Save each table and collect its number of rows
    number_of_rows = {}
    for name, table in tables.items():
        table.to_parquet(
            os.path.join(destination, f"{name}{PARQUET_EXTENSION}"), index=False
        )
        number_of_rows[str(name)] = len(table)

    return number_of_rows
