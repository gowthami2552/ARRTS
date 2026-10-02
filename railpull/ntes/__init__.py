"""
ntes/__init__.py — lightweight NTES API client.
Fetches train schedules from India's National Train Enquiry System.
"""
import json
import time
import random
import requests

NTES_BASE = "https://www.enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=trnNum&trainNo={train_no}&action=journeyDetail"
STATION_TRAINS_URL = "https://www.enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=stNum&stno={station_code}&action=arrDep"
NTES_SEARCH = "https://www.enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=trnNum&trainNo={prefix}&action=search"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ARRTS/1.0; research use)",
    "Accept": "application/json, */*",
    "Referer": "https://www.enquiry.indianrail.gov.in/mntes/",
}


class NTESError(Exception):
    pass


class NTESClient:
    def __init__(self, pause: float = 1.2):
        self.pause = pause
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    def _get(self, url: str) -> dict:
        time.sleep(self.pause + random.uniform(0, 0.3))
        resp = self.session.get(url, timeout=15)
        if resp.status_code == 404:
            raise NTESError(f"404: {url}")
        resp.raise_for_status()
        try:
            return resp.json()
        except Exception:
            raise NTESError(f"Non-JSON response from {url}")

    def search_trains(self, prefix: str) -> list:
        """Search trains by number prefix. Returns list of train dicts."""
        url = NTES_SEARCH.format(prefix=prefix)
        try:
            data = self._get(url)
            return data if isinstance(data, list) else data.get("trainsList", [])
        except NTESError:
            return []

    def get_schedule(self, train_no: str) -> dict | None:
        """Fetch full schedule for a train number. Returns raw NTES dict."""
        url = NTES_BASE.format(train_no=train_no)
        try:
            return self._get(url)
        except NTESError:
            return None
