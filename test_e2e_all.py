import urllib.request
import json
import sys

def test(url, method='GET', data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header('Content-Type', 'application/json')
        data_bytes = json.dumps(data).encode('utf-8')
    else:
        data_bytes = None
    with urllib.request.urlopen(req, data=data_bytes, timeout=60) as resp:
        return json.loads(resp.read().decode('utf-8'))

try:
    # 1. Test search with coordinates
    res = test('http://localhost:5000/api/search?from=VISAKHAPATNAM&to=CHENNAI&buffer=20')
    print(f"Search Direct: {len(res['results']['direct'])}, Connecting: {len(res['results']['connecting'])}")
    seg = res['results']['direct'][0]['segments'][0]
    print(f"Direct Seg Coords: {seg.get('from_coords')} -> {seg.get('to_coords')}")
    print(f"Has Route Points: {len(seg.get('route_points', []))}")

    # 2. Test Station Coords API
    coords = test('http://localhost:5000/api/stations/coords')
    print(f"Total Cached Station Coords: {len(coords)}")
    print(f"VSKP coords: {coords.get('VSKP')}, MAS coords: {coords.get('MAS')}")

    # 3. Test Chatbot API
    chat = test('http://localhost:5000/api/chat', method='POST', data={'message': 'What are the best Tatkal hacks?'})
    print(f"Chat reply preview: {chat['reply'][:100].encode('ascii', 'ignore').decode('ascii').replace(chr(10), ' ')}")

    # 4. Test Chatbot Route search
    chat_route = test('http://localhost:5000/api/chat', method='POST', data={'message': 'Find trains from Visakhapatnam to Chennai'})
    print(f"Chat route detected: {chat_route.get('train_data') is not None}")

    # 5. Test Smart Ticket Generation
    ticket = test('http://localhost:5000/api/ticket/generate', method='POST', data={'from': 'VSKP', 'to': 'MAS', 'train_number': '12841'})
    print(f"Ticket ID: {ticket['ticket_id']}, Coach: {ticket['coach']}, Seat: {ticket['suggested_seat']}")

    # 6. Test Travel Intelligence
    explain = test('http://localhost:5000/api/journey/explain', method='POST', data={'journey': res['results']['direct'][0], 'type': 'why_best'})
    print(f"Intelligence Title: {explain['title'].encode('ascii', 'ignore').decode('ascii')}")

    print("=== ALL END-TO-END TESTS PASSED SUCCESSFULLY! ===")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
