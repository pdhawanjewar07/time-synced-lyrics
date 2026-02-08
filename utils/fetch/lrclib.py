from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import requests
import random
from utils.helpers import human_delay, extract_lrclib_lyrics, build_search_query, match_song_metadata, get_songs
import time
import logging
import json

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

def fetch_lyrics(song_path: str) -> tuple:
    """
    Fetch lyrics from lrclib
    
    :param song_path: song path
    :type song_path: str
    :return: (synced_lyrics, unsynced_lyrics) items can be str|False
    :rtype: tuple

    """
    global _session, _request_count

    cache = {
        "synced_lyrics":False,
        "synced_description":False,
        "unsynced_lyrics":False,
        "unsynced_description":False
    }

    # rotate session periodically
    _request_count += 1
    if _request_count % SESSION_ROTATE_EVERY == 0:
        try:
            _session.close()
        finally:
            _session = new_session()

    """
    sleep_duration = human_delay()
    log.info(f"WAITING - {sleep_duration:0.2f}s before next lrclib request")
    time.sleep(sleep_duration)
    """

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
        return (False, False)

    except requests.exceptions.RequestException:
        return (False, False)

    # explicit rate-limit handling
    if response.status_code == 429:
        time.sleep(random.uniform(60, 120))
        return (False, False)

    if response.status_code != 200:
        return (False, False)

    try: json_response = response.json()
    except ValueError: return (False, False)
    # print(json_response)
    # with open(f"_lyrics/1.json", "w", encoding="utf-8") as f:
    #     json.dump(json_response, f, ensure_ascii=False, indent=2)
    
    lyrics = extract_lrclib_lyrics(json_data=json_response)  # tuple is returned
    # print(lyrics)

    cache["synced_lyrics"], cache["synced_description"], cache["unsynced_lyrics"], cache["unsynced_description"] = lyrics

    try:
        sync_flag = match_song_metadata(print_match=False, threshold=60, local_song_path=song_path, received_song_info=cache["synced_description"])
        unsync_flag = match_song_metadata(print_match=False, threshold=60, local_song_path=song_path, received_song_info=cache["unsynced_description"])
        if sync_flag is False: cache["synced_lyrics"] = False
        if unsync_flag is False: cache["unsynced_lyrics"] = False
    except:
        # log.info("FAILURE - LrcLib sync_flag: incorrect match")
        # log.info("FAILURE - LrcLib unsync_flag: incorrect match")
        pass

    return (cache["synced_lyrics"], cache["unsynced_lyrics"])


if __name__ == "__main__":
    MUSIC_DIRECTORY = "C:\\Users\\Max\\Desktop\\music\\small"
    music_files = get_songs(music_dir=MUSIC_DIRECTORY)

    for i, song_path in enumerate(music_files):
        print(f"{i+1}. {song_path.stem}")
        synced, unsynced =  fetch_lyrics(song_path=song_path)
        if synced is False: print(f"synced: False")
        if unsynced is False: print(f"unsynced: False")
        underline = "‾" * len(song_path.stem)
        with open(f"lyrics/{song_path.stem}.lrc", "w", encoding="utf-8") as f:
            f.write(f"{song_path.stem}\n{underline}\n{synced}")
            f.write(f"\n\n{song_path.stem}\n{underline}\n{unsynced}")

