# Franktorio Research Scanner
# Log file finder utility
# January 2026

import os
import platform
import glob 
from config.vars import USER_LOG_PATH

PLATFORM = platform.system().lower()

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
    
def _look_for_linux_logdir_path() -> str | None:
    """
    Look for the Roblox log file in common Linux/Wine/Proton/Sober locations.
    Returns the newest log file path if found.
    """
    home = os.path.expanduser('~')

    # candidate directories
    candidate_dirs = [
        os.path.join(home, '.wine', 'drive_c', 'users', '*', 'Local Settings', 'Application Data', 'Roblox', 'logs'),
        os.path.join(home, '.local', 'share', 'roblox', 'logs'),
        os.path.join(home, '.steam', 'steam', 'steamapps', 'compatdata', '*', 'pfx', 'drive_c', 'users', '*', 'Local Settings', 'Application Data', 'Roblox', 'logs'),
        os.path.join(home, '.local', 'share', 'sober', 'prefix', 'drive_c', 'users', '*', 'Local Settings', 'Application Data', 'Roblox', 'logs'),
    ]

    # expand wildcards
    dirs = []
    for d in candidate_dirs:
        dirs.extend(glob.glob(d))

    # pick newest log from all dirs
    latest_file = None
    latest_mtime = 0
    for d in dirs:
        if not os.path.isdir(d):
            continue
        files = [os.path.join(d, f) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f))]
        for f in files:
            mtime = os.path.getmtime(f)
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = f

    return latest_file

def get_latest_log_file_path() -> str | None:
    """
    Determine the latest log file path based on the operating system and user configuration.
    
    Returns:
        str | None: The path to the latest log file, or None if not found.
    """
    if USER_LOG_PATH != '':
        if os.path.isfile(USER_LOG_PATH):
            return USER_LOG_PATH
        elif os.path.isdir(USER_LOG_PATH):
            return _get_latest_file_from_directory(USER_LOG_PATH)
        else:
            return None
    
    if PLATFORM == 'windows':
        default_dir = os.path.join(os.getenv('LOCALAPPDATA', ''), 'Roblox', 'logs')
    elif PLATFORM == 'darwin':  # macOS
        default_dir = os.path.join(os.path.expanduser('~'), 'Library', 'Logs', 'Roblox')
    else:  # Linux / Wine / Proton / Sober
        return _look_for_linux_logdir_path()
        

    return _get_latest_file_from_directory(default_dir)