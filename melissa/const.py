"""Constants for Melissa platform."""

from typing import Dict

MELISSA_URL: str = "http://developer-api.seemelissa.com/v1/%s"
CLIENT_DATA: Dict[str, str] = {
    "client_id": "mclimate",
    "client_secret": "mclimate_core",
}
HEADERS: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 7.0; SM-G935F Build/NRD90M; wv)"
    " AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0"
    " Chrome/63.0.3239.111 Mobile Safari/537.36",
    "Connection": "keep-alive",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,sv-SE;q=0.9",
    "X-Requested-With": "at.cloudfaces.melissa",
}

CHANGE_THRESHOLD: int = 10
MIN_HUMIDITY_ALLOWED: int = 10
CHANGE_TIME_CACHE_DEFAULT: int = 120  # 2 min default
