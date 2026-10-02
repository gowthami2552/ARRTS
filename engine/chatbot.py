"""
chatbot.py — ARRTS AI Railway Travel Assistant & Travel Hacks Expert.

Features:
1. Deep railway travel knowledge base (IRCTC booking, Tatkal hacks, RAC/WL, chart prep,
   berth selection, baggage/pet rules, catering MRP, circular journeys, TDR & refunds).
2. Live route query capabilities: understands natural queries like "trains from Visakhapatnam to Chennai"
   and retrieves direct and connecting routes using the ARRTS engine.
3. Proactive questioning: asks follow-up questions to understand travel preferences,
   group composition, urgency, and budget.
4. Returns rich conversational markdown, structured train cards, and interactive suggestion pills.
"""

import re
from datetime import date, datetime, timedelta
from typing import Any, Optional

import pandas as pd


# ── Travel Hacks & Railway Rules Knowledge Base ──────────────────────────────

KNOWLEDGE_BASE = {
    "tatkal": {
        "title": "⚡ Ultimate Tatkal Booking Hacks (IRCTC)",
        "content": """### ⚡ Pro Tatkal Booking Hacks for Confirmed Tickets

1. **Exact Timing Rules:**
   - **AC Classes (1A, 2A, 3A, 3E, CC):** Opens at **10:00 AM IST** sharp, exactly 1 day prior to train origin departure date.
   - **Non-AC Classes (SL, 2S):** Opens at **11:00 AM IST** sharp.
   - *Note:* If your boarding station is Day 2 of the train's run, Tatkal still opens based on the **train's originating station date**!

2. **The Master List Trick (Saves 30–45 seconds):**
   - Go to *IRCTC Profile → Master List* well in advance.
   - Save all passenger details (Name, Age, Gender, Berth Preference, ID Card).
   - During Tatkal booking, click **"Add from Master List"**—passengers are selected in 1 click without manual typing!

3. **Lightning-Fast Payment Hack (No OTP delays):**
   - Traditional SMS OTP often arrives late and Tatkal berths vanish in seconds.
   - **Best Payment Option 1:** **IRCTC iMudra / IRCTC e-Wallet** (OTP-less or 1-tap approval).
   - **Best Payment Option 2:** **UPI via dynamic QR Code** (Scan immediately from PhonePe/GooglePay/Paytm—no waiting for bank SMS!).

4. **Login Timing Sweet Spot:**
   - Log in at **09:58 AM** for AC, and **10:58 AM** for Sleeper.
   - If you log in before 09:55 AM, IRCTC's security token expires right during checkout!

5. **Alternate Station / Quota Hack:**
   - If Tatkal quota from your station is waitlisted, check Tatkal availability from **1 or 2 stations earlier**. You can book from there and change your boarding station!
   - Consider **3E (3 AC Economy)** or **2A**—they often have seats remaining when 3A gets waitlisted instantly.
""",
        "follow_ups": [
            "How does Premium Tatkal differ from normal Tatkal?",
            "What happens if my Tatkal ticket remains Waitlisted (TQWL)?",
            "Can I change passenger names on a Tatkal ticket?",
            "Search trains for my journey"
        ]
    },

    "chart_prep": {
        "title": "📋 Chart Preparation & RAC / WL Confirmation Rules",
        "content": """### 📋 Chart Preparation Rules & RAC Secrets

1. **When is the Reservation Chart Prepared?**
   - **First Chart:** Prepared **4 hours before** scheduled departure of the train from its origin station (or 8:00 PM the previous evening for morning trains before 12:00 noon).
   - **Second & Final Chart:** Prepared **30 minutes before** train departure at the station.

2. **Current Booking Counter (Up to 10%–30% Discount):**
   - Once the first chart is prepared, any vacant berths are moved to **"Current Booking"**.
   - You can book these online on IRCTC or at station PRS counters at regular or discounted fares right until 30 minutes before departure!

3. **Waitlist Priority Order (Higher to Lower Chance of Confirmation):**
   - **GNWL (General Waiting List):** Highest confirmation chance. Cancels from the entire route pool confirm your seat.
   - **RLWL (Remote Location Waiting List):** Moderate confirmation chance; pooled from specific intermediate hubs.
   - **PQWL (Pooled Quota Waiting List):** Lower confirmation chance for intermediate legs.
   - **TQWL (Tatkal Waiting List):** Lowest confirmation probability. Avoid unless WL 1 to 3!

4. **RAC (Reservation Against Cancellation) Rules:**
   - An RAC ticket guarantees you can legally **board the train**!
   - You get half of a Side Lower (SL) berth (seated during day, shared at night).
   - Whenever any confirmed passenger cancels or does not turn up, RAC passengers get upgraded to full confirmed berths first in numerical order!
""",
        "follow_ups": [
            "What is Current Booking and how to get discounted tickets?",
            "How to check PNR status and confirmation probability?",
            "What if my e-ticket remains fully Waitlisted after chart prep?",
            "Search direct and connecting trains"
        ]
    },

    "connecting_hacks": {
        "title": "🔀 Connecting Journeys & Missed Connection Rights (Rule 23)",
        "content": """### 🔀 Connecting Journey Hacks & IRCTC Rule 23

1. **How ARRTS Helps with Connecting Journeys:**
   - When direct trains are full or unavailable, ARRTS automatically computes 1-transfer connecting routes across intermediate junction hubs (like Vijayawada, Rajahmundry, Howrah, Nagpur, Pune).
   - You can set custom buffer times (15 to 60+ minutes) to ensure safe, relaxed transfers!

2. **Indian Railways Rule 23 (Protection Against Missed Connections):**
   - If you book connecting tickets with linked PNRs (or declare connecting PNRs on IRCTC), and Train 1 runs late causing you to miss Train 2:
     - **Full refund** is granted on the unused connecting journey ticket without cancellation fee!
     - Alternatively, the Station Master / TTE can endorse your ticket for free travel on the **next available train** in the same class!

3. **Safe Buffer Recommendations:**
   - **Same Platform / Small Station:** Minimum 30–45 minutes.
   - **Major Junction Hub (BZA, HWH, NDLS, PUNE):** Minimum 60–90 minutes.
   - **Fog / Winter Seasons (Northern India):** Recommend 2 to 3 hours buffer due to morning fog delays.
""",
        "follow_ups": [
            "How to link two PNRs for connecting journey guarantee?",
            "What should I do at the station if my first train is running late?",
            "Find connecting trains for my route",
            "What are the best berth selection hacks?"
        ]
    },

    "berth_hacks": {
        "title": "💺 Best Berth, Seat & Coach Selection Hacks",
        "content": """### 💺 Smart Berth & Coach Selection Hacks

1. **Solo Travelers:**
   - Choose **Side Lower (SL)**: Offers personal window view, dedicated small table, luggage under seat, and your own power charging socket!
   - Choose **Side Upper (SU)**: Cleanest, undisturbed privacy without anyone requesting you to fold down the middle berth.

2. **Couples & Privacy:**
   - In **First AC (1A)**, there are two types of rooms: **Coupe (2 berths)** and **Cabin (4 berths)**.
   - If booking for 2 passengers, select *Coupe preference*. Cabin allocation is decided during chart preparation, and couples are given top priority for 2-berth Coupes!

3. **Senior Citizens & Pregnant Women (Lower Berth Quota):**
   - Male passengers aged 60+ and female passengers aged 45+ traveling alone or in pairs qualify for the **Lower Berth Quota (SS)**.
   - Always check the "Lower Berth Quota" option if eligible—it has dedicated seats even when General Quota is waitlisted!

4. **Which Coach Bay is the Quietest?**
   - **Avoid berths 1–8 and 65–72:** Located right next to the vestibules, heavy door banging, and toilet aromas.
   - **Best berths: 25 to 55** (Middle of the coach): Smoothest ride, least noise, furthest from toilets.
""",
        "follow_ups": [
            "How does First AC Coupe allocation work?",
            "Where are mobile charging sockets located in different classes?",
            "Tell me about food and catering hacks on trains",
            "Plan my journey now"
        ]
    },

    "food_hacks": {
        "title": "🍱 Food, Pantry & Catering Secrets (Avoid Overcharging)",
        "content": """### 🍱 Train Catering Secrets & Overcharging Defense

1. **Official IRCTC Mandated Meal Rates (Do NOT pay more!):**
   - **Standard Veg Breakfast:** ₹40
   - **Standard Non-Veg Breakfast (Egg):** ₹50
   - **Standard Veg Thali (Rice, Dal, Subzi, 2 Parathas/Rotis, Curd):** ₹80
   - **Standard Non-Veg Meal (Egg Curry):** ₹90
   - **Chicken Meal (Standard):** ₹130
   - **Rail Neer (1 Litre):** Exactly ₹15 (Pantry vendors often illegally demand ₹20—strictly refuse and demand bill).
   - **Tea (Tea bag + Hot water):** ₹10

2. **The "No Bill = Free Meal" Policy:**
   - Under official Indian Railways consumer policy, if the vendor refuses to provide a printed POS bill, you are entitled to refuse payment!

3. **IRCTC e-Catering ("Food on Track"):**
   - You don't have to eat pantry food! Download the *IRCTC Food on Track* app or website.
   - Enter your PNR to order from top restaurant chains like **Domino's, Haldiram's, Subway, Behrouz Biryani, Saravana Bhavan**, delivered hot directly to your seat at intermediate stations.

4. **Emergency Complaint:**
   - If a vendor overcharges or misbehaves, tweet to **@RailMinIndia** / **@IRCTCofficial** with your PNR and coach number, or call **139** (RailMadad). Action is typically taken within 1–2 hours at the next stop!
""",
        "follow_ups": [
            "What if pantry staff refuses to give a bill?",
            "How does IRCTC e-Catering work for late night arrivals?",
            "What are luggage and pet travel rules?",
            "Search train schedules"
        ]
    },

    "luggage_pets": {
        "title": "🐾 Pet Travel & Luggage Rules in Indian Railways",
        "content": """### 🐾 Luggage Limits & Traveling with Pets

1. **Luggage Allowance per Passenger (Free):**
   - **First AC (1A):** 70 kg free allowance + 15 kg marginal
   - **Second AC (2A):** 50 kg free allowance + 10 kg marginal
   - **Third AC (3A) & AC Chair Car (CC):** 40 kg free allowance
   - **Sleeper Class (SL):** 40 kg free allowance
   - **Second Sitting (2S):** 35 kg free allowance

2. **Traveling with Dogs or Cats:**
   - **Option A (In your compartment):** Only permitted in **First AC (1A)**. You must book the **entire 2-berth Coupe or 4-berth Cabin** exclusively under one PNR. No other passenger must share the room.
   - **Option B (Brake Van Dog Box):** For all other classes, pets must travel in the special Dog Box located in the Guard's Brake Van (SLR coach).
   - **Mandatory Requirements:**
     - A valid fitness & vaccination certificate from a registered veterinarian (issued within 24–48 hours of travel).
     - Visit the parcel office at the origin station 3 hours before departure to weigh the pet and pay the pet ticket fee.
""",
        "follow_ups": [
            "How to book an entire 1A coupe for pet travel?",
            "What items are prohibited on Indian trains?",
            "Tell me about Circular Journey tickets",
            "Search trains"
        ]
    },

    "refunds_tdr": {
        "title": "💰 TDR, Cancellation & Refund Hacks",
        "content": """### 💰 TDR Filing & Refund Rules

1. **Waitlisted e-Tickets After Chart Prep:**
   - If your e-ticket remains fully waitlisted after chart preparation, IRCTC **automatically cancels it and refunds 100% of the fare** directly to your payment source within 3–5 working days!
   - You cannot board reserved coaches with a waitlisted e-ticket.

2. **When to File a TDR (Ticket Deposit Receipt):**
   - **Train running late by > 3 hours:** 100% refund without cancellation fee! File TDR before train departure.
   - **AC failure in AC coach:** Difference of fare between AC and Sleeper class is refunded. Obtain certificate from TTE and file TDR within 20 hours.
   - **Train cancelled by Railways:** 100% automatic refund—no need to file TDR!
   - **Missed connection due to late running train:** File TDR under Rule 23 within 3 hours of train arrival at interchange station.
""",
        "follow_ups": [
            "How long does IRCTC refund take?",
            "What if one passenger is confirmed and others waitlisted?",
            "Give me Tatkal booking hacks",
            "Search trains"
        ]
    },

    "mission_mode": {
        "title": "🛰️ Mission Mode & Live Journey Telemetry",
        "content": """### 🛰️ Mission Mode: Real-Time Railway Telemetry

1. **What is Mission Mode?**
   - **Mission Mode** is an advanced operational dashboard that activates when you start or follow a journey in ARRTS.
   - It upgrades the interface with live telemetry, on-time performance probabilities, platform predictions, and next-action station alerts.

2. **Key Capabilities:**
   - **Next Action Engine:** Advises you in advance (e.g. *"Transfer at Vijayawada Junction in 40 min — switch to Platform 4"*).
   - **Transfer Buffer Monitor:** Continuously recalculates whether your connection remains safe if Train 1 suffers en-route speed restrictions.
   - **Platform Prediction:** Predicts arrival and departure platforms based on historical station traffic.
   - **Punctuality Score:** Real-time percentage odds of arriving on schedule.
""",
        "follow_ups": [
            "How do I activate Mission Mode?",
            "Is my transfer safe on this route?",
            "Issue a Smart General Ticket",
            "Search trains"
        ]
    },

    "smart_ticket": {
        "title": "🎫 Smart General Ticket (Digital UTS Prototype)",
        "content": """### 🎫 Smart General Ticket: Unreserved Digital Prototype

1. **What is the Smart General Ticket?**
   - A next-generation **Unreserved Digital Ticket prototype** inspired by modern transit ticketing.
   - Designed for daily commuters and unreserved (General Second / GS) passengers who need seamless digital ticketing without standing in long station counter queues.

2. **Key Prototype Features:**
   - **Smart Coach & Seat Suggestions:** Analyzes crowd patterns to suggest least-crowded coaches (e.g. `GS-2`, Suggested Seat: `48`).
   - **Dynamic En-route Fallback:** Proposes fallback seats at high-turnover intermediate stations (e.g. `Seat 31 after Vijayawada`).
   - **Offline Verification:** Generates a cryptographically signed UTS token and QR code for ticket examiners (TTE).
   - **Validity Window:** Auto-expires 3 hours after destination arrival or midnight.
""",
        "follow_ups": [
            "How does seat fallback work?",
            "Can I board reserved coaches with a General ticket?",
            "Why is this the best journey?",
            "Search trains"
        ]
    },

    "transfer_safety": {
        "title": "🛡️ Transfer Safety Assessment & Buffer Breakdown",
        "content": """### 🛡️ Transfer Safety Assessment: How ARRTS Validates Connections

1. **The Journey Decision Engine (JDE):**
   - ARRTS uses a strict **Connection Buffer Validator** that automatically filters out unrealistically tight transfers.
   - You can choose from **15m to 60m+** buffer thresholds.

2. **How Transfer Margin is Calculated:**
   - `Total Buffer` = Train 2 Departure − Train 1 Arrival.
   - `Station Transit Time`: ~5 to 10 minutes (platform change, Foot Over Bridge / lift).
   - `Net Delay Tolerance`: `Total Buffer` − `Transit Time`.
   - **Safety Ratings:**
     - **💚 Stable (Safe):** Net margin ≥ 40 minutes (absorbs normal route delays).
     - **⭐ Watch (Moderate):** Net margin 20–40 minutes.
     - **🔴 At Risk / Critical:** Net margin < 20 minutes.
""",
        "follow_ups": [
            "What if I miss my transfer due to train delay?",
            "Why is this the best journey?",
            "Show Tatkal hacks",
            "Search routes"
        ]
    }
}


# ── Chatbot Engine Class ──────────────────────────────────────────────────────

class RailwayChatbot:
    """
    Intelligent Railway AI Assistant that handles:
    - Travel hacks & railway rules questions
    - Real-time train searches via ARRTS engine
    - Proactive conversational guidance and smart follow-up suggestions
    """

    def __init__(self, stops_df: Optional[pd.DataFrame] = None, trains_df: Optional[pd.DataFrame] = None):
        self.stops_df = stops_df
        self.trains_df = trains_df

    def update_data(self, stops_df: pd.DataFrame, trains_df: pd.DataFrame):
        self.stops_df = stops_df
        self.trains_df = trains_df

    def respond(self, message: str, history: Optional[list] = None) -> dict:
        """Process a user message and return a comprehensive structured response."""
        msg = message.strip()
        msg_lower = msg.lower()

        # 1. Check if user is asking for train search or route advice
        search_query = self._detect_search_intent(msg_lower)
        if search_query:
            return self._handle_search_query(search_query, msg)

        # 2. Check for knowledge base / travel hack topic matches
        matched_topic = self._match_knowledge_topic(msg_lower)
        if matched_topic:
            kb = KNOWLEDGE_BASE[matched_topic]
            greeting = self._get_contextual_greeting(msg_lower)
            proactive_prompt = self._get_proactive_prompt(matched_topic)

            full_reply = f"{greeting}{kb['content']}\n\n{proactive_prompt}"
            return {
                "reply": full_reply,
                "topic": matched_topic,
                "suggestions": kb["follow_ups"],
                "train_data": None
            }

        # 3. Check for greeting / general introduction
        if any(w in msg_lower for w in ["hi", "hello", "hey", "namaste", "who are you", "what can you do", "help"]):
            return {
                "reply": (
                    "👋 **Hello! I am ARRTS AI, your specialized Indian Railways Travel & Routing Assistant.**\n\n"
                    "I can help you with:\n"
                    "• 🚄 **Route Planning:** Finding direct and smart connecting trains with buffer safety\n"
                    "• ⚡ **Tatkal Booking Hacks:** Secret timings, payment speedups, and master list tricks\n"
                    "• 📋 **RAC & Waitlist:** Understanding chart prep, current booking discounts, and confirmation odds\n"
                    "• 💺 **Berth Selection:** Tips on booking 1A Coupes, Side Lower window seats, and quiet middle bays\n"
                    "• 🍱 **Pantry & Food:** Mandated MRP caps and IRCTC e-Catering seat delivery\n"
                    "• 🐾 **Pet & Luggage Rules:** How to travel with dogs/cats and baggage limits\n\n"
                    "💡 *Try asking: 'Find trains from Visakhapatnam to Chennai' or 'Give me top Tatkal booking hacks'!*"
                ),
                "topic": "greeting",
                "suggestions": [
                    "🚄 Find trains from Visakhapatnam to Chennai",
                    "⚡ Best Tatkal Booking Hacks",
                    "📋 How does Chart Preparation & RAC work?",
                    "🔀 Connecting Journey & Missed Train rules",
                    "🍱 Food & Pantry Overcharging Hacks"
                ],
                "train_data": None
            }

        # 4. Default fallback with helpful railway guidance and smart inquiry
        return {
            "reply": (
                f"I understand you are asking about: *\"{msg}\"*.\n\n"
                "As your **ARRTS Railway Assistant**, I can assist with journey routing, Tatkal tricks, "
                "berth selection, IRCTC ticket rules, connecting buffers, and travel hacks!\n\n"
                "👉 **Could you clarify what you'd like to do?**\n"
                "1. **Search for a train journey?** (e.g. *\"Find trains from Visakhapatnam to Chennai\"*)\n"
                "2. **Get Tatkal or Waitlist hacks?** (e.g. *\"How to get confirmed Tatkal tickets?\"*)\n"
                "3. **Learn about food, pets, luggage, or refund rules?**"
            ),
            "topic": "general",
            "suggestions": [
                "Find trains from Visakhapatnam to Chennai",
                "Best Tatkal booking tips",
                "How does RAC confirmation work?",
                "What to do if connecting train is missed?"
            ],
            "train_data": None
        }

    # ── Intent Detection & Parsing ────────────────────────────────────────────

    def _detect_search_intent(self, text: str) -> Optional[dict]:
        """Detect if the user is asking to find trains between two stations."""
        patterns = [
            # "trains from X to Y", "find train from X to Y", "between X and Y"
            r"(?:trains?|journey|routes?|travel|go|tickets?|schedule)\s+(?:from|between)\s+([a-zA-Z\s\.\-]+?)\s+(?:to|and)\s+([a-zA-Z\s\.\-]+?)(?:\s+(?:on|date|for|at)\s+([0-9\-\/]+|\btomorrow\b|\btoday\b))?$",
            r"(?:from)\s+([a-zA-Z\s\.\-]+?)\s+(?:to)\s+([a-zA-Z\s\.\-]+?)(?:\s+(?:on|date|for|at)\s+([0-9\-\/]+|\btomorrow\b|\btoday\b))?$",
            r"([a-zA-Z\s\.\-]+?)\s+(?:to|->|→)\s+([a-zA-Z\s\.\-]+?)\s+(?:trains?|journey|routes?)",
        ]

        for p in patterns:
            m = re.search(p, text, re.IGNORECASE)
            if m:
                src = m.group(1).strip()
                dst = m.group(2).strip()

                # Filter out false positive phrases
                forbidden = {"tatkal", "irctc", "rac", "chart", "food", "pantry", "refund", "tdr", "pet", "berth"}
                if src.lower() in forbidden or dst.lower() in forbidden:
                    continue

                # Clean up station names
                src = re.sub(r"^(find|show|list|search|get|tell me|give me)\s+", "", src, flags=re.IGNORECASE).strip()
                dst = re.sub(r"\s+(please|fast|cheap|available|direct|today|tomorrow)$", "", dst, flags=re.IGNORECASE).strip()

                if len(src) >= 2 and len(dst) >= 2:
                    return {"from": src, "to": dst}

        # Check for simple "VSKP to MAS", "Visakhapatnam to Chennai"
        simple_arrow = re.search(r"([a-zA-Z\s]{3,25})\s*(?:to|->|→)\s*([a-zA-Z\s]{3,25})", text, re.IGNORECASE)
        if simple_arrow:
            src = simple_arrow.group(1).strip()
            dst = simple_arrow.group(2).strip()
            forbidden = {"how", "what", "why", "when", "can", "is", "tell", "give"}
            if not any(w in src.lower().split() for w in forbidden):
                return {"from": src, "to": dst}

        return None

    def _handle_search_query(self, query: dict, raw_msg: str) -> dict:
        """Query ARRTS search engine and format conversational result."""
        from_stn = query["from"]
        to_stn = query["to"]
        travel_date = date.today()

        direct_journeys = []
        connecting_journeys = []

        if self.stops_df is not None and self.trains_df is not None and not self.stops_df.empty:
            try:
                from engine.search import find_direct_journeys, find_connecting_journeys
                direct_journeys = find_direct_journeys(from_stn, to_stn, travel_date, self.stops_df, self.trains_df)
                connecting_journeys = find_connecting_journeys(from_stn, to_stn, travel_date, 15, self.stops_df, self.trains_df)
            except Exception as e:
                pass

        total_direct = len(direct_journeys)
        total_conn = len(connecting_journeys)

        if total_direct == 0 and total_conn == 0:
            return {
                "reply": (
                    f"🔍 I searched the railway timetable for journeys from **{from_stn.title()}** to **{to_stn.title()}**, "
                    f"but couldn't find an immediate timetable link with that spelling.\n\n"
                    f"💡 **Helpful Travel Tips:**\n"
                    f"• Try standard station codes (e.g. *VSKP* for Visakhapatnam, *MAS* for Chennai Central, *NDLS* for New Delhi, *HWH* for Howrah).\n"
                    f"• You can also use the main search bar above to see instant autocomplete suggestions!\n\n"
                    f"Would you like me to share travel hacks for booking long-distance trains or finding Tatkal seats?"
                ),
                "topic": "search_not_found",
                "suggestions": [
                    "How to book Tatkal tickets for high-demand routes?",
                    "What are the best connecting hubs in South India?",
                    "How does ARRTS calculate indirect journeys?"
                ],
                "train_data": None
            }

        # Build structured response
        lines = [
            f"### 🚄 ARRTS Journey Search: {from_stn.title()} → {to_stn.title()}",
            f"I found **{total_direct} Direct Train{'s' if total_direct != 1 else ''}** and **{total_conn} Connecting Route{'s' if total_conn != 1 else ''}**.\n"
        ]

        if total_direct > 0:
            lines.append("#### 🟢 Recommended Direct Trains:")
            for j in direct_journeys[:4]:
                s = j["segments"][0]
                lines.append(
                    f"• **Train {s['train_number']} — {s['train_name']}** ({s['train_type']})\n"
                    f"  Departure: **{s['departure']}** from {s['from']} ({s['from_code']}) → Arrival: **{s['arrival']}** at {s['to']} ({s['to_code']})\n"
                    f"  Duration: `{j['total_duration']}` | Health: **{j['journey_health']}** | Confidence: **{j['recommendation_confidence']}**\n"
                )

        if total_conn > 0:
            lines.append("#### 🔀 Top Connecting / Indirect Options:")
            for j in connecting_journeys[:3]:
                s1, s2 = j["segments"]
                lines.append(
                    f"• **Via {j['interchange_station']}** (Total Time: `{j['total_duration']}`)\n"
                    f"  1. 🚂 Train **{s1['train_number']}** ({s1['departure']} → {s1['arrival']})\n"
                    f"  2. ⏱ *Transfer at {j['interchange_station']}: {j['connection_minutes']} mins buffer*\n"
                    f"  3. 🚂 Train **{s2['train_number']}** ({s2['departure']} → {s2['arrival']})\n"
                    f"  Health: **{j['journey_health']}** | Confidence: **{j['recommendation_confidence']}**\n"
                )

        lines.append(
            "\n💡 **Pro Travel Tip:** "
            "If direct trains are full or waitlisted, booking the connecting route via our recommended safe buffer "
            "often gives confirmed berths on both legs without risk of missing connections!"
        )

        return {
            "reply": "\n".join(lines),
            "topic": "search_results",
            "suggestions": [
                f"How to get confirmed seats if {from_stn.title()} to {to_stn.title()} is full?",
                "What is the Tatkal strategy for this route?",
                "Show more connecting options with 30 min buffer",
                "Berth selection tips for overnight journeys"
            ],
            "train_data": {
                "from": from_stn,
                "to": to_stn,
                "direct_count": total_direct,
                "connecting_count": total_conn,
                "top_direct": direct_journeys[:4],
                "top_connecting": connecting_journeys[:3]
            }
        }

    # ── Knowledge Base Matching ───────────────────────────────────────────────

    def _match_knowledge_topic(self, text: str) -> Optional[str]:
        if any(w in text for w in ["tatkal", "tqwl", "premium tatkal", "tatkal time", "tatkal hack", "tatkal trick", "10 am", "11 am"]):
            return "tatkal"
        if any(w in text for w in ["chart", "charting", "chart prep", "rac", "waiting list", "gnwl", "rlwl", "pqwl", "current booking", "confirmation probability"]):
            return "chart_prep"
        if any(w in text for w in ["connecting", "connection", "transfer", "missed", "rule 23", "indirect", "buffer", "change train", "interchange"]):
            return "connecting_hacks"
        if any(w in text for w in ["berth", "seat", "side lower", "side upper", "coupe", "cabin", "lower berth", "senior citizen", "charging", "socket", "window seat"]):
            return "berth_hacks"
        if any(w in text for w in ["food", "pantry", "catering", "meal", "rail neer", "mrp", "overcharge", "overcharging", "dinner", "breakfast", "e-catering"]):
            return "food_hacks"
        if any(w in text for w in ["pet", "dog", "cat", "animal", "luggage", "baggage", "weight", "allowance", "parcel"]):
            return "luggage_pets"
        if any(w in text for w in ["refund", "tdr", "cancel", "cancellation", "late by 3 hours", "ac failure"]):
            return "refunds_tdr"
        if any(w in text for w in ["mission mode", "telemetry", "advanced statistics", "platform prediction", "punctuality"]):
            return "mission_mode"
        if any(w in text for w in ["smart ticket", "general ticket", "unreserved ticket", "digital ticket", "uts", "gs-2", "fallback seat"]):
            return "smart_ticket"
        if any(w in text for w in ["is my transfer safe", "transfer safe", "buffer safe", "jde", "transfer margin", "transfer breakdown"]):
            return "transfer_safety"
        return None

    def _get_contextual_greeting(self, text: str) -> str:
        if "hack" in text or "trick" in text or "tip" in text:
            return "💡 **Here is the expert travel hack you need:**\n\n"
        elif "rule" in text or "policy" in text:
            return "📜 **Official Indian Railways Guidelines & Pro Tips:**\n\n"
        return "🚆 **Here is what you need to know:**\n\n"

    def _get_proactive_prompt(self, topic: str) -> str:
        prompts = {
            "tatkal": "💬 *Are you planning a trip soon? Let me know your origin, destination, and travel date so I can inspect train availability and recommend the best Tatkal strategy!*",
            "chart_prep": "💬 *Do you currently have a waiting list or RAC ticket? Tell me your train number or stations to check alternatives!*",
            "connecting_hacks": "💬 *Need help finding a safe connecting route? Tell me where you are starting and where you want to go!*",
            "berth_hacks": "💬 *Are you traveling solo, with a partner, or with senior citizens? I can advise on the exact berth preferences to select during booking!*",
            "food_hacks": "💬 *Planning an upcoming long train journey? Make sure to download the IRCTC Food on Track app for restaurant food delivered to your seat!*",
            "luggage_pets": "💬 *Are you taking a pet with you? Remember that 1st AC (1A) full Coupe booking is the most comfortable way to travel with your dog or cat!*",
            "refunds_tdr": "💬 *Did your train get delayed or did you face AC issues? Let me know the details so I can guide you on the exact TDR reason code to choose!*",
            "mission_mode": "💬 *Start or follow any journey from the results list to view live telemetry and next-action station alerts!*",
            "smart_ticket": "💬 *You can issue a Smart General Ticket directly from the top bar or inside any journey details panel!*",
            "transfer_safety": "💬 *Would you like me to inspect a specific transfer station like Vijayawada or Rajahmundry?*"
        }
        return prompts.get(topic, "💬 *Feel free to ask any other questions about your train travel!*")
