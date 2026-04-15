"""
Run ETL pipeline for real FarmTrace exports.

Usage:
    python -m src.etl.run_real                          # defaults
    python -m src.etl.run_real --data-dir data/raw/real
    python -m src.etl.run_real --diesel-price 25.50
"""

import argparse
import glob
from datetime import date
from pathlib import Path

from . import schema
from .parsers_real import (
    parse_block_setup_real,
    parse_fuel_transactions_real,
    parse_stock_movements_real,
    parse_labour_real,
)
from .loader import (
    load_block_setup,
    load_fuel,
    load_stock,
    load_labour,
)


def _find_file(data_dir: Path, pattern: str) -> Path | None:
    """Find a file matching a glob pattern in the data directory."""
    matches = list(data_dir.glob(pattern))
    if matches:
        # Take the most recent file if multiple
        return max(matches, key=lambda p: p.stat().st_mtime)
    return None


def run_real(data_dir: Path, db_url: str, fresh: bool = False,
             diesel_price: float = 24.50, labour_date=None):
    """Execute the ETL pipeline for real FarmTrace exports."""
    engine = schema.get_engine(db_url)

    if fresh:
        print("Dropping existing tables...")
        schema.drop_all(engine)

    print("Creating tables (if not exists)...")
    schema.create_all(engine)

    # ── 1. Block setup / Annual Census (must load first — dimensions) ─
    census_file = _find_file(data_dir, "Annual*.*")
    if census_file:
        print(f"\n[1/4] Block setup: {census_file.name}")
        df = parse_block_setup_real(census_file)
        load_block_setup(engine, df)
    else:
        print("\n[1/4] Block setup: SKIPPED (no Annual* file found)")

    # ── 2. Fuel transactions ──────────────────────────────────────────
    fuel_file = _find_file(data_dir, "Fuel*.*")
    if fuel_file:
        print(f"\n[2/4] Fuel: {fuel_file.name}")
        print(f"  Diesel price: R{diesel_price}/litre")
        df = parse_fuel_transactions_real(fuel_file, diesel_price)
        load_fuel(engine, df)
    else:
        print("\n[2/4] Fuel: SKIPPED (no Fuel* file found)")

    # ── 3. Stock movements ────────────────────────────────────────────
    stock_file = _find_file(data_dir, "Stock*.*")
    if stock_file:
        print(f"\n[3/4] Stock movements: {stock_file.name}")
        df = parse_stock_movements_real(stock_file)
        load_stock(engine, df)
    else:
        print("\n[3/4] Stock movements: SKIPPED (no Stock* file found)")

    # ── 4. Labour ─────────────────────────────────────────────────────
    labour_file = _find_file(data_dir, "Staff*.*")
    if labour_file:
        print(f"\n[4/4] Labour: {labour_file.name}")
        if labour_date is None:
            labour_date = date.today()
        print(f"  Note: Labour is a period summary — "
              f"assigning all to {labour_date}")
        df = parse_labour_real(labour_file, report_date=labour_date)
        load_labour(engine, df)
    else:
        print("\n[4/4] Labour: SKIPPED (no Staff* file found)")

    print("\nETL complete.")

    return engine


def main():
    parser = argparse.ArgumentParser(
        description="AgriView ETL — Real FarmTrace Data"
    )
    parser.add_argument(
        "--data-dir", default="data/raw/real",
        help="Directory containing real FarmTrace exports",
    )
    parser.add_argument(
        "--db-url", default="sqlite:///data/agriview.db",
        help="SQLAlchemy database URL",
    )
    parser.add_argument(
        "--fresh", action="store_true",
        help="Drop and recreate all tables before loading",
    )
    parser.add_argument(
        "--diesel-price", type=float, default=24.50,
        help="Diesel price in ZAR per litre (default: 24.50)",
    )
    parser.add_argument(
        "--labour-date", default=None,
        help="Date to assign labour entries (YYYY-MM-DD). "
             "Default: today. Labour export is a period summary.",
    )
    args = parser.parse_args()

    labour_date = None
    if args.labour_date:
        labour_date = date.fromisoformat(args.labour_date)

    run_real(
        Path(args.data_dir), args.db_url, args.fresh,
        args.diesel_price, labour_date,
    )


if __name__ == "__main__":
    main()
