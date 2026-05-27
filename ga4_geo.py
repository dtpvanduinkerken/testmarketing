from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    Dimension,
    Metric,
    DateRange
)

from google_auth_oauthlib.flow import InstalledAppFlow
from oauth2client.service_account import ServiceAccountCredentials

import pandas as pd
import gspread
import os

# =====================================================
# CONFIG
# =====================================================

PROPERTY_ID = "314034198"

SPREADSHEET_NAME = "VDK Website Dashboard"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

# =====================================================
# GOOGLE ANALYTICS LOGIN (OAUTH)
# =====================================================

flow = InstalledAppFlow.from_client_secrets_file(
    "oauth.json",
    SCOPES
)

credentials = flow.run_local_server(
    port=8090
)

# =====================================================
# GA4 CLIENT
# =====================================================

client = BetaAnalyticsDataClient(
    credentials=credentials
)

# =====================================================
# REQUEST
# =====================================================

request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",

    dimensions=[
        Dimension(name="country"),
        Dimension(name="city")
    ],

    metrics=[
        Metric(name="activeUsers"),
        Metric(name="sessions"),
        Metric(name="purchaseRevenue"),
        Metric(name="transactions")
    ],

    date_ranges=[
        DateRange(
            start_date="30daysAgo",
            end_date="today"
        )
    ],

    limit=100
)

response = client.run_report(request)

# =====================================================
# DATAFRAME
# =====================================================

rows = []

for row in response.rows:

    rows.append({
        "land": row.dimension_values[0].value,
        "stad": row.dimension_values[1].value,
        "bezoekers": row.metric_values[0].value,
        "sessies": row.metric_values[1].value,
        "omzet": row.metric_values[2].value,
        "orders": row.metric_values[3].value
    })

df = pd.DataFrame(rows)

# =====================================================
# GOOGLE SHEETS LOGIN (SERVICE ACCOUNT)
# =====================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

creds = ServiceAccountCredentials.from_json_keyfile_name(
    "client_secret.json",
    scope
)

gc = gspread.authorize(creds)

sheet = gc.open(SPREADSHEET_NAME)

# =====================================================
# WORKSHEET
# =====================================================

try:
    worksheet = sheet.worksheet("geo")

except:
    worksheet = sheet.add_worksheet(
        title="geo",
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

# =====================================================
# DONE
# =====================================================

print("✅ Geo data succesvol geschreven!")
print(df.head())