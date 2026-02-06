import requests
import json
from utils.helpers import get_songs, build_search_query, match_song_metadata, clean_string


def fetch_lyrics(song_path:str)->tuple:
    headers = {"accept": "*/*"}

    query = build_search_query(song_path=song_path)
    req_url = f"https://saavn.sumit.co/api/search/songs?query={query}"

    # song search
    response = requests.get(url=req_url, headers=headers, timeout=30)
    json_data = response.json()

    # with open("jiosaavn_response.json", "w", encoding="utf-8") as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=2)

    success = json_data.get("success", bool)
    if success is False: return (False, False)

    data:dict = json_data.get("data", {})
    results:list = data.get("results", [])[:10] # top 10 hits

    def eval_results()->dict|bool:
        try:
            for result in results:
                recieved_song_title:str = result.get("name", "")
                recieved_song_album:str = result.get("album", {}).get("name", "")
                recieved_song_artists:list = result.get("artists", {}).get("all", [])
                recieved_song_artist:str = ""
                for artist in recieved_song_artists:
                    artist_name = artist.get("name", "")
                    recieved_song_artist += f"{artist_name} "
                recieved_song_info = f"{recieved_song_title} {recieved_song_album} {recieved_song_artist}"
                flag = match_song_metadata(print_match=False, threshold=60, local_song_path=song_path, received_song_info=recieved_song_info)
                if flag is True:
                    return result
            return False    # if no good match is found
        except: return False    # fail condition

    result = eval_results()
    if result is False: return (False, False)

    lyrics_id = result.get("id", "")
    lyrics_url = f"https://www.jiosaavn.com/api.php?__call=lyrics.getLyrics&lyrics_id={lyrics_id}&ctx=web6dot0&api_version=4&_format=json&_marker=0"

    # lyrics fetch
    response = requests.get(lyrics_url, timeout=30)
    json_data = response.json()

    # with open("jiosaavn_response.json", "w", encoding="utf-8") as f:
    #     json.dump(json_data, f, ensure_ascii=False, indent=2)

    unsynced_lyrics:str = json_data.get("lyrics", "")
    if len(unsynced_lyrics)<1: return (False, False)
    unsynced_lyrics = unsynced_lyrics.replace("<br>", "\n")
    unsynced_lyrics += "\nSource: JioSaavn"
    return (False, unsynced_lyrics)

if __name__ == "__main__":
    MUSIC_DIRECTORY = "C:\\Users\\Max\\Desktop\\music\\small"
    music_files = get_songs(music_dir=MUSIC_DIRECTORY)
    # music_files = ["C:\\Users\\Max\\Desktop\\music\\small\\Sunidhi Chauhan - Tum Mile.flac"]

    for i, song_path in enumerate(music_files):
        # from pathlib import Path
        # song_path = Path(song_path)
        print(f"{i+1}. {song_path.stem}")
        _, unsynced =  fetch_lyrics(song_path=song_path)
        print(unsynced)

        underline = "‾" * len(song_path.stem)
        with open(f"lyrics/{song_path.stem}.lrc", "w", encoding="utf-8") as f:
            f.write(f"{song_path.stem}\n{underline}\n{unsynced}")


