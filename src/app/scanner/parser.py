# Franktorio Research Scanner
# Log file parsing orchestration
# January 2026

from src.api.location import get_server_location_from_log

_disconect_switch = True # Roblox logs sends disconnect log twice, this switch helps manage that

def _get_roomname_from_logline(line: str) -> str | None:
    """
    Extract the room name from a log line if present.
    
    Args:
        line (str): The log line to extract from.
    Returns:
        str | None: The extracted room name, or None if not found.
    """
    parts = line.split()
    if parts:
        room_name = parts[-1]
    return room_name

def parse_log_lines(lines: list[str]) -> dict:
    """
    Parse log lines by sending them to the scanner API.
    
    Args:
        lines (list[str]): List of log lines to parse.
    Returns:
        dict: Parsed results from the API:
            {
                "rooms": [list of room names],
                "location: str | None (server location),
                "disconnected": bool (if a disconnect was detected)
            }
    """
    global _disconect_switch
    summary = {
        "rooms": [],
        "location": None,
        "disconnected": False
    }

    for line in lines:
        u_line = line.lower()

        if "room name" in u_line:
            room_name = _get_roomname_from_logline(line)
            summary["rooms"].append(room_name)

        if "udmux" in u_line and not summary["location"]:
            location = get_server_location_from_log(u_line)
            if location:
                summary["location"] = location

        if "[flog::network] client:disconnect" in u_line:
            if _disconect_switch:
                summary["disconnected"] = True
                _disconect_switch = False
            else:
                _disconect_switch = True

    return summary
            
