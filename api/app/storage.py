from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_FILE = DATA_DIR / "mobile_weapons.json"


def load_data():

    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read()
            if content.strip():
                return json.loads(content)
    return []


def save_data(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
