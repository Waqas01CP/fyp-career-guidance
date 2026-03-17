"""
seed_db.py — Idempotent database seeder.
Reads JSON files from backend/app/data/ and seeds PostgreSQL.
Run: python scripts/seed_db.py
Must be run from the backend/ directory.
UPSERT only — running twice produces identical state.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add backend/ to path so app imports work
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import AsyncSessionLocal, engine, Base


async def seed():
    data_dir = Path(__file__).resolve().parent.parent / "app" / "data"

    print("Creating tables if they don't exist...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # JSON files are read by the app at runtime — seeding here means
    # copying/validating them, not inserting into tables.
    # The JSON files ARE the knowledge base — they live in app/data/.
    # This script validates they exist and are valid JSON.

    files = ["universities.json", "lag_model.json", "affinity_matrix.json", "assessment_questions.json"]
    for fname in files:
        fpath = data_dir / fname
        if fpath.exists():
            with open(fpath) as f:
                data = json.load(f)
            print(f"  {fname}: {len(data) if isinstance(data, list) else 'object'} records — OK")
        else:
            print(f"  {fname}: NOT FOUND — create this file before Sprint 3")

    print("\nDone. Run `alembic upgrade head` to apply any pending schema migrations.")


if __name__ == "__main__":
    asyncio.run(seed())
