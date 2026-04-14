"""
Run the full ETL pipeline.

Usage:
    python -m src.etl.run                        # defaults: synthetic data → SQLite
    python -m src.etl.run --data-dir data/raw/real
    python -m src.etl.run --db-url postgresql://...
"""

import argparse
from pathlib import Path

from . import schema
from .parsers import (
    parse_block_setup,
    parse_fuel_transactions,
    parse_stock_movements,
    parse_labour,
    parse_harvesting,
)
from .loader import (
    load_block_setup,
    load_fuel,
    load_stock,
    load_labour,
    load_harvest,
)


def run(data_dir: Path, db_url: str, fresh: bool = False):
    """Execute the full ETL pipeline."""
    engine = schema.get_engine(db_url)

    if fresh:
        print("Dropping existing tables...")
        schema.drop_all(engine)

    print("Creating tables (if not exists)...")
    schema.create_all(engine)

    # ── 1. Block setup (must load first — dimensions) ─────────────────
    block_file = data_dir / "block_setup.csv"
    if block_file.exists():
        print(f"\n[1/5] Block setup: {block_file}")
        df = parse_block_setup(block_file)
        load_block_setup(engine, df)
    else:
        print(f"\n[1/5] Block setup: SKIPPED (no file at {block_file})")

    # ── 2. Fuel transactions ──────────────────────────────────────────
    fuel_file = data_dir / "fuel_transactions.csv"
    if fuel_file.exists():
        print(f"\n[2/5] Fuel: {fuel_file}")
        df = parse_fuel_transactions(fuel_file)
        load_fuel(engine, df)
    else:
        print(f"\n[2/5] Fuel: SKIPPED (no file at {fuel_file})")

    # ── 3. Stock movements ────────────────────────────────────────────
    stock_file = data_dir / "stock_movements.csv"
    if stock_file.exists():
        print(f"\n[3/5] Stock movements: {stock_file}")
        df = parse_stock_movements(stock_file)
        load_stock(engine, df)
    else:
        print(f"\n[3/5] Stock movements: SKIPPED (no file at {stock_file})")

    # ── 4. Labour ─────────────────────────────────────────────────────
    labour_file = data_dir / "labour.csv"
    if labour_file.exists():
        print(f"\n[4/5] Labour: {labour_file}")
        df = parse_labour(labour_file)
        load_labour(engine, df)
    else:
        print(f"\n[4/5] Labour: SKIPPED (no file at {labour_file})")

    # ── 5. Harvesting ─────────────────────────────────────────────────
    harvest_file = data_dir / "harvesting.csv"
    if harvest_file.exists():
        print(f"\n[5/5] Harvesting: {harvest_file}")
        df = parse_harvesting(harvest_file)
        load_harvest(engine, df)
    else:
        print(f"\n[5/5] Harvesting: SKIPPED (no file at {harvest_file})")

    print("\nETL complete.")
    return engine


def main():
    parser = argparse.ArgumentParser(description="AgriView ETL Pipeline")
    parser.add_argument(
        "--data-dir",
        default="data/raw/synthetic",
        help="Directory containing FarmTrace CSV exports",
    )
    parser.add_argument(
        "--db-url",
        default="sqlite:///data/agriview.db",
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--fresh",
        action="store_true",
        help="Drop and recreate all tables before loading",
    )
    args = parser.parse_args()

    run(Path(args.data_dir), args.db_url, args.fresh)


if __name__ == "__main__":
    main()
