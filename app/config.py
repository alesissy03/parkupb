import os
import json
from pathlib import Path

# directorul de bază al proiectului (folderul "parkupb")
BASE_DIR = Path(__file__).resolve().parent.parent

def load_config(env: str = "development") -> dict:
    """
    Task 1 - MINIM NECESAR ca să pornească aplicația:
    - citește config.json
    - setează SQLALCHEMY_DATABASE_URI
    - pune câteva valori default
    """
    config_path = BASE_DIR / "config.json"

    data = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    # din config.json ai deja:
    # "db_url": "sqlite:///parking.db"
    db_url = data.get("db_url", "sqlite:///parking.db")

    config = {
        # OBLIGATORIU pentru Flask-SQLAlchemy, altfel dă eroarea pe care o vezi
        "SQLALCHEMY_DATABASE_URI": db_url,
        # opțional dar recomandat
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        # cheie de dev
        "SECRET_KEY": data.get("secret_key", "secret"),
        # din config.json (le vei folosi când faci harta)
        "DEFAULT_ZOOM": data.get("default_zoom", 16),
        "DEFAULT_CENTER": data.get("default_center", [44.435, 26.05]),
    }

    # TODO (restul lui Task 1):
    # - poți adăuga aici setări diferite pentru "production", dacă e cazul

    return config
