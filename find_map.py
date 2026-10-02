with open("templates/index.html", "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        if 'id="map"' in line or '#map' in line or 'initMap' in line:
            print(f"{i+1}: {line.strip()}")
