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

WORKSHEET_NAME = "pages"

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
        {"name": "pagePath"},
    ],

    metrics=[
        {"name": "screenPageViews"},
        {"name": "sessions"},
        {"name": "averageSessionDuration"},
        {"name": "bounceRate"},
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

    views = int(float(row.metric_values[0].value))

    sessies = int(float(row.metric_values[1].value))

    gemiddelde_tijd = round(
        float(row.metric_values[2].value),
        2
    )

    bounce_rate = round(
        float(row.metric_values[3].value) * 100,
        2
    )

    rows.append({
        "date": date,
        "page": page,
        "views": views,
        "sessies": sessies,
        "gemiddelde_tijd_sec": gemiddelde_tijd,
        "bounce_rate": bounce_rate,
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