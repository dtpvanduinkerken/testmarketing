from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

from google_auth_oauthlib.flow import InstalledAppFlow

import pandas as pd

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

PROPERTY_ID = "314034198"

SPREADSHEET_NAME = "VDK Website Dashboard"

WORKSHEET_NAME = "landing_pages"

# =====================================================
# GA4 AUTH
# =====================================================

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

flow = InstalledAppFlow.from_client_secrets_file(
    "oauth.json",
    SCOPES
)

credentials = flow.run_local_server(port=8080)

# =====================================================
# GA4 CLIENT
# =====================================================

client = BetaAnalyticsDataClient(
    credentials=credentials
)

# =====================================================
# GA4 REQUEST
# =====================================================

request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",

    dimensions=[
        {"name": "date"},
        {"name": "landingPage"}
    ],

    metrics=[
        {"name": "sessions"},
        {"name": "totalUsers"},
        {"name": "transactions"},
        {"name": "purchaseRevenue"},
    ],

    date_ranges=[
        {
            "start_date": "30daysAgo",
            "end_date": "today"
        }
    ],

    limit=500
)

response = client.run_report(request)

# =====================================================
# DATAFRAME
# =====================================================

rows = []

for row in response.rows:

    date = row.dimension_values[0].value

    page = row.dimension_values[1].value

    sessies = int(float(row.metric_values[0].value))

    bezoekers = int(float(row.metric_values[1].value))

    transacties = int(float(row.metric_values[2].value))

    omzet = round(float(row.metric_values[3].value), 2)

    conversie = 0

    if sessies > 0:
        conversie = round((transacties / sessies) * 100, 2)

    rows.append({
        "date": date,
        "landing_page": page,
        "sessies": sessies,
        "bezoekers": bezoekers,
        "transacties": transacties,
        "omzet": omzet,
        "conversie": conversie,
    })

df = pd.DataFrame(rows)

# =====================================================
# DATUM FORMATTEREN
# =====================================================

df["date"] = pd.to_datetime(
    df["date"],
    format="%Y%m%d"
)

df["date"] = df["date"].dt.strftime("%Y-%m-%d")

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

print("✅ Sheet gevonden")

worksheet = sheet.worksheet(WORKSHEET_NAME)

print("✅ Worksheet gevonden")

# =====================================================
# SHEET LEEGMAKEN
# =====================================================

worksheet.clear()

# =====================================================
# DATA SCHRIJVEN
# =====================================================

data = [df.columns.tolist()] + df.values.tolist()

worksheet.update(data)

print("✅ Data succesvol geschreven!")

print(df.head())