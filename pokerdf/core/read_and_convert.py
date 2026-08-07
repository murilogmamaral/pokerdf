import os
import pandas as pd
from typing import List
from joblib import Parallel, delayed
from pokerdf.validation.pydantic_modules import ValidateInput
from pokerdf.utils.strings import PLATFORM
from pokerdf.regex.regex_execution import (
    capture_common_data,
    capture_general_data_of_the_hand,
    capture_specific_data_of_the_player,
    r,
)
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)


def get_files_paths(path: str) -> List[str]:
    """
    Retrieve the paths of the hand history files in the specified directory.

    Only files following the PokerStars naming convention are kept,
    i.e. names starting with "HH" and ending with ".txt".

    Args:
        path (str): The directory path to search for files.

    Returns:
        List[str]: Sorted list of full paths of the hand history files.
    """
    # Get files names
    list_of_all_files_names = os.listdir(path)

    # Order by ID
    list_of_all_files_names.sort()

    # Keep relevant files only
    list_of_selected_files = [
        file_name
        for file_name in list_of_all_files_names
        if file_name.startswith("HH") and file_name.endswith(".txt")
    ]

    # Compose the final path for each file
    paths = [os.path.join(path, file_name) for file_name in list_of_selected_files]

    return paths


def compose_dataframe() -> pd.DataFrame:
    """
    Create an empty DataFrame with predefined columns and dtypes to hold poker data.

    This is the single source of truth for the output schema: every converted
    hand is concatenated onto this frame, keeping column order and types stable.

    Returns:
        pd.DataFrame: An empty DataFrame with predefined columns and dtypes.
    """
    # Compose default dataframe
    df = pd.DataFrame(
        {
            "Modality": pd.Series(dtype="object"),
            "TableSize": pd.Series(dtype="int64"),
            "BuyIn": pd.Series(dtype="object"),
            "TournID": pd.Series(dtype="object"),
            "TableID": pd.Series(dtype="object"),
            "HandID": pd.Series(dtype="object"),
            "LocalTime": pd.Series(dtype="datetime64[ns]"),
            "Level": pd.Series(dtype="object"),
            "Ante": pd.Series(dtype="float64"),
            "Blinds": pd.Series(dtype="object"),
            "Owner": pd.Series(dtype="object"),
            "OwnersHand": pd.Series(dtype="object"),
            "Playing": pd.Series(dtype="int64"),
            "Player": pd.Series(dtype="object"),
            "Seat": pd.Series(dtype="int64"),
            "PostedAnte": pd.Series(dtype="float64"),
            "Position": pd.Series(dtype="object"),
            "PostedBlind": pd.Series(dtype="float64"),
            "Stack": pd.Series(dtype="float64"),
            "PreflopAction": pd.Series(dtype="object"),
            "FlopAction": pd.Series(dtype="object"),
            "TurnAction": pd.Series(dtype="object"),
            "RiverAction": pd.Series(dtype="object"),
            "AnteAllIn": pd.Series(dtype="bool"),
            "PreflopAllIn": pd.Series(dtype="bool"),
            "FlopAllIn": pd.Series(dtype="bool"),
            "TurnAllIn": pd.Series(dtype="bool"),
            "RiverAllIn": pd.Series(dtype="bool"),
            "BoardFlop": pd.Series(dtype="object"),
            "BoardTurn": pd.Series(dtype="object"),
            "BoardRiver": pd.Series(dtype="object"),
            "ShowDown": pd.Series(dtype="object"),
            "CardCombination": pd.Series(dtype="object"),
            "Result": pd.Series(dtype="object"),
            "Balance": pd.Series(dtype="float64"),
            "FinalRank": pd.Series(dtype="int64"),
            "Prize": pd.Series(dtype="float64"),
        }
    )
    return df


def apply_regex(txt: str) -> pd.DataFrame:
    """
    Apply regex functions to parse the hand history text and collect relevant data.

    Each hand is parsed at three levels: tournament-wide data, hand-wide data
    and player-specific data. The output has one row per player per hand, and
    every row is validated with pydantic before being appended.

    Args:
        txt (str): The text content of the poker hand history file.

    Returns:
        pd.DataFrame: A DataFrame containing the parsed data from the hand history.
    """
    # Generate dataframe
    df = compose_dataframe()

    # Splitting tournament's hands in a list
    list_of_hands_as_text = txt.split(f"{PLATFORM} ")

    # Cleaning list_of_hands_as_text (BOM marker, None and empty entries)
    string_to_remove = "\ufeff"
    if string_to_remove in list_of_hands_as_text:
        list_of_hands_as_text.remove(string_to_remove)
    list_of_hands_as_text = [hand for hand in list_of_hands_as_text if hand is not None]
    list_of_hands_as_text = [hand for hand in list_of_hands_as_text if len(hand) > 0]

    # Capture common info about the tournament
    common = capture_common_data(list_of_hands_as_text[0].split("\n*** "))

    for hand in list_of_hands_as_text:

        # Split hand in stages (pre-flop/flop/turn/river)
        splited_hand = hand.split("\n*** ")

        # Capture general info of the hand
        general = capture_general_data_of_the_hand(splited_hand)

        # Get players
        players = r.get_players(splited_hand)

        # Iterate over players
        for player in players:

            # Capture specific info of players' actions
            specific = capture_specific_data_of_the_player(splited_hand, player)

            # Combine collected info
            collected_data = {**common, **general, **specific}

            # Validate
            ValidateInput(**collected_data)

            # Convert to dataframe
            result = pd.DataFrame(collected_data)

            # Concat to the final results
            df = pd.concat([df, result])

    return df


def convert_txt_to_tabular_data(path: str) -> pd.DataFrame:
    """
    Convert a poker hand history text file into a structured DataFrame.

    This is the entry point for building incremental pipelines: it converts a
    single hand history file, with one row per player per hand.

    Args:
        path (str): The path to the .txt file containing the hand history.

    Returns:
        pd.DataFrame: A DataFrame with parsed data from the hand history.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as file:
        txt = file.read()
        result = apply_regex(txt)

    return result


def _save_log(msg: str, destination: str, file_name: str) -> None:
    """
    Append a log message to a file, creating the file if it does not exist.

    Args:
        msg (str): The message to be logged.
        destination (str): The folder where the log file will be saved.
        file_name (str): The name of the log file (for example, "success.txt").
    """
    # Compose path of the log
    path = os.path.join(destination, file_name)

    # Open the file
    file = open(path, "a")

    # Write content
    file.write(msg + "\n")

    # Close the writing process
    file.close()


class DataProcessing:
    """
    Process one poker hand history file and save it as .parquet, logging the result.

    Attributes:
        path (str): The path to the hand history file.
        destination (str): The directory where the processed data will be saved.
    """

    def __init__(self, path: str, destination: str) -> None:
        self.path = path
        self.destination = destination

    def run(self) -> None:
        """
        Trigger the data processing.

        Converts the file to a DataFrame and saves it as
        "{DATE_OF_TOURNAMENT}-T{TOURNAMENT_ID}.parquet" in the destination
        folder. Successes are appended to success.txt and failures to
        fail.txt (with the error message); a failure never raises.
        """
        try:

            # Convert text to pd.DataFrame
            df = convert_txt_to_tabular_data(self.path).reset_index(drop=True)

            # Compose name of the .parquet file (the Tournament ID + the Local Time)
            clean_datetime = str(df.LocalTime[0]).replace("-", "")[:8]
            file_name = clean_datetime + "-T" + str(df.TournID[0]) + ".parquet"

            # Path to save the file
            destination_path = os.path.join(self.destination, file_name)

            # Save the table
            df.to_parquet(destination_path, index=False)

            # Log / print DONE status
            msg = "   DONE: " + self.path.split("/")[-1]
            _save_log(msg, self.destination, "success.txt")
            print(msg)

        except Exception as e:

            # Log / print FAIL status
            msg = "   FAIL: " + self.path.split("/")[-1]
            msg += " (" + str(e) + ")"
            _save_log(msg, self.destination, "fail.txt")
            print(msg)


def execute_in_parallel(source: str, destination: str) -> None:
    """
    Convert all hand history files of a folder in parallel, using all CPU cores.

    Args:
        source (str): Directory containing the hand history .txt files.
        destination (str): Directory where the .parquet files and logs are saved.
    """
    # Get all paths
    all_paths = get_files_paths(source)

    # Run a DataProcessing per file in parallel
    Parallel(n_jobs=-1)(
        delayed(DataProcessing(path, destination).run)() for path in all_paths
    )
