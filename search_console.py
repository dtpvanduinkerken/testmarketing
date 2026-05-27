from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import pandas as pd

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

SITE_URL = "https://www.vanduinkerken.com/"

SPREADSHEET_NAME = "VDK Website Dashboard"

WORKSHEET_NAME = "search_console"

# =====================================================
# AUTH
# =====================================================

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "oauth.json",
    SCOPES
)

credentials = flow.run_local_server(port=8080)

service = build(
    "searchconsole",
    "v1",
    credentials=credentials
)

# =====================================================
# SEARCH CONSOLE REQUEST
# =====================================================

request = {
    "startDate": "2026-04-20",
    "endDate": "2026-05-20",
    "dimensions": ["query"],
    "rowLimit": 500
}

response = service.searchanalytics().query(
    siteUrl=SITE_URL,
    body=request
).execute()

# =====================================================
# DATAFRAME
# =====================================================

rows = []

for row in response.get("rows", []):

    keyword = row["keys"][0]

    clicks = row["clicks"]

    impressions = row["impressions"]

    ctr = round(row["ctr"] * 100, 2)

    position = round(row["position"], 2)

    rows.append({
        "zoekwoord": keyword,
        "clicks": clicks,
        "vertoningen": impressions,
        "ctr": ctr,
        "positie": position,
    })

df = pd.DataFrame(rows)

# =====================================================
# GOOGLE SHEETS AUTH
# =====================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "client_secret.json",
    scope
)

gs_client = gspread.authorize(creds)

# =====================================================
# GOOGLE SHEET OPENEN
# =====================================================

sheet = gs_client.open(SPREADSHEET_NAME)

worksheet = sheet.worksheet(WORKSHEET_NAME)

# =====================================================
# SHEET LEEGMAKEN
# =====================================================

worksheet.clear()

# =====================================================
# DATA SCHRIJVEN
# =====================================================

data = [df.columns.tolist()] + df.values.tolist()

worksheet.update(data)

print("✅ Search Console data succesvol geschreven!")
print(df.head())