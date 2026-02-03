# Franktorio Research Scanner
# Configuration Variables
# December 2025

import os
import sys
import platform
import src.app.user_data.appdata as appdata

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # If not bundled, use the current directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)

VERSION = "3.5.7" # Application Version

# API Base URL for the application
API_BASE_URL='https://nxgfwt5dei.execute-api.ca-central-1.amazonaws.com'

# User log file path from configuration
USER_LOG_PATH: str = appdata.get_value_from_config('set_log_path', '')

if platform.system() == 'Darwin':
    APP_ICON_PATH = get_resource_path('config/images/researchfrankbadge.icns')
else:
    APP_ICON_PATH = get_resource_path('config/images/researchfrankbadge.ico')
APP_ICON_PNG_PATH = get_resource_path('config/images/researchfrankbadge.png')
LOADING_GIF_PATH = get_resource_path('config/images/loading_gif.gif')

# GUI Configuration
RESIZE_MARGIN = 5
MIN_WIDTH = 800
MIN_HEIGHT = 600
MAX_WIDTH = 1920
MAX_HEIGHT = 1080

class SessionConfig:
    """Configuration class for application settings"""
    def __init__(self):
        # Session settings
        self.session_id = None # To be set when a session is created
        self.session_password = None # To be set when a session is created

    def set_session(self, session_id, session_password):
        """Set session ID and password"""
        self.session_id = session_id
        self.session_password = session_password

    def get_session(self):
        """Get current session ID and password"""
        return self.session_id, self.session_password
    
    def clear_session(self):
        """Clear session credentials"""
        self.session_id = None
        self.session_password = None

session_config = SessionConfig()