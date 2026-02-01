# Franktorio Research Scanner
# Scanner websocket server
# Jan 2026

import asyncio
import websockets
import json

SOCKET_BASE_URL = "wss://franktorio.dev/frd-wss/scanner-socket"

# GUI Signal references (set by main window)
_gui_add_player_signal = None
_gui_remove_player_signal = None
_gui_change_player_room_signal = None
_gui_new_room_encounter_signal = None
_gui_debug_log_signal = None

# Websocket connection reference (for sending from scanner)
_active_websocket = None

def _log_debug(message: str) -> None:
    """Log a debug message if the signal is available."""
    if _gui_debug_log_signal:
        _gui_debug_log_signal.emit(f"[WS] {message}")

async def _connect_scanner_websocket(username: str, socket_name: str, current_room: str) -> websockets.WebSocketClientProtocol | None:
    """Connect to the scanner websocket server with the provided token."""
    url = f"{SOCKET_BASE_URL}/{socket_name}?username={username}&current_room={current_room}"
    _log_debug(f"Attempting to connect to websocket: {url}")
    for attempt in range(3):
        try:
            websocket = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            _log_debug(f"Successfully connected to websocket server")
            return websocket
        except (websockets.InvalidStatusCode, websockets.WebSocketException) as e:
            _log_debug(f"Connection attempt {attempt + 1}/3 failed: {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            _log_debug(f"Unexpected error on connection attempt {attempt + 1}/3: {e}")
            await asyncio.sleep(2 ** attempt)
    _log_debug(f"Failed to connect after 3 attempts")
    return None

async def _send_json_via_websocket(websocket: websockets.WebSocketClientProtocol, data: dict) -> bool:
    """Send JSON data via the provided websocket connection."""
    try:
        await websocket.send(json.dumps(data))
        _log_debug(f"Sent event: {data.get('event', 'unknown')}")
        return True
    except websockets.WebSocketException as e:
        _log_debug(f"Error sending data: {e}")
        return False

async def send_join_room_event(websocket: websockets.WebSocketClientProtocol, room_name: str) -> bool:
    """Send a 'join_room' event via the websocket."""
    data = {
        "event": "join",
        "room_name": room_name
    }
    return await _send_json_via_websocket(websocket, data)

async def report_encountered_room(websocket: websockets.WebSocketClientProtocol, room_name: str) -> bool:
    """Report an encountered room via the websocket."""
    data = {
        "event": "encounter",
        "room_name": room_name
    }
    return await _send_json_via_websocket(websocket, data)

async def send_ping(websocket: websockets.WebSocketClientProtocol) -> bool:
    """Send a ping event to keep connection alive."""
    data = {
        "event": "ping"
    }
    return await _send_json_via_websocket(websocket, data)


# GUI Signal references (set by main window)
_gui_add_player_signal = None
_gui_remove_player_signal = None
_gui_change_player_room_signal = None
_gui_new_room_encounter_signal = None

# Websocket connection reference (for sending from scanner)
_active_websocket = None

def set_gui_signals(add_player_signal, remove_player_signal, change_player_room_signal, new_room_encounter_signal, debug_log_signal=None):
    """Set the GUI signals for websocket events."""
    global _gui_add_player_signal, _gui_remove_player_signal, _gui_change_player_room_signal, _gui_new_room_encounter_signal, _gui_debug_log_signal
    _gui_add_player_signal = add_player_signal
    _gui_remove_player_signal = remove_player_signal
    _gui_change_player_room_signal = change_player_room_signal
    _gui_new_room_encounter_signal = new_room_encounter_signal
    _gui_debug_log_signal = debug_log_signal

def get_active_websocket() -> websockets.WebSocketClientProtocol | None:
    """Get the currently active websocket connection, if any."""
    return _active_websocket

# Helpers to change scanner window via signals
def add_player(username: str) -> None:
    """Signal to add a player to the scanner GUI."""
    if _gui_add_player_signal:
        _gui_add_player_signal.emit(username)

def remove_player(username: str) -> None:
    """Signal to remove a player from the scanner GUI."""
    if _gui_remove_player_signal:
        _gui_remove_player_signal.emit(username)

def change_player_room(username: str, room_name: str) -> None:
    """Signal to change a player's room in the scanner GUI."""
    if _gui_change_player_room_signal:
        _gui_change_player_room_signal.emit(username, room_name)

def new_room_encounter(room_name: str) -> None:
    """Signal to log a new room encounter in the scanner GUI."""
    if _gui_new_room_encounter_signal:
        _gui_new_room_encounter_signal.emit(room_name)



async def websocket_loop(username: str, socket_name: str, current_room: str) -> None:
    """Main loop to handle websocket connection and room reporting."""
    global _active_websocket
    
    _log_debug(f"Starting websocket loop for user: {username}, socket: {socket_name}")
    websocket = await _connect_scanner_websocket(username, socket_name, current_room)
    if not websocket:
        _log_debug("Websocket connection failed, exiting loop")
        return

    try:
        # Store the active websocket for scanner to use
        _active_websocket = websocket
        _log_debug("Active websocket connection established")
        
        # Send join event to register with the server
        _log_debug(f"Sending join event for socket: {socket_name}")
        await send_join_room_event(websocket, socket_name)
        
        # Create a task to send periodic pings
        async def ping_task():
            while True:
                await asyncio.sleep(5)  # Send ping every 5 seconds
                await send_ping(websocket)
        
        # Start the ping task
        ping_worker = asyncio.create_task(ping_task())
        _log_debug("Started ping task (5s interval)")
        
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            event = data.get("event")

            _log_debug(f"Received event: {event}")

            match event:
                case "left":
                    username_left = data["username"]
                    _log_debug(f"Player left: {username_left}")
                    remove_player(username_left)
                case "joined":
                    username_joined = data["username"]
                    _log_debug(f"Player joined: {username_joined}")
                    add_player(username_joined)
                case "encounter":
                    reported_by = data.get("reported_by")
                    room_name = data.get("room_name")
                    is_new = data.get("is_new", False)
                    _log_debug(f"Room encounter: {room_name} (reported by: {reported_by}, new: {is_new})")
                    if reported_by:
                        change_player_room(reported_by, room_name)
                    if is_new:
                        new_room_encounter(room_name)
                case "state":
                    # Server sends current state with users dict and loaded_rooms
                    users = data.get("users", {})
                    loaded_rooms = data.get("loaded_rooms", [])
                    _log_debug(f"Received state: {len(users)} users, {len(loaded_rooms)} rooms")

                    # Add loaded rooms to GUI
                    for room in loaded_rooms:
                        new_room_encounter(room)

                    # Place current users in GUI
                    for user, user_data in users.items():
                        add_player(user)
                        current_room = user_data.get("current_room", "")
                        if current_room:
                            change_player_room(user, current_room)
                case _:
                    _log_debug(f"Unknown event received: {event}")

    except asyncio.CancelledError:
        _log_debug("Websocket loop cancelled")
    except Exception as e:
        _log_debug(f"Websocket error: {e}")
    finally:
        # Cancel the ping task if it exists
        if 'ping_worker' in locals():
            ping_worker.cancel()
            _log_debug("Ping task cancelled")
        # Clear the active websocket reference
        _active_websocket = None
        await websocket.close()
        _log_debug("Websocket connection closed")