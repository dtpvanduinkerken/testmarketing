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

landing_pages = pd.DataFrame(
    sheet.worksheet("landing_pages").get_all_records()
)

products = pd.DataFrame(
    sheet.worksheet("products").get_all_records()
)

seo = pd.DataFrame(
    sheet.worksheet("seo").get_all_records()
)

opportunities = []

# =====================================================
# LANDINGPAGES
# =====================================================

for _, row in landing_pages.iterrows():

    try:

        sessions = float(row["sessies"])
        purchases = float(row["aankopen"])

        if sessions > 500 and purchases < 2:

            opportunities.append({
                "categorie": "Landingpage",
                "kans": f"Landingpage '{row['landingpage']}' krijgt veel verkeer maar weinig aankopen."
            })

    except:
        pass

# =====================================================
# PRODUCTS
# =====================================================

for _, row in products.iterrows():

    try:

        views = float(row["weergaven"])
        revenue = float(row["omzet"])

        if views > 200 and revenue < 50:

            opportunities.append({
                "categorie": "Product",
                "kans": f"Product '{row['product']}' krijgt veel aandacht maar levert weinig omzet op."
            })

    except:
        pass

# =====================================================
# SEO
# =====================================================

for _, row in seo.iterrows():

    try:

        sessions = float(row["sessies"])
        purchases = float(row["aankopen"])

        if sessions > 300 and purchases == 0:

            opportunities.append({
                "categorie": "SEO",
                "kans": f"SEO pagina '{row['landingpage']}' trekt verkeer maar converteert niet."
            })

    except:
        pass

# =====================================================
# FALLBACK
# =====================================================

if len(opportunities) == 0:

    opportunities.append({
        "categorie": "Algemeen",
        "kans": "Geen directe optimalisatiekansen gevonden."
    })

# =====================================================
# DATAFRAME
# =====================================================

df = pd.DataFrame(opportunities)

# =====================================================
# WRITE TO SHEET
# =====================================================

try:
    worksheet = sheet.worksheet("opportunities")
except:
    worksheet = sheet.add_worksheet(
        title="opportunities",
        rows=1000,
        cols=20
    )

worksheet.clear()

worksheet.update(
    [df.columns.values.tolist()] +
    df.values.tolist()
)

print("✅ Opportunities succesvol geschreven!")
print(df)