# Franktorio Research Scanner
# Location services API
# January 2026

import requests

def get_server_location_from_log(line: str) -> dict | None:
    """
    Sends a request to an IP geolocation service to get the server location from a log line.
    
    Args:
        line (str): The log line containing the server IP.
    Returns:
        dict | None: A dictionary with location details or None if not found.
        {
            "city": str,
            "region": str,
            "country": str
        }
    """
    try:
        parts = line.split()
        ud_index = parts.index("udmux")
        if ud_index + 3 >= len(parts):
            return None
        ip = parts[ud_index + 3].strip(",")
        
        response = requests.get(f"https://ipinfo.io/{ip}/json", timeout=3)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city", "Unknown")
            region = data.get("region", "")
            country = data.get("country", "")
            res = {
                "city": city,
                "region": region,
                "country": country
            }
            return res
    except Exception as e:
        print(f"Error getting server location: {e}")
        return None