"""
Google Sheets Uploader — CAMX 2026 Final Output
=================================================
Uploads the final enriched + personalized dataset to a Google Sheet.

Setup:
  1. Create a Google Cloud project
  2. Enable Google Sheets API + Google Drive API
  3. Create a Service Account, download credentials JSON
  4. Share your target Google Sheet with the service account email
  5. Set env var: GOOGLE_CREDS_JSON = path to your credentials JSON file

Run:
  GOOGLE_CREDS_JSON=creds.json SHEET_ID=<your_sheet_id> python sheets_upload.py
"""

import os, json, csv
from pathlib import Path

CREDS_FILE = os.getenv("GOOGLE_CREDS_JSON", "credentials.json")
SHEET_ID   = os.getenv("SHEET_ID", "")        # your Google Sheet ID
INPUT_CSV  = "camx2026_final.csv"

# Column headers for the sheet (in order)
HEADERS = [
    "Company Name",
    "Booth",
    "Website",
    "LinkedIn URL",
    "Categories",
    "City", "State", "Country",
    "Description",
    "Signal / Enrichment Note",
    "Personalized First Line",
]

# Column mapping: CSV field → sheet column
FIELD_MAP = {
    "company_name":           "Company Name",
    "booth":                  "Booth",
    "website":                "Website",
    "linkedin_url":           "LinkedIn URL",
    "categories":             "Categories",
    "city":                   "City",
    "state":                  "State",
    "country":                "Country",
    "description":            "Description",
    "signal":                 "Signal / Enrichment Note",
    "personalized_first_line":"Personalized First Line",
}


def upload_to_sheets(rows: list[dict], sheet_id: str, creds_path: str) -> str:
    """
    Uploads rows to Google Sheets using gspread.
    Returns the sheet URL.
    """
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        raise SystemExit("Run: pip install gspread google-auth")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    gc    = gspread.authorize(creds)

    # Open sheet by ID or create new one
    if sheet_id:
        sh = gc.open_by_key(sheet_id)
    else:
        sh = gc.create("CAMX 2026 – Exhibitor Outreach")
        print(f"[sheets] Created new sheet: {sh.url}")

    ws = sh.sheet1
    ws.clear()

    # Write header row
    ws.append_row(HEADERS, value_input_option="USER_ENTERED")

    # Write data rows
    data_rows = []
    for row in rows:
        data_rows.append([row.get(f, "") for f in FIELD_MAP.keys()])

    if data_rows:
        ws.append_rows(data_rows, value_input_option="USER_ENTERED")

    # Format: freeze header, bold it, auto-resize columns
    ws.format("A1:K1", {
        "textFormat": {"bold": True},
        "backgroundColor": {"red": 0.2, "green": 0.4, "blue": 0.8},
        "horizontalAlignment": "CENTER",
    })
    ws.freeze(rows=1)

    print(f"[sheets] Uploaded {len(data_rows)} rows → {sh.url}")
    return sh.url


def load_csv(path: str) -> list[dict]:
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


if __name__ == "__main__":
    if not Path(INPUT_CSV).exists():
        raise SystemExit(f"Input file not found: {INPUT_CSV}. Run personalization.py first.")

    rows = load_csv(INPUT_CSV)

    if not SHEET_ID and not Path(CREDS_FILE).exists():
        print("[sheets] No credentials found. To upload to Google Sheets:")
        print("  1. Create a Service Account in Google Cloud Console")
        print("  2. Download credentials JSON")
        print(f"  3. Set GOOGLE_CREDS_JSON={CREDS_FILE}")
        print("  4. Set SHEET_ID=<your_google_sheet_id>")
        print("  5. Re-run this script")
        print()
        print(f"[sheets] Data is ready in: {INPUT_CSV}")
        print(f"[sheets] You can manually import this CSV into Google Sheets via:")
        print("  File → Import → Upload → camx2026_final.csv")
    else:
        url = upload_to_sheets(rows, SHEET_ID, CREDS_FILE)
        print(f"Sheet URL: {url}")
