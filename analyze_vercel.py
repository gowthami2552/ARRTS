"""
analyze_vercel.py — Analyze arrts.vercel.app frontend bundle to discover all features,
routes, UI components, tools, and widgets.
"""

import re
from pathlib import Path

bundle_path = Path("data/vercel_bundle.js")
if not bundle_path.exists():
    print("Bundle not found")
    exit(1)

with open(bundle_path, "r", encoding="utf-8", errors="ignore") as f:
    js = f.read()

print(f"Bundle size: {len(js)} chars")

# 1. Routes
routes = re.findall(r'path:\s*["\'](/[^"\']*)["\']', js)
print("\n=== Routes ===")
for r in sorted(set(routes)):
    if len(r) < 40:
        print(f"  {r}")

# 2. Page titles and headings
titles = re.findall(r'title:\s*["\']([^"\']{4,50})["\']', js)
print("\n=== Titles / Headings sample ===")
for t in list(set(titles))[:30]:
    print(f"  {t}")

# 3. Sidebar navigation / views
nav_labels = re.findall(r'label:\s*["\']([^"\']{3,30})["\']', js)
print("\n=== Navigation / Tab Labels ===")
for l in list(set(nav_labels))[:30]:
    print(f"  {l}")

# 4. Search for specific feature keywords
print("\n=== Specific Feature Mentions ===")
feature_keywords = [
    "PNR", "Live Status", "Train Tracker", "Seat Availability", "Fare",
    "Platform", "Coach", "Station", "Emergency", "SOS", "Delay",
    "Monitor", "Alarm", "Assistant", "Crowd", "Food", "Order", "Ticket"
]
for kw in feature_keywords:
    matches = set(re.findall(rf'["\']([^"\']{{0,30}}{kw}[^"\']{{0,30}})["\']', js, re.IGNORECASE))
    filtered = [m.strip() for m in matches if 4 <= len(m.strip()) <= 45 and not m.startswith("http") and not m.startswith("data:")]
    if filtered:
        print(f"\n[{kw}]:")
        for m in sorted(filtered)[:5]:
            print(f"    • {m}")
