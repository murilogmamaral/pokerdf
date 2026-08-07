from typing import Any

from pokerdf.regex.regex_patterns import RegexPatterns
from pokerdf.utils.columns import Column

r = RegexPatterns()


def capture_common_data(splitted_hand: list[str]) -> dict[str, Any]:
    """
    Capture the data shared by every hand of the tournament
    (modality, table size, buy-in, tournament ID and owner).

    Args:
        splitted_hand (list): Text of a hand split by stage ("\\n*** ").

    Returns:
        dict: Dictionary mapping column names to captured values,
            each value being a single-element list.
    """
    row: dict[str, Any] = {}
    row[Column.MODALITY] = r.get_modality(splitted_hand)
    row[Column.TABLE_SIZE] = r.get_table_size(splitted_hand)
    row[Column.BUY_IN] = r.get_buyin(splitted_hand)
    row[Column.TOURN_ID] = r.get_tourn_id(splitted_hand)
    row[Column.OWNER] = r.get_owner(splitted_hand)

    return row


def capture_general_data_of_the_hand(splitted_hand: list[str]) -> dict[str, Any]:
    """
    Capture the data that describes the hand as a whole
    (IDs, time, level, blinds, board cards, etc.), regardless of player.

    Args:
        splitted_hand (list): Text of a hand split by stage ("\\n*** ").

    Returns:
        dict: Dictionary mapping column names to captured values,
            each value being a single-element list.
    """
    row: dict[str, Any] = {}
    row[Column.HAND_ID] = r.get_hand_id(splitted_hand)
    row[Column.TABLE_ID] = r.get_table_id(splitted_hand)
    row[Column.LOCAL_TIME] = r.get_time(splitted_hand)
    row[Column.LEVEL] = r.get_level(splitted_hand)
    row[Column.ANTE] = r.get_ante(splitted_hand)
    row[Column.BLINDS] = r.get_blinds(splitted_hand)
    row[Column.OWNERS_HAND] = r.get_owner_cards(splitted_hand)
    row[Column.PLAYING] = r.get_number_of_active_players(splitted_hand)
    row[Column.BOARD_FLOP] = r.get_board(splitted_hand, stage="FLOP ***")
    row[Column.BOARD_TURN] = r.get_board(splitted_hand, stage="TURN ***")
    row[Column.BOARD_RIVER] = r.get_board(splitted_hand, stage="RIVER ***")

    return row


def capture_specific_data_of_the_player(
    splitted_hand: list[str], player: str
) -> dict[str, Any]:
    """
    Capture the data specific to one player in the hand
    (seat, position, stack, actions per stage, showdown and results).

    Args:
        splitted_hand (list): Text of a hand split by stage ("\\n*** ").
        player (str): Name of the player.

    Returns:
        dict: Dictionary mapping column names to captured values,
            each value being a single-element list.
    """
    row: dict[str, Any] = {}
    row[Column.PLAYER] = [player]
    row[Column.SEAT] = r.get_seat(player, splitted_hand)
    row[Column.POSTED_ANTE] = r.get_posted_ante(player, splitted_hand)
    row[Column.POSITION] = r.get_position(player, splitted_hand)
    row[Column.POSTED_BLIND] = r.get_posted_blind(player, splitted_hand)
    row[Column.STACK] = r.get_stack(player, splitted_hand)
    row[Column.BOUNTY] = r.get_bounty(player, splitted_hand)
    row[Column.PREFLOP_ACTION] = r.get_actions(
        player, splitted_hand, stage="HOLE CARDS ***"
    )
    row[Column.FLOP_ACTION] = r.get_actions(player, splitted_hand, stage="FLOP ***")
    row[Column.TURN_ACTION] = r.get_actions(player, splitted_hand, stage="TURN ***")
    row[Column.RIVER_ACTION] = r.get_actions(player, splitted_hand, stage="RIVER ***")
    row[Column.ANTE_ALL_IN] = r.get_allin(
        player, splitted_hand, stage=" posts the ante "
    )
    row[Column.PREFLOP_ALL_IN] = r.get_allin(
        player, splitted_hand, stage="HOLE CARDS ***"
    )
    row[Column.FLOP_ALL_IN] = r.get_allin(player, splitted_hand, stage="FLOP ***")
    row[Column.TURN_ALL_IN] = r.get_allin(player, splitted_hand, stage="TURN ***")
    row[Column.RIVER_ALL_IN] = r.get_allin(player, splitted_hand, stage="RIVER ***")
    row[Column.SHOW_DOWN] = r.get_showed_card(player, splitted_hand)
    row[Column.CARD_COMBINATION] = r.get_card_combination(player, splitted_hand)
    row[Column.RESULT] = r.get_result(player, splitted_hand)
    row[Column.BALANCE] = r.get_balance(player, splitted_hand)
    row[Column.UNCALLED_RETURNED] = r.get_uncalled_returned(player, splitted_hand)
    row[Column.BOUNTY_WON] = r.get_bounty_won(player, splitted_hand)
    row[Column.FINAL_RANK] = r.get_final_rank(player, splitted_hand)
    row[Column.PRIZE] = r.get_prize(player, splitted_hand)

    return row
