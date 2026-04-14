"""
AgriView Discovery Questionnaire

A Streamlit form for the production manager to fill out at his own pace.
Captures structured responses for the fuel consumption analytics POC.

Persistence: Google Sheets (for Streamlit Community Cloud deployment).
Falls back to local JSON if Google Sheets credentials aren't configured.

Run locally:  streamlit run src/questionnaire.py
Deploy:       See docs/DEPLOY.md
"""

import json
import streamlit as st
from datetime import datetime

# ── Persistence layer ──────────────────────────────────────────────────

# All question keys in display order — used for Sheet column headers
QUESTION_KEYS = [
    "farm_name",
    "your_role",
    "farm_size_hectares",
    "num_blocks",
    "block_names",
    "equipment_list",
    "fuel_types",
    "fuel_types_other",
    "fuel_source",
    "bowser_details",
    "fuel_budget",
    "fuel_theft_concern",
    "hour_meters",
    "fuel_tracking_method",
    "fuel_tracking_other",
    "who_captures_fuel",
    "capture_frequency",
    "google_forms_list",
    "farmtrace_usage",
    "data_history",
    "activity_tracking",
    "yield_per_block",
    "monday_numbers",
    "losing_money",
    "longest_report",
    "better_data_decisions",
    "time_for_system",
    "other_data_people",
    "internet_quality",
    "device",
    "compliance",
    "compliance_details",
    "anything_else",
    "who_else_to_talk_to",
    "_submitted",
    "_last_updated",
]


def _sheets_available() -> bool:
    """Check if Google Sheets credentials are configured."""
    try:
        return "gcp_service_account" in st.secrets
    except Exception:
        return False


def _get_worksheet():
    """Connect to Google Sheets and return the worksheet."""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes,
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["spreadsheet_id"])
    try:
        worksheet = sheet.worksheet("responses")
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet("responses", rows=3, cols=len(QUESTION_KEYS))
        worksheet.update("A1", [QUESTION_KEYS])
    return worksheet


def _serialize(value) -> str:
    """Convert a value to a string for Sheet storage."""
    if isinstance(value, list):
        return json.dumps(value)
    if isinstance(value, bool):
        return json.dumps(value)
    if value is None:
        return ""
    return str(value)


def _deserialize(raw: str, key: str):
    """Convert a Sheet string back to the appropriate Python type."""
    if not raw:
        return "" if key not in _LIST_KEYS else []
    if key in _LIST_KEYS:
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    if key == "_submitted":
        return raw.lower() == "true"
    return raw


# Keys that hold list values (multiselect)
_LIST_KEYS = {"fuel_types", "fuel_tracking_method", "device"}


def load_responses() -> dict:
    """Load saved responses from Google Sheets or session state."""
    if _sheets_available():
        try:
            ws = _get_worksheet()
            headers = ws.row_values(1)
            try:
                values = ws.row_values(2)
            except Exception:
                values = []
            # Pad values to match headers length
            values.extend([""] * (len(headers) - len(values)))
            return {h: _deserialize(v, h) for h, v in zip(headers, values) if h in QUESTION_KEYS}
        except Exception as e:
            st.warning(f"Could not load from Google Sheets: {e}")
            return {}
    return st.session_state.get("_responses", {})


def save_responses(responses: dict):
    """Save responses to Google Sheets (or session state as fallback)."""
    responses["_last_updated"] = datetime.now().isoformat()

    if _sheets_available():
        try:
            ws = _get_worksheet()
            headers = ws.row_values(1)
            if not headers:
                headers = QUESTION_KEYS
                ws.update("A1", [headers])

            row = [_serialize(responses.get(key, "")) for key in headers]
            ws.update("A2", [row])
            return True
        except Exception as e:
            st.error(f"Could not save to Google Sheets: {e}")
            return False
    else:
        st.session_state["_responses"] = responses
        return True


# ── Helper ─────────────────────────────────────────────────────────────


def get(saved: dict, key: str, default=""):
    """Get a saved response or return the default."""
    val = saved.get(key, default)
    if val == "" and default != "":
        return default
    return val


def radio_index(options: list, saved_value: str, default: str) -> int:
    """Get the index for a radio button, handling missing values."""
    value = saved_value if saved_value else default
    try:
        return options.index(value)
    except ValueError:
        return 0


# ── Main app ───────────────────────────────────────────────────────────


def main():
    st.set_page_config(
        page_title="AgriView - Farm Discovery",
        page_icon=":seedling:",
        layout="centered",
    )

    st.title("AgriView - Farm Discovery")
    st.markdown(
        "Hey Dad! Fill this out whenever you have a chance — no rush. "
        "It helps me understand the fuel situation on the farm so I can "
        "build something useful. Your progress saves automatically."
    )

    if not _sheets_available():
        st.info(
            "Running in local mode — responses are stored in your browser "
            "session only. For persistent storage, configure Google Sheets "
            "(see docs/DEPLOY.md)."
        )

    st.markdown("---")

    saved = load_responses()
    responses = {}

    # ── Section 1: The Basics ──────────────────────────────────────────

    st.header("1. The Basics")

    responses["farm_name"] = st.text_input(
        "What's the farm called?",
        value=get(saved, "farm_name"),
        placeholder="e.g. Southfield Blueberries",
    )

    responses["your_role"] = st.text_input(
        "What's your official role/title?",
        value=get(saved, "your_role"),
        placeholder="e.g. Production and Development Manager",
    )

    responses["farm_size_hectares"] = st.text_input(
        "Roughly how big is the farm? (hectares under production)",
        value=get(saved, "farm_size_hectares"),
        placeholder="e.g. 120 hectares",
    )

    responses["num_blocks"] = st.text_input(
        "How many blocks/orchards/sections does the farm have?",
        value=get(saved, "num_blocks"),
        placeholder="e.g. 24 blocks",
    )

    responses["block_names"] = st.text_area(
        "Can you list the block names? (however you refer to them internally)",
        value=get(saved, "block_names"),
        placeholder="e.g. A1, A2, B1, B2, Hill Block, Dam Block...",
        height=100,
    )

    # ── Section 2: Equipment & Fuel ────────────────────────────────────

    st.header("2. Equipment & Fuel")

    st.markdown("I need to understand every piece of equipment that uses fuel " "on the farm.")

    responses["equipment_list"] = st.text_area(
        "List all equipment that uses fuel (tractors, bakkies, trucks, "
        "generators, pumps, forklifts — everything)",
        value=get(saved, "equipment_list"),
        placeholder=(
            "e.g.\n"
            "- John Deere 5075E tractor (we call it T1)\n"
            "- John Deere 5075E tractor (T2)\n"
            "- Toyota Hilux bakkie (white one)\n"
            "- Diesel generator at the pack shed\n"
            "- ..."
        ),
        height=200,
    )

    fuel_type_options = [
        "Diesel",
        "Petrol (Unleaded)",
        "Petrol (Leaded)",
        "LPG",
        "Other",
    ]
    responses["fuel_types"] = st.multiselect(
        "What fuel types are used on the farm?",
        options=fuel_type_options,
        default=get(saved, "fuel_types", []),
    )

    if "Other" in responses["fuel_types"]:
        responses["fuel_types_other"] = st.text_input(
            "What other fuel types?",
            value=get(saved, "fuel_types_other"),
        )

    fuel_source_options = [
        "Bulk delivery to a farm tank/bowser",
        "Vehicles fill up at a petrol station",
        "Both — bulk tank on farm AND some vehicles fill at a station",
        "Other / not sure",
    ]
    responses["fuel_source"] = st.radio(
        "Where does the fuel come from?",
        options=fuel_source_options,
        index=radio_index(
            fuel_source_options, get(saved, "fuel_source"), "Bulk delivery to a farm tank/bowser"
        ),
    )

    responses["bowser_details"] = st.text_area(
        "If there's a bulk tank/bowser on the farm — is there a meter/pump? "
        "Does someone log each fill-up? What gets recorded?",
        value=get(saved, "bowser_details"),
        placeholder=(
            "e.g. Yes, we have a 5000L diesel tank with a meter pump. "
            "The driver fills in a Google Form with the date, machine name, "
            "and litres. The meter reading isn't always recorded..."
        ),
        height=120,
    )

    responses["fuel_budget"] = st.text_input(
        "Roughly what's the monthly fuel spend? (ballpark in Rands is fine)",
        value=get(saved, "fuel_budget"),
        placeholder="e.g. R80,000 - R120,000 per month",
    )

    theft_options = [
        "Yes, it's a known issue",
        "Suspected but can't prove it",
        "No, not really",
        "Not sure",
    ]
    responses["fuel_theft_concern"] = st.radio(
        "Has fuel theft or unexplained fuel loss ever been a concern?",
        options=theft_options,
        index=radio_index(theft_options, get(saved, "fuel_theft_concern"), "Not sure"),
    )

    hour_meter_options = [
        "Yes, we track hours for most machines",
        "Yes, but only for some machines",
        "The machines have hour meters but we don't record them",
        "No hour meters",
        "Not sure",
    ]
    responses["hour_meters"] = st.radio(
        "Do any of the tractors/machines have hour meters that get recorded?",
        options=hour_meter_options,
        index=radio_index(hour_meter_options, get(saved, "hour_meters"), "Not sure"),
    )

    # ── Section 3: How Data Gets Captured ──────────────────────────────

    st.header("3. How Data Gets Captured Today")

    tracking_options = [
        "Google Form filled in at each fill-up",
        "Written in a logbook at the fuel tank",
        "Logged in FarmTrace",
        "Recorded in a spreadsheet (Excel/Google Sheets)",
        "Fuel slips / receipts collected",
        "Not really tracked per machine — just total monthly purchase",
        "Other",
    ]
    responses["fuel_tracking_method"] = st.multiselect(
        "How is fuel usage currently tracked? (select all that apply)",
        options=tracking_options,
        default=get(saved, "fuel_tracking_method", []),
    )

    if "Other" in responses["fuel_tracking_method"]:
        responses["fuel_tracking_other"] = st.text_input(
            "How else is fuel tracked?",
            value=get(saved, "fuel_tracking_other"),
        )

    responses["who_captures_fuel"] = st.text_input(
        "Who fills in the fuel data? (the driver? a fuel attendant? a foreman?)",
        value=get(saved, "who_captures_fuel"),
        placeholder="e.g. The driver fills in the Google Form on his phone",
    )

    freq_options = [
        "Every single fill-up (real-time)",
        "End of each day",
        "Weekly",
        "Monthly",
        "When someone remembers",
    ]
    responses["capture_frequency"] = st.radio(
        "How often does fuel data get captured?",
        options=freq_options,
        index=radio_index(
            freq_options, get(saved, "capture_frequency"), "Every single fill-up (real-time)"
        ),
    )

    responses["google_forms_list"] = st.text_area(
        "Can you list all the Google Forms currently used on the farm? "
        "(not just fuel — everything: spraying logs, issue reports, etc.)",
        value=get(saved, "google_forms_list"),
        placeholder=(
            "e.g.\n"
            "- Fuel log form\n"
            "- Spray record form\n"
            "- Tractor issue report form\n"
            "- Daily activity log\n"
            "- ..."
        ),
        height=150,
    )

    responses["farmtrace_usage"] = st.text_area(
        "What do you use FarmTrace for? What data goes in there " "vs what goes in Google Forms?",
        value=get(saved, "farmtrace_usage"),
        placeholder=(
            "e.g. FarmTrace is mainly for spray records and compliance. "
            "Fuel is tracked in Google Forms. Activity logs are in both..."
        ),
        height=120,
    )

    history_options = [
        "Less than 3 months",
        "3-6 months",
        "6-12 months",
        "1-2 years",
        "More than 2 years",
        "Not sure",
    ]
    responses["data_history"] = st.radio(
        "How far back does your fuel data go? (in any system — forms, "
        "FarmTrace, spreadsheets, logbooks)",
        options=history_options,
        index=radio_index(history_options, get(saved, "data_history"), "Not sure"),
    )

    # ── Section 4: Activities & Blocks ─────────────────────────────────

    st.header("4. Linking Fuel to Blocks")

    st.markdown(
        "To figure out which blocks cost the most to maintain, I need to "
        "know whether we can link equipment activity to specific blocks."
    )

    activity_options = [
        "Yes — in a Google Form or FarmTrace with the block name",
        "Sometimes — depends on the activity",
        "No — we know roughly but it's not recorded",
        "Not sure",
    ]
    responses["activity_tracking"] = st.radio(
        "When a tractor works in a specific block (e.g. mowing Block A3), "
        "is that recorded anywhere?",
        options=activity_options,
        index=radio_index(activity_options, get(saved, "activity_tracking"), "Not sure"),
    )

    yield_options = [
        "Yes — per block per pick/harvest",
        "Yes — but only totals per block per season",
        "Only total farm yield, not per block",
        "Not sure",
    ]
    responses["yield_per_block"] = st.radio(
        "Do you track yield (kg harvested) per block?",
        options=yield_options,
        index=radio_index(yield_options, get(saved, "yield_per_block"), "Not sure"),
    )

    # ── Section 5: What Matters Most ───────────────────────────────────

    st.header("5. What You Actually Need")

    st.markdown(
        "**This is the most important section.** Your answers here decide "
        "what the dashboard shows."
    )

    responses["monday_numbers"] = st.text_area(
        "If I could put 3 numbers in front of you every Monday morning, " "what would they be?",
        value=get(saved, "monday_numbers"),
        placeholder=(
            "e.g.\n"
            "- Total litres used this week vs last week\n"
            "- Which machine used the most fuel\n"
            "- Are we over or under budget for the month\n"
        ),
        height=120,
    )

    responses["losing_money"] = st.text_area(
        "Where do you THINK you're losing money on fuel, but can't prove it?",
        value=get(saved, "losing_money"),
        placeholder=(
            "e.g. I think Tractor 3 is using way more diesel than it should. "
            "Or: I suspect the generator runs longer than necessary on weekends..."
        ),
        height=120,
    )

    responses["longest_report"] = st.text_area(
        "What fuel-related report takes you the longest to produce? "
        "What's in it and who sees it?",
        value=get(saved, "longest_report"),
        placeholder=(
            "e.g. Monthly fuel cost summary for the directors. "
            "I download from Google Sheets, split by machine type in Excel, "
            "calculate cost per hectare manually, takes about 2 hours..."
        ),
        height=120,
    )

    responses["better_data_decisions"] = st.text_area(
        "What decisions would you make differently if you had better "
        "fuel data? (pick one or two)",
        value=get(saved, "better_data_decisions"),
        placeholder=(
            "e.g.\n"
            "- I'd know when to service a tractor before it breaks down\n"
            "- I could justify replacing the old Ford truck\n"
            "- I could hold the fuel attendant accountable for losses\n"
            "- I could budget more accurately for next season\n"
        ),
        height=120,
    )

    # ── Section 6: Practical Stuff ─────────────────────────────────────

    st.header("6. Practical Stuff")

    time_options = [
        "Zero — it must just work on its own",
        "5-10 minutes to check a dashboard",
        "30 minutes to review and maybe adjust settings",
        "An hour or more",
    ]
    responses["time_for_system"] = st.radio(
        "How much time per week can you realistically spend on a new system?",
        options=time_options,
        index=radio_index(
            time_options, get(saved, "time_for_system"), "5-10 minutes to check a dashboard"
        ),
    )

    responses["other_data_people"] = st.text_input(
        "Who else enters data on the farm? (workshop manager, fuel attendant, "
        "foremen — and what do they capture?)",
        value=get(saved, "other_data_people"),
    )

    internet_options = [
        "Good — reliable fibre or fast wireless",
        "OK — works most of the time, sometimes slow",
        "Patchy — drops out regularly",
        "Basically no internet in the field, only at the office",
    ]
    responses["internet_quality"] = st.radio(
        "How's the internet/WiFi on the farm?",
        options=internet_options,
        index=radio_index(
            internet_options,
            get(saved, "internet_quality"),
            "OK — works most of the time, sometimes slow",
        ),
    )

    device_options = [
        "Phone (Android)",
        "Phone (iPhone)",
        "Tablet",
        "Laptop",
        "Desktop PC",
    ]
    responses["device"] = st.multiselect(
        "What devices do you use day-to-day?",
        options=device_options,
        default=get(saved, "device", []),
    )

    compliance_options = ["Yes", "No", "Not sure"]
    responses["compliance"] = st.radio(
        "Are there any compliance or reporting requirements related to fuel? "
        "(carbon tax, BEE reporting, sustainability certifications, etc.)",
        options=compliance_options,
        index=radio_index(compliance_options, get(saved, "compliance"), "Not sure"),
    )

    if responses["compliance"] == "Yes":
        responses["compliance_details"] = st.text_area(
            "What compliance/reporting is required?",
            value=get(saved, "compliance_details"),
            height=80,
        )

    # ── Section 7: Anything Else ───────────────────────────────────────

    st.header("7. Anything Else")

    responses["anything_else"] = st.text_area(
        "Anything about fuel on the farm that I haven't asked about? "
        "Or any ideas for what you'd want to see in a dashboard?",
        value=get(saved, "anything_else"),
        height=150,
    )

    responses["who_else_to_talk_to"] = st.text_input(
        "Anyone else I should chat to? (workshop manager, fuel attendant, etc.)",
        value=get(saved, "who_else_to_talk_to"),
    )

    # ── Save ───────────────────────────────────────────────────────────

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Progress", type="primary", use_container_width=True):
            if save_responses(responses):
                st.success("Saved! You can close this and come back later.")

    with col2:
        if st.button("Save & Submit", use_container_width=True):
            responses["_submitted"] = True
            if save_responses(responses):
                st.balloons()
                st.success(
                    "Thanks Dad! I've got everything I need to get started. "
                    "I'll go through your answers and then we can sit down "
                    "together so you can show me the actual forms and data."
                )

    # Show save status
    last_updated = saved.get("_last_updated")
    submitted = saved.get("_submitted", False)
    if last_updated:
        status = "Submitted" if submitted else "In progress"
        st.caption(f"Status: {status} | Last saved: {last_updated}")


if __name__ == "__main__":
    main()
