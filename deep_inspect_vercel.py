"""
deep_inspect_vercel.py — Search for visible texts, modals, buttons, and views in the bundle.
"""

import re
from pathlib import Path

with open("data/vercel_bundle.js", "r", encoding="utf-8", errors="ignore") as f:
    js = f.read()

# Find strings inside JSX children: "...", or text in button labels
texts = re.findall(r'children:\s*["\']([A-Z][A-Za-z0-9\s\.\-—\?:!]{3,60})["\']', js)
print("=== Common JSX Children / Headings ===")
for t in sorted(set(texts)):
    if not t.startswith("http") and not any(skip in t for skip in ["Resize", "SVG", "Path", "Clip", "Scale"]):
        print("  •", t)

# Look for button texts
btn_texts = re.findall(r'<button[^>]*>([^<]+)</button>', js)
print("\n=== Button texts ===")
for b in sorted(set(btn_texts))[:30]:
    print("  •", b)

# Search for navigation items or tabs
print("\n=== Navigation / Tab items ===")
nav_matches = re.findall(r'["\'](Home|Search|My Journeys|Monitor|Live|Tracker|Tickets?|Booking|Settings|Profile|History|Alerts|Notifications|AI Assistant|Crowd|Platform|Station Status|Digital Ticket)["\']', js)
print(set(nav_matches))
