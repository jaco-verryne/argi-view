# Discovery Session - Question Guide

Use this during your conversation with Dad. Don't try to ask every question
rigidly — follow the conversation. But make sure you cover **Sections A, F,
and G** at minimum. Those are non-negotiable.

Screen-record the session if he's comfortable with it. Seeing his actual
screens and files is worth 10x more than verbal answers.

---

## A. The Data Landscape (What exists today?)

These are the most important questions. The entire POC depends on the answers.

**A1. "Can you walk me through exactly how you track fuel right now, step by step?"**

Don't assume anything. Where does data get entered? FarmTrace? A Google Form?
A notebook? Fuel slips? Watch him do it if possible.

> *What this unlocks:* The real ingestion pipeline — not what we imagine, but
> what actually exists.

**A2. "Can you show me the Google Forms you use and the Sheets they feed into?"**

This is critical. For each relevant form:
- Open the linked Google Sheet and look at the column headers
- Note the Sheet URL / ID (you'll need this for the API)
- How far back does the data go?
- How many rows? (gives you a sense of volume)
- Is there a fuel-specific form, or is fuel captured in a general form?
- Who fills it in? The operator? A fuel attendant? A foreman?

> *What this unlocks:* The Google Sheets column names ARE your raw data model.
> This is the single most important thing to see.

**A3. "Can you also show me a FarmTrace export?"**

Get a real export file too, since FarmTrace may have historical data that
predates the Google Forms migration.
- What format? CSV? Excel? PDF?
- What columns exist?
- How far back does the history go?
- Is there overlap with the Google Forms data?

> *What this unlocks:* Whether you need two ingestion paths or can ignore
> FarmTrace for the POC.

**A4. "What other systems or documents have fuel data?"**

Probe for:
- Fuel supplier invoices (Engen, Shell, BP — whoever delivers to the farm)
- Fuel bowser logbooks (still handwritten, or replaced by the Google Form?)
- Monthly management reports he already produces
- Fleet management systems (if any)
- Accounting software (Sage, Xero, Pastel — SA farms often use these)

> *What this unlocks:* Secondary data sources for reconciliation and gap-filling.

**A5. "How often does fuel data get captured? Every fill-up? Daily summary? Weekly?"**

> *What this unlocks:* Dashboard refresh frequency. If data arrives monthly,
> a real-time dashboard is misleading.

**A6. "Can you give me 3-6 months of actual historical data to work with?"**

You need real data, not synthetic. The messier the better — it teaches you
what the cleaning pipeline must handle.

> *What this unlocks:* The actual POC dataset.

---

## B. The Fleet (What consumes fuel?)

**B1. "Can you list every piece of equipment that uses fuel?"**

Get the full inventory:
- Tractors (how many? what models?)
- Bakkies / light vehicles
- Trucks
- Generators
- Irrigation pumps
- Sprayers
- Forklifts
- Anything else

> *What this unlocks:* The equipment dimension of the data model.

**B2. "How do you refer to each piece of equipment internally?"**

This is critical for Master Data Management. Does he say "Tractor 1", "T1",
"the blue John Deere", "JD 5075E #3"? Do different people call the same
machine different things?

> *What this unlocks:* The entity resolution rules. If data says "T1" in one
> place and "Tractor 01" in another, we need a mapping table.

**B3. "Is there a fleet register or asset list somewhere — even an old spreadsheet?"**

You need a canonical equipment master list.

> *What this unlocks:* The equipment master table.

**B4. "Do different machines use different fuel types?"**

Diesel for tractors/trucks, petrol for bakkies, possibly other types.

> *What this unlocks:* Fuel type as a data dimension. Different prices per litre.

**B5. "Do you have hour meters or odometer readings for any equipment?"**

Hour meters on tractors + fuel consumption = litres/hour = efficiency metric.
This is gold if available.

> *What this unlocks:* Efficiency tracking and predictive maintenance signals.

---

## C. Fuel Flow (How does fuel physically move on the farm?)

**C1. "Where does fuel come from? Bulk delivery to a farm tank, or do vehicles fill up at a station?"**

Most large SA farms have one or more bulk fuel tanks (bowsers). Understanding
the physical flow tells you where measurement points exist.

> *What this unlocks:* The fuel reconciliation model (purchased vs dispensed).

**C2. "Is there a bowser system with a meter/pump? Does someone log each fill-up?"**

If there's a metered pump with a logbook, that logbook is your primary source.
What gets recorded?
- Date?
- Equipment name/ID?
- Operator name?
- Litres dispensed?
- Meter reading?

> *What this unlocks:* The granularity of the fuel transaction data.

**C3. "How do you reconcile fuel? Do you compare what was delivered vs what was dispensed?"**

> *What this unlocks:* Whether fuel accountability already exists or if it's
> just "we bought X litres this month."

**C4. "Has fuel theft ever been a concern?"**

If yes, anomaly detection immediately becomes a high-value feature.

> *What this unlocks:* Feature priority. Theft detection = instant ROI.

---

## D. Spatial Structure (The Block Map)

**D1. "How is the farm divided? What are the blocks/orchards/sections called?"**

Get the naming convention. Block A1, Block B3, "The hill block," etc.

> *What this unlocks:* The spatial dimension of the data model.

**D2. "How many hectares is each block? Is there a farm map?"**

You need a block register with areas (hectares). If he has a GIS/shape file
or even a Google Earth screenshot, take it.

> *What this unlocks:* The denominator for "cost per hectare" calculations.

**D3. "When a tractor works in a block, is that recorded anywhere?"**

This is the critical link between fuel and spatial attribution. If it's not
recorded, you'll have to estimate based on activity type + duration.

> *What this unlocks:* Whether block-level fuel attribution is possible or
> requires estimation.

**D4. "Are work activities logged? Spraying, mowing, harvesting — do you know which machine did what, where, and for how long?"**

FarmTrace may capture this. This is what lets you say "Block A3 cost R4,200
in fuel this month."

> *What this unlocks:* The activity-to-block-to-fuel attribution chain.

---

## E. The Yield Side (Connecting cost to output)

**E1. "Do you track yield per block? Kg of blueberries harvested per block per season?"**

Without yield data, you can't calculate cost-per-kg. With it, you unlock the
metric that actually matters: input cost per kg of output per block.

> *What this unlocks:* The output side of the profitability equation.

**E2. "What's a 'good' yield for a block? What's the benchmark?"**

You need to know what "normal" looks like to flag anomalies.

> *What this unlocks:* Threshold values for alerting.

---

## F. The Decisions (What does he actually need to know?)

These determine what goes on the dashboard. Do not skip this section.

**F1. "If I could put three numbers in front of you every Monday morning, what would they be?"**

His answer is your dashboard's homepage.

> *What this unlocks:* The primary KPIs.

**F2. "Where do you think you're losing money on fuel right now, but can't prove it?"**

Suspicions are features waiting to be validated.

> *What this unlocks:* High-value analytics that prove the system's worth.

**F3. "What report takes you the longest to produce? Can you show me one?"**

If you can auto-generate that report, you've already proven value.

> *What this unlocks:* The "quick win" — the first thing the POC should replace.

**F4. "Who else sees your reports? Directors? The farm owner? Accountants?"**

> *What this unlocks:* User roles and what level of detail each audience needs.

**F5. "What decisions would you make differently if you had better fuel data?"**

Examples to prompt him:
- Replace an inefficient tractor?
- Reallocate equipment between blocks?
- Change service intervals?
- Budget more accurately?
- Hold a fuel attendant accountable?

> *What this unlocks:* The business value story.

---

## G. The Constraints (What can kill this project?)

**G1. "How much time per week can you realistically spend on this system?"**

If the answer is "zero," ingestion must be fully automated.
If "30 minutes," you have some room.

> *What this unlocks:* The friction budget for data ingestion.

**G2. "Is there anyone else who enters data? Workshop manager, fuel attendant, foreman?"**

> *What this unlocks:* Multiple data entry points = multiple data quality risks.

**G3. "Does the farm have decent internet/WiFi connectivity?"**

SA farms can have spotty connectivity. This affects whether you build
cloud-first or need offline capability.

> *What this unlocks:* Hosting and deployment strategy.

**G4. "Are there any compliance or reporting requirements for fuel? Carbon tax? BEE reporting?"**

If yes, the system has regulatory value beyond operational analytics.

> *What this unlocks:* Additional value propositions and potential report formats.

**G5. "What's the fuel budget for the farm per month/year? Ballpark."**

This frames the potential savings. If fuel is R200k/month and you can find 5%
waste, that's R10k/month — the system pays for itself.

> *What this unlocks:* The ROI story.

---

## Session Close

Before wrapping up:

1. Confirm you have the data files (see DATA_CHECKLIST.md)
2. Ask: "Is there anything about fuel on this farm that I haven't asked about?"
3. Ask: "Who else should I talk to? The workshop manager? The fuel attendant?"
4. Set expectations: "I'll have something to show you in 2-3 weeks."
