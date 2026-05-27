from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric
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
WORKSHEET_NAME = "funnel"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

# =====================================================
# GOOGLE ANALYTICS AUTH
# =====================================================

credentials = service_account.Credentials.from_service_account_file(
    "client_secret.json",
    scopes=SCOPES
)

client = BetaAnalyticsDataClient(
    credentials=credentials
)

# =====================================================
# FUNNEL DATA
# =====================================================

funnel_metrics = [
    ("sessions", "Sessies"),
    ("addToCarts", "Toegevoegd aan winkelwagen"),
    ("checkouts", "Checkout gestart"),
    ("ecommercePurchases", "Aankopen")
]

results = []

for metric_id, label in funnel_metrics:

    request = RunReportRequest(
        property=f"properties/{PROPERTY_ID}",
        date_ranges=[
            DateRange(
                start_date="30daysAgo",
                end_date="today"
            )
        ],
        metrics=[
            Metric(name=metric_id)
        ]
    )

    response = client.run_report(request)

    value = int(
        float(
            response.rows[0].metric_values[0].value
        )
    )

    results.append({
        "stap": label,
        "aantal": value
    })

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(results)

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
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ Funnel data succesvol geschreven!")

print(df)
