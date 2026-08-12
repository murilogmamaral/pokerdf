import re
from datetime import timedelta, timezone
from typing import Any
import pandas as pd

from pokerdf.utils.columns import HandResult

# Every moment in the converted data is expressed in CET, as a fixed offset
# of one hour from UTC: it never shifts with daylight saving, so the
# difference between two moments is always the time that really elapsed
CET = timezone(timedelta(hours=1))

# The header of a hand closes with the moment it was dealt, in one of two
# shapes: the clock of the player followed by the time of the platform in
# brackets ("2020/10/14 10:33:59 BRT [2020/10/14 9:33:59 ET]"), or the time
# of the platform alone, when the client wrote no local time
# ("2021/02/22 17:51:13 ET"). One pattern reads both: the local moment and
# its time zone are optional, the Eastern Time moment is always there
_MOMENT = r"\d{4}/\d{2}/\d{2} \d{1,2}:\d{1,2}:\d{1,2}"
HEADER_MOMENTS = re.compile(rf" - (?:({_MOMENT}) ([A-Z]+) \[)?({_MOMENT}) ET\]?")


class RegexPatterns:
    """
    Contains all functions with regex patterns to extract data from the text files.

    The player-specific methods take the nickname exactly as it appears in the
    hand history and escape it themselves before interpolating it into their
    pattern: a nickname is arbitrary text, and characters like ".", "-", "(" or
    a space would otherwise be read as regex syntax. Escaping at the point of
    use keeps the nicknames the methods return - and the ones that reach the
    converted data - identical to the originals.
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
            list: List with the names of the active players, exactly as they
                appear in the hand history. The player-specific methods escape
                them before building their patterns.
        """
        # Pattern to extract
        regex = r"\nSeat \d{1}: (.*) \(\S+ in chips"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        players = re.findall(regex, target)

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

    def _eastern_to_cet(self, moment: pd.Timestamp) -> pd.Timestamp:
        """
        Convert a moment written in Eastern Time to CET.

        Args:
            moment (pd.Timestamp): Naive moment, as written by the platform
                in Eastern Time.

        Returns:
            pd.Timestamp: The same instant as a naive CET moment.
        """
        # Eastern Time follows the daylight saving of the United States, so
        # its distance to UTC changes through the year and only the time
        # zone database resolves it. On the night the clocks go back an hour
        # happens twice and the first one is taken; the hour that does not
        # exist when they go forward is shifted into the following one
        eastern = moment.tz_localize(
            "America/New_York", ambiguous=True, nonexistent="shift_forward"
        )

        return eastern.tz_convert(CET).tz_localize(None)

    def _get_header_moments(self, hand: list[str]) -> tuple[str | None, ...]:
        """
        Read the moments written in the header of the hand.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            tuple: (local moment, time zone of the player, Eastern Time
                moment), each as written. The first two are None when the
                client wrote no local time.
        """
        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        found = HEADER_MOMENTS.search(target)

        return found.groups() if found else (None, None, None)

    def get_time(self, hand: list[str]) -> list[pd.Timestamp]:
        """
        Get the moment the hand was dealt, in CET.

        The time of the platform, in Eastern Time, is the one moment present
        in every hand: the local time of the player is only written when the
        client knows a time zone of its own. Reading whichever moment comes
        first would mix time zones in the same column, so Eastern Time is
        the anchor and CET is derived from it.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the moment of the hand in CET as pd.Timestamp
                (for example, [Timestamp('2020-11-06 16:02:19')]).
        """
        _, _, eastern = self._get_header_moments(hand)

        # Normalize string and bring the moment to CET
        result = [self._eastern_to_cet(pd.to_datetime(eastern))] if eastern else []

        # Normalize output
        result = self._guarantee_unicity(result)

        return result

    def get_local_time(self, hand: list[str]) -> list[pd.Timestamp | None]:
        """
        Get the moment the hand was dealt, on the clock of the player.

        This is the wall clock the player was looking at, which is what the
        analysis of fatigue and of playing habits needs. The platform only
        writes it when the client has a time zone of its own to report, so
        it can be absent - and then it is simply not known, as nothing else
        in the file reveals where the player was.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the local moment as pd.Timestamp, or [None] when
                the client wrote no local time.
        """
        local, _, _ = self._get_header_moments(hand)

        # Normalize output
        result = [pd.to_datetime(local)] if local else [None]

        return result

    def get_timezone(self, hand: list[str]) -> list[str | None]:
        """
        Get the time zone of the player, as the platform abbreviated it.

        The abbreviation is what the client wrote ("BRT", "CET", "MSK") and
        is kept as provenance, to be read by a person. It must not be used
        to compute an offset: the same abbreviation means different things
        in different countries ("CST" is UTC-6 in the United States and
        UTC+8 in China). The offset of the player is the difference between
        the local moment and the one in CET, which is unambiguous.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the abbreviation of the time zone, or [None]
                when the client wrote no local time.
        """
        _, zone, _ = self._get_header_moments(hand)

        # Normalize output
        return [zone] if zone else [None]

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"Seat \d+: {escaped} \((\d+) in chips"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result if x.isdigit()]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_bounty(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get the bounty on the player's head, in knockout tournaments.

        The bounty is listed next to the stack in the seat line, like
        "Seat 1: player (3000 in chips, $0.46 bounty)". The currency symbol
        is dropped, so only the numeric value is captured.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the bounty on the player's head (for example,
                [0.46]), or [None] if the tournament has no bounties.
        """
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"Seat \d+: {escaped} \(\d+ in chips, [$€£]?(\d+(?:\.\d+)?) bounty\)"

        # Get the first content of a played hand
        target = hand[0]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result]
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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"{escaped}: posts \w+ blind (\d+)"

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"{escaped}: posts the ante (\d+)"

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
        escaped = re.escape(player)
        # Default value when the player has no action in the stage
        fill_empty = [[("", "")]]

        # Filter relevant data of a specific stage
        hand = [x for x in hand if stage in x]
        if hand == []:
            return fill_empty

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Pattern to extract
        regex = rf"{escaped}: (\w+) (\d+)?"

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
        escaped = re.escape(player)
        # Filter relevant data of a specific stage
        hand = [x for x in hand if stage in x]

        # If a specific stage is not available, return False
        if hand == []:
            return [False]

        # Pattern to extract
        regex = rf"{escaped}: .* (all-in)"

        # Get the first content of a played hand for a specific stage
        target = hand[0]

        # Apply regex
        all_in_data = re.findall(regex, target)

        # Was some all-in action found? (True/False)
        result = all_in_data != []

        return [result]

    def get_showed_card(
        self, player: str, hand: list[str]
    ) -> list[tuple[str, str | None]] | list[list[None]]:
        """
        Get the cards the player revealed, at showdown or voluntarily.

        At showdown the cards come from the summary ("showed [As Ks]" or
        "mucked [7h Td]"). A player who wins without showdown can still
        show one or both cards voluntarily ("shows [Ah]", "shows [Ah Kd]"),
        which is not mirrored in the summary, so the body of the hand is
        used as a fallback; on single-card shows the second card is None.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the cards of the player, like [('As', 'Ks')]
                or [('Ah', None)], or [[None, None]] if the player did not
                reveal any card.
        """
        escaped = re.escape(player)
        # Pattern to extract from the summary (the second card is optional)
        regex = rf"{escaped} .*(?:mucked|showed) \[(\S+)(?: (\S+))?\]"

        # Default value for empty results
        fill_empty: list[list[None]] = [[None, None]]

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        if result != []:
            first, second = result[0]
            cards: list[tuple[str, str | None]] = [(first, second if second else None)]
            return cards

        # Fallback: voluntary shows only appear in the body of the hand,
        # since the summary line of a winner without showdown carries no
        # cards ("collected"). The second card is optional, like above
        body_regex = rf"{escaped}: shows \[(\S+)(?: (\S+))?\]"
        body_result = re.findall(body_regex, "\n".join(hand))
        if body_result != []:
            first, second = body_result[0]
            cards = [(first, second if second else None)]
            return cards

        return fill_empty

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"{escaped}.*showed.*with (.*)"

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_result(self, player: str, hand: list[str]) -> list[str]:
        """
        Get the outcome of the hand for a player, as a HandResult value.

        The seat line of the player in the summary ends the hand with one of
        four keywords: "folded", or — only on showdown lines — "won", "lost"
        and "mucked". A seat line with none of them belongs to a player who
        collected the pot uncontested ("collected"). Each case is named after
        what it means, following the HandResult conventions.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the result, like ['won at showdown'] or
                ['won without showdown'].
        """
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"Seat \d+: {escaped} .*(\bfolded\b|\bwon\b|\blost\b|\bmucked\b).*"

        # Get the last content of a played hand
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Name the outcome after what the keyword means: "won" and "lost"
        # only ever appear on showdown lines, and a muck is a showdown loss
        # in which the cards were never shown at the table
        vocabulary = {
            "folded": HandResult.FOLDED,
            "won": HandResult.WON_AT_SHOWDOWN,
            "lost": HandResult.LOST_AT_SHOWDOWN,
            "mucked": HandResult.MUCKED_AT_SHOWDOWN,
        }
        result = [vocabulary[keyword] for keyword in result]

        # Normalize output
        result = self._guarantee_unicity(result, fill=HandResult.WON_WITHOUT_SHOWDOWN)

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"Seat \d: {escaped}.*(?:collected|won) \((\d+)\)"

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
        escaped = re.escape(player)
        # Pattern to extract. The end-of-line anchor prevents a player name
        # from matching a longer name that starts with it
        regex = rf"Uncalled bet \((\d+(?:\.\d+)?)\) returned to {escaped}\s*$"

        # The return can happen at any stage, so search the whole hand
        target = "\n".join(hand)

        # Apply regex
        result = re.findall(regex, target, flags=re.MULTILINE)

        # Nothing returned to the player in the hand
        if result == []:
            return [None]

        # Sum all the returns of the hand
        return [sum(float(x) for x in result)]

    def get_bounty_won(self, player: str, hand: list[str]) -> list[float | None]:
        """
        Get the total bounty amount won by the player in the hand.

        Knockout tournaments award bounties in two formats: regular knockouts
        ("wins the $X bounty for eliminating"), where the whole bounty of the
        eliminated player is won, and progressive knockouts ("wins $X for
        eliminating ... and their own bounty increases by $Y to $Z"), where
        the cash part is won and the rest feeds the player's own bounty.
        When two players split an elimination ("wins $X for splitting the
        elimination of"), each one's share is captured. Only the amount
        effectively won is captured, and multiple eliminations in the same
        hand are summed.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the total bounty won by the player (for example,
                [0.46]), or [None] if no bounty was won in the hand.
        """
        escaped = re.escape(player)
        # Patterns to extract, one per knockout format
        regex_regular = (
            rf"{escaped} wins the [$€£]?(\d+(?:\.\d+)?) bounty for eliminating"
        )
        regex_progressive = (
            rf"{escaped} wins [$€£]?(\d+(?:\.\d+)?) "
            rf"for (?:eliminating|splitting the elimination of) "
            rf".* and their own bounty increases"
        )

        # Bounties are awarded at any stage, so search the whole hand
        target = "\n".join(hand)

        # Apply regex
        result = re.findall(regex_regular, target) + re.findall(
            regex_progressive, target
        )

        # No bounty won by the player in the hand
        if result == []:
            return [None]

        # Sum all the bounties of the hand
        return [sum(float(x) for x in result)]

    def get_total_pot_log(self, hand: list[str]) -> list[float | None]:
        """
        Get the total pot of the hand, as reported in the summary.

        This is the value logged by the platform itself ("Total pot 840 |
        Rake 0"), captured to allow independent verification of any pot
        reconstruction done downstream.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the total pot of the hand (for example, [840.0]),
                or [None] if the summary does not report it.
        """
        # Pattern to extract
        regex = r"Total pot (\d+(?:\.\d+)?)"

        # Get the last content of a played hand (the summary)
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_rake(self, hand: list[str]) -> list[float | None]:
        """
        Get the rake of the hand, as reported in the summary.

        Tournament logs report 0 (the fee is charged in the buy-in), but the
        value is captured for completeness and future-proofing.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the rake of the hand (for example, [0.0]),
                or [None] if the summary does not report it.
        """
        # Pattern to extract
        regex = r"\| Rake (\d+(?:\.\d+)?)"

        # Get the last content of a played hand (the summary)
        target = hand[-1]

        # Apply regex
        result = re.findall(regex, target)

        # Normalize output
        result = [float(x) for x in result]
        result = self._guarantee_unicity(result, fill=None)

        return result

    def get_pot_breakdown(self, hand: list[str]) -> list[tuple[float, ...]]:
        """
        Get the decomposition of the pot, as reported in the summary.

        When a player is all-in and the others keep betting, the pot is
        decomposed ("Total pot 9136 Main pot 5820. Side pot 3316. | Rake 0")
        and each portion can be collected by a different player. The
        breakdown is captured as (main pot, side pot, ...) when the hand has
        side pots, or as a single-element tuple with the total pot otherwise,
        so the sum of the breakdown always equals TotalPotLog.

        Args:
            hand (list): List of texts from a specific hand.

        Returns:
            list: List with the tuple of pots (for example, [(5820.0, 3316.0)]),
                or [()] if the summary does not report a pot.
        """
        # Get the last content of a played hand (the summary)
        target = hand[-1]

        # Decomposed pot: the main pot first, then each side pot
        main = re.findall(r"Main pot (\d+(?:\.\d+)?)", target)
        sides = re.findall(r"Side pot(?:-\d+)? (\d+(?:\.\d+)?)", target)
        if main:
            return [tuple(float(x) for x in main + sides)]

        # Single pot: the breakdown is the total itself
        total = re.findall(r"Total pot (\d+(?:\.\d+)?)", target)
        if total:
            return [(float(total[0]),)]

        return [()]

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"\nSeat (\d+): {escaped}.*"

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
        escaped = re.escape(player)
        # Pattern to extract
        regex = rf"Seat \d+\: {escaped} \((button|small blind|big blind)\) "

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

        The finish lines usually follow the showdown, but a hand can end
        without one (for example, a player all-in on the blind post when
        everyone folds), so the whole hand is searched.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the final rank of the player, like [3] when the
                player is eliminated in the hand, or [1] when the player wins the
                tournament. Returns [0] when the log reports the finish without a
                place (for example, club knockout tournaments), and [-1] when the
                rank is not defined in the hand.
        """
        escaped = re.escape(player)
        # The finish can be reported at any stage, so search the whole hand
        target = "\n".join(hand)

        # Pattern to extract
        regex = rf"{escaped} finished the tournament in (\d+).*"

        # Apply regex
        list_of_results = re.findall(regex, target)

        # Normalize
        list_of_int = [
            int(x) if x.replace(".", "").isdigit() else -1 for x in list_of_results
        ]

        # Get the maximum value and return in a list
        if list_of_int != []:
            return [max(list_of_int)]

        # Try another pattern: position 1, if wins
        regex = rf"{escaped} wins the tournament"
        if re.findall(regex, target) != []:
            return [1]

        # Some logs report the finish without a place (for example, club
        # knockout tournaments): 0 marks "finished, place not reported",
        # keeping -1 for "not defined in the hand"
        regex = rf"{escaped} finished the tournament\s*$"
        if re.findall(regex, target, flags=re.MULTILINE) != []:
            return [0]

        return [-1]

    def get_prize(self, player: str, hand: list[str]) -> list[float] | list[None]:
        """
        Get prize received by the player, if awarded in the hand.

        The prize lines usually follow the showdown, but a hand can end
        without one (for example, when the runner-up folds an all-in blind
        post), so the whole hand is searched.

        Args:
            player (str): Name of the player.
            hand (list): List of texts from a specific hand.

        Returns:
            list: List containing the prize as a float, without the currency
                symbol (for example, [6.0]), or [None] if no prize was awarded
                to the player in the hand. Satellite tickets are captured
                through the face value in the ticket name
                (for example, "wins a 'Fast Track $1' ticket" -> [1.0]).
        """
        escaped = re.escape(player)
        # The prize can be awarded at any stage, so search the whole hand
        target = "\n".join(hand)

        # Pattern to extract
        regex = (
            rf"{escaped} .* (?:and receives|and received) (?:[$€£]?)\s*(\d+(?:\.\d+)?)"
        )

        # Apply regex
        final_result = re.findall(regex, target)[:1]

        # Satellite tickets are not cash prizes: the face value in the
        # ticket name is captured instead
        if final_result == []:
            regex_ticket = rf"{escaped} wins a '[^']*\$(\d+(?:\.\d+)?)[^']*' ticket"
            final_result = re.findall(regex_ticket, target)[:1]

        # Normalize output as float, matching the declared output schema
        if final_result == []:
            return [None]

        return [float(x) for x in final_result]
