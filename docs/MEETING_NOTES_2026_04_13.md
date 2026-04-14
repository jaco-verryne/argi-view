# Meeting Notes — 13 April 2026

Source: `data/raw/silo_data_meeting.txt` (Whisper translation from Afrikaans)

---

## The Real Problem (Dad's words)

> "There is no tool that brings the data together. Even within a department...
> But there is not something that goes beyond the spectrum."

> "What did my GMI application cost me? It was the chemical used. It's the
> tractor driver's hours. It's the diesel of the tractor as well. So that's
> what it cost me. But that's not something that all three of them connect."

> "That's the difficult part — how to get the silo's data to work together."

**Translation:** FarmTrace captures everything perfectly, but each module is
a silo. Dad wants a unified view that crosses all modules to answer:
"For Block X on Day Y, what was the total cost and where did it come from?"

---

## What FarmTrace Actually Has (Modules)

| Module | What it captures | Granularity |
|--------|-----------------|-------------|
| **HR / Labour** | Staff by phase/section, check-ins, absences, tasks, hours, job costing, timesheets, payroll | Per person, per task, per phase, per day |
| **Harvesting** | Piecework, lug/crate movements, kg picked, box weights | Per block, per variety, per phase, per day |
| **Stock Management** | Goods received (GRV), adjustments, movements (usage), bookouts | Per product, per block, per instruction, per day |
| **Tasking** | Chemical mixing instructions, block task products | Per instruction, per block |
| **Scouting** | Pest monitoring, grid scouting, observations | Per block, with parameters/norms |
| **Water Monitoring** | Daily water quality (EC, pH, volume) | Per day |
| **Fruit & Flower Counting** | Seasonal development tracking | Periodic |
| **Refueling** | Fuel transactions, logbook entries | Per vehicle, per day, with pump readings |

**Data volume:** ~500,000 lines for 10 days of stock movements alone. ~1,300
lines per day for stock movements. The data is VERY granular.

---

## Farm Structure

- **Phases:** 1, 2, 3, 4 (major farm divisions)
- **Blocks:** 28+ blocks nested within phases
- **Block setup data available:** block number, variety, hectares, plant count
- **Cost categories:** Labour, Chemicals (GMI), Diesel, Nursery, Toiletries,
  Workshop, Hardware

---

## What Dad Wants to See

### The Eagle View
- For any day/week/month: total operating cost per block
- Breakdown by category: what portion is labour, diesel, chemicals, etc.
- Aggregated by phase or drilled down to individual blocks

### Specific Questions He Wants Answered
1. "Phase three today cost 48,000 rands, phase two only 20,000 — why?"
2. "Why is 600 litres of diesel used in this phase today and not in phase two?"
3. "Is 50 litres of diesel enough for a day for a phase? If only 50, flag it —
   someone might be stealing diesel"
4. "We bought 18,000 [units] of a chemical but only used 4,000 — why didn't
   we just buy 5,000 and reorder next month?"
5. "Our labour costs half a million per month for specific management —
   can we maintain the same standard for less?"
6. "Kilograms per hectare — what is the yield relative to our input costs?"
7. "Do we use what we buy? Do we buy more than we use?"

### Budget vs Actual
- Monthly budget per category
- Flags when actual exceeds budget
- Cash flow projection adjustments when costs deviate

### Anomaly Flags
- Unexpected fuel usage (theft detection)
- Purchase/usage mismatches
- Cost spikes per block

---

## What Dad Is Currently Doing (The Workaround)

1. Export each module from FarmTrace separately
2. Pull data into a single Excel workbook
3. Build a query table to combine everything
4. Create pivot tables to visualize
5. Limited to **monthly summaries** because daily filtering is too tedious

He WANTS daily-level views but can't get there with manual Excel work.

> "I just chose a month and made the summary on a month... it's not what I
> want to see. But it's good that we have a lot of data."

---

## Data Delivery Plan (Agreed)

- Dad will export FarmTrace data and upload to a **shared Google Drive**
- Files will be labeled per category (diesel, labour, chemicals, etc.)
- Starting with **2-3 days of data** across multiple categories
- Each file will have specific timestamps for cross-referencing

### Key exports to expect:
1. **Block setup** — block number, variety, hectares, plant count
2. **Labour/tasks** — date, phase, task, hours, cost
3. **Fuel transactions** — date, phase, vehicle, pump readings, litres, hours, odometer
4. **Stock movements** — date, product, block, quantity, category (GMI/workshop/etc.)
5. **Products master** — unit costs, package sizes, price per unit, category

### Cross-referencing key:
- **Date + Phase/Block** links all tables
- **Timestamp** links fuel transactions to stock movements
- Fuel transactions have vehicle IDs that appear in logbook entries

---

## Revised Scope

The POC is NOT just fuel. It's the **unified cost view** that dad is already
trying to build manually. The fuel-only scope was our initial assumption;
the real need is:

**One table, all costs, per block, per day.**

This is actually simpler in concept (just aggregate) but broader in data
(multiple FarmTrace modules). The dashboard should show:

1. **Daily cost heatmap** — blocks coloured by total cost
2. **Cost breakdown** — drill into any block to see labour vs diesel vs
   chemicals vs stock
3. **Budget tracker** — monthly budget vs actual per category
4. **Anomaly flags** — spikes, purchase/usage gaps, fuel theft signals
5. **Yield efficiency** — kg per hectare vs cost per hectare

---

## Next Steps

1. Wait for dad to upload FarmTrace exports to Google Drive
2. Examine the actual file formats and column names
3. Build the data model based on real columns (not assumptions)
4. Create the unified fact table
5. Build the dashboard
