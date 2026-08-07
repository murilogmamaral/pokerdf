import os
import sys
import datetime

from pokerdf.core.read_and_convert import execute_in_parallel
from pokerdf.modeling.star_schema import build_star_schema


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

        # Check if the source path exists
        if not os.path.exists(source_path):
            print(f"The source path '{source_path}' does not exist.")
            sys.exit(1)
        # Check if the source path is a directory
        if not os.path.isdir(source_path):
            print(f"The source path '{source_path}' is not a directory.")
            sys.exit(1)
        # Check if the source path is empty
        if not os.listdir(source_path):
            print(f"The source path '{source_path}' is empty.")
            sys.exit(1)
        # Check if the source path is a valid poker hand history file
        if not any(file.endswith(".txt") for file in os.listdir(source_path)):
            print(
                f"The source path '{source_path}' does not contain any poker hand history files."
            )
            sys.exit(1)

        # Get start time
        start_time = datetime.datetime.now()

        # Generate session ID
        session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Generate destination path
        destination_path = f"./output/{session_id}"

        # Create folder
        os.makedirs(destination_path)

        # Execute pipeline
        execute_in_parallel(source=source_path, destination=destination_path)

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

    elif command == "modeling":

        # Check if the source path exists
        if not os.path.exists(source_path):
            print(f"The source path '{source_path}' does not exist.")
            sys.exit(1)
        # Check if the source path is a directory
        if not os.path.isdir(source_path):
            print(f"The source path '{source_path}' is not a directory.")
            sys.exit(1)
        # Check if the source path contains converted .parquet files
        if not any(file.endswith(".parquet") for file in os.listdir(source_path)):
            print(
                f"The source path '{source_path}' does not contain any .parquet files."
            )
            sys.exit(1)

        # Get start time
        start_time = datetime.datetime.now()

        # Generate session ID
        session_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")

        # Generate destination path
        destination_path = f"./modeling/{session_id}"

        # Create folder
        os.makedirs(destination_path)

        # Build the star schema (one fact table and four dimensions)
        number_of_rows = build_star_schema(
            source=source_path, destination=destination_path
        )

        # Print a summary of the generated tables
        for name, rows in number_of_rows.items():
            print(f"   DONE: {name}.parquet ({rows} rows)")

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

    else:
        print(f"The command '{command}' does not exist.")


if __name__ == "__main__":
    main()
