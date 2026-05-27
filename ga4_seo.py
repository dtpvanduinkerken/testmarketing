from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter
)

from google.oauth2 import service_account

import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

PROPERTY_ID = "314034198"

SPREADSHEET_NAME = "VDK Website Dashboard"
WORKSHEET_NAME = "seo"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

# =====================================================
# AUTH
# =====================================================

credentials = service_account.Credentials.from_service_account_file(
    "client_secret.json",
    scopes=SCOPES
)

client = BetaAnalyticsDataClient(
    credentials=credentials
)

# =====================================================
# API REQUEST
# =====================================================

request = RunReportRequest(
    property=f"properties/{PROPERTY_ID}",

    date_ranges=[
        DateRange(
            start_date="30daysAgo",
            end_date="today"
        )
    ],

    dimensions=[
        Dimension(name="landingPage")
    ],

    metrics=[
        Metric(name="sessions"),
        Metric(name="totalUsers"),
        Metric(name="screenPageViews"),
        Metric(name="ecommercePurchases"),
        Metric(name="purchaseRevenue")
    ],

    dimension_filter=FilterExpression(
        filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(
                value="Organic Search"
            )
        )
    ),

    limit=100
)

response = client.run_report(request)

# =====================================================
# DATAFRAME
# =====================================================

data = []

for row in response.rows:

    data.append({
        "landingpage": row.dimension_values[0].value,
        "sessies": int(row.metric_values[0].value),
        "gebruikers": int(row.metric_values[1].value),
        "paginaweergaven": int(row.metric_values[2].value),
        "aankopen": int(row.metric_values[3].value),
        "omzet": round(float(row.metric_values[4].value), 2)
    })

df = pd.DataFrame(data)

df = df.sort_values(
    by="sessies",
    ascending=False
)

# =====================================================
# GOOGLE SHEETS AUTH
# =====================================================

sheet_scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

sheet_creds = ServiceAccountCredentials.from_json_keyfile_name(
    "client_secret.json",
    sheet_scope
)

gs_client = gspread.authorize(sheet_creds)

# =====================================================
# WRITE TO SHEET
# =====================================================

sheet = gs_client.open(SPREADSHEET_NAME)

try:
    worksheet = sheet.worksheet(WORKSHEET_NAME)

except:
    worksheet = sheet.add_worksheet(
        title=WORKSHEET_NAME,
        rows=2000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ SEO data succesvol geschreven!")

print(df.head())
