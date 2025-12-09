import os
import json
from pathlib import Path

# directorul de baza al proiectului (folderul "parkupb")
BASE_DIR = Path(__file__).resolve().parent.parent

def is_wsl():
    try:
        with open('/proc/version', 'r') as f:
            return 'microsoft' in f.read().lower() or 'wsl' in f.read().lower()
    except:
        return False

def get_db_path():
    instance_dir = BASE_DIR / "instance"
    instance_dir.mkdir(exist_ok=True)
    db_file = instance_dir / "parking.db"
    
    db_path = str(db_file).replace("\\", "/")
    return f"sqlite:///{db_path}"

def load_config(env: str = "development") -> dict:
    """
    MINIM NECESAR ca să pornească aplicația:
    - citește config.json
    - setează SQLALCHEMY_DATABASE_URI
    - pune câteva valori default
    """
    config_path = BASE_DIR / "config.json"

    data = {}
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

    db_url = get_db_path()

    config = {
        "SQLALCHEMY_DATABASE_URI": db_url,
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        "SECRET_KEY": data.get("secret_key", "secret"),
        "DEFAULT_ZOOM": data.get("default_zoom", 16),
        "DEFAULT_CENTER": data.get("default_center", [44.435, 26.05]),
    }

    return config
