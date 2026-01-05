# Franktorio Research Scanner
# Image downloading API
# January 2026

import requests

def download_image(url: str) -> bytes | None:
    """
    Download an image from a given URL.
    
    Args:
        url (str): The URL of the image to download.
    Returns:
        bytes | None: The image data in bytes, or None if download failed.
    """
    try:
        response = requests.get(url, timeout=2)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None