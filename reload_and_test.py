"""reload_and_test.py — Reload ARRTS data and run search test."""
import sys, io, urllib.request, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Reload
r = urllib.request.urlopen('http://localhost:5000/api/reload')
print('Reload:', json.loads(r.read()))

# Status
r2 = urllib.request.urlopen('http://localhost:5000/api/status')
status = json.loads(r2.read())
print('Status:', status)

# VSKP -> MAS search
r3 = urllib.request.urlopen('http://localhost:5000/api/search?from=VSKP&to=MAS&date=2026-09-29&buffer=15')
res = json.loads(r3.read())
direct = res['results']['direct']
connecting = res['results']['connecting']
print(f'Direct: {len(direct)}, Connecting: {len(connecting)}')
for j in direct[:3]:
    seg = j['segments'][0]
    print(f'  DIRECT: Train {seg["train_number"]} {seg["train_name"]} {seg["departure"]}->{seg["arrival"]} ({j["total_duration"]})')
for j in connecting[:3]:
    s1, s2 = j['segments']
    print(f'  CONNECT: {s1["train_number"]} + {s2["train_number"]} via {j["interchange_station"]} ({j["connection_minutes"]}min, {j["total_duration"]})')
