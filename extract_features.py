"""
extract_features.py — Extract the exact text, logic, and structures of the top features in arrts.vercel.app
"""

import re

with open("data/vercel_bundle.js", "r", encoding="utf-8", errors="ignore") as f:
    js = f.read()

def print_contexts(keyword, max_matches=3, window=250):
    print(f"\n==================== Context for: {keyword} ====================")
    for m in re.finditer(re.escape(keyword), js, re.IGNORECASE):
        start = max(0, m.start() - window)
        end = min(len(js), m.end() + window)
        snippet = js[start:end]
        # clean snippet
        snippet = re.sub(r'[\r\n\t]+', ' ', snippet)
        print("...", snippet, "...\n")
        max_matches -= 1
        if max_matches <= 0:
            break

print_contexts("Smart General Ticket")
print_contexts("Mission Mode")
print_contexts("Why is this the best journey")
print_contexts("Is my transfer safe")
print_contexts("Alert when a better journey appears")
