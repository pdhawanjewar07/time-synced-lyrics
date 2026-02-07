import requests
import json
import os
import time
from dotenv import load_dotenv
from utils.totp import TOTP

# ------------------------------------------
TOKEN_URL = "https://open.spotify.com/api/token"
SERVER_TIME_URL = "https://open.spotify.com/api/server-time"
SPOTIFY_HOME_PAGE_URL = "https://open.spotify.com/"
CLIENT_VERSION = "1.2.46.25.g7f189073"

HEADERS = {
    "accept": "application/json",
    "accept-language": "en-US",
    "content-type": "application/json",
    "origin": SPOTIFY_HOME_PAGE_URL,
    "referer": SPOTIFY_HOME_PAGE_URL,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/127.0.0.0 Safari/537.36"
    ),
    "spotify-app-version": CLIENT_VERSION,
    "app-platform": "WebPlayer",
}

REFRESH_MARGIN_MS = 5 * 60 * 1000  # 5 minutes
# ------------------------------------------

load_dotenv()
SP_DC = os.getenv("SP_DC_TOKEN")
if not SP_DC:
    raise RuntimeError("SP_DC_TOKEN missing")

# ------------------------------------------

class SpotifyAuthManager:
    def __init__(self, sp_dc: str = SP_DC):
        self.session = requests.Session()
        self.session.cookies.set("sp_dc", sp_dc)
        self.session.headers.update(HEADERS)

        self.totp = TOTP()
        self.access_token = None
        self.expires_at_ms = 0

    def _get_server_time_ms(self) -> int:
        r = self.session.get(SERVER_TIME_URL, timeout=10)
        r.raise_for_status()
        return r.json()["serverTime"] * 1000

    def _mint_token(self):
        server_time_ms = self._get_server_time_ms()

        totp_code = self.totp.generate(timestamp=server_time_ms)

        params = {
            "reason": "init",
            "productType": "web-player",
            "totp": totp_code,
            "totpVer": str(self.totp.version),
            "ts": str(server_time_ms),
        }

        r = self.session.get(TOKEN_URL, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()

        self.access_token = data["accessToken"]
        self.expires_at_ms = data["accessTokenExpirationTimestampMs"]

        # Optional debug dump
        # with open("sp_token_data.json", "w", encoding="utf-8") as f:
        #     json.dump(data, f, indent=2)

    def get_token(self) -> str:
        now_ms = int(time.time() * 1000)

        if (
            not self.access_token
            or now_ms >= self.expires_at_ms - REFRESH_MARGIN_MS
        ):
            self._mint_token()

        return self.access_token

# ------------------------------------------
# Usage
if __name__ == "__main__":
    auth = SpotifyAuthManager()
    token = auth.get_token()
    print(token)



