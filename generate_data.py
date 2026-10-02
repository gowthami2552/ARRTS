"""
generate_data.py — Download NTES timetable data for ARRTS using the ntes-client package.

Uses the ntes-client (pip install ntes-client) which handles the NTES authentication
and returns clean JSON data.

Output:
  data/out/trains.csv
  data/out/stops.csv
  data/out/stations.csv
  data/out/schedules.jsonl

Usage:
  python generate_data.py                    # fetch all seed trains
  python generate_data.py --trains 12841,12842
  python generate_data.py --between VSKP MAS # trains between two stations
"""

import argparse
import csv
import json
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

warnings.filterwarnings("ignore")

# Install check
try:
    from ntes import NTESClient, NTESError
except ImportError:
    print("ERROR: ntes-client not installed. Run: pip install ntes-client")
    sys.exit(1)

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "out"
OUT.mkdir(parents=True, exist_ok=True)

WEEK_DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

TYPE_LABEL = {
    "RAJ": "Rajdhani", "SHT": "Shatabdi", "JSH": "Jan Shatabdi",
    "DRNT": "Duronto", "GBR": "Garib Rath", "TEJ": "Tejas",
    "GT": "Gatimaan", "VNDB": "Vande Bharat", "VNDM": "Vande Bharat Metro",
    "VNDS": "Vande Bharat Sleeper", "SUF": "Superfast", "AMTB": "Amrit Bharat",
    "SKR": "Sampark Kranti", "HUM": "Humsafar", "ANT": "Antyodaya",
    "SUV": "Suvidha", "MEX": "Mail/Express", "EXP": "Express",
    "SPL": "Special", "SUB": "Suburban", "PAS": "Passenger",
    "MEMU": "MEMU", "DEMU": "DEMU", "EMU": "EMU", "": "Express",
}

# Comprehensive list of real train numbers covering key corridors
# Especially the Visakhapatnam ↔ Chennai and surrounding network
SEED_TRAINS = [
    # ── VSKP ↔ Chennai direct trains ──────────────────────────────────────
    "12841",  # Coromandel Express (HWH→MAS, via VSKP)
    "12842",  # Coromandel Express (MAS→HWH, via VSKP)
    "12839",  # Chennai Mail (HWH→MAS via VSKP)
    "12840",  # Chennai Mail (MAS→HWH via VSKP)
    "12849",  # Bilaspur – Visakhapatnam SF
    "12850",
    "17230",  # Seshadri Express VSKP→MAS
    "17229",  # Seshadri Express MAS→VSKP
    "12649",  # Sampark Kranti Express
    "12650",
    "12659",  # Gurudev Express
    "12660",
    "22819",  # Bhubaneswar Rajdhani (via VSKP to MAS)
    "22820",
    "12703",  # Falaknuma Express VSKP→SC
    "12704",  # Falaknuma Express SC→VSKP
    "12737",  # Gowthami Express VSKP→SC
    "12738",  # Gowthami Express SC→VSKP
    "17239",  # Simhapuri Express VSKP→MAS
    "17240",  # Simhapuri Express MAS→VSKP
    "12863",  # Yesvantpur Express (VSKP→YPR)
    "12864",  # Yesvantpur Express (YPR→VSKP)
    "12881",  # Garib Rath (BBS→MAS via VSKP)
    "12882",
    "18501",  # Visakha Express (VSKP→SC)
    "18502",
    "17015",  # Rameswaram Express (VSKP→RMM)
    "17016",
    "17007",  # Simhapuri Express
    "17008",
    "12773",  # Shalimar – Ernakulam Express (via VSKP and MAS)
    "12774",
    "12843",  # Puri – Ahmedabad Express (via VSKP)
    "12844",
    "18189",  # Alleppey–Danapur Express (via VSKP)
    "18190",
    "20815",  # Vande Bharat Express VSKP→MAS
    "20816",
    "17241",  # VSKP–TPTY Express
    "17242",
    "12713",  # Satavahana Express SC→VSKP
    "12714",
    # ── Andhra Pradesh internal / connecting trains ──────────────────────
    "17001",  # Hyderabad–Visakhapatnam Express
    "17002",
    "12727",  # VSKP–SC Intercity Express
    "12728",
    "12805",  # Janmabhoomi Express VSKP→BZA
    "12806",
    "17209",  # Golconda Express SC→VSKP
    "17210",
    "17211",  # Kakinada–Nagarsol Express
    "17212",
    "18047",  # Amaravathi Express
    "18048",
    "22605",  # Villupuram – Chennai Express (branch)
    "22606",
    "12604",  # Hyderabad–Chennai Express
    "12603",
    # ── Chennai ↔ Vijayawada / Hyderabad ─────────────────────────────────
    "12759",  # Charminar Express SC→MAS
    "12760",
    "12031",  # Shatabdi MAS→SC
    "12032",
    "12163",  # Dadar–Chennai Express (via BZA)
    "12164",
    "12269",  # Chennai–Delhi Duronto (via BZA)
    "12270",
    # ── Chennai ↔ Bengaluru ───────────────────────────────────────────────
    "12637",  # Pandian Express MAS→MDU
    "12638",
    "12658",  # Bengaluru Mail MAS→SBC
    "12657",
    "22625",  # KSR Bengaluru Express MAS→SBC
    "22626",
    # ── HWH / Odisha ↔ VSKP (connecting trains) ──────────────────────────
    "12813",  # Steel Express HWH→VSKP
    "12814",
    "12821",  # Dhauli Express HWH→BBS
    "12822",
    "12860",  # Gitanjali Express (via VSKP)
    "12859",
    "22807",  # Santragachi–Tirunelveli AC Express (via VSKP→MAS)
    "22808",
    # ── South India connecting trains ─────────────────────────────────────
    "12671",  # Nilagiri Express MAS→CBE
    "12672",
    "12653",  # Rock Fort Express MAS→TPTY
    "12654",
    "12621",  # Tamil Nadu Express DLI→MAS
    "12622",
    "12623",  # Thiruvananthapuram Mail MAS→TVC
    "12624",
    "16359",  # Patna–Ernakulam Express
    "16360",
    "11027",  # Mumbai–Chennai Mail
    "11028",
    "12601",  # Mangala Express NZM→MAS
    "12602",
    "12773",  # Shalimar–Ernakulam (via MAS)
    "12774",
    # ── Rajdhani / Premium ────────────────────────────────────────────────
    "22221",  # Rajdhani NDLS→MAS
    "22222",
    "12245",  # Duronto Yeshvantpur
    "12246",
    "12083",  # Chennai–Coimbatore Jan Shatabdi
    "12084",
    # ── More Andhra / Telangana trains ───────────────────────────────────
    "17021",  # Tungabhadra Express MAS→GTL
    "17022",
    "17201",  # Golconda Express SC→HYB
    "17202",
    "17301",  # VSKP–Howrah Express
    "17302",
    "12169",  # Sabarmati Express MAS→AII via BZA
    "12170",
    "12723",  # Telangana Express SC→NDLS
    "12724",
    "22833",  # Vivek Express (DBRG→KYQ – long distance, via BZA area)
    "22834",
]


def running_days(sched: dict) -> str:
    """Extract running days from NTES schedule response."""
    dates = sched.get("vStartDateList") or []
    if not dates:
        days_str = (sched.get("DaysOfRun") or "").lower()
        return "Daily" if "daily" in days_str or "all" in days_str else "Unknown"
    seen = set()
    for d in dates:
        d = str(d).strip()
        for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                seen.add(datetime.strptime(d, fmt).weekday())
                break
            except ValueError:
                pass
    if not seen:
        return "Unknown"
    if len(seen) == 7:
        return "Daily"
    return ",".join(WEEK_DAYS[i] for i in sorted(seen))


def parse_station(s: dict, train_no: str, seq: int) -> dict:
    """Parse a station dict from NTES stations list."""
    code = str(s.get("StationCode") or s.get("stationCode") or "").strip().upper()
    name = str(s.get("StationName") or s.get("stationName") or code).strip().title()
    arr = str(s.get("STA") or s.get("scheduledArrival") or s.get("arrival") or "").strip()
    dep = str(s.get("STD") or s.get("scheduledDeparture") or s.get("departure") or "").strip()
    day = int(s.get("Day") or s.get("dayCount") or 0)
    halt = str(s.get("Halt") or s.get("haltTime") or "").strip()
    dist = int(s.get("Distance") or s.get("distance") or 0)

    # Normalize: source has no arrival, destination has no departure
    if not arr or arr in ("-", "--", "Source", "source"):
        arr = dep
    if not dep or dep in ("-", "--", "Destination", "destination"):
        dep = arr

    return {
        "train_no": train_no,
        "seq": seq,
        "station_code": code,
        "station_name": name,
        "day_offset": day - 1 if day >= 1 else 0,  # convert to 0-based
        "arrival": arr,
        "departure": dep,
        "halt": str(halt),
        "distance": dist,
    }


def extract_from_schedule(raw: dict) -> tuple[dict, list] | None:
    """Extract train info and stops from ntes-client schedule response."""
    try:
        train_no = str(raw.get("TrainNumber") or raw.get("trainNumber") or "").strip()
        if not train_no:
            return None

        train_name = str(raw.get("TrainName") or raw.get("trainName") or train_no).strip()
        # Remove Hindi characters by keeping ASCII
        train_name = "".join(c for c in train_name if ord(c) < 128).strip()
        if not train_name:
            train_name = str(raw.get("DestinationName", "")) + " Express"

        train_type_code = str(raw.get("TrainType") or "").strip()
        train_type = TYPE_LABEL.get(train_type_code, "Express")
        days = running_days(raw)

        stations = raw.get("stations") or raw.get("stationList") or []
        if not stations:
            return None

        stops = []
        for i, s in enumerate(stations, 1):
            stop = parse_station(s, train_no, i)
            if stop["station_code"]:
                stops.append(stop)

        if len(stops) < 2:
            return None

        src = stops[0]
        dst = stops[-1]

        train_row = {
            "train_no": train_no,
            "train_name": train_name,
            "train_type": train_type,
            "runs_days": days,
            "source_code": src["station_code"],
            "source_name": src["station_name"],
            "destination_code": dst["station_code"],
            "destination_name": dst["station_name"],
            "distance": dst["distance"],
            "total_stops": len(stops),
        }
        return train_row, stops

    except Exception as e:
        print(f"  [PARSE ERROR] {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate ARRTS timetable data from NTES")
    parser.add_argument("--trains", help="Comma-separated train numbers")
    parser.add_argument("--between", nargs=2, metavar=("FROM", "TO"),
                        help="Fetch trains between two station codes")
    parser.add_argument("--pause", type=float, default=1.0)
    args = parser.parse_args()

    client = NTESClient(timeout=15, retries=2)

    train_numbers = []
    if args.between:
        from_stn, to_stn = args.between
        print(f"Finding trains between {from_stn} and {to_stn}...")
        try:
            result = client.trains_between(from_stn, to_stn)
            if isinstance(result, list):
                for t in result:
                    tn = str(t.get("TrainNumber") or t.get("trainNumber") or "").strip()
                    if tn:
                        train_numbers.append(tn)
            print(f"Found {len(train_numbers)} trains")
        except Exception as e:
            print(f"trains_between error: {e}")

    if args.trains:
        extra = [t.strip() for t in args.trains.split(",") if t.strip()]
        train_numbers.extend(extra)

    if not train_numbers:
        # Deduplicate seed list
        seen = set()
        for t in SEED_TRAINS:
            if t not in seen:
                seen.add(t)
                train_numbers.append(t)

    print(f"\nARRTS Data Generator — fetching {len(train_numbers)} trains from NTES")
    print(f"Output: {OUT}")
    print("-" * 60)

    all_trains = []
    all_stops = []
    all_stations = {}  # code -> name
    success = 0
    failed = 0

    for idx, train_no in enumerate(train_numbers, 1):
        print(f"[{idx}/{len(train_numbers)}] Train {train_no}...", end=" ", flush=True)

        try:
            raw = client.schedule(train_no)
            if not raw:
                print("SKIPPED (no data)")
                failed += 1
                time.sleep(args.pause * 0.5)
                continue
        except NTESError as e:
            print(f"SKIPPED (NTES error: {e})")
            failed += 1
            time.sleep(args.pause * 0.5)
            continue
        except Exception as e:
            print(f"ERROR: {e}")
            failed += 1
            time.sleep(args.pause)
            continue

        result = extract_from_schedule(raw)
        if not result:
            print("SKIPPED (parse failed)")
            failed += 1
            time.sleep(args.pause * 0.3)
            continue

        train_row, stops = result
        all_trains.append(train_row)
        all_stops.extend(stops)
        for s in stops:
            if s["station_code"]:
                all_stations[s["station_code"]] = s["station_name"]

        # Use ASCII-safe printing
        name_safe = train_row['train_name'].encode('ascii', 'replace').decode('ascii')
        print(f"OK - {name_safe} ({len(stops)} stops, {train_row['source_code']}->{train_row['destination_code']})")
        success += 1
        time.sleep(args.pause)

    print("-" * 60)
    print(f"Result: {success} trains, {failed} failed, {len(all_stops)} stops, {len(all_stations)} stations")

    if success == 0:
        print("\n[ERROR] No trains fetched successfully.")
        print("Possible causes:")
        print("  1. NTES service may be temporarily unavailable")
        print("  2. Network connectivity issues")
        print("  3. Try running again later or with specific train numbers")
        sys.exit(1)

    # Write trains.csv
    trains_path = OUT / "trains.csv"
    with open(trains_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "train_no", "train_name", "train_type", "runs_days",
            "source_code", "source_name", "destination_code", "destination_name",
            "distance", "total_stops"
        ])
        w.writeheader()
        w.writerows(all_trains)
    print(f"Written: {trains_path}")

    # Write stops.csv
    stops_path = OUT / "stops.csv"
    with open(stops_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "train_no", "seq", "station_code", "station_name",
            "day_offset", "arrival", "departure", "halt", "distance"
        ])
        w.writeheader()
        w.writerows(all_stops)
    print(f"Written: {stops_path}")

    # Write stations.csv
    stations_path = OUT / "stations.csv"
    with open(stations_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["code", "name", "lat", "lon"])
        w.writeheader()
        for code, name in sorted(all_stations.items()):
            w.writerow({"code": code, "name": name, "lat": "", "lon": ""})
    print(f"Written: {stations_path}")

    # Write schedules.jsonl
    sched_path = OUT / "schedules.jsonl"
    with open(sched_path, "w", encoding="utf-8") as f:
        for t in all_trains:
            train_stops = [s for s in all_stops if s["train_no"] == t["train_no"]]
            record = {**t, "stops": train_stops}
            f.write(json.dumps(record, ensure_ascii=True) + "\n")
    print(f"Written: {sched_path}")

    print(f"\n✓ Data generation complete! {success} trains ready for ARRTS.")
    print(f"  Key stations in database: {', '.join(sorted(all_stations.keys())[:20])}...")


if __name__ == "__main__":
    main()
