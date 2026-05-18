import io
from datetime import datetime

import pandas as pd
import plotly.express as px
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
# SIDEBAR NAVIGATION
# =====================================================

with st.sidebar:

    st.markdown("""
    <style>
    .sidebar-title{
        font-size:20px;
        font-weight:600;
        margin-bottom:20px;
        padding-bottom:12px;
        border-bottom:1px solid rgba(255,255,255,0.15);
        opacity:0.95;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-bottom:40px; text-align:center;">
        <div style="font-size:42px;">📊</div>
        <div style="font-size:18px; font-weight:700;">
            VDK Marketing
        </div>
        <div style="font-size:12px; opacity:0.7;">
            Dashboard v2.0
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown(
        '<div class="sidebar-title">Dashboards</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🏠 Home",
        use_container_width=True
    ):
        st.switch_page("main.py")

    if st.button(
        "📱 Social Media",
        use_container_width=True
    ):
        st.switch_page("pages/social.py")

    if st.button(
        "👥 Members",
        use_container_width=True
    ):
        st.switch_page("pages/members.py")

    if st.button(
        "✉️ Nieuwsbrief",
        use_container_width=True
    ):
        st.switch_page("pages/newsletter.py")

    if st.button(
        "📅 Afspraken",
        use_container_width=True
    ):
        st.switch_page("pages/events.py")

    st.write("")
    st.divider()
    st.write("")

    st.markdown(
        '<div class="sidebar-title">Hulpmiddelen</div>',
        unsafe_allow_html=True
    )

    if st.button(
        "🔄 Vernieuwen gegevens",
        use_container_width=True
    ):
        st.cache_data.clear()
        st.rerun()

    st.write("")
    st.divider()

    st.markdown("""
    <div style="
        font-size:12px;
        opacity:0.65;
        text-align:center;
        margin-top:20px;
        line-height:1.7;
    ">
        📦 Google Sheets koppeling<br>
        🔄 Live synchronisatie<br>
        ☁️ Hosted via Render
    </div>
    """, unsafe_allow_html=True)

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

/* VERBERG STREAMLIT ELEMENTEN */

#MainMenu{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

header{
    visibility:hidden;
}

/* VERBERG DUBBELE NAVIGATIE */

[data-testid="stSidebarNav"]{
    display:none !important;
}

[data-testid="stSidebarNavItems"]{
    display:none !important;
}

section[data-testid="stSidebar"] ul{
    display:none !important;
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

section[data-testid="stSidebar"] button{
    background:transparent !important;
    color:white !important;
    border:
        1px solid rgba(255,255,255,0.12) !important;
    border-radius:14px !important;
    font-weight:500 !important;
    font-size:15px !important;
    padding:12px 16px !important;
    margin-bottom:10px !important;
    transition:0.2s;
}

section[data-testid="stSidebar"] button:hover{
    background:
        rgba(255,255,255,0.08) !important;
    border:
        1px solid rgba(255,255,255,0.25) !important;
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

/* BUTTONS */

div.stButton > button{
    width:100%;
    background:white;
    color:#084422;
    border:
        2px solid rgba(8,68,34,0.1);
    border-radius:22px;
    padding:28px 20px;
    text-align:left;
    font-size:18px;
    font-weight:700;
    box-shadow:
        0 8px 20px rgba(8,68,34,0.05);
    min-height:100px;
    transition:0.2s;
}

div.stButton > button:hover{
    background:#084422;
    color:white;
    border:2px solid #084422;
    transform:translateY(-4px);
    box-shadow:
        0 15px 35px rgba(8,68,34,0.15);
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

/* CARDS */

.feature-card{
    background:white;
    padding:25px;
    border-radius:22px;
    box-shadow:
        0 8px 20px rgba(8,68,34,0.05);
    border-left:4px solid #084422;
    transition:0.2s;
}

.feature-card:hover{
    transform:translateY(-4px);
    box-shadow:
        0 12px 30px rgba(8,68,34,0.1);
}

/* DIVIDER */

.divider-line{
    height:2px;
    background:
        linear-gradient(
            90deg,
            transparent,
            #084422,
            transparent
        );
    margin:40px 0;
}

/* FOOTER */

.footer-info{
    background:
        rgba(8,68,34,0.05);
    padding:30px;
    border-radius:24px;
    margin-top:50px;
    text-align:center;
    border-top:2px solid #084422;
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
Centraal overzicht van social media,
members, nieuwsbrieven en marketingprestaties.
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
        "Totale volgers",
        f"{instagram_followers + facebook_followers:,}".replace(",", ".")
    )

with col4:

    st.metric(
        "Dashboard status",
        "✅ Live"
    )

# =====================================================
# DASHBOARD BUTTONS
# =====================================================

st.write("")
st.write("")

st.markdown(
    '<div class="section-title">🎯 Dashboards</div>',
    unsafe_allow_html=True
)

col1, col2 = st.columns(2)

with col1:

    if st.button(
        "📱 Social Media Dashboard",
        use_container_width=True
    ):
        st.switch_page("pages/social.py")

with col2:

    if st.button(
        "👥 Members Dashboard",
        use_container_width=True
    ):
        st.switch_page("pages/members.py")

col3, col4 = st.columns(2)

with col3:

    if st.button(
        "✉️ Nieuwsbrief Dashboard",
        use_container_width=True
    ):
        st.switch_page("pages/newsletter.py")

with col4:

    if st.button(
        "📅 Events Dashboard",
        use_container_width=True
    ):
        st.switch_page("pages/events.py")

# =====================================================
# GRAPH
# =====================================================

if not followers.empty:

    st.markdown(
        '<div class="divider-line"></div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="section-title">📊 Volgers ontwikkeling</div>',
        unsafe_allow_html=True
    )

    chart_df = followers.copy()

    chart_df["date"] = pd.to_datetime(
        chart_df["date"],
        errors="coerce"
    )

    fig = px.line(
        chart_df,
        x="date",
        y=[
            "instagram_followers",
            "facebook_followers"
        ],
        template="simple_white"
    )

    fig.update_layout(
        height=500,
        paper_bgcolor="white",
        plot_bgcolor="#ffffff",
        xaxis_title="",
        yaxis_title="Volgers"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

# =====================================================
# FOOTER
# =====================================================

st.markdown(
    '<div class="divider-line"></div>',
    unsafe_allow_html=True
)

st.markdown(f"""
<div class="footer-info">

<h3>📋 Dashboard informatie</h3>

<p>
Databronnen:
Google Sheets API
</p>

<p>
Hosting:
Render Cloud
</p>

<p style="
    margin-top:20px;
    font-size:14px;
    opacity:0.7;
">
Laatst bijgewerkt:
{datetime.now().strftime('%d %B %Y om %H:%M')}
</p>

</div>
""", unsafe_allow_html=True)
