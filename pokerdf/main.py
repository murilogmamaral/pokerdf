import os
import sys
import datetime

from pokerdf.core.read_and_convert import execute_in_parallel


def main() -> None:
    """
    Main function to process command line arguments and execute the 'convert' command.

    - Checks if the command is 'convert'.
    - If 'convert', generates a session ID and creates a destination path.
    - Executes the pipeline function `execute_in_parallel` to process files from source to destination.

    Raises:
        SystemExit: If there are not enough arguments or if an invalid command is provided.
    """

    if len(sys.argv) < 3:
        print("Usage: pokerdf convert <path>")
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

        # Generate destionation path
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

    else:
        print(f"The command '{command}' does not exist.")


if __name__ == "__main__":
    main()
