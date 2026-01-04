# Franktorio Research Scanner
# Configuration Variables
# December 2025

import os
import dotenv

VERSION = "INDEV" # Application Version, INDEV until first viable release

# API Configuration
dotenv.load_dotenv(dotenv_path="config/.env")  # Load environment variables from .env file

API_BASE_URL = os.getenv("API_BASE_URL")

# GUI Configuration
RESIZE_MARGIN = 5
MIN_WIDTH = 800
MIN_HEIGHT = 600

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