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

WORKSHEET_NAME = "overview_kpis"

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
        {"name": "date"}
    ],

    metrics=[
        {"name": "totalRevenue"},
        {"name": "transactions"},
        {"name": "activeUsers"},
        {"name": "sessions"},
        {"name": "addToCarts"},
        {"name": "checkouts"},
        {"name": "ecommercePurchases"},
    ],

    date_ranges=[
        {
            "start_date": "30daysAgo",
            "end_date": "today"
        }
    ],
)

response = client.run_report(request)

# =====================================================
# DATAFRAME
# =====================================================

rows = []

for row in response.rows:

    omzet = float(row.metric_values[0].value)

    orders = int(float(row.metric_values[1].value))

    bezoekers = int(float(row.metric_values[2].value))

    sessies = int(float(row.metric_values[3].value))

    add_to_carts = int(float(row.metric_values[4].value))

    checkout_start = int(float(row.metric_values[5].value))

    aankopen = int(float(row.metric_values[6].value))

    # =================================================
    # CONVERSIE BEREKENEN
    # =================================================

    conversie = 0

    if sessies > 0:
        conversie = (orders / sessies) * 100

    # =================================================
    # GEMIDDELDE ORDERWAARDE
    # =================================================

    gemiddelde_orderwaarde = 0

    if orders > 0:
        gemiddelde_orderwaarde = omzet / orders

    # =================================================
    # ROW TOEVOEGEN
    # =================================================

    rows.append({
        "date": row.dimension_values[0].value,
        "omzet": round(omzet, 2),
        "orders": orders,
        "bezoekers": bezoekers,
        "sessies": sessies,
        "conversie": round(conversie, 2),
        "add_to_carts": add_to_carts,
        "checkout_start": checkout_start,
        "aankopen": aankopen,
        "gemiddelde_orderwaarde": round(gemiddelde_orderwaarde, 2),
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

# =====================================================
# CONTROLE
# =====================================================

print(df.head())
