"""
probe_ntes.py — Investigate the NTES API response format to fix the data generator.
"""
import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "X-Requested-With": "XMLHttpRequest",
    "Referer": "https://www.enquiry.indianrail.gov.in/mntes/",
    "Connection": "keep-alive",
}

URLS = [
    "https://www.enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=trnNum&trainNo=12841&action=journeyDetail",
    "https://www.enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=trnNum&trainNo=12841",
    "https://enquiry.indianrail.gov.in/mntes/q?opt=TR&subOpt=trnNum&trainNo=12841&action=journeyDetail",
]

session = requests.Session()
session.headers.update(HEADERS)

for url in URLS:
    print(f"\nURL: {url}")
    try:
        r = session.get(url, timeout=15)
        print(f"Status: {r.status_code}")
        print(f"Content-Type: {r.headers.get('content-type', 'unknown')}")
        print(f"First 500 chars: {r.text[:500]!r}")
    except Exception as e:
        print(f"ERROR: {e}")
