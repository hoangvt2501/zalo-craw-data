from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import psycopg
from psycopg.types.json import Jsonb

AI_WORKER_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(AI_WORKER_ROOT))

from app.config.settings import load_settings  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed properties from hotels.csv")
    parser.add_argument(
        "--csv",
        default=str(PROJECT_ROOT / "data" / "hotels.csv"),
        help="Path to source hotels.csv",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    settings = load_settings()
    rows = 0

    with psycopg.connect(settings.database_url) as conn:
        with conn.transaction():
            with csv_path.open("r", encoding="utf-8-sig", newline="") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if not row.get("id") or not row.get("name"):
                        continue
                    conn.execute(
                        """
                        INSERT INTO properties (id, name, address, district, province, metadata)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (id) DO UPDATE SET
                          name = EXCLUDED.name,
                          address = EXCLUDED.address,
                          district = EXCLUDED.district,
                          province = EXCLUDED.province,
                          metadata = EXCLUDED.metadata,
                          updated_at = now()
                        """,
                        (
                            row.get("id"),
                            row.get("name"),
                            row.get("address"),
                            row.get("district"),
                            row.get("province"),
                            Jsonb({"source_csv": str(csv_path)}),
                        ),
                    )
                    rows += 1

    print(f"[SEED] upserted properties: {rows}")


if __name__ == "__main__":
    main()
