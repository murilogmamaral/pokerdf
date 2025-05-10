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
    Retrieve the paths of relevant files in the specified directory.

    Args:
        path (str): The directory path to search for files.

    Returns:
        List[str]: A list of file paths that match the criteria.
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
    Create an empty DataFrame with predefined columns to hold poker data.

    Returns:
        pd.DataFrame: An empty DataFrame with predefined columns.
    """
    # Compose default dataframe
    df = pd.DataFrame(
        columns=[
            "Modality",
            "TableSize",
            "BuyIn",
            "TournID",
            "TableID",
            "HandID",
            "LocalTime",
            "Level",
            "Ante",
            "Blinds",
            "Owner",
            "OwnersHand",
            "Playing",
            "Player",
            "Seat",
            "PostedAnte",
            "Position",
            "PostedBlind",
            "Stack",
            "PreflopAction",
            "FlopAction",
            "TurnAction",
            "RiverAction",
            "AnteAllIn",
            "PreflopAllIn",
            "FlopAllIn",
            "TurnAllIn",
            "RiverAllIn",
            "BoardFlop",
            "BoardTurn",
            "BoardRiver",
            "ShowDown",
            "CardCombination",
            "Result",
            "Balance",
            "FinalRank",
            "Prize",
        ],
        data=None,
    )
    return df


def apply_regex(txt: str) -> pd.DataFrame:
    """
    Apply regex functions to parse the hand history text and collect relevant data.

    Args:
        txt (str): The text content of the poker hand history file.

    Returns:
        pd.DataFrame: A DataFrame containing the parsed data from the hand history.
    """
    # Generate dataframe
    df = compose_dataframe()

    # Spliting tournament's hands in a list
    list_of_hands_as_text = txt.split(f"{PLATFORM} ")

    # Cleaning list_of_hands_as_text
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
    Save a log message to a file.

    Args:
        msg (str): The message to be logged.
        destination (str): The folder where the log file will be saved.
        file_name (str): The name of the log file.
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
    Process and save a poker hand history file, logging the result.

    Args:
        path (str): The path to the hand history file.
        destination (str): The directory where the processed data will be saved.
    """

    def __init__(self, path: str, destination: str) -> None:
        self.path = path
        self.destination = destination

    def run(self) -> None:
        """
        Trigger the data processing.
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
    Function to run the DataProcessing with multiple cores
    """

    # Get all paths
    all_paths = get_files_paths(source)

    # Run a DataProcessing in parallel.
    Parallel(n_jobs=-1)(
        delayed(DataProcessing(path, destination).run)() for path in all_paths
    )
