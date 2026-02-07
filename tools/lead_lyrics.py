import re
from pathlib import Path

TIME_PATTERN = re.compile(r"\[(\d{2}):(\d{2}\.\d{2})\]")

def shift_lrc_timestamps(src_dir: str,dst_dir: str,offset_seconds: float) -> bool:
    src = Path(src_dir)
    dst = Path(dst_dir)

    if not src.is_dir(): raise ValueError(f"Source directory does not exist: {src}")

    dst.mkdir(parents=True, exist_ok=True)

    def replace_time(match: re.Match) -> str:
        minutes = int(match.group(1))
        seconds = float(match.group(2))

        total_seconds = minutes * 60 + seconds + offset_seconds
        if total_seconds < 0:
            total_seconds = 0.0

        new_minutes = int(total_seconds // 60)
        new_seconds = total_seconds % 60

        return f"[{new_minutes:02d}:{new_seconds:05.2f}]"

    for lrc_file in src.glob("*.lrc"):
        content = lrc_file.read_text(encoding="utf-8")

        updated = TIME_PATTERN.sub(replace_time, content)

        out_path = dst / lrc_file.name
        out_path.write_text(updated, encoding="utf-8")
    print("Done")
    return True


# you can replace original .lrc files by making 'DEST_DIR = SOURCE_DIR'
if __name__ == "__main__":
    SOURCE_DIR = r"C:\\Users\\Max\\Desktop\\music\\found"
    DEST_DIR = r"C:\\Users\\Max\\Desktop\\music\\found"
    # offset = lyrics lead(-ve), lyrics lag(+ve)
    shift_lrc_timestamps(src_dir=SOURCE_DIR, dst_dir=DEST_DIR, offset_seconds=-0.25) # Recommended: -0.25