# preferences
LYRICS_SOURCES = ["musixmatch-via-spotify", "lrclib", "genius"] # "lyricsfind-via-ytmusic"
AUDIO_EXTENSIONS = {".mp3", ".flac", ".wav", ".aac", ".m4a",".ogg", ".opus", ".alac", ".aiff"}

# music paths
MUSIC_DIRECTORY = "C:/Users/Max/Desktop/music/small" # non recursive musixmatch_found
OUTPUT_DIRECTORY = "C:/Users/Max/Desktop/music/small"

# chrome & driver paths
DRIVER_PATH = "C:/Users/Max/Desktop/VS-Code/Github Repositories/time-synced-lyrics/bin/chromedriver-win64/chromedriver.exe"  # must correspond to chrome version
CHROME_BINARY = r"C:/Users/Max/Desktop/VS-Code/Github Repositories/time-synced-lyrics/bin/chrome-win64/chrome.exe"

# selenium element identifiers
SPOTIFY_TRACK_CSS_SELECTOR = "#searchPage > div > div > div > div.eaxF79s4oV8I2CPQ > div > div.m9t_KhZ6MI0XQj9b > div:nth-child(2) > div:nth-child(1) > div > div.NILrlF6tOUcbSyzo > div > a > div"
GENIUS_LYRICS_ELEMENT_XPATH = '//*[@id="lyrics-root"]/div[1]'

