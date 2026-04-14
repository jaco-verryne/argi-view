# Production Plan — Cost-Efficient Architecture

## Total Cost: R0/month

Every component below is free-tier. You pay nothing until you outgrow
the free limits, which won't happen with one farm and likely not with
ten farms.

---

## Architecture

```
  Dad exports from                  ETL runs on              Dashboard on
  FarmTrace weekly                  schedule                 Streamlit Cloud
  ──────────────                    ────────                 ───────────────

  ┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────────────┐
  │ FarmTrace │───>│  Google   │───>│  GitHub   │───>│ Streamlit Community│
  │  exports  │    │  Drive    │    │  Actions  │    │     Cloud          │
  │ (CSV/Excel│    │ (shared   │    │ (ETL cron)│    │  (dashboard app)   │
  │  files)   │    │  folder)  │    │           │    │                    │
  └───────────┘    └─────┬─────┘    └─────┬─────┘    └────────┬──────────┘
                         │                │                   │
                         │                ▼                   │
                         │         ┌───────────┐              │
                         └────────>│ Supabase  │<─────────────┘
                          files    │PostgreSQL │  SQL queries
                          stored   │ (free)    │
                          here too └───────────┘
```

### Component Breakdown

| Component | Service | Free Tier Limits | Our Usage |
|-----------|---------|-----------------|-----------|
| **Database** | Supabase | 500MB storage, unlimited reads | ~50MB/year per farm |
| **Dashboard** | Streamlit Community Cloud | Unlimited public apps | 1 app |
| **ETL runner** | GitHub Actions | 2,000 min/month | ~30 min/month |
| **File storage** | Google Drive | 15GB | A few MB of exports |
| **Code hosting** | GitHub | Unlimited private repos | 1 repo |

**500MB on Supabase** = roughly 10 years of data for one farm, or 1 year
for 10 farms. You won't hit this limit for a long time.

---

## How Each Layer Works

### Layer 1: Database (Supabase PostgreSQL)

Supabase gives you a full PostgreSQL database for free. It's managed —
no servers, no backups, no patching. You just connect and query.

**Connection from Python/Streamlit:**
```python
import streamlit as st
import psycopg2

# Connection string stored in Streamlit secrets
conn = psycopg2.connect(st.secrets["supabase_url"])
```

**Key tables:**
```sql
-- The unified cost table (the core of everything)
CREATE TABLE fact_cost (
    cost_id     SERIAL PRIMARY KEY,
    date        DATE NOT NULL,
    phase_id    INT NOT NULL,
    block_id    INT,                -- nullable (some costs are phase-level)
    category    TEXT NOT NULL,       -- 'labour', 'diesel', 'chemicals', etc.
    subcategory TEXT,                -- task name, product name, vehicle
    quantity    DECIMAL,
    unit        TEXT,                -- 'litres', 'kg', 'hours'
    cost_rands  DECIMAL NOT NULL,
    source_module TEXT,              -- 'fuel', 'labour', 'stock_movement'
    source_file TEXT
);

-- Indexes for fast queries
CREATE INDEX idx_cost_date ON fact_cost(date);
CREATE INDEX idx_cost_phase ON fact_cost(phase_id, date);
CREATE INDEX idx_cost_block ON fact_cost(block_id, date);
CREATE INDEX idx_cost_category ON fact_cost(category, date);
```

**Why these indexes matter:**
Without indexes, the database scans every row to find matches. With
indexes, it jumps directly to the matching rows. The difference:
- Without index: ~200ms for 1M rows (still fast, but grows linearly)
- With index: ~2ms regardless of table size

### Layer 2: ETL Pipeline (GitHub Actions)

GitHub Actions runs your Python ETL script on a schedule. No servers
to manage. It:
1. Downloads new files from Google Drive
2. Parses each FarmTrace export
3. Normalizes and unifies into fact_cost schema
4. Loads into Supabase PostgreSQL

**Schedule:** Daily at 05:00 SAST (or on-demand via manual trigger)

```yaml
# .github/workflows/etl.yml
name: ETL Pipeline
on:
  schedule:
    - cron: '0 3 * * *'  # 03:00 UTC = 05:00 SAST
  workflow_dispatch:       # manual trigger button

jobs:
  etl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python src/etl/run.py
        env:
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          GOOGLE_CREDENTIALS: ${{ secrets.GOOGLE_CREDENTIALS }}
```

**Cost:** GitHub Actions gives 2,000 minutes/month free. The ETL for one
farm takes ~1 minute per run. Daily runs = 30 minutes/month. You could
run 60 farms before hitting the limit.

### Layer 3: Dashboard (Streamlit Community Cloud)

The Streamlit app connects to Supabase and queries on every interaction.

**How queries update as dad interacts:**

```python
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine

# Connect once (cached)
@st.cache_resource
def get_engine():
    return create_engine(st.secrets["supabase_url"])

# This function re-runs every time a filter changes
def eagle_view():
    # Dad picks a date range and phase
    date_range = st.date_input("Date range", value=[...])
    phase = st.selectbox("Phase", ["All", "Phase 1", "Phase 2", ...])

    # Build query based on selections
    query = """
        SELECT category, SUM(cost_rands) as total_cost
        FROM fact_cost
        WHERE date BETWEEN %(start)s AND %(end)s
    """
    params = {"start": date_range[0], "end": date_range[1]}

    if phase != "All":
        query += " AND phase_id = %(phase_id)s"
        params["phase_id"] = get_phase_id(phase)

    query += " GROUP BY category ORDER BY total_cost DESC"

    # Query fires, results come back, chart renders
    df = pd.read_sql(query, get_engine(), params=params)
    st.bar_chart(df.set_index("category"))
```

**What happens on each interaction:**
1. Dad changes a filter → Streamlit re-runs the function
2. New SQL query with updated WHERE clause → sent to Supabase
3. Supabase returns results in ~5ms over the network
4. Streamlit renders updated charts
5. Total time: ~100-300ms (feels instant)

**Caching for speed:**
```python
# Cache query results for 5 minutes
# Same filter combination = instant, no database hit
@st.cache_data(ttl=300)
def query_costs(farm_id, start_date, end_date, phase_id=None):
    # ... SQL query here ...
    return df
```

---

## Query Patterns

These are the actual SQL queries that power each dashboard page.

### Eagle View — Total cost breakdown
```sql
SELECT
    category,
    SUM(cost_rands) as total_cost,
    COUNT(*) as transaction_count
FROM fact_cost
WHERE date BETWEEN :start_date AND :end_date
GROUP BY category
ORDER BY total_cost DESC;
```

### Eagle View — Daily trend
```sql
SELECT
    date,
    category,
    SUM(cost_rands) as daily_cost
FROM fact_cost
WHERE date BETWEEN :start_date AND :end_date
GROUP BY date, category
ORDER BY date;
```

### Block Drill-Down — Cost per hectare
```sql
SELECT
    b.name as block_name,
    b.hectares,
    SUM(c.cost_rands) as total_cost,
    SUM(c.cost_rands) / b.hectares as cost_per_hectare
FROM fact_cost c
JOIN dim_block b ON c.block_id = b.block_id
WHERE c.phase_id = :phase_id
  AND c.date BETWEEN :start_date AND :end_date
GROUP BY b.name, b.hectares
ORDER BY cost_per_hectare DESC;
```

### Budget vs Actual
```sql
SELECT
    c.category,
    SUM(c.cost_rands) as actual,
    b.budget_rands as budget,
    SUM(c.cost_rands) - b.budget_rands as variance
FROM fact_cost c
JOIN fact_budget b
  ON c.category = b.category
  AND EXTRACT(MONTH FROM c.date) = b.month
  AND EXTRACT(YEAR FROM c.date) = b.year
WHERE c.farm_id = :farm_id
  AND EXTRACT(MONTH FROM c.date) = :month
  AND EXTRACT(YEAR FROM c.date) = :year
GROUP BY c.category, b.budget_rands;
```

### Purchase vs Usage (the "did we buy too much?" question)
```sql
SELECT
    p.name as product,
    SUM(CASE WHEN s.movement_type = 'grv' THEN s.quantity END) as purchased,
    SUM(CASE WHEN s.movement_type = 'usage' THEN s.quantity END) as used,
    SUM(CASE WHEN s.movement_type = 'grv' THEN s.quantity END) -
    SUM(CASE WHEN s.movement_type = 'usage' THEN s.quantity END) as surplus
FROM fact_stock_detail s
JOIN dim_product p ON s.product_id = p.product_id
WHERE s.date_id BETWEEN :start AND :end
GROUP BY p.name
HAVING SUM(CASE WHEN s.movement_type = 'grv' THEN s.quantity END) >
       SUM(CASE WHEN s.movement_type = 'usage' THEN s.quantity END) * 1.5
ORDER BY surplus DESC;
```

### Fuel Theft Flag
```sql
WITH daily_avg AS (
    SELECT
        equipment_id,
        AVG(litres) as avg_litres,
        STDDEV(litres) as std_litres
    FROM fact_fuel_detail
    WHERE date_id BETWEEN :start AND :end
    GROUP BY equipment_id
)
SELECT
    f.date_id, e.name as vehicle,
    f.litres, a.avg_litres,
    f.litres - a.avg_litres as deviation
FROM fact_fuel_detail f
JOIN dim_equipment e ON f.equipment_id = e.equipment_id
JOIN daily_avg a ON f.equipment_id = a.equipment_id
WHERE f.litres > a.avg_litres + (2 * a.std_litres)
ORDER BY deviation DESC;
```

---

## Performance Optimizations

### 1. Indexes (already covered above)
Every column that appears in a WHERE or GROUP BY gets an index.

### 2. Materialized Views (pre-computed summaries)
For queries that run constantly (e.g., monthly totals), pre-compute:

```sql
-- Refreshed by ETL after each data load
CREATE MATERIALIZED VIEW mv_monthly_cost AS
SELECT
    phase_id, block_id, category,
    DATE_TRUNC('month', date) as month,
    SUM(cost_rands) as total_cost,
    SUM(quantity) as total_quantity
FROM fact_cost
GROUP BY phase_id, block_id, category, DATE_TRUNC('month', date);

CREATE INDEX idx_mv_monthly ON mv_monthly_cost(month);
```

Dashboard queries the materialized view instead of scanning fact_cost.
Result: sub-millisecond queries for monthly summaries.

### 3. Streamlit Caching
```python
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_monthly_costs(year, month):
    ...
```
Same filter combination within 5 minutes = zero database load.

### 4. Connection Pooling
```python
@st.cache_resource  # One connection pool for the whole app
def get_engine():
    return create_engine(
        st.secrets["supabase_url"],
        pool_size=5,
        pool_recycle=3600
    )
```

---

## Scaling Path

This POC is for one farm. The commercial path is decided after the demo.

| Stage | What | Database | Cost |
|-------|------|----------|------|
| **POC** | One farm, ~500k rows/yr | Supabase free | R0/month |
| **If farm buys it** | Same setup, add more data | Supabase free | R0/month |
| **If FarmTrace buys it** | Their problem | Their infra | N/A |
| **If consulting** | Adapt per client | Supabase per client | ~R0-400/month |

Don't build for scale until scale is the actual problem.

---

## Setup Checklist

1. [ ] **Supabase account** — sign up at supabase.com, create a project
2. [ ] **Create tables** — run the SQL schema above
3. [ ] **Get connection string** — from Supabase dashboard > Settings > Database
4. [ ] **Add to Streamlit secrets** — `supabase_url = "postgresql://..."`
5. [ ] **GitHub Actions** — add SUPABASE_URL and GOOGLE_CREDENTIALS as repo secrets
6. [ ] **Test** — load a sample FarmTrace export, query from Streamlit
