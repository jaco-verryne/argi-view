# Deploying to Streamlit Community Cloud

Free, always-on hosting. Dad gets a permanent link.

## Prerequisites

- A GitHub account (yours — the code repo)
- A Google account (yours — for the service account)

## Step 1: Create the Google Sheet (2 min)

1. Go to [Google Sheets](https://sheets.google.com) and create a new blank sheet
2. Name it "AgriView Discovery Responses"
3. Copy the **spreadsheet ID** from the URL:
   ```
   https://docs.google.com/spreadsheets/d/THIS_PART_IS_THE_ID/edit
   ```
4. Keep this tab open — you'll share it with the service account in Step 3

## Step 2: Create a Google Service Account (5 min)

This lets the app read/write the Sheet without your personal login.

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project (or use an existing one). Name it "agriview"
3. Enable the **Google Sheets API**:
   - Go to APIs & Services > Library
   - Search "Google Sheets API"
   - Click Enable
4. Enable the **Google Drive API** (same process)
5. Create a service account:
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "Service Account"
   - Name it "agriview-sheets"
   - Skip the optional steps, click Done
6. Create a key for the service account:
   - Click on the service account you just created
   - Go to the "Keys" tab
   - Click "Add Key" > "Create new key" > JSON
   - A JSON file will download — **keep this safe, you'll need it**
7. Copy the service account email (looks like `agriview-sheets@yourproject.iam.gserviceaccount.com`)

## Step 3: Share the Sheet with the Service Account (1 min)

1. Go back to the Google Sheet you created in Step 1
2. Click "Share"
3. Paste the service account email from Step 2
4. Give it **Editor** access
5. Uncheck "Notify people" and click Share

## Step 4: Push to GitHub (2 min)

```bash
cd /path/to/agri_view

git init
git add .
git commit -m "Initial commit: discovery questionnaire"
git remote add origin https://github.com/YOUR_USERNAME/agri-view.git
git push -u origin main
```

The repo can be private — Streamlit Community Cloud supports private repos.

## Step 5: Deploy on Streamlit Community Cloud (3 min)

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repo, branch `main`, and set the main file path to:
   ```
   src/questionnaire.py
   ```
5. Click "Deploy"

## Step 6: Add Secrets (2 min)

This is how the app gets the Google credentials without them being in the code.

1. In Streamlit Community Cloud, go to your app's settings
2. Click "Secrets"
3. Paste the following, replacing the values with your actual credentials:

```toml
spreadsheet_id = "YOUR_SPREADSHEET_ID_FROM_STEP_1"

[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "key-id-from-json"
private_key = "-----BEGIN PRIVATE KEY-----\nYOUR_KEY_HERE\n-----END PRIVATE KEY-----\n"
client_email = "agriview-sheets@yourproject.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/agriview-sheets%40yourproject.iam.gserviceaccount.com"
```

The values come directly from the JSON file you downloaded in Step 2.
Copy each field from the JSON into the TOML format above.

4. Click "Save". The app will restart automatically.

## Step 7: Test & Share

1. Open the app URL (something like `https://your-app.streamlit.app`)
2. Fill in a test answer and click "Save Progress"
3. Check the Google Sheet — you should see the response appear in row 2
4. WhatsApp the link to Dad

## Local Development

To run locally with Google Sheets persistence, create a secrets file:

```bash
mkdir -p .streamlit
```

Create `.streamlit/secrets.toml` with the same content as Step 6.
This file is gitignored by default.

Then run:
```bash
streamlit run src/questionnaire.py
```

Without secrets configured, the app still works but responses are only
stored in the browser session (lost on page refresh).

## Troubleshooting

**"Could not load from Google Sheets"**
- Check that the Sheet is shared with the service account email
- Check that the spreadsheet_id in secrets matches the Sheet URL
- Check that Google Sheets API and Google Drive API are both enabled

**App shows "local mode" warning**
- Secrets aren't configured. Follow Step 6.

**Responses not saving**
- Check the Google Sheet for a tab called "responses"
- Check the Streamlit Cloud logs for error messages
