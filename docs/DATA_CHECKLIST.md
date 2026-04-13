# Data Collection Checklist

Walk away from the discovery session with as many of these as possible.
Save everything into `data/raw/`.

## Must Have (don't leave without these)

- [ ] **Google Sheets URLs/IDs** — for every form that captures fuel data
      - Open each linked Sheet, screenshot or note the column headers
      - Note who has access (you'll need read access for the API)
      - Check how far back the data goes and how many rows exist
- [ ] **Google Sheet export** — download each relevant Sheet as CSV
      - This is your working dataset until the API is wired up
      - Ideally 3-6 months of history
- [ ] **Equipment list** — every machine that uses fuel, with the names/IDs
      used in the Google Forms and in conversation
      - Even a handwritten list or a photo of a whiteboard works
- [ ] **One completed report** — a real management report he's produced manually
      - This is your "automate this first" target
- [ ] **His "three Monday morning numbers"** — write these down verbatim

## Should Have

- [ ] **FarmTrace export** — at least one export file (CSV/Excel)
      - Note whether this overlaps with or replaces the Google Forms data
      - Note the export steps so you can repeat it
- [ ] **Block/orchard map** — how the farm is divided, with hectares per block
      - A photo of a printed map, a Google Earth screenshot, or a spreadsheet
- [ ] **Fuel bowser logbook** — is this now the Google Form, or still separate?
      - If separate: photos of a few pages, note the fields captured per fill-up
- [ ] **Supplier invoice** — a sample fuel delivery invoice
      - Shows bulk purchase quantities, prices, delivery dates
- [ ] **Yield data** — kg harvested per block per season (even one season)

## Nice to Have

- [ ] **Accounting export** — fuel costs from their accounting software
      - Good for cross-referencing against operational data
- [ ] **Hour meter readings** — if they track tractor hours, get any records
- [ ] **Farm shape files / GIS data** — if they exist
- [ ] **Photos of the fuel bowser setup** — helps understand the physical flow
- [ ] **List of all Google Forms in use** — not just fuel, all of them
      - Gives you a map of what other modules (chemicals, issues, etc.) could
        plug into later

## Technical Notes to Capture

- [ ] Google account that owns the Forms/Sheets (you'll need API access)
- [ ] FarmTrace login URL and how exports work
- [ ] Accounting software name and version
- [ ] Internet connectivity quality on the farm
- [ ] What devices he uses day-to-day (phone, tablet, laptop?)
- [ ] What Google Workspace plan (free Gmail or paid Workspace?)
- [ ] Any existing shared drives, Dropbox, Google Drive folders

## After the Session

1. Copy all collected files into `data/raw/`
2. Open each file and note the columns, formats, and quality
3. Write quick notes on anything surprising or different from expectations
4. Identify the biggest data gaps (things you expected but don't exist)
5. Try to get read access to the Google Sheets (shared with your Google account
   or a service account) — test that you can pull data via the API
