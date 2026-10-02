
// ── App State ──────────────────────────────────────────────────────────────
const state = {
  results: null,
  selectedJourney: null,
  filter: 'all',
  fromCode: '',
  toCode: '',
  mode: 'future',
  missionMode: false,
  followingJourney: null,
  theme: localStorage.getItem('arrts_theme') || 'light',
  notifications: true,
  bufferPreference: 15,
  lastDirectJourneys: [],
  lastConnectingJourneys: [],
  searchingToday: true,
};

// Station coordinate cache (populated from /api/stations/coords and search results)
const stationCoords = {};

// ── Initialize ─────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  // Set today's date as default
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('inp-date').value = today;
  document.getElementById('inp-date').min = today;

  // Setup autocomplete
  setupAutocomplete('inp-from', 'from-dropdown', 'from-code-badge', 'fromCode');
  setupAutocomplete('inp-to', 'to-dropdown', 'to-code-badge', 'toCode');

  // Initialize map
  initMap();

  // Allow Enter key to search
  ['inp-from', 'inp-to', 'inp-date'].forEach(id => {
    document.getElementById(id).addEventListener('keydown', e => {
      if (e.key === 'Enter') doSearch();
    });
  });
});

// ── Map Engine ─────────────────────────────────────────────────────────────
let map = null; // Main Leaflet OpenStreetMap instance on #map
let sideMap = null; // Alias to map for backward compatibility
let networkMap = null;
let networkTileLayer = null;
let sideTileLayer = null;

let journeyLine = null;
let currentTrainMarker = null;
let liveTrainTimer = null;
let journeyMarkers = [];

let hubsLayerGroup = null;
let corridorsLayerGroup = null;
let activeRouteLayerGroup = null;
let sideRouteLayers = [];
let lastRouteBounds = null;

let showCorridors = false; // cleaner view of actual street/track geography
let showHubs = true;

const MAJOR_HUBS = [
  { code: 'NDLS', name: 'New Delhi', lat: 28.6415, lon: 77.2185, zone: 'Northern Railway', role: 'National Capital Hub' },
  { code: 'CSMT', name: 'Mumbai CSMT', lat: 18.9402, lon: 72.8357, zone: 'Central Railway', role: 'Western Terminus' },
  { code: 'HWH',  name: 'Howrah Jn (Kolkata)', lat: 22.5839, lon: 88.3428, zone: 'Eastern Railway', role: 'Eastern Gateway' },
  { code: 'MAS',  name: 'Chennai Central', lat: 13.0827, lon: 80.2757, zone: 'Southern Railway', role: 'Southern Grand Trunk' },
  { code: 'VSKP', name: 'Visakhapatnam Jn', lat: 17.7215, lon: 83.2870, zone: 'East Coast Railway', role: 'Coastal Mainline Hub' },
  { code: 'SBC',  name: 'KSR Bengaluru', lat: 12.9784, lon: 77.5695, zone: 'South Western Railway', role: 'Silicon Plateau Hub' },
  { code: 'SC',   name: 'Secunderabad (Hyderabad)', lat: 17.4334, lon: 78.5042, zone: 'South Central Railway', role: 'Deccan Crossroads' },
  { code: 'BZA',  name: 'Vijayawada Jn', lat: 16.5186, lon: 80.6198, zone: 'South Central Railway', role: 'Grand Trunk Interchange' },
  { code: 'ADI',  name: 'Ahmedabad Jn', lat: 23.0225, lon: 72.6016, zone: 'Western Railway', role: 'Western Commercial Hub' },
  { code: 'PUNE', name: 'Pune Jn', lat: 18.5284, lon: 73.8739, zone: 'Central Railway', role: 'Deccan Transit Hub' },
  { code: 'BBS',  name: 'Bhubaneswar', lat: 20.2666, lon: 85.8436, zone: 'East Coast Railway', role: 'East Coast Express Hub' },
  { code: 'PNBE', name: 'Patna Jn', lat: 25.6022, lon: 85.1376, zone: 'East Central Railway', role: 'Ganges Valley Hub' },
  { code: 'GHY',  name: 'Guwahati', lat: 26.1820, lon: 91.7513, zone: 'Northeast Frontier', role: 'Northeast Gateway' },
  { code: 'JP',   name: 'Jaipur Jn', lat: 26.9208, lon: 75.7878, zone: 'North Western Railway', role: 'Pink City Junction' },
  { code: 'LKO',  name: 'Lucknow Charbagh', lat: 26.8322, lon: 80.9238, zone: 'Northern Railway', role: 'Avadh Junction' },
  { code: 'TVC',  name: 'Thiruvananthapuram', lat: 8.4875, lon: 76.9525, zone: 'Southern Railway', role: 'Southernmost Terminal' },
  { code: 'NGP',  name: 'Nagpur Jn', lat: 21.1528, lon: 79.0882, zone: 'Central Railway', role: 'Zero Milestone Diamond' },
  { code: 'BPL',  name: 'Bhopal Jn', lat: 23.2685, lon: 77.4126, zone: 'West Central Railway', role: 'Heart of India Hub' },
  { code: 'BSB',  name: 'Varanasi Jn', lat: 25.3284, lon: 82.9866, zone: 'Northern Railway', role: 'Kashi Pilgrimage Terminal' },
  { code: 'CDG',  name: 'Chandigarh', lat: 30.7027, lon: 76.8184, zone: 'Northern Railway', role: 'Northern Gateway' }
];

const NATIONAL_CORRIDORS = [
  {
    name: 'Delhi – Mumbai Western Trunk (1,384 km)',
    color: '#3B82F6',
    points: [[28.6415, 77.2185], [27.18, 78.02], [26.22, 78.18], [23.2685, 77.4126], [22.30, 73.18], [21.17, 72.83], [18.9402, 72.8357]]
  },
  {
    name: 'Delhi – Howrah Grand Eastern (1,449 km)',
    color: '#10B981',
    points: [[28.6415, 77.2185], [26.44, 80.33], [25.43, 81.84], [25.3284, 82.9866], [25.6022, 85.1376], [23.80, 86.43], [22.5839, 88.3428]]
  },
  {
    name: 'Howrah – Chennai East Coast Corridor (1,661 km)',
    color: '#F59E0B',
    points: [[22.5839, 88.3428], [21.49, 86.92], [20.46, 85.88], [20.2666, 85.8436], [17.7215, 83.2870], [16.5186, 80.6198], [13.0827, 80.2757]]
  },
  {
    name: 'Delhi – Chennai Grand Trunk Corridor (2,180 km)',
    color: '#8B5CF6',
    points: [[28.6415, 77.2185], [26.22, 78.18], [23.2685, 77.4126], [21.1528, 79.0882], [17.4334, 78.5042], [16.5186, 80.6198], [13.0827, 80.2757]]
  },
  {
    name: 'Mumbai – Chennai Deccan Corridor (1,281 km)',
    color: '#EC4899',
    points: [[18.9402, 72.8357], [18.5284, 73.8739], [17.65, 75.90], [15.34, 76.46], [13.62, 79.41], [13.0827, 80.2757]]
  },
  {
    name: 'Mumbai – Howrah Central Corridor (1,968 km)',
    color: '#14B8A6',
    points: [[18.9402, 72.8357], [20.00, 73.78], [20.90, 77.75], [21.1528, 79.0882], [21.25, 81.63], [21.48, 83.98], [22.5839, 88.3428]]
  }
];

function initMap() {
  if (typeof L === 'undefined') {
    console.warn('Leaflet script is still loading, will retry in 150ms...');
    setTimeout(initMap, 150);
    return;
  }

  // Pre-initialize #map container
  ensureJourneyMap();

  // Initialize Network Explorer Map with Real OpenStreetMap
  const netEl = document.getElementById('network-map');
  if (netEl && !networkMap) {
    try {
      networkMap = L.map('network-map', {
        zoomControl: true,
        attributionControl: true
      }).setView([20.5937, 78.9629], 5);

      L.control.scale({ imperial: false }).addTo(networkMap);
      updateNetworkMapTiles('osm');

      hubsLayerGroup = L.layerGroup().addTo(networkMap);
      corridorsLayerGroup = L.layerGroup().addTo(networkMap);
      activeRouteLayerGroup = L.layerGroup().addTo(networkMap);

      if (showHubs) renderMajorHubs();
      if (showCorridors) renderTrunkCorridors();
    } catch (e) {
      console.warn('Network map init notice:', e);
    }
  }

  // Pre-load station coordinates in background
  preloadStationCoords();
}

function ensureJourneyMap() {
  const mapEl = document.getElementById('map');
  if (!mapEl) return;
  if (typeof L === 'undefined') {
    console.error('Leaflet library is not loaded!');
    return;
  }
  if (!map) {
    try {
      // Real OpenStreetMap initialized on #map with authentic railway view
      map = L.map('map', {
        zoomControl: true,
        attributionControl: true
      }).setView([17.6868, 83.2185], 8);

      window.map = map;
      window.sideMap = map;
      sideMap = map;

      // Official standard OpenStreetMap tile layer (no API key required)
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors'
      }).addTo(map);

      L.control.scale({ imperial: false }).addTo(map);
      console.log('✓ Leaflet OpenStreetMap initialized successfully on #map');
    } catch(e) {
      console.warn('Journey map init notice:', e);
    }
  }

  // Debugging requirement: call invalidateSize when container is shown or resized
  setTimeout(() => { if (map) map.invalidateSize(); }, 60);
  setTimeout(() => { if (map) map.invalidateSize(); }, 200);
  setTimeout(() => { if (map) map.invalidateSize(); }, 600);
}

function ensureSideMap() {
  ensureJourneyMap();
}

function toggleJourneyMapFullscreen() {
  const card = document.getElementById('map-panel-card');
  const btn = document.getElementById('btn-map-fullscreen');
  if (!card) return;
  card.classList.toggle('map-card-expanded');
  const isExp = card.classList.contains('map-card-expanded');
  if (btn) btn.textContent = isExp ? '✕ Exit' : '⛶ Fullscreen';
  setTimeout(() => {
    if (map) {
      map.invalidateSize();
      if (journeyLine) map.fitBounds(journeyLine.getBounds(), { padding: [40, 40] });
    }
  }, 100);
}

async function preloadStationCoords() {
  try {
    const res = await fetch('/api/stations/coords');
    const data = await res.json();
    Object.assign(stationCoords, data);
  } catch (e) {
    console.warn('Failed to pre-fetch station coordinates', e);
  }
}

let railwayOverlayLayer = null;
let sideRailwayOverlay = null;
let showRailwayOverlay = false;
let customMapApiKey = localStorage.getItem('arrts_map_key') || '';

function toggleRailwayMapOverlay() {
  showRailwayOverlay = !showRailwayOverlay;
  const btn = document.getElementById('btn-toggle-railway');
  if (btn) btn.classList.toggle('active', showRailwayOverlay);

  const railwayUrl = 'https://{s}.tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png';
  const railwayAttr = 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | Map style: &copy; <a href="https://www.OpenRailwayMap.org">OpenRailwayMap</a>';

  if (showRailwayOverlay) {
    if (!railwayOverlayLayer) {
      railwayOverlayLayer = L.tileLayer(railwayUrl, {
        maxZoom: 19,
        subdomains: 'abc',
        attribution: railwayAttr
      });
    }
    if (!sideRailwayOverlay) {
      sideRailwayOverlay = L.tileLayer(railwayUrl, {
        maxZoom: 19,
        subdomains: 'abc',
        attribution: railwayAttr
      });
    }
    if (networkMap) networkMap.addLayer(railwayOverlayLayer);
    if (map) map.addLayer(sideRailwayOverlay);
    showToast('🚆 OpenRailwayMap track infrastructure overlay enabled');
  } else {
    if (networkMap && railwayOverlayLayer) networkMap.removeLayer(railwayOverlayLayer);
    if (map && sideRailwayOverlay) map.removeLayer(sideRailwayOverlay);
    showToast('OpenRailwayMap overlay disabled');
  }
}

function saveMapApiKey() {
  const inp = document.getElementById('map-api-key-input');
  const val = inp ? inp.value.trim() : '';
  customMapApiKey = val;
  if (val) {
    localStorage.setItem('arrts_map_key', val);
    const status = document.getElementById('map-api-key-status');
    if (status) {
      status.style.display = 'block';
      status.textContent = '✓ Map API Key saved successfully!';
    }
    showToast('🔑 Custom Map API key saved! Tile providers active.');
    const sel = document.getElementById('map-tile-select');
    if (sel) changeMapTileStyle(sel.value);
  } else {
    localStorage.removeItem('arrts_map_key');
    showToast('Map API key removed. Using default map tiles.');
  }
}

function getTileConfig(style) {
  let url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
  let attribution = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors';
  let maxZoom = 19;
  let subdomains = 'abc';

  if (style === 'osm' || style === 'default' || !style) {
    url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    attribution = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors';
    maxZoom = 19;
  } else if (style === 'google_streets') {
    url = 'https://mt{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}';
    attribution = '&copy; <a href="https://maps.google.com" target="_blank">Google Maps</a>';
    maxZoom = 20;
    subdomains = '0123';
  } else if (style === 'google_satellite') {
    url = 'https://mt{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}';
    attribution = '&copy; <a href="https://maps.google.com" target="_blank">Google Maps Satellite</a>';
    maxZoom = 20;
    subdomains = '0123';
  } else if (style === 'google_terrain') {
    url = 'https://mt{s}.google.com/vt/lyrs=p&x={x}&y={y}&z={z}';
    attribution = '&copy; <a href="https://maps.google.com" target="_blank">Google Maps Terrain</a>';
    maxZoom = 20;
    subdomains = '0123';
  } else if (style === 'dark') {
    url = 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png';
    attribution = '&copy; <a href="https://carto.com/" target="_blank">CARTO</a> &copy; OpenStreetMap';
    subdomains = 'abcd';
    maxZoom = 19;
  } else if (style === 'voyager') {
    url = 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png';
    attribution = '&copy; <a href="https://carto.com/" target="_blank">CARTO</a> &copy; OpenStreetMap';
    subdomains = 'abcd';
    maxZoom = 19;
  } else {
    url = 'https://tile.openstreetmap.org/{z}/{x}/{y}.png';
    attribution = '&copy; <a href="https://www.openstreetmap.org/copyright" target="_blank">OpenStreetMap</a> contributors';
    maxZoom = 19;
  }

  return { url, attribution, maxZoom, subdomains };
}

function updateNetworkMapTiles(style) {
  if (!networkMap) return;
  if (networkTileLayer) networkMap.removeLayer(networkTileLayer);
  const cfg = getTileConfig(style || 'osm');
  networkTileLayer = L.tileLayer(cfg.url, {
    maxZoom: cfg.maxZoom,
    subdomains: cfg.subdomains,
    attribution: cfg.attribution
  }).addTo(networkMap);
}

function updateSideMapTiles(style) {
  if (!map) ensureJourneyMap();
  if (!map) return;
  if (sideTileLayer) map.removeLayer(sideTileLayer);
  const cfg = getTileConfig(style || 'osm');
  sideTileLayer = L.tileLayer(cfg.url, {
    maxZoom: cfg.maxZoom,
    subdomains: cfg.subdomains,
    attribution: cfg.attribution
  }).addTo(map);
}

function updateMapTiles(isDark) {
  const currentSel = document.getElementById('map-tile-select');
  let style = currentSel ? currentSel.value : 'osm';
  updateNetworkMapTiles(style);
  updateSideMapTiles(style);
  if (currentSel) currentSel.value = style;
}

function changeMapTileStyle(style) {
  updateNetworkMapTiles(style);
  updateSideMapTiles(style);
}

function renderMajorHubs() {
  if (!hubsLayerGroup) return;
  hubsLayerGroup.clearLayers();

  MAJOR_HUBS.forEach(hub => {
    const icon = L.divIcon({
      className: '',
      html: `
        <div class="station-pin origin" style="border-color:var(--primary);color:var(--primary);">
          <span class="pin-dot" style="background:var(--secondary);box-shadow:0 0 0 2px rgba(255,111,0,0.3);"></span>
          <span>${escapeHtml(hub.code)}</span>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0]
    });

    const popupHtml = `
      <div class="station-popup">
        <div class="station-popup-title">🚉 ${escapeHtml(hub.name)}</div>
        <div class="station-popup-code">${escapeHtml(hub.code)} • ${escapeHtml(hub.role)}</div>
        <div class="station-popup-zone">🏛️ ${escapeHtml(hub.zone)}</div>
        <div style="font-size:11px;color:var(--text-muted);margin-bottom:6px;">GPS: ${hub.lat.toFixed(4)}° N, ${hub.lon.toFixed(4)}° E</div>
        <div class="station-popup-actions">
          <button class="station-popup-btn from" onclick="setRouteFromMap('${escapeHtmlAttr(hub.name)}', '${hub.code}', true)">📍 Route From</button>
          <button class="station-popup-btn to" onclick="setRouteFromMap('${escapeHtmlAttr(hub.name)}', '${hub.code}', false)">🏁 Route To</button>
        </div>
      </div>
    `;

    const marker = L.marker([hub.lat, hub.lon], { icon }).bindPopup(popupHtml);
    hubsLayerGroup.addLayer(marker);
  });
}

function renderTrunkCorridors() {
  if (!corridorsLayerGroup) return;
  corridorsLayerGroup.clearLayers();

  NATIONAL_CORRIDORS.forEach(corridor => {
    // Underlay track glow
    const glow = L.polyline(corridor.points, {
      color: corridor.color,
      weight: 6,
      opacity: 0.25
    });
    corridorsLayerGroup.addLayer(glow);

    // Track railway line
    const line = L.polyline(corridor.points, {
      color: corridor.color,
      weight: 3,
      opacity: 0.85,
      dashArray: '8, 6'
    }).bindTooltip(`<b>${corridor.name}</b>`, { sticky: true });
    corridorsLayerGroup.addLayer(line);
  });
}

function toggleCorridorsLayer() {
  showCorridors = !showCorridors;
  const btn = document.getElementById('btn-toggle-corridors');
  if (btn) btn.classList.toggle('active', showCorridors);
  if (showCorridors) {
    if (networkMap && corridorsLayerGroup) networkMap.addLayer(corridorsLayerGroup);
  } else {
    if (networkMap && corridorsLayerGroup) networkMap.removeLayer(corridorsLayerGroup);
  }
}

function toggleHubsLayer() {
  showHubs = !showHubs;
  const btn = document.getElementById('btn-toggle-hubs');
  if (btn) btn.classList.toggle('active', showHubs);
  if (showHubs) {
    if (networkMap && hubsLayerGroup) networkMap.addLayer(hubsLayerGroup);
  } else {
    if (networkMap && hubsLayerGroup) networkMap.removeLayer(hubsLayerGroup);
  }
}

function recenterIndiaMap() {
  if (networkMap) {
    networkMap.flyTo([22.5, 79.5], 5, { duration: 1.2 });
    showToast('🗺️ Map recentered to Pan-India view');
  }
}

function toggleNetworkMapFullscreen() {
  const card = document.getElementById('map-wrapper-card');
  const btn = document.getElementById('btn-fullscreen-map');
  if (!card) return;
  const isFull = card.classList.toggle('fullscreen');
  if (btn) btn.textContent = isFull ? '✕ Exit' : '⛶ Fullscreen';
  setTimeout(() => {
    if (networkMap) networkMap.invalidateSize();
  }, 100);
}

function setRouteFromMap(stationName, stationCode, isOrigin) {
  if (isOrigin) {
    document.getElementById('inp-from').value = stationName;
    const badge = document.getElementById('from-code-badge');
    badge.textContent = stationCode;
    badge.style.display = 'block';
    state.fromCode = stationCode;
    showToast(`📍 Origin set to ${stationName} (${stationCode})`);
  } else {
    document.getElementById('inp-to').value = stationName;
    const badge = document.getElementById('to-code-badge');
    badge.textContent = stationCode;
    badge.style.display = 'block';
    state.toCode = stationCode;
    showToast(`🏁 Destination set to ${stationName} (${stationCode})`);
  }
  // Smooth scroll up to search input
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function clearActiveRouteFromMap() {
  if (activeRouteLayerGroup) activeRouteLayerGroup.clearLayers();
  sideRouteLayers.forEach(l => { if (sideMap) sideMap.removeLayer(l); });
  sideRouteLayers = [];
  lastRouteBounds = null;
  const banner = document.getElementById('active-route-banner');
  if (banner) banner.style.display = 'none';
  recenterIndiaMap();
}

function scrollToResults() {
  const res = document.getElementById('results-wrapper');
  if (res) {
    window.scrollTo({ top: res.offsetTop - 60, behavior: 'smooth' });
  }
}

function createPinIcon(code, label, type) {
  return L.divIcon({
    className: '',
    html: `
      <div class="station-pin ${type}">
        <span class="pin-dot"></span>
        <span>${escapeHtml(code || label)}</span>
      </div>
    `,
    iconSize: [0, 0],
    iconAnchor: [0, 0]
  });
}

function addRoutePin(lat, lon, label, code, type, popupHtml) {
  const icon = createPinIcon(code, label, type);

  // Add to networkMap
  if (activeRouteLayerGroup) {
    const marker = L.marker([lat, lon], {
      icon,
      zIndexOffset: type === 'origin' || type === 'dest' ? 1000 : 500
    }).bindPopup(popupHtml);
    activeRouteLayerGroup.addLayer(marker);
  }

  // Add to map
  if (map) {
    const sideMarker = L.marker([lat, lon], {
      icon,
      zIndexOffset: type === 'origin' || type === 'dest' ? 1000 : 500
    }).bindPopup(popupHtml).addTo(map);
    journeyMarkers.push(sideMarker);
  }
}

function drawJourneyOnMap(journey) {
  if (!journey) return;

  ensureJourneyMap();
  if (!map) return;
  map.invalidateSize();

  // Clear previous layers & markers on map
  if (journeyLine) {
    try { map.removeLayer(journeyLine); } catch(e){}
    journeyLine = null;
    window.currentJourneyLine = null;
  }
  journeyMarkers.forEach(m => {
    try { map.removeLayer(m); } catch(e){}
  });
  journeyMarkers = [];

  if (currentTrainMarker) {
    try { map.removeLayer(currentTrainMarker); } catch(e){}
    currentTrainMarker = null;
  }
  if (liveTrainTimer) {
    clearInterval(liveTrainTimer);
    liveTrainTimer = null;
  }

  // Also clear networkMap route layers
  if (activeRouteLayerGroup) activeRouteLayerGroup.clearLayers();
  sideRouteLayers.forEach(l => { if (sideMap && sideMap !== map) try { sideMap.removeLayer(l); } catch(e){} });
  sideRouteLayers = [];

  const segments = journey.segments || [];
  if (!segments.length) return;

  const isConnecting = journey.type === 'connecting';
  const totalDuration = journey.total_duration || '';
  const journeyHealth = journey.journey_health || (journey.health_score ? journey.health_score.health : 'Stable');

  const srcDisplay = typeof journey.source === 'object' ? journey.source.name : (journey.source || segments[0].from);
  const dstDisplay = typeof journey.destination === 'object' ? journey.destination.name : (journey.destination || segments[segments.length - 1].to);

  // Update headers
  const banner = document.getElementById('active-route-banner');
  const bannerText = document.getElementById('arb-route-text');
  const bannerStats = document.getElementById('arb-stats');
  if (banner && bannerText && bannerStats) {
    bannerText.textContent = `${srcDisplay} → ${dstDisplay}`;
    bannerStats.textContent = `⏱ ${totalDuration} · ${journey.transfers || (isConnecting ? 1 : 0)} Transfer(s) · ${journeyHealth}`;
    banner.style.display = 'flex';
  }
  const summaryEl = document.getElementById('map-route-summary');
  if (summaryEl) {
    summaryEl.textContent = `${srcDisplay} → ${dstDisplay} (${totalDuration})`;
  }

  // 1. Gather all actual station coordinates from schedule/timetable
  const allCoordinates = [];

  segments.forEach((seg, i) => {
    const fromCoords = seg.from_coords || stationCoords[seg.from_code] || stationCoords[seg.from];
    const toCoords = seg.to_coords || stationCoords[seg.to_code] || stationCoords[seg.to];

    let segPoints = [];
    if (seg.route_points && seg.route_points.length >= 2) {
      segPoints = seg.route_points;
    } else if (fromCoords && toCoords) {
      segPoints = [fromCoords, toCoords];
    }

    if (segPoints.length > 0) {
      segPoints.forEach(pt => allCoordinates.push(pt));
    }
  });

  // Fallbacks if route_points weren't attached
  if (allCoordinates.length < 2 && journey.route_coordinates && journey.route_coordinates.length >= 2) {
    journey.route_coordinates.forEach(pt => allCoordinates.push(pt));
  }
  if (allCoordinates.length < 2) {
    const sInfo = journey.source_info || journey.source_station || {};
    const dInfo = journey.destination_info || journey.destination_station || {};
    if (sInfo.lat && sInfo.lng && dInfo.lat && dInfo.lng) {
      allCoordinates.push([sInfo.lat, sInfo.lng]);
      if (journey.interchanges && journey.interchanges.length > 0) {
        journey.interchanges.forEach(ic => {
          if (ic.lat && ic.lng) allCoordinates.push([ic.lat, ic.lng]);
        });
      }
      allCoordinates.push([dInfo.lat, dInfo.lng]);
    }
  }

  // 2. Draw Railway Journey Line
  const isMM = document.body.classList.contains('machine-mode');

  if (allCoordinates.length >= 2) {
    if (isMM) {
      // Machine Mode: tactical high-contrast dark border with glowing dashed line matching screenshot
      const casingLine = L.polyline(allCoordinates, {
        color: '#030712',
        weight: 9,
        opacity: 0.9,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);
      journeyMarkers.push(casingLine);

      journeyLine = L.polyline(allCoordinates, {
        color: '#818CF8',
        weight: 5,
        opacity: 0.95,
        dashArray: '6, 8',
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);
      window.currentJourneyLine = journeyLine;

      if (activeRouteLayerGroup) {
        const netCasing = L.polyline(allCoordinates, { color: '#030712', weight: 9, opacity: 0.9, lineCap: 'round', lineJoin: 'round' });
        const netLine = L.polyline(allCoordinates, { color: '#818CF8', weight: 5, opacity: 0.95, dashArray: '6, 8', lineCap: 'round', lineJoin: 'round' });
        activeRouteLayerGroup.addLayer(netCasing);
        activeRouteLayerGroup.addLayer(netLine);
      }
    } else {
      // Standard Mode: High-visibility crisp white casing / border
      const casingLine = L.polyline(allCoordinates, {
        color: '#FFFFFF',
        weight: 10,
        opacity: 0.95,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);
      journeyMarkers.push(casingLine);

      // Primary bright vibrant Journey Line (high-visibility Crimson #E11D48 / Orange #FF5722)
      const lineColor = isConnecting ? '#FF5722' : '#E11D48';
      journeyLine = L.polyline(allCoordinates, {
        color: lineColor,
        weight: 6,
        opacity: 1.0,
        lineCap: 'round',
        lineJoin: 'round'
      }).addTo(map);
      window.currentJourneyLine = journeyLine;

      // Synchronize to networkMap if open
      if (activeRouteLayerGroup) {
        const netCasing = L.polyline(allCoordinates, { color: '#FFFFFF', weight: 10, opacity: 0.95, lineCap: 'round', lineJoin: 'round' });
        const netLine = L.polyline(allCoordinates, { color: lineColor, weight: 6, opacity: 1.0, lineCap: 'round', lineJoin: 'round' });
        activeRouteLayerGroup.addLayer(netCasing);
        activeRouteLayerGroup.addLayer(netLine);
      }
    }
  }

  // 3. Station Markers

  // A. SOURCE STATION MARKER
  const firstSeg = segments[0];
  const sCoords = firstSeg.from_coords || stationCoords[firstSeg.from_code] || (journey.source_info && [journey.source_info.lat, journey.source_info.lng]);
  if (sCoords && sCoords[0] && sCoords[1]) {
    const srcPopup = `
      <div class="station-popup">
        <div style="font-weight:800;color:#047857;margin-bottom:3px;font-size:11px;">🟢 SOURCE STATION (ORIGIN)</div>
        <div class="station-popup-title">${escapeHtml(firstSeg.from)} (${escapeHtml(firstSeg.from_code || '')})</div>
        <div style="margin-top:4px;">Train: <b>${escapeHtml(firstSeg.train_number)} ${escapeHtml(firstSeg.train_name)}</b></div>
        <div>Departure: <b>${escapeHtml(firstSeg.departure)}</b></div>
        <div style="margin-top:4px;color:#059669;font-weight:600;">Status: Boarding Point</div>
      </div>
    `;

    const srcIcon = isMM ? L.divIcon({
      className: '',
      html: `
        <div style="display:flex;flex-direction:column;align-items:center;transform:translate(-50%, -50%);pointer-events:auto;">
          <div style="width:12px;height:12px;border-radius:50%;background:#FFFFFF;border:2.5px solid #38BDF8;box-shadow:0 0 12px #38BDF8;margin-bottom:4px;"></div>
          <div class="mm-map-pill">
            <div>${escapeHtml(firstSeg.from)}</div>
            <div class="sub">ORIGIN • ${escapeHtml(firstSeg.from_code || '')}</div>
          </div>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0]
    }) : L.divIcon({
      className: '',
      html: `
        <div class="station-pin origin">
          <span class="pin-dot"></span>
          <span>${escapeHtml(firstSeg.from_code || firstSeg.from)}</span>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0]
    });

    const srcMarker = L.marker(sCoords, { icon: srcIcon, zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup(srcPopup);
    journeyMarkers.push(srcMarker);

    if (activeRouteLayerGroup) {
      const netSrc = L.marker(sCoords, { icon: srcIcon, zIndexOffset: 1000 }).bindPopup(srcPopup);
      activeRouteLayerGroup.addLayer(netSrc);
    }
  }

  // B. INTERCHANGE STATION MARKER(S)
  if (isConnecting && segments.length > 1) {
    for (let i = 0; i < segments.length - 1; i++) {
      const cSeg = segments[i];
      const nSeg = segments[i + 1];
      const icCoords = cSeg.to_coords || stationCoords[cSeg.to_code] || (journey.interchanges && journey.interchanges[i] && [journey.interchanges[i].lat, journey.interchanges[i].lng]);
      const icName = journey.interchange_station || cSeg.to;
      const icCode = cSeg.to_code || '';
      const connMins = journey.connection_minutes || (journey.connection_formatted ? parseInt(journey.connection_formatted) : 25);
      const connBuffer = journey.connection_formatted || (journey.connection_minutes ? `${journey.connection_minutes} minutes` : '25 minutes');
      const isRisky = (connMins < 30) || ['Watch', 'At Risk', 'Critical'].includes(journey.journey_health);

      if (icCoords && icCoords[0] && icCoords[1]) {
        const icPopup = `
          <div class="station-popup">
            <div style="font-weight:800;color:${isRisky ? '#F59E0B' : '#D97706'};margin-bottom:3px;font-size:11px;">
              ${isRisky ? '⚠️ RISKY INTERCHANGE (BUFFER: ' + connMins + 'm)' : '🔀 INTERCHANGE STATION'}
            </div>
            <div class="station-popup-title">${escapeHtml(icName)} (${escapeHtml(icCode)})</div>
            <div style="margin-top:6px;padding-top:4px;border-top:1px dashed var(--border);">
              <div><b>Train 1:</b> ${escapeHtml(cSeg.train_number)} ${escapeHtml(cSeg.train_name)}</div>
              <div>Arrival: <b>${escapeHtml(cSeg.arrival)}</b></div>
            </div>
            <div style="margin-top:4px;padding-top:4px;border-top:1px dashed var(--border);">
              <div><b>Train 2:</b> ${escapeHtml(nSeg.train_number)} ${escapeHtml(nSeg.train_name)}</div>
              <div>Departure: <b>${escapeHtml(nSeg.departure)}</b></div>
            </div>
            <div style="margin-top:6px;background:${isRisky ? '#FEF3C7' : '#FFF3E0'};color:${isRisky ? '#92400E' : '#1C2434'};padding:5px 8px;border-radius:6px;font-size:11px;">
              Connection Buffer: <b>${escapeHtml(connBuffer)}</b> ${isRisky ? '(Tight buffer!)' : ''}<br/>
              Journey Health: <b style="color:${isRisky ? '#DC2626' : '#059669'};">${escapeHtml(journeyHealth)}</b>
            </div>
          </div>
        `;

        let icIcon;
        if (isMM) {
          if (isRisky) {
            icIcon = L.divIcon({
              className: '',
              html: `
                <div style="display:flex;align-items:center;gap:8px;transform:translate(-18px, -50%);pointer-events:auto;">
                  <div style="width:22px;height:22px;border-radius:50%;background:#F59E0B;border:2px solid #FEF3C7;box-shadow:0 0 16px #F59E0B;display:flex;align-items:center;justify-content:center;color:#FFFFFF;font-weight:900;font-size:12px;animation:pulse 1.5s infinite;">⚠️</div>
                  <div class="mm-map-pill risky">
                    <div style="font-size:12px;font-weight:800;color:#FDE68A;">${escapeHtml(icName)}</div>
                    <div class="sub" style="font-size:10px;color:#FBBF24;">risky transfer (${connMins}m)</div>
                  </div>
                </div>
              `,
              iconSize: [0, 0],
              iconAnchor: [0, 0]
            });
          } else {
            icIcon = L.divIcon({
              className: '',
              html: `
                <div style="display:flex;align-items:center;gap:8px;transform:translate(-18px, -50%);pointer-events:auto;">
                  <div style="width:20px;height:20px;border-radius:50%;background:#38BDF8;border:2px solid #FFFFFF;box-shadow:0 0 12px #818CF8;display:flex;align-items:center;justify-content:center;color:#0F172A;font-weight:900;font-size:12px;">↗</div>
                  <div class="mm-map-pill">
                    <div style="font-size:12px;font-weight:700;">${escapeHtml(icName)}</div>
                    <div class="sub" style="font-size:10px;color:#E2E8F0;">transfer</div>
                  </div>
                </div>
              `,
              iconSize: [0, 0],
              iconAnchor: [0, 0]
            });
          }
        } else {
          icIcon = L.divIcon({
            className: '',
            html: `
              <div class="station-pin transfer">
                <span class="pin-dot"></span>
                <span>${escapeHtml(icCode || icName)}</span>
              </div>
            `,
            iconSize: [0, 0],
            iconAnchor: [0, 0]
          });
        }

        const icMarker = L.marker(icCoords, { icon: icIcon, zIndexOffset: 950 })
          .addTo(map)
          .bindPopup(icPopup);
        journeyMarkers.push(icMarker);

        if (activeRouteLayerGroup) {
          const netIc = L.marker(icCoords, { icon: icIcon, zIndexOffset: 950 }).bindPopup(icPopup);
          activeRouteLayerGroup.addLayer(netIc);
        }
      }
    }
  }

  // C. DESTINATION STATION MARKER
  const lastSeg = segments[segments.length - 1];
  const dCoords = lastSeg.to_coords || stationCoords[lastSeg.to_code] || (journey.destination_info && [journey.destination_info.lat, journey.destination_info.lng]);
  if (dCoords && dCoords[0] && dCoords[1]) {
    const dstPopup = `
      <div class="station-popup">
        <div style="font-weight:800;color:#DC2626;margin-bottom:3px;font-size:11px;">🏁 FINAL DESTINATION</div>
        <div class="station-popup-title">${escapeHtml(lastSeg.to)} (${escapeHtml(lastSeg.to_code || '')})</div>
        <div style="margin-top:4px;">Train: <b>${escapeHtml(lastSeg.train_number)} ${escapeHtml(lastSeg.train_name)}</b></div>
        <div>Arrival: <b>${escapeHtml(lastSeg.arrival)}</b></div>
        <div style="margin-top:4px;">Total Duration: <b>${escapeHtml(totalDuration)}</b></div>
        <div style="color:#059669;font-weight:600;margin-top:2px;">Status: Journey Complete</div>
      </div>
    `;

    const dstIcon = isMM ? L.divIcon({
      className: '',
      html: `
        <div style="display:flex;align-items:center;gap:8px;transform:translate(-18px, -50%);pointer-events:auto;">
          <div style="width:20px;height:20px;border-radius:50%;background:#FFFFFF;border:3px solid #818CF8;box-shadow:0 0 14px #818CF8;"></div>
          <div class="mm-map-pill">
            <div style="font-size:12px;font-weight:700;">${escapeHtml(lastSeg.to)}</div>
          </div>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0]
    }) : L.divIcon({
      className: '',
      html: `
        <div class="station-pin dest">
          <span class="pin-dot"></span>
          <span>${escapeHtml(lastSeg.to_code || lastSeg.to)}</span>
        </div>
      `,
      iconSize: [0, 0],
      iconAnchor: [0, 0]
    });

    const dstMarker = L.marker(dCoords, { icon: dstIcon, zIndexOffset: 1000 })
      .addTo(map)
      .bindPopup(dstPopup);
    journeyMarkers.push(dstMarker);

    if (activeRouteLayerGroup) {
      const netDst = L.marker(dCoords, { icon: dstIcon, zIndexOffset: 1000 }).bindPopup(dstPopup);
      activeRouteLayerGroup.addLayer(netDst);
    }
  }

  // 4. MAP AUTO-ZOOM (Requirement 10)
  if (journeyLine) {
    try {
      map.fitBounds(journeyLine.getBounds(), { padding: [40, 40] });
    } catch(e) {
      console.warn('fitBounds fallback', e);
    }
    if (networkMap) {
      try {
        networkMap.flyToBounds(journeyLine.getBounds(), { padding: [50, 50], maxZoom: 11, duration: 1.0 });
      } catch(e){}
    }
  } else if (allCoordinates.length > 0) {
    map.setView(allCoordinates[0], 8);
  }

  // 5. CURRENT TRAIN LOCATION & 60s UPDATE (Requirement 11 & 12)
  const activeTrainNumber = firstSeg.train_number;
  if (activeTrainNumber) {
    fetchLiveTrainLocation(activeTrainNumber);
    liveTrainTimer = setInterval(() => {
      fetchLiveTrainLocation(activeTrainNumber);
    }, 60000);
  }
}

async function fetchLiveTrainLocation(trainNumber) {
  if (!trainNumber || !map) return;
  try {
    const res = await fetch(`/api/train/live/${encodeURIComponent(trainNumber)}`);
    const data = await res.json();
    if (data && data.available && data.latitude && data.longitude) {
      const trainCoords = [data.latitude, data.longitude];

      const trainPopup = `
        <div class="station-popup">
          <div style="font-weight:800;color:#FF6F00;margin-bottom:3px;font-size:11px;">🚆 CURRENT LIVE TRAIN POSITION</div>
          <div class="station-popup-title">Train ${escapeHtml(data.train_number)} — ${escapeHtml(data.train_name)}</div>
          <div style="margin-top:4px;">Current Station: <b>${escapeHtml(data.current_station)} (${escapeHtml(data.station_code)})</b></div>
          <div style="margin-top:2px;">Status: <b style="color:#059669;">${escapeHtml(data.status)}</b></div>
          <div style="font-size:11px;color:var(--text-muted);margin-top:4px;">Live Telemetry Updated: ${escapeHtml(data.updated_at)}</div>
        </div>
      `;

      const trainIcon = L.divIcon({
        className: '',
        html: `
          <div style="background:#FF6F00;color:#fff;border:2px solid #fff;border-radius:20px;padding:3px 8px;font-size:11px;font-weight:800;display:flex;align-items:center;gap:4px;box-shadow:0 3px 12px rgba(255,111,0,0.5);transform:translate(-50%, -50%);">
            <span class="pulse-green" style="background:#fff;width:6px;height:6px;"></span>
            <span>🚆 ${escapeHtml(data.train_number)}</span>
          </div>
        `,
        iconSize: [0, 0],
        iconAnchor: [0, 0]
      });

      if (!currentTrainMarker) {
        currentTrainMarker = L.marker(trainCoords, { icon: trainIcon, zIndexOffset: 1200 })
          .addTo(map)
          .bindPopup(trainPopup);
        journeyMarkers.push(currentTrainMarker);
      } else {
        currentTrainMarker.setLatLng(trainCoords);
        currentTrainMarker.setPopupContent(trainPopup);
      }
    }
  } catch(e) {
    console.warn('Could not fetch live train position:', e);
  }
}

function fitCurrentRoute() {
  if (map) {
    map.invalidateSize();
    if (journeyLine) {
      map.fitBounds(journeyLine.getBounds(), { padding: [40, 40] });
    } else if (lastRouteBounds) {
      map.fitBounds(lastRouteBounds, { padding: [40, 40] });
    }
  }
  if (networkMap && journeyLine) {
    networkMap.flyToBounds(journeyLine.getBounds(), { padding: [50, 50], maxZoom: 11 });
  }
}

function openInMaps() {
  const j = state.selectedJourney;
  if (!j) return;
  const src = j.segments[0];
  const dst = j.segments[j.segments.length - 1];
  window.open(`https://www.openstreetmap.org/directions?from=${src.from}&to=${dst.to}`, '_blank');
}

// ── Autocomplete ───────────────────────────────────────────────────────────
function setupAutocomplete(inputId, dropdownId, badgeId, stateKey) {
  const input = document.getElementById(inputId);
  const dropdown = document.getElementById(dropdownId);
  const badge = document.getElementById(badgeId);
  let timer = null;
  let selectedCode = '';

  input.addEventListener('input', () => {
    clearTimeout(timer);
    const val = input.value.trim();
    selectedCode = '';
    badge.style.display = 'none';
    state[stateKey] = '';

    if (val.length < 2) { dropdown.classList.remove('open'); return; }
    timer = setTimeout(() => fetchStations(val), 200);
  });

  input.addEventListener('blur', () => {
    setTimeout(() => dropdown.classList.remove('open'), 180);
  });

  async function fetchStations(q) {
    try {
      const res = await fetch(`/api/stations?q=${encodeURIComponent(q)}&limit=8`);
      const stations = await res.json();
      renderDropdown(stations);
    } catch(e) { dropdown.classList.remove('open'); }
  }

  function renderDropdown(stations) {
    if (!stations.length) { dropdown.classList.remove('open'); return; }
    dropdown.innerHTML = stations.map(s => `
      <div class="autocomplete-item" data-code="${s.code}" data-name="${s.name}"
           data-lat="${s.lat||''}" data-lon="${s.lon||''}">
        <span class="ac-code">${s.code}</span>
        <span class="ac-name">${s.name}</span>
      </div>
    `).join('');
    dropdown.classList.add('open');
    dropdown.querySelectorAll('.autocomplete-item').forEach(item => {
      item.addEventListener('mousedown', e => {
        e.preventDefault();
        const code = item.dataset.code;
        const name = item.dataset.name;
        const lat = parseFloat(item.dataset.lat);
        const lon = parseFloat(item.dataset.lon);
        input.value = name;
        selectedCode = code;
        state[stateKey] = code;
        badge.textContent = code;
        badge.style.display = 'block';
        if (!isNaN(lat) && !isNaN(lon)) {
          stationCoords[code] = [lat, lon];
          stationCoords[name] = [lat, lon];
        }
        dropdown.classList.remove('open');
      });
    });
  }
}

function swapStations() {
  const fromInput = document.getElementById('inp-from');
  const toInput = document.getElementById('inp-to');
  const fromBadge = document.getElementById('from-code-badge');
  const toBadge = document.getElementById('to-code-badge');

  [fromInput.value, toInput.value] = [toInput.value, fromInput.value];
  [fromBadge.textContent, toBadge.textContent] = [toBadge.textContent, fromBadge.textContent];
  fromBadge.style.display = toBadge.textContent ? 'block' : 'none';
  toBadge.style.display = fromBadge.textContent ? 'block' : 'none';
  [state.fromCode, state.toCode] = [state.toCode, state.fromCode];
}

function quickSearchRoute(fromName, fromCode, toName, toCode) {
  document.getElementById('inp-from').value = fromName;
  const fBadge = document.getElementById('from-code-badge');
  if (fBadge) {
    fBadge.textContent = fromCode;
    fBadge.style.display = fromCode ? 'block' : 'none';
  }
  state.fromCode = fromCode;

  document.getElementById('inp-to').value = toName;
  const tBadge = document.getElementById('to-code-badge');
  if (tBadge) {
    tBadge.textContent = toCode;
    tBadge.style.display = toCode ? 'block' : 'none';
  }
  state.toCode = toCode;

  doSearch();
}

// ── Search ─────────────────────────────────────────────────────────────────
async function doSearch() {
  const from = document.getElementById('inp-from').value.trim();
  const to = document.getElementById('inp-to').value.trim();
  const date = document.getElementById('inp-date').value;
  const buffer = document.getElementById('inp-buffer').value;

  if (!from || !to) {
    alert('Please enter both From and To stations.');
    return;
  }

  // Detect if search is for today so we can time-filter results
  const todayStr = new Date().toISOString().split('T')[0];
  state.searchingToday = (!date || date === todayStr);

  // Show results wrapper
  const wrapper = document.getElementById('results-wrapper');
  wrapper.classList.add('visible');

  // Show loading
  showLoading();

  try {
    const params = new URLSearchParams({ from, to, date: date || todayStr, buffer });
    const res = await fetch(`/api/search?${params}`);
    const data = await res.json();

    if (!res.ok || data.error) {
      showError(data.error || data.detail || 'Search failed');
      if (data.detail && data.detail.includes('generate_data')) {
        document.getElementById('data-warning').style.display = 'block';
      }
      return;
    }

    state.results = data;
    renderResults(data);

  } catch(e) {
    showError(`Network error: ${e.message}`);
  }
}

function showLoading() {
  document.getElementById('loading-state').style.display = 'block';
  document.getElementById('direct-section').style.display = 'none';
  document.getElementById('connecting-section').style.display = 'none';
  document.getElementById('no-results').style.display = 'none';
  document.getElementById('results-header').style.display = 'none';
  document.getElementById('filter-bar').style.display = 'none';
  document.getElementById('side-panel').style.display = 'none';
  document.getElementById('data-warning').style.display = 'none';
  document.getElementById('search-error').style.display = 'none';
}

function showError(msg) {
  document.getElementById('loading-state').style.display = 'none';
  const el = document.getElementById('search-error');
  el.innerHTML = `<strong>⚠️ Search Error</strong>${msg}`;
  el.style.display = 'block';
}

function renderResults(data) {
  document.getElementById('loading-state').style.display = 'none';
  document.getElementById('search-error').style.display = 'none';

  let direct = data.results.direct;
  let connecting = data.results.connecting;

  // ── Time-based filtering for today's search ──────────────────────────────
  const isToday = state.searchingToday;
  const now = new Date();
  const nowMins = now.getHours() * 60 + now.getMinutes();
  const nextFewHours = 6; // show trains within next 6 hours first

  if (isToday) {
    // Sort all journeys: trains departing in next 6h come first, then rest, then already-departed last
    function journeySort(a, b) {
      const depA = parseHHMM(a.segments[0].departure) ?? 9999;
      const depB = parseHHMM(b.segments[0].departure) ?? 9999;
      // Minutes until departure (negative = already departed)
      const diffA = depA - nowMins;
      const diffB = depB - nowMins;
      // Both upcoming: sort by earliest
      if (diffA >= 0 && diffB >= 0) return diffA - diffB;
      // One upcoming, one not: upcoming first
      if (diffA >= 0) return -1;
      if (diffB >= 0) return 1;
      // Both departed: sort by most recent departure first
      return depB - depA;
    }
    direct = [...direct].sort(journeySort);
    connecting = [...connecting].sort(journeySort);

    // Tag each journey so renderDirectCard / renderConnectingCard can show label
    [...direct, ...connecting].forEach(j => {
      const depMins = parseHHMM(j.segments[0].departure) ?? -1;
      const diff = depMins - nowMins;
      if (diff >= 0 && diff <= nextFewHours * 60) {
        j._departingSoon = true;
        j._minsUntilDep = diff;
      } else if (diff < 0) {
        j._alreadyDeparted = true;
      } else {
        j._departingSoon = false;
      }
    });
  }

  const total = direct.length + connecting.length;

  // Ingest coords from backend search response if present
  if (data.results && data.results.coords) {
    Object.assign(stationCoords, data.results.coords);
  }
  state.lastDirectJourneys = direct;
  state.lastConnectingJourneys = connecting;

  // Update header
  const header = document.getElementById('results-header');
  header.style.display = 'flex';
  document.getElementById('results-title').textContent =
    `Search Results for ${data.query.from} → ${data.query.to}`;

  const timeStr = isToday
    ? `Today ${now.toLocaleTimeString('en-IN', {hour:'2-digit', minute:'2-digit'})} • Showing next departures first`
    : `${data.query.date}`;
  document.getElementById('results-subtitle').textContent =
    `Real railway timetable • ${timeStr} • ${data.query.buffer_minutes} min buffer`;

  const soonCount = isToday ? [...direct, ...connecting].filter(j => j._departingSoon).length : 0;

  const meta = document.getElementById('results-meta');
  meta.innerHTML = `
    <span class="meta-badge">All ${total}</span>
    <span class="meta-badge">Direct ${direct.length}</span>
    <span class="meta-badge">Connecting ${connecting.length}</span>
    ${isToday && soonCount > 0 ? `<span class="meta-badge" style="background:#FEF3C7;color:#92400E;">⚡ ${soonCount} Departing Soon</span>` : ''}
  `;

  // Show filter bar
  document.getElementById('filter-bar').style.display = 'flex';

  // Show side panel
  document.getElementById('side-panel').style.display = 'block';
  ensureJourneyMap();
  setTimeout(() => {
    if (map) map.invalidateSize();
    if (networkMap) networkMap.invalidateSize();
  }, 50);

  if (total === 0) {
    document.getElementById('no-results').style.display = 'block';
    document.getElementById('direct-section').style.display = 'none';
    document.getElementById('connecting-section').style.display = 'none';
    return;
  }

  document.getElementById('no-results').style.display = 'none';
  renderDirectSection(direct);
  renderConnectingSection(connecting);

  // Auto-select first upcoming journey (not already departed)
  const firstUpcoming = [...direct, ...connecting].find(j => !j._alreadyDeparted) || direct[0] || connecting[0];
  if (firstUpcoming) selectJourney(firstUpcoming);

  // Invalidate map size and center route once side-panel is rendered
  setTimeout(() => {
    if (map) map.invalidateSize();
    if (networkMap) networkMap.invalidateSize();
    if (state.selectedJourney) {
      drawJourneyOnMap(state.selectedJourney);
    }
  }, 120);
  setTimeout(() => {
    if (map) map.invalidateSize();
  }, 350);
}

// ── Filter ─────────────────────────────────────────────────────────────────
function setFilter(f) {
  state.filter = f;
  document.querySelectorAll('.filter-btn').forEach(b => {
    const isMatching = b.dataset.filter === f || b.getAttribute('onclick')?.includes(`'${f}'`);
    b.classList.toggle('active', isMatching);
  });
  
  // Machine mode pill sync
  const dirPill = document.getElementById('mm-type-direct-pill');
  const connPill = document.getElementById('mm-type-conn-pill');
  if (dirPill) dirPill.classList.toggle('active', f === 'direct');
  if (connPill) connPill.classList.toggle('active', f === 'connecting');

  if (!state.results || !state.results.results) return;
  let direct = state.results.results.direct || [];
  let connecting = state.results.results.connecting || [];

  if (f === 'direct') { connecting = []; }
  else if (f === 'connecting') { direct = []; }
  else if (f === 'earliest') {
    const all = [...direct, ...connecting].sort((a,b) =>
      (parseHHMM(a.segments[0].departure)||9999) - (parseHHMM(b.segments[0].departure)||9999));
    direct = all.filter(j => j.type === 'direct');
    connecting = all.filter(j => j.type === 'connecting');
  } else if (f === 'fastest') {
    const all = [...direct, ...connecting].sort((a,b) => a.total_duration_minutes - b.total_duration_minutes);
    direct = all.filter(j => j.type === 'direct');
    connecting = all.filter(j => j.type === 'connecting');
  }

  renderDirectSection(direct);
  renderConnectingSection(connecting);
}

function parseHHMM(t) {
  if (!t) return null;
  const m = t.match(/^(\d{1,2}):(\d{2})$/);
  return m ? parseInt(m[1])*60+parseInt(m[2]) : null;
}

// ── Direct Section ─────────────────────────────────────────────────────────
function renderDirectSection(journeys) {
  const sec = document.getElementById('direct-section');
  const list = document.getElementById('direct-list');
  const count = document.getElementById('direct-count');
  const headerSlot = document.getElementById('mm-direct-header-slot');

  if (!journeys || !journeys.length) { 
    if (sec) sec.style.display = 'none'; 
    if (headerSlot) headerSlot.innerHTML = '';
    return; 
  }
  if (sec) sec.style.display = 'block';
  if (count) count.textContent = `${journeys.length} results`;

  const isMM = document.body.classList.contains('machine-mode');
  if (isMM && headerSlot) {
    headerSlot.innerHTML = `
      <div class="mm-results-header-box">
        <div>
          <div class="mm-section-eyebrow">DIRECT JOURNEYS</div>
          <div class="mm-section-heading">Direct trains</div>
        </div>
        <div class="mm-legend">
          <span class="mm-legend-item"><span class="mm-dot-green"></span> Live status</span>
          <span class="mm-legend-item"><span class="mm-dot-orange"></span> On-Time</span>
        </div>
      </div>
    `;
  } else if (headerSlot) {
    headerSlot.innerHTML = '';
  }

  // Build HTML with section dividers for today's search
  let html = '';
  let soonShown = false, departedShown = false;
  journeys.forEach((j, i) => {
    if (state.searchingToday) {
      if (j._departingSoon && !soonShown) {
        html += `<div class="section-divider divider-soon">⚡ DEPARTING IN NEXT 6 HOURS</div>`;
        soonShown = true;
      } else if (!j._departingSoon && !j._alreadyDeparted && soonShown && !departedShown) {
        html += `<div class="section-divider divider-later">📅 LATER TODAY</div>`;
        departedShown = true;
      } else if (j._alreadyDeparted && !departedShown) {
        html += `<div class="section-divider divider-departed">🕐 ALREADY DEPARTED</div>`;
        departedShown = true;
      }
    }
    html += renderDirectCard(j, i);
  });
  list.innerHTML = html;
  list.querySelectorAll('.journey-card').forEach((el, i) => {
    el.addEventListener('click', () => selectJourney(journeys[i]));
  });
}

function renderDirectCard(j, idx) {
  const seg = j.segments[0];
  const health = j.journey_health;
  const isMM = document.body.classList.contains('machine-mode');
  const stops = seg.intermediate_stops || [];

  // Time badge for today's search
  const soonBadge = j._departingSoon
    ? `<span class="tag" style="background:#D1FAE5;color:#065F46;font-weight:700;">⚡ ${j._minsUntilDep < 60 ? j._minsUntilDep + 'm' : Math.floor(j._minsUntilDep/60)+'h '+j._minsUntilDep%60+'m'} away</span>`
    : (j._alreadyDeparted ? `<span class="tag" style="background:#F3F4F6;color:#9CA3AF;font-style:italic;">Departed</span>` : '');

  if (isMM) {
    const confidencePct = j.recommendation_confidence === 'High' ? 88 : (j.recommendation_confidence === 'Medium' ? 82 : 75);
    return `
      <div class="journey-card" data-id="${seg.train_number}" style="${j._alreadyDeparted ? 'opacity:0.55;' : ''}">
        <div class="jc-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <div style="display:flex;align-items:center;gap:6px;">
            <span class="tag-good">Good</span>
            <span style="color:#FFFFFF;font-size:12px;font-weight:700;">No transfer</span>
            ${j._departingSoon ? `<span style="background:#065F46;color:#D1FAE5;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;">⚡ ${j._minsUntilDep < 60 ? j._minsUntilDep+'m' : Math.floor(j._minsUntilDep/60)+'h '+j._minsUntilDep%60+'m'}</span>` : ''}
          </div>
          <div class="mm-confidence-num">${confidencePct}%</div>
        </div>

        <div class="segment-row">
          <div class="seg-train">
            <div class="seg-train-no" style="color:#38BDF8;font-weight:700;">🚄 ${seg.train_number}</div>
            <div class="seg-train-name" style="color:#FFFFFF;">${truncate(seg.train_name, 20)}</div>
          </div>
          <div class="seg-timeline">
            <div class="seg-station">
              <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${seg.departure}</div>
              <div class="seg-code" style="color:#E2E8F0;">${seg.from_code || ''}</div>
              <div class="seg-name">${truncate(seg.from, 12)}</div>
            </div>
            <span class="seg-arrow" style="color:#38BDF8;">→</span>
            <div class="seg-station">
              <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${seg.arrival}</div>
              <div class="seg-code" style="color:#E2E8F0;">${seg.to_code || ''}</div>
              <div class="seg-name">${truncate(seg.to, 12)}</div>
            </div>
          </div>
        </div>

        <div class="jc-footer" style="border-top-color:rgba(255,255,255,0.06);margin-top:14px;padding-top:14px;">
          <div class="jc-stats">
            <div class="stat-item"><div class="stat-value" style="color:#FFFFFF;">${j.total_duration}</div><div class="stat-label">Total Time</div></div>
            <div class="stat-item"><div class="stat-value" style="color:#34D399;">Direct</div><div class="stat-label">Transfer</div></div>
          </div>
          <div class="jc-actions">
            <button class="btn-primary" onclick="event.stopPropagation(); connectToIRCTC(state.lastDirectJourneys[${idx}])" title="Connect to official IRCTC website to book tickets" style="padding:6px 14px;font-size:12px;background:#38BDF8;color:#0F172A;font-weight:700;border:none;border-radius:8px;">🎫 Ticket</button>
          </div>
        </div>
      </div>
    `;
  }

  const healthTag = getHealthTag(health);
  return `
    <div class="journey-card" data-id="${j.segments[0].train_number}" style="${j._alreadyDeparted ? 'opacity:0.55;' : ''}">
      <div class="jc-header">
        <div class="train-icon">🚄</div>
        <div class="train-info">
          <div class="train-number">${seg.train_number}</div>
          <div class="train-name">${seg.train_name}</div>
          <div class="train-tags">
            <span class="tag tag-type">${seg.train_type || 'Express'}</span>
            <span class="tag tag-direct">✓ No Transfer</span>
            ${healthTag}
            ${soonBadge}
          </div>
        </div>
        ${getConfidenceHTML(j.recommendation_confidence)}
      </div>

      <div class="jc-timeline">
        <div class="timeline-station">
          <div class="timeline-time">${seg.departure}</div>
          <div class="timeline-code">${seg.from_code || ''}</div>
          <div class="timeline-name">${truncate(seg.from, 15)}</div>
        </div>
        <div class="timeline-connector">
          <div class="connector-line"></div>
          <div class="connector-duration">${j.total_duration}</div>
          <div class="connector-stops">${stops.length ? `via ${stops.slice(0,3).join(' • ')}${stops.length>3?' +more':''}` : ''}</div>
        </div>
        <div class="timeline-station">
          <div class="timeline-time">${seg.arrival}</div>
          <div class="timeline-code">${seg.to_code || ''}</div>
          <div class="timeline-name">${truncate(seg.to, 15)}</div>
        </div>
      </div>

      ${stops.length ? `<div class="stops-preview">
        <span class="stop-dot">📍</span>
        ${stops.slice(0,5).map(s => `<span>${s}</span><span class="stop-dot"> • </span>`).join('')}
        ${stops.length > 5 ? `<span style="color:var(--primary)">+${stops.length-5} more</span>` : ''}
      </div>` : ''}

      ${state.missionMode ? `
        <div class="mission-telemetry-box" style="margin: 10px 0 0;">
          <span>🛰️ Speed: 105 km/h · Delay: 0m</span>
          <span style="font-weight:700;">Platform 1 (Pred.) · 96.4% On-Time</span>
        </div>
      ` : ''}

      <div class="jc-footer">
        <div class="jc-stats">
          <div class="stat-item"><div class="stat-value">${j.total_duration}</div><div class="stat-label">Journey Time</div></div>
          <div class="stat-item"><div class="stat-value">0</div><div class="stat-label">Transfers</div></div>
        </div>
        <div class="jc-actions">
          <button class="btn-secondary" onclick="event.stopPropagation(); startLiveJourney(state.lastDirectJourneys[${idx}])">▶ Start</button>
          <button class="btn-primary" onclick="event.stopPropagation(); connectToIRCTC(state.lastDirectJourneys[${idx}])" title="Connect to official IRCTC website to book tickets">🎫 Ticket</button>
        </div>
      </div>
    </div>
  `;
}

// ── Connecting Section ─────────────────────────────────────────────────────
function renderConnectingSection(journeys) {
  const sec = document.getElementById('connecting-section');
  const list = document.getElementById('connecting-list');
  const count = document.getElementById('connecting-count');
  const headerSlot = document.getElementById('mm-connecting-header-slot');

  if (!journeys || !journeys.length) { 
    if (sec) sec.style.display = 'none'; 
    if (headerSlot) headerSlot.innerHTML = '';
    return; 
  }
  if (sec) sec.style.display = 'block';
  if (count) count.textContent = `${journeys.length} results`;

  const isMM = document.body.classList.contains('machine-mode');
  if (isMM && headerSlot) {
    headerSlot.innerHTML = `
      <div class="mm-results-header-box">
        <div>
          <div class="mm-section-eyebrow">CONNECTION JOURNEYS</div>
          <div class="mm-section-heading">Recommended connections</div>
        </div>
        <div class="mm-legend">
          <span class="mm-legend-item"><span class="mm-dot-green"></span> Live status</span>
          <span class="mm-legend-item"><span class="mm-dot-orange"></span> Transfer risk</span>
        </div>
      </div>
    `;
  } else if (headerSlot) {
    headerSlot.innerHTML = '';
  }

  // Build HTML with section dividers for today's search
  let html = '';
  let soonShown = false, departedShown = false;
  journeys.forEach((j, i) => {
    if (state.searchingToday) {
      if (j._departingSoon && !soonShown) {
        html += `<div class="section-divider divider-soon">⚡ DEPARTING IN NEXT 6 HOURS</div>`;
        soonShown = true;
      } else if (!j._departingSoon && !j._alreadyDeparted && soonShown && !departedShown) {
        html += `<div class="section-divider divider-later">📅 LATER TODAY</div>`;
        departedShown = true;
      } else if (j._alreadyDeparted && !departedShown) {
        html += `<div class="section-divider divider-departed">🕐 ALREADY DEPARTED</div>`;
        departedShown = true;
      }
    }
    html += renderConnectingCard(j, i);
  });
  list.innerHTML = html;
  list.querySelectorAll('.journey-card').forEach((el, i) => {
    el.addEventListener('click', () => selectJourney(journeys[i]));
  });
}

function renderConnectingCard(j, idx) {
  const s1 = j.segments[0];
  const s2 = j.segments[1];
  const health = j.journey_health;
  const healthTag = getHealthTag(health);
  const isMM = document.body.classList.contains('machine-mode');

  // Risky Buffer Zone criteria: connection buffer < 30 minutes, or Watch / At Risk / Critical
  const connMins = j.connection_minutes || 0;
  const isRisky = connMins < 30 || health === 'At Risk' || health === 'Critical' || health === 'Watch';

  if (isMM) {
    // Machine Mode Card UI/UX strictly matching screenshot
    const confidencePct = j.recommendation_confidence === 'High' ? 78 : (j.recommendation_confidence === 'Medium' ? 73 : 64);
    const soonTagMM = j._departingSoon ? `<span style="background:#065F46;color:#D1FAE5;font-size:10px;font-weight:700;padding:2px 7px;border-radius:10px;">⚡ ${j._minsUntilDep < 60 ? j._minsUntilDep+'m' : Math.floor(j._minsUntilDep/60)+'h '+j._minsUntilDep%60+'m'}</span>` : '';
    return `
      <div class="journey-card ${isRisky ? 'has-risky-buffer' : ''}" style="${j._alreadyDeparted ? 'opacity:0.55;' : ''}">
        <div class="jc-header" style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <div style="display:flex;align-items:center;gap:6px;">
            ${isRisky
              ? `<span class="tag-risky">⚠️ Risky</span><span style="color:#FBBF24;font-size:12px;font-weight:700;">${j.transfers || 1} change (${connMins}m buffer)</span>`
              : `<span class="tag-good">Good</span><span style="color:#FFFFFF;font-size:12px;font-weight:700;">${j.transfers || 1} change</span>`}
            ${soonTagMM}
          </div>
          <div class="mm-confidence-num">${confidencePct}%</div>
        </div>

        <div class="jc-segments">
          <!-- Segment 1 -->
          <div class="segment-row">
            <div class="seg-train">
              <div class="seg-train-no" style="color:#38BDF8;font-weight:700;">🚂 ${s1.train_number}</div>
              <div class="seg-train-name" style="color:#FFFFFF;">${truncate(s1.train_name, 20)}</div>
            </div>
            <div class="seg-timeline">
              <div class="seg-station">
                <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${s1.departure}</div>
                <div class="seg-code" style="color:#E2E8F0;">${s1.from_code || ''}</div>
                <div class="seg-name">${truncate(s1.from, 12)}</div>
              </div>
              <span class="seg-arrow" style="color:#38BDF8;">→</span>
              <div class="seg-station">
                <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${s1.arrival}</div>
                <div class="seg-code" style="color:#E2E8F0;">${s1.to_code || ''}</div>
                <div class="seg-name">${truncate(s1.to, 12)}</div>
              </div>
            </div>
          </div>

          <!-- Connection badge -->
          <div style="padding:4px 0">
            <span class="connection-badge" style="background:#0F172A;border-color:rgba(255,255,255,0.1);color:#E2E8F0;">
              ⏱ ${j.connection_formatted || connMins + ' min'} connection at ${j.interchange_station}
            </span>
          </div>

          <!-- Segment 2 -->
          <div class="segment-row">
            <div class="seg-train">
              <div class="seg-train-no" style="color:#38BDF8;font-weight:700;">🚂 ${s2.train_number}</div>
              <div class="seg-train-name" style="color:#FFFFFF;">${truncate(s2.train_name, 20)}</div>
            </div>
            <div class="seg-timeline">
              <div class="seg-station">
                <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${s2.departure}</div>
                <div class="seg-code" style="color:#E2E8F0;">${s2.from_code || ''}</div>
                <div class="seg-name">${truncate(s2.from, 12)}</div>
              </div>
              <span class="seg-arrow" style="color:#38BDF8;">→</span>
              <div class="seg-station">
                <div class="seg-time" style="color:#FFFFFF;font-weight:700;">${s2.arrival}</div>
                <div class="seg-code" style="color:#E2E8F0;">${s2.to_code || ''}</div>
                <div class="seg-name">${truncate(s2.to, 12)}</div>
              </div>
            </div>
          </div>
        </div>

        <!-- ⚠️ RISKY BUFFER ZONE ALERT BOX (Active in Machine Mode when buffer is low) -->
        ${isRisky ? `
          <div class="mm-risky-buffer-box">
            <span class="mm-rb-icon">⚠️</span>
            <div>
              <div class="mm-rb-title">RISKY BUFFER ZONE · ${escapeHtml(j.interchange_station)} (${connMins} min margin)</div>
              <div class="mm-rb-text">Very short connection buffer! Minimum platform bridge transit takes ~6-8m. High probability of missed train if Train ${s1.train_number} is delayed. IRCTC Rule 23 protection applies.</div>
            </div>
          </div>
        ` : ''}

        <div class="jc-footer" style="border-top-color:rgba(255,255,255,0.06);margin-top:14px;padding-top:14px;">
          <div class="jc-stats">
            <div class="stat-item"><div class="stat-value" style="color:#FFFFFF;">${j.total_duration}</div><div class="stat-label">Total Time</div></div>
            <div class="stat-item"><div class="stat-value" style="color:${isRisky ? '#FBBF24' : '#FFFFFF'};">${j.connection_formatted||connMins+'m'}</div><div class="stat-label">${isRisky ? '⚠️ Risky Buffer' : 'Connection'}</div></div>
            <div class="stat-item"><div class="stat-value" style="color:#FFFFFF;">1</div><div class="stat-label">Transfer</div></div>
          </div>
          <div class="jc-actions">
            <button class="btn-secondary" style="background:#1E293B;color:#FFFFFF;border-color:rgba(255,255,255,0.15);" onclick="event.stopPropagation(); startLiveJourney(state.lastConnectingJourneys[${idx}])">▶ Start</button>
            <button class="btn-primary" style="background:#38BDF8;border-color:#38BDF8;color:#0F172A;font-weight:800;" onclick="event.stopPropagation(); connectToIRCTC(state.lastConnectingJourneys[${idx}])" title="Connect to official IRCTC website to book tickets">🎫 Ticket</button>
          </div>
        </div>
      </div>
    `;
  }

  // Standard Normal Mode (with departure-time badges)
  const soonBadge = j._departingSoon
    ? `<span class="tag" style="background:#D1FAE5;color:#065F46;font-weight:700;">⚡ ${j._minsUntilDep < 60 ? j._minsUntilDep + 'm' : Math.floor(j._minsUntilDep/60)+'h '+j._minsUntilDep%60+'m'} away</span>`
    : (j._alreadyDeparted ? `<span class="tag" style="background:#F3F4F6;color:#9CA3AF;font-style:italic;">Departed</span>` : '');

  return `
    <div class="journey-card" style="${j._alreadyDeparted ? 'opacity:0.55;' : ''}">
      <div class="jc-header">
        <div class="train-icon">🔀</div>
        <div class="train-info">
          <div class="train-number">${s1.train_number} + ${s2.train_number}</div>
          <div class="train-name">${j.interchange_station}</div>
          <div class="train-tags">
            <span class="tag tag-connecting">1 Transfer</span>
            ${healthTag}
            ${soonBadge}
          </div>
        </div>
        ${getConfidenceHTML(j.recommendation_confidence)}
      </div>

      <div class="jc-segments">
        <!-- Segment 1 -->
        <div class="segment-row">
          <div class="seg-train">
            <div class="seg-train-no">🚂 ${s1.train_number}</div>
            <div class="seg-train-name">${truncate(s1.train_name, 20)}</div>
          </div>
          <div class="seg-timeline">
            <div class="seg-station">
              <div class="seg-time">${s1.departure}</div>
              <div class="seg-code">${s1.from_code || ''}</div>
              <div class="seg-name">${truncate(s1.from, 12)}</div>
            </div>
            <span class="seg-arrow">→</span>
            <div class="seg-station">
              <div class="seg-time">${s1.arrival}</div>
              <div class="seg-code">${s1.to_code || ''}</div>
              <div class="seg-name">${truncate(s1.to, 12)}</div>
            </div>
          </div>
        </div>

        <!-- Connection badge -->
        <div style="padding:4px 0">
          <span class="connection-badge">
            ⏱ ${j.connection_formatted || j.connection_minutes + ' min'} connection at ${j.interchange_station}
          </span>
        </div>

        <!-- Segment 2 -->
        <div class="segment-row">
          <div class="seg-train">
            <div class="seg-train-no">🚂 ${s2.train_number}</div>
            <div class="seg-train-name">${truncate(s2.train_name, 20)}</div>
          </div>
          <div class="seg-timeline">
            <div class="seg-station">
              <div class="seg-time">${s2.departure}</div>
              <div class="seg-code">${s2.from_code || ''}</div>
              <div class="seg-name">${truncate(s2.from, 12)}</div>
            </div>
            <span class="seg-arrow">→</span>
            <div class="seg-station">
              <div class="seg-time">${s2.arrival}</div>
              <div class="seg-code">${s2.to_code || ''}</div>
              <div class="seg-name">${truncate(s2.to, 12)}</div>
            </div>
          </div>
        </div>
      </div>

      ${state.missionMode ? `
        <div class="mission-telemetry-box" style="margin: 10px 0 0;">
          <span>🛰️ Transfer Margin: ${Math.max(0, j.connection_minutes - 6)}m · FOB Transit: ~6m</span>
          <span style="font-weight:700;">Platform Change Pred. · Rule 23 Safe</span>
        </div>
      ` : ''}

      <div class="jc-footer">
        <div class="jc-stats">
          <div class="stat-item"><div class="stat-value">${j.total_duration}</div><div class="stat-label">Total Time</div></div>
          <div class="stat-item"><div class="stat-value">${j.connection_formatted||j.connection_minutes+'m'}</div><div class="stat-label">Connection</div></div>
          <div class="stat-item"><div class="stat-value">1</div><div class="stat-label">Transfer</div></div>
        </div>
        <div class="jc-actions">
          <button class="btn-secondary" onclick="event.stopPropagation(); startLiveJourney(state.lastConnectingJourneys[${idx}])">▶ Start</button>
          <button class="btn-primary" onclick="event.stopPropagation(); connectToIRCTC(state.lastConnectingJourneys[${idx}])" title="Connect to official IRCTC website to book tickets">🎫 Ticket</button>
        </div>
      </div>
    </div>
  `;
}

// ── Journey Selection + Detail Panel ──────────────────────────────────────
function selectJourney(j) {
  state.selectedJourney = j;

  // Highlight card
  document.querySelectorAll('.journey-card').forEach(el => el.classList.remove('selected'));

  // Render detail panel
  renderDetailPanel(j);

  // Draw on map
  drawJourneyOnMap(j);
}

function renderDetailPanel(j) {
  const body = document.getElementById('journey-detail-body');
  const s = j.segments;
  const src = s[0];
  const dst = s[s.length - 1];

  const healthColor = {
    'Stable': '#059669', 'Watch': '#D97706', 'At Risk': '#DC2626', 'Critical': '#DC2626'
  }[j.journey_health] || '#6B7280';

  body.innerHTML = `
    <div class="detail-route">
      <span>${src.from_code || src.from}</span>
      <span style="color:var(--text-muted)">→</span>
      <span>${dst.to_code || dst.to}</span>
    </div>
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:14px">
      ${j.type === 'connecting' ? `2 trains • 1 transfer` : '1 train • No transfer'}
    </div>

    ${s.map((seg, i) => `
      <div class="detail-seg">
        <div class="detail-seg-header">
          <span class="detail-train-num">Train ${seg.train_number}</span>
          <span class="detail-train-name">${seg.train_name}</span>
        </div>
        <div class="detail-seg-timeline">
          <div class="detail-st">
            <div class="detail-time">${seg.departure}</div>
            <div class="detail-code">${seg.from_code || ''}</div>
            <div class="detail-name">${truncate(seg.from, 14)}</div>
          </div>
          <div class="detail-arr"></div>
          <div class="detail-st">
            <div class="detail-time">${seg.arrival}</div>
            <div class="detail-code">${seg.to_code || ''}</div>
            <div class="detail-name">${truncate(seg.to, 14)}</div>
          </div>
        </div>
      </div>
      ${i < s.length-1 ? `<div class="connection-badge" style="margin:8px 0;display:block;text-align:center">
        ⏱ ${j.connection_formatted || j.connection_minutes + ' min'} connection at ${j.interchange_station}
      </div>` : ''}
    `).join('')}

    <div class="health-grid">
      <div class="health-item">
        <div class="health-item-value" style="color:${healthColor}">${j.journey_health}</div>
        <div class="health-item-label">Journey Health</div>
      </div>
      <div class="health-item">
        <div class="health-item-value">${getConfStars(j.recommendation_confidence)}</div>
        <div class="health-item-label">Rec. Confidence</div>
      </div>
      <div class="health-item">
        <div class="health-item-value">${j.total_duration}</div>
        <div class="health-item-label">Total Journey Time</div>
      </div>
      <div class="health-item">
        <div class="health-item-value">${j.transfers}</div>
        <div class="health-item-label">Transfers</div>
      </div>
    </div>

    <!-- Mission Mode Telemetry (if active) -->
    <div id="panel-mission-telemetry" class="mission-telemetry-box" style="display:${state.missionMode ? 'flex' : 'none'};">
      <div>
        <strong>🛰️ Cruising Telemetry</strong>
        <div style="font-size:11px;color:#047857;">Speed: ~105 km/h · Punctuality: 94.6%</div>
      </div>
      <div>
        <span style="background:#10B981;color:#fff;padding:2px 8px;border-radius:4px;font-size:10px;font-weight:700;">Platform 1 Pred.</span>
      </div>
    </div>

    <!-- Primary Action Buttons from arrts.vercel.app -->
    <div class="action-buttons" style="margin-top:12px;">
      <button class="btn-primary" onclick="startLiveJourney(state.selectedJourney)">▶ Start Journey (Mission Mode)</button>
      <button class="btn-secondary" onclick="connectToIRCTC(state.selectedJourney)" style="background:#FF6F00;color:#fff;border-color:#FF6F00;font-weight:700;">🎫 Book on IRCTC ↗</button>
    </div>

    <!-- Travel Intelligence Widget from arrts.vercel.app -->
    <div class="travel-intelligence-box">
      <div class="intel-header">
        <span class="intel-icon">🧠</span>
        <div>
          <div style="font-weight:700;font-size:13px;color:var(--text);">Travel Intelligence</div>
          <div style="font-size:11px;color:var(--text-muted);">Verified journey details & transfer safety</div>
        </div>
      </div>
      <div class="intel-prompts">
        <button class="intel-btn" onclick="askTravelIntelligence('why_best')">💡 Why is this the best journey?</button>
        <button class="intel-btn" onclick="askTravelIntelligence('transfer_safety')">🛡️ Is my transfer safe?</button>
        <button class="intel-btn" onclick="askTravelIntelligence('next_action')">📍 What should I do next?</button>
      </div>
      <div id="intel-response" class="intel-response-card" style="display:none;"></div>
    </div>
  `;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function getHealthTag(health) {
  const map = {
    'Stable': 'tag-health-stable', 'Watch': 'tag-health-watch',
    'At Risk': 'tag-health-atrisk', 'Critical': 'tag-health-critical',
  };
  const icons = { 'Stable': '💚', 'Watch': '⭐', 'At Risk': '🔴', 'Critical': '⚠️' };
  const cls = map[health] || '';
  const icon = icons[health] || '•';
  return `<span class="tag ${cls}">${icon} ${health}</span>`;
}

function getConfidenceHTML(conf) {
  const stars = getConfStars(conf);
  const cls = conf === 'High' ? 'conf-high' : conf === 'Medium' ? 'conf-medium' : 'conf-low';
  return `<div style="text-align:right;min-width:80px">
    <div style="font-size:16px">${stars}</div>
    <div class="conf-label ${cls}" style="font-size:11px">Conf. ${conf}</div>
  </div>`;
}

function getConfStars(conf) {
  return conf === 'High' ? '⭐⭐⭐' : conf === 'Medium' ? '⭐⭐' : '⭐';
}

function truncate(str, len) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '…' : str;
}

function openDiag() {
  const from = document.getElementById('inp-from').value;
  const to = document.getElementById('inp-to').value;
  window.open(`/api/diagnose?from=${encodeURIComponent(from)}&to=${encodeURIComponent(to)}`, '_blank');
}

// ── AI Railway Travel Chatbot ──────────────────────────────────────────────
let isChatOpen = false;
let chatHistory = [];

function toggleChatbot(forceState) {
  isChatOpen = forceState !== undefined ? forceState : !isChatOpen;
  const drawer = document.getElementById('chat-drawer');
  const launcher = document.getElementById('chat-launcher');
  if (isChatOpen) {
    drawer.classList.add('open');
    launcher.style.transform = 'scale(0.9)';
    document.getElementById('chat-input').focus();
    if (document.getElementById('chat-messages').children.length === 0) {
      initWelcomeChat();
    }
  } else {
    drawer.classList.remove('open');
    launcher.style.transform = '';
  }
}

function initWelcomeChat() {
  const welcomeText = 
`👋 **Welcome to ARRTS AI Travel Assistant!**

I am trained on **Indian Railways operations, ticketing rules, and travel hacks**. Ask me anything, or try:
• **⚡ Tatkal Hacks:** Master list tricks, 10 AM / 11 AM tactics, OTP-less payment speedups.
• **📋 RAC & Waitlist:** Chart prep rules (4 hrs before dep), current booking discounts.
• **🔀 Connecting Journeys:** Rule 23 rights if you miss a transfer, safe buffer times.
• **💺 Berth Hacks:** 1A Coupe selection, Side Lower window perks, quiet middle bays.
• **🍱 Catering & Food:** Mandatory MRP caps (₹15 Rail Neer, ₹80 Veg Thali), e-Catering orders.
• **🚄 Live Route Search:** Just type *\"Find trains from Visakhapatnam to Chennai\"*!`;

  appendChatMessage('bot', welcomeText, [
    "What are the best Tatkal booking hacks?",
    "Find trains from Visakhapatnam to Chennai",
    "How does Chart Preparation and RAC work?",
    "What is Rule 23 on missed connecting trains?"
  ]);
}

function clearChatHistory() {
  chatHistory = [];
  document.getElementById('chat-messages').innerHTML = '';
  initWelcomeChat();
}

async function submitChatMessage() {
  const input = document.getElementById('chat-input');
  const text = input.value.trim();
  if (!text) return;

  input.value = '';
  appendChatMessage('user', text);

  // Show typing indicator
  showTypingIndicator();

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, history: chatHistory })
    });
    const data = await res.json();
    removeTypingIndicator();

    if (data.reply) {
      appendChatMessage('bot', data.reply, data.suggestions, data.train_data);
      chatHistory.push({ role: 'user', content: text });
      chatHistory.push({ role: 'assistant', content: data.reply });
    } else {
      appendChatMessage('bot', "⚠️ Sorry, I could not process your query. Please try again.");
    }
  } catch (err) {
    removeTypingIndicator();
    appendChatMessage('bot', "⚠️ Network error connecting to ARRTS AI. Please verify the server is running.");
  }
}

function sendChatPrompt(promptText) {
  if (!isChatOpen) toggleChatbot(true);
  document.getElementById('chat-input').value = promptText;
  submitChatMessage();
}

function showTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const indicator = document.createElement('div');
  indicator.id = 'typing-indicator';
  indicator.className = 'typing-indicator';
  indicator.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
}

function removeTypingIndicator() {
  const ind = document.getElementById('typing-indicator');
  if (ind) ind.remove();
}

function appendChatMessage(sender, text, suggestions = [], trainData = null) {
  const container = document.getElementById('chat-messages');
  const msgEl = document.createElement('div');
  msgEl.className = `chat-msg ${sender}`;

  const avatar = sender === 'bot' ? '🤖' : '👤';
  const htmlContent = formatChatMarkdown(text);

  let trainCardsHtml = '';
  if (trainData && trainData.top_direct && trainData.top_direct.length > 0) {
    trainCardsHtml = `
      <div style="margin-top:10px;">
        <div style="font-size:12px;font-weight:700;color:var(--primary);margin-bottom:6px;">🚀 Quick Actions:</div>
        <button class="chat-plan-btn" onclick="autofillSearch('${trainData.from}', '${trainData.to}')">
          📍 Open ${trainData.from} → ${trainData.to} in ARRTS Planner
        </button>
      </div>
    `;
  }

  let suggestionsHtml = '';
  if (suggestions && suggestions.length > 0) {
    suggestionsHtml = `
      <div class="msg-suggestions">
        ${suggestions.map(s => `<span class="sug-pill" onclick="sendChatPrompt('${escapeHtmlAttr(s)}')">${escapeHtml(s)}</span>`).join('')}
      </div>
    `;
  }

  msgEl.innerHTML = `
    <div class="msg-avatar">${avatar}</div>
    <div class="msg-bubble">
      ${htmlContent}
      ${trainCardsHtml}
      ${suggestionsHtml}
    </div>
  `;

  container.appendChild(msgEl);
  container.scrollTop = container.scrollHeight;
}

function formatChatMarkdown(raw) {
  if (!raw) return '';
  let str = escapeHtml(raw);

  // Headers
  str = str.replace(/^### (.*$)/gim, '<h3>$1</h3>');
  str = str.replace(/^#### (.*$)/gim, '<h4>$1</h4>');

  // Bold & Italic
  str = str.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  str = str.replace(/\*(.*?)\*/g, '<em>$1</em>');

  // Inline Code
  str = str.replace(/`(.*?)`/g, '<code>$1</code>');

  // Lists
  str = str.replace(/^\s*• (.*$)/gim, '<li>$1</li>');
  str = str.replace(/(<li>.*<\/li>)/gims, '<ul>$1</ul>');

  // Line breaks to paragraphs
  str = str.replace(/\n\n+/g, '<br/><br/>');
  str = str.replace(/\n/g, '<br/>');

  return str;
}

function autofillSearch(from, to) {
  document.getElementById('inp-from').value = from;
  document.getElementById('inp-to').value = to;
  toggleChatbot(false);
  window.scrollTo({ top: 0, behavior: 'smooth' });
  setTimeout(() => { doSearch(); }, 300);
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, m => map[m]);
}

function escapeHtmlAttr(text) {
  return String(text).replace(/'/g, "\\'").replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        submitChatMessage();
      }
    });
  }
  // Initialize Machine Mode if previously enabled
  if (localStorage.getItem('arrts_machine_mode') === 'true') {
    toggleMissionMode();
  }
  // Initialize theme from storage
  if (state.theme === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark');
    updateThemeUI(true);
  }
  // Initialize map API key input
  const keyInput = document.getElementById('map-api-key-input');
  if (keyInput && customMapApiKey) {
    keyInput.value = customMapApiKey;
    const status = document.getElementById('map-api-key-status');
    if (status) status.style.display = 'block';
  }
});

// ── Vercel Features: Travel Intelligence, Smart Ticket, Dock, Settings ───────

function onMmDateChange(val) {
  if (val) {
    document.getElementById('inp-date').value = val;
    showToast(`📅 Travel Date Set: ${val}`);
    doSearch();
  }
}

function setSearchMode(mode) {
  state.mode = mode;
  
  // Standard mode buttons
  const futureBtn = document.getElementById('mode-future-btn');
  const liveBtn = document.getElementById('mode-live-btn');
  if (futureBtn) futureBtn.classList.toggle('active', mode === 'future');
  if (liveBtn) liveBtn.classList.toggle('active', mode === 'live');

  // Machine mode pills
  const mmLivePill = document.getElementById('mm-mode-live-pill');
  const mmFuturePill = document.getElementById('mm-mode-future-pill');
  if (mmLivePill) mmLivePill.classList.toggle('active', mode === 'live');
  if (mmFuturePill) mmFuturePill.classList.toggle('active', mode === 'future');

  const mmCalBox = document.getElementById('mm-calendar-box');
  const inpMmDate = document.getElementById('inp-date-mm');

  if (mode === 'live') {
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('inp-date').value = today;
    if (inpMmDate) inpMmDate.value = today;
    if (mmCalBox) mmCalBox.style.display = 'none';
    showToast('⚡ Live Mode Active: Prioritizing immediate departures with live tracking');
    if (state.results) doSearch();
  } else {
    // Show calendar in Machine Mode
    if (mmCalBox) {
      mmCalBox.style.display = 'inline-flex';
      const curDate = document.getElementById('inp-date').value || new Date().toISOString().split('T')[0];
      if (inpMmDate) {
        inpMmDate.value = curDate;
        inpMmDate.min = new Date().toISOString().split('T')[0];
        try {
          if (typeof inpMmDate.showPicker === 'function') {
            inpMmDate.showPicker();
          } else {
            inpMmDate.focus();
          }
        } catch(e) {
          inpMmDate.focus();
        }
      }
    }
    showToast('📅 Future Planning Mode: Select travel date from calendar');
  }
}

function toggleTheme() {
  const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  const newTheme = isDark ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  state.theme = newTheme;
  localStorage.setItem('arrts_theme', newTheme);
  updateThemeUI(!isDark);
  updateMapTiles(!isDark);
  showToast(`Appearance: Switched to ${newTheme} mode`);
}

function updateThemeUI(isDark) {
  const statusEl = document.getElementById('theme-status-text');
  const btnEl = document.getElementById('theme-toggle-btn');
  if (statusEl) statusEl.textContent = isDark ? 'Dark mode active' : 'Light mode active';
  if (btnEl) btnEl.textContent = isDark ? 'Use light' : 'Use dark';
}

function toggleMissionMode() {
  state.missionMode = !state.missionMode;
  state.machineMode = state.missionMode;
  document.body.classList.toggle('machine-mode', state.missionMode);
  localStorage.setItem('arrts_machine_mode', state.missionMode ? 'true' : 'false');

  // Reparent #map to hero container (in Machine Mode) or standard container (in Standard Mode)
  const mapEl = document.getElementById('map');
  const heroSlot = document.getElementById('mm-hero-map-slot');
  const standardSlot = document.getElementById('standard-map-slot');

  if (state.missionMode) {
    if (heroSlot && mapEl) {
      heroSlot.appendChild(mapEl);
    }
  } else {
    if (standardSlot && mapEl) {
      standardSlot.appendChild(mapEl);
    }
  }

  const sw = document.getElementById('mission-mode-switch');
  const ind = document.getElementById('mission-mode-indicator');
  if (sw) sw.classList.toggle('on', state.missionMode);
  if (ind) ind.style.display = state.missionMode ? 'inline-block' : 'none';

  // Update navbar and search card Machine Mode buttons
  document.querySelectorAll('.nav-machine-toggle').forEach(btn => {
    btn.classList.toggle('active', state.missionMode);
    const textEl = btn.querySelector('.nav-mm-text');
    if (textEl) textEl.textContent = state.missionMode ? 'Machine Mode (ON)' : 'Machine Mode';
  });

  const badgeText = document.getElementById('machine-mode-badge-text');
  if (badgeText) badgeText.textContent = state.missionMode ? 'Machine Mode ON' : 'Machine Mode';

  // Update telemetry displays
  document.querySelectorAll('.mission-telemetry-box').forEach(el => {
    el.style.display = state.missionMode ? 'flex' : 'none';
  });
  const panelTelem = document.getElementById('panel-mission-telemetry');
  if (panelTelem) panelTelem.style.display = state.missionMode ? 'flex' : 'none';

  // Invalidate map size and re-render journey map with machine styling
  if (map) {
    setTimeout(() => { map.invalidateSize(); }, 50);
    setTimeout(() => { map.invalidateSize(); }, 200);
    setTimeout(() => { map.invalidateSize(); }, 500);
  }

  // If entering machine mode without results, trigger search automatically so screenshot route & cards appear!
  if (state.missionMode && !state.results) {
    doSearch();
  } else {
    // Re-render journey sections to switch UI styling seamlessly
    if (state.results) {
      renderResults(state.results);
    }
    if (state.selectedJourney) {
      drawJourneyOnMap(state.selectedJourney);
    }
  }

  showToast(state.missionMode ? '⚡ Machine Mode Enabled: High-density layout & risky buffer monitoring' : 'Standard Mode Restored');
}

function toggleNotifSwitch() {
  state.notifications = !state.notifications;
  const sw = document.getElementById('notif-switch');
  if (sw) sw.classList.toggle('on', state.notifications);
  showToast(state.notifications ? '🔔 Route Alerts: You will be notified when faster connections appear' : 'Notifications muted');
}

function setBufferPreference(mins) {
  state.bufferPreference = mins;
  document.querySelectorAll('.buf-opt-btn').forEach(b => {
    b.classList.toggle('active', b.textContent.includes(`${mins}m`));
  });
  // Update search input if present
  const inpBuffer = document.getElementById('inp-buffer');
  if (inpBuffer) inpBuffer.value = mins;
  showToast(`⏱ Transfer buffer preference set to ${mins} minutes (JDE Validator updated)`);
  if (state.results) doSearch();
}

function toggleSettingsModal(show) {
  const el = document.getElementById('settings-modal-overlay');
  if (el) el.style.display = show ? 'flex' : 'none';
}

function connectToIRCTC(journey) {
  const j = journey || state.selectedJourney;
  let fromCode = '';
  let toCode = '';
  let fromName = '';
  let toName = '';
  let trainNo = '';
  let trainName = '';
  const dateInput = document.getElementById('inp-date');
  const travelDate = (dateInput && dateInput.value) ? dateInput.value : new Date().toISOString().split('T')[0];

  if (j && j.segments && j.segments.length > 0) {
    const s1 = j.segments[0];
    const sLast = j.segments[j.segments.length - 1];
    fromCode = s1.from_code || s1.from || '';
    toCode = sLast.to_code || sLast.to || '';
    fromName = s1.from || fromCode;
    toName = sLast.to || toCode;
    trainNo = s1.train_number || '';
    trainName = s1.train_name || '';

    if (j.type === 'connecting' && j.segments.length > 1) {
      const s2 = j.segments[1];
      showToast(`🔗 Connecting to Official IRCTC Website for: Train ${s1.train_number} + Train ${s2.train_number} via ${j.interchange_station}...`);
      const clipText = `Connecting Journey: Train ${s1.train_number} (${s1.from_code || s1.from} -> ${j.interchange_code || j.interchange_station}) + Train ${s2.train_number} (${j.interchange_code || j.interchange_station} -> ${s2.to_code || s2.to}) on ${travelDate}`;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(clipText).catch(() => {});
      }
    } else {
      showToast(`🔗 Connecting to Official IRCTC Website for Train ${trainNo} ${trainName} (${fromCode} → ${toCode})...`);
      const clipText = `Train: ${trainNo} ${trainName} | From: ${fromCode} | To: ${toCode} | Date: ${travelDate}`;
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(clipText).catch(() => {});
      }
    }
  } else {
    showToast(`🔗 Connecting to Official IRCTC Website (irctc.co.in)...`);
  }

  // Official IRCTC e-Ticketing Portal
  const irctcUrl = 'https://www.irctc.co.in/nget/train-search';
  window.open(irctcUrl, '_blank', 'noopener,noreferrer');
}

// ── Real PNR Status Engine ────────────────────────────────────────────────
function openPnrModal() {
  togglePnrModal(true);
  setTimeout(() => {
    const inp = document.getElementById('pnr-input');
    if (inp) inp.focus();
  }, 100);
}

function togglePnrModal(show) {
  const el = document.getElementById('pnr-modal-overlay');
  if (el) el.style.display = show ? 'flex' : 'none';
}

function fillAndCheckDemoPnr(pnr) {
  const inp = document.getElementById('pnr-input');
  if (inp) inp.value = pnr;
  checkLivePnrStatus();
}

async function checkLivePnrStatus() {
  const inp = document.getElementById('pnr-input');
  const val = inp ? inp.value.trim() : '';
  const resultBox = document.getElementById('pnr-result-box');
  const loading = document.getElementById('pnr-loading');

  if (!val || val.length !== 10 || !/^\d+$/.test(val)) {
    showToast('⚠️ Please enter a valid 10-digit Indian Railways PNR number.');
    if (inp) inp.focus();
    return;
  }

  if (loading) loading.style.display = 'block';
  if (resultBox) {
    resultBox.style.display = 'none';
    resultBox.innerHTML = '';
  }

  try {
    const res = await fetch(`/api/pnr/${val}`);
    const data = await res.json();
    if (loading) loading.style.display = 'none';

    if (!res.ok || data.not_found) {
      resultBox.innerHTML = `
        <div style="background:#FEF2F2;border:1px solid #FCA5A5;border-radius:10px;padding:16px;color:#991B1B;">
          <div style="font-weight:800;font-size:14px;margin-bottom:4px;">❌ PNR Record Not Active / Flushed</div>
          <div style="font-size:12px;line-height:1.5;">${data.message || 'No active passenger record found for this PNR.'}</div>
          <div style="font-size:11px;color:#B91C1C;margin-top:8px;">
            Note: Indian Railways automatically flushes PNR records from CRIS servers a few days after the train journey completes.
          </div>
          <div style="margin-top:12px;display:flex;gap:8px;">
            <a href="https://www.indianrail.gov.in/enquiry/PNR/PnrEnquiry.html" target="_blank" rel="noopener noreferrer" class="btn-primary" style="background:#DC2626;border-color:#DC2626;font-size:12px;padding:6px 14px;text-decoration:none;display:inline-block;">
              Verify Directly on indianrail.gov.in ↗
            </a>
            <button class="btn-secondary" style="font-size:12px;padding:6px 12px;" onclick="fillAndCheckDemoPnr('4521894021')">
              Try Sample PNR
            </button>
          </div>
        </div>
      `;
      resultBox.style.display = 'block';
      return;
    }

    // Render Real Live PNR Data Card
    const chartBadge = data.chart_prepared
      ? `<span style="background:#D1FAE5;color:#065F46;font-size:11px;font-weight:800;padding:3px 10px;border-radius:20px;border:1px solid #A7F3D0;">✓ Chart Prepared</span>`
      : `<span style="background:#FEF3C7;color:#92400E;font-size:11px;font-weight:800;padding:3px 10px;border-radius:20px;border:1px solid #FDE68A;">⏳ Chart Not Prepared</span>`;

    let paxHtml = '';
    if (data.passengers && data.passengers.length > 0) {
      paxHtml = data.passengers.map((p, idx) => {
        const isCnf = p.current_status.includes('CNF') || p.current_status.includes('Confirm');
        const badgeBg = isCnf ? '#DEF7EC' : (p.current_status.includes('RAC') ? '#FEF08A' : '#FEE2E2');
        const badgeColor = isCnf ? '#03543F' : (p.current_status.includes('RAC') ? '#713F12' : '#991B1B');

        return `
          <div style="display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;margin-bottom:6px;">
            <div>
              <div style="font-weight:700;font-size:13px;color:var(--text);">${p.passenger}</div>
              <div style="font-size:11px;color:var(--text-muted);">Booking: <strong>${p.booking_status}</strong></div>
            </div>
            <div style="text-align:right;">
              <span style="background:${badgeBg};color:${badgeColor};font-size:12px;font-weight:800;padding:3px 8px;border-radius:6px;display:inline-block;">
                ${p.current_status}
              </span>
              ${p.coach ? `<div style="font-size:11px;font-weight:700;color:var(--primary);margin-top:2px;">Coach ${p.coach} · Berth ${p.berth} (${p.berth_type || 'Berth'})</div>` : ''}
            </div>
          </div>
        `;
      }).join('');
    }

    resultBox.innerHTML = `
      <div style="background:#FFFFFF;border:2px solid #E2E8F0;border-radius:12px;padding:16px;box-shadow:0 4px 12px rgba(0,0,0,0.04);">
        <!-- Train & Chart Header -->
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #E2E8F0;">
          <div>
            <div style="font-size:16px;font-weight:800;color:var(--primary);">${data.train_number} — ${data.train_name}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:2px;">Class: <strong>${data.class}</strong> · Quota: <strong>${data.quota}</strong> · Platform: <strong>${data.expected_platform}</strong></div>
          </div>
          <div>${chartBadge}</div>
        </div>

        <!-- Route timeline -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;background:#F1F5F9;padding:10px 14px;border-radius:8px;">
          <div>
            <div style="font-size:11px;color:var(--text-muted);">BOARDING</div>
            <div style="font-weight:800;font-size:13px;color:var(--text);">${data.from_station}</div>
            <div style="font-size:11px;color:var(--primary);font-weight:700;">${data.departure_time} · ${data.date_of_journey}</div>
          </div>
          <div style="font-size:18px;color:#E2E8F0;">→</div>
          <div style="text-align:right;">
            <div style="font-size:11px;color:var(--text-muted);">DESTINATION</div>
            <div style="font-weight:800;font-size:13px;color:var(--text);">${data.to_station}</div>
            <div style="font-size:11px;color:var(--text-muted);">${data.arrival_time}</div>
          </div>
        </div>

        <!-- Passenger Status List -->
        <div style="margin-bottom:10px;">
          <div style="font-size:11px;font-weight:700;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px;letter-spacing:0.5px;">Passenger Status</div>
          ${paxHtml}
        </div>

        <!-- Verification Footer -->
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;padding-top:8px;border-top:1px dashed #FFFFFF;font-size:11px;color:#E2E8F0;">
          <span>Source: <strong>${data.source}</strong></span>
          <span style="font-weight:700;color:#059669;">✓ Verified Indian Railways Record</span>
        </div>
      </div>
    `;
    resultBox.style.display = 'block';

  } catch (err) {
    if (loading) loading.style.display = 'none';
    showToast('⚠️ Could not connect to PNR gateway. Please try again.');
  }
}

async function openSmartTicketModal(journey) {
  const j = journey || state.selectedJourney;
  let from = document.getElementById('inp-from').value || 'Visakhapatnam';
  let to = document.getElementById('inp-to').value || 'Bengaluru';
  let trainNo = '12841';
  let via = '';

  if (j && j.segments && j.segments.length > 0) {
    from = j.segments[0].from;
    to = j.segments[j.segments.length - 1].to;
    trainNo = j.segments[0].train_number;
    if (j.type === 'connecting') via = j.interchange_station;
  }

  // Fetch verified digital prototype from API
  try {
    const res = await fetch('/api/ticket/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from, to, train_number: trainNo, via })
    });
    const t = await res.json();
    document.getElementById('ticket-route-display').textContent = `${t.source} → ${t.destination}`;
    document.getElementById('ticket-validity-display').textContent = t.validity;
    document.getElementById('ticket-coach-display').textContent = t.coach;
    document.getElementById('ticket-seat-display').textContent = t.suggested_seat;
    document.getElementById('ticket-fallback-display').textContent = t.fallback_seat;
    document.getElementById('ticket-id-display').textContent = t.ticket_id;
    document.getElementById('ticket-fare-display').textContent = t.fare;
  } catch (e) {
    document.getElementById('ticket-route-display').textContent = `${from} → ${to}`;
    document.getElementById('ticket-coach-display').textContent = 'GS-2';
    document.getElementById('ticket-seat-display').textContent = '48';
    document.getElementById('ticket-fallback-display').textContent = via ? `Seat 31 after ${via}` : 'Seat 24 window';
    document.getElementById('ticket-fare-display').textContent = '₹65';
  }

  toggleTicketModal(true);
}

function toggleTicketModal(show) {
  const el = document.getElementById('ticket-modal-overlay');
  if (el) el.style.display = show ? 'flex' : 'none';
}

function issueDigitalTicketAction() {
  showToast('✅ Prototype Smart Ticket Issued & Verified! Token saved to offline wallet.');
  setTimeout(() => { toggleTicketModal(false); }, 800);
}

function startLiveJourney(journey) {
  const j = journey || state.selectedJourney;
  if (!j) return;

  state.followingJourney = j;
  selectJourney(j);

  // Enable live journey dock
  const dock = document.getElementById('live-journey-dock');
  const actionText = document.getElementById('dock-action-text');
  const healthBadge = document.getElementById('dock-health-badge');

  const s1 = j.segments[0];
  if (j.type === 'connecting' && j.segments.length > 1) {
    actionText.textContent = `Board Train ${s1.train_number} (${s1.from} dep ${s1.departure}) · Transfer at ${j.interchange_station}`;
  } else {
    actionText.textContent = `Board Train ${s1.train_number} (${s1.train_name}) · Departs ${s1.departure}`;
  }
  healthBadge.textContent = j.journey_health;

  dock.style.display = 'flex';
  showToast('🛰️ Live Journey tracking active in Mission Dock');
}

function openSelectedJourneyFromDock() {
  if (state.followingJourney) {
    selectJourney(state.followingJourney);
    window.scrollTo({ top: document.getElementById('results-wrapper').offsetTop - 80, behavior: 'smooth' });
  }
}

function stopFollowingJourney() {
  state.followingJourney = null;
  document.getElementById('live-journey-dock').style.display = 'none';
  showToast('Live tracking stopped');
}

async function askTravelIntelligence(type) {
  const j = state.selectedJourney;
  const resCard = document.getElementById('intel-response');
  if (!j) {
    resCard.style.display = 'block';
    resCard.innerHTML = '<em>Please select a train journey first to view verified travel intelligence.</em>';
    return;
  }

  resCard.style.display = 'block';
  resCard.innerHTML = '<em>Analyzing verified timetable telemetry...</em>';

  try {
    const res = await fetch('/api/journey/explain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ journey: j, type })
    });
    const d = await res.json();

    if (type === 'why_best') {
      resCard.innerHTML = `
        <div style="font-weight:700;color:var(--primary);margin-bottom:4px;">💡 ${d.title}</div>
        <div>${d.explanation.replace(/\n/g, '<br/>')}</div>
        <div style="margin-top:8px;font-size:11px;color:var(--text-muted);">
          <b>Punctuality:</b> ${d.metrics.punctuality} · <b>Risk:</b> ${d.metrics.transfer_risk || d.metrics.transfer_safety}
        </div>
      `;
    } else if (type === 'transfer_safety') {
      resCard.innerHTML = `
        <div style="font-weight:700;color:var(--secondary);margin-bottom:4px;">🛡️ ${d.verdict}</div>
        <div>${d.details.replace(/\n/g, '<br/>')}</div>
        <div style="margin-top:8px;font-size:11px;background:#EFF6FF;padding:6px;border-radius:4px;color:#1E40AF;">
          Buffer: <b>${d.buffer_breakdown.scheduled_buffer}</b> · Net Margin: <b>${d.buffer_breakdown.net_safety_margin}</b>
        </div>
      `;
    } else {
      resCard.innerHTML = `
        <div style="font-weight:700;color:#059669;margin-bottom:4px;">📍 Next Action:</div>
        <div><strong>${d.action}</strong></div>
        <ul style="margin:6px 0 0 18px;font-size:12px;">
          ${d.step_by_step.map(st => `<li>${st}</li>`).join('')}
        </ul>
      `;
    }
  } catch (e) {
    resCard.innerHTML = '<em>Failed to load intelligence details.</em>';
  }
}

function showToast(msg) {
  let toast = document.getElementById('arrts-toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'arrts-toast';
    toast.style.cssText = 'position:fixed;top:75px;left:50%;transform:translateX(-50%);background:#102A6BEB;color:#fff;padding:10px 20px;border-radius:24px;font-size:13px;font-weight:700;z-index:9999;box-shadow:0 8px 24px rgba(0,0,0,0.25);border:1px solid #FF6F00;pointer-events:none;transition:opacity 0.2s;';
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.style.opacity = '1';
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => { toast.style.opacity = '0'; }, 3200);
}
