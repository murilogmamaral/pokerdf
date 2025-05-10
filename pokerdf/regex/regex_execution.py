from typing import Any
from pokerdf.regex.regex_patterns import RegexPatterns

r = RegexPatterns()


def capture_common_data(hand: list[str]) -> dict[str, Any]:
    """
    Captures the common data of the tournament

    Args:
        hand (list): List of texts from a specific hand.

    Returns:
        dict: Dictionary of captured values.
    """
    row: dict[str, Any] = {}
    row["Modality"] = r.get_modality(hand)
    row["TableSize"] = r.get_table_size(hand)
    row["BuyIn"] = r.get_buyin(hand)
    row["TournID"] = r.get_tourn_id(hand)
    row["Owner"] = r.get_owner(hand)

    return row


def capture_general_data_of_the_hand(splitted_hand: list[str]) -> dict[str, Any]:
    """
    Captures the general data of the hand

    Args:
        hand (list): List of texts from a specific hand.

    Returns:
        dict: Dictionary of captured values.
    """
    row: dict[str, Any] = {}
    row["HandID"] = r.get_hand_id(splitted_hand)
    row["TableID"] = r.get_table_id(splitted_hand)
    row["LocalTime"] = r.get_time(splitted_hand)
    row["Level"] = r.get_level(splitted_hand)
    row["Ante"] = r.get_ante(splitted_hand)
    row["Blinds"] = r.get_blinds(splitted_hand)
    row["OwnersHand"] = r.get_owner_cards(splitted_hand)
    row["Playing"] = r.get_number_of_active_players(splitted_hand)
    row["BoardFlop"] = r.get_board(splitted_hand, stage="FLOP ***")
    row["BoardTurn"] = r.get_board(splitted_hand, stage="TURN ***")
    row["BoardRiver"] = r.get_board(splitted_hand, stage="RIVER ***")

    return row


def capture_specific_data_of_the_player(
    splitted_hand: list[str], player: str
) -> dict[str, Any]:
    """
    Captures the specific data of a player

    Args:
        hand (list): List of texts from a specific hand.
        player (str): Name of the player.

    Returns:
        dict: Dictionary of captured values.
    """
    row: dict[str, Any] = {}
    row["Player"] = [player]
    row["Seat"] = r.get_seat(player, splitted_hand)
    row["PostedAnte"] = r.get_posted_ante(player, splitted_hand)
    row["Position"] = r.get_position(player, splitted_hand)
    row["PostedBlind"] = r.get_posted_blind(player, splitted_hand)
    row["Stack"] = r.get_stack(player, splitted_hand)
    row["PreflopAction"] = r.get_actions(player, splitted_hand, stage="HOLE CARDS ***")
    row["FlopAction"] = r.get_actions(player, splitted_hand, stage="FLOP ***")
    row["TurnAction"] = r.get_actions(player, splitted_hand, stage="TURN ***")
    row["RiverAction"] = r.get_actions(player, splitted_hand, stage="RIVER ***")
    row["AnteAllIn"] = r.get_allin(player, splitted_hand, stage=" posts the ante ")
    row["PreflopAllIn"] = r.get_allin(player, splitted_hand, stage="HOLE CARDS ***")
    row["FlopAllIn"] = r.get_allin(player, splitted_hand, stage="FLOP ***")
    row["TurnAllIn"] = r.get_allin(player, splitted_hand, stage="TURN ***")
    row["RiverAllIn"] = r.get_allin(player, splitted_hand, stage="RIVER ***")
    row["ShowDown"] = r.get_showed_card(player, splitted_hand)
    row["CardCombination"] = r.get_card_combination(player, splitted_hand)
    row["Result"] = r.get_result(player, splitted_hand)
    row["Balance"] = r.get_balance(player, splitted_hand)
    row["FinalRank"] = r.get_final_rank(player, splitted_hand)
    row["Prize"] = r.get_prize(player, splitted_hand)

    return row
