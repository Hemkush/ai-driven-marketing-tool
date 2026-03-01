import json
from pathlib import Path
from datetime import datetime, timezone

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
FILE_PATH = DATA_DIR / "generations.jsonl"

def save_generation(payload: dict, result: dict) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": payload,
        "output": result,
    }
    with FILE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record

def list_generations(limit: int = 20) -> list[dict]:
    if not FILE_PATH.exists():
        return []
    lines = FILE_PATH.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return records[-limit:][::-1]
