<p align="center">
  <img src="assets/cover.png" alt="lyricsforge cover" width="100%">
</p>

fetch lyrics from musixmatch-via-spotify, lrclib, genius, jiosaavn. 

## Steps to follow -
1. **setup a virtual environment**
```pwsh
python -m venv .venv
```

```pwsh
.venv\Scripts\activate.ps1
```

2. **install required packages**
``` pwsh
pip install -r requirements.txt
```

3. **set preferences in config**

4. **save your auth token(s) in .env**
  - GENIUS_ACCESS_TOKEN, SP_DC_TOKEN

5. run **main.py**

### Notes -
1. you can use MP3TAG (https://www.mp3tag.de/) to embed lyrics to songs.
2. you can check logs in **main.log** file.