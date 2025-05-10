import re
from typing import Any
import pandas as pd


class RegexPatterns:
    """
    Contains all functions with regex patterns to extract data from the text files
    """

    def __init__(self) -> None:
        """
        Initialize the RegexPatterns class.
        """
        # Initialize the class
        # This class does not need any specific initialization
        pass

    def _guarantee_unicity(
        self, result: list[Any], fill: str | int | None = "Unknown"
    ) -> list[Any]:
        """
        Guarantee that the returned result is a list with just one element.

        Args:
            result (list): List of strings extracted with regex.
            fill (str | int): Value to fill if nothing is captured by the regex. Default is "Unknown".

        Returns:
            list: List with exactly one string.
        """
        # If nothing is found, it is set as "Unkown"
        if result == []:
            return [fill]

        # If more than one info is found, only the first is considered
        elif len(result) > 1:
            result = [result[0]]

        return result

    def get_modality(self, hand: list[str]) -> list[str]:
        """
        Get name of poker modality (for example, "Hold'em No Limit").

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with just one string, i.e. the name of the modality.
        """
        # Pattern to extract
        regex = r",\s+\S+\s+(.*?)\s+-\s+(?:Level|Match)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result)

        # Return list with exactly one element
        return result

    def get_tourn_id(self, hand: list[str]) -> list[str]:
        """
        Get ID of a specific tournament (for example, "3285336035").

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with just one string, i.e. the ID of the tournament.
        """
        # Pattern to extract
        regex = r"Tournament #(\d+),.*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result)

        # Return list with exactly one element
        return result

    def get_hand_id(self, hand: list[str]) -> list[str]:
        """
        Get ID of a specific hand (for example, "230689290677").

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with just one string, i.e. the ID of the hand.
        """
        # Pattern to extract
        regex = r"Hand #(\d+):.*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result)

        return result

    def get_players(self, hand: list[str]) -> list[str]:
        """
        Get list of active players in a specific hand.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the names of the active players.
        """
        # Pattern to extract
        regex = r"\nSeat \d{1}: (.*) \(\S+ in chips"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        players = re.findall(regex, target)

        # Normalize output
        players = [re.escape(x) for x in players]

        return players

    def get_number_of_active_players(self, hand: list[str]) -> list[int]:
        """
        Get the number of active players in a specific hand.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with one integer element, the number of players.
        """
        # Pattern to extract
        regex = r"\nSeat \d{1}: (.*) \(.*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex and count the items found
        n = len(re.findall(regex, target))

        # Normalize output
        result = [n]

        return result

    def get_buyin(self, hand: list[str]) -> list[str]:
        """
        Get buy-in paid.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the value of the buy-in paid.
        """
        # Pattern to extract
        regex = r"\d+, (\S+) .*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        buyin = re.findall(regex, target)

        # Normalize output
        buyin = self._guarantee_unicity(buyin)

        return buyin

    def get_level(self, hand: list[str]) -> list[str]:
        """
        Get level of the tournament.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the level of the tournament (for example, ["IV"]).
        """
        # Pattern to extract
        regex = r" Level (\S+) .*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        return result

    def get_blinds(self, hand: list[str]) -> list[list[float]]:
        """
        Get current blinds of the tournament.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the list of blinds (for example, [['10', '20']]).
        """
        # Pattern to extract
        regex = r" Level \w+ \((\d+)/(\d+)\).*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = [[float(x) for x in re.findall(regex, target)[0]]]

        return result

    def get_ante(self, hand: list[str]) -> list[float | None]:
        """
        Get current ante of the tournament.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the current ante of the tournament (for example, [10]).
        """
        # Pattern to extract
        regex = r"posts the ante (\d+)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Convert to integer
        result = [float(x) for x in result if x.isdigit()]

        # This list cannot be empty
        if result == []:
            return [None]

        # Get the maximum value and return in a list
        result = [max(result)]

        return result

    def get_time(self, hand: list[str]) -> list[pd.Timestamp]:
        """
        Get current datetime of the tournament.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the current datetime (for example, ['2020-11-06 10:02:19']).
        """
        # Pattern to extract
        regex = r"(\d{4}/\d{2}/\d{2} \d{1,2}:\d{1,2}:\d{1,2})"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize string
        result = [pd.to_datetime(x) for x in result]

        # Normalize output
        result = self._guarantee_unicity(result)

        return result

    def get_table_size(self, hand: list[str]) -> list[int]:
        """
        Get total number of players per table in the tournament.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the number of players per table (for example, ['9']).
        """
        # Pattern to extract
        regex = r"(\d)-max"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = [int(re.findall(regex, target)[0])]

        return result

    def get_table_id(self, hand: list[str]) -> list[str]:
        """
        Get ID of a specific hand (for example, "1").

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with just one string, i.e. the ID of the table.
        """
        # Pattern to extract
        regex = r"Table \'\d+ (\d+)\' .*"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        return result

    def get_owner_cards(self, hand: list[str]) -> list[str]:
        """
        Get cards from the owner of the logs (for example, ['As', '5s']).

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with a list of the owners' cards, like [['As', '5s']].
        """
        # Pattern to extract
        regex = r"Dealt to .* \[(\S+) (\S+)\]"

        # Get the first content of a played hand
        target = hand[1]

        # Apply regex
        result = re.findall(regex, target)

        return result

    def get_owner(self, hand: list[str]) -> list[str]:
        """
        Get name of the owner of the logs (for example, 'garciamurilo').

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the name of the owner, like ['garciamurilo'].
        """
        # Pattern to extract
        regex = r"Dealt to (.*) \[.*"

        # Get the first content of a played hand
        target = hand[1]

        # Apply regex
        result = re.findall(regex, target)

        return result

    def get_stack(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get the current stack of the player (for example, '500').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the stack of the player (for example, ['500']).
        """
        # Pattern to extract
        regex = rf"Seat \d+: {player} \((\d+) in chips\)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result if x.isdigit()]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_posted_blind(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get blind posted by the player (for example, '30').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the blide posted by the player (for example, ['30']).
        """
        # Pattern to extract
        regex = rf"{player}: posts \w+ blind (\d+)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result if x.isdigit()]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_posted_ante(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get ante posted by the player (for example, '10').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the ante posted by the player (for example, ['10']).
        """
        # Pattern to extract
        regex = rf"{player}: posts the ante (\d+)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result if x.isdigit()]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_actions(
        self, player: str, hand: list[str], stage: str
    ) -> list[list[tuple[str, str]]]:
        """
        Get action the player (for example, ('call', '50')).

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered

        Returns:
            list: List of actions in a stage, like [('call', '50'),  ('fold', '')].
        """
        # Initial value to be returned
        fill_empty = [[("", "")]]

        # Filter relevant data of a specific stage
        hand = [x for x in hand if stage in x]
        if hand == []:
            return fill_empty

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Pattern to extract
        regex = rf"{player}: (\w+) (\d+)?"

        # Apply regex
        result = re.findall(regex, target)

        # Guarantee that empty list will not be return
        if result == []:
            return fill_empty

        return [result]

    def get_allin(self, player: str, hand: list[str], stage: str) -> list[bool]:
        """
        Get if the player is all-in (it is boolean, True or False).

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered

        Returns:
            list: List containing True or False, like [True].
        """
        # Filter relevant data of a specific stage
        hand = [x for x in hand if stage in x]

        # If a specific stage is not available, return False
        if hand == []:
            return [False]

        # Pattern to extract
        regex = rf"{player}: .* (all-in)"

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Apply regex
        all_in_data = re.findall(regex, target)

        # Was some all-in action found? (True/False)
        result = all_in_data != []

        return [result]

    def get_showed_card(
        self, player: str, hand: list[str]
    ) -> list[list[str]] | list[list[None]]:
        """
        Get cards, if the player showed them.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the cards of the player, like [['As', 'Ks']].
        """
        # Pattern to extract
        regex = rf"{player} .*(?:mucked|showed) \[(\S+) (\S+)\]"

        # Defauld value for empty values
        fill_empty = [[None, None]]

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Guarantee that empty list will not be return
        if result == []:
            return fill_empty

        return result

    def get_card_combination(self, player: str, hand: list[str]) -> list[str]:
        """
        Get cards combination, if the player went to showdown.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the card combination, like ['a pair of Kings'].
        """
        # Pattern to extract
        regex = rf"{player}.*showed.*with (.*)"

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_result(self, player: str, hand: list[str]) -> list[str]:
        """
        Get the result of a showdown for a player.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the result, like ['won'].
        """
        # Pattern to extract
        regex = rf"Seat \d+: {player} .*(\bfolded\b|\bwon\b|\blost\b|\bmucked\b).*"

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result, fill="non-sd win")

        return result

    def get_balance(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get how much a player won from the pot.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the balance, like ['320'].
        """
        # Pattern to extract
        regex = rf"Seat \d: {player}.*(?:collected|won) \((\d+)\)"

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [
            float(x) if x is not None else None
            for x in self._guarantee_unicity(result, fill=None)
        ]

        return result

    def get_board(
        self, hand: list[str], stage: str
    ) -> (
        list[tuple[str, str, str]]  # Flop
        | list[tuple[str, str, str, str]]  # Turn
        | list[tuple[str, str, str, str, str]]  # River
        | list[tuple[()]]
    ):
        """
        Get the cards on the board.

        Args:
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered

        Returns:
            list: List containing the cards on the board, like [('As', 'Ks', '2h')].
        """
        # Defauld value for empty values
        fill_empty = [()]

        # Filter hands and reduce strings (to speed up the search)
        hand = [x[0:30] for x in hand if stage in x]

        # If no info for a specific stage is found, return empty values
        if hand == []:
            return fill_empty

        # Pattern to extract board, that is between [ and ]
        pre_regex = r"\[(.*)\]"

        # Pattern to extract cards on the board
        regex_cards = r"\b([\dTJQKA]{1}[shdc]{1})\b"

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Apply regex
        pre_selection = re.findall(pre_regex, target)
        if pre_selection == []:
            return fill_empty
        else:
            result = re.findall(regex_cards, pre_selection[0])

        return [tuple(result)]

    def get_seat(self, player: str, hand: list[str]) -> list[int]:
        """
        Get the seat number of the player.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the number of the seat, like ['1'].
        """
        # Pattern to extract
        regex = rf"\nSeat (\d+): {player}.*"

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [int(x) for x in self._guarantee_unicity(result, fill=None)]

        return result

    def get_position(self, player: str, hand: list[str]) -> list[str]:
        """
        Get position of the player (for example, 'button').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the position of the player, like ['small blind'].
        """
        # Pattern to extract
        regex = rf"Seat \d+\: {player} \((button|small blind|big blind)\) "

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_final_rank(self, player: str, hand: list[str]) -> list[int]:
        """
        Get final rank of the player (for example, '14').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the final rank of the player, like ['1'].
        """
        # Filter content from SHOW_DOWN
        hand = [x for x in hand if "SHOW DOWN ***" in x]

        if hand != []:

            # Pattern to extract
            regex = rf"{player} finished the tournament in (\d+).*"

            # Get the first SHOW_DOWN content of a played hand
            target = hand[0]

            # Apply regex
            list_of_results = re.findall(regex, target)

            # Normalize
            list_of_int = [
                int(x) if x.replace(".", "").isdigit() else -1 for x in list_of_results
            ]

            # Try another pattern, if nothing is found
            if list_of_int == []:

                # Pattern to extract
                regex = rf"{player} (wins) the tournament"

                # Apply regex again
                result_of_regex = re.findall(regex, target)

                # Position 1, if wins
                if result_of_regex == ["wins"]:
                    return [1]
                else:
                    return [-1]
            else:
                # Get the maximum value and return in a list
                result = [max(list_of_int)]

                return result

        # If no SHOW_DOWN content is found, return -1
        else:
            return [-1]

    def get_prize(self, player: str, hand: list[str]) -> list[float] | list[None]:
        """
        Get prize of the player (for example, '$50.00').

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the prize, like ['$50.00'].
        """
        # Filter content from SHOW_DOWN
        hand = [x for x in hand if "SHOW DOWN ***" in x]

        if hand != []:

            # Pattern to extract
            regex = rf"{player} .* (?:and receives|and received) (\S+)"

            # Get the first SHOW_DOWN content of a played hand
            target = hand[0]

            # Apply regex
            result_of_regex = re.findall(regex, target)

            # Normalize
            final_result = [float(x) for x in result_of_regex if str(x).isdigit()]

            # Normalize output
            if final_result == []:
                return [None]
            else:
                return final_result

        else:
            return [None]
