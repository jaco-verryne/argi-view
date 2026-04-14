"""
Generate realistic synthetic FarmTrace exports for a SA blueberry farm.

Creates CSV files that mimic actual FarmTrace export formats:
- block_setup.csv       (static reference data)
- fuel_transactions.csv (daily fuel records)
- stock_movements.csv   (product usage, purchases, adjustments)
- labour.csv            (tasks, hours, costs per phase)
- harvesting.csv        (kg picked per block)

Data covers April 2026 (one month) for a farm with:
- 4 phases, 28 blocks
- ~12 vehicles
- ~60 products across categories
- Realistic SA pricing (ZAR)

Usage: python src/generate_synthetic.py
Output: data/raw/synthetic/
"""

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

# Reproducible randomness
random.seed(42)

OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw" / "synthetic"

# ── Farm Structure ─────────────────────────────────────────────────────

PHASES = [
    {"name": "Phase 1", "established": 2018},
    {"name": "Phase 2", "established": 2019},
    {"name": "Phase 3", "established": 2021},
    {"name": "Phase 4", "established": 2023},
]

# Blocks distributed across phases, realistic SA blueberry varieties
VARIETIES = ["Star", "Emerald", "Jewel", "Legacy", "Ventura", "Eureka Blue"]

BLOCKS = []
block_num = 1
blocks_per_phase = [8, 7, 7, 6]
for i, phase in enumerate(PHASES):
    for j in range(blocks_per_phase[i]):
        BLOCKS.append(
            {
                "block_number": block_num,
                "block_name": f"Block {block_num}",
                "phase": phase["name"],
                "variety": random.choice(VARIETIES),
                "hectares": round(random.uniform(2.5, 7.0), 1),
                "plant_count": 0,  # calculated below
                "year_planted": phase["established"],
            }
        )
        # ~3,000-4,500 plants per hectare for blueberries
        BLOCKS[-1]["plant_count"] = int(BLOCKS[-1]["hectares"] * random.randint(3000, 4500))
        block_num += 1

# ── Equipment Fleet ────────────────────────────────────────────────────

VEHICLES = [
    {
        "id": "TK-01",
        "name": "Tractor 1",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 8.5,
    },
    {
        "id": "TK-02",
        "name": "Tractor 2",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 9.0,
    },
    {
        "id": "TK-03",
        "name": "Tractor 3",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 7.8,
    },
    {
        "id": "TK-04",
        "name": "Tractor 4",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 8.2,
    },
    {
        "id": "TK-05",
        "name": "Tractor 5",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 10.5,
    },  # older, less efficient
    {
        "id": "TK-06",
        "name": "Tractor 6",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 8.0,
    },
    {
        "id": "TK-07",
        "name": "Tractor 7",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 7.5,
    },
    {
        "id": "TK-08",
        "name": "Tractor 8",
        "type": "tractor",
        "fuel": "diesel",
        "avg_litres_per_hour": 9.2,
    },
    {
        "id": "BK-01",
        "name": "Bakkie 1",
        "type": "bakkie",
        "fuel": "diesel",
        "avg_litres_per_hour": 4.5,
    },
    {
        "id": "BK-02",
        "name": "Bakkie 2",
        "type": "bakkie",
        "fuel": "diesel",
        "avg_litres_per_hour": 5.0,
    },
    {
        "id": "GN-01",
        "name": "Generator 1",
        "type": "generator",
        "fuel": "diesel",
        "avg_litres_per_hour": 12.0,
    },
    {
        "id": "GN-02",
        "name": "Generator 2",
        "type": "generator",
        "fuel": "diesel",
        "avg_litres_per_hour": 6.0,
    },
]

# ── Tractor Tasks ──────────────────────────────────────────────────────

TRACTOR_TASKS = [
    "Folio Spray",
    "Mowing",
    "Compost Spreading",
    "Transport - Internal",
    "Herbicide Application",
    "Fertigation",
    "Pruning Cleanup",
    "Netting",
    "General Maintenance",
]

# ── Products (chemicals, stock items) ──────────────────────────────────

PRODUCTS = [
    # GMI / Chemicals
    {
        "name": "Mancozeb 800 WP",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 185.00,
        "package_size": 25,
    },
    {
        "name": "Copper Oxychloride",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 142.50,
        "package_size": 5,
    },
    {
        "name": "Malathion 500 EC",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 210.00,
        "package_size": 5,
    },
    {
        "name": "Cypermethrin 200 EC",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 275.00,
        "package_size": 5,
    },
    {
        "name": "Chlorpyrifos 480 EC",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 195.00,
        "package_size": 5,
    },
    {
        "name": "Glyphosate 360 SL",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 125.00,
        "package_size": 20,
    },
    {
        "name": "Paraquat 200 SL",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 98.00,
        "package_size": 20,
    },
    {
        "name": "Sulphur 800 WP",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 65.00,
        "package_size": 25,
    },
    {
        "name": "Potassium Nitrate",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 32.50,
        "package_size": 25,
    },
    {
        "name": "Calcium Nitrate",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 28.00,
        "package_size": 25,
    },
    {
        "name": "MAP (Mono Ammonium Phosphate)",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 38.00,
        "package_size": 25,
    },
    {"name": "Urea", "category": "GMI", "unit": "kg", "unit_cost": 22.00, "package_size": 50},
    {
        "name": "Iron Chelate EDDHA",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 420.00,
        "package_size": 5,
    },
    {
        "name": "Magnesium Sulphate",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 18.50,
        "package_size": 25,
    },
    {
        "name": "Boron 150 SL",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 155.00,
        "package_size": 5,
    },
    {
        "name": "Wetting Agent",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 85.00,
        "package_size": 20,
    },
    {
        "name": "Fulvic Acid",
        "category": "GMI",
        "unit": "litres",
        "unit_cost": 165.00,
        "package_size": 20,
    },
    {
        "name": "Humic Acid Granules",
        "category": "GMI",
        "unit": "kg",
        "unit_cost": 55.00,
        "package_size": 25,
    },
    # Workshop / Hardware
    {
        "name": "Hydraulic Oil 20L",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 1250.00,
        "package_size": 1,
    },
    {
        "name": "Engine Oil 15W40 20L",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 980.00,
        "package_size": 1,
    },
    {
        "name": "Grease Cartridge",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 65.00,
        "package_size": 1,
    },
    {
        "name": "Cable Ties (pack)",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 45.00,
        "package_size": 1,
    },
    {
        "name": "Bolts & Nuts Assorted",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 120.00,
        "package_size": 1,
    },
    {
        "name": "Irrigation Drippers (100)",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 350.00,
        "package_size": 1,
    },
    {
        "name": "Poly Pipe 25mm (100m)",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 875.00,
        "package_size": 1,
    },
    {
        "name": "Netting Clips (bag)",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 280.00,
        "package_size": 1,
    },
    {
        "name": "Brush Cutter Line",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 195.00,
        "package_size": 1,
    },
    {
        "name": "Mower Blades (set)",
        "category": "Workshop",
        "unit": "units",
        "unit_cost": 560.00,
        "package_size": 1,
    },
    # Toiletries / Consumables
    {
        "name": "Toilet Paper (48 pack)",
        "category": "Toiletries",
        "unit": "units",
        "unit_cost": 185.00,
        "package_size": 1,
    },
    {
        "name": "Hand Soap 5L",
        "category": "Toiletries",
        "unit": "units",
        "unit_cost": 95.00,
        "package_size": 1,
    },
    {
        "name": "Paper Towels (6 pack)",
        "category": "Toiletries",
        "unit": "units",
        "unit_cost": 145.00,
        "package_size": 1,
    },
    {
        "name": "Refuse Bags (20)",
        "category": "Toiletries",
        "unit": "units",
        "unit_cost": 55.00,
        "package_size": 1,
    },
    {
        "name": "Sanitizer 5L",
        "category": "Toiletries",
        "unit": "units",
        "unit_cost": 125.00,
        "package_size": 1,
    },
    # Diesel (tracked as stock movement AND fuel transaction)
    {
        "name": "Diesel 50ppm",
        "category": "Diesel",
        "unit": "litres",
        "unit_cost": 24.50,
        "package_size": 1,
    },
]

# ── Labour Task Types ──────────────────────────────────────────────────

LABOUR_TASKS = [
    {"task": "Pruning", "rate_per_hour": 38.50, "typical_headcount": (15, 40)},
    {"task": "Netting Installation", "rate_per_hour": 35.00, "typical_headcount": (8, 20)},
    {"task": "Netting Removal", "rate_per_hour": 35.00, "typical_headcount": (8, 20)},
    {"task": "Mowing (Manual)", "rate_per_hour": 32.00, "typical_headcount": (4, 10)},
    {"task": "Compost Application", "rate_per_hour": 35.00, "typical_headcount": (6, 15)},
    {"task": "Irrigation Maintenance", "rate_per_hour": 40.00, "typical_headcount": (3, 8)},
    {"task": "Scouting", "rate_per_hour": 42.00, "typical_headcount": (2, 6)},
    {"task": "General Maintenance", "rate_per_hour": 35.00, "typical_headcount": (5, 12)},
    {"task": "Spraying (Manual)", "rate_per_hour": 38.00, "typical_headcount": (4, 10)},
    {"task": "Planting", "rate_per_hour": 32.00, "typical_headcount": (10, 30)},
    {"task": "Supervision", "rate_per_hour": 55.00, "typical_headcount": (1, 3)},
    {"task": "Pack Shed", "rate_per_hour": 35.00, "typical_headcount": (10, 25)},
]

# ── Date Range ─────────────────────────────────────────────────────────

START_DATE = date(2026, 4, 1)
END_DATE = date(2026, 4, 30)

DIESEL_PRICE = 24.50  # ZAR per litre, April 2026


def daterange(start: date, end: date):
    """Yield each date in the range [start, end]."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def is_workday(d: date) -> bool:
    """Monday-Saturday are workdays on a farm. Sunday is off."""
    return d.weekday() < 6  # 0=Mon, 5=Sat, 6=Sun


# ── Generator: Block Setup ─────────────────────────────────────────────


def generate_block_setup():
    """Generate block_setup.csv — static reference data."""
    rows = []
    for b in BLOCKS:
        rows.append(
            {
                "Block Number": b["block_number"],
                "Block Name": b["block_name"],
                "Phase": b["phase"],
                "Variety": b["variety"],
                "Hectares": b["hectares"],
                "Plant Count": b["plant_count"],
                "Year Planted": b["year_planted"],
            }
        )
    return rows


# ── Generator: Fuel Transactions ───────────────────────────────────────


def generate_fuel_transactions():
    """Generate fuel_transactions.csv — daily fuel records.

    Realistic patterns:
    - Tractors refuel 1-2 times per day when working
    - Not all tractors work every day
    - Bakkies refuel every 2-3 days
    - Generators run daily during load shedding periods
    - Pump readings are sequential and consistent
    - Hours and odometer increment realistically
    """
    rows = []
    # Track cumulative state per vehicle
    vehicle_state = {}
    for v in VEHICLES:
        vehicle_state[v["id"]] = {
            "pump_reading": random.randint(50000, 200000),
            "odometer": random.randint(5000, 80000) if v["type"] != "generator" else 0,
            "hours": random.randint(1000, 8000),
        }

    for day in daterange(START_DATE, END_DATE):
        if not is_workday(day):
            # Generators might still run on Sundays (load shedding)
            if random.random() < 0.3:
                gen = random.choice([v for v in VEHICLES if v["type"] == "generator"])
                state = vehicle_state[gen["id"]]
                hours_run = round(random.uniform(2, 6), 1)
                litres = round(
                    hours_run * gen["avg_litres_per_hour"] * random.uniform(0.85, 1.15), 1
                )
                state["pump_reading"] += litres
                state["hours"] += hours_run
                time_str = f"{random.randint(6, 8):02d}:{random.randint(0, 59):02d}"
                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Time": time_str,
                        "Phase": random.choice(["Phase 1", "Phase 2", "Phase 3", "Phase 4"]),
                        "Vehicle ID": gen["id"],
                        "Vehicle Name": gen["name"],
                        "Vehicle Type": gen["type"],
                        "Task": "Load Shedding",
                        "Pump Reading Initial": round(state["pump_reading"] - litres, 1),
                        "Pump Reading Final": round(state["pump_reading"], 1),
                        "Litres": litres,
                        "Cost (ZAR)": round(litres * DIESEL_PRICE, 2),
                        "Hours": hours_run,
                        "Odometer": state["odometer"],
                        "Service Interval": "",
                    }
                )
            continue

        # Decide which tractors work today (typically 4-7 of 8)
        working_tractors = random.sample(
            [v for v in VEHICLES if v["type"] == "tractor"],
            k=random.randint(4, min(7, len([v for v in VEHICLES if v["type"] == "tractor"]))),
        )

        for tractor in working_tractors:
            state = vehicle_state[tractor["id"]]
            phase = random.choice(PHASES)
            task = random.choice(TRACTOR_TASKS)
            hours_worked = round(random.uniform(4, 9), 1)
            litres = round(
                hours_worked * tractor["avg_litres_per_hour"] * random.uniform(0.8, 1.2), 1
            )

            # Tractor 5 is the old one — occasionally uses way too much
            if tractor["id"] == "TK-05" and random.random() < 0.15:
                litres = round(litres * random.uniform(1.4, 1.8), 1)

            state["pump_reading"] += litres
            state["hours"] += hours_worked
            state["odometer"] += random.randint(5, 30)

            time_str = f"{random.randint(5, 7):02d}:" f"{random.randint(0, 59):02d}"

            # Service interval flag
            service = ""
            if state["hours"] % 500 < 10:
                service = "500hr service due"
            elif state["hours"] % 250 < 10:
                service = "250hr service due"

            rows.append(
                {
                    "Date": day.isoformat(),
                    "Time": time_str,
                    "Phase": phase["name"],
                    "Vehicle ID": tractor["id"],
                    "Vehicle Name": tractor["name"],
                    "Vehicle Type": tractor["type"],
                    "Task": task,
                    "Pump Reading Initial": round(state["pump_reading"] - litres, 1),
                    "Pump Reading Final": round(state["pump_reading"], 1),
                    "Litres": litres,
                    "Cost (ZAR)": round(litres * DIESEL_PRICE, 2),
                    "Hours": hours_worked,
                    "Odometer": state["odometer"],
                    "Service Interval": service,
                }
            )

        # Bakkies refuel every 2-3 days
        for bakkie in [v for v in VEHICLES if v["type"] == "bakkie"]:
            if random.random() < 0.4:
                state = vehicle_state[bakkie["id"]]
                litres = round(random.uniform(25, 55), 1)
                state["pump_reading"] += litres
                state["odometer"] += random.randint(40, 120)
                time_str = f"{random.randint(6, 16):02d}:" f"{random.randint(0, 59):02d}"
                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Time": time_str,
                        "Phase": "General",
                        "Vehicle ID": bakkie["id"],
                        "Vehicle Name": bakkie["name"],
                        "Vehicle Type": bakkie["type"],
                        "Task": "Transport - General",
                        "Pump Reading Initial": round(state["pump_reading"] - litres, 1),
                        "Pump Reading Final": round(state["pump_reading"], 1),
                        "Litres": litres,
                        "Cost (ZAR)": round(litres * DIESEL_PRICE, 2),
                        "Hours": 0,
                        "Odometer": state["odometer"],
                        "Service Interval": "",
                    }
                )

        # Generators (load shedding days — roughly 40% of workdays)
        if random.random() < 0.4:
            for gen in [v for v in VEHICLES if v["type"] == "generator"]:
                if random.random() < 0.7:
                    state = vehicle_state[gen["id"]]
                    hours_run = round(random.uniform(2, 8), 1)
                    litres = round(
                        hours_run * gen["avg_litres_per_hour"] * random.uniform(0.9, 1.1), 1
                    )
                    state["pump_reading"] += litres
                    state["hours"] += hours_run
                    time_str = f"{random.randint(6, 9):02d}:" f"{random.randint(0, 59):02d}"
                    rows.append(
                        {
                            "Date": day.isoformat(),
                            "Time": time_str,
                            "Phase": random.choice(["Phase 1", "Phase 2", "Pack Shed"]),
                            "Vehicle ID": gen["id"],
                            "Vehicle Name": gen["name"],
                            "Vehicle Type": gen["type"],
                            "Task": "Load Shedding",
                            "Pump Reading Initial": round(state["pump_reading"] - litres, 1),
                            "Pump Reading Final": round(state["pump_reading"], 1),
                            "Litres": litres,
                            "Cost (ZAR)": round(litres * DIESEL_PRICE, 2),
                            "Hours": hours_run,
                            "Odometer": 0,
                            "Service Interval": "",
                        }
                    )

    return rows


# ── Generator: Stock Movements ─────────────────────────────────────────


def generate_stock_movements():
    """Generate stock_movements.csv — product purchases, usage, adjustments.

    Realistic patterns:
    - Chemical applications happen on specific blocks on specific days
    - Fertiliser usage is regular across phases
    - GRVs (purchases) happen a few times per month
    - Adjustments are rare (stock counts)
    - Toiletries and workshop items are used at phase level, not block level
    - ~1,300 rows per day as dad described (when fully granular)
    """
    rows = []

    # GRVs — bulk purchases a few times per month
    grv_dates = random.sample(
        [d for d in daterange(START_DATE, END_DATE) if is_workday(d)],
        k=6,
    )
    grv_dates.sort()

    for grv_date in grv_dates:
        # Each GRV has 8-15 products
        products_in_delivery = random.sample(PRODUCTS, k=random.randint(8, 15))
        for product in products_in_delivery:
            qty = random.randint(2, 20) * product["package_size"]
            rows.append(
                {
                    "Date": grv_date.isoformat(),
                    "Product Name": product["name"],
                    "Product Category": product["category"],
                    "Phase": "Central Store",
                    "Block": "",
                    "Movement Type": "GRV",
                    "Quantity": qty,
                    "Unit": product["unit"],
                    "Unit Cost (ZAR)": product["unit_cost"],
                    "Total Cost (ZAR)": round(qty * product["unit_cost"], 2),
                    "Instruction Reference": f"GRV-{grv_date.strftime('%Y%m%d')}"
                    f"-{random.randint(100, 999)}",
                    "Batch Number": f"B{random.randint(10000, 99999)}",
                }
            )

    # Daily usage
    gmi_products = [p for p in PRODUCTS if p["category"] == "GMI"]
    workshop_products = [p for p in PRODUCTS if p["category"] == "Workshop"]
    toiletry_products = [p for p in PRODUCTS if p["category"] == "Toiletries"]

    for day in daterange(START_DATE, END_DATE):
        if not is_workday(day):
            continue

        # Chemical applications — 2-4 products applied across various blocks
        num_applications = random.randint(2, 4)
        applied_products = random.sample(gmi_products, k=min(num_applications, len(gmi_products)))

        for product in applied_products:
            # Each application covers 3-8 blocks in a phase
            phase = random.choice(PHASES)
            phase_blocks = [b for b in BLOCKS if b["phase"] == phase["name"]]
            target_blocks = random.sample(
                phase_blocks,
                k=min(random.randint(3, 8), len(phase_blocks)),
            )

            instruction_ref = (
                f"INSTR-{day.strftime('%Y%m%d')}-"
                f"{product['name'][:3].upper()}-"
                f"{random.randint(100, 999)}"
            )

            for block in target_blocks:
                # Quantity proportional to block hectares
                qty_per_ha = round(random.uniform(0.5, 3.0), 2)
                qty = round(qty_per_ha * block["hectares"], 2)
                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Product Name": product["name"],
                        "Product Category": product["category"],
                        "Phase": block["phase"],
                        "Block": block["block_name"],
                        "Movement Type": "Usage",
                        "Quantity": qty,
                        "Unit": product["unit"],
                        "Unit Cost (ZAR)": product["unit_cost"],
                        "Total Cost (ZAR)": round(qty * product["unit_cost"], 2),
                        "Instruction Reference": instruction_ref,
                        "Batch Number": "",
                    }
                )

        # Fertigation — daily for most blocks during growing season
        fert_products = [
            p
            for p in gmi_products
            if p["name"]
            in (
                "Potassium Nitrate",
                "Calcium Nitrate",
                "MAP (Mono Ammonium Phosphate)",
                "Urea",
                "Magnesium Sulphate",
            )
        ]
        # Fertigation covers all phases, 1-2 products per day
        fert_today = random.sample(fert_products, k=min(random.randint(1, 2), len(fert_products)))
        for product in fert_today:
            for block in BLOCKS:
                qty = round(block["hectares"] * random.uniform(0.3, 1.5), 2)
                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Product Name": product["name"],
                        "Product Category": product["category"],
                        "Phase": block["phase"],
                        "Block": block["block_name"],
                        "Movement Type": "Usage",
                        "Quantity": qty,
                        "Unit": product["unit"],
                        "Unit Cost (ZAR)": product["unit_cost"],
                        "Total Cost (ZAR)": round(qty * product["unit_cost"], 2),
                        "Instruction Reference": (
                            f"FERT-{day.strftime('%Y%m%d')}-" f"{product['name'][:3].upper()}"
                        ),
                        "Batch Number": "",
                    }
                )

        # Workshop items — occasional usage at phase level
        if random.random() < 0.3:
            product = random.choice(workshop_products)
            qty = random.randint(1, 3)
            rows.append(
                {
                    "Date": day.isoformat(),
                    "Product Name": product["name"],
                    "Product Category": product["category"],
                    "Phase": random.choice(PHASES)["name"],
                    "Block": "",
                    "Movement Type": "Usage",
                    "Quantity": qty,
                    "Unit": product["unit"],
                    "Unit Cost (ZAR)": product["unit_cost"],
                    "Total Cost (ZAR)": round(qty * product["unit_cost"], 2),
                    "Instruction Reference": "",
                    "Batch Number": "",
                }
            )

        # Toiletries — used weekly per phase
        if day.weekday() == 0:  # Mondays
            for phase in PHASES:
                product = random.choice(toiletry_products)
                qty = random.randint(1, 3)
                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Product Name": product["name"],
                        "Product Category": product["category"],
                        "Phase": phase["name"],
                        "Block": "",
                        "Movement Type": "Usage",
                        "Quantity": qty,
                        "Unit": product["unit"],
                        "Unit Cost (ZAR)": product["unit_cost"],
                        "Total Cost (ZAR)": round(qty * product["unit_cost"], 2),
                        "Instruction Reference": "",
                        "Batch Number": "",
                    }
                )

    # Stock adjustments — 2-3 per month (stock count discrepancies)
    adj_dates = random.sample(
        [d for d in daterange(START_DATE, END_DATE) if is_workday(d)],
        k=3,
    )
    for adj_date in adj_dates:
        product = random.choice(PRODUCTS)
        adj_qty = round(random.uniform(-5, -0.5), 2)
        rows.append(
            {
                "Date": adj_date.isoformat(),
                "Product Name": product["name"],
                "Product Category": product["category"],
                "Phase": "Central Store",
                "Block": "",
                "Movement Type": "Adjustment",
                "Quantity": adj_qty,
                "Unit": product["unit"],
                "Unit Cost (ZAR)": product["unit_cost"],
                "Total Cost (ZAR)": round(adj_qty * product["unit_cost"], 2),
                "Instruction Reference": (
                    f"ADJ-{adj_date.strftime('%Y%m%d')}-" f"{random.randint(100, 999)}"
                ),
                "Batch Number": "",
            }
        )

    return rows


# ── Generator: Labour ──────────────────────────────────────────────────


def generate_labour():
    """Generate labour.csv — daily labour allocation per phase.

    Realistic patterns:
    - Each phase has a mix of tasks per day
    - Headcount varies by task and phase size
    - April is post-harvest in SA — focus on pruning, maintenance, netting
    - Working hours: 7-9 hours per person per day
    - Labour rate: varies by task complexity
    """
    rows = []

    for day in daterange(START_DATE, END_DATE):
        if not is_workday(day):
            continue

        for phase in PHASES:
            # Each phase gets 3-5 tasks per day
            num_tasks = random.randint(3, 5)
            day_tasks = random.sample(LABOUR_TASKS, k=min(num_tasks, len(LABOUR_TASKS)))

            for task_info in day_tasks:
                headcount = random.randint(*task_info["typical_headcount"])
                hours_per_person = round(random.uniform(7, 9), 1)
                total_hours = round(headcount * hours_per_person, 1)
                cost = round(total_hours * task_info["rate_per_hour"], 2)

                # Find blocks in this phase for section allocation
                phase_blocks = [b for b in BLOCKS if b["phase"] == phase["name"]]
                section = random.choice(phase_blocks)["block_name"]

                rows.append(
                    {
                        "Date": day.isoformat(),
                        "Phase": phase["name"],
                        "Section": section,
                        "Task": task_info["task"],
                        "Headcount": headcount,
                        "Hours per Person": hours_per_person,
                        "Total Hours": total_hours,
                        "Rate per Hour (ZAR)": task_info["rate_per_hour"],
                        "Total Cost (ZAR)": cost,
                    }
                )

    return rows


# ── Generator: Harvesting ──────────────────────────────────────────────


def generate_harvesting():
    """Generate harvesting.csv — kg picked per block.

    April in SA is late harvest / tail end for some varieties.
    Only early varieties (Star, Emerald) might still have some picking.
    Most blocks will have zero harvest in April (post-season).
    Include some data so the yield calculations work.
    """
    rows = []

    # Only blocks with early varieties have harvest in April
    harvesting_blocks = [
        b
        for b in BLOCKS
        if b["variety"] in ("Star", "Emerald") and b["year_planted"] <= 2021  # mature enough
    ]

    if not harvesting_blocks:
        # Ensure at least a few blocks have harvest data
        harvesting_blocks = random.sample(
            [b for b in BLOCKS if b["year_planted"] <= 2021],
            k=min(4, len([b for b in BLOCKS if b["year_planted"] <= 2021])),
        )

    # Harvest happens on ~60% of workdays for tail-end picking
    harvest_days = [
        d for d in daterange(START_DATE, END_DATE) if is_workday(d) and random.random() < 0.6
    ]

    for day in harvest_days:
        # Pick from a subset of harvesting blocks each day
        picking_today = random.sample(
            harvesting_blocks,
            k=min(random.randint(2, 5), len(harvesting_blocks)),
        )

        for block in picking_today:
            # Tail-end harvest: lower yields
            kg_per_hectare = random.uniform(20, 120)
            kg = round(block["hectares"] * kg_per_hectare, 1)
            # Lugs are ~10kg each
            lugs = int(kg / 10)

            rows.append(
                {
                    "Date": day.isoformat(),
                    "Phase": block["phase"],
                    "Block": block["block_name"],
                    "Variety": block["variety"],
                    "Kg Harvested": kg,
                    "Lug Count": lugs,
                    "Pickers": random.randint(8, 25),
                }
            )

    return rows


# ── Write CSV Files ────────────────────────────────────────────────────


def write_csv(filename: str, rows: list[dict]):
    """Write a list of dicts to a CSV file."""
    if not rows:
        print(f"  {filename}: no data to write")
        return

    filepath = OUTPUT_DIR / filename
    fieldnames = list(rows[0].keys())
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"  {filename}: {len(rows)} rows")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Generating synthetic FarmTrace exports for April 2026...")
    print(f"Output: {OUTPUT_DIR}/")
    print()

    print("Block Setup:")
    block_data = generate_block_setup()
    write_csv("block_setup.csv", block_data)
    total_ha = sum(b["hectares"] for b in BLOCKS)
    print(f"  {len(BLOCKS)} blocks across {len(PHASES)} phases, " f"{total_ha:.1f} hectares total")
    print()

    print("Fuel Transactions:")
    fuel_data = generate_fuel_transactions()
    write_csv("fuel_transactions.csv", fuel_data)
    total_litres = sum(r["Litres"] for r in fuel_data)
    total_fuel_cost = sum(r["Cost (ZAR)"] for r in fuel_data)
    print(f"  {total_litres:,.0f} litres, R{total_fuel_cost:,.0f} total")
    print()

    print("Stock Movements:")
    stock_data = generate_stock_movements()
    write_csv("stock_movements.csv", stock_data)
    grv_total = sum(r["Total Cost (ZAR)"] for r in stock_data if r["Movement Type"] == "GRV")
    usage_total = sum(r["Total Cost (ZAR)"] for r in stock_data if r["Movement Type"] == "Usage")
    print(f"  GRV (purchased): R{grv_total:,.0f}")
    print(f"  Usage: R{usage_total:,.0f}")
    print()

    print("Labour:")
    labour_data = generate_labour()
    write_csv("labour.csv", labour_data)
    total_labour = sum(r["Total Cost (ZAR)"] for r in labour_data)
    print(f"  R{total_labour:,.0f} total labour cost")
    print()

    print("Harvesting:")
    harvest_data = generate_harvesting()
    write_csv("harvesting.csv", harvest_data)
    total_kg = sum(r["Kg Harvested"] for r in harvest_data)
    print(f"  {total_kg:,.0f} kg harvested")
    print()

    print("=" * 50)
    total_rows = (
        len(block_data) + len(fuel_data) + len(stock_data) + len(labour_data) + len(harvest_data)
    )
    print(f"Total: {total_rows:,} rows across 5 files")
    print()
    print("Summary of monthly costs:")
    print(f"  Fuel:     R{total_fuel_cost:>12,.2f}")
    print(f"  Stock:    R{usage_total:>12,.2f} (usage)")
    print(f"  Labour:   R{total_labour:>12,.2f}")
    grand_total = total_fuel_cost + usage_total + total_labour
    print(f"  ─────────────────────────")
    print(f"  Total:    R{grand_total:>12,.2f}")


if __name__ == "__main__":
    main()
