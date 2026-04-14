"""
Data layer for the AgriView dashboard.

All database queries live here. Each function returns a DataFrame
ready for charting. Streamlit caching is applied at the page level,
not here — this keeps the data layer framework-agnostic for testing.
"""

from sqlalchemy import create_engine, text
import pandas as pd

_ENGINE = None


def _default_db_url() -> str:
    """Get DB URL from Streamlit secrets, env var, or fallback to SQLite."""
    try:
        import streamlit as st
        return st.secrets["database"]["url"]
    except Exception:
        pass
    import os
    return os.environ.get("DATABASE_URL", "sqlite:///data/agriview.db")


def get_engine(db_url: str | None = None):
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(db_url or _default_db_url())
    return _ENGINE


def _query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Run a SQL query and return a DataFrame."""
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)


# ── Filter helpers ────────────────────────────────────────────────────


def get_phases() -> list[str]:
    """Return all phase names."""
    df = _query("SELECT name FROM dim_phase ORDER BY name")
    return df["name"].tolist()


def get_date_range() -> tuple:
    """Return (min_date, max_date) from fact_cost."""
    df = _query("SELECT MIN(date) as mn, MAX(date) as mx FROM fact_cost")
    return pd.to_datetime(df["mn"][0]).date(), pd.to_datetime(df["mx"][0]).date()


def get_categories() -> list[str]:
    """Return distinct cost categories."""
    df = _query("SELECT DISTINCT category FROM fact_cost ORDER BY category")
    return df["category"].tolist()


def get_blocks(phase: str | None = None) -> pd.DataFrame:
    """Return block details, optionally filtered by phase."""
    if phase:
        return _query(
            """
            SELECT b.block_id, b.name, b.hectares, b.variety,
                   b.plant_count, b.year_planted, p.name as phase
            FROM dim_block b
            JOIN dim_phase p ON b.phase_id = p.phase_id
            WHERE p.name = :phase
            ORDER BY b.block_number
        """,
            {"phase": phase},
        )
    return _query(
        """
        SELECT b.block_id, b.name, b.hectares, b.variety,
               b.plant_count, b.year_planted, p.name as phase
        FROM dim_block b
        JOIN dim_phase p ON b.phase_id = p.phase_id
        ORDER BY p.name, b.block_number
    """
    )


# ── Eagle View queries ────────────────────────────────────────────────


def total_cost(date_from, date_to, phase: str | None = None) -> float:
    """Total cost for a period, optionally filtered by phase."""
    sql = """
        SELECT COALESCE(SUM(fc.cost_rands), 0) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    df = _query(sql, params)
    return float(df["total"][0])


def cost_by_category(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Cost breakdown by category for a period."""
    sql = """
        SELECT fc.category,
               SUM(fc.cost_rands) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY fc.category ORDER BY total DESC"
    return _query(sql, params)


def cost_by_phase(date_from, date_to) -> pd.DataFrame:
    """Cost breakdown by phase for a period."""
    return _query(
        """
        SELECT p.name as phase,
               SUM(fc.cost_rands) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date BETWEEN :d1 AND :d2
        GROUP BY p.name
        ORDER BY total DESC
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )


def daily_cost_trend(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Daily cost trend, split by category."""
    sql = """
        SELECT fc.date, fc.category,
               SUM(fc.cost_rands) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY fc.date, fc.category ORDER BY fc.date"
    df = _query(sql, params)
    df["date"] = pd.to_datetime(df["date"])
    return df


def cost_by_phase_category(date_from, date_to) -> pd.DataFrame:
    """Phase x category matrix for the eagle view."""
    return _query(
        """
        SELECT p.name as phase, fc.category,
               SUM(fc.cost_rands) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date BETWEEN :d1 AND :d2
        GROUP BY p.name, fc.category
        ORDER BY p.name, total DESC
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )


# ── Daily Register queries ────────────────────────────────────────────


def daily_register(target_date, phase: str | None = None) -> pd.DataFrame:
    """Every cost line for a single day — the view dad wants."""
    sql = """
        SELECT fc.category, fc.subcategory, fc.description,
               fc.quantity, fc.unit, fc.cost_rands,
               fc.source_module,
               COALESCE(b.name, '-') as block,
               p.name as phase
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        LEFT JOIN dim_block b ON fc.block_id = b.block_id
        WHERE fc.date = :d
    """
    params = {"d": str(target_date)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " ORDER BY fc.category, fc.cost_rands DESC"
    return _query(sql, params)


def daily_register_summary(target_date, phase: str | None = None) -> pd.DataFrame:
    """Daily register grouped by category + subcategory."""
    sql = """
        SELECT fc.category, fc.subcategory,
               COUNT(*) as lines,
               SUM(fc.quantity) as total_qty,
               fc.unit,
               SUM(fc.cost_rands) as total_cost
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        WHERE fc.date = :d
    """
    params = {"d": str(target_date)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY fc.category, fc.subcategory, fc.unit"
    sql += " ORDER BY fc.category, total_cost DESC"
    return _query(sql, params)


# ── Block Drill-Down queries ─────────────────────────────────────────


def cost_by_block(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Cost per block with hectares for cost/ha calculation."""
    sql = """
        SELECT b.name as block, b.hectares, b.variety,
               fc.category,
               SUM(fc.cost_rands) as total
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        JOIN dim_block b ON fc.block_id = b.block_id
        WHERE fc.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY b.name, b.hectares, b.variety, fc.category"
    sql += " ORDER BY b.name, total DESC"
    return _query(sql, params)


def cost_per_hectare(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Total cost per hectare by block."""
    sql = """
        SELECT b.name as block, b.hectares, b.variety,
               p.name as phase,
               SUM(fc.cost_rands) as total_cost,
               SUM(fc.cost_rands) / b.hectares as cost_per_ha
        FROM fact_cost fc
        JOIN dim_phase p ON fc.phase_id = p.phase_id
        JOIN dim_block b ON fc.block_id = b.block_id
        WHERE fc.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY b.name, b.hectares, b.variety, p.name"
    sql += " ORDER BY cost_per_ha DESC"
    return _query(sql, params)


# ── Category Deep-Dive queries ───────────────────────────────────────


def category_trend(date_from, date_to, category: str) -> pd.DataFrame:
    """Daily trend for a specific category."""
    df = _query(
        """
        SELECT fc.date, SUM(fc.cost_rands) as total
        FROM fact_cost fc
        WHERE fc.date BETWEEN :d1 AND :d2
          AND fc.category = :cat
        GROUP BY fc.date
        ORDER BY fc.date
    """,
        {"d1": str(date_from), "d2": str(date_to), "cat": category},
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def category_top_drivers(date_from, date_to, category: str) -> pd.DataFrame:
    """Top subcategories driving cost for a category."""
    return _query(
        """
        SELECT fc.subcategory,
               SUM(fc.cost_rands) as total,
               SUM(fc.quantity) as total_qty,
               fc.unit
        FROM fact_cost fc
        WHERE fc.date BETWEEN :d1 AND :d2
          AND fc.category = :cat
        GROUP BY fc.subcategory, fc.unit
        ORDER BY total DESC
        LIMIT 20
    """,
        {"d1": str(date_from), "d2": str(date_to), "cat": category},
    )


def stock_purchase_vs_usage(date_from, date_to) -> pd.DataFrame:
    """Compare GRV (purchases) vs Usage for stock items."""
    return _query(
        """
        SELECT p.name as product,
               SUM(CASE WHEN s.movement_type = 'GRV'
                   THEN s.quantity ELSE 0 END) as purchased,
               SUM(CASE WHEN s.movement_type = 'Usage'
                   THEN s.quantity ELSE 0 END) as used,
               SUM(CASE WHEN s.movement_type = 'GRV'
                   THEN s.cost_rands ELSE 0 END) as purchase_value,
               SUM(CASE WHEN s.movement_type = 'Usage'
                   THEN s.cost_rands ELSE 0 END) as usage_value
        FROM fact_stock_detail s
        JOIN dim_product p ON s.product_id = p.product_id
        WHERE s.date BETWEEN :d1 AND :d2
        GROUP BY p.name
        ORDER BY purchase_value DESC
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )


# ── Fuel Detail queries ──────────────────────────────────────────────


def fuel_by_vehicle(date_from, date_to) -> pd.DataFrame:
    """Fuel consumption by vehicle."""
    return _query(
        """
        SELECT e.name as vehicle, e.vehicle_type,
               COUNT(*) as transactions,
               SUM(f.litres) as total_litres,
               SUM(f.cost_rands) as total_cost,
               SUM(f.hours) as total_hours,
               CASE WHEN SUM(f.hours) > 0
                    THEN SUM(f.litres) / SUM(f.hours)
                    ELSE 0 END as litres_per_hour
        FROM fact_fuel_detail f
        JOIN dim_equipment e ON f.equipment_id = e.equipment_id
        WHERE f.date BETWEEN :d1 AND :d2
        GROUP BY e.name, e.vehicle_type
        ORDER BY total_litres DESC
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )


def fuel_daily_by_vehicle(date_from, date_to) -> pd.DataFrame:
    """Daily fuel consumption per vehicle (for anomaly detection)."""
    df = _query(
        """
        SELECT f.date, e.name as vehicle,
               SUM(f.litres) as litres,
               SUM(f.cost_rands) as cost
        FROM fact_fuel_detail f
        JOIN dim_equipment e ON f.equipment_id = e.equipment_id
        WHERE f.date BETWEEN :d1 AND :d2
        GROUP BY f.date, e.name
        ORDER BY f.date, e.name
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def fuel_transactions(date_from, date_to, vehicle: str | None = None) -> pd.DataFrame:
    """Individual fuel transactions."""
    sql = """
        SELECT f.date, f.time, e.name as vehicle, e.vehicle_type,
               p.name as phase, f.task, f.litres, f.cost_rands,
               f.pump_reading_start, f.pump_reading_end,
               f.hours, f.odometer
        FROM fact_fuel_detail f
        JOIN dim_equipment e ON f.equipment_id = e.equipment_id
        JOIN dim_phase p ON f.phase_id = p.phase_id
        WHERE f.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if vehicle:
        sql += " AND e.name = :vehicle"
        params["vehicle"] = vehicle
    sql += " ORDER BY f.date, f.time"
    return _query(sql, params)


# ── Yield queries ────────────────────────────────────────────────────


def yield_by_block(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Harvest kg by block with hectares for kg/ha."""
    sql = """
        SELECT b.name as block, b.hectares, b.variety,
               p.name as phase,
               SUM(y.kg_harvested) as total_kg,
               SUM(y.kg_harvested) / b.hectares as kg_per_ha,
               SUM(y.lug_count) as total_lugs,
               SUM(y.pickers) as total_pickers
        FROM fact_yield y
        JOIN dim_block b ON y.block_id = b.block_id
        JOIN dim_phase p ON y.phase_id = p.phase_id
        WHERE y.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY b.name, b.hectares, b.variety, p.name"
    sql += " ORDER BY kg_per_ha DESC"
    return _query(sql, params)


def daily_yield(date_from, date_to) -> pd.DataFrame:
    """Daily harvest totals."""
    df = _query(
        """
        SELECT y.date, SUM(y.kg_harvested) as total_kg
        FROM fact_yield y
        WHERE y.date BETWEEN :d1 AND :d2
        GROUP BY y.date
        ORDER BY y.date
    """,
        {"d1": str(date_from), "d2": str(date_to)},
    )
    df["date"] = pd.to_datetime(df["date"])
    return df


def cost_per_kg(date_from, date_to, phase: str | None = None) -> pd.DataFrame:
    """Cost per kg harvested by block — the efficiency metric."""
    sql = """
        SELECT b.name as block, b.hectares, b.variety,
               p.name as phase,
               COALESCE(SUM(y.kg_harvested), 0) as total_kg,
               COALESCE(costs.total_cost, 0) as total_cost,
               CASE WHEN COALESCE(SUM(y.kg_harvested), 0) > 0
                    THEN COALESCE(costs.total_cost, 0)
                         / SUM(y.kg_harvested)
                    ELSE NULL END as cost_per_kg
        FROM fact_yield y
        JOIN dim_block b ON y.block_id = b.block_id
        JOIN dim_phase p ON y.phase_id = p.phase_id
        LEFT JOIN (
            SELECT block_id, SUM(cost_rands) as total_cost
            FROM fact_cost
            WHERE date BETWEEN :d1 AND :d2
            GROUP BY block_id
        ) costs ON costs.block_id = b.block_id
        WHERE y.date BETWEEN :d1 AND :d2
    """
    params = {"d1": str(date_from), "d2": str(date_to)}
    if phase:
        sql += " AND p.name = :phase"
        params["phase"] = phase
    sql += " GROUP BY b.name, b.hectares, b.variety, p.name, costs.total_cost"
    sql += " ORDER BY cost_per_kg"
    return _query(sql, params)


# ── Anomaly Detection queries ────────────────────────────────────────

def detect_fuel_anomalies(date_from, date_to) -> pd.DataFrame:
    """Flag vehicles with litres/hour >20% above fleet average."""
    df = fuel_by_vehicle(date_from, date_to)
    tractors = df[
        (df["vehicle_type"] == "tractor") &
        (df["litres_per_hour"] > 0)
    ].copy()
    if tractors.empty:
        return pd.DataFrame()
    avg = tractors["litres_per_hour"].mean()
    flagged = tractors[tractors["litres_per_hour"] > avg * 1.2].copy()
    flagged["avg_litres_per_hour"] = avg
    flagged["pct_above"] = (
        (flagged["litres_per_hour"] - avg) / avg * 100
    )
    return flagged


def detect_stock_gaps(date_from, date_to) -> pd.DataFrame:
    """Flag products where >50% of purchased value is unused."""
    df = stock_purchase_vs_usage(date_from, date_to)
    if df.empty:
        return pd.DataFrame()
    df = df[df["purchase_value"] > 0].copy()
    df["usage_pct"] = df["usage_value"] / df["purchase_value"] * 100
    df["gap_value"] = df["purchase_value"] - df["usage_value"]
    flagged = df[df["usage_pct"] < 50].copy()
    return flagged.sort_values("gap_value", ascending=False)


def detect_block_cost_outliers(date_from, date_to) -> pd.DataFrame:
    """Flag blocks with cost/ha >25% above average."""
    df = cost_per_hectare(date_from, date_to)
    if df.empty:
        return pd.DataFrame()
    avg = df["cost_per_ha"].mean()
    flagged = df[df["cost_per_ha"] > avg * 1.25].copy()
    flagged["avg_cost_per_ha"] = avg
    flagged["pct_above"] = (
        (flagged["cost_per_ha"] - avg) / avg * 100
    )
    return flagged


def detect_all_anomalies(date_from, date_to) -> dict:
    """Run all anomaly checks, return dict of results."""
    return {
        "fuel": detect_fuel_anomalies(date_from, date_to),
        "stock": detect_stock_gaps(date_from, date_to),
        "blocks": detect_block_cost_outliers(date_from, date_to),
    }
