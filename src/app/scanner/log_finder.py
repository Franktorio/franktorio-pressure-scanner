# Franktorio Research Scanner
# Log file finder utility
# January 2026

import os

def _get_latest_file_from_directory(directory: str) -> str | None:
    """
    Get the latest file from a specified directory.
    
    Args:
        directory (str): The directory to search for files.
    Returns:
        str | None: The path to the latest file, or None if no files are found
    """
    try:
        files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        latest_file = max(files, key=os.path.getmtime)
        return latest_file
    except ValueError:
        return None

def get_latest_logfile_path() -> str:
    """Retrieve the path to the latest log file found on Roblox's appdata."""
    local_appdata = os.getenv("LOCALAPPDATA") # Get local appdata directory
    if not local_appdata:
        raise EnvironmentError("LOCALAPPDATA was not found in your device environment variables, cannot locate Roblox log files.")
    
    logs_dir = os.path.join(local_appdata, "Roblox", "logs") # Construct logs directory path
    if not os.path.exists(logs_dir):
        raise FileNotFoundError("Roblox logs directory not found, ensure Roblox is installed and has been run at least once.")
    
    latest_logfile = _get_latest_file_from_directory(logs_dir)

    if not latest_logfile:
        raise FileNotFoundError("No log files found in Roblox logs directory.")
    
    return latest_logfile
