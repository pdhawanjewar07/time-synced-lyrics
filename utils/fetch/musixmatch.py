from utils.helpers import extract_spotify_lyrics, build_search_query, match_song_metadata, get_songs, clear_profile_cache
import logging
from bs4 import BeautifulSoup
from config import SPOTIFY_TRACK_CSS_SELECTOR
import requests
from utils.playwright_driver import PlaywrightDriver
import re
import json
import time
from utils.spotify_auth import SpotifyAuthManager

total_wasted_time = {"total_wasted_time": 0}

log = logging.getLogger(__name__)

auth = SpotifyAuthManager()
driver = PlaywrightDriver(headless=True)  # False for debugging

def fetch_lyrics(song_path: str) -> tuple:
    """
    Fetch lyrics from musixmatch-via-spotify
    
    :param song_path: song path
    :type song_path: str
    :return: (synced_lyrics, unsynced_lyrics) items can be str|False
    :rtype: tuple

    """
    cache = {
        "synced_lyrics":False,
        "unsynced_lyrics":False
    }

    search_query = build_search_query(song_path=song_path)
    # print(f"______Search Query: {search_query}")
    search_url = f"https://open.spotify.com/search/{search_query}/tracks"
    # print(f"Spotify search url: {search_url}")

    # ---------------------------------------
    wasted_time_start = time.time()
    # ---------------------------------------

    driver.page.goto(search_url)
    driver.page.wait_for_selector(SPOTIFY_TRACK_CSS_SELECTOR)
    driver.page.click(SPOTIFY_TRACK_CSS_SELECTOR)
    driver.page.wait_for_url("**/track/**")

    spotify_track_url = driver.page.url
    # print(f"Spotify _track url: {spotify_track_url}")

    #/start For track comparison 
    resp = requests.get(spotify_track_url,headers={"User-Agent": "Mozilla/5.0"},timeout=10)
    if resp.status_code != 200: return (False, False)  

    soup = BeautifulSoup(resp.text, "html.parser")
    def meta(prop):
        tag = soup.find("meta", property=prop)
        return tag["content"] if tag else None
    
    try:
        encoded_img_url = meta("og:image")
        # print(f"Encoded image url: {encoded_img_url}")
        match = re.search(r"/image/([A-Za-z0-9]+)", encoded_img_url)
        encoded_img_id = match.group(1)
        # print(f"Encoded image id: {encoded_img_id}")
    except: return (False, False)

    recieved_song_title = meta("og:title")
    recieved_song_description = meta("og:description")
    recieved_song_info = f'{recieved_song_title} {recieved_song_description}'
    flag = match_song_metadata(local_song_path=song_path, received_song_info=recieved_song_info, threshold=70)
    if flag is False: return (False, False)
    #/end For track comparison

    match = re.search(r"/track/([A-Za-z0-9]+)", spotify_track_url)
    spotify_track_id = match.group(1)
    # print(f"Spotify track id: {spotify_track_id}")

    # ---------------------------------------
    elapsed_wasted_time = time.time() - wasted_time_start
    total_wasted_time["total_wasted_time"] += elapsed_wasted_time
    # ---------------------------------------

    lyrics_url = f"https://spclient.wg.spotify.com/color-lyrics/v2/track/{spotify_track_id}/image/https%3A%2F%2Fi.scdn.co%2Fimage%2F{encoded_img_id}?format=json&vocalRemoval=false&market=from_token"
    
    spotify_auth_token = auth.get_token()
    spotify_auth = f"Bearer {spotify_auth_token}"
    headers = {
        "Authorization": spotify_auth,
        "App-Platform": "WebPlayer",
        "User-Agent": "Spotify/1.2.0",
    }

    try:
        response = requests.get(url=lyrics_url, headers=headers)
        json_data = response.json()
        # with open(f"lyrics/{recieved_song_title}.json", "w", encoding="utf-8") as f:
        #     json.dump(json_data, f, ensure_ascii=False, indent=2)
    except: return (False, False)

    lyrics = extract_spotify_lyrics(json_data=json_data)
    try: 
        cache["synced_lyrics"] = lyrics[0]
        cache["unsynced_lyrics"] = lyrics[1]
    except: pass
        

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


