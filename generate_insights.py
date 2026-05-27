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

channels = pd.DataFrame(
    sheet.worksheet("channels").get_all_records()
)

devices = pd.DataFrame(
    sheet.worksheet("devices").get_all_records()
)

products = pd.DataFrame(
    sheet.worksheet("products").get_all_records()
)

seo = pd.DataFrame(
    sheet.worksheet("seo").get_all_records()
)

# =====================================================
# INSIGHTS
# =====================================================

insights = []

# KPI INSIGHTS

total_revenue = overview["omzet"].sum()
total_sessions = overview["sessies"].sum()
total_orders = overview["orders"].sum()

insights.append({
    "type": "Omzet",
    "insight": f"De webshop behaalde €{round(total_revenue, 2)} omzet in de afgelopen periode."
})

insights.append({
    "type": "Verkeer",
    "insight": f"De website kreeg {int(total_sessions)} sessies."
})

insights.append({
    "type": "Bestellingen",
    "insight": f"Er werden {int(total_orders)} bestellingen geplaatst."
})

# CHANNEL INSIGHTS

top_channel = channels.sort_values(
    by="sessies",
    ascending=False
).iloc[0]

insights.append({
    "type": "Kanaal",
    "insight": f"Het grootste verkeerskanaal is {top_channel['kanaal']} met {top_channel['sessies']} sessies."
})

# DEVICE INSIGHTS

top_device = devices.sort_values(
    by="sessies",
    ascending=False
).iloc[0]

insights.append({
    "type": "Device",
    "insight": f"De meeste bezoekers gebruiken {top_device['device']}."
})

# PRODUCT INSIGHTS

top_product = products.sort_values(
    by="omzet",
    ascending=False
).iloc[0]

insights.append({
    "type": "Product",
    "insight": f"Het best presterende product is '{top_product['product']}' met €{round(top_product['omzet'],2)} omzet."
})

# SEO INSIGHTS

seo_sessions = seo["sessies"].sum()

insights.append({
    "type": "SEO",
    "insight": f"SEO genereerde {int(seo_sessions)} sessies in de afgelopen periode."
})

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(insights)

# =====================================================
# WRITE TO SHEET
# =====================================================

try:
    worksheet = sheet.worksheet("insights")
except:
    worksheet = sheet.add_worksheet(
        title="insights",
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ Insights succesvol geschreven!")
print(df)