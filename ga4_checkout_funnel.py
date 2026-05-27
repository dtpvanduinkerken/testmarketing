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

WORKSHEET_NAME = "checkout_funnel"

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

    metrics=[
        {"name": "itemsViewed"},
        {"name": "addToCarts"},
        {"name": "checkouts"},
        {"name": "transactions"},
    ],

    date_ranges=[
        {
            "start_date": "30daysAgo",
            "end_date": "today"
        }
    ]
)

response = client.run_report(request)

# =====================================================
# DATAFRAME
# =====================================================

row = response.rows[0]

product_views = int(float(row.metric_values[0].value))

add_to_carts = int(float(row.metric_values[1].value))

checkouts = int(float(row.metric_values[2].value))

aankopen = int(float(row.metric_values[3].value))

funnel_data = pd.DataFrame([
    {
        "stap": "Product bekeken",
        "aantal": product_views
    },
    {
        "stap": "Toegevoegd aan winkelwagen",
        "aantal": add_to_carts
    },
    {
        "stap": "Checkout gestart",
        "aantal": checkouts
    },
    {
        "stap": "Aankopen",
        "aantal": aankopen
    }
])

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

data = [funnel_data.columns.tolist()] + funnel_data.values.tolist()

worksheet.update(data)

print("✅ Funnel data succesvol geschreven!")

print(funnel_data)