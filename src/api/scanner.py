# Franktorio Research Scanner
# Scanner endpoint API
# Jan 2026

import threading
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

config_lock = threading.Lock() # All API calls must acquire this lock and thus they must be run in threadsafe executors

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

        with config_lock:
            session_config.set_session(data["session_id"], data["password"])

        return data.get("success", False)
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error requesting session: {e}")
        return False

def _end_session() -> bool:
    """End the current session"""
    try:
        with config_lock:
            session_id, password = session_config.get_session()

        resp = requests.post(
            f"{API_BASE_URL}/end_session",
            json={"session_id": session_id, "password": password},
            timeout=_REQ_TIMEOUT
        )
        data = resp.json()
        return data.get("success", False)
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error ending session: {e}")
        return False

def _get_room_info(room_name: str) -> RoomInfo | None:
    """Get room information from the API"""
    try:
        with config_lock:
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
            return RoomInfo(**data)
        else:
            return None
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error getting room info for {room_name}: {e}")
        return None

def _log_room_encounter(room_name: str) -> bool:
    """Log that a room has been encountered"""
    try:
        with config_lock:
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
        return data.get("success", False)
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"Error logging room encounter for {room_name}: {e}")
        return False

async def request_session() -> bool:
    """Asynchronously request a new session from the API"""
    return await _run_in_executor(_request_session)

async def end_session() -> bool:
    """Asynchronously end the current session"""
    return await _run_in_executor(_end_session)

async def room_encountered(room_name: str) -> tuple[bool, RoomInfo | None]:
    """Asynchronously get room info and log the encounter"""

    # Get coroutines to run in executor
    logged =  _run_in_executor(_log_room_encounter, room_name)
    room_info =  _run_in_executor(_get_room_info, room_name)

    # Run both tasks concurrently
    logged, room_info = await asyncio.gather(logged, room_info)

    # Edge case: if room info was retrieved but logging failed, get a new session and retry logging
    if room_info and not logged:
        success = await request_session()

        if not success:
            return False, room_info
        
        logged = await _run_in_executor(_log_room_encounter, room_name)

    return logged, room_info
    