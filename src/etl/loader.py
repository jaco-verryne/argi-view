"""
Load parsed FarmTrace data into the database.

Handles:
1. Dimension tables (phases, blocks, equipment, products) — upsert
2. Fact detail tables (fuel, stock, labour, yield) — append
3. Unified fact_cost table — append, tagged by source module

The fact_cost table is the core of the product. Every cost from every
module lands here with the same schema so the dashboard can aggregate
across all modules.
"""

from datetime import date
from sqlalchemy import select, insert, text
from sqlalchemy.engine import Engine
import pandas as pd

from . import schema


# ── Dimension Loaders ──────────────────────────────────────────────────

def _get_or_create_phase(conn, phase_name: str) -> int:
    """Get phase_id for a phase name, creating it if needed."""
    result = conn.execute(
        select(schema.dim_phase.c.phase_id).where(
            schema.dim_phase.c.name == phase_name
        )
    ).fetchone()
    if result:
        return result[0]

    result = conn.execute(
        insert(schema.dim_phase).values(name=phase_name)
    )
    return result.inserted_primary_key[0]


def _get_or_create_block(conn, block_row: dict, phase_id: int) -> int:
    """Get block_id, creating the block if needed."""
    block_name = str(block_row.get("Block Name", block_row.get("name", "")))
    result = conn.execute(
        select(schema.dim_block.c.block_id).where(
            schema.dim_block.c.name == block_name
        )
    ).fetchone()
    if result:
        return result[0]

    result = conn.execute(
        insert(schema.dim_block).values(
            phase_id=phase_id,
            block_number=block_row.get("Block Number", 0),
            name=block_name,
            hectares=block_row.get("Hectares", 0),
            variety=block_row.get("Variety", ""),
            plant_count=block_row.get("Plant Count"),
            year_planted=block_row.get("Year Planted"),
        )
    )
    return result.inserted_primary_key[0]


def _get_or_create_equipment(conn, vehicle_id: str, name: str,
                             vehicle_type: str) -> int:
    """Get equipment_id, creating the vehicle if needed."""
    result = conn.execute(
        select(schema.dim_equipment.c.equipment_id).where(
            schema.dim_equipment.c.vehicle_id == vehicle_id
        )
    ).fetchone()
    if result:
        return result[0]

    result = conn.execute(
        insert(schema.dim_equipment).values(
            vehicle_id=vehicle_id,
            name=name,
            vehicle_type=vehicle_type,
            fuel_type="diesel",
        )
    )
    return result.inserted_primary_key[0]


def _get_or_create_product(conn, name: str, category: str,
                           unit: str = "", unit_cost: float = 0) -> int:
    """Get product_id, creating the product if needed."""
    result = conn.execute(
        select(schema.dim_product.c.product_id).where(
            schema.dim_product.c.name == name
        )
    ).fetchone()
    if result:
        return result[0]

    result = conn.execute(
        insert(schema.dim_product).values(
            name=name,
            category=category,
            unit=unit,
            unit_cost=unit_cost,
        )
    )
    return result.inserted_primary_key[0]


# ── Block Setup Loader ─────────────────────────────────────────────────

def load_block_setup(engine: Engine, df: pd.DataFrame):
    """Load block setup data into dim_phase and dim_block."""
    with engine.begin() as conn:
        for _, row in df.iterrows():
            phase_id = _get_or_create_phase(conn, row["Phase"])
            _get_or_create_block(conn, row.to_dict(), phase_id)

    print(f"  Loaded {len(df)} blocks")


# ── Fuel Loader ────────────────────────────────────────────────────────

def load_fuel(engine: Engine, df: pd.DataFrame):
    """Load fuel transactions into fact_fuel_detail and fact_cost."""
    cost_rows = []
    detail_rows = []

    with engine.begin() as conn:
        # Build lookup caches
        phase_cache = {}
        equip_cache = {}

        for _, row in df.iterrows():
            phase_name = row["Phase"]
            if phase_name not in phase_cache:
                phase_cache[phase_name] = _get_or_create_phase(
                    conn, phase_name
                )
            phase_id = phase_cache[phase_name]

            vid = row["Vehicle ID"]
            if vid not in equip_cache:
                equip_cache[vid] = _get_or_create_equipment(
                    conn, vid, row["Vehicle Name"], row["Vehicle Type"]
                )
            equip_id = equip_cache[vid]

            row_date = row["Date"]
            if isinstance(row_date, str):
                row_date = date.fromisoformat(row_date)

            detail_rows.append({
                "date": row_date,
                "time": str(row.get("Time", "")),
                "phase_id": phase_id,
                "equipment_id": equip_id,
                "task": row.get("Task", ""),
                "litres": row["Litres"],
                "cost_rands": row["Cost (ZAR)"],
                "pump_reading_start": row.get("Pump Reading Initial"),
                "pump_reading_end": row.get("Pump Reading Final"),
                "hours": row.get("Hours", 0),
                "odometer": row.get("Odometer"),
                "service_interval": row.get("Service Interval", ""),
                "source_file": row.get("source_file", ""),
            })

            cost_rows.append({
                "date": row_date,
                "phase_id": phase_id,
                "block_id": None,
                "category": "diesel",
                "subcategory": row["Vehicle Name"],
                "description": (
                    f"{row['Vehicle Name']} - {row.get('Task', '')}"
                ),
                "quantity": row["Litres"],
                "unit": "litres",
                "cost_rands": row["Cost (ZAR)"],
                "source_module": "fuel",
                "source_file": row.get("source_file", ""),
            })

        if detail_rows:
            conn.execute(insert(schema.fact_fuel_detail), detail_rows)
        if cost_rows:
            conn.execute(insert(schema.fact_cost), cost_rows)

    print(f"  Loaded {len(detail_rows)} fuel transactions")


# ── Stock Movements Loader ─────────────────────────────────────────────

def load_stock(engine: Engine, df: pd.DataFrame):
    """Load stock movements into fact_stock_detail and fact_cost."""
    detail_rows = []
    cost_rows = []

    with engine.begin() as conn:
        phase_cache = {}
        block_cache = {}
        product_cache = {}

        for _, row in df.iterrows():
            phase_name = str(row["Phase"]).strip()
            if not phase_name:
                phase_name = "General"
            if phase_name not in phase_cache:
                phase_cache[phase_name] = _get_or_create_phase(
                    conn, phase_name
                )
            phase_id = phase_cache[phase_name]

            block_name = str(row.get("Block", "")).strip()
            block_id = None
            if block_name and block_name != "nan":
                if block_name not in block_cache:
                    result = conn.execute(
                        select(schema.dim_block.c.block_id).where(
                            schema.dim_block.c.name == block_name
                        )
                    ).fetchone()
                    block_cache[block_name] = result[0] if result else None
                block_id = block_cache[block_name]

            product_name = row["Product Name"]
            if product_name not in product_cache:
                product_cache[product_name] = _get_or_create_product(
                    conn, product_name, row["Product Category"],
                    row.get("Unit", ""), row.get("Unit Cost (ZAR)", 0),
                )
            product_id = product_cache[product_name]

            row_date = row["Date"]
            if isinstance(row_date, str):
                row_date = date.fromisoformat(row_date)

            movement_type = row["Movement Type"]

            detail_rows.append({
                "date": row_date,
                "product_id": product_id,
                "phase_id": phase_id,
                "block_id": block_id,
                "movement_type": movement_type,
                "quantity": row["Quantity"],
                "unit_cost": row.get("Unit Cost (ZAR)", 0),
                "cost_rands": row["Total Cost (ZAR)"],
                "instruction_ref": row.get("Instruction Reference", ""),
                "batch_number": row.get("Batch Number", ""),
                "source_file": row.get("source_file", ""),
            })

            # Only usage and adjustments go into fact_cost
            # GRV (purchases) are tracked in stock detail but aren't
            # operating costs — they're inventory additions
            if movement_type in ("Usage", "Adjustment"):
                category = row["Product Category"].lower()
                # Map product categories to cost categories
                category_map = {
                    "gmi": "chemicals",
                    "workshop": "workshop",
                    "toiletries": "toiletries",
                    "diesel": "diesel",
                }
                cost_category = category_map.get(category, category)

                cost_rows.append({
                    "date": row_date,
                    "phase_id": phase_id,
                    "block_id": block_id,
                    "category": cost_category,
                    "subcategory": product_name,
                    "description": (
                        f"{product_name} - {movement_type}"
                    ),
                    "quantity": abs(row["Quantity"]),
                    "unit": row.get("Unit", ""),
                    "cost_rands": abs(row["Total Cost (ZAR)"]),
                    "source_module": "stock_movement",
                    "source_file": row.get("source_file", ""),
                })

        if detail_rows:
            conn.execute(insert(schema.fact_stock_detail), detail_rows)
        if cost_rows:
            conn.execute(insert(schema.fact_cost), cost_rows)

    print(f"  Loaded {len(detail_rows)} stock movements "
          f"({len(cost_rows)} as costs)")


# ── Labour Loader ──────────────────────────────────────────────────────

def load_labour(engine: Engine, df: pd.DataFrame):
    """Load labour data into fact_labour_detail and fact_cost."""
    detail_rows = []
    cost_rows = []

    with engine.begin() as conn:
        phase_cache = {}
        block_cache = {}

        for _, row in df.iterrows():
            phase_name = row["Phase"]
            if phase_name not in phase_cache:
                phase_cache[phase_name] = _get_or_create_phase(
                    conn, phase_name
                )
            phase_id = phase_cache[phase_name]

            # Section maps to a block
            section = str(row.get("Section", "")).strip()
            block_id = None
            if section and section != "nan":
                if section not in block_cache:
                    result = conn.execute(
                        select(schema.dim_block.c.block_id).where(
                            schema.dim_block.c.name == section
                        )
                    ).fetchone()
                    block_cache[section] = result[0] if result else None
                block_id = block_cache[section]

            row_date = row["Date"]
            if isinstance(row_date, str):
                row_date = date.fromisoformat(row_date)

            detail_rows.append({
                "date": row_date,
                "phase_id": phase_id,
                "block_id": block_id,
                "task": row["Task"],
                "headcount": row.get("Headcount"),
                "hours_per_person": row.get("Hours per Person"),
                "total_hours": row["Total Hours"],
                "rate_per_hour": row.get("Rate per Hour (ZAR)"),
                "cost_rands": row["Total Cost (ZAR)"],
                "source_file": row.get("source_file", ""),
            })

            cost_rows.append({
                "date": row_date,
                "phase_id": phase_id,
                "block_id": block_id,
                "category": "labour",
                "subcategory": row["Task"],
                "description": (
                    f"{row['Task']} - {row.get('Headcount', '?')} people, "
                    f"{row['Total Hours']}hrs"
                ),
                "quantity": row["Total Hours"],
                "unit": "hours",
                "cost_rands": row["Total Cost (ZAR)"],
                "source_module": "labour",
                "source_file": row.get("source_file", ""),
            })

        if detail_rows:
            conn.execute(insert(schema.fact_labour_detail), detail_rows)
        if cost_rows:
            conn.execute(insert(schema.fact_cost), cost_rows)

    print(f"  Loaded {len(detail_rows)} labour entries")


# ── Harvest Loader ─────────────────────────────────────────────────────

def load_harvest(engine: Engine, df: pd.DataFrame):
    """Load harvesting data into fact_yield.

    Harvest data doesn't go into fact_cost — it's the output side
    (kg produced), not the input side (cost incurred). It's used for
    cost-per-kg calculations in the dashboard.
    """
    rows = []

    with engine.begin() as conn:
        phase_cache = {}
        block_cache = {}

        for _, row in df.iterrows():
            phase_name = row["Phase"]
            if phase_name not in phase_cache:
                phase_cache[phase_name] = _get_or_create_phase(
                    conn, phase_name
                )
            phase_id = phase_cache[phase_name]

            block_name = str(row.get("Block", "")).strip()
            block_id = None
            if block_name and block_name != "nan":
                if block_name not in block_cache:
                    result = conn.execute(
                        select(schema.dim_block.c.block_id).where(
                            schema.dim_block.c.name == block_name
                        )
                    ).fetchone()
                    block_cache[block_name] = result[0] if result else None
                block_id = block_cache[block_name]

            if block_id is None:
                continue  # Can't record yield without a block

            row_date = row["Date"]
            if isinstance(row_date, str):
                row_date = date.fromisoformat(row_date)

            rows.append({
                "date": row_date,
                "phase_id": phase_id,
                "block_id": block_id,
                "variety": row.get("Variety", ""),
                "kg_harvested": row["Kg Harvested"],
                "lug_count": row.get("Lug Count"),
                "pickers": row.get("Pickers"),
                "source_file": row.get("source_file", ""),
            })

        if rows:
            conn.execute(insert(schema.fact_yield), rows)

    print(f"  Loaded {len(rows)} harvest records")


# ── Budget Loader ──────────────────────────────────────────────────────

def load_budget(engine: Engine, budgets: list[dict]):
    """Load budget data.

    budgets: list of dicts with keys: year, month, category, budget_rands
    """
    with engine.begin() as conn:
        if budgets:
            conn.execute(insert(schema.fact_budget), budgets)
    print(f"  Loaded {len(budgets)} budget entries")
