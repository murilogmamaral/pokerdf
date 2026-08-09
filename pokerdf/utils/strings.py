"""Single source of truth for the naming conventions used across the package."""

# Platform whose hand histories are supported
PLATFORM = "PokerStars"

# Naming convention of the hand history files exported by the platform
HAND_HISTORY_PREFIX = "HH"
HAND_HISTORY_EXTENSION = ".txt"

# Extension of the tables saved by the convert and modeling commands
PARQUET_EXTENSION = ".parquet"

# Log files of a conversion session
SUCCESS_LOG = "success.txt"
FAIL_LOG = "fail.txt"

# Report saved alongside an anonymized modeling session
ANONYMIZATION_REPORT = "anonymization.txt"

# Root folders and session identifier of the outputs
OUTPUT_FOLDER = "output"
MODELING_FOLDER = "modeling"
SESSION_ID_FORMAT = "%Y%m%d-%H%M%S"
