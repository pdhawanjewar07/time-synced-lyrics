# unsynced only - community based

from dotenv import load_dotenv
import os
import requests
import json
from lxml import html
from utils.helpers import build_search_query, match_song_metadata, clean_string, get_songs

load_dotenv()
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}


def fetch_lyrics(song_path:str)->tuple:
    search_query = build_search_query(song_path=song_path)
    search_url = f"https://api.genius.com/search?q={search_query}"

    response = requests.get(url=search_url, headers=headers)
    json_data = response.json()

    # with open("genius_response.json", "w", encoding="utf-8") as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=2)

    response = json_data.get("response", {})
    hits = response.get("hits", [])
    try: first_hit = hits[0]    # if no hits return False
    except: return (False, False)
    result = first_hit.get("result", {})

    genius_trk_url = result.get("url", "")
    # print(f"Url: {genius_trk_url}")

    recieved_title = result.get("full_title", "")
    recieved_artist = result.get("artist_names", "")
    recieved_song_info = clean_string(f"{recieved_title} {recieved_artist}")
    # print(f"Description: {recieved_song_info}")

    flag = match_song_metadata(print_match=False, threshold=60, local_song_path=song_path, received_song_info=recieved_song_info)
    if flag is False: return (False, False)

    response = requests.get(genius_trk_url, timeout=10)
    tree = html.fromstring(response.text)

    lyrics_xpath = '//*[@id="lyrics-root"]//*[@data-lyrics-container="true"]/text()'
    text:list = tree.xpath(lyrics_xpath)

    if len(text)>0:
        lyrics = ""
        for line in text:
            lyrics += f"{line}\n"
        # with open("genius_response.txt", "w", encoding="utf-8") as f:
        #     for line in text:
        #         f.write(line + "\n")
        lyrics += "\nSource: Genius"
        return (False, lyrics)
    return (False, False)


if __name__ == "__main__":
    MUSIC_DIRECTORY = "C:\\Users\\Max\\Desktop\\music\\small"
    music_files = get_songs(music_dir=MUSIC_DIRECTORY)

    for i, song_path in enumerate(music_files):
        print(f"{i+1}. {song_path.stem}")
        _, unsynced = fetch_lyrics(song_path=song_path)
        underline = "‾" * len(song_path.stem)
        with open(f"lyrics/{song_path.stem}.lrc", "w", encoding="utf-8") as f:
            f.write(f"{song_path.stem}\n{underline}\n{unsynced}")
    