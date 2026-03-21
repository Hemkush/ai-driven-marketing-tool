import json
from app.db import SessionLocal
from app.models import Generation


def save_generation(payload: dict, result: dict, project_id: int | None = None) -> dict:
    with SessionLocal() as db:
        row = Generation(
            project_id=project_id,
            input_json=json.dumps(payload),
            output_json=json.dumps(result),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return {
            "id": row.id,
            "timestamp": row.timestamp.isoformat(),
            "project_id": row.project_id,
            "input": payload,
            "output": result,
        }


def list_generations(limit: int = 20, project_id: int | None = None) -> list[dict]:
    with SessionLocal() as db:
        query = db.query(Generation)
        if project_id is not None:
            query = query.filter(Generation.project_id == project_id)
        rows = query.order_by(Generation.id.desc()).limit(limit).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp.isoformat(),
                "project_id": r.project_id,
                "input": json.loads(r.input_json),
                "output": json.loads(r.output_json),
            }
            for r in rows
        ]
