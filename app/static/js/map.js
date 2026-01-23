/**
 * Script pentru initializarea si gestionarea hartii Leaflet
 */

// Coordonatele Universitatii Politehnica Bucuresti
const UPB_LAT = 44.439611824934026;
const UPB_LNG = 26.0492114360659;
const DEFAULT_ZOOM = 16;

// Variabile pentru rutare
let routeControl = null;
let routeMarkers = []; // optional

// Coordonatele intrării în campus
const CAMPUS_GATE_LAT = 44.434583;
const CAMPUS_GATE_LNG = 26.045166;
let hasShownRoutePrivacyHint = false;  // flag

let map = null;
let markers = [];
let parkingLotPolygons = [];
let routingCancelWrapper = null;

let myReservations = [];     // încărcat din /reservation/my
let myReservationsTotal = 0;        // total count from backend
let showFullReservationHistory = false;

const RESERVATION_HISTORY_LIMIT = 5;

let selectedReserveSpotId = null;

const MARKER_COLORS = {
    free: '#28a745',      // Verde - liber
    occupied: '#dc3545',  // Rosu - ocupat
    reserved: '#ffc107',  // Galben - rezervat
    default: '#007bff'    // Albastru - implicit
};

const PARKING_LOT_COLORS = {
    default: '#3388ff',   // Albastru - implicit
    hover: '#ff7800',     // Portocaliu - hover
    selected: '#ffed4e'   // Galben - selectat
};

// helpers
function isLoggedIn() {
    return window.CURRENT_USER && window.CURRENT_USER.isAuthenticated;
}

function isoFromDatetimeLocal(value) {
    // "YYYY-MM-DDTHH:MM" e acceptat de datetime.fromisoformat
    return value;
}

function formatDateRO(iso) {
    try {
        return new Date(iso).toLocaleString('ro-RO');
    } catch {
        return iso;
    }
}

function getActiveReservationForSpot(spotId) {
    // "active" înseamnă not cancelled/finished
    return myReservations.find(r => r.spot_id === spotId && r.status === "active") || null;
}

function fetchMyReservations({ forceFull = false } = {}) {
    if (!isLoggedIn()) return Promise.resolve([]);

     // Decide what to load
    const wantFull = forceFull || showFullReservationHistory;
    const limit = wantFull ? 1000 : RESERVATION_HISTORY_LIMIT; // "enough" instead of infinity
    const offset = 0;

    return fetch(`/reservations/my?limit=${limit}&offset=${offset}`)
        .then(res => {
            if (res.status === 401) return { total: 0, items: [] };
            if (!res.ok) throw new Error(`API error: ${res.status}`);
            return res.json();
        })
        .then(data => {
            myReservationsTotal = Number(data?.total || 0);
            myReservations = Array.isArray(data?.items) ? data.items : [];

            renderReservationSidebar();
            return myReservations;
        })
        .catch(err => {
            console.warn('Eroare la incarcarea rezervarilor:', err);
            myReservationsTotal = 0;
            myReservations = [];
            renderReservationSidebar();
            return [];
        });
}

function renderReservationSidebar() {
    const currentEl = document.getElementById('current-reservation-content');
    const historyEl = document.getElementById('reservation-history-content');
    if (!currentEl || !historyEl) return;

    if (!isLoggedIn()) {
        currentEl.innerHTML = `<div class="no-reservation"><p>Conectează-te pentru rezervări.</p></div>`;
        historyEl.innerHTML = `<div class="empty-state"><p>Conectează-te pentru istoric.</p></div>`;
        return;
    }

    if (!myReservations.length) {
        currentEl.innerHTML = `<div class="no-reservation"><p>Nu ai nicio rezervare activă</p></div>`;
        historyEl.innerHTML = `<div class="empty-state"><p>Nu ai rezervări</p></div>`;
        return;
    }

    // Current = prima rezervare activă începând cu start_time (closest upcoming/current)
    const active = myReservations
        .filter(r => r.status === "active")
        .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

    if (active.length) {
        const r = active[0];
        currentEl.innerHTML = `
          <div class="user-info-card">
            <p><strong>Spot #${r.spot_id}</strong></p>
            <p class="text-muted">${formatDateRO(r.start_time)} → ${formatDateRO(r.end_time)}</p>
            <button class="btn btn-danger btn-sm" onclick="cancelReservation(${r.id})">❌ Anulează</button>
          </div>
        `;
    } else {
        currentEl.innerHTML = `<div class="no-reservation"><p>Nu ai nicio rezervare activă</p></div>`;
    }

    // tot istoricul
    // const rows = myReservations
    //     .slice()
    //     .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
    //     .map(r => `
    //       <div style="padding:8px 0; border-bottom:1px solid rgba(0,0,0,0.06);">
    //         <div style="display:flex; justify-content:space-between; gap:10px;">
    //           <div>
    //             <div><strong>#${r.spot_id}</strong> <span style="opacity:0.7;">(${r.status})</span></div>
    //             <div style="font-size:12px; opacity:0.75;">${formatDateRO(r.start_time)} → ${formatDateRO(r.end_time)}</div>
    //           </div>
    //           <div style="text-align:right;">
    //             ${r.status === "active" ? `<button class="btn btn-danger btn-sm" onclick="cancelReservation(${r.id})">Anulează</button>` : ``}
    //           </div>
    //         </div>
    //       </div>
    //     `)
    //     .join('');

    // historyEl.innerHTML = rows || `<div class="empty-state"><p>Nu ai rezervări</p></div>`;

    // ultimele 5 rezervări + buton pentru înterg istoricul
    const sorted = myReservations
    .slice()
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time));

    const rows = sorted
    .map(r => `
        <div style="padding:8px 0; border-bottom:1px solid rgba(0,0,0,0.06);">
        <div style="display:flex; justify-content:space-between; gap:10px;">
            <div>
            <div><strong>#${r.spot_id}</strong> <span style="opacity:0.7;">(${r.status})</span></div>
            <div style="font-size:12px; opacity:0.75;">${formatDateRO(r.start_time)} → ${formatDateRO(r.end_time)}</div>
            </div>
            <div style="text-align:right;">
            ${r.status === "active" ? `<button class="btn btn-danger btn-sm" onclick="cancelReservation(${r.id})">Anulează</button>` : ``}
            </div>
        </div>
        </div>
    `)
    .join('');

    // afiseaza butonul "Vezi toate" doar daca numărul total de rezervări > 5
    let footer = '';
    if (myReservationsTotal > RESERVATION_HISTORY_LIMIT) {
    footer = `
        <div style="margin-top:10px; display:flex; justify-content:center;">
        <button class="btn btn-secondary btn-sm" onclick="toggleReservationHistory()">
            ${showFullReservationHistory ? 'Arată mai puțin' : `Vezi toate (${myReservationsTotal})`}
        </button>
        </div>
    `;
    }

    historyEl.innerHTML = (rows ? rows + footer : `<div class="empty-state"><p>Nu ai rezervări</p></div>`);
}

function showToast(message, type = 'info', timeoutMs = 5000) {
    const container = document.getElementById('toast-container');

    if (!container) {
        // fallback dacă container-ul lipsește
        console.warn("toast-container missing:", message);
        return;
    }

    const colors = {
        info:  '#ffffff',
        success: '#ffffff',
        warning: '#ffffff',
        error: '#ffffff'
    };

    const borders = {
        info:   '#3b82f6',
        success:'#22c55e',
        warning:'#f59e0b',
        error:  '#ef4444'
    };

    const toast = document.createElement('div');
    toast.style.background = colors[type] || '#fff';
    toast.style.color = '#111827';
    toast.style.border = `1px solid ${borders[type] || '#e5e7eb'}`;
    toast.style.borderLeft = `6px solid ${borders[type] || '#e5e7eb'}`;
    toast.style.borderRadius = '12px';
    toast.style.boxShadow = '0 10px 25px rgba(0,0,0,0.15)';
    toast.style.padding = '12px 14px';
    toast.style.minWidth = '280px';
    toast.style.maxWidth = '420px';
    toast.style.fontSize = '14px';
    toast.style.lineHeight = '1.35';
    toast.style.display = 'flex';
    toast.style.gap = '10px';
    toast.style.alignItems = 'flex-start';
    toast.style.pointerEvents = 'auto';

    toast.innerHTML = `
        <div style="flex:1; white-space:pre-line;">${message}</div>
        <button style="border:none; background:transparent; cursor:pointer; color:#6b7280; font-size:16px; line-height:1;">✕</button>
    `;

    const closeBtn = toast.querySelector('button');
    closeBtn.addEventListener('click', () => toast.remove());

    container.appendChild(toast);

    if (timeoutMs > 0) {
        setTimeout(() => {
        if (toast.isConnected) toast.remove();
        }, timeoutMs);
    }
}

function reservationErrorMessage(code, httpStatus) {
    const map = {
        INVALID_DATA: "Completează toate câmpurile (spot, start, end).",
        INVALID_DATETIME: "Format dată invalid.",
        INVALID_TIMEFRAME: "Interval invalid: start trebuie să fie înainte de end.",
        SPOT_NOT_FOUND: "Locul de parcare nu există.",
        SPOT_OCCUPIED: "Locul este ocupat.",
        SPOT_OVERLAP: "Locul este deja rezervat în acel interval.",
        EXISTING_RESERVATION_OVERLAP: "Ai deja o rezervare activă în acel interval.",
        NOT_FOUND: "Rezervarea nu există.",
        FORBIDDEN: "Nu ai voie să modifici această rezervare.",
        BAD_REQUEST: "Cerere invalidă."
    };

    return map[code] || `Eroare (${httpStatus})`;
}

function toggleReservationHistory() {
    showFullReservationHistory = !showFullReservationHistory;

    // When user expands, fetch full history once
    return fetchMyReservations({ forceFull: showFullReservationHistory });
}

function isRouteActive() {
  if (!routeControl) return false;

  // If you use markers for route, easiest check:
  if (routeMarkers && routeMarkers.length > 0) return true;

  // Also check waypoints (LRM stores waypoints even after set)
  try {
    const wps = routeControl.getWaypoints?.() || [];
    return wps.filter(w => w && w.latLng).length >= 2;
  } catch (e) {
    return false;
  }
}

function isRoutingPanelExpanded() {
  if (!routeControl) return false;
  const c = routeControl.getContainer?.();
  if (!c) return false;
  return !c.classList.contains("leaflet-routing-container-hide");
}

function updateCancelButtonVisibility() {
  // show only if route exists AND panel is expanded
  const shouldShow = isRouteActive() && isRoutingPanelExpanded();
  setRoutingCancelVisible(shouldShow);
}

function ensureRoutingCancelButton(position = "top") {
    if (!routeControl) return;

    const container = routeControl.getContainer?.();
    if (!container) return;

    // Already created
    if (routingCancelWrapper) return;

    const wrapper = document.createElement("div");
    wrapper.style.margin = "8px";
    wrapper.style.display = "none"; // hidden until a route exists
    wrapper.style.textAlign = "center";
    wrapper.style.width = "calc(100% - 16px)";


    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-outline-secondary btn-sm";
    btn.textContent = "Anulează afișarea rutei";
    btn.style.width = "100%";
    btn.style.whiteSpace = "nowrap";
    btn.onclick = () => clearRoute();

    wrapper.appendChild(btn);

    // IMPORTANT: don't let clicks on the button move/zoom the map
    if (window.L && L.DomEvent) {
        L.DomEvent.disableClickPropagation(wrapper);
        L.DomEvent.disableScrollPropagation(wrapper);
    }

    // Place it where you want:
    // "top" = above instructions
    // "bottom" = below instructions
    if (position === "top") {
        container.insertBefore(wrapper, container.firstChild);
    } else {
        container.appendChild(wrapper);
    }

    routingCancelWrapper = wrapper;

    // --- sync cancel button with panel collapse/expand ---
    const collapseBtn = container.querySelector(".leaflet-routing-collapse-btn");
    if (collapseBtn && !collapseBtn.dataset.cancelHooked) {
    collapseBtn.dataset.cancelHooked = "1";
    collapseBtn.addEventListener("click", () => {
        // wait for LRM to toggle class
        setTimeout(updateCancelButtonVisibility, 0);
    });
    }

    // Watch container class changes (best + works even if LRM changes DOM)
    if (!container.dataset.cancelObserver) {
    container.dataset.cancelObserver = "1";
    const obs = new MutationObserver(() => updateCancelButtonVisibility());
    obs.observe(container, { attributes: true, attributeFilter: ["class"] });
    }

    // initial sync
    updateCancelButtonVisibility();
}

function setRoutingCancelVisible(visible) {
    if (!routingCancelWrapper) return;
    routingCancelWrapper.style.display = visible ? "block" : "none";
}


// end of helpers

// ===== STATS (backend) =====

let lastStatsLot = null;

function getSelectedParkingLotName() {
    const sel = document.getElementById('filter-parking-lot');
    if (!sel) return '';
    return (sel.value || '').trim();
}

function getSelectedStatsHour() {
    const sel = document.getElementById('stats-hour');
    if (!sel) return '';
    return (sel.value || '').trim(); // "" sau "13"
}

function renderHourlyStats(stats, hour) {
  const probEl = document.getElementById("stat-hour-prob");
  if (!probEl) return;

  // 1) Text probabilitate pentru ora selectată
  if (hour !== "") {
    const pct = stats?.selected_hour_probability_percent;
    probEl.textContent = (pct === undefined || pct === null) ? "—" : `${pct}%`;
  } else {
    probEl.textContent = "—";
  }

  // 2) Mini chart (distribuție)
  const chart = document.getElementById("hourly-mini-chart");
  if (!chart) return;

  const arr = stats?.hourly_occupancy_probability;
  if (!Array.isArray(arr) || arr.length === 0) {
    chart.innerHTML = "";
    return;
  }

  const filtered = arr.filter(x => x.hour >= 8 && x.hour <= 20);
  const selectedHour = (hour === "" ? null : Number(hour));

  chart.innerHTML = `
    <div style="font-size:12px; margin-bottom:6px; color:#666;">Distribuție pe ore (8–20)</div>
    <div id="hourly-bars" style="display:flex; gap:4px; align-items:flex-end; height:50px;">
      ${filtered.map(x => {
        const pct = Number(x.percent ?? (x.p * 100) ?? 0);
        const h = x.hour;
        const barH = Math.max(0, Math.min(50, Math.round(pct / 2)));

        // Dacă e selectată o oră: highlight doar pe ea, restul dimmed
        // Dacă nu e selectată: toate normale
        const classes = [
          "hour-bar",
          (selectedHour === null) ? "" : (h === selectedHour ? "selected" : "dimmed")
        ].join(" ").trim();

        return `
          <div
            class="${classes}"
            data-hour="${h}"
            title="${String(h).padStart(2,'0')}:00 • ${pct.toFixed(1)}%"
            style="height:${barH}px"
          ></div>
        `;
      }).join("")}
    </div>
  `;

  // 3) Click pe bară => selectează ora din dropdown + refresh
  const bars = document.querySelectorAll("#hourly-bars .hour-bar");
  bars.forEach(bar => {
    bar.addEventListener("click", () => {
      const h = bar.getAttribute("data-hour");
      const sel = document.getElementById("stats-hour");
      if (sel) {
        sel.value = h;
        refreshStats();
      }
    });
  });
}

function refreshStats() {
    const lotName = getSelectedParkingLotName(); // din dropdown-ul de parcare
    const hour = getSelectedStatsHour();

    console.log("refreshStats()", { lotName, hour });

    const params = new URLSearchParams();
    if (lotName) params.set("lot", lotName);
    if (hour !== "") params.set("hour", hour);

    const url = `/parking/stats${params.toString() ? `?${params.toString()}` : ""}`;

    fetch(url)
        .then(r => {
        if (!r.ok) throw new Error(`Stats API error: ${r.status}`);
        return r.json();
        })
        .then(stats => {
        renderStats(stats, lotName);
        renderHourlyStats(stats, hour);
        })
        .catch(err => {
        console.warn("Eroare refreshStats:", err);
        const probEl = document.getElementById("stat-hour-prob");
        if (probEl) probEl.textContent = "—";
        });
}

window.refreshStats = refreshStats;
window.getSelectedStatsHour = getSelectedStatsHour;
window.getSelectedParkingLotName = getSelectedParkingLotName;

function setStatsLoadingState(titleText = "Se încarcă...") {
    const title = document.getElementById('stats-title');
    if (title) title.textContent = titleText;

    const ids = ["stat-total", "stat-free", "stat-occupied", "stat-reserved", "stat-availability", "stats-updated"];
    ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.textContent = "—";
    });

    const bar = document.getElementById("availability-bar");
    if (bar) bar.style.width = "0%";
}

function renderStats(stats, lotName) {
    // stats expected:
    // { total_spots, free_spots, occupied_spots, reserved_spots, availability_percent, updated_at }

    const title = document.getElementById('stats-title');
    if (title) title.textContent = lotName ? `Parcare: ${lotName}` : "Statistici globale";

    const setText = (id, value) => {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    };

    setText("stat-total", stats?.total_spots ?? 0);
    setText("stat-free", stats?.free_spots ?? 0);
    setText("stat-occupied", stats?.occupied_spots ?? 0);
    setText("stat-reserved", stats?.reserved_spots ?? 0);

    const pct = Number(stats?.availability_percent ?? 0);
    setText("stat-availability", `${pct}%`);

    const bar = document.getElementById("availability-bar");
    if (bar) bar.style.width = `${Math.max(0, Math.min(100, pct))}%`;

    const updated = document.getElementById("stats-updated");
    if (updated) {
        const iso = stats?.updated_at;
        updated.textContent = iso ? `Actualizat: ${formatDateRO(iso)}` : "—";
    }
}

function fetchParkingStatsForSelection({ silent = false } = {}) {
    // dacă nu ai încă secțiunea de stats în HTML, ieșim fără erori
    if (!document.getElementById("stats-title")) return Promise.resolve(null);

    const lotName = getSelectedParkingLotName(); // "" => global
    lastStatsLot = lotName;

    if (!silent) {
        setStatsLoadingState(lotName ? `Se încarcă: ${lotName}...` : "Se încarcă: global...");
    }

    const url = lotName
        ? `/parking/stats?lot=${encodeURIComponent(lotName)}`
        : `/parking/stats`;

    return fetch(url)
        .then(res => {
        if (!res.ok) throw new Error(`Stats API error: ${res.status}`);
        return res.json();
        })
        .then(stats => {
        // dacă user a schimbat selecția între timp, ignorăm răspunsul vechi
        if (getSelectedParkingLotName() !== lastStatsLot) return null;
        renderStats(stats, lotName);
        return stats;
        })
        .catch(err => {
        console.warn("Eroare stats:", err);
        if (!silent) {
            const title = document.getElementById("stats-title");
            if (title) title.textContent = "Statistici indisponibile";
        }
        return null;
        });
}

// funcții pentru rutare

function initRouting() {
    if (!window.L || !L.Routing) {
      console.warn("Leaflet Routing Machine not loaded (L.Routing missing).");
      return;
    }

    routeControl = L.Routing.control({
        waypoints: [],
        addWaypoints: false,
        draggableWaypoints: true,
        routeWhileDragging: true,
        fitSelectedRoutes: true,
        collapsible: true,
        show: true,
        router: L.Routing.osrmv1({
            serviceUrl: "https://router.project-osrm.org/route/v1"
        })
    }).addTo(map);

    // adaugă butonul de anulare a rutării
    ensureRoutingCancelButton("top");

    // verifică că butonul apare doar dacă rutarea e activă
    // routeControl.on("routesfound", () => setRoutingCancelVisible(true));
    // routeControl.on("routingerror", () => setRoutingCancelVisible(isRouteActive()));
    // routeControl.on("waypointschanged", () => setRoutingCancelVisible(isRouteActive()));

    routeControl.on("routesfound", updateCancelButtonVisibility);
    routeControl.on("routingerror", updateCancelButtonVisibility);
    routeControl.on("waypointschanged", updateCancelButtonVisibility);
    console.log("Rutare initializata.");
}

function routeFromGateTo(lat, lng) {
    if (!routeControl) initRouting();
    if (!routeControl) {
        // alert("Routing is not initialized.");
        showToast("Routing nu este inițializat.", "error");
        return;
    }

    const start = L.latLng(CAMPUS_GATE_LAT, CAMPUS_GATE_LNG);
    const dest = L.latLng(lat, lng);

    routeControl.setWaypoints([start, dest]);
    updateCancelButtonVisibility();

    // Optional: show markers
    routeMarkers.forEach(m => map.removeLayer(m));
    routeMarkers = [
        L.marker(start).addTo(map).bindPopup("Poartă campus").openPopup(),
        L.marker(dest).addTo(map).bindPopup("Destinație")
    ];
}


function routeFromMyLocationTo(lat, lng) {
    if (!routeControl) initRouting();
    if (!routeControl) {
        // alert("Routing is not initialized.");
        showToast("Routing nu este inițializat.", "error");
        return;
    }

    const dest = L.latLng(lat, lng);

    if (!navigator.geolocation) {
        showToast("Geolocation nu poate fi utilizat. Afișez ruta de la poarta campusului.", "warning", 6000);
        routeFromGateTo(lat, lng);
        return;
    }

    if (!hasShownRoutePrivacyHint) {
        hasShownRoutePrivacyHint = true;
        showToast(
            "Pentru ruta optimă folosesc locația ta.\n" +
            "Dacă nu permiți accesul, îți arăt ruta de la poarta campusului către locul de parcare.",
            "info",
            7000
        );
    }

    navigator.geolocation.getCurrentPosition(
        (pos) => {
        const start = L.latLng(pos.coords.latitude, pos.coords.longitude);
        routeControl.setWaypoints([start, dest]);
        updateCancelButtonVisibility();

        // Optional: show markers
        routeMarkers.forEach(m => map.removeLayer(m));
        routeMarkers = [
            L.marker(start).addTo(map).bindPopup("Locația mea").openPopup(),
            L.marker(dest).addTo(map).bindPopup("Destinație")
        ];

        console.log("Route set:", start, "->", dest);
        },
        (err) => {
            console.warn("Geolocation error:", err);
            // dacă utilizatorul nu permite accesul la locația sa,
            // atunci îi arătăm ruta de la intrarea în campus către locul de parcare
            showToast("Nu ai oferit acces la locație. Afișez ruta de la poarta campusului.", "warning", 6000);
            routeFromGateTo(lat, lng);
        },
        { enableHighAccuracy: true, timeout: 8000 }
    );

}

function clearRoute() {
    if (routeControl) {
        routeControl.setWaypoints([]);

        // if (typeof routeControl.hide === "function") routeControl.hide();
        // else routeControl.getContainer()?.classList.add("leaflet-routing-container-hide");

    } 
    routeMarkers.forEach(m => map.removeLayer(m));
    routeMarkers = [];
    updateCancelButtonVisibility();
}

// sfarsit functii pentru rutare

function initMap() {
    map = L.map('map').setView([UPB_LAT, UPB_LNG], DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
    }).addTo(map);

    // pentru rutare
    initRouting();

    const upbMarker = L.marker([UPB_LAT, UPB_LNG], {
        title: 'UPB - Universitatea Politehnica București'
    }).addTo(map);

    upbMarker.bindPopup(`
        <div class="marker-popup">
            <h4>🏫 Universitatea Politehnica București</h4>
            <p>Bld. Iuliu Maniu 1-3, București</p>
        </div>
    `);

    console.log('Harta Leaflet initializata pe UPB');

    loadParkingLots();
    loadParkingSpots();
}

function loadParkingLots() {
    fetch('/parking/lots')
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(lots => {
            console.log('Parking Lots (poligoane GIS) încărcate:', lots.length);
            
            parkingLotPolygons.forEach(poly => map.removeLayer(poly));
            parkingLotPolygons = [];

            lots.forEach(lot => {
                if (lot.polygon_geojson) {
                    addParkingLotPolygon(lot);
                }
            });
        })
        .catch(error => {
            console.error('Eroare la incarcarea parking lots:', error);
        });
}

function addParkingLotPolygon(lot) {
    try {
        const geoJSON = typeof lot.polygon_geojson === 'string' 
            ? JSON.parse(lot.polygon_geojson) 
            : lot.polygon_geojson;

        const feature = {
            type: 'Feature',
            geometry: geoJSON,
            properties: {
                name: lot.name,
                total_spots: lot.total_spots,
                columns: lot.columns,
                id: lot.id
            }
        };

        const style = {
            color: PARKING_LOT_COLORS.default,
            weight: 3,
            opacity: 0.8,
            fill: true,
            fillColor: PARKING_LOT_COLORS.default,
            fillOpacity: 0.25,
            dashArray: '5, 5'
        };

        const geoJsonLayer = L.geoJSON(feature, {
            style: style,
            onEachFeature: function(feature, layer) {
                const props = feature.properties;
                const popupContent = `
                    <div class="parking-lot-popup">
                        <h4>${props.name}</h4>
                        <p><strong>Total locuri:</strong> ${props.total_spots}</p>
                        <p><strong>Coloane:</strong> ${props.columns}</p>
                        <p><strong>ID Lot:</strong> ${props.id}</p>
                    </div>
                `;
                layer.bindPopup(popupContent);

                layer.on('mouseover', function() {
                    this.setStyle({
                        color: PARKING_LOT_COLORS.hover,
                        fillColor: PARKING_LOT_COLORS.hover,
                        fillOpacity: 0.35,
                        weight: 4
                    });
                });

                layer.on('mouseout', function() {
                    this.setStyle({
                        color: PARKING_LOT_COLORS.default,
                        fillColor: PARKING_LOT_COLORS.default,
                        fillOpacity: 0.25,
                        weight: 3
                    });
                });

                layer.bindTooltip(`<strong>${props.name}</strong><br/>${props.total_spots} locuri`, {
                    permanent: false,
                    direction: 'top',
                    className: 'parking-lot-tooltip'
                });
            }
        }).addTo(map);

        parkingLotPolygons.push(geoJsonLayer);
        console.log(`Lot "${lot.name}" adaugat ca poligon GIS`);
    } catch (error) {
        console.error(`Eroare la parsare GeoJSON pentru lot ${lot.name}:`, error);
    }
}

function getParkingStatus(spot) {

    if (spot.is_occupied) {
        return 'occupied';
    }

    if (spot.reservation && spot.reservation.start_time && spot.reservation.end_time) {
        return 'reserved';
    } else {
        return 'free';
    }
}

function createMarkerIcon(status) {
    const color = MARKER_COLORS[status] || MARKER_COLORS.default;
    return L.divIcon({
        html: `<div style="background-color: ${color}; border-radius: 50%; width: 25px; height: 25px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">🅿️</div>`,
        iconSize: [25, 25],
        className: 'parking-marker'
    });
}

function getStatusLabel(status) {
    const labels = {
        'free': '🟢 Liber',
        'occupied': '🔴 Ocupat',
        'reserved': '🟡 Rezervat'
    };
    return labels[status] || 'Necunoscut';
}

function loadParkingSpots() {
    fetch('/parking/spots')
        .then(response => {
            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }
            return response.json();
        })
        .then(spots => {
            console.log('Locuri de parcare incarcate:', spots.length);
            allParkingSpots = spots;
            spots.forEach(spot => {
                addParkingMarker(spot);
            });
        })
        .catch(error => {
            console.error('Eroare la incarcarea locurilor de parcare:', error);
        });
}

function addParkingMarker(spot) {
    const status = getParkingStatus(spot);

    if (spot.polygon_geojson) {
        addParkingSpotPolygon(spot);
    } else {
        const icon = createMarkerIcon(status);
        const marker = L.marker([spot.latitude, spot.longitude], {
            icon: icon,
            title: `${spot.parking_lot} #${spot.spot_number || spot.id} (${getStatusLabel(status)})`
        }).addTo(map);

        let popupContent = `
            <div class="marker-popup">
                <h4>🅿️ ${spot.parking_lot} #${spot.spot_number || spot.id}</h4>
                <p><strong>Stare:</strong> ${getStatusLabel(status)}</p>
        `;

        if (spot.reservation && spot.reservation.start_time) {
            const startTime = new Date(spot.reservation.start_time).toLocaleString('ro-RO');
            const endTime = new Date(spot.reservation.end_time).toLocaleString('ro-RO');
            popupContent += `
                <p><strong>Rezervare:</strong> ${startTime} - ${endTime}</p>
            `;
        }

        if (spot.occupied_by_email) {
            popupContent += `
                <p><strong>Ocupat de:</strong> ${spot.occupied_by_email}</p>
            `;
        }

        const buttonText = spot.is_occupied ? 'Eliberează' : 'Ocupă';
        const buttonClass = spot.is_occupied ? 'btn-danger' : 'btn-success';
        
        popupContent += `
                <button class="btn ${buttonClass} btn-sm" onclick="toggleParkingSpot(${spot.id}, ${spot.is_occupied})">
                    ${buttonText}
                </button>
        `;

        // Reservation buttons
        if (typeof isLoggedIn === "function" && isLoggedIn()) {
            const myActive = (typeof getActiveReservationForSpot === "function")
                ? getActiveReservationForSpot(spot.id)
                : null;

            if (myActive) {
                popupContent += `
                    <button class="btn btn-warning btn-sm" style="margin-left:6px;"
                            onclick="cancelReservation(${myActive.id})">
                        Anulează rezervarea
                    </button>
                `;
            } else if (status === 'free' && !spot.is_occupied) {
                popupContent += `
                    <button class="btn btn-primary btn-sm" style="margin-left:6px;"
                            onclick="reserveParkingSpot(${spot.id})">
                        Rezervă
                    </button>
                `;
            }
        }

        // ROUTING buttons
        popupContent += `
            <div style="margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;">
                <button class="btn btn-outline-primary btn-sm"
                        onclick="routeFromMyLocationTo(${spot.latitude}, ${spot.longitude})">
                    Vezi ruta din locația ta
                </button>

                <button class="btn btn-outline-secondary btn-sm"
                        onclick="routeFromGateTo(${spot.latitude}, ${spot.longitude})">
                    Vezi ruta de la intrare
                </button>
            </div>
        `;

        if (isRouteActive()) {
        popupContent += `
            <button class="btn btn-outline-secondary btn-sm"
                    onclick="clearRoute()">
                Anulează afișarea rutei
            </button>
        `;
        }

        popupContent += `
            </div>
        `;

        marker.bindPopup(popupContent);
        markers.push(marker);
    }
}

function addParkingSpotPolygon(spot) {
    try {
        const status = getParkingStatus(spot);
        const geoJSON = typeof spot.polygon_geojson === 'string' 
            ? JSON.parse(spot.polygon_geojson) 
            : spot.polygon_geojson;

        const spotColor = {
            'free': '#28a745',       // Verde - liber
            'occupied': '#dc3545',   // Rosu - ocupat
            'reserved': '#ffc107'    // Galben - rezervat
        };

        const color = spotColor[status] || '#007bff';

        const style = {
            color: color,
            weight: 2,
            opacity: 0.9,
            fill: true,
            fillColor: color,
            fillOpacity: 0.6,
            dashArray: null
        };

        const feature = {
            type: 'Feature',
            geometry: geoJSON,
            properties: {
                id: spot.id,
                spot_number: spot.spot_number || spot.id,
                parking_lot: spot.parking_lot,
                is_occupied: spot.is_occupied,
                status: status
            }
        };

        const geoJsonLayer = L.geoJSON(feature, {
            style: style,
            onEachFeature: function(feature, layer) {
                const props = feature.properties;
                
                let popupContent = `
                    <div class="parking-spot-popup">
                        <h4>🅿️ ${props.parking_lot} #${props.spot_number}</h4>
                        <p><strong>Stare:</strong> ${getStatusLabel(props.status)}</p>
                `;

                if (spot.reservation && spot.reservation.start_time) {
                    const startTime = new Date(spot.reservation.start_time).toLocaleString('ro-RO');
                    const endTime = new Date(spot.reservation.end_time).toLocaleString('ro-RO');
                    popupContent += `
                        <p><strong>Rezervare:</strong> ${startTime} - ${endTime}</p>
                    `;
                }

                if (spot.occupied_by_email) {
                    popupContent += `
                        <p><strong>Ocupat de:</strong> ${spot.occupied_by_email}</p>
                    `;
                }

                const buttonText = props.is_occupied ? 'Eliberează' : 'Ocupă';
                const buttonClass = props.is_occupied ? 'btn-danger' : 'btn-success';
                
                popupContent += `
                        <button class="btn ${buttonClass} btn-sm" onclick="toggleParkingSpot(${props.id}, ${props.is_occupied})">
                            ${buttonText}
                        </button>
                `;

                // Reservation buttons
                if (typeof isLoggedIn === "function" && isLoggedIn()) {
                    const myActive = (typeof getActiveReservationForSpot === "function")
                        ? getActiveReservationForSpot(spot.id)
                        : null;

                    if (myActive) {
                        popupContent += `
                            <button class="btn btn-warning btn-sm" style="margin-left:6px;"
                                    onclick="cancelReservation(${myActive.id})">
                                Anulează rezervarea
                            </button>
                        `;
                    } else if (status === 'free' && !spot.is_occupied) {
                        popupContent += `
                            <button class="btn btn-primary btn-sm" style="margin-left:6px;"
                                    onclick="reserveParkingSpot(${spot.id})">
                                Rezervă
                            </button>
                        `;
                    }
                }

                // Routing buttons
                popupContent += `
                    <div style="margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;">
                        <button class="btn btn-outline-primary btn-sm"
                                onclick="routeFromMyLocationTo(${spot.latitude}, ${spot.longitude})">
                            Vezi ruta din locația ta
                        </button>

                        <button class="btn btn-outline-secondary btn-sm"
                                onclick="routeFromGateTo(${spot.latitude}, ${spot.longitude})">
                            Vezi ruta de la intrare
                        </button>
                    </div>
                `;

                if (isRouteActive()) {
                    popupContent += `
                        <button class="btn btn-outline-secondary btn-sm"
                                onclick="clearRoute()">
                            Anulează afișarea rutei
                        </button>
                    `;
                }

                popupContent += `
                    </div>
                `;

                layer.bindPopup(popupContent);

                layer.on('mouseover', function() {
                    this.setStyle({
                        weight: 3,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                });

                layer.on('mouseout', function() {
                    this.setStyle({
                        weight: 2,
                        opacity: 0.9,
                        fillOpacity: 0.6
                    });
                });

                layer.bindTooltip(`<strong>${props.parking_lot} #${props.spot_number}</strong><br/>${getStatusLabel(props.status)}`, {
                    permanent: false,
                    direction: 'top',
                    className: 'parking-spot-tooltip'
                });
            }
        }).addTo(map);

        markers.push(geoJsonLayer);
        console.log(`Spot "${spot.parking_lot} #${spot.spot_number}" adaugat ca poligon`);
    } catch (error) {
        console.error(`Eroare la parsare poligon spot ${spot.id}:`, error);
        const status = getParkingStatus(spot);
        const icon = createMarkerIcon(status);
        const marker = L.marker([spot.latitude, spot.longitude], {
            icon: icon,
            title: `${spot.parking_lot} #${spot.spot_number || spot.id}`
        }).addTo(map);
        markers.push(marker);
    }
}

function clearMarkers() {
    markers.forEach(marker => map.removeLayer(marker));
    markers = [];
}

function toggleParkingSpot(spotId, currentStatus) {
    fetch(`/parking/spots/${spotId}/toggle`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })
    .then( async (response) => {
        const data = await response.json().catch(() => ({}));
        
        if (response.status === 409) {
            showToast(data?.error || 'Loc indisponibil.', 'warning');
            return null;
            
        }
        if (response.status === 403) {
            showToast('Acest loc e ocupat de o altă persoană!', 'error');
            return null;
        }
        if (response.status === 401) {
            showToast('Trebuie să te conectezi pentru a ocupa un loc!', 'error');
            return null;
        }

        if (!response.ok) {
            showToast(`Eroare la ocupare (${response.status})`, 'error');
            return null;
        }
        return data;
    })
    .then(data => {
        if (!data) return;
        if (data.warning?.type === "UPCOMING_RESERVATION") {
            showToast(data.warning.message, 'warning', 8000);
        } else {
            showToast('Status actualizat.', 'success', 2500);
        }

        refreshParkingSpots();
    })
    .catch(error => {
        console.error('Eroare la toggle ocupare:', error);
        showToast('Eroare la actualizarea locului!', 'error');
    });
}

function reserveParkingSpot(spotId) {
    console.log('Rezervare loc de parcare:', spotId);

    if (!isLoggedIn()) {
        showToast('Trebuie să te conectezi pentru a rezerva!', 'error');
        return;
    }

    const spot = allParkingSpots.find(s => s.id === spotId);
    
    if (!spot) {
        showToast('Spot invalid!', 'error');
        return;
    }

    // Prevent reserving occupied spot (optional rule)
    if (spot.is_occupied) {
        showToast('Locul este ocupat. Nu poți rezerva acum.', 'warning');
        return;
    }

    // If already reserved by you (active reservation), suggest cancel
    const myActive = getActiveReservationForSpot(spotId);
    if (myActive) {
        showToast('Ai deja o rezervare activă pentru acest loc. O poți anula din popup sau din sidebar.', 'warning', 7000);
        return;
    }

    openReservationModal(spotId, spot);

}

function openReservationModal(spotId, spot) {
    selectedReserveSpotId = spotId;

    const modal = document.getElementById('reservation-modal');
    const startInput = document.getElementById('reserve-start');
    const endInput = document.getElementById('reserve-end');
    const hint = document.getElementById('reservation-modal-hint');

    // Default: start in 5 minutes, end in 120 minutes
    const now = new Date();
    const start = new Date(now.getTime() + 5 * 60 * 1000);
    const end = new Date(now.getTime() + 120 * 60 * 1000);

    function toLocalDatetimeValue(d) {
        const pad = (x) => String(x).padStart(2, '0');
        return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }

    startInput.value = toLocalDatetimeValue(start);
    endInput.value = toLocalDatetimeValue(end);

    hint.textContent = `Spot: ${spot.parking_lot} #${spot.spot_number || spot.id}`;

    modal.style.display = 'block';
}

function closeReservationModal() {
    const modal = document.getElementById('reservation-modal');
    modal.style.display = 'none';
    selectedReserveSpotId = null;
}

function submitReservationModal() {
    if (!selectedReserveSpotId) return;

    const startVal = document.getElementById('reserve-start').value;
    const endVal = document.getElementById('reserve-end').value;

    if (!startVal || !endVal) {
        showToast('Completează start și end.', 'warning');
        return;
    }

    const payload = {
        spot_id: selectedReserveSpotId,
        start_time: isoFromDatetimeLocal(startVal),
        end_time: isoFromDatetimeLocal(endVal)
    };

    fetch('/reservations/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    })
    .then(async (res) => {
        const data = await res.json().catch(() => ({}));

        if (res.status === 401) {
            showToast('Trebuie să te conectezi pentru a rezerva!', 'error');
            return null;
        }
        if (!res.ok) {
            const code = data?.error;
            showToast(reservationErrorMessage(code, res.status), 'warning');
            return null;
        }
        return data;
    })
    .then((data) => {
        if (!data) return;

        // -----

        const startIso = data.start_time || payload.start_time;
        if (startIso) {
            const start = new Date(startIso);
            const deadline = new Date(start.getTime() + 15 * 60 * 1000);
            showToast(
            `Rezervare creată!\n\n` +
            `Dacă nu ocupi locul în 15 minute de la ora de început a rezervării, aceasta se anulează automat.\n\n` +
            `Trebuie să parchezi până la: ${deadline.toLocaleString('ro-RO')}`,
            'warning',
            9000
            );
      }

        // -----

        closeReservationModal();
        return fetchMyReservations().then(() => refreshParkingSpots());
    })
    .catch(err => {
        console.error('Eroare rezervare:', err);
        showToast('Eroare la rezervare! Încearcă din nou.', 'error');
    });
}

function cancelReservation(reservationId) {
    if (!isLoggedIn()) {
        showToast('Trebuie să te conectezi!', 'error');
        return;
    }

    fetch(`/reservations/${reservationId}`, { method: 'DELETE' })
        .then(async (res) => {
            const data = await res.json().catch(() => ({}));

            if (res.status === 401) {
                showToast('Trebuie să te conectezi!', 'error');
                return false;
            }

            if (!res.ok) {
                const code = data?.error;
                showToast(reservationErrorMessage(code, res.status), 'warning');
                return false;
            }

            showToast('Rezervarea a fost anulată.', 'success', 4000);
            return true;
        })
        .then((ok) => {
            if (!ok) return;
            return fetchMyReservations().then(() => refreshParkingSpots());
        })
        .catch(err => {
            console.error('Eroare anulare rezervare:', err);
            showToast('Eroare la anulare! Încearcă din nou.', 'error');
        });
}


// ------
function centerMap(lat, lng, zoom = DEFAULT_ZOOM) {
    map.setView([lat, lng], zoom);
}

function refreshParkingSpots() {
    clearMarkers();
    loadParkingSpots();
}

document.addEventListener('DOMContentLoaded', function() {
    const mapContainer = document.getElementById('map');
    if (mapContainer && !map) {
        initMap();
        initializeFilters();
        startAutoRefresh();
        refreshStats();

        if (window.CURRENT_USER && window.CURRENT_USER.isAuthenticated) {
            fetchMyReservations().then(() => {
                refreshParkingSpots();
            });
        }
    }
});

let allParkingSpots = [];

function initializeFilters() {
    fetch('/parking/spots')
        .then(response => response.json())
        .then(spots => {
            allParkingSpots = spots;
            
            const parkingLots = [...new Set(spots.map(s => s.parking_lot))].sort();
            const select = document.getElementById('filter-parking-lot');
            
            parkingLots.forEach(lot => {
                const option = document.createElement('option');
                option.value = lot;
                option.textContent = lot;
                select.appendChild(option);
            });
            
            restoreFilters();
            applyFilters();
            fetchParkingStatsForSelection({ silent: false });
        })
        .catch(error => console.error('Eroare la popularea filtrelor:', error));
}

function applyFilters() {
    const parkingLotFilter = document.getElementById('filter-parking-lot').value;
    const statusFilter = document.getElementById('filter-status').value;
    
    let visibleCount = 0;
    
    markers.forEach((marker, index) => {
        const spot = allParkingSpots[index];
        
        const parkingLotMatch = !parkingLotFilter || spot.parking_lot === parkingLotFilter;
        const status = getParkingStatus(spot);
        const statusMatch = !statusFilter || status === statusFilter;
        
        if (parkingLotMatch && statusMatch) {
            marker.addTo(map);
            visibleCount++;
        } else {
            if (map.hasLayer(marker)) {
                map.removeLayer(marker);
            }
        }
    });
    
    document.getElementById('spots-count').textContent = `Locuri afișate: ${visibleCount}/${markers.length}`;
    fetchParkingStatsForSelection({ silent: true });

    saveFilters();
    refreshStats();
}

function resetFilters() {
    document.getElementById('filter-parking-lot').value = '';
    document.getElementById('filter-status').value = '';
    localStorage.removeItem('parkingFilters');
    applyFilters();
    fetchParkingStatsForSelection({ silent: false });
    refreshStats();
}

function saveFilters() {
    const filters = {
        parkingLot: document.getElementById('filter-parking-lot').value,
        status: document.getElementById('filter-status').value
    };
    localStorage.setItem('parkingFilters', JSON.stringify(filters));
}

function restoreFilters() {
    const saved = localStorage.getItem('parkingFilters');
    if (saved) {
        try {
            const filters = JSON.parse(saved);
            document.getElementById('filter-parking-lot').value = filters.parkingLot || '';
            document.getElementById('filter-status').value = filters.status || '';
        } catch (e) {
            console.warn('Eroare la restaurarea filtrelor:', e);
        }
    }
}

let AUTO_REFRESH_MS = 5000; // 5s (pick 5–15s)

function startAutoRefresh() {
  setInterval(() => {
    // This will fetch latest spots; since backend finalizes expired ones here,
    // the yellow -> green/red transitions happen automatically.
    refreshParkingSpots();
    fetchParkingStatsForSelection({ silent: true });

    // Optional: also refresh reservation panels if you show them
    // if (window.CURRENT_USER?.isAuthenticated && typeof fetchMyReservations === "function") {
    //   fetchMyReservations();
    // }

    if (window.CURRENT_USER?.isAuthenticated && typeof fetchMyReservations === "function") {
        // Keep sidebar updated, but avoid reloading full history too often
        fetchMyReservations({ forceFull: false });
    }
  }, AUTO_REFRESH_MS);
}