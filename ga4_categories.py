from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

from google.oauth2 import service_account

import pandas as pd

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

PROPERTY_ID = "314034198"

SPREADSHEET_NAME = "VDK Website Dashboard"

WORKSHEET_NAME = "categories"

# =====================================================
# GA4 AUTH
# =====================================================

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

credentials = service_account.Credentials.from_service_account_file(
    "client_secret.json",
    scopes=SCOPES
)

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
        {"name": "itemCategory"},
    ],

    metrics=[
        {"name": "itemsViewed"},
        {"name": "itemsPurchased"},
        {"name": "itemRevenue"},
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

    category = row.dimension_values[1].value

    views = int(float(row.metric_values[0].value))

    aankopen = int(float(row.metric_values[1].value))

    omzet = round(float(row.metric_values[2].value), 2)

    conversie = 0

    if views > 0:
        conversie = round((aankopen / views) * 100, 2)

    rows.append({
        "date": date,
        "categorie": category,
        "views": views,
        "aankopen": aankopen,
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
