import requests
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from syrics.api import Spotify
from config import SPOTIFY_TRACK_CSS_SELECTOR
from utils.helpers import extract_spotify_lyrics, build_search_query, match_song_metadata
from utils.selenium_startup import get_driver
from dotenv import load_dotenv
import os
import logging
from bs4 import BeautifulSoup


load_dotenv()
SPOTIFY_DC_TOKEN = os.getenv("SPOTIFY_DC_TOKEN")

log = logging.getLogger(__name__)
sp = Spotify(SPOTIFY_DC_TOKEN)
driver = get_driver()

cache = {
    "synced_lyrics":None,
    "unsynced_lyrics":None
}

def fetch_lyrics(song_path: str, mode:int) -> str|bool:
    """
    Fetch lyrics json response from musixmatch_via_spotify
    
    Args:
        search_query: song path
        mode: synced(0), unsynced(1), synced_with_fallback(2)

    Returns:
        Lyrics(str) if found, otherwise False
    """
    # if unsynced is requested, return cached if available
    if cache["unsynced_lyrics"] is not None and mode == 1:
        log.info("SUCCESS - MusixMatch: unsynced lyrics found")
        return cache["unsynced_lyrics"]

    search_query = build_search_query(song_path=song_path)

    url = f"https://open.spotify.com/search/{requests.utils.quote(search_query)}/tracks"

    try:
        driver.get(url)
        first_track = WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, SPOTIFY_TRACK_CSS_SELECTOR)))
    except: 
        log.info("Spotify: could not get track(selenium driver time out)")
        return False

    old_url = driver.current_url
    first_track.click()
    WebDriverWait(driver, 30).until(lambda d: d.current_url != old_url and "/track/" in d.current_url)

    track_url = driver.current_url
    # print(track_url)

    #/start For track comparison 
    resp = requests.get(track_url,headers={"User-Agent": "Mozilla/5.0"},timeout=10)
    if resp.status_code != 200:
        pass    # continue any way

    soup = BeautifulSoup(resp.text, "html.parser")
    def meta(prop):
        tag = soup.find("meta", property=prop)
        return tag["content"] if tag else None
    
    recieved_song_info = f'{meta("og:title")} {meta("og:description")}'
    
    flag = match_song_metadata(local_song_path=song_path, received_song_info=recieved_song_info, threshold=70)

    if flag is False:
        log.info("FAILURE - MusixMatch: synced/unsynced lyrics not found")
        return False

    #/end For track comparison 

    match = re.search(r"/track/([A-Za-z0-9]+)", track_url)
    track_id = match.group(1)
    # print(track_id)

    json_response = sp.get_lyrics(track_id=track_id)
    # print(json_response)
    lyrics = extract_spotify_lyrics(json_data=json_response)
    cache["synced_lyrics"] = lyrics[0]
    cache["unsynced_lyrics"] = lyrics[1]
    # print(lyrics)

    match mode:
        case 0: # synced only
            if cache["synced_lyrics"] is not None:
                log.info("SUCCESS - MusixMatch: synced lyrics found")
                return cache["synced_lyrics"]
            else: log.info("FAILURE - MusixMatch: synced lyrics not found")
        case 1: # unsynced only
            if cache["unsynced_lyrics"] is not None:
                log.info("SUCCESS - MusixMatch: unsynced lyrics found")
                return cache["unsynced_lyrics"]
            else: log.info("FAILURE - MusixMatch: unsynced lyrics not found")
        case _: # Default: synced_with_fallback
            if cache["synced_lyrics"] is not None:
                log.info("SUCCESS - MusixMatch: synced lyrics found")
                return cache["synced_lyrics"]
            elif cache["unsynced_lyrics"] is not None:
                log.info("SUCCESS - MusixMatch: unsynced lyrics found")
                return cache["unsynced_lyrics"]
            else:
                log.info("FAILURE - MusixMatch: synced/unsynced lyrics not found")
    return False      

if __name__ == "__main__":
    # Outstation - Tum Se.flac | Shreya Ghoshal - Cry Cry.flac
    output = fetch_lyrics(song_path="C:\\Users\\Max\\Desktop\\music\\small\\Outstation - Tum Se.flac", mode=2)
    # print(output)
    if type(output) is str:
        with open("musixmatch_lyrics.lrc", "w", encoding="utf-8") as f:
            f.write(output)

