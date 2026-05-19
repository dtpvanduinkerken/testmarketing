import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="VDK Marketing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# STYLING
# =====================================================

st.markdown("""
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>

html,
body,
[data-testid="stAppViewContainer"]{
    background:#f4efe6;
    font-family:'sofia-pro',sans-serif;
}

/* STREAMLIT */

#MainMenu{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

header{
    visibility:hidden;
}

/* PAGINA */

.block-container{
    padding-top:35px;
    padding-left:55px;
    padding-right:55px;
    padding-bottom:55px;
    max-width:1800px;
}

/* SIDEBAR */

section[data-testid="stSidebar"]{
    background:
        linear-gradient(
            180deg,
            #084422 0%,
            #0b5a33 100%
        );
    border-right:
        1px solid rgba(255,255,255,0.08);
    padding-top:25px;
}

section[data-testid="stSidebar"] *{
    color:white !important;
}

/* STREAMLIT NAVIGATIE */

[data-testid="stSidebarNav"]{
    padding-top:20px;
}

[data-testid="stSidebarNav"]::before{
    content:"📊 VDK Marketing";
    display:block;
    font-size:22px;
    font-weight:700;
    margin-bottom:30px;
    padding-left:10px;
    color:white;
}

[data-testid="stSidebarNav"] li{
    margin-bottom:8px;
}

[data-testid="stSidebarNav"] a{
    background:transparent !important;
    border:
        1px solid rgba(255,255,255,0.12);
    border-radius:14px;
    padding:12px 14px;
    transition:0.2s;
}

[data-testid="stSidebarNav"] a:hover{
    background:
        rgba(255,255,255,0.08) !important;
    border:
        1px solid rgba(255,255,255,0.25);
}

[data-testid="stSidebarNav"] a[aria-current="page"]{
    background:white !important;
    color:#084422 !important;
    font-weight:700;
}

/* HERO */

.hero{
    background:
        linear-gradient(
            135deg,
            #084422 0%,
            #0f5f33 100%
        );
    padding:60px;
    border-radius:34px;
    color:white;
    margin-bottom:50px;
    box-shadow:
        0 12px 30px rgba(8,68,34,0.15);
}

.hero h1{
    margin:0;
}

/* KPI */

[data-testid="stMetric"]{
    background:white;
    padding:28px;
    border-radius:24px;
    border:
        1px solid rgba(8,68,34,0.05);
    box-shadow:
        0 10px 25px rgba(8,68,34,0.05);
}

[data-testid="stMetric"]:hover{
    transform:translateY(-2px);
    box-shadow:
        0 15px 35px rgba(8,68,34,0.1);
}

/* TITELS */

.section-title{
    font-size:28px;
    font-weight:700;
    color:#084422;
    margin-bottom:25px;
    padding-bottom:12px;
    border-bottom:3px solid #084422;
    display:inline-block;
}

h1,h2,h3,h4{
    color:#084422;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNCTIONS
# =====================================================

def load_csv(url):

    try:

        response = requests.get(
            url,
            timeout=20
        )

        response.raise_for_status()

        return pd.read_csv(
            io.StringIO(response.text)
        )

    except:

        return pd.DataFrame()

def calculate_growth(current, previous):

    if previous == 0:
        return 0

    return round(
        ((current - previous) / previous) * 100,
        1
    )

# =====================================================
# DATA SOURCES
# =====================================================

SOCIAL_SHEET = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"
MEMBERS_SHEET = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"
NEWSLETTER_SHEET = "1seQjiFaLzEm7PZ2vTDeylSZKEXGqDl6FHe2l1nVPnfg"

FOLLOWERS_GID = "730161295"
MEMBERS_GID = "0"

# =====================================================
# FOLLOWERS DATA
# =====================================================

followers_url = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SOCIAL_SHEET}/export?format=csv&gid={FOLLOWERS_GID}"
)

followers = load_csv(followers_url)

instagram_followers = 0
facebook_followers = 0
instagram_growth = 0
facebook_growth = 0

if not followers.empty:

    followers.columns = (
        followers.columns
        .str.lower()
        .str.strip()
    )

    followers["instagram_followers"] = pd.to_numeric(
        followers["instagram_followers"],
        errors="coerce"
    )

    followers["facebook_followers"] = pd.to_numeric(
        followers["facebook_followers"],
        errors="coerce"
    )

    followers = followers.dropna()

    if len(followers) >= 2:

        current = followers.iloc[-1]
        previous = followers.iloc[-2]

        instagram_followers = int(
            current["instagram_followers"]
        )

        facebook_followers = int(
            current["facebook_followers"]
        )

        instagram_growth = calculate_growth(
            instagram_followers,
            int(previous["instagram_followers"])
        )

        facebook_growth = calculate_growth(
            facebook_followers,
            int(previous["facebook_followers"])
        )

# =====================================================
# MEMBERS DATA
# =====================================================

members_url = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{MEMBERS_SHEET}/export?format=csv&gid={MEMBERS_GID}"
)

members = load_csv(members_url)

total_members = 0

if not members.empty:
    total_members = len(members)

# =====================================================
# NEWSLETTER DATA
# =====================================================

newsletter_url = (
    f"https://opensheet.elk.sh/{NEWSLETTER_SHEET}/Sheet1"
)

try:
    response = requests.get(newsletter_url, timeout=15)
    newsletter = pd.DataFrame(response.json())
except:
    newsletter = pd.DataFrame()

avg_open_rate = 0

if not newsletter.empty:

    newsletter.columns = (
        newsletter.columns
        .str.lower()
        .str.strip()
    )

    if "open_rate" in newsletter.columns:

        newsletter["open_rate"] = pd.to_numeric(
            newsletter["open_rate"],
            errors="coerce"
        )

        avg_open_rate = round(
            newsletter["open_rate"].mean(),
            1
        )

# =====================================================
# HERO
# =====================================================

st.markdown(f"""
<div class="hero">

<h1 style="
    color:white;
    font-size:64px;
    margin-bottom:16px;
">
📊 VDK Marketing Dashboard
</h1>

<p style="
    font-size:20px;
    opacity:0.95;
    max-width:900px;
    line-height:1.8;
">
Live overzicht van de belangrijkste marketing KPI's.
</p>

<p style="
    margin-top:30px;
    font-size:16px;
    opacity:0.85;
">
📅 {datetime.now().strftime('%d %B %Y')}
</p>

</div>
""", unsafe_allow_html=True)

# =====================================================
# KPI'S
# =====================================================

st.markdown(
    '<div class="section-title">📈 Snelle statistieken</div>',
    unsafe_allow_html=True
)

st.write("")

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Instagram volgers",
        f"{instagram_followers:,}".replace(",", "."),
        f"{instagram_growth:+.1f}%"
    )

with col2:

    st.metric(
        "Facebook volgers",
        f"{facebook_followers:,}".replace(",", "."),
        f"{facebook_growth:+.1f}%"
    )

with col3:

    st.metric(
        "Nieuwe members 2026",
        f"{total_members:,}".replace(",", ".")
    )

with col4:

    st.metric(
        "Gem. open rate",
        f"{avg_open_rate:.1f}%"
    )
