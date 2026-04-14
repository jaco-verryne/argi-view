"""
Database schema for AgriView.

Creates all dimension and fact tables. Works with SQLite (local dev)
and PostgreSQL (Supabase production). Uses SQLAlchemy for portability.
"""

from sqlalchemy import (
    Column, Integer, String, Float, Date, Text, Boolean,
    ForeignKey, Index, MetaData, Table, create_engine,
)

metadata = MetaData()

# ── Dimension Tables ───────────────────────────────────────────────────

dim_phase = Table(
    "dim_phase", metadata,
    Column("phase_id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True),
)

dim_block = Table(
    "dim_block", metadata,
    Column("block_id", Integer, primary_key=True, autoincrement=True),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("block_number", Integer, nullable=False),
    Column("name", String, nullable=False),
    Column("hectares", Float, nullable=False),
    Column("variety", String),
    Column("plant_count", Integer),
    Column("year_planted", Integer),
)

dim_equipment = Table(
    "dim_equipment", metadata,
    Column("equipment_id", Integer, primary_key=True, autoincrement=True),
    Column("vehicle_id", String, nullable=False, unique=True),
    Column("name", String, nullable=False),
    Column("vehicle_type", String, nullable=False),
    Column("fuel_type", String, default="diesel"),
)

dim_product = Table(
    "dim_product", metadata,
    Column("product_id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False, unique=True),
    Column("category", String, nullable=False),
    Column("unit", String),
    Column("unit_cost", Float),
    Column("package_size", Float),
)

# ── Fact Tables ────────────────────────────────────────────────────────

# The unified cost table — this is the core of the product
fact_cost = Table(
    "fact_cost", metadata,
    Column("cost_id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("block_id", Integer, ForeignKey("dim_block.block_id")),
    Column("category", String, nullable=False),
    Column("subcategory", String),
    Column("description", Text),
    Column("quantity", Float),
    Column("unit", String),
    Column("cost_rands", Float, nullable=False),
    Column("source_module", String, nullable=False),
    Column("source_file", String),
    Index("idx_cost_date", "date"),
    Index("idx_cost_phase_date", "phase_id", "date"),
    Index("idx_cost_block_date", "block_id", "date"),
    Index("idx_cost_category", "category", "date"),
)

# Fuel detail — drill-down for fuel-specific analysis
fact_fuel_detail = Table(
    "fact_fuel_detail", metadata,
    Column("txn_id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("time", String),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("equipment_id", Integer, ForeignKey("dim_equipment.equipment_id"),
           nullable=False),
    Column("task", String),
    Column("litres", Float, nullable=False),
    Column("cost_rands", Float, nullable=False),
    Column("pump_reading_start", Float),
    Column("pump_reading_end", Float),
    Column("hours", Float),
    Column("odometer", Float),
    Column("service_interval", String),
    Column("source_file", String),
    Index("idx_fuel_date", "date"),
    Index("idx_fuel_equip", "equipment_id", "date"),
)

# Stock detail — drill-down for chemical/product analysis
fact_stock_detail = Table(
    "fact_stock_detail", metadata,
    Column("movement_id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("product_id", Integer, ForeignKey("dim_product.product_id"),
           nullable=False),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("block_id", Integer, ForeignKey("dim_block.block_id")),
    Column("movement_type", String, nullable=False),
    Column("quantity", Float, nullable=False),
    Column("unit_cost", Float),
    Column("cost_rands", Float, nullable=False),
    Column("instruction_ref", String),
    Column("batch_number", String),
    Column("source_file", String),
    Index("idx_stock_date", "date"),
    Index("idx_stock_product", "product_id", "date"),
    Index("idx_stock_movement_type", "movement_type", "date"),
)

# Labour detail — drill-down for labour analysis
fact_labour_detail = Table(
    "fact_labour_detail", metadata,
    Column("entry_id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("block_id", Integer, ForeignKey("dim_block.block_id")),
    Column("task", String, nullable=False),
    Column("headcount", Integer),
    Column("hours_per_person", Float),
    Column("total_hours", Float, nullable=False),
    Column("rate_per_hour", Float),
    Column("cost_rands", Float, nullable=False),
    Column("source_file", String),
    Index("idx_labour_date", "date"),
    Index("idx_labour_phase", "phase_id", "date"),
)

# Yield / harvest data
fact_yield = Table(
    "fact_yield", metadata,
    Column("yield_id", Integer, primary_key=True, autoincrement=True),
    Column("date", Date, nullable=False),
    Column("phase_id", Integer, ForeignKey("dim_phase.phase_id"),
           nullable=False),
    Column("block_id", Integer, ForeignKey("dim_block.block_id"),
           nullable=False),
    Column("variety", String),
    Column("kg_harvested", Float, nullable=False),
    Column("lug_count", Integer),
    Column("pickers", Integer),
    Column("source_file", String),
    Index("idx_yield_date", "date"),
    Index("idx_yield_block", "block_id", "date"),
)

# Budget (for budget vs actual)
fact_budget = Table(
    "fact_budget", metadata,
    Column("budget_id", Integer, primary_key=True, autoincrement=True),
    Column("year", Integer, nullable=False),
    Column("month", Integer, nullable=False),
    Column("category", String, nullable=False),
    Column("budget_rands", Float, nullable=False),
)


def create_all(engine):
    """Create all tables. Safe to call multiple times (IF NOT EXISTS)."""
    metadata.create_all(engine)


def drop_all(engine):
    """Drop all tables. Use with caution."""
    metadata.drop_all(engine)


def get_engine(url: str = "sqlite:///data/agriview.db"):
    """Create a database engine.

    Default: SQLite file in the data directory.
    Production: Pass a PostgreSQL URL from Supabase.
    """
    return create_engine(url)
