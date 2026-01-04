# Franktorio Research Scanner
# Image downloading API
# January 2026

import asyncio
import requests

def _download_image(url: str) -> bytes | None:
    """
    Download an image from a given URL.
    
    Args:
        url (str): The URL of the image to download.
    Returns:
        bytes | None: The image data in bytes, or None if download failed.
    """
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        return response.content
    except requests.RequestException as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def download_images(urls: list[str]) -> dict[str, bytes | None]:
    """
    Download multiple images concurrently.
    
    Args:
        urls (list[str]): List of image URLs to download.
    Returns:
        dict[str, bytes | None]: A dictionary mapping URLs to their downloaded image data or None if failed.
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def _download_all():
        tasks = []
        for url in urls:
            tasks.append(loop.run_in_executor(None, _download_image, url))
        results = await asyncio.gather(*tasks)
        return {url: result for url, result in zip(urls, results)}
    
    return loop.run_until_complete(_download_all())