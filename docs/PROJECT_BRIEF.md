# AgriView - Project Brief

## What

A cross-module analytics dashboard that breaks FarmTrace's data silos into
a unified cost view per block per day. Starting as a POC for a large-scale
blueberry farm in South Africa, with the goal of becoming a commercial
product for other farms.

## Why

FarmTrace captures excellent, granular data across all farm operations —
labour, diesel, chemicals, stock, harvesting, scouting. But each module is
a silo. There's no tool that combines them to answer the fundamental question:

> "For Block X on Day Y, what was the total cost — and where did it come from?"

The production manager currently exports each module to Excel, builds query
tables and pivot tables manually, and is limited to monthly summaries. Daily-
level analysis is too tedious by hand. This system automates that entirely.

## Who

- **End user:** Production and development manager (farm-level decision maker)
- **Secondary users:** Farm owner/directors, accountants (report consumers)
- **Future users:** Other farms (commercial product)

## Core Principle

> "The data capture is incredibly good. It's getting it back out in a
> unified way — that's where the work starts."
> — Dad, discovery session

## The Problem in One Sentence

**Data silo decay:** the farm captures everything but can't see across modules.

## Scope

### POC (Phase 1) — Unified Cost View
- Ingest FarmTrace exports: fuel, labour, stock movements, harvesting, block setup
- Unify all costs into a single table: (date, block, category, cost)
- Eagle View dashboard: total cost per phase/block with drill-down
- Budget vs actual tracking
- Anomaly flags (fuel theft, purchase/usage gaps, cost spikes)
- Yield efficiency: kg per hectare, cost per kg

### Phase 2 — Automation & Intelligence
- FarmTrace API integration (eliminate manual exports)
- Automated anomaly alerts (WhatsApp/email)
- Automated weekly PDF reports
- Scouting and water monitoring integration
- Predictive maintenance signals

### Phase 3 — Commercial Product
- Multi-tenant SaaS for other farms
- Configurable modules per customer
- Mobile-optimized dashboard
- Sustainability/traceability exports for EU/UK retailers

## Key Metrics

| Metric | What it answers |
|--------|----------------|
| Total cost per block per day | Where is the money going? |
| Cost per hectare per block | Which blocks are expensive? |
| Kg per hectare | Which blocks are productive? |
| Cost per kg | Which blocks are efficient? |
| Budget vs actual | Are we on track? |
| Purchase vs usage | Are we buying more than we use? |

## Data Sources

All data comes from **FarmTrace exports** uploaded to a shared Google Drive.

| FarmTrace Module | Data | Volume |
|-----------------|------|--------|
| Fuel transactions | Vehicle, litres, pump readings, hours, task | ~10 per day |
| Stock movements | Product, block, quantity, category | ~1,300 per day |
| Labour/tasks | Phase, task, hours, cost | varies |
| Harvesting | Block, variety, kg, lugs | seasonal |
| Block setup | Block number, variety, hectares, plants | static |

## Project Structure

```
agri_view/
  docs/                        # Project documentation
    PROJECT_BRIEF.md             # This file
    ARCHITECTURE.md              # Technical architecture
    MEETING_NOTES_2026_04_13.md  # Discovery session findings
    DISCOVERY.md                 # Original interview questions
    DATA_CHECKLIST.md            # What to collect
    DEPLOY.md                    # Streamlit Cloud deployment
    AGENT_PROMPTS.md             # Reusable AI agent prompts
  data/
    raw/                         # FarmTrace exports (gitignored)
    processed/                   # Cleaned, unified data
  src/                           # Application source code
    questionnaire.py             # Discovery questionnaire app
  notebooks/                     # Exploratory data analysis
```

## Status

**Phase:** Waiting for FarmTrace exports from Dad via Google Drive.
Once files arrive, we build the ETL pipeline and dashboard against real data.
