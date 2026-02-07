import hashlib
import hmac
import math
import requests


# thanks to https://github.com/xyloflake/spot-secrets-go/
SECRET_CIPHER_DICT_URL = "https://github.com/xyloflake/spot-secrets-go/blob/main/secrets/secretDict.json?raw=true"
class TOTP:
    def __init__(self) -> None:
        self.secret, self.version = self.get_secret_version()
        self.period = 30
        self.digits = 6

    def generate(self, timestamp: int) -> str:
        counter = math.floor(timestamp / 1000 / self.period)
        counter_bytes = counter.to_bytes(8, byteorder="big")

        h = hmac.new(self.secret, counter_bytes, hashlib.sha1)
        hmac_result = h.digest()

        offset = hmac_result[-1] & 0x0F
        binary = (
            (hmac_result[offset] & 0x7F) << 24
            | (hmac_result[offset + 1] & 0xFF) << 16
            | (hmac_result[offset + 2] & 0xFF) << 8
            | (hmac_result[offset + 3] & 0xFF)
        )

        return str(binary % (10**self.digits)).zfill(self.digits)
    
    def get_secret_version(self) -> tuple[str, int]:
        req = requests.get(SECRET_CIPHER_DICT_URL)
        if req.status_code != 200:
            print("Failed to fetch TOTP secret and version.")
        data = req.json()
        secret_version = list(data.keys())[-1]
        ascii_codes = data[secret_version]
        transformed = [val ^ ((i % 33) + 9) for i, val in enumerate(ascii_codes)]
        secret_key = "".join(str(num) for num in transformed)
        return bytes(secret_key, 'utf-8'), secret_version