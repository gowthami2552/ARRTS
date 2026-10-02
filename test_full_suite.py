"""
test_full_suite.py — Comprehensive test for ARRTS with ingested attachments & AI Chatbot.
"""

import sys
import io
import json
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_URL = "http://localhost:5000"


def http_get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def http_post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def run_tests():
    print("=" * 60)
    print("Running ARRTS Full Test Suite (Attachments + AI Chatbot)")
    print("=" * 60)

    # 1. Status Check
    print("\n[1] Checking /api/status...")
    status = http_get("/api/status")
    print(f"  Status: {status.get('status')}")
    print(f"  Data Loaded: {status.get('data_loaded')}")
    print(f"  Trains in System: {status.get('trains')}")
    print(f"  Stops in System: {status.get('stops')}")
    print(f"  Stations in System: {status.get('stations')}")
    assert status.get("trains") >= 5000, f"Expected >= 5000 trains, got {status.get('trains')}"
    assert status.get("stations") >= 4500, f"Expected >= 4500 stations, got {status.get('stations')}"
    print("  ✓ Status Check PASSED!")

    # 2. Search Check: VSKP -> MAS
    print("\n[2] Checking /api/search (VSKP -> MAS)...")
    search_res = http_get("/api/search?from=VSKP&to=MAS&date=2026-09-29&buffer=15")
    direct = search_res["results"]["direct"]
    connecting = search_res["results"]["connecting"]
    print(f"  Direct Journeys: {len(direct)}")
    print(f"  Connecting Journeys: {len(connecting)}")
    assert len(direct) >= 1, "Expected at least 1 direct journey"
    assert len(connecting) >= 10, "Expected at least 10 connecting journeys"
    print(f"  Sample Direct: Train {direct[0]['segments'][0]['train_number']} {direct[0]['segments'][0]['train_name']}")
    print(f"  Sample Connecting: via {connecting[0]['interchange_station']} ({connecting[0]['total_duration']})")
    print("  ✓ Search Check PASSED!")

    # 3. AI Chatbot Test: Tatkal Hacks
    print("\n[3] Testing AI Chatbot: Tatkal Hacks...")
    chat1 = http_post("/api/chat", {"message": "What are the best tatkal booking hacks?"})
    assert "Master List" in chat1["reply"], "Expected Master List hack in reply"
    assert "10:00 AM" in chat1["reply"], "Expected 10:00 AM in reply"
    print("  Reply preview:\n " + "\n  ".join(chat1["reply"].splitlines()[:5]))
    print(f"  Follow-up suggestions: {chat1.get('suggestions')}")
    print("  ✓ Tatkal Hacks Chatbot PASSED!")

    # 4. AI Chatbot Test: Charting & RAC
    print("\n[4] Testing AI Chatbot: Charting & RAC...")
    chat2 = http_post("/api/chat", {"message": "How does chart preparation and RAC work?"})
    assert "Current Booking" in chat2["reply"], "Expected Current Booking in reply"
    assert "4 hours" in chat2["reply"], "Expected 4 hours in reply"
    print("  Reply preview:\n " + "\n  ".join(chat2["reply"].splitlines()[:5]))
    print("  ✓ Charting & RAC Chatbot PASSED!")

    # 5. AI Chatbot Test: Food & Pantry MRP
    print("\n[5] Testing AI Chatbot: Food & Pantry MRP...")
    chat3 = http_post("/api/chat", {"message": "How much should I pay for train food and Rail Neer?"})
    assert "15" in chat3["reply"], "Expected Rail Neer Rs 15 price in reply"
    assert "e-Catering" in chat3["reply"] or "Food on Track" in chat3["reply"], "Expected e-Catering mention"
    print("  Reply preview:\n " + "\n  ".join(chat3["reply"].splitlines()[:5]))
    print("  ✓ Food & Pantry Chatbot PASSED!")

    # 6. AI Chatbot Test: Live Train Search Query
    print("\n[6] Testing AI Chatbot: Live Route Query (Visakhapatnam to Chennai)...")
    chat4 = http_post("/api/chat", {"message": "Find trains from Visakhapatnam to Chennai"})
    assert "Direct" in chat4["reply"] or "Connecting" in chat4["reply"], "Expected train results in chat response"
    print("  Reply preview:\n " + "\n  ".join(chat4["reply"].splitlines()[:6]))
    if chat4.get("train_data"):
        td = chat4["train_data"]
        print(f"  Returned train data: {td.get('direct_count')} direct, {td.get('connecting_count')} connecting")
    print("  ✓ Chatbot Live Route Search PASSED!")

    # 7. AI Chatbot Suggestions API
    print("\n[7] Testing /api/chat/suggestions...")
    sug_res = http_get("/api/chat/suggestions")
    categories = sug_res.get("categories", [])
    print(f"  Found {len(categories)} categories")
    for cat in categories:
        print(f"   • {cat['label']} ({len(cat['prompts'])} prompts)")
    assert len(categories) >= 5, "Expected at least 5 categories"
    print("  ✓ Chatbot Suggestions PASSED!")

    print("\n" + "=" * 60)
    print("🎉 ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()
