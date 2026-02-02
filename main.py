from utils.helpers import save_lyrics
from config import AUDIO_EXTENSIONS, MUSIC_DIRECTORY, OUTPUT_DIRECTORY, LYRICS_FETCH_MODE, LYRICS_SOURCES
from pathlib import Path
import logging
from utils.fetch import from_all

def main() -> int:
    """main function

    :return: 0
    :rtype: int
    """

    log = logging.getLogger(__name__)

    total_processed = 0
    total_found_and_saved = 0

    music_dir = Path(MUSIC_DIRECTORY)
    music_files = [f for f in music_dir.iterdir() if f.is_file() and f.suffix.lower() in AUDIO_EXTENSIONS]
    for song_path in music_files:        
        total_processed += 1
        log.info(f"{total_processed}. {song_path}")

        lyrics = from_all.fetch_lyrics(song_path=song_path, lyrics_fetch_mode=LYRICS_FETCH_MODE, lyrics_sources=LYRICS_SOURCES)

        # extract and save lyrics to location
        if lyrics:
            save_lyrics(lyrics=lyrics, out_dir=OUTPUT_DIRECTORY, out_filename=song_path.stem) # song.stem = song filename only
            total_found_and_saved += 1


    log.info("==== Summary ====")
    success_rate = (total_found_and_saved/total_processed)*100
    log.info(f"Success Rate: {success_rate:0.2f}% | {total_found_and_saved}/{total_processed}")
    
    return 0

if __name__ == "__main__":
    main()
