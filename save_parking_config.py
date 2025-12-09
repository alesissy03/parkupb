#!/usr/bin/env python3
"""
Script helper pentru a exporta locurile de parcare curente.
"""

import json
import sys
from app import create_app, db
from app.models import ParkingLot, ParkingSpot

def save_parking_config():
    """Salveaza configuratia curenta de parking"""
    app = create_app()
    
    with app.app_context():
        lots = ParkingLot.query.all()
        spots = ParkingSpot.query.all()
        
        print(f"Salvez {len(lots)} lots si {len(spots)} spots...")
        
        # Construiește structura de export
        export_data = {
            "parking_lots": [],
            "parking_spots": []
        }
        
        # Exportă lots
        for lot in lots:
            lot_data = {
                "id": lot.id,
                "name": lot.name,
                "campus_zone": lot.campus_zone,
                "lat_center": lot.lat_center,
                "lng_center": lot.lng_center,
                "total_spots": lot.total_spots,
                "columns": lot.columns,
                "polygon_geojson": lot.polygon_geojson
            }
            export_data["parking_lots"].append(lot_data)
        
        # Exportă spots
        for spot in spots:
            spot_data = {
                "id": spot.id,
                "parking_lot": spot.parking_lot,
                "spot_number": spot.spot_number,
                "latitude": spot.latitude,
                "longitude": spot.longitude,
                "is_occupied": spot.is_occupied,
                "polygon_geojson": spot.polygon_geojson
            }
            export_data["parking_spots"].append(spot_data)
        
        # Scrie în fișier JSON
        output_file = "parking_seed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nConfigurattia salvata in '{output_file}':")
        print(f"{len(export_data['parking_lots'])} parking lots")
        print(f"{len(export_data['parking_spots'])} parking spots")
        print(f"\nDatele vor fi incarcate automat la urmatoarea rulare a create_db.py")
        
        return output_file

if __name__ == "__main__":
    try:
        save_parking_config()
    except Exception as e:
        print(f"Eroare: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
