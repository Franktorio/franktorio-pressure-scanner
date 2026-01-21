# Franktorio Research Scanner
# Main orchestrator for log file scanning
# January 2026

from io import TextIOWrapper

MAX_READ_LINES = 50 # Maximum lines to read per interval

class Stalker:
    def __init__(self):
        self.file = None
        self.file_position = 0

        # Debug stats
        self.total_reads = 0
        self.total_lines_read = 0
        self.empty_reads = 0

    def find_starting_point(self, file: TextIOWrapper) -> None:
        """
        Sets the file position to the latest disconnect entry in the log file.

        Find: if "[flog::network] client:disconnect" in u_line:
        """

        self.file_position = 0
        file.seek(0)  # Start from the beginning

        
        while True:
            line = file.readline()
            if not line:
                break  # End of file reached
            if "[flog::network] client:disconnect" in line.lower():
                self.file_position = file.tell()  # Update position to after this line
            

    def observe_logfile_changes(self, file: TextIOWrapper) -> list[str]:
        """
        Return the latest lines added to the log file since the last read.
        """
        file.seek(self.file_position)  # Move to the last known position
        new_lines = []
        for _ in range(MAX_READ_LINES):
            line = file.readline()
            if not line:
                break  # No more new lines
            new_lines.append(line)
        self.file_position = file.tell()  # Update the position
        filtered_lines = [line.strip() for line in new_lines if line.strip()]
        
        # Update debug stats
        self.total_reads += 1
        self.total_lines_read += len(filtered_lines)
        if not filtered_lines:
            self.empty_reads += 1
        
        return filtered_lines  # Return non-empty lines
        