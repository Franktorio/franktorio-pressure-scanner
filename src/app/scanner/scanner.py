# Franktorio Research Scanner
# Scanner thread module
# January 2026]]

import asyncio
import threading

from config.vars import session_config, VERSION
from src.api.scanner import request_session, end_session, room_encountered, RoomInfo, check_scanner_version
from src.app.scanner.stalker import Stalker, observe_logfile_changes
from src.app.scanner.parser import parse_log_lines
from src.app.scanner.log_finder import get_latest_logfile_path

class Scanner:
    """Scanner object to manage the scanning task."""
    def __init__(self):
        self.task = None  # Asyncio task
        self.alive = False
        self.thread = None  # Thread for running asyncio loop
        self.loop = None  # Asyncio event loop

        self.has_session = False

        # Scanner configuration
        self.loop_interval = 0.5  # Seconds between line parses
        self.stalker = None  # To be set to Stalker instance
        self.latest_rooms = []  # List of up to 5 latest scanned room names to prevent duplicates
        self.current_path = None  # Current log file path being monitored
        self.last_scanned_path = None  # Last scanned log file path

        version_thread = threading.Thread(target=self._run_version_check_loop, daemon=True)
        version_thread.start()

    def start(self):
        """Start the scanning task in a separate thread."""
        if self.thread is None or not self.thread.is_alive():
            self.alive = True
            self.thread = threading.Thread(target=self._run_async_loop, daemon=True)
            self.thread.start()
            self.update_start_button.emit(False)  # Disable start button
            self.update_stop_button.emit(True)    # Enable stop button
            self._log_console_message("Scanner has been started.")
    
    def _run_async_loop(self):
        """Run asyncio event loop in separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.scanner_loop())

    def _run_version_check_loop(self):
        """Run version check in separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.version_check_loop())

    def stop(self):
        """Stop the scanning task."""
        self.alive = False
        self.update_start_button.emit(True)   # Enable start button
        self.update_stop_button.emit(False)    # Disable stop button
        self._log_console_message("Scanner has been stopped.")

    async def report_new_rooms(self, parsed_rooms: list[str]) -> RoomInfo | None:
        """
        Check parsed rooms against the latest rooms list to prevent duplicates.
        Requests a session if there isn't one already.
        
        Args:
            parsed_rooms (list[str]): List of newly parsed room names.

        Returns:
            RoomInfo: Information about the latest encountered room.
        """

        # Only request a session if we don't have one AND there are rooms to report
        if not self.has_session and parsed_rooms:
            success = await request_session()
            if not success:
                return None
            self.has_session = True
        
        latest_room = None
        for room in parsed_rooms:
            if room in self.latest_rooms:
                self._log_console_message(f"Returned to room: {room}.")
                _, latest_room = await room_encountered(room_name=room, log_event=False)
            else:
                self.latest_rooms.append(room)
                if len(self.latest_rooms) > 5:
                    self.latest_rooms.pop(0)  # Maintain only the last 5 rooms
                self._log_console_message(f"Encountered new room: {room}.")
                _, latest_room = await room_encountered(room_name=room, log_event=True)
        
        return latest_room
    
    def _reset_scanner_visuals(self):
        """Reset scanner-related UI elements via signals."""
        self.update_room_info.emit(RoomInfo())  # Clear room info display by sending empty RoomInfo
        self.update_server_info.emit({})  # Clear server info display by sending empty dict
    
    async def reset(self):
        """Reset the scanner state."""
        self.latest_rooms.clear()
        await end_session()
        session_config.clear_session()  # Clear expired credentials
        self.has_session = False  # Force new session request
        self._reset_scanner_visuals()
        self._log_console_message("Scanner state has been reset.")

    def _validate_signals_setup(self):
        """Ensure that all required signals are set up."""
        required_signals = [
            'update_server_info',
            'update_room_info',
            'update_start_button',
            'update_stop_button',
            'version_check_ready'
        ]
        for signal_name in required_signals:
            if not hasattr(self, signal_name):
                return False
        return True

    async def scanner_loop(self):
        """Asynchronous loop to run the scan function at specified intervals."""
        self.stalker = Stalker()

        _no_new_lines_accumulator = 0
        
        while self.alive:
            await asyncio.sleep(self.loop_interval)

            if not self._validate_signals_setup():
                print("Scanner signals not properly set up, skipping iteration")
                continue  # Signals not properly set up

            if not self.stalker:
                continue  # Stalker not initialized yet

            # Ensure we have a log file path
            if not self.current_path:
                try:
                    self.current_path = get_latest_logfile_path()
                    self.stalker.file_position = 0  # Reset file position for new log file
                    self._log_console_message(f"Monitoring log file: {self.current_path}")
                except (EnvironmentError, FileNotFoundError) as e:
                    continue
            
            # Open the log file and observe changes
            try:
                with open(self.current_path, "r", encoding="utf-8") as logfile:
                    new_lines = observe_logfile_changes(logfile, self.stalker)
            except (IOError, OSError) as e:
                # File might have been deleted, clear path and retry
                self.current_path = None
                continue

            if not new_lines:
                _no_new_lines_accumulator += 1
                if _no_new_lines_accumulator >= 50:
                    latest_file = get_latest_logfile_path()
                    if latest_file != self.current_path:
                        self.current_path = latest_file
                        self.stalker.file_position = 0  # Reset file position for new log file
                        self._log_console_message(f"Switched to new log file: {self.current_path}")
                        # Reset scanner 
                        await self.reset()
                    _no_new_lines_accumulator = 0
                continue

            parsed_results = parse_log_lines(new_lines)
            rooms = parsed_results.get("rooms", [])
            location = parsed_results.get("location", None)
            disconnected = parsed_results.get("disconnected", False)

            # Process parsed results
            latest_room = await self.report_new_rooms(rooms)

            if latest_room:
                self.update_room_info.emit(latest_room)

            if location:
                self._log_console_message(f"Location updated: {location}")
                self.update_server_info.emit(location)
            
            # Reset state on disconnect
            if disconnected:
                await self.reset()


    def _log_console_message(self, message: str):
        """Log a message to the console via signal."""
        if not hasattr(self, 'log_console_message'):
            return
        self.log_console_message.emit(message)

    def set_server_info_signal(self, signal):
        """Set the signal for server info updates."""
        self.update_server_info = signal

    def set_room_info_signal(self, signal):
        """Set the signal for room info updates."""
        self.update_room_info = signal

    def set_start_button_signal(self, signal):
        """Set the signal for start button state updates."""
        self.update_start_button = signal
    
    def set_stop_button_signal(self, signal):
        """Set the signal for stop button state updates."""
        self.update_stop_button = signal

    def set_log_console_message_signal(self, signal):
        """Set the signal for logging messages to console."""
        self.log_console_message = signal

    def set_version_check_ready_signal(self, signal):
        """Set the signal for version check ready notification."""
        self.version_check_ready = signal

    async def version_check_loop(self):
        """Wait for scanner to be ready, then perform version check."""
        while not self._validate_signals_setup():
            await asyncio.sleep(0.1)
        
        try:
            self._log_console_message("Performing version check...")
            latest_version = await check_scanner_version()
            if hasattr(self, 'version_check_ready'):
                self.version_check_ready.emit(latest_version)
        except Exception as e:
            self._log_console_message(f"Version check failed: {e}")
            if hasattr(self, 'version_check_ready'):
                self.version_check_ready.emit("")  # Emit empty string on failure




