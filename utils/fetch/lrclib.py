# from requests.adapters import HTTPAdapter
# from urllib3.util.retry import Retry
import requests
# import random
from utils.helpers import human_delay, extract_lrclib_lyrics, build_search_query, match_song_metadata
# import time
import json
import logging


log = logging.getLogger(__name__)

cache = {
    "synced_lyrics":None,
    "synced_description":None,
    "unsynced_lyrics":None,
    "unsynced_description":None
}

def fetch_lyrics(song_path: str, mode:int=2) -> str | bool:
    """
    Fetch lyrics json response from lrclib.

    Args:
        song_path: song path
        mode: synced(0), unsynced(1), synced_with_fallback(2).

    Returns:
        Lyrics(str) if found, otherwise False
    """
    # if unsynced is requested, return cached if available
    if cache["unsynced_lyrics"] is not None and mode == 1:
        log.info("SUCCESS - LrcLib: unsynced lyrics found")
        return cache["unsynced_lyrics"]
    
    search_query = build_search_query(song_path=song_path)

    # this shit needs way too much delay between requests
    # human_delay(mean=10, jitter=0.5, minimum=8)

    response = requests.get(f"https://lrclib.net/api/search", params={"q":search_query}, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

    if response.status_code != 200:
        log.info("FAILURE - Lrclib: request not 200 OK!")
        return False

    json_data = response.json()

    # lyrics_and_description = (synced_lyrics, unsynced_lyrics, description)
    synced_unsynced = extract_lrclib_lyrics(json_data=json_data)
    
    cache["synced_lyrics"] = synced_unsynced[0]
    cache["synced_description"] = synced_unsynced[1]
    cache["unsynced_lyrics"] = synced_unsynced[2]
    cache["unsynced_description"] = synced_unsynced[3]


    flag = ""
    if flag is False:
        log.info("FAILURE - Lrclib: synced/unsynced lyrics not found")
        return False
    
    try: sync_flag = match_song_metadata(local_song_path=song_path, received_song_info=cache["synced_description"], threshold=70)
    except: log.info("FAILURE - LrcLib: synced lyrics not found")
    try: unsync_flag = match_song_metadata(local_song_path=song_path, received_song_info=cache["unsynced_description"], threshold=70)
    except: log.info("FAILURE - LrcLib: unsynced lyrics not found")

    match mode:
        case 0: # synced only
            if cache["synced_lyrics"] is not None and sync_flag is True:
                log.info("SUCCESS - LrcLib: synced lyrics found")
                return cache["synced_lyrics"]
            else: log.info("FAILURE - LrcLib: synced lyrics not found")
        case 1: # unsynced only
            if cache["unsynced_lyrics"] is not None and unsync_flag is True:
                log.info("SUCCESS - LrcLib: unsynced lyrics found")
                return cache["unsynced_lyrics"]
            else: log.info("FAILURE - LrcLib: unsynced lyrics not found")
        case _: # Default: synced_with_fallback
            if cache["synced_lyrics"] is not None and sync_flag is True:
                log.info("SUCCESS - LrcLib: synced lyrics found")
                return cache["synced_lyrics"]
            elif cache["unsynced_lyrics"] is not None and unsync_flag is True:
                log.info("SUCCESS - LrcLib: unsynced lyrics found")
                return cache["unsynced_lyrics"]
            else:
                log.info("FAILURE - Lrclib: synced/unsynced lyrics not found")
                return False


if __name__ == "__main__":
    output = fetch_lyrics(song_path="C:\\Users\\Max\\Desktop\\music\\small\\MOHIT CHAUHAN - Naina.flac", mode=2)
    # print(output)
    if type(output) is str:
        with open("lrclib_lyrics.lrc", "w", encoding="utf-8") as f:
            f.write(output)

