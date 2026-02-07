from pathlib import Path
import shutil

AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".m4a",".ogg", ".opus", ".alac", ".aiff"}

def move_audio_lrc_pairs(src_dir: str, dst_dir: str) -> bool:
    src = Path(src_dir)
    dst = Path(dst_dir)

    if not src.is_dir():
        raise ValueError(f"Source directory does not exist: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    for audio in src.iterdir():
        if audio.is_file() and audio.suffix.lower() in AUDIO_EXTENSIONS:
            lrc = audio.with_suffix(".lrc")

            if lrc.exists():
                shutil.move(audio, dst / audio.name)
                shutil.move(lrc, dst / lrc.name)
    
    print("Done")
    return True


if __name__ == "__main__":
    SOURCE_DIR = r"C:\\Users\\Max\\Desktop\\music"
    DEST_DIR = r"C:\\Users\\Max\\Desktop\\music\\found"

    move_audio_lrc_pairs(SOURCE_DIR, DEST_DIR)