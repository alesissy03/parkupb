#!/usr/bin/env python3
"""
Script pentru a exporta locurile de parcare curente din BD
și a crea un fișier de seed pentru viitoare recreări ale BD.
"""

import json
import sys
from app import create_app, db
from app.models import ParkingLot, ParkingSpot

def export_parking_data():
    """Exportă datele de parking din BD și le scrie în parking_seed.json"""
    app = create_app()
    
    with app.app_context():
        lots = ParkingLot.query.all()
        spots = ParkingSpot.query.all()
        
        print(f"📊 Exporting {len(lots)} lots și {len(spots)} spots...")
        
        export_data = {
            "parking_lots": [],
            "parking_spots": []
        }
        
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
        
        output_file = "parking_seed.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"Datele au fost salvate în '{output_file}'")
        print(f"   - {len(export_data['parking_lots'])} parking lots")
        print(f"   - {len(export_data['parking_spots'])} parking spots")
        
        return output_file

if __name__ == "__main__":
    try:
        export_parking_data()
    except Exception as e:
        print(f"Eroare: {e}")
        sys.exit(1)
