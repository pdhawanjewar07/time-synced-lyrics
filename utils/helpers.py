import random
import re
from mutagen import File
import logging
from rapidfuzz import fuzz
from pathlib import Path
import shutil


# Setup logging
logging.basicConfig(
    level=logging.INFO, # DEBUG 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("main.log", encoding='utf-8'),
        logging.StreamHandler()  # also print to console
    ]
)
log = logging.getLogger(__name__)
log.info("==== New log session was started ====")

def get_songs(music_dir:str)->list[str]:
    AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".m4a",".ogg", ".opus", ".alac", ".aiff"}
    # MUSIC_DIRECTORY = "C:\\Users\\Max\\Desktop\\music\\small"
    music_dir = Path(music_dir)
    music_files = (
        f for f in music_dir.iterdir()
        if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS
    )
    return music_files

def format_time(seconds: float) -> str:
    ms = int((seconds % 1) * 1000)
    secs = int(seconds) % 60
    mins = (int(seconds) // 60) % 60
    hrs = int(seconds) // 3600
    # 23hrs:12min:59sec,213ms
    return f"{hrs:02}hrs:{mins:02}min:{secs:02}sec,{ms:03}ms"

def clean_string(raw_string:str) -> str:
    """
    regex clean given string
    
    :param raw_string: raw string
    :type raw_string: str
    :return: a clean string in lowercase
    :rtype: str
    
    """
    clean_string = raw_string.lower()                         # to lowercase
    clean_string = re.sub(r"\s*\([^)]*\)", "", clean_string)  # remove anything inside brackets with themselves
    clean_string = re.sub(r"[^\w\s÷]", " ", clean_string, flags=re.UNICODE)  # remove punctuation, keep unicode,÷(for other languages)
    clean_string = clean_string.replace("_", " ") # unicode flag ignores "_"
    clean_string = re.sub(r"\s*Various Interprets", "", clean_string, flags=re.IGNORECASE)  # remove "Various Interprets"
    clean_string = re.sub(r"\s*Various Artists", "", clean_string, flags=re.IGNORECASE)  # remove "Various Interprets"
    clean_string = re.sub(r"\s+", " ", clean_string).strip()  # clean excess whitespace
    return clean_string

def match_song_metadata(local_song_path:str, received_song_info:str, threshold:float, print_match:bool=False) -> bool:
    """fuzzy match local and recieved song metadata

    :param local_song_path: local song path
    :type local_song_path: str
    :param received_song_info: recieved song complete description as a string
    :type received_song_info: str
    :param threshold: [0-100]
    :type threshold: float
    :return: True if match is good, otherise False
    :rtype: bool
    """

    audio = File(local_song_path, easy=True)
    if audio is None:
        raise ValueError("Unsupported or corrupted audio file")

    local_song_title:str = clean_string(audio.get("title", [None])[0])
    local_song_artist:str = clean_string(audio.get("artist", [None])[0])
    local_song_album:str = clean_string(audio.get("album", [None])[0])
    received_song_info:str = clean_string(received_song_info)

    score_title = fuzz.partial_ratio(local_song_title, received_song_info)
    title_flag = True
    if score_title<threshold: title_flag = False
    # if local_song_title in received_song_info: title_flag = True
    if print_match and title_flag is False:   # print info on match fail condition
        print(f"__local_title_info: {local_song_title}")
        print(f"received_song_info: {received_song_info}")
        print(f"_title_match_score: {score_title:0.2f}%")
    

    score_artist = fuzz.partial_ratio(local_song_artist, received_song_info)
    artist_flag = True
    if score_artist<threshold: artist_flag = False
    if print_match and artist_flag is False:  # print info on match fail condition
        print(f"_local_artist_info: {local_song_artist}")
        print(f"received_song_info: {received_song_info}")
        print(f"artist_match_score: {score_artist:0.2f}%")

    score_album = fuzz.partial_ratio(local_song_album, received_song_info)
    album_flag = True
    if score_album<threshold: album_flag = False
    if print_match and album_flag is False:   # print info on match fail condition
        print(f"__local_album_info: {local_song_album}")
        print(f"received_song_info: {received_song_info}")
        print(f"_album_match_score: {score_album:0.2f}%")
    
    global_flag = title_flag and (artist_flag or album_flag)
    return global_flag

def build_search_query(song_path: str) -> str:
    """Build a search query string from selected audio tags.

    :param song_path: Path to the audio file.
    :type song_path: str
    :param source: musixmatch-via-spotify[0], lrclib[1], genius[2]
    :type source: int
    :return: Clean search query
    :rtype: str
    """
    # TAGS_PRIORITY_ORDER = ["title", "artist", "albumartist" "album"]
    # set default tags to include
    
    audio = File(song_path)
    title:str = audio.tags.get("title", [None])[0]
    album:str = audio.tags.get("album", [None])[0]
    artist:str = audio.tags.get("artist", [None])[0]
    
    if title in album:  # remove redundant title present in album eg. title artist title+album -> title artist album
        album = album.replace(title, "")
    
    raw_query = f"{title} {artist} {album}"

    clean_query = clean_string(raw_string=raw_query)
    # log.info(f"QUERY: {clean_query}")
    return clean_query

def human_delay(mean: float = 5.0, jitter: float = 0.3, minimum: float = 3.0):
    delay = random.gauss(mean, mean * jitter)
    sleep_duration = max(minimum, delay)
    return sleep_duration

def save_lyrics(lyrics:str, out_dir: str, out_filename:str) -> bool:
    lyrics_file = out_dir + f"\\{out_filename}.lrc"
    with open(lyrics_file, "w", encoding="utf-8") as f:
        f.write(lyrics)
    return True

def extract_genius_song_url(json_data: dict) -> str|bool:
    """
    extract genius unsynced lyrics from json response
    
    Args:
        json_data: json response from genius fetch

    Returns:
        lyrics(str) if found, otherwise False
    """
    if json_data is None:
        return False
    
    try:
        response = json_data.get("response", {})
        hits = response.get("hits", [])
        song_obj = hits[0] # best match(first)
        result = song_obj.get("result", {})
        genius_song_url = result.get("relationships_index_url", "")
        # print(genius_song_url)
        return genius_song_url
    except:
        return False
    
def extract_spotify_lyrics(json_data: dict) -> tuple:
    """
    extract spotify lyrics from json response
    
    :param json_data: json response from spotify fetch
    :type json_data: dict
    :return: (synced_lyrics, unsynced_lyrics) tuple. items can be False.
    :rtype: str | bool

    """
    if json_data is None: return (False, False)

    lyrics = json_data.get("lyrics", {})
    syncType = lyrics.get("syncType", "")
    lines_data = lyrics.get("lines", [])
    lyrics_data = {
        "synced_lyrics": False,
        "unsynced_lyrics": False
    }
    
    def ms_to_timestamp(ms: int) -> str:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes:02d}:{seconds:05.2f}"

    def synced()-> str|bool:
        if syncType == "LINE_SYNCED":
            lyrics_data["synced_lyrics"] = ""
            for entry in lines_data:
                words = entry.get("words", "").strip()
                start_ms = int(entry["startTimeMs"])
                timestamp = ms_to_timestamp(start_ms)
                lyrics_data["synced_lyrics"] += f"[{timestamp}]{words}\n"
            return True
        return False

    def unsynced()-> str|bool:
        if syncType in ["UNSYNCED", "LINE_SYNCED"]: # to extract unynced lyrics from synced too..
            lyrics_data["unsynced_lyrics"] = ""
            for entry in lines_data:
                words = entry.get("words", "").strip()
                lyrics_data["unsynced_lyrics"] += f"{words}\n"
            return True
        return False
        
    if synced() is True:
        lyrics_data["synced_lyrics"] += "\nSource: MusixMatch via Spotify"
    if unsynced() is True:
        lyrics_data["unsynced_lyrics"] += "\nSource: MusixMatch via Spotify"

    return (lyrics_data["synced_lyrics"], lyrics_data["unsynced_lyrics"])

def extract_lrclib_lyrics(json_data: list[dict]) -> tuple:
    """
    extract lyrics and description from json data
    
    :param json_data: Description
    :type json_data: list[dict]
    :param mode: synced[0], unsynced[1], synced_with_fallback[2]
    :type mode: int
    :return: (synced_lyrics, synced_description, unsynced_lyrics, unsynced_description) tuple.
    :rtype: tuple
    
    """
    if not isinstance(json_data, list): return False
    
    def get_description(item:dict)->str:
        title = clean_string(item.get("trackName", ""))
        artist = clean_string(item.get("artistName", ""))
        album = clean_string(item.get("albumName", ""))
        return f"{title} {artist} {album}" # description

    def get_synced() -> str|bool:
        """
        get synced lyrics from lrclib
        
        :param json_data: lrclib json data
        :type json_data: list[dict]
        :return: (unsynced_lyrics, unsynced_description) items can be False
        :rtype: tuple

        """
        synced_lyrics:str = ""
        synced_description:str|bool = False
        for item in json_data:
            synced = item.get("syncedLyrics")    # can be str|None
            if  synced is not None:
                synced_lyrics = synced  + "\n\nSource: Lrclib"
                synced_description = get_description(item=item)
                return synced_lyrics, synced_description
        return (False, False)

    def get_unsynced() -> str|bool:
        """
        get unsynced lyrics from lrclib
        
        :param json_data: lrclib json data
        :type json_data: list[dict]
        :return: (unsynced_lyrics, unsynced_description) items can be False
        :rtype: tuple
        
        """
        unsynced_lyrics:str = ""
        unsynced_description:str|bool = False
        for item in json_data:
            unsynced = item.get("plainLyrics")   # can be str|None
            if  unsynced is not None:
                unsynced_lyrics = unsynced  + "\n\nSource: Lrclib"
                unsynced_description = get_description(item=item)
                return unsynced_lyrics, unsynced_description
        return (False, False)

    synced_lyrics, synced_description = get_synced()
    unsynced_lyrics, unsynced_description = get_unsynced()

    return (synced_lyrics, synced_description, unsynced_lyrics, unsynced_description)

def clear_profile_cache():
    PROFILE = Path("playwright_profile")
    SAFE_TO_DELETE = [
        "component_crx_cache",
        "Crashpad",
        "Default/Cache",
        "Default/Code Cache",
        "Default/DawnGraphiteCache",
        "Default/DawnWebGPUCache",
        "Default/GPUCache",
        "extensions_crx_cache",
        "GraphiteDawnCache",
        "GrShaderCache",
        "ShaderCache"
    ]
    for name in SAFE_TO_DELETE:
        path = PROFILE / name
        if path.exists():
            shutil.rmtree(path)
            # print(f"Deleted {path}")
    log.info("==== Playwright Profile Cache was safely cleared! ====")
    return True


if __name__ == "__main__":
    # build_search_query(song_path="C:\\Users\\Max\\Desktop\\music\\found\\Aanchal Tyagi - Dhak Dhak.flac")

    received_song_info = 'Tauba Tauba Salim–Sulaiman, Sonu Nigam, Kunal Ganjawala, Sunidhi Chauhan, Richa Sharma · Kaal (Original Motion Picture Soundtrack) · Song · 2005'
    flag = match_song_metadata(local_song_path="C:\\Users\\Max\\Desktop\\music\\Sonu Nigam - Tauba Tauba.flac", received_song_info=received_song_info, threshold=70)
    print(flag)

    

