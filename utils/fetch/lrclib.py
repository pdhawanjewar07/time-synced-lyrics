from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
import random
from utils.helpers import human_delay, extract_lrclib_lyrics, build_search_query
import time
import logging


log = logging.getLogger(__name__)

# General Variables Declaration
UA_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
]
BASE_HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    # kill keep-alive to avoid poisoned TLS sockets
    "Connection": "close",
}
_retry = Retry(
    total=0,
    backoff_factor=1.5,
    status_forcelist=[500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False,
)

_adapter = HTTPAdapter(max_retries=_retry)

# Session factory
def new_session() -> requests.Session:
    s = requests.Session()
    s.mount("https://", _adapter)
    headers = BASE_HEADERS.copy()
    headers["User-Agent"] = random.choice(UA_POOL)
    s.headers.update(headers)
    return s

# Global session (rotated)
_session = new_session()
_request_count = 0
SESSION_ROTATE_EVERY = 7

def fetch_lyrics(song_path: str, mode:int=2) -> str | bool:
    """
    Fetch lyrics json response from lrclib.

    Args:
        song_path: song path
        mode: synced(0), unsynced(1), synced_with_fallback(2).

    Returns:
        Lyrics(str) if found, otherwise False
    """
    global _session, _request_count

    # rotate session periodically
    _request_count += 1
    if _request_count % SESSION_ROTATE_EVERY == 0:
        try:
            _session.close()
        finally:
            _session = new_session()

    human_delay()

    search_query = build_search_query(song_path=song_path)

    try:
        response = _session.get(
            "https://lrclib.net/api/search",
            params={
                "q": search_query,
                "limit": random.choice([10, 15, 20]),
            },
            timeout=(3, 10),
            allow_redirects=True,
        )

    except requests.exceptions.SSLError:
        # poisoned TLS session → hard reset
        try:
            _session.close()
        finally:
            _session = new_session()
        return False

    except requests.exceptions.RequestException:
        return False

    # explicit rate-limit handling
    if response.status_code == 429:
        time.sleep(random.uniform(60, 120))
        return False

    if response.status_code != 200:
        return False

    try:
        data = response.json()
    except ValueError:
        return False

    # small post-request pause
    human_delay()

    lyrics = extract_lrclib_lyrics(json_data=data, mode=mode)
    if lyrics:
        if mode == 1:
            log.info("SUCCESS - LrcLib: unsynced lyrics found")
        else:
            log.info("SUCCESS - LrcLib: synced lyrics found")
        return lyrics
    else:
        if mode == 1:
            log.info("FAILURE - LrcLib: unsynced lyrics not found")
        else:
            log.info("FAILURE - LrcLib: synced lyrics not found")
