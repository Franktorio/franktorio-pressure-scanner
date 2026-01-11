# Franktorio Research Scanner
# Scanner thread module
# January 2026]]

import asyncio
import time
import traceback
import threading

from config.vars import session_config
from src.api.scanner import request_session, end_session, room_encountered, RoomInfo, check_scanner_version
from src.app.scanner.stalker import Stalker, observe_logfile_changes
from src.app.scanner.parser import parse_log_lines
from src.app.scanner.log_finder import get_latest_log_file_path

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

        # Debug statistics
        self.debug_stats = {
            "file_checks": 0,
            "file_switches": 0,
            "api_calls": 0,
            "session_requests": 0,
            "total_rooms_reported": 0,
            "scanner_iterations": 0,
            "errors_caught": 0
        }
        self.last_file_check_time = time.time()

        version_thread = threading.Thread(target=self._run_version_check_loop, daemon=True)
        version_thread.start()

    def start(self):
        """Start the scanning task in a separate thread."""
        if self.thread is None or not self.thread.is_alive():
            self.alive = True
            self.thread = threading.Thread(target=self._run_async_loop_wrapper, daemon=True)
            self.thread.start()
            self.update_start_button.emit(False)  # Disable start button
            self.update_stop_button.emit(True)    # Enable stop button
            self._log_console_message("Scanner has been started.")
            self._log_debug_message("Scanner thread started successfully")
    
    def _run_async_loop_wrapper(self):
        """Wrapper to catch and handle scanner thread crashes."""
        try:
            self._log_debug_message("Entering async event loop")
            self._run_async_loop()
        except Exception as e:
            self.debug_stats["errors_caught"] += 1
            self._log_console_message(f"CRITICAL ERROR: Scanner thread crashed: {e}")
            self._log_debug_message(f"Scanner thread exception details: {type(e).__name__}: {e}")
            self._log_debug_message(f"Traceback: {traceback.format_exc()}")
            # Try to reset button states
            try:
                self.update_start_button.emit(True)
                self.update_stop_button.emit(False)
            except:
                pass
    
    def _run_async_loop(self):
        """Run asyncio event loop in separate thread."""
        self._log_debug_message("Creating new asyncio event loop")
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self._log_debug_message("Starting scanner_loop coroutine")
        self.loop.run_until_complete(self.scanner_loop())
        self._log_debug_message("Scanner loop completed")

    def _run_version_check_loop(self):
        """Run version check in separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.version_check_loop())

    def stop(self):
        """Stop the scanning task."""
        self._log_debug_message("Stop command received")
        self.alive = False
        self.update_start_button.emit(True)   # Enable start button
        self.update_stop_button.emit(False)    # Disable stop button
        self._log_console_message("Scanner has been stopped.")
        self._log_debug_message("Scanner stopped successfully")

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
            self.debug_stats["session_requests"] += 1
            self._log_debug_message("Requesting new API session...")
            success = await request_session()
            if not success:
                self._log_debug_message("Session request failed")
                return None
            self.has_session = True
            self._log_debug_message("Session request successful")
        
        latest_room = None
        for room in parsed_rooms:
            self.debug_stats["api_calls"] += 1
            self.debug_stats["total_rooms_reported"] += 1
            if room in self.latest_rooms:
                self._log_console_message(f"Returned to room: {room}.")
                self._log_debug_message(f"API call: room_encountered (duplicate room: {room}) with logging=False")
                _, latest_room = await room_encountered(room_name=room, log_event=False)
            else:
                self.latest_rooms.append(room)
                if len(self.latest_rooms) > 5:
                    self.latest_rooms.pop(0)  # Maintain only the last 5 rooms
                self._log_console_message(f"Encountered new room: {room}.")
                self._log_debug_message(f"API call: room_encountered (new room: {room}) with logging=True")
                _, latest_room = await room_encountered(room_name=room, log_event=True)
        
        return latest_room
    
    def _reset_scanner_visuals(self):
        """Reset scanner-related UI elements via signals."""
        self.update_room_info.emit(RoomInfo())  # Clear room info display by sending empty RoomInfo
        self.update_server_info.emit({})  # Clear server info display by sending empty dict
    
    async def reset(self):
        """Reset the scanner state."""
        self._log_debug_message("Resetting scanner state...")
        self.latest_rooms.clear()
        await end_session()
        session_config.clear_session()  # Clear expired credentials
        self.has_session = False  # Force new session request
        self._reset_scanner_visuals()
        self._log_console_message("Scanner state has been reset.")
        self._log_debug_message("Scanner reset complete")

    def _validate_signals_setup(self):
        """Ensure that all required signals are set up."""
        required_signals = [
            'update_server_info',
            'update_room_info',
            'update_start_button',
            'update_stop_button',
            'version_check_ready',
            'debug_console_message'
        ]
        for signal_name in required_signals:
            if not hasattr(self, signal_name):
                return False
        return True

    async def scanner_loop(self):
        """Asynchronous loop to run the scan function at specified intervals."""
        self._log_debug_message("Initializing scanner loop")
        self.stalker = Stalker()
        self._log_debug_message("Stalker initialized")

        _no_new_lines_accumulator = 0
        import time
        
        self._log_debug_message("Entering main scanner loop")
        while self.alive:
            await asyncio.sleep(self.loop_interval)
            self.debug_stats["scanner_iterations"] += 1

            if not self._validate_signals_setup():
                print("Scanner signals not properly set up, skipping iteration")
                continue  # Signals not properly set up

            if not self.stalker:
                continue  # Stalker not initialized yet

            # Ensure we have a log file path
            if not self.current_path:
                try:
                    self._log_debug_message("Searching for log file...")
                    self.current_path = get_latest_log_file_path()
                    self.stalker.file_position = 0  # Reset file position for new log file
                    self._log_console_message(f"Monitoring log file: {self.current_path}")
                    self._log_debug_message(f"Log file found and monitoring started: {self.current_path}")
                except (EnvironmentError, FileNotFoundError) as e:
                    self.debug_stats["errors_caught"] += 1
                    self._log_debug_message(f"Error finding log file: {type(e).__name__}: {e}")
                    continue
            
            # Open the log file and observe changes
            try:
                with open(self.current_path, "r", encoding="utf-8") as logfile:
                    new_lines = observe_logfile_changes(logfile, self.stalker)
            except (IOError, OSError) as e:
                # File might have been deleted, clear path and retry
                self.debug_stats["errors_caught"] += 1
                self._log_debug_message(f"Error reading log file: {e}")
                self.current_path = None
                continue

            if not new_lines:
                _no_new_lines_accumulator += 1
                if _no_new_lines_accumulator >= 50:
                    self.debug_stats["file_checks"] += 1
                    current_time = time.time()
                    time_since_last_check = current_time - self.last_file_check_time
                    self.last_file_check_time = current_time
                    self._log_debug_message(f"Checking for new log file (last check: {time_since_last_check:.1f}s ago)")
                    latest_file = get_latest_log_file_path()
                    if latest_file != self.current_path:
                        self.debug_stats["file_switches"] += 1
                        self.current_path = latest_file
                        self.stalker.file_position = 0  # Reset file position for new log file
                        self._log_console_message(f"Switched to new log file: {self.current_path}")
                        self._log_debug_message(f"File switch detected: {self.current_path}")
                        # Reset scanner 
                        await self.reset()
                    _no_new_lines_accumulator = 0
                continue

            parsed_results = parse_log_lines(new_lines)
            rooms = parsed_results.get("rooms", [])
            location = parsed_results.get("location", None)
            disconnected = parsed_results.get("disconnected", False)
            lines_parsed = parsed_results.get("lines_parsed", 0)
            
            if lines_parsed > 0:
                self._log_debug_message(f"Parsed {lines_parsed} new lines - rooms: {len(rooms)}, location: {location is not None}, disconnect: {disconnected}")

            # Process parsed results
            if rooms:
                self._log_debug_message(f"Processing {len(rooms)} room(s): {rooms}")
            latest_room = await self.report_new_rooms(rooms)

            if latest_room:
                self.update_room_info.emit(latest_room)

            if location:
                self._log_console_message(f"Location updated: {location}")
                self._log_debug_message(f"Server location detected: {location}")
                self.update_server_info.emit(location)
            
            # Reset state on disconnect
            if disconnected:
                self._log_debug_message("Disconnect detected, resetting scanner state")
                await self.reset()


    def _log_console_message(self, message: str):
        """Log a message to the console via signal."""
        if not hasattr(self, 'log_console_message'):
            return
        self.log_console_message.emit(message)

    def _log_debug_message(self, message: str):
        """Log a debug message to the debug console via signal."""
        if not hasattr(self, 'debug_console_message'):
            return
        self.debug_console_message.emit(message)

    def get_debug_stats(self) -> dict:
        """Return current debug statistics."""
        stats = self.debug_stats.copy()
        if self.stalker:
            stats["stalker_reads"] = self.stalker.total_reads
            stats["stalker_lines_read"] = self.stalker.total_lines_read
            stats["stalker_empty_reads"] = self.stalker.empty_reads
        
        # Import parser stats
        from src.app.scanner.parser import get_parser_stats
        parser_stats = get_parser_stats()
        stats.update(parser_stats)
        
        return stats

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

    def set_debug_console_message_signal(self, signal):
        """Set the signal for debug console messages."""
        self.debug_console_message = signal

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




