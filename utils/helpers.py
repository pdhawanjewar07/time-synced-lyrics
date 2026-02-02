import time
import random
import re
from mutagen import File
import logging
from rapidfuzz import fuzz

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
    clean_string = re.sub(r"[^a-z0-9\s]", " ", clean_string)  # remove punctuation
    clean_string = re.sub(r"\s*Various Interprets", "", clean_string, flags=re.IGNORECASE)  # remove "Various Interprets"
    clean_string = re.sub(r"\s+", " ", clean_string).strip()  # clean excess whitespace
    return clean_string

def match_song_metadata(local_song_path:str, received_song_info:str, threshold:float) -> bool:
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

    flag = True

    score_title = fuzz.partial_ratio(local_song_title, received_song_info)
    if score_title<threshold: flag = False
    # print(f"_title_match_score: {score_title:0.2f}%")
    # print(f"__local_title_info: {local_song_title}")
    # print(f"received_song_info: {received_song_info}")
    

    # score_artist = fuzz.partial_ratio(local_song_artist, received_song_info)
    # if score_artist<threshold: flag = False
    # print(f"artist_match_score: {score_artist}")
    # print(f"_local_artist_info: {local_song_title}")
    # print(f"received_song_info: {received_song_info}")

    score_album = fuzz.partial_ratio(local_song_album, received_song_info)
    if score_album<threshold: flag = False
    # print(f"_album_match_score: {score_album:0.2f}%")
    # print(f"__local_album_info: {local_song_title}")
    # print(f"received_song_info: {received_song_info}")
    
    
    return flag

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
    log.info(f"WAITING - {sleep_duration:0.2f}s before next lrclib request")
    time.sleep(sleep_duration)

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
    if json_data is None: return False

    lyrics = json_data.get("lyrics", {})
    syncType = lyrics.get("syncType", "")
    lines_data = lyrics.get("lines", [])
    lyrics = {
        "synced_lyrics": "",
        "unsynced_lyrics": ""
    }
    

    def ms_to_timestamp(ms: int) -> str:
        minutes = ms // 60000
        seconds = (ms % 60000) / 1000
        return f"{minutes:02d}:{seconds:05.2f}"

    def synced()-> str|bool:
        if syncType == "LINE_SYNCED":
            for entry in lines_data:
                words = entry.get("words", "").strip()
                # if not words: continue
                start_ms = int(entry["startTimeMs"])
                timestamp = ms_to_timestamp(start_ms)
                lyrics["synced_lyrics"] += f"\n[{timestamp}]{words}"
            return True
        return False

    def unsynced()-> str|bool:
        if syncType in ["LINE_SYNCED", "UNSYNCED"]:
            for entry in lines_data:
                words = entry.get("words", "").strip()
                # if not words: continue
                lyrics["unsynced_lyrics"] += f"\n[{words}"
            return True
        return False
        
    if synced() is True:
        lyrics["synced_lyrics"] += "\n\nSource: MusixMatch via Spotify"
    if unsynced() is True:
        lyrics["unsynced_lyrics"] += "\n\nSource: MusixMatch via Spotify"

    return (lyrics["synced_lyrics"], lyrics["unsynced_lyrics"])

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
    
    synced_lyrics:str|None = None
    unsynced_lyrics:str|None = None
    synced_description:str|bool = None
    unsynced_description:str|bool = None

    def get_description(item:dict)->str:
        title = clean_string(item.get("trackName", ""))
        artist = clean_string(item.get("artistName", ""))
        album = clean_string(item.get("albumName", ""))
        return f"{title} {artist} {album}" # description

    def get_synced_description() -> str|bool:
        """
        get synced lyrics from lrclib
        
        :param json_data: lrclib json data
        :type json_data: list[dict]
        :return: synced lyrics & description if found, otherwise False
        :rtype: tuple | bool

        """
        for item in json_data:
            synced_lyrics = item.get("syncedLyrics")    # can be str|None
            if  synced_lyrics is not None:
                synced_lyrics = synced_lyrics  + "\n\nSource: Lrclib"
                synced_description = get_description(item=item)
                return synced_description
        return False

    def get_unsynced_description() -> str|bool:
        """
        get unsynced lyrics from lrclib
        
        :param json_data: lrclib json data
        :type json_data: list[dict]
        :return: unsynced lyrics & description if found, otherwise False
        :rtype: tuple | bool
        
        """
        for item in json_data:
            unsynced_lyrics = item.get("plainLyrics")   # can be str|None
            if  unsynced_lyrics is not None:
                unsynced_lyrics = unsynced_lyrics  + "\n\nSource: Lrclib"
                unsynced_description = get_description(item=item)
                return unsynced_description
        return False

    synced_description = get_synced_description()
    unsynced_description = get_unsynced_description()

    return (synced_lyrics, synced_description, unsynced_lyrics, unsynced_description)




if __name__ == "__main__":
    # build_search_query(song_path="C:\\Users\\Max\\Desktop\\music\\found\\Aanchal Tyagi - Dhak Dhak.flac")

    received_song_info = 'Tauba Tauba Salim–Sulaiman, Sonu Nigam, Kunal Ganjawala, Sunidhi Chauhan, Richa Sharma · Kaal (Original Motion Picture Soundtrack) · Song · 2005'
    flag = match_song_metadata(local_song_path="C:\\Users\\Max\\Desktop\\music\\Sonu Nigam - Tauba Tauba.flac", received_song_info=received_song_info, threshold=70)
    print(flag)

