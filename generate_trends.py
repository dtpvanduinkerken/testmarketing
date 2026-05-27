import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

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

sheet = gs_client.open("VDK Website Dashboard")

# =====================================================
# LOAD DATA
# =====================================================

overview = pd.DataFrame(
    sheet.worksheet("overview_kpis").get_all_records()
)

overview["date"] = pd.to_datetime(overview["date"])

overview = overview.sort_values("date")

# =====================================================
# TREND CALCULATIONS
# =====================================================

latest = overview.iloc[-1]
previous = overview.iloc[-2]

def calc_growth(current, previous):

    if previous == 0:
        return 0

    return round(((current - previous) / previous) * 100, 1)

trends = []

# =====================================================
# OMZET
# =====================================================

revenue_growth = calc_growth(
    latest["omzet"],
    previous["omzet"]
)

trends.append({
    "metric": "Omzet",
    "huidig": latest["omzet"],
    "vorig": previous["omzet"],
    "groei_%": revenue_growth
})

# =====================================================
# SESSIES
# =====================================================

sessions_growth = calc_growth(
    latest["sessies"],
    previous["sessies"]
)

trends.append({
    "metric": "Sessies",
    "huidig": latest["sessies"],
    "vorig": previous["sessies"],
    "groei_%": sessions_growth
})

# =====================================================
# ORDERS
# =====================================================

orders_growth = calc_growth(
    latest["orders"],
    previous["orders"]
)

trends.append({
    "metric": "Orders",
    "huidig": latest["orders"],
    "vorig": previous["orders"],
    "groei_%": orders_growth
})

# =====================================================
# BEZOEKERS
# =====================================================

visitors_growth = calc_growth(
    latest["bezoekers"],
    previous["bezoekers"]
)

trends.append({
    "metric": "Bezoekers",
    "huidig": latest["bezoekers"],
    "vorig": previous["bezoekers"],
    "groei_%": visitors_growth
})

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(trends)

# =====================================================
# WRITE TO SHEET
# =====================================================

try:
    worksheet = sheet.worksheet("trends")
except:
    worksheet = sheet.add_worksheet(
        title="trends",
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ Trends succesvol geschreven!")
print(df)