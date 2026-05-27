from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest

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

WORKSHEET_NAME = "site_search"

TOKEN_FILE = "token.json"

# =====================================================
# GA4 AUTH
# =====================================================

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

credentials = None

# =====================================================
# TOKEN CHECK
# =====================================================

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

else:

    print("❌ GEEN TOKEN GEVONDEN")

# =====================================================
# NIEUWE LOGIN
# =====================================================

if credentials is None:

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

    print("✅ LOGIN SUCCESVOL")

    with open(TOKEN_FILE, "w") as token:

        token.write(credentials.to_json())

    print("✅ TOKEN.JSON OPGESLAGEN")

# =====================================================
# DEBUG
# =====================================================

print("📁 HUIDIGE MAP:")
print(os.getcwd())

print("📄 BESTANDEN IN MAP:")
print(os.listdir())

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
# SORTEREN
# =====================================================

df = df.sort_values(
    by="zoekopdrachten",
    ascending=False
)

# =====================================================
# GOOGLE SHEETS AUTH
# =====================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

sheet_creds = ServiceAccountCredentials.from_json_keyfile_name(
    "client_secret.json",
    scope
)

gs_client = gspread.authorize(sheet_creds)

# =====================================================
# GOOGLE SHEET OPENEN
# =====================================================

sheet = gs_client.open(SPREADSHEET_NAME)

try:

    worksheet = sheet.worksheet(WORKSHEET_NAME)

    print("✅ Worksheet gevonden")

except:

    worksheet = sheet.add_worksheet(
        title=WORKSHEET_NAME,
        rows=2000,
        cols=20
    )

    print("✅ Nieuwe worksheet aangemaakt")

# =====================================================
# SHEET LEEGMAKEN
# =====================================================

worksheet.clear()

# =====================================================
# DATA SCHRIJVEN
# =====================================================

data = [df.columns.tolist()] + df.values.tolist()

worksheet.update(data)

# =====================================================
# DONE
# =====================================================

print("✅ Site search data succesvol geschreven!")

print(df.head())
