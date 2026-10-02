"""test_search.py — Test the ARRTS search engine with real data."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import warnings
warnings.filterwarnings('ignore')

import pandas as pd
from datetime import date
from engine.search import find_direct_journeys, find_connecting_journeys, diagnose

stops_df = pd.read_csv('data/out/stops.csv', dtype=str, na_filter=False)
trains_df = pd.read_csv('data/out/trains.csv', dtype=str, na_filter=False)
stops_df['seq'] = pd.to_numeric(stops_df['seq'], errors='coerce').fillna(0).astype(int)
stops_df['day_offset'] = pd.to_numeric(stops_df['day_offset'], errors='coerce').fillna(0).astype(int)
stops_df['station_code'] = stops_df['station_code'].str.strip().str.upper()

travel_date = date(2026, 9, 29)

print("=== DIAGNOSTIC: VSKP to MAS ===")
diag = diagnose('Visakhapatnam', 'Chennai', travel_date, stops_df, trains_df)
for k, v in diag.items():
    print(f"  {k}: {v}")

print()
print("=== DIRECT: VSKP -> MAS ===")
direct = find_direct_journeys('VSKP', 'MAS', travel_date, stops_df, trains_df)
print(f"Found: {len(direct)} direct journeys")
for j in direct[:5]:
    seg = j['segments'][0]
    print(f"  Train {seg['train_number']} {seg['train_name']}: dep={seg['departure']} arr={seg['arrival']} dur={j['total_duration']}")

print()
print("=== DIRECT by name: Visakhapatnam -> Chennai ===")
direct2 = find_direct_journeys('Visakhapatnam', 'Chennai', travel_date, stops_df, trains_df)
print(f"Found: {len(direct2)} direct journeys")

print()
print("=== CONNECTING: VSKP -> MAS (15min buffer) ===")
connecting = find_connecting_journeys('VSKP', 'MAS', travel_date, 15, stops_df, trains_df)
print(f"Found: {len(connecting)} connecting journeys")
for j in connecting[:5]:
    s1, s2 = j['segments']
    print(f"  Train {s1['train_number']} + Train {s2['train_number']} via {j['interchange_station']} ({j['connection_minutes']}min conn, {j['total_duration']} total, health={j['journey_health']})")

print()
print("=== TEST: Invalid direction (MAS->VSKP on HWH->MAS train) ===")
# Train 12841 runs HWH->MAS (VSKP is before MAS)
# So MAS->VSKP should NOT be returned as a valid direct journey
invalid = find_direct_journeys('MAS', 'VSKP', travel_date, stops_df, trains_df)
print(f"Found {len(invalid)} journeys (should be 0 for train 12841 which runs HWH->MAS)")
for j in invalid[:3]:
    seg = j['segments'][0]
    print(f"  FOUND: Train {seg['train_number']}")

print()
print("All tests complete!")
