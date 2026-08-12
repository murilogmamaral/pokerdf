"""Single source of truth for the column names, table names and categorical
vocabularies used across the package.

The enums inherit from StrEnum, so every member behaves exactly like its string
value: they can index DataFrames, be used as dictionary keys and be written to
parquet transparently, while keeping the names centralized and refactorable.
"""

from enum import StrEnum


class Column(StrEnum):
    """
    Columns of the converted data, in the canonical output order.

    This is the schema produced by the convert command: one row per player per
    hand, validated by ValidateInput (which mirrors these names field by field).
    """

    MODALITY = "Modality"
    TABLE_SIZE = "TableSize"
    BUY_IN = "BuyIn"
    TOURN_ID = "TournID"
    TABLE_ID = "TableID"
    HAND_ID = "HandID"
    HAND_START_TIME_CET = "HandStartTimeCET"
    HAND_START_TIME_LOCAL = "HandStartTimeLocal"
    HAND_TIMEZONE = "HandTimezone"
    LEVEL = "Level"
    ANTE = "Ante"
    BLINDS = "Blinds"
    OWNER = "Owner"
    OWNERS_HAND = "OwnersHand"
    PLAYING = "Playing"
    PLAYER = "Player"
    SEAT = "Seat"
    POSTED_ANTE = "PostedAnte"
    POSITION = "Position"
    POSTED_BLIND = "PostedBlind"
    STACK = "Stack"
    BOUNTY = "Bounty"
    PREFLOP_ACTION = "PreflopAction"
    FLOP_ACTION = "FlopAction"
    TURN_ACTION = "TurnAction"
    RIVER_ACTION = "RiverAction"
    ANTE_ALL_IN = "AnteAllIn"
    PREFLOP_ALL_IN = "PreflopAllIn"
    FLOP_ALL_IN = "FlopAllIn"
    TURN_ALL_IN = "TurnAllIn"
    RIVER_ALL_IN = "RiverAllIn"
    BOARD_FLOP = "BoardFlop"
    BOARD_TURN = "BoardTurn"
    BOARD_RIVER = "BoardRiver"
    SHOW_DOWN = "ShowDown"
    CARD_COMBINATION = "CardCombination"
    RESULT = "Result"
    BALANCE = "Balance"
    UNCALLED_RETURNED = "UncalledReturned"
    BOUNTY_WON = "BountyWon"
    TOTAL_POT_LOG = "TotalPotLog"
    RAKE = "Rake"
    POT_BREAKDOWN = "PotBreakdown"
    FINAL_RANK = "FinalRank"
    PRIZE = "Prize"


class ModelColumn(StrEnum):
    """
    Columns that exist only in the star schema tables, complementing Column.

    They are produced by the modeling command when flattening hierarchical
    columns (blinds, cards, boards) and exploding the player actions.
    """

    TOURN_FIRST_HAND_TIME_CET = "TournFirstHandTimeCET"
    TOURN_FIRST_HAND_TIME_LOCAL = "TournFirstHandTimeLocal"
    TOURN_TIMEZONE = "TournTimezone"
    SMALL_BLIND = "SmallBlind"
    BIG_BLIND = "BigBlind"
    OWNER_C1 = "OwnerC1"
    OWNER_C2 = "OwnerC2"
    BOARD_C1 = "BoardC1"
    BOARD_C2 = "BoardC2"
    BOARD_C3 = "BoardC3"
    BOARD_C4 = "BoardC4"
    BOARD_C5 = "BoardC5"
    OWNER_COMBINATION = "OwnerCombination"
    OWNER_COMBINATION_SCORE = "OwnerCombinationScore"
    REVEALED_SHOW_DOWN_C1 = "RevealedShowDownC1"
    REVEALED_SHOW_DOWN_C2 = "RevealedShowDownC2"
    REVEALED_SHOW_DOWN_COMBINATION = "RevealedShowDownCombination"
    REVEALED_SHOW_DOWN_COMBINATION_SCORE = "RevealedShowDownCombinationScore"
    REVEALED_SHOW_DOWN_POKER_HAND = "RevealedShowDownPokerHand"
    ROUND = "Round"
    ACTION_ORDER = "ActionOrder"
    ACTION_INDEX = "ActionIndex"
    ACTION = "Action"
    VALUE = "Value"
    ADDED_VALUE = "AddedValue"
    TOTAL_VALUE = "TotalValue"
    TOTAL_POT = "TotalPot"


class Round(StrEnum):
    """Rounds of a hand, in chronological order."""

    PREFLOP = "preflop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"


class HandResult(StrEnum):
    """
    Vocabulary of the Result column: the outcome of a hand for a player.

    Every player dealt into a hand leaves it in exactly one of these five
    ways. The values follow two conventions, so the common questions are one
    string predicate away instead of a list kept in the head: every win
    starts with "won", whether or not cards were needed, and every showdown
    ends with "at showdown", whatever the outcome. A muck is a loss — the
    platform always reveals a winning hand, so a mucked one never won — kept
    apart from LOST_AT_SHOWDOWN because the cards were never shown at the
    table.
    """

    FOLDED = "folded"
    WON_WITHOUT_SHOWDOWN = "won without showdown"
    WON_AT_SHOWDOWN = "won at showdown"
    LOST_AT_SHOWDOWN = "lost at showdown"
    MUCKED_AT_SHOWDOWN = "mucked at showdown"


class ModelTable(StrEnum):
    """Tables of the star schema produced by the modeling command."""

    FACT_PLAYER_ACTION = "fact_player_action"
    DIM_TOURNAMENT = "dim_tournament"
    DIM_HAND = "dim_hand"
    DIM_FINAL_RANK = "dim_final_rank"
