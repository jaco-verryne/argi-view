# AgriView - Technical Architecture

> This is a preliminary architecture. It will be refined after the discovery
> session based on the actual data formats and constraints uncovered.

## Design Principles

1. **Zero-friction ingestion** — The user must never upload files to a web form.
   Data arrives via shared folders, email forwarding, or scheduled exports.
2. **Block-level attribution** — Every cost must be attributable to a spatial
   block on the farm. If direct attribution isn't possible, estimate and flag.
3. **Real data only** — No synthetic data in the POC. It must run against
   actual farm exports, however messy.
4. **Insight over infrastructure** — The POC proves the value of the analytics,
   not the scalability of the platform. Keep it simple.

---

## System Overview

```
  DATA SOURCES               ETL PIPELINE              STORAGE              DASHBOARD
  ============               ============              =======              =========

  Google Forms ─────┐
  (via Google       │
   Sheets API)      │       ┌─────────────┐       ┌──────────┐       ┌──────────────┐
                    ├──────>│  Python ETL  │──────>│ PostgreSQL│──────>│   Streamlit   │
  FarmTrace Export ─┤       │             │       │          │       │   Dashboard   │
  (CSV/Excel)       │       │ - pull from │       │ - master │       │              │
                    │       │   Sheets API│       │   tables │       │ - KPIs       │
  Supplier Invoice ─┤       │ - clean     │       │ - fact   │       │ - charts     │
  (PDF/Excel)       │       │ - resolve   │       │   tables │       │ - trends     │
                    │       │   entities  │       │ - farm_id│       │ - alerts     │
  Equipment List ───┤       │ - attribute │       │   on all │       │ - export     │
  (Sheets/Manual)   │       │   to blocks │       │   tables │       │              │
                    │       └─────────────┘       └──────────┘       └──────────────┘
  Block/Yield Data ─┘
  (Sheets/FarmTrace)        Cron / scheduled        Local/VM             Browser
                            pull from
                            Google Sheets
```

> **Key insight:** The farm has moved from pen-and-paper to **Google Forms**
> for data capture. Form responses flow automatically into Google Sheets.
> This means the primary ingestion path is the **Google Sheets API** — not
> file uploads, not PDF parsing. This is significantly simpler than expected.

---

## Data Model (Star Schema)

### Multi-Tenancy

Every table includes a `farm_id` column from day one. The POC will only have
one farm, but this costs nothing now and avoids a painful migration later when
selling to other farms.

**dim_farm**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| farm_id         | PK      | Internal ID                          |
| name            | text    | "Southfield Blueberries"             |
| region          | text    | Province / area                      |
| total_hectares  | decimal |                                      |

### Dimension Tables

**dim_equipment**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| equipment_id    | PK      | Internal ID                          |
| farm_id         | FK      | -> dim_farm                          |
| name            | text    | Canonical name ("Tractor 01")        |
| aliases         | text[]  | All known names ("T1", "Blue JD")    |
| category        | text    | tractor, bakkie, generator, pump,... |
| fuel_type       | text    | diesel, petrol                       |
| model           | text    | Manufacturer model if known          |
| year            | int     | Year of manufacture if known         |
| hour_meter      | boolean | Whether hour tracking is available   |

**dim_block**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| block_id        | PK      | Internal ID                          |
| farm_id         | FK      | -> dim_farm                          |
| name            | text    | "A1", "B3", "Hill Block"             |
| hectares        | decimal | Area                                 |
| variety         | text    | Blueberry variety if relevant        |
| plant_year      | int     | Year planted (age affects yield)     |
| lat             | decimal | Center point latitude (for mapping)  |
| lon             | decimal | Center point longitude               |

**dim_date**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| date_id         | PK      | YYYYMMDD                             |
| date            | date    |                                      |
| week            | int     | ISO week number                      |
| month           | int     |                                      |
| quarter         | int     |                                      |
| year            | int     |                                      |
| season          | text    | "2024/25" (SA blueberry season)      |

### Fact Tables

**fact_fuel_transaction**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| txn_id          | PK      | Auto-generated                       |
| farm_id         | FK      | -> dim_farm                          |
| date_id         | FK      | -> dim_date                          |
| equipment_id    | FK      | -> dim_equipment                     |
| block_id        | FK      | -> dim_block (nullable)              |
| litres          | decimal | Volume dispensed                     |
| cost_rands      | decimal | Cost in ZAR                          |
| price_per_litre | decimal | Derived or from invoice              |
| meter_reading   | decimal | Hour meter or odometer (nullable)    |
| operator        | text    | Who was operating (nullable)         |
| activity        | text    | spraying, mowing, transport (null.)  |
| source          | text    | "farmtrace", "bowser_log", "invoice" |
| source_file     | text    | Original filename for traceability   |

**fact_fuel_delivery**
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| delivery_id     | PK      |                                      |
| farm_id         | FK      | -> dim_farm                          |
| date_id         | FK      | -> dim_date                          |
| fuel_type       | text    | diesel, petrol                       |
| litres          | decimal | Volume delivered                     |
| cost_rands      | decimal | Total cost                           |
| supplier        | text    |                                      |
| invoice_ref     | text    |                                      |
| source_file     | text    |                                      |

**fact_yield** (Phase 1 if data available, otherwise Phase 2)
| Column          | Type    | Notes                                |
|-----------------|---------|--------------------------------------|
| yield_id        | PK      |                                      |
| date_id         | FK      | -> dim_date                          |
| block_id        | FK      | -> dim_block                         |
| kg_harvested    | decimal |                                      |
| season          | text    |                                      |

---

## ETL Pipeline

### Step 1: Ingest

The primary data source is **Google Sheets** (populated by Google Forms).
Secondary sources may include FarmTrace exports and supplier invoices.

```python
# Pseudocode — column names TBD after seeing actual Google Forms/Sheets

import gspread
from google.oauth2.service_account import Credentials

def connect_to_sheets(credentials_path):
    """Authenticate with Google Sheets API using a service account."""
    creds = Credentials.from_service_account_file(credentials_path)
    client = gspread.authorize(creds)
    return client

def ingest_fuel_form(client, spreadsheet_id):
    """Pull fuel log data from Google Form responses sheet."""
    sheet = client.open_by_key(spreadsheet_id).sheet1
    df = pd.DataFrame(sheet.get_all_records())
    df["source"] = "google_form_fuel"
    return df

def ingest_farmtrace(filepath):
    """Read FarmTrace CSV/Excel export (secondary source)."""
    df = pd.read_excel(filepath)  # or read_csv
    df["source"] = "farmtrace"
    df["source_file"] = filepath.name
    return df

def ingest_invoice(filepath):
    """Read fuel supplier invoice (PDF or Excel)."""
    # May need pdfplumber for PDFs
    pass
```

### Step 2: Clean & Normalize

```python
def normalize_equipment(raw_name, equipment_master):
    """Map raw equipment names to canonical IDs.

    Uses fuzzy matching against the aliases in dim_equipment.
    E.g., "T1" -> equipment_id 1 ("Tractor 01")
    """
    pass

def normalize_date(raw_date):
    """Parse various date formats to a standard date object."""
    pass

def validate_transaction(row):
    """Flag suspicious records:
    - Negative litres
    - Litres > max tank capacity for that equipment
    - Duplicate timestamps
    - Missing equipment ID
    """
    pass
```

### Step 3: Attribute to Block

```python
def attribute_to_block(transaction, activity_log):
    """Link a fuel transaction to a block.

    Priority:
    1. Direct: activity log says Tractor 01 was in Block A3 on this date
    2. Estimated: Tractor 01 only works in blocks A1-A5, split proportionally
    3. Null: cannot attribute (e.g., generator for pack shed)
    """
    pass
```

### Step 4: Load

```python
def load_to_db(df, table_name, engine):
    """Upsert cleaned data into PostgreSQL."""
    df.to_sql(table_name, engine, if_exists="append", index=False)
```

---

## Dashboard Views (Streamlit)

### Page 1: Executive Summary
- **The "Monday Morning" KPIs** (determined by discovery question F1)
- Total fuel cost this month vs last month vs budget
- Month-on-month trend line
- Biggest movers (equipment or blocks with largest change)

### Page 2: Equipment Analysis
- Bar chart: fuel consumption by equipment (ranked, top 15)
- Filters: date range, equipment category, fuel type
- Table: litres, cost, hours (if available), litres/hour
- Trend line per selected equipment (efficiency over time)

### Page 3: Block Analysis (if spatial data available)
- Fuel cost per hectare by block (bar chart or heatmap)
- Comparison: this season vs last season
- Flag blocks where cost/ha exceeds farm average by >25%
- Link to yield: fuel cost per kg produced (if yield data available)

### Page 4: Reconciliation
- Fuel purchased (deliveries) vs fuel dispensed (transactions)
- Variance over time — does the gap grow? (theft/leak indicator)
- Unaccounted litres highlighted

### Page 5: Anomaly Alerts
- Transactions where litres > 2x standard deviation from that equipment's mean
- Equipment with declining efficiency (litres/hour trending up)
- Days with unusual total consumption

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
| Sheets API   | gspread         | Pull data from Google Forms/Sheets       |
| Auth         | google-auth     | Service account auth for Sheets API      |
| PDF parsing  | pdfplumber      | If invoices are PDFs                     |
| Fuzzy match  | rapidfuzz       | For equipment name resolution            |
| Hosting      | Local / Hetzner | SA datacenter available, cheap VMs       |
| Version ctrl | Git             | Standard                                 |

---

## Deployment (POC)

For the POC, keep it dead simple:

```
Option A: Local                    Option B: VM
─────────────                      ──────────
Run on your laptop.                Hetzner CPX11 (~R80/month).
Dad accesses via Tailscale         Public URL with basic auth.
or screen share.                   Dad bookmarks it on his phone.

Shared Google Drive folder         Same shared folder setup.
for data ingestion.                Cron job checks for new files.
```

### Ingestion Trigger

Since the primary source is Google Sheets (always up to date as forms are
submitted), ingestion is a **scheduled pull**, not a file-watch.

```
Option 1: Scheduled Pull (recommended for POC)
- Cron job runs every N hours (e.g. daily at 05:00)
- Pulls latest rows from Google Sheets via API
- Runs ETL pipeline, updates database
- Dashboard always shows data as of last pull
- No action required from Dad at all

Option 2: On-Demand
- You or Dad triggers a refresh via a button in the dashboard
- Useful during the POC while tuning the pipeline

Option 3: Near-Real-Time (Phase 2)
- Google Apps Script triggers a webhook on form submission
- Pipeline runs within minutes of a new entry
```

---

## Product Roadmap (Modular Expansion)

The fuel module is the first of several planned modules. Each module follows
the same pattern: Google Form for capture -> Sheets API for ingestion ->
dedicated fact table -> dashboard page.

```
MODULE              STATUS          FACT TABLE                GOOGLE FORM
──────              ──────          ──────────                ───────────
Fuel Consumption    POC (now)       fact_fuel_transaction     Fuel log form
                                    fact_fuel_delivery
Chemical Usage      Phase 2         fact_chemical_application Spray log form
Equipment Issues    Phase 2         fact_equipment_issue      Issue report form
Labour Tracking     Phase 3         fact_labour_entry         Timesheet form
Water Usage         Phase 3         fact_water_usage          Irrigation log form
Yield/Harvest       Phase 2-3       fact_yield                Harvest log form
```

Each module is self-contained but shares the same dimension tables (equipment,
blocks, dates, farm). This means cross-module queries are natural:
"What was the total input cost (fuel + chemicals + labour) per kg for Block A3?"

When selling to other farms, modules can be enabled/disabled per customer.
A livestock farm doesn't need the chemical spray module; a wine farm does.

---

## What Changes After Discovery

Almost everything above is a hypothesis. After the session, expect to revise:

1. **Data model columns** — based on actual FarmTrace export columns
2. **Entity resolution rules** — based on actual naming conventions
3. **Block attribution logic** — may be simple or may not exist
4. **Dashboard pages** — based on the "three Monday morning numbers"
5. **Ingestion method** — based on what's easiest for Dad specifically
6. **Reconciliation** — only possible if both delivery and dispensing data exist
