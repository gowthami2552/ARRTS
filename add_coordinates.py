"""
add_coordinates.py — Add known coordinates to stations.csv.

Adds lat/lon for major Indian railway stations to enable map display.
These are approximate coordinates of the main station areas.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STATIONS_CSV = ROOT / "data" / "out" / "stations.csv"

# Known station coordinates (approximate)
KNOWN_COORDS = {
    # East Coast / AP
    "VSKP": (17.6868, 83.2185),  # Visakhapatnam
    "BBS": (20.2961, 85.8245),   # Bhubaneswar
    "BBSN": (20.2961, 85.8245),
    "RJY": (17.0005, 81.8040),   # Rajahmundry
    "BZA": (16.5193, 80.6305),   # Vijayawada
    "GNT": (16.3008, 80.4428),   # Guntur
    "NLR": (14.4426, 79.9865),   # Nellore
    "OGL": (15.4909, 80.0540),   # Ongole
    "COA": (16.9424, 82.2350),   # Kakinada
    "SMVB": (13.0067, 77.5667),  # Bangalore Yeshvantpur
    "SBC": (12.9766, 77.5713),   # Bangalore City
    "YPR": (13.0067, 77.5667),
    "TPTY": (13.6288, 79.4192),  # Tirupati
    "RU": (14.1663, 79.9864),
    "RJY": (17.0005, 81.8040),
    "LPI": (17.6868, 83.2185),   # Waltair (Visakhapatnam)
    "BAM": (14.5204, 79.1286),   # Bapatla
    "TDD": (16.4839, 80.6306),
    # Chennai
    "MAS": (13.0827, 80.2707),   # Chennai Central
    "MS": (13.0797, 80.2609),    # Chennai Egmore
    "MSB": (13.0846, 80.2746),   # Chennai Beach
    "TBM": (12.9249, 80.1291),   # Tambaram
    # HWH / Kolkata
    "HWH": (22.5839, 88.3427),   # Howrah
    "SDAH": (22.5726, 88.3693),  # Sealdah
    "SHM": (22.5621, 88.4291),   # Shalimar
    # Hyderabad
    "SC": (17.4375, 78.4980),    # Secunderabad
    "HYB": (17.3850, 78.4867),   # Hyderabad
    "KCG": (17.3646, 78.4708),   # Kacheguda
    "NED": (18.0781, 75.5497),   # Nanded
    "CHZ": (17.4375, 78.4980),   # Cherlapally
    # Odisha
    "PURI": (19.8116, 85.8346),  # Puri
    "CTC": (20.4625, 85.8830),   # Cuttack
    # Maharashtra
    "CSTM": (18.9400, 72.8358),  # Mumbai CST
    "LTT": (19.0760, 72.9051),   # Mumbai LTT
    "DD": (18.5204, 73.8567),    # Pune
    "NGP": (21.0913, 79.1152),   # Nagpur
    "BPL": (23.2599, 77.4126),   # Bhopal
    # Tamil Nadu
    "MDU": (9.9252, 78.1198),    # Madurai
    "CBE": (11.0168, 76.9558),   # Coimbatore
    "TPJ": (10.8050, 78.6856),   # Trichy
    "ED": (11.5410, 77.6884),    # Erode
    "SA": (11.6643, 78.1460),    # Salem
    "VM": (11.9401, 79.4861),    # Villupuram
    "PLNI": (10.5277, 77.5249),  # Palani
    # Kerala
    "ERS": (10.0016, 76.2999),   # Ernakulam
    "TVC": (8.5241, 76.9366),    # Trivandrum
    "CLT": (11.2588, 75.7804),   # Calicut
    # Karnataka
    "UBL": (15.3647, 75.1240),   # Hubli
    "MYS": (12.2958, 76.6394),   # Mysore
    "MAQ": (12.8698, 74.8432),   # Mangalore
    # North India
    "NDLS": (28.6428, 77.2197),  # New Delhi
    "NZM": (28.5965, 77.2449),   # Hazrat Nizamuddin
    "DLI": (28.6562, 77.2410),   # Old Delhi
    "PNBE": (25.5941, 85.1376),  # Patna
    "BSB": (25.3176, 82.9739),   # Varanasi
    "LKO": (26.8467, 80.9462),   # Lucknow
    "ADI": (23.0225, 72.5714),   # Ahmedabad
    "ST": (21.1702, 72.8311),    # Surat
    # Between VSKP and BZA
    "VZM": (18.1067, 83.3956),   # Vizianagaram
    "NASP": (17.6868, 83.2185),
    "VKB": (16.8782, 82.2195),
    "ANV": (17.0896, 82.5571),   # Anakapalle
    "RJY": (17.0005, 81.8040),   # Rajahmundry
    "SLO": (17.1333, 82.2000),   # Samalkot Jn
    "TADP": (17.0619, 81.5195),  # Tadepalligudem
    "EE": (16.7155, 81.0903),    # Eluru
    "KVR": (16.3008, 80.4428),   # Kavali (near Guntur)
    "GDR": (14.1463, 79.8453),   # Gudur
    "TPTY": (13.6288, 79.4192),
    # SMVB area
    "SSPN": (13.0067, 77.5667),
    # Orissa coast
    "PRDP": (19.7947, 85.8299),
    "KUR": (19.8116, 85.8346),
    "TATA": (22.7840, 86.1834),  # Tatanagar
    "ROU": (22.2593, 84.8828),   # Rourkela
    # Connecting stations
    "GNT": (16.3008, 80.4428),
    "PALKD": (16.5193, 80.6305),
    "TPT": (16.7155, 81.0903),
    "VNEC": (17.0005, 81.8040),
    "TDV": (17.0619, 81.5195),
}


def main():
    if not STATIONS_CSV.exists():
        print(f"stations.csv not found at {STATIONS_CSV}")
        return

    rows = []
    with open(STATIONS_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["code"].strip().upper()
            if not row.get("lat") and code in KNOWN_COORDS:
                lat, lon = KNOWN_COORDS[code]
                row["lat"] = str(lat)
                row["lon"] = str(lon)
            rows.append(row)

    with open(STATIONS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["code", "name", "lat", "lon"])
        writer.writeheader()
        writer.writerows(rows)

    filled = sum(1 for r in rows if r.get("lat"))
    print(f"Coordinates added. {filled}/{len(rows)} stations now have coordinates.")


if __name__ == "__main__":
    main()
