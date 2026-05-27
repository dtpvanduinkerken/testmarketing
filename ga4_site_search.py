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

WORKSHEET_NAME = "site_search"

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
        {"name": "searchTerm"}
    ],

    metrics=[
        {"name": "eventCount"},
        {"name": "totalUsers"},
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

    zoekterm = row.dimension_values[0].value

    zoekopdrachten = int(float(row.metric_values[0].value))

    gebruikers = int(float(row.metric_values[1].value))

    rows.append({
        "zoekterm": zoekterm,
        "zoekopdrachten": zoekopdrachten,
        "gebruikers": gebruikers,
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

print("✅ Site search data succesvol geschreven!")

print(df.head())