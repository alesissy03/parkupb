from app import create_app
from app.extensions import db
from app.models import ParkingSpot, ParkingLot
from datetime import datetime, timedelta
import json
import os

app = create_app()

def load_seed_data():
    """Încarca datele de seed din parking_seed.json daca exista"""
    seed_file = os.path.join(os.path.dirname(__file__), 'parking_seed.json')
    
    if not os.path.exists(seed_file):
        print(f"Fisierul {seed_file} nu exista.")
        return None
    
    try:
        with open(seed_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Datele sunt incarcate din {seed_file}")
        return data
    except Exception as e:
        print(f"Eroare la incarcarea datelor: {e}")
        return None

with app.app_context():
    db.create_all()
    print("Baza de date creata cu succes.")
    
    existing_lots = ParkingLot.query.first()
    existing_spots = ParkingSpot.query.first()
    
    if not existing_lots and not existing_spots:
        
        seed_data = load_seed_data()
        
        if seed_data and seed_data.get('parking_lots'):
            for lot_data in seed_data['parking_lots']:
                lot = ParkingLot(
                    name=lot_data.get('name'),
                    campus_zone=lot_data.get('campus_zone'),
                    lat_center=lot_data.get('lat_center'),
                    lng_center=lot_data.get('lng_center'),
                    total_spots=lot_data.get('total_spots'),
                    columns=lot_data.get('columns'),
                    polygon_geojson=lot_data.get('polygon_geojson')
                )
                db.session.add(lot)
            db.session.commit()
            print(f"Adaugate {len(seed_data['parking_lots'])} parking lots!")
            
            if seed_data.get('parking_spots'):
                for spot_data in seed_data['parking_spots']:
                    spot = ParkingSpot(
                        parking_lot=spot_data.get('parking_lot'),
                        spot_number=spot_data.get('spot_number'),
                        latitude=spot_data.get('latitude'),
                        longitude=spot_data.get('longitude'),
                        is_occupied=spot_data.get('is_occupied', False),
                        polygon_geojson=spot_data.get('polygon_geojson')
                    )
                    db.session.add(spot)
                db.session.commit()
                print(f"Adaugate {len(seed_data['parking_spots'])} parking spots!")
        else:
            test_spots = [
                ParkingSpot(
                    parking_lot="Parcare A",
                    latitude=44.4400,
                    longitude=26.0490,
                    is_occupied=False,
                    reservation_start_time=None,
                    reservation_end_time=None
                ),
                ParkingSpot(
                    parking_lot="Parcare A",
                    latitude=44.4401,
                    longitude=26.0491,
                    is_occupied=True,
                    reservation_start_time=None,
                    reservation_end_time=None
                ),
                ParkingSpot(
                    parking_lot="Parcare B",
                    latitude=44.4395,
                    longitude=26.0485,
                    is_occupied=False,
                    reservation_start_time=datetime.utcnow(),
                    reservation_end_time=datetime.utcnow() + timedelta(hours=2)
                ),
                ParkingSpot(
                    parking_lot="Parcare B",
                    latitude=44.4396,
                    longitude=26.0486,
                    is_occupied=False,
                    reservation_start_time=None,
                    reservation_end_time=None
                ),
                ParkingSpot(
                    parking_lot="Parcare C",
                    latitude=44.4405,
                    longitude=26.0495,
                    is_occupied=False,
                    reservation_start_time=None,
                    reservation_end_time=None
                ),
                ParkingSpot(
                    parking_lot="Parcare C",
                    latitude=44.4406,
                    longitude=26.0496,
                    is_occupied=True,
                    reservation_start_time=None,
                    reservation_end_time=None
                ),
            ]
            
            db.session.add_all(test_spots)
            db.session.commit()
            print(f"Adaugate {len(test_spots)} locuri de parcare test!")
    else:
        print("Baza de date contine locuri de parcare")
