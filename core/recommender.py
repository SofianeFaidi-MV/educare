from pathlib import Path
import json

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

def load_json(name: str) -> dict:
    p = DATA_DIR / name
    return json.loads(p.read_text(encoding="utf-8"))

def list_modules() -> list[str]:
    data = load_json("parcours.json")
    return [p["titre"] for p in data.get("parcours", [])]
