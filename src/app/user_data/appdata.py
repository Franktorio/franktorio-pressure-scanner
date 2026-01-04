# Franktorio Research Scanner
# User data management module
# January 2026

from email.policy import default
import os
import json
import platform

PLATFORM = platform.system().lower()
HOME = os.path.expanduser('~')

def get_user_data_directory() -> str:
    """
    Get the path to the user data directory based on the operating system.
    """
    if PLATFORM == 'windows':
        appdata = os.getenv('APPDATA')
        if appdata:
            return os.path.join(appdata, 'FranktorioResearchScanner')
        else:
            return os.path.join(HOME, 'AppData', 'Roaming', 'FranktorioResearchScanner')
    elif PLATFORM == 'darwin':  # macOS
        return os.path.join(HOME, 'Library', 'Application Support', 'FranktorioResearchScanner')
    else:  # Linux and other Unix-like systems
        base = os.getenv("XDG_DATA_HOME") or os.path.join(HOME, ".local", "share")
        return os.path.join(base, "franktorio-research-scanner")

def create_json_config_file(file_path: str, default_data: dict) -> None:
    """
    Create a JSON configuration file with default data if it does not exist.
    """
    
    # Exit if file already exists
    if os.path.isfile(file_path):
        return
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(default_data, f, indent=4)

def setup_user_data() -> None:
    """
    Set up the user data directory and default configuration files.
    """
    user_data_dir = get_user_data_directory()
    os.makedirs(user_data_dir, exist_ok=True)
    
    config_file_path = os.path.join(user_data_dir, 'config.json')
    default_config = {
        "set_log_path": "", # User-defined log file path
    }
    
    create_json_config_file(config_file_path, default_config)

def get_value_from_config(key: str, default: any = None) -> any:
    """
    Retrieve a value from the configuration file.
    """
    user_data_dir = get_user_data_directory()
    config_file_path = os.path.join(user_data_dir, 'config.json')
    
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
            return config_data.get(key, default)
    except (FileNotFoundError, json.JSONDecodeError):
        return default
    
def set_value_in_config(key: str, value: any) -> None:
    """
    Set a value in the configuration file.
    """
    user_data_dir = get_user_data_directory()
    config_file_path = os.path.join(user_data_dir, 'config.json')
    
    config_data = {}
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    
    config_data[key] = value
    
    with open(config_file_path, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4)