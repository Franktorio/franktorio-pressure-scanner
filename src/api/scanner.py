# Franktorio Research Scanner
# Scanner endpoint API
# Jan 2026

import asyncio
import requests
from config.vars import API_BASE_URL, session_config, VERSION

_REQ_TIMEOUT = 5 # seconds

class RoomInfo:
    """Class representing room information retrieved from the API"""
    def __init__(self, **kwargs):
        self.room_name: str = kwargs.get("room_name")
        self.picture_urls: list[str] = kwargs.get("picture_urls", [])
        self.description: str = kwargs.get("description", "N/A")
        self.roomtype: str = kwargs.get("roomtype", "N/A")
        self.tags: list[str] = kwargs.get("tags", [])
        self.last_updated: float = kwargs.get("last_updated", 0.0)
        self.doc_by_user_id: int = kwargs.get("doc_by_user_id", -1)
        self.edits: list[dict] = kwargs.get("edits", []) # List of edit records, not used

def _run_in_executor(func, *args, **kwargs):
    loop = asyncio.get_running_loop()
    return loop.run_in_executor(None, func, *args, **kwargs)

def _request_session() -> bool:
    """Request a new session from the API"""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/request_session",
            json={"scanner_version": VERSION},
            timeout=_REQ_TIMEOUT
        )
        data = resp.json()

        session_config.set_session(data["session_id"], data["password"])
        
        return data.get("success", False)
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error requesting session: {e}")
        return False

def _end_session() -> bool:
    """End the current session"""
    try:
        session_id, password = session_config.get_session()
        
        resp = requests.post(
            f"{API_BASE_URL}/end_session",
            json={"session_id": session_id, "password": password},
            timeout=_REQ_TIMEOUT
        )
        data = resp.json()
        success = data.get("success", False)
        return success
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error ending session: {e}")
        return False

def _get_room_info(room_name: str) -> RoomInfo | None:
    """
    Get room information from the API
    
    Returns:
        tuple[RoomInfo | None, bool]: (room_info, had_error)
            - room_info: Room information if successful, None otherwise
            - had_error: True if there was a connection/auth error, False if room just doesn't exist
    """
    try:
        session_id, password = session_config.get_session()
        
        resp = requests.post(
            f"{API_BASE_URL}/get_roominfo",
            json={
                "room_name": room_name,
                "session_id": session_id,
                "password": password
            },
            timeout=_REQ_TIMEOUT
        )
        data = resp.json()
        if data.get("success"):
            # Ensure room_name is included in the response data
            room_info_data = data["room_info"]
            room_info_data["room_name"] = room_name
            return RoomInfo(**room_info_data)
        else:
            # Return RoomInfo with only the room name + (Undocumented) next to it
            return RoomInfo(room_name=f"{room_name} (Undocumented)")
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error getting room info for {room_name}: {e}")
        return None

def _log_room_encounter(room_name: str) -> bool:
    """
    Log that a room has been encountered
    
    Returns:
        tuple[bool, bool]: (success, had_error)
            - success: True if encounter was logged successfully
            - had_error: True if there was a connection/auth error, False otherwise
    """
    try:
        session_id, password = session_config.get_session()
        
        resp = requests.post(
            f"{API_BASE_URL}/room_encountered",
            json={
                "room_name": room_name,
                "session_id": session_id,
                "password": password
            },
            timeout=_REQ_TIMEOUT
        )
        data = resp.json()
        success = data.get("success", False)
        return success
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error logging room encounter for {room_name}: {e}")
        return False
    
async def request_session() -> bool:
    """Asynchronously request a new session from the API"""
    return await _run_in_executor(_request_session)

async def end_session() -> bool:
    """Asynchronously end the current session"""
    return await _run_in_executor(_end_session)

async def room_encountered(room_name: str, log_event: bool) -> tuple[bool, RoomInfo | None]:
    """Asynchronously get room info and log the encounter"""
    # Get coroutines to run in executor
    if log_event:
        logged_task =  _run_in_executor(_log_room_encounter, room_name)
        room_info_task =  _run_in_executor(_get_room_info, room_name)

        # Run both tasks concurrently
        logged, room_info = await asyncio.gather(logged_task, room_info_task)
    else:
        room_info = await _run_in_executor(_get_room_info, room_name)
        logged = False
    
    return logged, room_info
    