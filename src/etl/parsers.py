"""
Parsers for each FarmTrace export type.

Each parser reads a CSV/Excel file and returns a cleaned DataFrame
ready for normalization and loading.
"""

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


def parse_block_setup(filepath: Path) -> pd.DataFrame:
    """Parse block setup export.

    Expected columns: Block Number, Block Name, Phase, Variety,
                      Hectares, Plant Count, Year Planted
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    required = ["Block Number", "Phase", "Hectares"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Block setup missing columns: {missing}")

    return df


def parse_fuel_transactions(filepath: Path) -> pd.DataFrame:
    """Parse fuel transaction export.

    Expected columns: Date, Time, Phase, Vehicle ID, Vehicle Name,
                      Vehicle Type, Task, Pump Reading Initial,
                      Pump Reading Final, Litres, Cost (ZAR), Hours,
                      Odometer, Service Interval
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Litres"] = pd.to_numeric(df["Litres"], errors="coerce").fillna(0)
    df["Cost (ZAR)"] = pd.to_numeric(
        df["Cost (ZAR)"], errors="coerce"
    ).fillna(0)
    df["Hours"] = pd.to_numeric(df["Hours"], errors="coerce").fillna(0)
    df["source_file"] = filepath.name

    return df


def parse_stock_movements(filepath: Path) -> pd.DataFrame:
    """Parse stock movement export.

    Expected columns: Date, Product Name, Product Category, Phase,
                      Block, Movement Type, Quantity, Unit,
                      Unit Cost (ZAR), Total Cost (ZAR),
                      Instruction Reference, Batch Number
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce").fillna(0)
    df["Total Cost (ZAR)"] = pd.to_numeric(
        df["Total Cost (ZAR)"], errors="coerce"
    ).fillna(0)
    df["Unit Cost (ZAR)"] = pd.to_numeric(
        df["Unit Cost (ZAR)"], errors="coerce"
    ).fillna(0)
    df["Block"] = df["Block"].fillna("").astype(str).str.strip()
    df["source_file"] = filepath.name

    return df


def parse_labour(filepath: Path) -> pd.DataFrame:
    """Parse labour export.

    Expected columns: Date, Phase, Section, Task, Headcount,
                      Hours per Person, Total Hours,
                      Rate per Hour (ZAR), Total Cost (ZAR)
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Total Cost (ZAR)"] = pd.to_numeric(
        df["Total Cost (ZAR)"], errors="coerce"
    ).fillna(0)
    df["Total Hours"] = pd.to_numeric(
        df["Total Hours"], errors="coerce"
    ).fillna(0)
    df["source_file"] = filepath.name

    return df


def parse_harvesting(filepath: Path) -> pd.DataFrame:
    """Parse harvesting export.

    Expected columns: Date, Phase, Block, Variety, Kg Harvested,
                      Lug Count, Pickers
    """
    df = read_file(filepath)
    df.columns = df.columns.str.strip()

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    df["Kg Harvested"] = pd.to_numeric(
        df["Kg Harvested"], errors="coerce"
    ).fillna(0)
    df["source_file"] = filepath.name

    return df
