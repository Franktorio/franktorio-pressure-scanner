# Franktorio Research Scanner
# Scanner websocket server
# Jan 2026

import asyncio
import websockets
import json

SOCKET_BASE_URL = "wss://franktorio.dev/frd-wss/scanner-socket"

async def _connect_scanner_websocket(username: str, socket_name: str, current_room: str) -> websockets.WebSocketClientProtocol | None:
    """Connect to the scanner websocket server with the provided token."""
    url = f"{SOCKET_BASE_URL}/{socket_name}?username={username}&current_room={current_room}"
    for attempt in range(3):
        try:
            websocket = await websockets.connect(url, ping_interval=20, ping_timeout=10)
            print(f"Connected to websocket server at {url}")
            return websocket
        except (websockets.InvalidStatusCode, websockets.WebSocketException) as e:
            print(f"Websocket connection attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            print(f"Unexpected error on websocket connection attempt {attempt + 1}: {e}")
            await asyncio.sleep(2 ** attempt)
    print(f"Failed to connect to websocket server at {url} after 3 attempts.")
    return None

async def _send_json_via_websocket(websocket: websockets.WebSocketClientProtocol, data: dict) -> bool:
    """Send JSON data via the provided websocket connection."""
    try:
        await websocket.send(json.dumps(data))
        print(f"Sent data via websocket: {data}")
        return True
    except websockets.WebSocketException as e:
        print(f"Error sending data via websocket: {e}")
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


# GUI Signal references (set by main window)
_gui_add_player_signal = None
_gui_remove_player_signal = None
_gui_change_player_room_signal = None
_gui_new_room_encounter_signal = None

# Websocket connection reference (for sending from scanner)
_active_websocket = None

def set_gui_signals(add_player_signal, remove_player_signal, change_player_room_signal, new_room_encounter_signal):
    """Set the GUI signals for websocket events."""
    global _gui_add_player_signal, _gui_remove_player_signal, _gui_change_player_room_signal, _gui_new_room_encounter_signal
    _gui_add_player_signal = add_player_signal
    _gui_remove_player_signal = remove_player_signal
    _gui_change_player_room_signal = change_player_room_signal
    _gui_new_room_encounter_signal = new_room_encounter_signal

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
    
    websocket = await _connect_scanner_websocket(username, socket_name, current_room)
    if not websocket:
        return

    try:
        # Store the active websocket for scanner to use
        _active_websocket = websocket
        
        # Send join event to register with the server
        await send_join_room_event(websocket, socket_name)
        
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            event = data.get("event")

            print(f"Received websocket event: {data}")

            match event:
                case "left":
                    remove_player(data["username"])
                case "joined":
                    add_player(data["username"])
                case "encounter":
                    reported_by = data.get("reported_by")
                    room_name = data.get("room_name")
                    if reported_by:
                        change_player_room(reported_by, room_name)
                    if data.get("is_new", False):
                        new_room_encounter(room_name)
                case "state":
                    # Server sends current state with users dict and loaded_rooms
                    users = data.get("users", {})
                    loaded_rooms = data.get("loaded_rooms", [])

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
                    print(f"Unknown event received via websocket: {data}")

    except asyncio.CancelledError:
        print("Websocket loop cancelled.")
    finally:
        # Clear the active websocket reference
        _active_websocket = None
        await websocket.close()
        print("Websocket connection closed.")