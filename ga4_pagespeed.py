import requests
import pandas as pd

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# =====================================================
# CONFIG
# =====================================================

API_KEY = "AIzaSyAwj3lZ4wMt_IKuZcVwIgEJoEN11ta0P-U"

SPREADSHEET_NAME = "VDK Website Dashboard"

WORKSHEET_NAME = "page_speed"

URLS = [
    "https://www.vanduinkerken.com/",
    "https://www.vanduinkerken.com/kamperen",
    "https://www.vanduinkerken.com/wandelen",
]

# =====================================================
# DATA OPHALEN
# =====================================================

rows = []

for url in URLS:

    mobile_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=mobile&key={API_KEY}"

    desktop_url = f"https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url={url}&strategy=desktop&key={API_KEY}"

    mobile_response = requests.get(mobile_url).json()

    desktop_response = requests.get(desktop_url).json()

    try:

        mobile_score = mobile_response["lighthouseResult"]["categories"]["performance"]["score"] * 100

        desktop_score = desktop_response["lighthouseResult"]["categories"]["performance"]["score"] * 100

        rows.append({
            "pagina": url,
            "mobile_speed": round(mobile_score),
            "desktop_speed": round(desktop_score),
        })

    except:
        print(f"❌ Fout bij {url}")

df = pd.DataFrame(rows)

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

data = [df.columns.tolist()] + df.values.tolist()

worksheet.update(data)

print("✅ PageSpeed data succesvol geschreven!")

print(df)