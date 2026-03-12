const map = L.map('map').setView([20, 0], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  maxZoom: 18,
  attribution: '&copy; OpenStreetMap contributors'
}).addTo(map);

const markers = L.layerGroup().addTo(map);

async function loadAircraft() {
  const resp = await fetch('/api/aircraft/live?limit=2000');
  const aircraft = await resp.json();
  markers.clearLayers();
  aircraft.forEach(a => {
    if (a.latitude != null && a.longitude != null) {
      L.circleMarker([a.latitude, a.longitude], { radius: 3, color: '#0b6' })
        .bindPopup(`${a.callsign || 'N/A'} | ${a.model || 'unknown model'} | ${a.icao24}`)
        .addTo(markers);
    }
  });
}

async function analyzeRoute() {
  const origin = document.getElementById('origin').value.toUpperCase();
  const destination = document.getElementById('destination').value.toUpperCase();
  const resp = await fetch(`/api/route/analyze?origin=${origin}&destination=${destination}`);
  const data = await resp.json();
  if (!resp.ok) {
    document.getElementById('summary').innerText = `Route analysis failed: ${data.detail || 'unknown error'}`;
    document.getElementById('output').innerText = JSON.stringify(data, null, 2);
    return;
  }
  document.getElementById('summary').innerText = `Route ${origin}→${destination} | Distance: ${data.route?.distance_nm || 'N/A'} nm | Feasible: ${data.feasible_aircraft?.length || 0}`;
  document.getElementById('output').innerText = JSON.stringify(data, null, 2);
}

document.getElementById('analyzeBtn').addEventListener('click', analyzeRoute);

loadAircraft();
setInterval(loadAircraft, 60000);
