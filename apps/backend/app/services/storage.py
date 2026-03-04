import json
from app.db import SessionLocal
from app.models import Generation

def save_generation(payload: dict, result: dict) -> dict:
    with SessionLocal() as db:
        row = Generation(
            input_json=json.dumps(payload),
            output_json=json.dumps(result),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "id": row.id,
            "timestamp": row.timestamp.isoformat(),
            "input": payload,
            "output": result,
        }

def list_generations(limit: int = 20) -> list[dict]:
    with SessionLocal() as db:
        rows = db.query(Generation).order_by(Generation.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "input": json.loads(r.input_json),
                "output": json.loads(r.output_json),
            }
            for r in rows
        ]
