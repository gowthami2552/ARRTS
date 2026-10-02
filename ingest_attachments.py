"""
ingest_attachments.py — Integrate uploaded stations JSON and trains CSV into ARRTS.

This script reads:
1. media_1790691134170.json (4,598 stations)
2. media_1790691134199.csv (5,207 trains)

And merges them into:
- data/out/stations.csv
- data/out/trains.csv
- data/out/stops.csv
- data/out/schedules.jsonl
Preserving all existing detailed NTES stop sequences.
"""

import csv
import json
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "out"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MEDIA_DIR = Path("C:/Users/gowthami/.gemini/antigravity/brain/957edd73-0131-4ff7-b7f6-88e42dfa8730/.user_uploaded")
STATIONS_JSON = MEDIA_DIR / "media_1790691134170.json"
TRAINS_CSV = MEDIA_DIR / "media_1790691134199.csv"

# Known GPS coordinates for major Indian stations
KNOWN_COORDS = {
    "VSKP": (17.6868, 83.2185), "BBS": (20.2961, 85.8245), "BBSN": (20.2961, 85.8245),
    "RJY": (17.0005, 81.8040), "BZA": (16.5193, 80.6305), "GNT": (16.3008, 80.4428),
    "NLR": (14.4426, 79.9865), "OGL": (15.4909, 80.0540), "COA": (16.9424, 82.2350),
    "CCT": (16.9424, 82.2350), "SMVB": (13.0067, 77.5667), "SBC": (12.9766, 77.5713),
    "YPR": (13.0067, 77.5667), "TPTY": (13.6288, 79.4192), "RU": (14.1663, 79.9864),
    "LPI": (17.6868, 83.2185), "BAM": (19.3150, 84.7941), "TDD": (16.8120, 81.5269),
    "MAS": (13.0827, 80.2707), "MS": (13.0797, 80.2609), "MSB": (13.0846, 80.2746),
    "TBM": (12.9249, 80.1291), "HWH": (22.5839, 88.3427), "SDAH": (22.5726, 88.3693),
    "SHM": (22.5621, 88.4291), "SC": (17.4375, 78.4980), "HYB": (17.3850, 78.4867),
    "KCG": (17.3646, 78.4708), "PURI": (19.8116, 85.8346), "CTC": (20.4625, 85.8830),
    "CSTM": (18.9400, 72.8358), "CSMT": (18.9400, 72.8358), "LTT": (19.0760, 72.9051),
    "BSR": (19.3838, 72.8336), "BDTS": (19.0544, 72.8406), "PUNE": (18.5284, 73.8744),
    "DD": (18.4632, 74.5828), "NGP": (21.1524, 79.0888), "BPL": (23.2599, 77.4126),
    "MDU": (9.9252, 78.1198), "CBE": (11.0168, 76.9558), "TPJ": (10.8050, 78.6856),
    "ED": (11.3410, 77.7172), "SA": (11.6643, 78.1460), "ERS": (9.9674, 76.2999),
    "TVC": (8.5241, 76.9366), "MAQ": (12.8698, 74.8432), "UBL": (15.3647, 75.1240),
    "MYS": (12.3168, 76.6433), "NDLS": (28.6428, 77.2197), "NZM": (28.5965, 77.2449),
    "DLI": (28.6562, 77.2410), "PNBE": (25.5941, 85.1376), "BSB": (25.3176, 82.9739),
    "LKO": (26.8467, 80.9462), "LJN": (26.8467, 80.9462), "ADI": (23.0225, 72.5714),
    "ST": (21.1702, 72.8311), "GKP": (26.7606, 83.3732), "JAT": (32.7060, 74.8770),
    "ASR": (31.6340, 74.8723), "KIR": (25.5540, 87.5710), "GHY": (26.1806, 91.7539),
    "DHN": (23.7957, 86.4304), "TATA": (22.7840, 86.1834), "ROU": (22.2593, 84.8828),
    "BSP": (22.0797, 82.1409), "R": (21.2514, 81.6296), "DURG": (21.1904, 81.2849),
    "JBP": (23.1815, 79.9864), "GWL": (26.2183, 78.1828), "AGC": (27.1584, 78.0081),
    "AF": (27.1815, 78.0165), "CNB": (26.4547, 80.3507), "ALD": (25.4358, 81.8463),
    "MGS": (25.2796, 83.1203), "DDU": (25.2796, 83.1203), "BKN": (28.0229, 73.3119),
    "JU": (26.2867, 73.0289), "JP": (26.9196, 75.7878), "AII": (26.4499, 74.6399),
}

# Aliases for mapping common station names in trains CSV to station codes
CUSTOM_NAME_TO_CODE = {
    "MUMBAI CST": "CSTM",
    "MUMBAI CENTRAL": "BCT",
    "MUMBAI DADAR CENTRAL": "DR",
    "MUMBAI DADAR WEST": "DDR",
    "MUMBAI BANDRA TERMINUS": "BDTS",
    "LOKMANYA TILAK TERM": "LTT",
    "CHENNAI CENTRAL": "MAS",
    "CHENNAI EGMORE": "MS",
    "CHENNAI BEACH": "MSB",
    "TAMBARAM": "TBM",
    "NEW DELHI": "NDLS",
    "OLD DELHI": "DLI",
    "DELHI H NIZAMUDDIN": "NZM",
    "DELHI SARAI ROHILLA": "DEE",
    "DELHI ANAND VIHAR": "ANVT",
    "ANAND VIHAR TRM": "ANVT",
    "HOWRAH JN": "HWH",
    "KOLKATA SEALDAH": "SDAH",
    "KOLKATA CHITPUR": "KOAA",
    "KOLKATA SHALIMAR": "SHM",
    "SANTRAGACHI JN": "SRC",
    "BANGALORE CITY JN": "SBC",
    "BANGALORE CANT": "BNC",
    "YESVANTPUR JN": "YPR",
    "SMVT BENGALURU": "SMVB",
    "PUNE JN": "PUNE",
    "HYDERABAD DECCAN": "HYB",
    "SECUNDERABAD JN": "SC",
    "KACHEGUDA": "KCG",
    "KACHEGUDA FALAKNUMA": "FM",
    "AHMEDABAD JN": "ADI",
    "GANDHIDHAM BG": "GIMB",
    "BHUJ": "BHUJ",
    "SURAT": "ST",
    "VADODARA JN": "BRC",
    "BHOPAL JN": "BPL",
    "HABIBGANJ": "HBJ",
    "JABALPUR": "JBP",
    "GWALIOR JN": "GWL",
    "AGRA CANTT": "AGC",
    "AGRA FORT": "AF",
    "KANPUR CENTRAL": "CNB",
    "LUCKNOW": "LKO",
    "LUCKNOW JN": "LJN",
    "VARANASI JN": "BSB",
    "MUGHAL SARAI JN": "MGS",
    "ALLAHABAD JN": "ALD",
    "PATNA JN": "PNBE",
    "RAJENDRA NAGAR BIHAR": "RJPB",
    "DANAPUR": "DNR",
    "GAYA JN": "GAYA",
    "JAMMU TAWI": "JAT",
    "UDHAMPUR": "UHP",
    "S M V D KATRA": "SVDK",
    "AMRITSAR JN": "ASR",
    "CHANDIGARH": "CDG",
    "KALKA": "KLK",
    "DEHRADUN": "DDN",
    "HARIDWAR JN": "HW",
    "KATHGODAM": "KGM",
    "JAIPUR": "JP",
    "JODHPUR JN": "JU",
    "AJMER JN": "AII",
    "BIKANER JN": "BKN",
    "UDAIPUR CITY": "UDZ",
    "KOTA JN": "KOTA",
    "VISHAKAPATNAM": "VSKP",
    "VISAKHAPATNAM": "VSKP",
    "VIJAYAWADA JN": "BZA",
    "GUNTUR JN": "GNT",
    "TIRUPATI MAIN": "TPTY",
    "BHUBANESWAR": "BBS",
    "PURI": "PURI",
    "CUTTACK": "CTC",
    "ROURKELA": "ROU",
    "TATANAGAR JN": "TATA",
    "RANCHI": "RNC",
    "HATIA": "HTE",
    "DHANBAD JN": "DHN",
    "ASANSOL JN": "ASN",
    "GUWAHATI": "GHY",
    "KAMAKHYA": "KYQ",
    "DIBRUGARH": "DBRG",
    "DIBRUGARH TOWN": "DBRT",
    "COIMBATORE JN": "CBE",
    "MADURAI JN": "MDU",
    "TIRUCHIRAPPALLI": "TPJ",
    "TIRUNELVELI": "TEN",
    "KANYAKUMARI": "CAPE",
    "ERNAKULAM JN": "ERS",
    "TRIVANDRUM CENTRAL": "TVC",
    "KOCHUVELI": "KCVL",
    "KOLLAM JN": "QLN",
    "MANGALORE CNTL": "MAQ",
    "MANGALORE JN": "MAJN",
    "HUBLI JN": "UBL",
    "MYSORE JN": "MYS",
    "SOLAPUR JN": "SUR",
    "C SHAHU M RAJ KOLHAPUR TERM": "KOP",
    "NAGPUR": "NGP",
    "ITWARI": "ITR",
    "RAIPUR JN": "R",
    "BILASPUR JN": "BSP",
    "DURG": "DURG",
    "BHUSAVAL JN": "BSL",
    "MANMAD JN": "MMR",
    "SAINAGAR SHIRDI": "SNSI",
}


def normalize_name(name: str) -> str:
    if not name:
        return ""
    n = name.upper().strip()
    n = re.sub(r"\b(JN|JUNCTION|TERMINUS|TERMINAL|TERM|CENTRAL|CNTL|CITY|CST|CSTM|T|BG|MG|SUBURBAN)\b", "", n)
    n = re.sub(r"[^A-Z0-9 ]", "", n).strip()
    return re.sub(r"\s+", " ", n)


def load_stations_map():
    """Load all stations from media_1790691134170.json and existing stations.csv."""
    name_to_code = {}
    code_to_name = {}
    code_to_coords = dict(KNOWN_COORDS)

    # 1. Existing stations.csv
    existing_stations_file = DATA_DIR / "stations.csv"
    if existing_stations_file.exists():
        with open(existing_stations_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                c = row["code"].strip().upper()
                n = row["name"].strip()
                code_to_name[c] = n
                name_to_code[n.upper()] = c
                if row.get("lat") and row.get("lon"):
                    try:
                        code_to_coords[c] = (float(row["lat"]), float(row["lon"]))
                    except ValueError:
                        pass

    # 2. Uploaded JSON stations
    if STATIONS_JSON.exists():
        with open(STATIONS_JSON, "r", encoding="utf-8") as f:
            data = json.load(f)
            for stn in data.get("stations", []):
                c = stn["stnCode"].strip().upper()
                n = stn["stnName"].strip()
                city = stn.get("stnCity", "").strip()
                if c not in code_to_name:
                    code_to_name[c] = n
                name_to_code[n.upper()] = c
                if city and city.upper() not in name_to_code:
                    name_to_code[city.upper()] = c

    # Add custom name mappings
    for k, v in CUSTOM_NAME_TO_CODE.items():
        name_to_code[k.upper()] = v
        if v not in code_to_name:
            code_to_name[v] = k.title()

    # Pre-build normalized lookup
    norm_to_code = {}
    for n, c in name_to_code.items():
        norm = normalize_name(n)
        if norm and norm not in norm_to_code:
            norm_to_code[norm] = c

    return name_to_code, norm_to_code, code_to_name, code_to_coords


def resolve_station(name: str, name_to_code: dict, norm_to_code: dict, code_to_name: dict) -> tuple[str, str]:
    """Resolve raw station name string to (code, proper_name)."""
    if not name:
        return "UNK", "Unknown"

    raw = name.strip()
    raw_upper = raw.upper()

    # Check direct code (if someone passed 3-4 letter code directly)
    if raw_upper in code_to_name:
        return raw_upper, code_to_name[raw_upper]

    # Check direct name
    if raw_upper in name_to_code:
        c = name_to_code[raw_upper]
        return c, code_to_name.get(c, raw.title())

    # Check normalized name
    norm = normalize_name(raw_upper)
    if norm in norm_to_code:
        c = norm_to_code[norm]
        return c, code_to_name.get(c, raw.title())

    # Partial / word boundary match
    for known_norm, c in norm_to_code.items():
        if len(known_norm) >= 4 and (known_norm in norm or norm in known_norm):
            return c, code_to_name.get(c, raw.title())

    # Fallback: create a deterministic 3-5 character code
    clean = re.sub(r"[^A-Z0-9]", "", norm)
    gen_code = clean[:5] if len(clean) >= 3 else (raw_upper[:4] if len(raw_upper) >= 3 else "STN")
    code_to_name[gen_code] = raw.title()
    name_to_code[raw_upper] = gen_code
    return gen_code, raw.title()


def parse_time_str(t: str) -> str:
    """Normalize time string to HH:MM format."""
    if not t or str(t).lower() in ("nan", "none", ""):
        return "00:00"
    m = re.search(r"(\d{1,2}):(\d{2})", str(t))
    if m:
        return f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
    return "00:00"


def parse_day_offset(total_time_str: str, dep_time: str, arr_time: str) -> int:
    """Determine arrival day offset (0 for same day, 1 for next day, etc.)."""
    if total_time_str and "days" in str(total_time_str):
        m = re.search(r"(\d+)\s*days", str(total_time_str))
        if m:
            return int(m.group(1))

    # Fallback to dep/arr comparison
    dep_m = int(dep_time.split(":")[0]) * 60 + int(dep_time.split(":")[1])
    arr_m = int(arr_time.split(":")[0]) * 60 + int(arr_time.split(":")[1])
    if arr_m < dep_m:
        return 1
    return 0


def main():
    print("=" * 60)
    print("ARRTS Dataset Ingestion: Stations JSON + Trains CSV")
    print("=" * 60)

    name_to_code, norm_to_code, code_to_name, code_to_coords = load_stations_map()
    print(f"Loaded {len(code_to_name)} distinct stations in catalog.")

    # 1. Existing data
    existing_trains_path = DATA_DIR / "trains.csv"
    existing_stops_path = DATA_DIR / "stops.csv"

    existing_train_nos = set()
    existing_trains = []
    if existing_trains_path.exists():
        with open(existing_trains_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_trains.append(row)
                existing_train_nos.add(str(row["train_no"]).strip())

    existing_stops = []
    if existing_stops_path.exists():
        with open(existing_stops_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing_stops.append(row)

    print(f"Existing detailed NTES trains: {len(existing_trains)}, stops: {len(existing_stops)}")

    # 2. Process uploaded trains CSV
    new_trains = []
    new_stops = []
    added_count = 0

    if TRAINS_CSV.exists():
        print(f"Reading uploaded trains from {TRAINS_CSV}...")
        trains_df = pd.read_csv(TRAINS_CSV)

        for _, row in trains_df.iterrows():
            train_no = str(row.get("train_number", "")).strip()
            # remove decimal suffix if any, e.g. 12841.0
            if train_no.endswith(".0"):
                train_no = train_no[:-2]

            if not train_no or train_no in existing_train_nos:
                continue

            train_name = str(row.get("train_name", "")).strip()
            if not train_name or train_name.lower() == "nan":
                train_name = f"Train {train_no}"

            src_raw = str(row.get("source", "")).strip()
            dst_raw = str(row.get("destination", "")).strip()

            if not src_raw or not dst_raw or src_raw.lower() == "nan" or dst_raw.lower() == "nan":
                continue

            src_code, src_name = resolve_station(src_raw, name_to_code, norm_to_code, code_to_name)
            dst_code, dst_name = resolve_station(dst_raw, name_to_code, norm_to_code, code_to_name)

            if src_code == dst_code:
                continue

            dep_time = parse_time_str(row.get("departure"))
            arr_time = parse_time_str(row.get("arrival"))
            total_time = str(row.get("total_time", ""))
            day_offset = parse_day_offset(total_time, dep_time, arr_time)

            distance = row.get("distance", 0)
            try:
                distance = int(float(distance))
            except (ValueError, TypeError):
                distance = 0

            # Infer train type from name
            nm_upper = train_name.upper()
            if "RAJDHANI" in nm_upper:
                ttype = "Rajdhani"
            elif "SHATABDI" in nm_upper or "JAN SHATABDI" in nm_upper:
                ttype = "Shatabdi"
            elif "DURONTO" in nm_upper:
                ttype = "Duronto"
            elif "GARIB RATH" in nm_upper:
                ttype = "Garib Rath"
            elif "SUPERFAST" in nm_upper or " SF " in nm_upper or nm_upper.endswith(" SF"):
                ttype = "Superfast"
            elif "MAIL" in nm_upper:
                ttype = "Mail"
            elif "PASSENGER" in nm_upper or "PASS" in nm_upper or "LOCAL" in nm_upper or "EMU" in nm_upper:
                ttype = "Passenger"
            else:
                ttype = "Express"

            train_row = {
                "train_no": train_no,
                "train_name": train_name,
                "train_type": ttype,
                "runs_days": "Daily",
                "source_code": src_code,
                "source_name": src_name,
                "destination_code": dst_code,
                "destination_name": dst_name,
                "distance": distance,
                "total_stops": 2,
            }
            new_trains.append(train_row)
            existing_train_nos.add(train_no)

            # Generate origin and destination stops
            stop_orig = {
                "train_no": train_no,
                "seq": 1,
                "station_code": src_code,
                "station_name": src_name,
                "day_offset": 0,
                "arrival": dep_time,
                "departure": dep_time,
                "halt": "",
                "distance": 0,
            }
            stop_dest = {
                "train_no": train_no,
                "seq": 2,
                "station_code": dst_code,
                "station_name": dst_name,
                "day_offset": day_offset,
                "arrival": arr_time,
                "departure": arr_time,
                "halt": "",
                "distance": distance,
            }
            new_stops.extend([stop_orig, stop_dest])
            added_count += 1

    print(f"Successfully processed {added_count} new trains from CSV.")

    # 3. Combine and write out
    all_trains = existing_trains + new_trains
    all_stops = existing_stops + new_stops

    print(f"Total Trains: {len(all_trains)}")
    print(f"Total Stops: {len(all_stops)}")

    # Write trains.csv
    trains_file = DATA_DIR / "trains.csv"
    with open(trains_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "train_no", "train_name", "train_type", "runs_days",
            "source_code", "source_name", "destination_code", "destination_name",
            "distance", "total_stops"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_trains)
    print(f"Saved: {trains_file}")

    # Write stops.csv
    stops_file = DATA_DIR / "stops.csv"
    with open(stops_file, "w", newline="", encoding="utf-8") as f:
        fieldnames = [
            "train_no", "seq", "station_code", "station_name",
            "day_offset", "arrival", "departure", "halt", "distance"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_stops)
    print(f"Saved: {stops_file}")

    # Write stations.csv (including all 4,598 stations from JSON + any newly encountered)
    stations_file = DATA_DIR / "stations.csv"
    station_rows = []
    for code, name in sorted(code_to_name.items()):
        coords = code_to_coords.get(code)
        lat = coords[0] if coords else ""
        lon = coords[1] if coords else ""
        station_rows.append({"code": code, "name": name, "lat": lat, "lon": lon})

    with open(stations_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "lat", "lon"])
        writer.writeheader()
        writer.writerows(station_rows)
    print(f"Saved: {stations_file} ({len(station_rows)} stations)")

    # Write schedules.jsonl
    sched_file = DATA_DIR / "schedules.jsonl"
    stops_by_train = {}
    for s in all_stops:
        stops_by_train.setdefault(s["train_no"], []).append(s)

    with open(sched_file, "w", encoding="utf-8") as f:
        for t in all_trains:
            rec = {**t, "stops": stops_by_train.get(t["train_no"], [])}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Saved: {sched_file}")

    print("\n✓ Attachment Ingestion Complete!")


if __name__ == "__main__":
    main()
