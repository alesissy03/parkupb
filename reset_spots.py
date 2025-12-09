#!/usr/bin/env python3
"""
Script pentru a regenera spoturile din lot-urile existente și a salva în seed.

Detalii:
  1. Ștergă spoturile vechi
  2. Generează spoturile noi pe baza lot-urilor (cu poligoane)
  3. Salvează configurația în parking_seed.json
"""

import json
import math
import sys
from app import create_app, db
from app.models import ParkingLot, ParkingSpot

def generate_spots_for_lot(lot):
    if not lot.total_spots:
        return []
    
    try:
        import ast
        if isinstance(lot.polygon_geojson, str):
            poly_dict = ast.literal_eval(lot.polygon_geojson)
        else:
            poly_dict = lot.polygon_geojson
        
        coords = poly_dict['coordinates'][0]
        
        lngs = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        
        left_lng = min(lngs)
        right_lng = max(lngs)
        bottom_lat = min(lats)
        top_lat = max(lats)
    except Exception as e:
        if not lot.lat_center or not lot.lng_center:
            return []
        top_lat = lot.lat_center + 0.0005
        bottom_lat = lot.lat_center - 0.0005
        left_lng = lot.lng_center - 0.001
        right_lng = lot.lng_center + 0.001
    
    total_spots = lot.total_spots
    columns = lot.columns or 1
    rows = math.ceil(total_spots / columns)
    
    spots = []
    for idx in range(total_spots):
        r = idx // columns
        c = idx % columns
        
        u = (c + 0.5) / columns
        v = (r + 0.5) / rows
        lat = top_lat + v * (bottom_lat - top_lat)
        lng = left_lng + u * (right_lng - left_lng)
        
        spot_width = (right_lng - left_lng) / columns
        spot_height = (top_lat - bottom_lat) / rows
        
        spot_left = left_lng + c * spot_width
        spot_right = spot_left + spot_width
        spot_top = top_lat - r * spot_height
        spot_bottom = spot_top - spot_height
        
        # GeoJSON Polygon
        spot_polygon = {
            "type": "Polygon",
            "coordinates": [[
                [spot_left, spot_bottom],
                [spot_right, spot_bottom],
                [spot_right, spot_top],
                [spot_left, spot_top],
                [spot_left, spot_bottom]
            ]]
        }
        
        spot_data = {
            "id": None,
            "parking_lot": lot.name,
            "spot_number": str(idx + 1),
            "latitude": lat,
            "longitude": lng,
            "is_occupied": False,
            "polygon_geojson": json.dumps(spot_polygon)
        }
        spots.append(spot_data)
    
    return spots

def regenerate_all_spots():
    """Regenerează toate spoturile din lots și salvează"""
    app = create_app()
    
    with app.app_context():
        lots = ParkingLot.query.all()
        
        if not lots:
            print("Nu sunt parking lots în BD!")
            return False
        
        print(f"Regenerez spoturile pentru {len(lots)} lots...")
        
        existing = ParkingSpot.query.all()
        if existing:
            print(f"Sterg {len(existing)} spoturile vechi...")
            for spot in existing:
                db.session.delete(spot)
            db.session.commit()
        
        total_created = 0
        for lot in lots:
            spots_data = generate_spots_for_lot(lot)
            print(f"Lot '{lot.name}' ({lot.total_spots} spots)...")
            
            for spot_data in spots_data:
                spot = ParkingSpot(
                    parking_lot=spot_data['parking_lot'],
                    spot_number=spot_data['spot_number'],
                    latitude=spot_data['latitude'],
                    longitude=spot_data['longitude'],
                    is_occupied=spot_data['is_occupied'],
                    polygon_geojson=spot_data['polygon_geojson']
                )
                db.session.add(spot)
                total_created += 1
        
        db.session.commit()
        print(f"\nAu fost generate {total_created} spoturi!")
        
        print(f"\nSalvez configuratia in parking_seed.json...")
        save_seed_file()
        
        return True

def save_seed_file():
    """Salveaza configuratia curenta in parking_seed.json"""
    app = create_app()
    
    with app.app_context():
        lots = ParkingLot.query.all()
        spots = ParkingSpot.query.all()
        
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
        
        print(f"Fisierul '{output_file}' actualizat:")
        print(f"{len(export_data['parking_lots'])} parking lots")
        print(f"{len(export_data['parking_spots'])} parking spots")

if __name__ == "__main__":
    try:
        success = regenerate_all_spots()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Eroare: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print('✅ Loc de parcare nou adaugat!')
    print(f'   Nume: Parcarea Precis')
    print(f'   Latitudine: 44.434856')
    print(f'   Longitudine: 26.048233')
    
    # Verifica
    all_spots = ParkingSpot.query.all()
    print(f'✅ Total locuri in baza: {len(all_spots)}')
