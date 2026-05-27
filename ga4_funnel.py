from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Metric
)

from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials

import pandas as pd
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

PROPERTY_ID = "314034198"

SPREADSHEET_NAME = "VDK Website Dashboard"
WORKSHEET_NAME = "funnel"

TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

# =====================================================
# TOKEN CHECK
# =====================================================

credentials = None

print("🔍 TOKEN BESTAAT:", os.path.exists(TOKEN_FILE))

# =====================================================
# BESTAAND TOKEN LADEN
# =====================================================

if os.path.exists(TOKEN_FILE):

    credentials = Credentials.from_authorized_user_file(
        TOKEN_FILE,
        SCOPES
    )

    print("✅ Bestaand token geladen")

# =====================================================
# NIEUWE LOGIN
# =====================================================

else:

    print("🔐 Nieuwe Google login gestart")

    flow = InstalledAppFlow.from_client_secrets_file(
        "oauth.json",
        SCOPES
    )

    credentials = flow.run_local_server(
        port=8080,
        access_type="offline",
        prompt="consent"
    )

    with open(TOKEN_FILE, "w") as token:

        token.write(credentials.to_json())

    print("✅ TOKEN.JSON opgeslagen")

# =====================================================
# DEBUG
# =====================================================

print("📁 HUIDIGE MAP:")
print(os.getcwd())

print("📄 BESTANDEN IN MAP:")
print(os.listdir())

# =====================================================
# GOOGLE ANALYTICS CLIENT
# =====================================================

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