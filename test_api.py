"""test_api.py — Quick test of the ARRTS Flask API."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import urllib.request, json, warnings
warnings.filterwarnings('ignore')

def get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# Status check
print("=== /api/status ===")
status = get('http://localhost:5000/api/status')
print(f"  Data loaded: {status['data_loaded']}")
print(f"  Trains: {status['trains']}, Stops: {status['stops']}, Stations: {status['stations']}")

# Main search
print("\n=== /api/search?from=VSKP&to=MAS ===")
results = get('http://localhost:5000/api/search?from=VSKP&to=MAS&date=2026-09-29&buffer=15')
direct = results['results']['direct']
connecting = results['results']['connecting']
print(f"  Direct journeys: {len(direct)}")
print(f"  Connecting journeys: {len(connecting)}")

for j in direct[:3]:
    seg = j['segments'][0]
    print(f"  DIRECT: Train {seg['train_number']} {seg['train_name']} {seg['departure']}->{seg['arrival']} ({j['total_duration']})")

for j in connecting[:3]:
    s1, s2 = j['segments']
    print(f"  CONNECT: {s1['train_number']} + {s2['train_number']} via {j['interchange_station']} ({j['connection_minutes']}min conn, {j['total_duration']} total, health={j['journey_health']})")

# Name-based search
print("\n=== Search by name: Visakhapatnam -> Chennai ===")
results2 = get('http://localhost:5000/api/search?from=Visakhapatnam&to=Chennai&date=2026-09-29&buffer=15')
print(f"  Direct: {len(results2['results']['direct'])}, Connecting: {len(results2['results']['connecting'])}")

# Autocomplete
print("\n=== Autocomplete: /api/stations?q=VSKP ===")
stations = get('http://localhost:5000/api/stations?q=VSKP')
print(f"  Stations: {[s['code']+' '+s['name'] for s in stations[:5]]}")

print("\n=== Autocomplete: /api/stations?q=Chennai ===")
stations2 = get('http://localhost:5000/api/stations?q=Chennai')
print(f"  Stations: {[s['code']+' '+s['name'] for s in stations2[:5]]}")

print("\nAll API tests passed!")
