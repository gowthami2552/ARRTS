"""
test_vercel_features.py — Test new endpoints inspired by arrts.vercel.app.
"""

import sys
import io
import json
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
BASE = "http://localhost:5000"


def http_post(path, data):
    body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=body,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))


def http_get(path):
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode('utf-8')


def main():
    print("=" * 60)
    print("Testing New ARRTS Features from arrts.vercel.app")
    print("=" * 60)

    # 1. Test /api/journey/explain - Why Best
    print("\n[1] Testing /api/journey/explain (why_best)...")
    sample_journey = {
        "type": "connecting",
        "source": "Visakhapatnam",
        "destination": "Chennai Central",
        "total_duration": "14h 30m",
        "journey_health": "Stable",
        "interchange_station": "Vijayawada Junction",
        "connection_minutes": 105,
        "segments": [
            {"train_number": "12717", "train_name": "Ratnachal SF Express", "departure": "12:30", "arrival": "18:35", "from": "Visakhapatnam"},
            {"train_number": "12839", "train_name": "Chennai Mail", "departure": "20:20", "arrival": "03:20", "to": "Chennai Central"}
        ]
    }
    exp1 = http_post("/api/journey/explain", {"journey": sample_journey, "type": "why_best"})
    print("  Title:", exp1.get("title"))
    print("  Explanation snippet:", exp1.get("explanation")[:120].replace('\n', ' '))
    print("  Metrics:", exp1.get("metrics"))
    assert "Vijayawada" in exp1.get("explanation"), "Expected interchange in explanation"
    print("  ✓ why_best PASSED!")

    # 2. Test /api/journey/explain - Transfer Safety
    print("\n[2] Testing /api/journey/explain (transfer_safety)...")
    exp2 = http_post("/api/journey/explain", {"journey": sample_journey, "type": "transfer_safety"})
    print("  Verdict:", exp2.get("verdict"))
    print("  Buffer breakdown:", exp2.get("buffer_breakdown"))
    assert "Safe" in exp2.get("verdict"), "Expected safe verdict"
    print("  ✓ transfer_safety PASSED!")

    # 3. Test /api/journey/explain - Next Action
    print("\n[3] Testing /api/journey/explain (next_action)...")
    exp3 = http_post("/api/journey/explain", {"journey": sample_journey, "type": "next_action"})
    print("  Action:", exp3.get("action"))
    print("  Steps count:", len(exp3.get("step_by_step", [])))
    assert len(exp3.get("step_by_step", [])) == 4, "Expected 4 steps"
    print("  ✓ next_action PASSED!")

    # 4. Test /api/ticket/generate - Smart General Ticket
    print("\n[4] Testing /api/ticket/generate (Smart General Ticket)...")
    tkt = http_post("/api/ticket/generate", {
        "from": "Visakhapatnam",
        "to": "Bengaluru",
        "train_number": "12863",
        "via": "Vijayawada"
    })
    print("  Ticket Type:", tkt.get("ticket_type"))
    print("  Ticket ID:", tkt.get("ticket_id"))
    print(f"  Route: {tkt.get('source')} → {tkt.get('destination')}")
    print(f"  Coach: {tkt.get('coach')} · Seat: {tkt.get('suggested_seat')}")
    print(f"  Fallback: {tkt.get('fallback_seat')}")
    print(f"  Fare: {tkt.get('fare')} · Validity: {tkt.get('validity')}")
    assert "UTS-ARRTS-" in tkt.get("ticket_id"), "Expected UTS ID"
    assert "GS-" in tkt.get("coach"), "Expected General coach"
    print("  ✓ Smart General Ticket PASSED!")

    # 5. Test AI Chatbot knowledge of new features
    print("\n[5] Testing Chatbot on Mission Mode & Smart Ticket...")
    chat_m = http_post("/api/chat", {"message": "What is Mission Mode in ARRTS?"})
    print("  Mission Mode Reply:", chat_m.get("reply")[:150].replace('\n', ' '))
    assert "Mission Mode" in chat_m.get("reply"), "Expected Mission Mode in reply"

    chat_t = http_post("/api/chat", {"message": "How does the smart general ticket work?"})
    print("  Smart Ticket Reply:", chat_t.get("reply")[:150].replace('\n', ' '))
    assert "Smart General Ticket" in chat_t.get("reply"), "Expected Smart Ticket in reply"
    print("  ✓ Chatbot feature knowledge PASSED!")

    # 6. Verify HTML frontend contains all components
    print("\n[6] Checking index.html markup for Vercel components...")
    html = http_get("/")
    assert "journey-dock" in html, "Expected journey-dock in HTML"
    assert "ticket-modal-overlay" in html, "Expected ticket modal in HTML"
    assert "settings-modal-overlay" in html, "Expected settings modal in HTML"
    assert "travel-intelligence-box" in html, "Expected travel intelligence in HTML"
    assert "search-mode-bar" in html, "Expected mode switcher in HTML"
    print("  ✓ Frontend Markup PASSED!")

    print("\n" + "=" * 60)
    print("🎉 ALL VERCEL FEATURE TESTS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    main()
