# AgriView - Project Brief

## What

A modular analytics platform for commercial farms, starting with a **fuel
consumption POC** for a large-scale blueberry farm in South Africa. The long-term
goal is a commercial product sold to other farms covering fuel, chemicals,
equipment maintenance, labour, and more.

## Why

There is a gap in agriculture analytics. Farms capture significant data (now
increasingly via Google Forms) but lack tools to turn it into actionable
insights. The current workflow is: capture data -> export to Excel -> manually
analyse -> manually report. This is slow, error-prone, and doesn't scale.

Dad's farm is the first customer and case study.

## Who

- **End user:** Production and development manager (farm-level decision maker)
- **Secondary users:** Farm owner/directors, accountants (report consumers)

## Core Principle

> "If you make the user do more work to get the data in, the project will fail."

The system must ingest data with **zero friction**. Since the farm already
captures data via Google Forms (which flow into Google Sheets), the primary
ingestion path is the Google Sheets API — the data is already there, we just
need to pull it.

## Scope

### POC (Phase 1) — Fuel Only
- Ingest fuel data from Google Sheets (Forms responses) and FarmTrace exports
- Normalize equipment names to a master list
- Dashboard: consumption by equipment, by block, over time
- Anomaly flagging (unusual consumption spikes)
- Cost per hectare per block (if block-level data available)

### Phase 2 — Multi-Input Cost
- Add chemicals, labour, water to the cost model
- Geospatial heatmap of the farm
- Automated weekly PDF reports via email
- Predictive maintenance signals (fuel efficiency degradation)

### Phase 3 — Commercial Product
- Multi-tenant SaaS (sell to other farms)
- Real-time equipment issue logging module
- API integrations (FarmTrace, accounting systems)
- Sustainability/traceability exports for EU/UK retailers
- Mobile app

## Key Metric

Total Landed Cost per hectare:

    TC_L(h) = Fuel_h + Labor_h + Chem_h + Water_h

For the POC, we focus on the Fuel_h component only.

## Project Structure

```
agri_view/
  docs/               # Project documentation
    PROJECT_BRIEF.md   # This file
    DISCOVERY.md       # Interview questions for discovery session
    ARCHITECTURE.md    # Technical architecture plan
    DATA_CHECKLIST.md  # What to collect from the session
  data/
    raw/               # Raw exports, logbooks, invoices (gitignored)
    processed/         # Cleaned, normalized data
  src/                 # Application source code
  notebooks/           # Exploratory data analysis
```

## Status

**Phase:** Pre-discovery — preparing for initial data gathering session.
