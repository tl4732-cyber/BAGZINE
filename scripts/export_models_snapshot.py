#!/usr/bin/env python3
"""Write web/public/data/models.json from the local analytics API view."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "public" / "data" / "models.json"

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://lvbp:lvbp_dev@localhost:5433/luxury_bags",
)
sys.path.insert(0, str(ROOT))

from api import queries  # noqa: E402
from api.schemas import ModelSummary  # noqa: E402
from db.session import get_session_factory  # noqa: E402


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with get_session_factory()() as db:
        models = [
            ModelSummary(**row).model_dump(mode="json")
            for row in queries.fetch_models(db)
        ]
    OUT.write_text(json.dumps(models, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(models)} models to {OUT}")


if __name__ == "__main__":
    main()
