from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    FilterExpression,
    Filter
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
WORKSHEET_NAME = "seo"

TOKEN_FILE = "token.json"

SCOPES = [
    "https://www.googleapis.com/auth/analytics.readonly"
]

# =====================================================
# GA4 AUTH
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

    landingpage = row.dimension_values[0].value

    sessies = int(float(row.metric_values[0].value))

    gebruikers = int(float(row.metric_values[1].value))

    paginaweergaven = int(float(row.metric_values[2].value))

    aankopen = int(float(row.metric_values[3].value))

    omzet = round(float(row.metric_values[4].value), 2)

    conversie = 0

    if sessies > 0:
        conversie = round((aankopen / sessies) * 100, 2)

    data.append({
        "landingpage": landingpage,
        "sessies": sessies,
        "gebruikers": gebruikers,
        "paginaweergaven": paginaweergaven,
        "aankopen": aankopen,
        "omzet": omzet,
        "conversie": conversie
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

    print("✅ Worksheet gevonden")

except:

    worksheet = sheet.add_worksheet(
        title=WORKSHEET_NAME,
        rows=2000,
        cols=20
    )

    print("✅ Nieuwe worksheet aangemaakt")

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

# =====================================================
# DONE
# =====================================================

print("✅ SEO data succesvol geschreven!")

print(df.head())