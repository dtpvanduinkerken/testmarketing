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

page_speed = pd.DataFrame(
    sheet.worksheet("page_speed").get_all_records()
)

funnel = pd.DataFrame(
    sheet.worksheet("funnel").get_all_records()
)

devices = pd.DataFrame(
    sheet.worksheet("devices").get_all_records()
)

alerts = []

# =====================================================
# OMZET ALERT
# =====================================================

avg_revenue = overview["omzet"].mean()
latest_revenue = overview.iloc[0]["omzet"]

if latest_revenue < avg_revenue * 0.7:
    alerts.append({
        "prioriteit": "Hoog",
        "categorie": "Omzet",
        "melding": "De omzet ligt fors lager dan gemiddeld."
    })

# =====================================================
# PAGE SPEED ALERT
# =====================================================

try:
    mobile_score = page_speed[
        page_speed["device"] == "mobile"
    ].iloc[0]["performance_score"]

    if mobile_score < 50:
        alerts.append({
            "prioriteit": "Hoog",
            "categorie": "Website snelheid",
            "melding": "Mobiele paginasnelheid is erg laag."
        })

except:
    pass

# =====================================================
# CHECKOUT ALERT
# =====================================================

try:
    cart = funnel[
        funnel["stap"] == "Toegevoegd aan winkelwagen"
    ].iloc[0]["aantal"]

    purchases = funnel[
        funnel["stap"] == "Aankopen"
    ].iloc[0]["aantal"]

    conversion = purchases / cart

    if conversion < 0.15:
        alerts.append({
            "prioriteit": "Gemiddeld",
            "categorie": "Checkout",
            "melding": "Veel winkelwagens converteren niet naar aankopen."
        })

except:
    pass

# =====================================================
# DEVICE ALERT
# =====================================================

try:
    mobile = devices[
        devices["device"] == "mobile"
    ].iloc[0]["sessies"]

    desktop = devices[
        devices["device"] == "desktop"
    ].iloc[0]["sessies"]

    if mobile > desktop * 2:
        alerts.append({
            "prioriteit": "Informatie",
            "categorie": "Mobile",
            "melding": "Meer dan 2x zoveel verkeer komt via mobiel."
        })

except:
    pass

# =====================================================
# FALLBACK
# =====================================================

if len(alerts) == 0:

    alerts.append({
        "prioriteit": "Info",
        "categorie": "Algemeen",
        "melding": "Geen kritieke meldingen gevonden."
    })

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(alerts)

# =====================================================
# WRITE TO SHEET
# =====================================================

try:
    worksheet = sheet.worksheet("alerts")
except:
    worksheet = sheet.add_worksheet(
        title="alerts",
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ Alerts succesvol geschreven!")
print(df)