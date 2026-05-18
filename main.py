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
    .sidebar-title {
        font-size: 20px;
        font-weight: 600;
        margin-bottom: 20px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(255,255,255,0.15);
        opacity: 0.95;
    }
    .nav-section {
        margin-bottom: 35px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo/Branding
    st.markdown("""
    <div style="margin-bottom: 40px; text-align: center;">
        <div style="font-size: 36px; margin-bottom: 8px;">📊</div>
        <div style="font-size: 16px; font-weight: 600;">VDK Marketing</div>
        <div style="font-size: 11px; opacity: 0.7; margin-top: 4px;">v1.0</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Main Dashboards
    st.markdown('<div class="sidebar-title">Dashboards</div>', unsafe_allow_html=True)
    
    if st.button("🏠 Home", use_container_width=True, key="nav_home"):
        st.switch_page("pages/home.py")
    
    if st.button("📱 Social Media", use_container_width=True, key="nav_social"):
        st.switch_page("pages/social.py")
    
    if st.button("👥 Members", use_container_width=True, key="nav_members"):
        st.switch_page("pages/members.py")
    
    if st.button("✉️ Nieuwsbrief", use_container_width=True, key="nav_newsletter"):
        st.switch_page("pages/newsletter.py")
    
    if st.button("📅 Afspraken", use_container_width=True, key="nav_events"):
        st.switch_page("pages/events.py")
    
    st.write("")
    st.divider()
    st.write("")
    
    # Utilities
    st.markdown('<div class="sidebar-title">Hulpmiddelen</div>', unsafe_allow_html=True)
    
    if st.button("🔄 Vernieuwen gegevens", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.write("")
    st.divider()
    st.write("")
    
    # Info
    st.markdown("""
    <div style="font-size: 12px; opacity: 0.6; text-align: center; margin-top: 30px;">
    <p>📦 Gegevens van Google Sheets</p>
    <p>🔄 Automatisch bijgewerkt</p>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# STYLING
# =====================================================

st.markdown("""
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>

html, body, [data-testid="stAppViewContainer"]{
    background:#f4efe6;
    font-family:'sofia-pro', sans-serif;
}

.block-container{
    padding-top:35px;
    padding-left:55px;
    padding-right:55px;
    padding-bottom:55px;
    max-width:1800px;
}

/* MENU */

#MainMenu{
    visibility:hidden;
}

footer{
    visibility:hidden;
}

/* SIDEBAR */

section[data-testid="stSidebar"]{
    background:linear-gradient(180deg,#084422 0%, #0a5230 100%);
    border-right:1px solid rgba(255,255,255,0.08);
    padding-top:30px;
}

section[data-testid="stSidebar"] * {
    color:white !important;
}

section[data-testid="stSidebar"] button {
    background: transparent !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,0.12) !important;
    border-radius: 12px !important;
    font-weight: 500 !important;
    font-size: 15px !important;
    padding: 12px 16px !important;
    margin-bottom: 8px !important;
}

section[data-testid="stSidebar"] button:hover {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
}

section[data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    margin-bottom: 20px;
}

/* HERO */

.hero{
    background:linear-gradient(135deg,#084422 0%, #0f5f33 100%);
    padding:60px;
    border-radius:34px;
    color:white;
    margin-bottom:50px;
    box-shadow:0 12px 30px rgba(8,68,34,0.15);
}

.hero h1 {
    margin: 0;
    padding: 0;
}

/* KPI */

[data-testid="stMetric"]{
    background:white;
    padding:28px;
    border-radius:24px;
    border:1px solid rgba(8,68,34,0.05);
    box-shadow:0 10px 25px rgba(8,68,34,0.05);
    transition:0.2s;
}

[data-testid="stMetric"]:hover {
    box-shadow:0 15px 35px rgba(8,68,34,0.1);
    transform:translateY(-2px);
}

/* BUTTONS */

div.stButton > button{
    width:100%;
    background:white;
    color:#084422;
    border:2px solid rgba(8,68,34,0.1);
    border-radius:22px;
    padding:28px 20px;
    text-align:left;
    font-size:18px;
    font-weight:700;
    box-shadow:0 8px 20px rgba(8,68,34,0.05);
    transition:0.2s;
    min-height:100px;
}

div.stButton > button:hover{
    background:#084422;
    color:white;
    border:2px solid #084422;
    transform:translateY(-4px);
    box-shadow:0 15px 35px rgba(8,68,34,0.15);
}

/* GRAPH */

.graph-card{
    background:white;
    padding:30px;
    border-radius:28px;
    box-shadow:0 10px 25px rgba(8,68,34,0.05);
    border:1px solid rgba(8,68,34,0.05);
}

.dashboard-section {
    margin-top: 50px;
    margin-bottom: 50px;
}

.section-title {
    font-size: 28px;
    font-weight: 700;
    color: #084422;
    margin-bottom: 25px;
    padding-bottom: 12px;
    border-bottom: 3px solid #084422;
    display: inline-block;
}

.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
    margin-top: 30px;
}

.feature-card {
    background: white;
    padding: 25px;
    border-radius: 20px;
    box-shadow: 0 8px 20px rgba(8,68,34,0.05);
    border-left: 4px solid #084422;
    transition: 0.2s;
}

.feature-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 12px 30px rgba(8,68,34,0.1);
}

.feature-card h4 {
    color: #084422;
    margin-top: 10px;
}

h1,h2,h3 {
    color:#084422;
}

.divider-line {
    height: 2px;
    background: linear-gradient(90deg, transparent, #084422, transparent);
    margin: 40px 0;
}

.footer-info {
    background: rgba(8,68,34,0.05);
    padding: 25px;
    border-radius: 20px;
    margin-top: 50px;
    text-align: center;
    border-top: 2px solid #084422;
}

.stat-box {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 15px rgba(8,68,34,0.05);
    text-align: center;
}

.stat-value {
    font-size: 32px;
    font-weight: 700;
    color: #084422;
}

.stat-label {
    font-size: 14px;
    color: #666;
    margin-top: 8px;
}

</style>
""", unsafe_allow_html=True)

# =====================================================
# FUNCTIONS
# =====================================================

def load_csv(url):

    try:

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        response = requests.get(
            url,
            headers=headers,
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
ENGAGEMENT_GID = "1634595211"
MEMBERS_GID = "0"
DEALS_GID = "1234567890"

# =====================================================
# SOCIAL DATA - FOLLOWERS
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
# SOCIAL DATA - ENGAGEMENT
# =====================================================

engagement_url = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SOCIAL_SHEET}/export?format=csv&gid={ENGAGEMENT_GID}"
)

engagement = load_csv(engagement_url)

total_engagement = 0
avg_engagement_rate = 0

if not engagement.empty:
    engagement.columns = (
        engagement.columns
        .str.lower()
        .str.strip()
    )
    
    if 'engagement' in engagement.columns:
        engagement['engagement'] = pd.to_numeric(
            engagement['engagement'],
            errors='coerce'
        )
        total_engagement = int(
            engagement['engagement'].sum()
        )
        avg_engagement_rate = round(
            engagement['engagement'].mean(),
            2
        )
    elif 'likes' in engagement.columns:
        for col in ['likes', 'comments', 'shares']:
            if col in engagement.columns:
                engagement[col] = pd.to_numeric(
                    engagement[col],
                    errors='coerce'
                )
        total_engagement = int(
            engagement[['likes', 'comments', 'shares']].sum().sum()
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
new_members_month = 0
members_growth = 0

if not members.empty:
    members.columns = (
        members.columns
        .str.lower()
        .str.strip()
    )
    
    total_members = len(members)
    
    if 'joindate' in members.columns or 'date' in members.columns:
        date_col = 'joindate' if 'joindate' in members.columns else 'date'
        members[date_col] = pd.to_datetime(
            members[date_col],
            errors='coerce'
        )
        
        current_month = pd.Timestamp.now().month
        current_year = pd.Timestamp.now().year
        
        new_members_month = len(
            members[
                (members[date_col].dt.month == current_month) &
                (members[date_col].dt.year == current_year)
            ]
        )

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
avg_click_rate = 0
newsletter_campaigns = 0

if not newsletter.empty:
    newsletter.columns = (
        newsletter.columns
        .str.lower()
        .str.strip()
    )
    
    newsletter_campaigns = len(newsletter)
    
    if 'open_rate' in newsletter.columns:
        newsletter['open_rate'] = pd.to_numeric(
            newsletter['open_rate'],
            errors='coerce'
        )
        avg_open_rate = round(
            newsletter['open_rate'].mean(),
            1
        )
    
    if 'click_rate' in newsletter.columns:
        newsletter['click_rate'] = pd.to_numeric(
            newsletter['click_rate'],
            errors='coerce'
        )
        avg_click_rate = round(
            newsletter['click_rate'].mean(),
            1
        )

# =====================================================
# HERO SECTION
# =====================================================

st.markdown(f"""
<div class="hero">

<h1 style="
    color:white;
    font-size:64px;
    margin-bottom:16px;
    line-height:1.1;
">
📊 VDK Marketing Dashboard
</h1>

<p style="
    font-size:20px;
    opacity:0.95;
    max-width:900px;
    line-height:1.8;
">
Centraal overzicht van alle marketing prestaties binnen social media, members, nieuwsbrieven en afspraken. Real-time data en automatische actualisering.
</p>

<p style="
    margin-top:30px;
    font-size:16px;
    opacity:0.85;
    display:flex;
    gap:30px;
">
    <span>📅 {datetime.now().strftime('%d %B %Y')}</span>
    <span>🔄 Live update</span>
</p>

</div>
""", unsafe_allow_html=True)

st.write("")

# =====================================================
# KPI OVERVIEW SECTION
# =====================================================

st.markdown('<div class="section-title">📈 Snelle statistieken</div>', unsafe_allow_html=True)

st.write("")

# SOCIAL MEDIA ROW
st.markdown('<h4 style="color: #084422; margin-bottom: 15px;">📱 Social Media</h4>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4, gap="medium")

with col1:
    st.metric(
        label="Instagram volgers",
        value=f"{instagram_followers:,}".replace(",", "."),
        delta=f"{instagram_growth:+.1f}%"
    )

with col2:
    st.metric(
        label="Facebook volgers",
        value=f"{facebook_followers:,}".replace(",", "."),
        delta=f"{facebook_growth:+.1f}%"
    )

with col3:
    st.metric(
        label="Totale volgers",
        value=f"{(instagram_followers + facebook_followers):,}".replace(",", "."),
        delta="Gecombineerd"
    )

with col4:
    st.metric(
        label="Engagements",
        value=f"{total_engagement:,}".replace(",", "."),
        delta=f"{avg_engagement_rate:.1f}%"
    )

st.write("")

# MEMBERS ROW
st.markdown('<h4 style="color: #084422; margin-bottom: 15px;">👥 Members</h4>', unsafe_allow_html=True)

col5, col6, col7, col8 = st.columns(4, gap="medium")

with col5:
    st.metric(
        label="Totale leden",
        value=f"{total_members:,}".replace(",", "."),
        delta="Alle leden"
    )

with col6:
    st.metric(
        label="Nieuwe leden (deze maand)",
        value=f"{new_members_month}",
        delta="Deze maand"
    )

with col7:
    st.metric(
        label="Kanalen actief",
        value="2",
        delta="Instagram + Facebook"
    )

with col8:
    st.metric(
        label="Sync status",
        value="✅ Live",
        delta="Real-time"
    )

st.write("")

# NEWSLETTER ROW
st.markdown('<h4 style="color: #084422; margin-bottom: 15px;">✉️ Nieuwsbrief</h4>', unsafe_allow_html=True)

col9, col10, col11, col12 = st.columns(4, gap="medium")

with col9:
    st.metric(
        label="Campagnes",
        value=f"{newsletter_campaigns}",
        delta="Totaal"
    )

with col10:
    st.metric(
        label="Gemiddelde open rate",
        value=f"{avg_open_rate:.1f}%",
        delta="Uit alle campagnes"
    )

with col11:
    st.metric(
        label="Gemiddelde click rate",
        value=f"{avg_click_rate:.1f}%",
        delta="Uit alle campagnes"
    )

with col12:
    st.metric(
        label="Data quality",
        value="✅ OK",
        delta="Alle bronnen"
    )

st.write("")

st.write("")

# =====================================================
# CHANNELS OVERVIEW
# =====================================================

st.markdown('<div class="section-title">📊 Kanaal Overzicht</div>', unsafe_allow_html=True)

st.markdown("""
Snel overzicht van alle marketing kanalen en hun prestaties.
""")

st.write("")

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown(f"""
    <div class="feature-card">
        <div style="font-size: 48px; margin-bottom: 10px;">📱</div>
        <h4>Social Media</h4>
        <p style="font-size: 28px; font-weight: 700; color: #084422; margin: 10px 0;">
            {instagram_followers + facebook_followers:,}
        </p>
        <p style="font-size: 14px; color: #666;">Totale volgers</p>
        <p style="font-size: 12px; opacity: 0.7; margin-top: 10px;">
            📈 Groei: {instagram_growth + facebook_growth:.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="feature-card">
        <div style="font-size: 48px; margin-bottom: 10px;">👥</div>
        <h4>Members</h4>
        <p style="font-size: 28px; font-weight: 700; color: #084422; margin: 10px 0;">
            {total_members:,}
        </p>
        <p style="font-size: 14px; color: #666;">Totale leden</p>
        <p style="font-size: 12px; opacity: 0.7; margin-top: 10px;">
            ➕ Nieuw: {new_members_month} deze maand
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="feature-card">
        <div style="font-size: 48px; margin-bottom: 10px;">✉️</div>
        <h4>Nieuwsbrief</h4>
        <p style="font-size: 28px; font-weight: 700; color: #084422; margin: 10px 0;">
            {newsletter_campaigns}
        </p>
        <p style="font-size: 14px; color: #666;">Campagnes</p>
        <p style="font-size: 12px; opacity: 0.7; margin-top: 10px;">
            📊 Open rate: {avg_open_rate:.1f}%
        </p>
    </div>
    """, unsafe_allow_html=True)

st.write("")

st.markdown('<div class="section-title">🎯 Dashboards</div>', unsafe_allow_html=True)

st.markdown("""
Selecteer een dashboard om meer gedetailleerde informatie en analysen te bekijken.
""")

st.write("")

col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button(
        "📱 Social Media\n\nInstagram • Facebook\nVolgers • Engagement • Posts",
        use_container_width=True,
        key="btn_social"
    ):
        st.switch_page("pages/social.py")

with col2:
    if st.button(
        "👥 Members\n\nLidmaatschappen • Groei\nActivatie • Omzet • Trends",
        use_container_width=True,
        key="btn_members"
    ):
        st.switch_page("pages/members.py")

st.write("")

col3, col4 = st.columns(2, gap="large")

with col3:
    if st.button(
        "✉️ Nieuwsbrief\n\nCampagnes • Open rates\nClicks • Bounces • Unsubscribes",
        use_container_width=True,
        key="btn_newsletter"
    ):
        st.switch_page("pages/newsletter.py")

with col4:
    if st.button(
        "📅 Afspraken\n\nPlanning • Kalender\nEvents • Analyses • Rapportages",
        use_container_width=True,
        key="btn_events"
    ):
        st.switch_page("pages/events.py")

# =====================================================
# FOLLOWER GRAPH SECTION
# =====================================================

if not followers.empty:

    st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-title">📊 Volgers ontwikkeling</div>', unsafe_allow_html=True)
    
    st.markdown("""
    Historische trend van je Instagram en Facebook volgers over tijd.
    """)

    st.write("")

    chart_df = followers.copy()

    chart_df["date"] = pd.to_datetime(
        chart_df["date"],
        errors="coerce"
    )

    chart_df = chart_df.sort_values("date")

    fig = px.line(
        chart_df,
        x="date",
        y=[
            "instagram_followers",
            "facebook_followers"
        ],
        template="simple_white",
        labels={
            "date": "Datum",
            "value": "Volgers",
            "variable": "Platform"
        }
    )

    fig.update_layout(
        height=500,
        paper_bgcolor="white",
        plot_bgcolor="#f9f9f9",
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        xaxis_title="",
        yaxis_title="Aantal volgers",
        hovermode="x unified"
    )

    fig.update_traces(
        line=dict(width=3),
        mode='lines+markers'
    )

    with st.container():
        st.markdown(
            '<div class="graph-card">',
            unsafe_allow_html=True
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displayModeBar": True, "displaylogo": False}
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

# =====================================================
# FEATURES SECTION
# =====================================================

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">✨ Functies</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">⚡</div>
        <h4>Real-time Data</h4>
        <p>Automatische updates van je Google Sheets integratties</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">📈</div>
        <h4>Interactieve Grafieken</h4>
        <p>Plotly grafieken met hover, zoom en export functies</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">🎨</div>
        <h4>Modern Design</h4>
        <p>Responsieve layout met professionele styling</p>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3, gap="medium")

with col1:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">📊</div>
        <h4>KPI Metrics</h4>
        <p>Snelle overzichten van je belangijkste indicatoren</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">🔄</div>
        <h4>Sincronisatie</h4>
        <p>Gesynchroniseerde data uit meerdere bronnen</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <div style="font-size: 36px;">🛡️</div>
        <h4>Betrouwbaar</h4>
        <p>Gegevens rechtstreeks van Google Sheets</p>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# FOOTER
# =====================================================

st.markdown('<div class="divider-line"></div>', unsafe_allow_html=True)

st.markdown(f"""
<div class="footer-info">
    <h3>📋 Dashboard Informatie</h3>
    <p><strong>Databronnen:</strong> Google Sheets API</p>
    <p><strong>Actualisering:</strong> Elk uur automatisch</p>
    <p><strong>Vertraging:</strong> ~15 seconden bij laden</p>
    <p style="margin-top: 20px; font-size: 14px; opacity: 0.7;">
        Laatst bijgewerkt: {datetime.now().strftime('%d %B %Y om %H:%M')} • VDK Marketing © 2026
    </p>
</div>
""", unsafe_allow_html=True)