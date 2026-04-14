"""
Parsers for real FarmTrace exports.

These handle the actual column names and quirks of FarmTrace exports,
which differ significantly from our synthetic data format.
"""

import re
import pandas as pd
from pathlib import Path


def read_file(filepath: Path) -> pd.DataFrame:
    """Read CSV or Excel file, auto-detecting format."""
    suffix = filepath.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(filepath)
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(filepath)
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def _extract_phase_from_facility(facility: str) -> str:
    """Extract phase name from Storage Facility Description.

    'Phase 1 Fertilizer Store' → 'Phase 1'
    'Phase 3 Chemical Store'   → 'Phase 3'
    'Fuel Tank 1 WS'           → 'General'
    'Workshop'                 → 'Workshop'
    'z Container Chem'         → 'General'
    """
    match = re.match(r"(Phase \d+)", str(facility))
    if match:
        return match.group(1)
    facility_lower = str(facility).lower()
    if "workshop" in facility_lower:
        return "Workshop"
    if "coldroom" in facility_lower:
        return "Coldroom"
    return "General"


def _facility_to_category(facility: str) -> str:
    """Map Storage Facility Description to cost category.

    'Phase 1 Fertilizer Store' → 'fertilizer'
    'Phase 2 Chemical Store'   → 'chemicals'
    'Fuel Tank 1 WS'           → 'diesel'
    'Workshop'                 → 'workshop'
    'Toilet Papers & Soaps'    → 'toiletries'
    """
    facility_lower = str(facility).lower()
    if "fertilizer" in facility_lower or "fertili" in facility_lower:
        return "fertilizer"
    if "chemical" in facility_lower or "chem" in facility_lower:
        return "chemicals"
    if "fuel" in facility_lower or "diesel" in facility_lower:
        return "diesel"
    if "workshop" in facility_lower:
        return "workshop"
    if "toilet" in facility_lower or "soap" in facility_lower:
        return "toiletries"
    return "other"


def _vehicle_type(name: str) -> str:
    """Derive vehicle type from vehicle description."""
    name_lower = str(name).lower()
    if any(t in name_lower for t in ("tafe", "landini", "tractor")):
        return "tractor"
    if any(t in name_lower for t in ("hilux", "prado", "ranger", "legend")):
        return "bakkie"
    if "excavator" in name_lower:
        return "excavator"
    if "water truck" in name_lower or "mercedes" in name_lower:
        return "truck"
    if "generator" in name_lower:
        return "generator"
    return "other"


def _vehicle_id(name: str) -> str:
    """Extract a short ID from vehicle description."""
    match = re.match(r"#?(\d+)", str(name).strip())
    if match:
        return f"VEH-{match.group(1)}"
    # For bakkies/other vehicles, use first word
    return str(name).strip().replace(" ", "-")[:20]


# ── Fuel Transactions ────────────────────────────────────────────────

def parse_fuel_transactions_real(filepath: Path,
                                 diesel_price: float = 24.50
                                 ) -> pd.DataFrame:
    """Parse real FarmTrace fuel transaction export.

    Column mapping:
        Timestamp           → Date, Time
        Phase Description   → Phase
        Task Category       → Task
        Vehicle Description → Vehicle Name
        Quantity            → Litres
        Initial Pump Reading → Pump Reading Initial
        End Pump Reading    → Pump Reading Final
        Vehicle Odometer Reading → Odometer
        Service Interval    → Service Interval

    diesel_price: ZAR per litre (used to calculate cost since
                  FarmTrace doesn't export it). Default based on
                  current SA diesel price.
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    # Parse timestamp into date and time
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Date"] = df["Timestamp"].dt.date
    df["Time"] = df["Timestamp"].dt.strftime("%H:%M")

    # Rename columns to our schema
    df = df.rename(columns={
        "Phase Description": "Phase",
        "Task Category": "Task",
        "Vehicle Description": "Vehicle Name",
        "Quantity": "Litres",
        "Initial Pump Reading": "Pump Reading Initial",
        "End Pump Reading": "Pump Reading Final",
        "Vehicle Odometer Reading": "Odometer",
    })

    # Derive fields
    df["Vehicle ID"] = df["Vehicle Name"].apply(_vehicle_id)
    df["Vehicle Type"] = df["Vehicle Name"].apply(_vehicle_type)
    df["Cost (ZAR)"] = df["Litres"].abs() * diesel_price
    df["Hours"] = 0  # Not available in real data
    df["source_file"] = filepath.name

    # Clean up
    df["Litres"] = df["Litres"].abs()

    return df


# ── Stock Movements ──────────────────────────────────────────────────

def parse_stock_movements_real(filepath: Path) -> pd.DataFrame:
    """Parse real FarmTrace stock movement export.

    Column mapping:
        Timestamp                   → Date
        Description                 → Movement Type
        Product Item Description    → Product Name
        Storage Facility Description → Phase (derived), Product Category (derived)
        Quantity                    → Quantity (abs value)
        GRV Unit Price              → Unit Cost (ZAR) for GRV
        Block Task Block Name       → Block
        Stock Item Batch            → Batch Number

    Cost calculation:
        Movement Value is 0 for all rows in FarmTrace exports.
        For GRV: cost = Quantity * GRV Unit Price
        For Usage: cost = |Quantity| * weighted avg GRV price per product
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df["Date"] = df["Timestamp"].dt.date

    # Build weighted average cost per product from GRV records
    grv = df[df["Description"] == "GRV"].copy()
    grv["grv_value"] = grv["Quantity"] * grv["GRV Unit Price"]
    avg_prices = (
        grv.groupby("Product Item Description")
        .apply(lambda g: g["grv_value"].sum() / g["Quantity"].sum()
               if g["Quantity"].sum() > 0 else 0,
               include_groups=False)
        .to_dict()
    )

    # Rename columns
    df = df.rename(columns={
        "Description": "Movement Type",
        "Product Item Description": "Product Name",
        "Stock Item Batch": "Batch Number",
        "Block Task Block Name": "Block",
    })

    # Derive phase and category from storage facility
    df["Phase"] = df["Storage Facility Description"].apply(
        _extract_phase_from_facility
    )
    df["Product Category"] = df["Storage Facility Description"].apply(
        _facility_to_category
    )

    # Exclude diesel from stock — it's already tracked in fuel transactions
    # (FarmTrace logs fuel tank drawdowns in stock AND as fuel transactions)
    df = df[df["Product Name"] != "Diesel"].copy()

    # Normalize movement type
    df["Movement Type"] = df["Movement Type"].replace({
        "Quantity Adjustment": "Adjustment",
    })

    # Calculate costs
    def calc_cost(row):
        if row["Movement Type"] == "GRV":
            price = row.get("GRV Unit Price", 0) or 0
            return abs(row["Quantity"]) * price
        else:
            # Use weighted average GRV price
            price = avg_prices.get(row["Product Name"], 0)
            return abs(row["Quantity"]) * price

    df["Unit Cost (ZAR)"] = df.apply(
        lambda r: r.get("GRV Unit Price", 0) or
                  avg_prices.get(r["Product Name"], 0),
        axis=1,
    )
    df["Total Cost (ZAR)"] = df.apply(calc_cost, axis=1)
    df["Quantity"] = df["Quantity"].abs()

    # Clean block
    df["Block"] = df["Block"].fillna("").astype(str).str.strip()

    # Unit (derive from product name/category)
    df["Unit"] = ""

    df["source_file"] = filepath.name

    return df


# ── Labour / Staff Job Costings ──────────────────────────────────────

def parse_labour_real(filepath: Path, report_date=None) -> pd.DataFrame:
    """Parse real FarmTrace staff job costings export.

    This is a PERIOD SUMMARY — no individual dates. We use
    report_date as the date for all entries.

    Column mapping:
        Section Description → Phase (and Section)
        Task Category       → Task
        Hours               → Total Hours (comma decimal separator!)
        Cost                → Total Cost (ZAR)
        Units               → Headcount

    report_date: date to assign to all rows (default: today).
                 FarmTrace labour export is a period summary, not daily.
    """
    from datetime import date as date_cls
    if report_date is None:
        report_date = date_cls.today()

    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    # Fix comma decimal separator in Hours
    df["Hours"] = (
        df["Hours"]
        .astype(str)
        .str.replace(",", ".", regex=False)
    )
    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0)

    # Map section to phase
    phase_map = {
        "Phase 1": "Phase 1",
        "Phase 2": "Phase 2",
        "Phase 3": "Phase 3",
        "Phase 4": "Phase 4",
        "General All Phases": "General",
        "Coldroom": "Coldroom",
        "Safety Officers": "General",
        "Workshop": "Workshop",
    }

    df = df.rename(columns={
        "Section Description": "Section",
        "Task Category": "Task",
        "Hours": "Total Hours",
        "Cost": "Total Cost (ZAR)",
        "Units": "Headcount",
    })

    df["Phase"] = df["Section"].map(phase_map).fillna("General")
    df["Date"] = report_date
    df["Total Cost (ZAR)"] = pd.to_numeric(
        df["Total Cost (ZAR)"], errors="coerce"
    ).fillna(0)
    df["source_file"] = filepath.name

    return df
