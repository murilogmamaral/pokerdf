import os
import re
from glob import glob
from typing import Any

import pandas as pd
import pyarrow as pa
import pyarrow.dataset

from pokerdf.modeling.anonymize import (
    GdprMode,
    anonymize_fact,
    describe,
    generate_salt,
)
from pokerdf.modeling.evaluation import COMBINATION_SCORES, evaluate_hand
from pokerdf.utils.columns import Column, ModelColumn, ModelTable, Round
from pokerdf.utils.strings import ANONYMIZATION_REPORT, PARQUET_EXTENSION

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
        (Column.BOUNTY, pa.float64()),
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
        (Column.UNCALLED_RETURNED, pa.float64()),
        (Column.BOUNTY_WON, pa.float64()),
        (Column.TOTAL_POT_LOG, pa.float64()),
        (Column.RAKE, pa.float64()),
        (Column.POT_BREAKDOWN, pa.list_(pa.float64())),
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


def _combination(
    card1: str | None, card2: str | None, board: tuple[str, ...]
) -> tuple[str | None, int | None]:
    """
    Name and score the combination made by two hole cards and a board.

    Args:
        card1 (str | None): First hole card.
        card2 (str | None): Second hole card.
        board (tuple[str, ...]): Community cards visible at the moment,
            empty on preflop.

    Returns:
        tuple[str | None, int | None]: Name and score of the combination
            (1 High Card to 10 Royal Flush), or (None, None) when the two
            hole cards are not both known — a single revealed card cannot
            say what the hand was.
    """
    if card1 is None or card2 is None:
        return None, None

    combination = evaluate_hand((card1, card2, *board))
    return str(combination), COMBINATION_SCORES[combination]


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
        pd.DataFrame: Columns TournID, LocalStartTime, Modality and BuyIn.
            TableSize and Owner belong to the fact table.
    """
    # One row per tournament: the start time is the time of its first hand.
    # The owner is not an attribute of the tournament — archives of more
    # than one owner can cover the same tournament — so it lives in the fact
    dim = (
        df.groupby(Column.TOURN_ID, as_index=False)
        .agg(
            **{
                ModelColumn.LOCAL_START_TIME: (Column.LOCAL_TIME, "min"),
                Column.MODALITY: (Column.MODALITY, "first"),
                Column.BUY_IN: (Column.BUY_IN, "first"),
            }
        )
        .astype({Column.TOURN_ID: "int64"})
        .sort_values(ModelColumn.LOCAL_START_TIME, ignore_index=True)
    )

    return dim


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


def _blind_post_action(position: Any, posted: float, blinds: Any) -> str:
    """
    Name the blind post action of a player.

    Args:
        position (Any): Position of the player (button, small blind, big blind).
        posted (float): Amount posted by the player.
        blinds (Any): Nominal [small blind, big blind] of the hand.

    Returns:
        str: "posts small blind" or "posts big blind". In heads-up the button
            is the small blind; without a position, the nominal values decide.
    """
    if position == "big blind":
        return "posts big blind"
    if position in ("small blind", "button"):
        return "posts small blind"

    return (
        "posts big blind" if posted == _get_element(blinds, 1) else "posts small blind"
    )


def _explode_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Explode the hierarchical action columns into one row per action, adding
    one row per ante and blind post.

    The posts are events of the hand like any other action: they carry the
    real amount that left the player's stack (partial when all-in), and they
    give a row to players that never acted voluntarily, like a big blind
    that wins a walk or goes all-in on the post.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: One row per post or action, with the keys, the context
            of the hand and an internal _phase marker (0 antes, 1 blinds,
            2 voluntary actions). ActionIndex is 0 for posts and restarts at
            1 for each player/round of voluntary actions.
    """
    # One row per player per hand, with the four hierarchical action columns
    # and the context needed downstream (seat, position, posts, stack, the
    # hand context that goes into the fact table, and the boards)
    context_columns = [
        Column.LOCAL_TIME,
        Column.SEAT,
        Column.POSITION,
        Column.STACK,
        Column.POSTED_ANTE,
        Column.POSTED_BLIND,
        Column.BLINDS,
        Column.TABLE_SIZE,
        Column.LEVEL,
        Column.PLAYING,
        Column.ANTE,
        Column.OWNER,
        Column.OWNERS_HAND,
        Column.SHOW_DOWN,
        Column.CARD_COMBINATION,
        Column.RESULT,
        Column.BALANCE,
        Column.BOARD_FLOP,
        Column.BOARD_TURN,
        Column.BOARD_RIVER,
    ]
    base = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]
    ).loc[
        :,
        [
            Column.TOURN_ID,
            Column.HAND_ID,
            Column.PLAYER,
            *context_columns,
            *ROUNDS.keys(),
        ],
    ]

    # One row per ante posted, before any voluntary action
    antes = base[base[Column.POSTED_ANTE].astype("float64").notna()].copy()
    antes[ModelColumn.ROUND] = Round.PREFLOP
    antes[ModelColumn.ACTION] = "posts ante"
    antes[ModelColumn.VALUE] = antes[Column.POSTED_ANTE].astype("float64")
    antes["_phase"] = 0

    # One row per blind posted, after the antes: the small blind posts
    # first, then the big blind (also in heads-up, where the button is the
    # small blind)
    blinds = base[base[Column.POSTED_BLIND].astype("float64").notna()].copy()
    blinds[ModelColumn.ROUND] = Round.PREFLOP
    blinds[ModelColumn.ACTION] = [
        _blind_post_action(position, posted, nominal)
        for position, posted, nominal in zip(
            blinds[Column.POSITION],
            blinds[Column.POSTED_BLIND],
            blinds[Column.BLINDS],
        )
    ]
    blinds[ModelColumn.VALUE] = blinds[Column.POSTED_BLIND].astype("float64")
    blinds["_phase"] = (blinds[ModelColumn.ACTION] == "posts big blind").astype(int) + 1

    # Turn the four action columns into rows, one per round
    melted = base.melt(
        id_vars=[
            Column.TOURN_ID,
            Column.HAND_ID,
            Column.PLAYER,
            *context_columns,
        ],
        value_vars=list(ROUNDS.keys()),
        var_name=ModelColumn.ROUND,
        value_name="Pair",
    )
    melted[ModelColumn.ROUND] = melted[ModelColumn.ROUND].map(ROUNDS)

    # Explode the list of [action, amount] pairs: one row per action taken,
    # preserving the order in which the actions happened within the round
    actions = melted.explode("Pair", ignore_index=True)

    # Split each pair into the action and its amount
    actions[ModelColumn.ACTION] = [_get_element(x, 0) for x in actions["Pair"]]
    actions[ModelColumn.VALUE] = pd.to_numeric(
        pd.Series([_get_element(x, 1) for x in actions["Pair"]]), errors="coerce"
    )
    actions = actions.drop(columns="Pair")
    actions["_phase"] = 3

    # Discard placeholders of rounds in which the player did not act
    actions = actions[
        actions[ModelColumn.ACTION].notna() & (actions[ModelColumn.ACTION] != "")
    ]

    # Order of the action within its player/round, following the exploded
    # order. In a betting round the action moves clockwise in orbits, so this
    # index also identifies the orbit in which the action happened
    actions[ModelColumn.ACTION_INDEX] = (
        actions.groupby(
            [Column.TOURN_ID, Column.HAND_ID, Column.PLAYER, ModelColumn.ROUND]
        ).cumcount()
        + 1
    )

    # Posts come before the voluntary actions, with ActionIndex 0
    posts = pd.concat([antes, blinds], ignore_index=True).drop(
        columns=list(ROUNDS.keys())
    )
    posts[ModelColumn.ACTION_INDEX] = 0

    fact = pd.concat([posts, actions], ignore_index=True)

    return fact


def _sort_chronologically(fact: pd.DataFrame, players: pd.DataFrame) -> pd.DataFrame:
    """
    Sort the events of each hand in the order in which they happened.

    The posts open the hand in seat order from the small blind (antes first,
    then the blinds). Inside a betting round the voluntary action moves
    clockwise in orbits: the round starts on the seat after the big blind
    (preflop) or after the button (postflop, which also covers heads-up),
    everyone acts once, and further orbits happen when a bet or raise
    reopens the action. Sorting by round, orbit (ActionIndex), phase and the
    rotation of the seats reproduces the exact sequence of the hand.

    Args:
        fact (pd.DataFrame): Exploded posts and actions, one row per event.
        players (pd.DataFrame): One row per player per hand, with seat and
            position. This must include every player of the hand — a big
            blind or button that goes all-in on the blind/ante has no
            voluntary action, but still anchors the order of the others.

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
    # the cyclic distance modulo 10 preserves the clockwise order of play.
    # The voluntary preflop starts after the big blind; postflop rounds
    # start after the button
    preflop_voluntary = (fact[ModelColumn.ROUND] == Round.PREFLOP) & (
        fact["_phase"] == 3
    )
    first_to_act = fact["_bb_seat"].where(preflop_voluntary, fact["_button_seat"]) + 1
    fact["_rotation"] = (fact[Column.SEAT] - first_to_act).mod(10)

    # Posts are ordered by phase (antes, then small blind, then big blind)
    # and, among the antes, by plain seat order like the platform does
    posts = fact["_phase"] < 3
    fact.loc[posts, "_rotation"] = fact.loc[posts, Column.SEAT]

    # Chronological order: round, orbit, phase (antes, blinds, actions),
    # rotation inside the orbit
    round_order = {round_name: order for order, round_name in enumerate(Round)}
    fact = fact.assign(
        _round_order=fact[ModelColumn.ROUND].map(round_order)
    ).sort_values(
        [*keys, "_round_order", ModelColumn.ACTION_INDEX, "_phase", "_rotation"],
        ignore_index=True,
    )

    # Sequence of the event inside the hand
    fact[ModelColumn.ACTION_ORDER] = fact.groupby(keys).cumcount() + 1

    return fact.drop(columns=["_bb_seat", "_button_seat", "_rotation", "_round_order"])


def _compute_bet_amounts(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Compute AddedValue, TotalValue and the dynamic Stack for each event.

    The Value captured from the logs is ambiguous: "calls X" means X chips
    added, but "raises X to Y" means the bet was increased BY X, and the
    chips the player actually added depend on what was already committed.
    The amounts are reconstructed by replaying each hand with a state
    machine that follows the arithmetic of the platform:

    - The bet level of a round (amount to match) is the largest total bet
      by any player so far. The blind posts build it on preflop — so a
      short all-in big blind lowers it, exactly like the platform — and
      postflop it starts at zero.
    - Posts and calls add their amount to the player's total; bets/raises
      reach the new level (level + X). Checks and folds add nothing.
    - Every total can push the level up. This also covers the short all-in
      big blind: the first caller still pays the nominal big blind, and
      that call becomes the new level for the raises that follow.
    - AddedValue is the difference to the previously committed amount, i.e.
      the chips the player actually pushed with the event.
    - TotalValue is everything the player put in during the round after the
      event: on preflop it includes the posted ante and blind.
    - Stack is the stack of the player right after the event: the starting
      stack minus everything pushed so far in the hand. Uncalled bets
      returned at the end of the hand are not discounted.

    Args:
        fact (pd.DataFrame): Exploded posts and actions sorted chronologically.

    Returns:
        pd.DataFrame: The same rows with AddedValue, TotalValue and the
            dynamic Stack attached.
    """
    # Replay the hands in chronological order (the rows already are)
    added_values: list[float] = []
    total_values: list[float] = []
    levels: dict[tuple[Any, ...], float] = {}
    betting: dict[tuple[Any, ...], float] = {}
    antes: dict[tuple[Any, ...], float] = {}
    for tourn_id, hand_id, round_name, player, action, value in zip(
        fact[Column.TOURN_ID],
        fact[Column.HAND_ID],
        fact[ModelColumn.ROUND],
        fact[Column.PLAYER],
        fact[ModelColumn.ACTION],
        fact[ModelColumn.VALUE],
    ):
        round_key = (tourn_id, hand_id, round_name)
        player_key = (tourn_id, hand_id, round_name, player)
        ante_key = (tourn_id, hand_id, player)

        # Current bet level of the round and amounts of the player
        level = levels.get(round_key, 0.0)
        committed = betting.get(player_key, 0.0)
        ante = antes.get(ante_key, 0.0)
        amount = float(value) if pd.notna(value) else float("nan")

        # The arithmetic of each event type
        if action == "posts ante":
            ante += amount
            total = committed
        elif action in ("posts small blind", "posts big blind", "calls"):
            total = committed + amount
        elif action in ("bets", "raises"):
            total = level + amount
        else:
            total = committed

        # Update the state of the round and of the player
        if pd.notna(total):
            levels[round_key] = max(level, total)
            betting[player_key] = total
        if pd.notna(ante):
            antes[ante_key] = ante

        # The chips pushed by the event and the round total of the player,
        # which on preflop includes the posted ante
        if action == "posts ante":
            added_values.append(amount)
        else:
            added_values.append(total - committed)
        in_round_ante = ante if round_name == Round.PREFLOP else 0.0
        total_values.append(total + in_round_ante)

    fact[ModelColumn.ADDED_VALUE] = added_values
    fact[ModelColumn.TOTAL_VALUE] = total_values

    # The stack right after each event: the starting stack minus everything
    # the player pushed so far in the hand (posts included)
    pushed = fact.groupby([Column.TOURN_ID, Column.HAND_ID, Column.PLAYER])[
        ModelColumn.ADDED_VALUE
    ].cumsum()
    fact[Column.STACK] = fact[Column.STACK].astype("float64") - pushed

    return fact


def _compute_total_pot(fact: pd.DataFrame) -> pd.DataFrame:
    """
    Compute TotalPot: the total pot right after each event.

    With the ante and blind posts materialized as rows, the pot is simply
    everything pushed so far in the hand. Uncalled bets returned at the end
    of the hand are not discounted, so after the last event TotalPot equals
    the "Total pot" reported by the platform plus the returned amount, when
    there is one.

    Args:
        fact (pd.DataFrame): Events sorted chronologically, with AddedValue.

    Returns:
        pd.DataFrame: The same rows with TotalPot attached.
    """
    fact[ModelColumn.TOTAL_POT] = fact.groupby([Column.TOURN_ID, Column.HAND_ID])[
        ModelColumn.ADDED_VALUE
    ].cumsum()

    return fact


def build_fact_player_actions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build the fact table, with one row per event of a player in a hand.

    The ante and blind posts are materialized as rows ("posts ante",
    "posts small blind", "posts big blind", with the real — possibly
    partial — amounts), followed by the voluntary actions exploded from the
    hierarchical action columns (PreflopAction, FlopAction, TurnAction and
    RiverAction). Everything is sorted exactly as the hand unfolded: posts
    in seat order, then rounds in chronological order starting from the
    first seat to act (the seat after the big blind on preflop, the seat
    after the button postflop).

    Each row carries the context of the hand and the reconstructed amounts:

    - AddedValue: the exact chips pushed by the event.
    - TotalValue: the total put in by the player in that round after the
      event — on preflop it includes the posted ante and blind.
    - TotalPot: the total pot right after the event.
    - Stack: the stack of the player right after the event.

    Args:
        df (pd.DataFrame): Converted data loaded with load_converted_data.

    Returns:
        pd.DataFrame: Columns TournID, HandID, Owner (whose archive logged
            the hand — archives of more than one owner can be modeled
            together), LocalTime, TableSize, Playing, Level, Ante,
            SmallBlind, BigBlind, Round, Player, Seat, Position, Stack,
            PostedAnte, PostedBlind, Action, ActionIndex, ActionOrder,
            AddedValue, TotalValue, TotalPot and BoardC1 to BoardC5, plus
            the cards and combinations: OwnerC1, OwnerC2, OwnerCombination
            and OwnerCombinationScore describe the owner's holding on every
            row of the hand, like the board; RevealedShowDownC1,
            RevealedShowDownC2, RevealedShowDownCombination,
            RevealedShowDownCombinationScore and RevealedShowDownPokerHand
            (the combination the platform itself named) register, on every
            row of the player that revealed cards at showdown — the owner
            included — what the show at the end proved the player was
            holding. Scores go from 1 (High Card) to 10 (Royal Flush).
            Result and Balance close each row with the outcome of the
            player in the hand, also a future event registered early. Rows
            are sorted by ActionOrder inside each hand. ActionIndex is 0
            for posts and restarts at 1 for each player/round of voluntary
            actions.
    """
    # One row per event, sorted as the hand unfolded, with the amounts.
    # The full list of players anchors the order even when the big blind or
    # the button had no voluntary action
    players = df.drop_duplicates(
        subset=[Column.TOURN_ID, Column.HAND_ID, Column.PLAYER]
    ).loc[:, [Column.TOURN_ID, Column.HAND_ID, Column.SEAT, Column.POSITION]]
    fact = _explode_actions(df)
    fact = _sort_chronologically(fact, players)
    fact = _compute_bet_amounts(fact)
    fact = _compute_total_pot(fact)

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

    # Flatten the hand context that lives in the fact: level as an integer,
    # one column per blind and per owner card. The owner's cards are hand
    # context on every row, like the board: the private knowledge the whole
    # hand was observed with
    fact[Column.LEVEL] = fact[Column.LEVEL].map(_roman_to_int).astype("Int64")
    fact[ModelColumn.SMALL_BLIND] = [_get_element(x, 0) for x in fact[Column.BLINDS]]
    fact[ModelColumn.BIG_BLIND] = [_get_element(x, 1) for x in fact[Column.BLINDS]]
    fact[ModelColumn.OWNER_C1] = [_get_element(x, 0) for x in fact[Column.OWNERS_HAND]]
    fact[ModelColumn.OWNER_C2] = [_get_element(x, 1) for x in fact[Column.OWNERS_HAND]]

    # The cards the player of the row revealed at showdown — the owner
    # included. The show is a future event of the hand, registered on every
    # row of the player from the first action: knowing what was held is what
    # makes the behavior that led to the show analyzable
    fact[ModelColumn.REVEALED_SHOW_DOWN_C1] = [
        _get_element(x, 0) for x in fact[Column.SHOW_DOWN]
    ]
    fact[ModelColumn.REVEALED_SHOW_DOWN_C2] = [
        _get_element(x, 1) for x in fact[Column.SHOW_DOWN]
    ]

    # The combination made at the moment of each event, with the board
    # visible in the round: the owner's on every row, the revealed one on
    # the rows of the player that revealed both cards. On preflop the board
    # is empty, so a pocket pair is already One Pair
    boards = [tuple(board) if board is not None else () for board in visible_boards]
    owner_combinations = [
        _combination(c1, c2, board)
        for c1, c2, board in zip(
            fact[ModelColumn.OWNER_C1], fact[ModelColumn.OWNER_C2], boards
        )
    ]
    revealed_combinations = [
        _combination(c1, c2, board)
        for c1, c2, board in zip(
            fact[ModelColumn.REVEALED_SHOW_DOWN_C1],
            fact[ModelColumn.REVEALED_SHOW_DOWN_C2],
            boards,
        )
    ]
    fact[ModelColumn.OWNER_COMBINATION] = [name for name, _ in owner_combinations]
    fact[ModelColumn.OWNER_COMBINATION_SCORE] = pd.array(
        [score for _, score in owner_combinations], dtype="Int64"
    )
    fact[ModelColumn.REVEALED_SHOW_DOWN_COMBINATION] = [
        name for name, _ in revealed_combinations
    ]
    fact[ModelColumn.REVEALED_SHOW_DOWN_COMBINATION_SCORE] = pd.array(
        [score for _, score in revealed_combinations], dtype="Int64"
    )

    # The combination the platform itself named at showdown ("two pair,
    # Aces and Kings"), when the player showed: richer than the inferred
    # category, and another future event registered on the player's rows
    fact[ModelColumn.REVEALED_SHOW_DOWN_POKER_HAND] = fact[Column.CARD_COMBINATION]

    # Final structure of the fact table
    fact = fact.astype({Column.TOURN_ID: "int64", Column.HAND_ID: "int64"}).loc[
        :,
        [
            Column.TOURN_ID,
            Column.HAND_ID,
            Column.OWNER,
            Column.LOCAL_TIME,
            Column.TABLE_SIZE,
            Column.PLAYING,
            Column.LEVEL,
            Column.ANTE,
            ModelColumn.SMALL_BLIND,
            ModelColumn.BIG_BLIND,
            ModelColumn.ROUND,
            Column.PLAYER,
            Column.SEAT,
            Column.POSITION,
            Column.STACK,
            Column.POSTED_ANTE,
            Column.POSTED_BLIND,
            ModelColumn.ACTION,
            ModelColumn.ACTION_INDEX,
            ModelColumn.ACTION_ORDER,
            ModelColumn.ADDED_VALUE,
            ModelColumn.TOTAL_VALUE,
            ModelColumn.TOTAL_POT,
            ModelColumn.BOARD_C1,
            ModelColumn.BOARD_C2,
            ModelColumn.BOARD_C3,
            ModelColumn.BOARD_C4,
            ModelColumn.BOARD_C5,
            ModelColumn.OWNER_C1,
            ModelColumn.OWNER_C2,
            ModelColumn.OWNER_COMBINATION,
            ModelColumn.OWNER_COMBINATION_SCORE,
            ModelColumn.REVEALED_SHOW_DOWN_C1,
            ModelColumn.REVEALED_SHOW_DOWN_C2,
            ModelColumn.REVEALED_SHOW_DOWN_COMBINATION,
            ModelColumn.REVEALED_SHOW_DOWN_COMBINATION_SCORE,
            ModelColumn.REVEALED_SHOW_DOWN_POKER_HAND,
            Column.RESULT,
            Column.BALANCE,
        ],
    ]

    return fact


def _parse_gdpr_mode(gdpr: GdprMode | str | None) -> GdprMode | None:
    """
    Validate the GDPR mode before any work is done.

    Args:
        gdpr (GdprMode | str | None): Mode as received from the caller.

    Returns:
        GdprMode | None: The parsed mode, or None when no mode was informed.

    Raises:
        ValueError: If the mode is not one of the supported values, with the
            accepted ones listed in the message.
    """
    if gdpr is None:
        return None
    try:
        return GdprMode(gdpr)
    except ValueError:
        accepted = ", ".join(mode.value for mode in GdprMode)
        raise ValueError(
            f"invalid GDPR mode {gdpr!r}: expected one of {accepted}"
        ) from None


def build_star_schema(
    source: str,
    destination: str,
    gdpr: GdprMode | str | None = None,
    salt: str | None = None,
) -> dict[str, int]:
    """
    Build the star schema from converted data and save it as .parquet files.

    Reads all .parquet files produced by the convert command, concatenates
    them and splits the result into one fact table and two dimensions:
    fact_player_actions, dim_tourn_summary and dim_final_rank.

    When a GDPR mode is informed, only the fact table is generated, with the
    identifying columns pseudonymized and removed as described in the
    anonymize module, and a report of the transformations is saved next
    to it.

    Args:
        source (str): Directory containing the converted .parquet files.
        destination (str): Directory where the tables will be saved.
        gdpr (GdprMode | str | None): GDPR anonymization mode ("full" or
            "keep-owner"), or None to build the complete star schema.
        salt (str | None): Salt of the pseudonyms. When omitted, a random one
            is generated for this session and not stored.

    Returns:
        dict[str, int]: Number of rows of each generated table.
    """
    # Load all converted files as a single DataFrame
    df = load_converted_data(source)

    mode = _parse_gdpr_mode(gdpr)
    if mode:
        # The dimensions are not generated: they exist to describe who the
        # players are, how the tournament went and what each one received.
        # The Player column stores names escaped for regex, so the owners
        # are escaped the same way to match them in keep-owner mode
        owners = {re.escape(owner) for owner in df[Column.OWNER].dropna().unique()}
        fact = anonymize_fact(
            build_fact_player_actions(df),
            salt or generate_salt(),
            mode=mode,
            owners=owners,
        )
        tables = {ModelTable.FACT_PLAYER_ACTIONS: fact}
    else:
        # Build the three tables of the star schema
        tables = {
            ModelTable.FACT_PLAYER_ACTIONS: build_fact_player_actions(df),
            ModelTable.DIM_TOURN_SUMMARY: build_dim_tourn_summary(df),
            ModelTable.DIM_FINAL_RANK: build_dim_final_rank(df),
        }

    # Save each table and collect its number of rows
    number_of_rows = {}
    for name, table in tables.items():
        table.to_parquet(
            os.path.join(destination, f"{name}{PARQUET_EXTENSION}"), index=False
        )
        number_of_rows[str(name)] = len(table)

    # Save the report of what was applied next to the data, only after the
    # data itself exists: a failed save must not leave an orphan report
    if mode:
        report_path = os.path.join(destination, ANONYMIZATION_REPORT)
        with open(report_path, "w") as file:
            file.write(describe(mode, reused_salt=salt is not None))

    return number_of_rows
