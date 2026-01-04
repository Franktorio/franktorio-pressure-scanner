# Franktorio Research Scanner
# Main orchestrator for log file scanning
# January 2026

from io import TextIOWrapper
from pydoc import text


class Stalker:
    def __init__(self):
        self.file_position = 0

MAX_READ_LINES = 50 # Maximum lines to read per interval

def observe_logfile_changes(file: TextIOWrapper, stalker: Stalker) -> list[str]:
    """
    Return the latest lines added to the log file since the last read.
    """
    file.seek(stalker.file_position)  # Move to the last known position
    new_lines = []
    for _ in range(MAX_READ_LINES):
        line = file.readline()
        if not line:
            break  # No more new lines
        new_lines.append(line)
    stalker.file_position = file.tell()  # Update the position
    filtered_lines = [line.strip() for line in new_lines if line.strip()]
    return filtered_lines  # Return non-empty lines
    