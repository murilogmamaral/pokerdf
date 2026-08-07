import datetime
import os
import sys

from pokerdf.core.read_and_convert import execute_in_parallel
from pokerdf.modeling.star_schema import build_star_schema
from pokerdf.utils.strings import (
    HAND_HISTORY_EXTENSION,
    MODELING_FOLDER,
    OUTPUT_FOLDER,
    PARQUET_EXTENSION,
    SESSION_ID_FORMAT,
)


def _validate_source_directory(
    path: str, extension: str, content_description: str
) -> None:
    """
    Validate that the source path is a directory with the expected content.

    Args:
        path (str): The source path informed in the command line.
        extension (str): Extension the directory must contain at least once.
        content_description (str): Description of the expected files, used in
            the error message.

    Raises:
        SystemExit: If the path does not exist, is not a directory, is empty
            or does not contain any file with the expected extension.
    """
    # Check if the source path exists
    if not os.path.exists(path):
        print(f"The source path '{path}' does not exist.")
        sys.exit(1)
    # Check if the source path is a directory
    if not os.path.isdir(path):
        print(f"The source path '{path}' is not a directory.")
        sys.exit(1)
    # Check if the source path is empty
    if not os.listdir(path):
        print(f"The source path '{path}' is empty.")
        sys.exit(1)
    # Check if the source path contains the expected files
    if not any(file.endswith(extension) for file in os.listdir(path)):
        print(f"The source path '{path}' does not contain any {content_description}.")
        sys.exit(1)


def _create_destination_folder(root_folder: str) -> str:
    """
    Create the destination folder of a new session.

    Args:
        root_folder (str): Root folder of the command (for example, "output").

    Returns:
        str: The created path, in the format ./{root_folder}/{SESSION_ID}.
    """
    # Generate session ID
    session_id = datetime.datetime.now().strftime(SESSION_ID_FORMAT)

    # Generate destination path
    destination_path = f"./{root_folder}/{session_id}"

    # Create folder
    os.makedirs(destination_path)

    return destination_path


def _print_elapsed_time(start_time: datetime.datetime) -> None:
    """
    Print how long the processing took, in a readable format.

    Args:
        start_time (datetime.datetime): Moment when the processing started.
    """
    # Get end time
    end_time = datetime.datetime.now()
    elapsed_time = end_time - start_time

    # Get the completed time in hours, minutes, and seconds
    hours, remainder = divmod(elapsed_time.total_seconds(), 3600)
    minutes, seconds = divmod(remainder, 60)

    # Print the completed time in a readable format
    print(
        f"Processing completed in {int(hours)} hours, {int(minutes)} minutes, and {int(seconds)} seconds."
    )


def main() -> None:
    """
    Main function to process command line arguments and execute a command.

    - 'convert': converts hand history .txt files into .parquet files,
      saving them in ./output/{SESSION_ID}.
    - 'modeling': reads converted .parquet files and splits them into a star
      schema (one fact table and four dimensions), saving the five tables
      in ./modeling/{SESSION_ID}.

    Raises:
        SystemExit: If there are not enough arguments or if an invalid command is provided.
    """

    if len(sys.argv) < 3:
        print("Usage: pokerdf convert <path> | pokerdf modeling <path>")
        sys.exit(1)

    command = sys.argv[1]
    source_path = sys.argv[2]

    if command == "convert":

        # The source must be a directory with hand history files
        _validate_source_directory(
            source_path, HAND_HISTORY_EXTENSION, "poker hand history files"
        )

        # Get start time
        start_time = datetime.datetime.now()

        # Create the destination folder of the session
        destination_path = _create_destination_folder(OUTPUT_FOLDER)

        # Execute pipeline
        execute_in_parallel(source=source_path, destination=destination_path)

        # Report the elapsed time
        _print_elapsed_time(start_time)

    elif command == "modeling":

        # The source must be a directory with converted .parquet files
        _validate_source_directory(
            source_path, PARQUET_EXTENSION, f"{PARQUET_EXTENSION} files"
        )

        # Get start time
        start_time = datetime.datetime.now()

        # Create the destination folder of the session
        destination_path = _create_destination_folder(MODELING_FOLDER)

        # Build the star schema (one fact table and four dimensions)
        number_of_rows = build_star_schema(
            source=source_path, destination=destination_path
        )

        # Print a summary of the generated tables
        for name, rows in number_of_rows.items():
            print(f"   DONE: {name}{PARQUET_EXTENSION} ({rows} rows)")

        # Report the elapsed time
        _print_elapsed_time(start_time)

    else:
        print(f"The command '{command}' does not exist.")


if __name__ == "__main__":
    main()
