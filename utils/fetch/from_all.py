from utils.fetch.musixmatch import fetch_lyrics as fetch_musixmatch
from utils.fetch.lrclib import fetch_lyrics as fetch_lrclib
from utils.fetch.genius import fetch_lyrics as fetch_genius
import logging

log = logging.getLogger(__name__)

SOURCE_FETCHERS = {
    "MusixMatch": fetch_musixmatch,
    "Lrclib": fetch_lrclib,
    "Genius": fetch_genius
}


def fetch_lyrics(song_path:str, fetch_mode:int) -> str|bool:
    """fetch lyrics from all sources

    :param song_path: song path
    :type song_path: str
    :param fetch_mode: synced[0], unsynced[1], synced_with_fallback[2]
    :type fetch_mode: int
    :return: lyrics if found, otherwise False
    :rtype: str | bool
    """
    for source_name, source in SOURCE_FETCHERS.items():  # use source as module
        synced_lyrics, unsynced_lyrics = source(song_path=song_path)

        match fetch_mode:
            case 0: # synced only
                if synced_lyrics is not False:
                    log.info(f"SUCCESS - {source_name}: synced lyrics found")
                    return synced_lyrics
            case 1: # unsynced only
                if unsynced_lyrics is not False:
                    log.info(f"SUCCESS - {source_name}: unsynced lyrics found")
                    return unsynced_lyrics
            case _: # Default: synced with fallback
                if synced_lyrics is not False:
                    log.info(f"SUCCESS - {source_name}: synced lyrics found")
                    return synced_lyrics
                if unsynced_lyrics is not False:
                    log.info(f"SUCCESS - {source_name}: unsynced lyrics found")
                    return unsynced_lyrics
        log.info(f"FAILURE - {source_name}: synced/unsynced lyrics not found")

    return False



if __name__ == "__main__":
    SONG_PATHS = [
        "C:\\Users\\Max\\Desktop\\music\\small\\Sunidhi Chauhan - Tanha Tere Bagair.flac", # musixmatch only
        "C:\\Users\\Max\\Desktop\\music\\small\\Shreya Ghoshal - Cry Cry.flac", # lrclib only
        "C:\\Users\\Max\\Desktop\\music\\small\\Outstation - Tum Se.flac", # both
        "C:\\Users\\Max\\Desktop\\music\\small\\Heil Hitler Kanye West.flac" # none
        ]
    for i, song in enumerate(SONG_PATHS):
        print(f"{i+1}. {song}")
        lyrics = fetch_lyrics(song_path=song, fetch_mode=2)
        if lyrics is not False:
            with open(f"lyrics/{i+1}.lrc", "w", encoding="utf-8") as f:
                f.write(song + "\n\n" + lyrics)


