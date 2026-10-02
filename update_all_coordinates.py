"""
update_all_coordinates.py — Populate accurate GPS coordinates for all stations in ARRTS
using the authoritative 8,697+ Indian Railways stations dataset.
"""

import csv
import json
import urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
STATIONS_CSV = ROOT / "data" / "out" / "stations.csv"

# Pre-defined known coordinates for major hubs & custom abbreviations
MANUAL_COORDS = {
    "VSKP": (17.7215, 83.2870), "BBS": (20.2666, 85.8436), "BBSN": (20.3547, 85.8174),
    "RJY": (17.0005, 81.7770), "BZA": (16.5175, 80.6200), "GNT": (16.2952, 80.4414),
    "NLR": (14.4426, 79.9865), "OGL": (15.4909, 80.0540), "COA": (16.9424, 82.2350),
    "CCT": (16.9840, 82.2472), "SMVB": (13.0036, 77.6534), "SBC": (12.9778, 77.5707),
    "YPR": (13.0238, 77.5503), "BNC": (12.9930, 77.5980), "TPTY": (13.6288, 79.4192),
    "RU": (13.6366, 79.5161), "LPI": (17.4870, 78.3245), "BAM": (19.3150, 84.7941),
    "TDD": (16.8120, 81.5269), "MAS": (13.0827, 80.2757), "MS": (13.0797, 80.2609),
    "MSB": (13.0906, 80.2917), "TBM": (12.9249, 80.1291), "HWH": (22.5839, 88.3427),
    "SDAH": (22.5697, 88.3713), "SHM": (22.5562, 88.3188), "SRC": (22.5816, 88.2778),
    "SC": (17.4344, 78.5017), "HYB": (17.3927, 78.4682), "KCG": (17.3878, 78.4975),
    "PURI": (19.8116, 85.8346), "CTC": (20.4625, 85.8830), "CSTM": (18.9400, 72.8358),
    "CSMT": (18.9400, 72.8358), "LTT": (19.0700, 72.8906), "BCT": (18.9696, 72.8194),
    "BSR": (19.3838, 72.8336), "BDTS": (19.0544, 72.8406), "DR": (19.0178, 72.8478),
    "DDR": (19.0185, 72.8433), "PUNE": (18.5284, 73.8744), "DD": (18.4632, 74.5828),
    "NGP": (21.1524, 79.0888), "ITR": (21.1610, 79.1170), "BPL": (23.2599, 77.4126),
    "HBJ": (23.2086, 77.4367), "MDU": (9.9252, 78.1198), "CBE": (11.0016, 76.9667),
    "TPJ": (10.7938, 78.6837), "ED": (11.3410, 77.7172), "SA": (11.6643, 78.1460),
    "ERS": (9.9674, 76.2999), "TVC": (8.4875, 76.9525), "KCVL": (8.5130, 76.9038),
    "QLN": (8.8879, 76.5956), "MAQ": (12.8642, 74.8427), "MAJN": (12.8698, 74.8722),
    "UBL": (15.3444, 75.1489), "MYS": (12.3168, 76.6433), "NDLS": (28.6428, 77.2197),
    "NZM": (28.5888, 77.2536), "DLI": (28.6562, 77.2410), "DEE": (28.6669, 77.1818),
    "ANVT": (28.6508, 77.3152), "PNBE": (25.6022, 85.1376), "RJPB": (25.5997, 85.1619),
    "DNR": (25.6267, 85.0442), "BSB": (25.3268, 82.9863), "LKO": (26.8322, 80.9238),
    "LJN": (26.8300, 80.9200), "ADI": (23.0225, 72.5714), "ST": (21.2049, 72.8406),
    "BRC": (22.3107, 73.1812), "GKP": (26.7588, 83.3820), "JAT": (32.7060, 74.8770),
    "UHP": (32.9262, 75.1322), "SVDK": (32.9917, 74.9317), "ASR": (31.6340, 74.8723),
    "CDG": (30.7046, 76.8013), "KLK": (30.8354, 76.9348), "DDN": (30.3165, 78.0322),
    "HW": (29.9457, 78.1642), "KGM": (29.2736, 79.5447), "KIR": (25.5540, 87.5710),
    "GHY": (26.1806, 91.7539), "KYQ": (26.1558, 91.7062), "DBRG": (27.4728, 94.9120),
    "DBRT": (27.4870, 94.9200), "DHN": (23.7957, 86.4304), "TATA": (22.7840, 86.1834),
    "ROU": (22.2593, 84.8828), "BSP": (22.0797, 82.1409), "R": (21.2514, 81.6296),
    "DURG": (21.1904, 81.2849), "JBP": (23.1815, 79.9864), "GWL": (26.2183, 78.1828),
    "AGC": (27.1584, 78.0081), "AF": (27.1815, 78.0165), "CNB": (26.4547, 80.3507),
    "ALD": (25.4358, 81.8463), "MGS": (25.2796, 83.1203), "DDU": (25.2796, 83.1203),
    "BKN": (28.0229, 73.3119), "JU": (26.2867, 73.0289), "JP": (26.9196, 75.7878),
    "AII": (26.4499, 74.6399), "KOP": (16.6956, 74.2317), "SUR": (17.6599, 75.9064),
    "BSL": (21.0500, 75.7833), "MMR": (20.2500, 74.4500), "SNSI": (19.7645, 74.4762),
    "GIMB": (23.0753, 70.1337), "BHUJ": (23.2420, 69.6669), "UDZ": (24.5854, 73.7125),
    "KOTA": (25.1800, 75.8300), "RNC": (23.3441, 85.3096), "HTE": (23.3089, 85.3167),
    "ASN": (23.6889, 86.9661), "TEN": (8.7139, 77.7567), "CAPE": (8.0883, 77.5385),
    # Additional key route junctions:
    "KGP": (22.3382, 87.3205), "BLS": (21.5035, 86.9264), "BHC": (21.0543, 86.4957),
    "JJKR": (20.9507, 86.1367), "PSA": (18.7719, 84.4172), "CHE": (18.2949, 83.8967),
    "AKP": (17.6896, 83.0034), "TUNI": (17.3547, 82.5487), "SLO": (17.0500, 82.1667),
    "NDD": (16.9067, 81.6667), "TEL": (16.2430, 80.6400), "BPP": (15.9042, 80.4682),
    "CLX": (15.8246, 80.3522), "KPD": (12.9698, 79.1325), "AJJ": (13.0827, 79.6677),
    "VGLJ": (25.4484, 78.5685), "CPSN": (19.8762, 75.3433), "HUZUR": (19.1528, 77.3195),
    "SHIML": (31.1048, 77.1734), "BOLPU": (23.6693, 87.6934), "RAXAU": (26.9786, 84.8504),
    "DIGHA": (21.6266, 87.5113), "METTU": (11.3013, 76.9427), "BERHA": (24.1042, 88.2515),
    "BARBI": (22.1220, 85.3940), "MANDA": (24.7800, 87.0300), "BAPUD": (26.6500, 84.9167),
    "ANUPG": (29.1900, 73.2100), "BAIJN": (32.0500, 76.6500), "DEVAN": (13.2500, 77.7100),
    "MANCH": (18.8700, 79.4600), "LFG": (25.1800, 93.0200)
}


def main():
    print("=" * 60)
    print("Updating All ARRTS Stations with Precise GPS Coordinates")
    print("=" * 60)

    # 1. Fetch datameet 8,697 stations
    datameet_url = "https://raw.githubusercontent.com/datameet/railways/master/stations.json"
    print(f"Fetching station coordinates from {datameet_url}...")
    coords_dict = dict(MANUAL_COORDS)

    try:
        req = urllib.request.Request(datameet_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8"))
            for f in data.get("features", []):
                props = f.get("properties", {})
                code = props.get("code", "").strip().upper()
                geom = f.get("geometry")
                if geom and "coordinates" in geom:
                    coords = geom["coordinates"]
                    if len(coords) == 2 and coords[0] and coords[1]:
                        lon, lat = coords[0], coords[1]
                        # Don't overwrite our manual high-precision overrides
                        if code not in coords_dict:
                            coords_dict[code] = (round(lat, 5), round(lon, 5))
        print(f"Successfully loaded {len(coords_dict)} station coordinates.")
    except Exception as e:
        print(f"Failed to fetch remote coordinates: {e}")
        print("Using local manual coordinates.")

    # 2. Update stations.csv
    if not STATIONS_CSV.exists():
        print(f"File not found: {STATIONS_CSV}")
        return

    stns_df = pd.read_csv(STATIONS_CSV, dtype=str)
    updated_count = 0
    new_rows = []

    for _, row in stns_df.iterrows():
        code = str(row["code"]).strip().upper()
        name = str(row["name"]).strip()
        existing_lat = str(row.get("lat", "")).strip()
        existing_lon = str(row.get("lon", "")).strip()

        if code in coords_dict:
            lat, lon = coords_dict[code]
            new_rows.append({"code": code, "name": name, "lat": lat, "lon": lon})
            updated_count += 1
        elif existing_lat and existing_lon:
            new_rows.append({"code": code, "name": name, "lat": existing_lat, "lon": existing_lon})
            updated_count += 1
        else:
            new_rows.append({"code": code, "name": name, "lat": "", "lon": ""})

    out_df = pd.DataFrame(new_rows)
    out_df.to_csv(STATIONS_CSV, index=False)
    print(f"Updated {STATIONS_CSV}")
    print(f"Total Stations: {len(out_df)}, Stations with Coordinates: {updated_count} ({updated_count*100//len(out_df)}%)")

    # 3. Export a fast JSON coordinate map for client caching
    json_path = ROOT / "data" / "out" / "station_coords.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(coords_dict, f)
    print(f"Saved fast coordinate cache to {json_path}")


if __name__ == "__main__":
    main()
