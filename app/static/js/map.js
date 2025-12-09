/**
 * Script pentru initializarea si gestionarea hartii Leaflet
 */

// Coordonatele Universitatii Politehnica Bucuresti
const UPB_LAT = 44.439611824934026;
const UPB_LNG = 26.0492114360659;
const DEFAULT_ZOOM = 16;

let map = null;
let markers = [];
let parkingLotPolygons = [];

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

function initMap() {
    map = L.map('map').setView([UPB_LAT, UPB_LNG], DEFAULT_ZOOM);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
    }).addTo(map);

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
                        <h4>🏢 ${props.name}</h4>
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
    if (spot.reservation && spot.reservation.start_time && spot.reservation.end_time) {
        return 'reserved';
    } else if (spot.is_occupied) {
        return 'occupied';
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

        const buttonText = spot.is_occupied ? '❌ Eliberează' : '✅ Ocupă';
        const buttonClass = spot.is_occupied ? 'btn-danger' : 'btn-success';
        
        popupContent += `
                <button class="btn ${buttonClass} btn-sm" onclick="toggleParkingSpot(${spot.id}, ${spot.is_occupied})">
                    ${buttonText}
                </button>
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

                const buttonText = props.is_occupied ? '❌ Eliberează' : '✅ Ocupă';
                const buttonClass = props.is_occupied ? 'btn-danger' : 'btn-success';
                
                popupContent += `
                        <button class="btn ${buttonClass} btn-sm" onclick="toggleParkingSpot(${props.id}, ${props.is_occupied})">
                            ${buttonText}
                        </button>
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
    .then(response => {
        if (response.status === 409) {
            return response.json().then(data => {
                alert('⚠️ ' + data.error);
                return null;
            });
        }
        if (response.status === 403) {
            alert('❌ Acest loc e ocupat de o altă persoană!');
            return null;
        }
        if (response.status === 401) {
            alert('❌ Trebuie să te conectezi pentru a ocupa un loc!');
            return null;
        }
        if (!response.ok) {
            throw new Error(`Eroare: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data) {
            console.log('✅ Status loc actualizado:', data);
            refreshParkingSpots();
        }
    })
    .catch(error => {
        console.error('Eroare la toggle ocupare:', error);
        alert('Eroare la actualizarea locului!');
    });
}

function reserveParkingSpot(spotId) {
    console.log('Rezervare loc de parcare:', spotId);
    // TODO: Implementare logica pentru rezervare
    alert('Funcționalitate de rezervare - spot #' + spotId);
}

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
    
    saveFilters();
}

function resetFilters() {
    document.getElementById('filter-parking-lot').value = '';
    document.getElementById('filter-status').value = '';
    localStorage.removeItem('parkingFilters');
    applyFilters();
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
