# AgriView - Technical Architecture

> **Updated after discovery session (13 April 2026).**
> The core problem is not fuel analytics — it's breaking FarmTrace's data
> silos into a unified cost view per block per day.

## Design Principles

1. **Silo breaker** — The entire value is in combining data that FarmTrace
   keeps separate. Every design decision serves the unified view.
2. **Block-level attribution** — Every cost must be attributable to a spatial
   block (or at minimum a phase). If direct attribution isn't possible,
   estimate and flag it.
3. **Daily granularity** — Dad currently works at monthly level because daily
   is too tedious by hand. The system must deliver daily-level drill-down.
4. **Zero-friction ingestion** — Dad exports from FarmTrace to Google Drive.
   The system picks up new files automatically.
5. **Real data only** — The POC runs against actual FarmTrace exports.
6. **One farm, no premature abstraction** — This is a POC for one farm. No
   multi-tenancy, no farm_id overhead. If the commercial path requires
   multi-tenant, that's a future rewrite — not today's problem.

---

## System Overview

```
  FARMTRACE                    ETL PIPELINE              STORAGE             DASHBOARD
  =========                    ============              =======             =========

  Labour Export ────────┐
  (tasks, hours, cost)  │
                        │
  Fuel Transactions ────┤     ┌──────────────┐     ┌──────────┐     ┌───────────────┐
  (vehicle, litres,     │     │  Python ETL   │     │PostgreSQL│     │   Streamlit    │
   pump readings)       │     │              │     │          │     │   Dashboard    │
                        ├────>│ - parse each │────>│ - dim_   │────>│               │
  Stock Movements ──────┤     │   module     │     │   block  │     │ - Eagle View  │
  (products, blocks,    │     │ - normalize  │     │ - dim_   │     │ - Block drill │
   quantities)          │     │ - unify into │     │   equip  │     │ - Budget vs   │
                        │     │   fact_cost  │     │ - dim_   │     │   actual      │
  Harvesting ───────────┤     │ - tag with   │     │   product│     │ - Anomalies   │
  (kg, blocks,          │     │   category   │     │ - fact_  │     │ - Yield/ha    │
   varieties)           │     │              │     │   cost   │     │               │
                        │     └──────────────┘     │ - fact_  │     └───────────────┘
  Block Setup ──────────┘                          │   yield  │
  (hectares, variety,         Google Drive          └──────────┘          Browser
   plant count)               watched folder

  All files: FarmTrace CSV/Excel exports uploaded to shared Google Drive
```

---

## Data Model

Single-farm design. No multi-tenancy overhead.

### Dimension Tables

**dim_phase**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| phase_id        | PK      | Internal ID                          |
| name            | text    | "Phase 1", "Phase 2", etc.           |

**dim_block**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| block_id        | PK      | Internal ID                          |
| phase_id        | FK      | -> dim_phase                         |
| name            | text    | Block number / name from FarmTrace   |
| hectares        | decimal | Area                                 |
| variety         | text    | Blueberry variety                    |
| plant_count     | int     | Number of plants                     |

**dim_equipment**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| equipment_id    | PK      | Internal ID                          |
| name            | text    | FarmTrace name / fleet number        |
| category        | text    | tractor, bakkie, generator, pump,... |
| fuel_type       | text    | diesel, petrol                       |

**dim_product**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| product_id      | PK      | Internal ID                          |
| name            | text    | Product name from FarmTrace          |
| category        | text    | GMI, workshop, toiletry, hardware,...|
| unit            | text    | litres, kg, units                    |
| unit_cost       | decimal | Price per unit (ZAR)                 |
| package_size    | decimal | Size of package/container            |

**dim_date**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| date_id         | PK      | YYYYMMDD                             |
| date            | date    |                                      |
| day_of_week     | text    | Monday, Tuesday, ...                 |
| week            | int     | ISO week number                      |
| month           | int     |                                      |
| year            | int     |                                      |
| season          | text    | "2025/26" (SA blueberry season)      |

### Fact Tables

The central design: **one unified cost table** that all modules feed into,
plus module-specific tables for detail drill-down.

**fact_cost** (The unified table — this IS the product)
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| cost_id         | PK      | Auto-generated                       |
| date_id         | FK      | -> dim_date                          |
| block_id        | FK      | -> dim_block (nullable — some costs are phase-level) |
| phase_id        | FK      | -> dim_phase                         |
| category        | text    | "labour", "diesel", "chemicals", "stock", "toiletries", "workshop" |
| subcategory     | text    | Finer detail: task name, product name, vehicle ID |
| description     | text    | Human-readable detail                |
| quantity         | decimal | Units consumed (litres, kg, hours)   |
| unit            | text    | "litres", "kg", "hours", "units"     |
| cost_rands      | decimal | Total cost in ZAR                    |
| source_module   | text    | "fuel", "labour", "stock_movement", "harvesting" |
| source_file     | text    | Original FarmTrace export filename   |

> **This is the table that breaks the silos.** Every cost from every module
> lands here with the same schema: date + block + category + amount. The
> dashboard queries this single table.

**fact_fuel_detail** (drill-down for fuel-specific analysis)
| Column             | Type    | Notes                             |
|--------------------|---------|-----------------------------------|
| txn_id             | PK      | Auto-generated                    |
| date_id            | FK      | -> dim_date                       |
| equipment_id       | FK      | -> dim_equipment                  |
| phase_id           | FK      | -> dim_phase                      |
| task               | text    | Activity (folio spray, mowing,..) |
| litres             | decimal | Volume dispensed                  |
| cost_rands         | decimal | Cost in ZAR                       |
| pump_reading_start | decimal | Initial pump meter reading        |
| pump_reading_end   | decimal | Final pump meter reading          |
| hours              | decimal | Hours worked                      |
| odometer           | decimal | Odometer reading                  |
| service_interval   | text    | Service interval status           |
| source_file        | text    | Original filename                 |

**fact_stock_detail** (drill-down for stock/chemicals)
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| movement_id     | PK      | Auto-generated                       |
| date_id         | FK      | -> dim_date                          |
| product_id      | FK      | -> dim_product                       |
| block_id        | FK      | -> dim_block (nullable)              |
| phase_id        | FK      | -> dim_phase                         |
| movement_type   | text    | "grv" (purchased), "usage", "adjustment" |
| quantity         | decimal | Amount                               |
| cost_rands      | decimal | Value in ZAR                         |
| instruction_ref | text    | FarmTrace instruction reference      |
| source_file     | text    | Original filename                    |

**fact_labour_detail** (drill-down for labour)
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| entry_id        | PK      | Auto-generated                       |
| date_id         | FK      | -> dim_date                          |
| phase_id        | FK      | -> dim_phase                         |
| block_id        | FK      | -> dim_block (nullable)              |
| task            | text    | Task description                     |
| hours           | decimal | Hours worked                         |
| headcount       | int     | Number of workers                    |
| cost_rands      | decimal | Labour cost in ZAR                   |
| source_file     | text    | Original filename                    |

**fact_yield**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| yield_id        | PK      | Auto-generated                       |
| date_id         | FK      | -> dim_date                          |
| block_id        | FK      | -> dim_block                         |
| phase_id        | FK      | -> dim_phase                         |
| variety         | text    | Blueberry variety                    |
| kg_harvested    | decimal | Kilograms picked                     |
| lug_count       | int     | Number of lugs/crates                |
| source_file     | text    | Original filename                    |

**fact_budget** (for budget vs actual comparison)
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| budget_id       | PK      | Auto-generated                       |
| month           | int     | Budget month                         |
| year            | int     | Budget year                          |
| category        | text    | "labour", "diesel", "chemicals",...  |
| budget_rands    | decimal | Budgeted amount in ZAR               |

---

## ETL Pipeline

### Overview

```
FarmTrace Exports (Google Drive)
        │
        ▼
┌─────────────────┐
│  Module Parsers  │  One parser per FarmTrace export type
│  - parse_fuel()  │  Each returns a standardized DataFrame
│  - parse_labour()│
│  - parse_stock() │
│  - parse_harvest()│
│  - parse_blocks()│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Normalizer     │  Map FarmTrace IDs to internal IDs
│  - resolve block │  Validate data quality
│  - resolve equip │  Flag anomalies
│  - resolve prod  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Cost Unifier    │  Every module → fact_cost rows
│  - tag category  │  (date, block, category, cost)
│  - calculate cost│
│  - write unified │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Loader        │  Write to PostgreSQL
│  - dims first   │  Upsert to avoid duplicates
│  - facts second │
└─────────────────┘
```

### Step 1: Parse Module Exports

```python
# Each parser reads one FarmTrace export type and returns a DataFrame
# Column names TBD based on actual export files

def parse_fuel_transactions(filepath):
    """Parse FarmTrace fuel transaction export.

    Expected columns (from meeting): date, phase, vehicle, task,
    pump_reading_initial, pump_reading_final, litres, hours, odometer
    """
    df = pd.read_excel(filepath)
    df["source_module"] = "fuel"
    df["source_file"] = filepath.name
    return df

def parse_stock_movements(filepath):
    """Parse FarmTrace stock movement export.

    Expected columns: date, product, category (GMI/workshop/toiletry),
    block, phase, quantity, movement_type (GRV/usage/adjustment)

    Note: ~1,300 rows per day, ~500k rows for 10 days.
    """
    df = pd.read_excel(filepath)
    df["source_module"] = "stock_movement"
    df["source_file"] = filepath.name
    return df

def parse_labour(filepath):
    """Parse FarmTrace labour/task export.

    Expected columns: date, phase, section, task, hours, cost
    """
    df = pd.read_excel(filepath)
    df["source_module"] = "labour"
    df["source_file"] = filepath.name
    return df

def parse_harvest(filepath):
    """Parse FarmTrace harvesting export.

    Expected columns: date, block, variety, phase, kg, lug_count
    """
    df = pd.read_excel(filepath)
    df["source_module"] = "harvesting"
    df["source_file"] = filepath.name
    return df

def parse_block_setup(filepath):
    """Parse FarmTrace block setup / production unit data.

    Expected columns: block_number, variety, hectares, plant_count, phase
    """
    df = pd.read_excel(filepath)
    return df
```

### Step 2: Normalize & Validate

```python
def normalize_to_cost(df, module_type):
    """Transform any module DataFrame into fact_cost schema.

    Maps module-specific columns to the unified schema:
    (date, block, phase, category, quantity, unit, cost_rands)
    """
    # Module-specific mapping logic here
    # E.g., fuel: category="diesel", quantity=litres, cost=litres*price
    # E.g., stock: category=product_category, cost=quantity*unit_cost
    # E.g., labour: category="labour", cost=hours*rate
    pass

def validate_costs(df):
    """Flag anomalies in the unified cost data.

    - Daily fuel > 2x rolling average for that phase → theft flag
    - Purchase quantity >> usage quantity → overstock flag
    - Cost per hectare > farm average by 25% → efficiency flag
    - Negative quantities
    - Missing block/phase attribution
    """
    pass
```

### Step 3: Load

```python
def load_dimensions(engine, block_setup_df, equipment_df, product_df):
    """Load/update dimension tables from FarmTrace master data."""
    pass

def load_facts(engine, cost_df, detail_dfs):
    """Load unified fact_cost and module detail tables.

    Uses upsert to handle re-processing of the same export files.
    """
    pass
```

---

## Dashboard Views (Streamlit)

### Page 1: Eagle View (The Home Page)

This is what dad opens every morning. One screen, full picture.

- **Date selector** — pick a day, week, or month
- **Total cost** for selected period, with trend arrow (up/down vs prior period)
- **Cost breakdown bar** — stacked bar showing labour / diesel / chemicals / stock / other
- **Phase summary cards** — one card per phase showing total cost + top cost driver
- **Budget gauge** — actual vs budget for the month, red/amber/green

### Page 2: Block Drill-Down

- **Select a phase** → see all blocks in that phase
- **Per block:** total cost, cost per hectare, breakdown by category
- **Comparison:** blocks side-by-side within a phase
- **Anomaly highlights:** blocks where cost/ha is >25% above phase average

### Page 3: Cost Category Deep-Dive

Pick a category (diesel, chemicals, labour, etc.) and see:
- **Trend:** daily/weekly/monthly cost over time
- **Top drivers:** which blocks, vehicles, or products are driving the cost
- **Purchase vs Usage** (for stock categories): did we buy more than we used?
  Flag items where purchased >> used

### Page 4: Fuel Detail

- Fuel transactions per vehicle per day
- Pump reading reconciliation (litres dispensed vs pump reading delta)
- Litres per hour per vehicle (efficiency metric)
- **Theft flags:** unusual consumption, pump reading gaps

### Page 5: Budget vs Actual

- Monthly budget per category
- Actual spend overlaid
- Variance (over/under) with highlighting
- Cash flow projection: if current run rate continues, what's the year-end position?
- **Early warning:** categories trending above budget before month-end

### Page 6: Yield & Efficiency

- Kg harvested per block per day/week/season
- **Kg per hectare** by block (the benchmark metric)
- **Cost per kg** by block (total input cost / kg harvested)
- Phase-level and variety-level aggregations

---

## Tech Stack

| Layer        | Technology     | Rationale                                |
|--------------|----------------|------------------------------------------|
| Language     | Python 3.11+   | Data ecosystem, Thomas's skillset        |
| ETL          | pandas          | Good enough for farm-scale data volumes  |
| Database     | PostgreSQL      | Free, robust, good SQL. SQLite fallback  |
| ORM          | SQLAlchemy      | Standard, works with both PG and SQLite  |
| Dashboard    | Streamlit       | Fastest path to interactive dashboard    |
| Charts       | Plotly          | Interactive, good defaults, Streamlit-native |
| Maps         | Folium          | Leaflet-based, for block heatmaps        |
| Google Drive | PyDrive2/gdrive | Watch for new FarmTrace exports          |
| Fuzzy match  | rapidfuzz       | For entity resolution if names vary      |
| Hosting      | Local / Hetzner | SA datacenter available, cheap VMs       |
| Version ctrl | Git             | Standard                                 |

---

## Deployment (POC)

```
Shared Google Drive
      │
      │  Dad uploads FarmTrace exports here
      │
      ▼
Your machine / Hetzner VM
      │
      ├── Cron: check Drive for new files every hour
      ├── ETL: parse → normalize → unify → load
      └── Streamlit: dashboard on port 8501
              │
              ▼
        Dad opens on phone/laptop
        (Streamlit Community Cloud or Tailscale)
```

### Ingestion Trigger

```
POC: Manual or cron-based
- Dad exports from FarmTrace, saves to Google Drive
- You run the ETL pipeline (or cron runs it hourly)
- Dashboard refreshes on next page load

Future: FarmTrace API
- Dad mentioned the possibility of direct API access
- Would eliminate the export-upload step entirely
- Explore after POC proves value
```

---

## Roadmap

### POC (Now)
- Ingest FarmTrace exports: fuel, labour, stock movements, harvesting
- Unified fact_cost table
- Eagle View dashboard with block drill-down
- Budget vs actual (if budget data available)

### If POC lands with stakeholders
- FarmTrace API integration (eliminate manual exports)
- Anomaly detection and alerting (WhatsApp/email)
- Automated weekly PDF report
- Scouting + water monitoring integration

### Commercial path (decided after demo)
- **Option A:** Farm buys it → you maintain as contractor/consultant
- **Option B:** FarmTrace buys/licenses it → they integrate into their platform
- **Option C:** Portfolio piece → use to pitch consulting to other farms
