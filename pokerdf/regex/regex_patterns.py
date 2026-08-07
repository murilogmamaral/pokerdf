import re
from typing import Any
import pandas as pd


class RegexPatterns:
    """
    Contains all functions with regex patterns to extract data from the text files
    """

    def __init__(self) -> None:
        """
        Initialize the RegexPatterns class. No state is required.
        """
        pass

    def _guarantee_unicity(
        self, result: list[Any], fill: str | int | None = "Unknown"
    ) -> list[Any]:
        """
        Guarantee that the returned result is a list with exactly one element.

        Args:
            result (list): List of values extracted with regex.
            fill (str | int | None): Value to use when nothing is captured by the regex. Default is "Unknown".

        Returns:
            list: List with exactly one element (the first match, or the fill value).
        """
        # If nothing is found, use the fill value
        if result == []:
            return [fill]

        # If more than one match is found, only the first is considered
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
            list: List with the names of the active players. Names are escaped
                with re.escape, so they can be safely interpolated into the
                regex patterns of the player-specific methods.
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
            list: List with the list of blinds as floats (for example, [[10.0, 20.0]]).
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
            list: List with the current ante of the tournament (for example, [10.0]),
                or [None] if no ante was posted in the hand.
        """
        # Pattern to extract
        regex = r"posts the ante (\d+)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Convert to float
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
            list: List with the current datetime as pd.Timestamp
                (for example, [Timestamp('2020-11-06 10:02:19')]).
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
            list: List with the number of players per table (for example, [9]).
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
        Get ID of the table inside the tournament (for example, "1").

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
        Get the current stack of the player at the start of the hand.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the stack of the player (for example, [500.0]),
                or [None] if the stack cannot be captured.
        """
        # Pattern to extract
        regex = rf"Seat \d+: {player} \((\d+) in chips"

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
        Get blind posted by the player (small or big blind).

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the blind posted by the player (for example, [30.0]),
                or [None] if the player did not post a blind.
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
        Get ante posted by the player.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the ante posted by the player (for example, [10.0]),
                or [None] if the player did not post an ante.
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
        Get the actions taken by the player during a specific stage.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered
                (for example, "HOLE CARDS ***" or "FLOP ***").

        Returns:
            list: List with the list of (action, amount) tuples of the stage,
                like [[('calls', '50'), ('folds', '')]]. The amount is an empty
                string when the action has no associated value. If the stage is
                not present or the player did not act, returns [[('', '')]].
        """
        # Default value when the player has no action in the stage
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

        # Guarantee that an empty list will not be returned
        if result == []:
            return fill_empty

        return [result]

    def get_allin(self, player: str, hand: list[str], stage: str) -> list[bool]:
        """
        Check whether the player went all-in during a specific stage.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered
                (for example, "HOLE CARDS ***" or " posts the ante ").

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
        Get the cards of the player, if they were showed or mucked at showdown.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the cards of the player, like [('As', 'Ks')],
                or [[None, None]] if the player did not reveal the cards.
        """
        # Pattern to extract
        regex = rf"{player} .*(?:mucked|showed) \[(\S+) (\S+)\]"

        # Default value for empty results
        fill_empty = [[None, None]]

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Guarantee that an empty list will not be returned
        if result == []:
            return fill_empty

        return result

    def get_card_combination(self, player: str, hand: list[str]) -> list[str]:
        """
        Get the card combination, if the player went to showdown.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the card combination, like ['a pair of Kings'],
                or [None] if the player did not show a combination.
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
        Get the result of the hand for a player (folded, won, lost or mucked).

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the result, like ['won']. When the player
                collected the pot without a showdown, returns ['non-sd win'].
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
        Get how much a player collected from the pot.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the balance, like [320.0], or [None]
                if the player did not collect anything.
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

    def get_uncalled_returned(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get the total amount of uncalled bets returned to the player in the hand.

        A bet (or the excess of a raise over an all-in) that nobody calls is
        given back to the player with an "Uncalled bet (X) returned to" line.
        The same player can receive more than one return in the same hand
        (for example, the excess of a raise over a short all-in and, later,
        an uncalled bet on another street), so the amounts are summed.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the total amount returned to the player
                (for example, [320.0]), or [None] if nothing was returned.
        """
        # Pattern to extract. The end-of-line anchor prevents a player name
        # from matching a longer name that starts with it
        regex = rf"Uncalled bet \((\d+(?:\.\d+)?)\) returned to {player}\s*$"

        # The return can happen at any stage, so search the whole hand
        target = "\n".join(hand)

        # Apply regex
        result = re.findall(regex, target, flags=re.MULTILINE)

        # Nothing returned to the player in the hand
        if result == []:
            return [None]

        # Sum all the returns of the hand
        return [sum(float(x) for x in result)]

    def get_board(
        self, hand: list[str], stage: str
    ) -> (
        list[tuple[str, str, str]]  # Flop
        | list[tuple[str, str, str, str]]  # Turn
        | list[tuple[str, str, str, str, str]]  # River
        | list[tuple[()]]
    ):
        """
        Get the cards on the board at a specific stage.

        Args:
            hand (list): List of texts from a specific hand.
            stage (str): Name of the stage to be considered
                (for example, "FLOP ***", "TURN ***" or "RIVER ***").

        Returns:
            list: List containing the tuple of cards on the board, like
                [('As', 'Ks', '2h')] for the flop, growing to 4 cards on the
                turn and 5 on the river. Returns [()] if the stage was not reached.
        """
        # Default value for empty results
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
            list: List containing the number of the seat, like [1].
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
        Get position of the player (button, small blind or big blind).

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the position of the player, like ['small blind'],
                or [None] if the player had no special position.
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
        Get final rank of the player in the tournament, if defined in the hand.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the final rank of the player, like [3] when the
                player is eliminated in the hand, or [1] when the player wins the
                tournament. Returns [-1] when the rank is not defined in the hand.
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
        Get prize received by the player, if awarded in the hand.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the prize as captured from the text, without
                the currency symbol (for example, ['6.00']), or [None] if no
                prize was awarded to the player in the hand.
        """
        # Filter content from SHOW_DOWN
        hand = [x for x in hand if "SHOW DOWN ***" in x]

        if hand != []:

            # Pattern to extract
            regex = rf"{player} .* (?:and receives|and received) (?:[$€£]?)\s*(\d+(?:\.\d+)?)"

            # Get the first SHOW_DOWN content of a played hand
            target = hand[0]

            # Apply regex
            final_result = re.findall(regex, target)[:1]

            # Normalize output
            if final_result == []:
                return [None]
            else:
                return final_result

        else:
            return [None]
