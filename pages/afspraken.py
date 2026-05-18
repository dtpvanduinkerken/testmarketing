import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Afspraken",
    layout="wide",
)

STYLE = """
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>

html, body, [data-testid="stAppViewContainer"]{
    background:#f6f1e7;
    font-family:'sofia-pro', sans-serif;
}

.block-container{
    padding-top:30px;
    padding-left:55px;
    padding-right:55px;
    padding-bottom:40px;
    max-width:1700px;
}

.dashboard-title{
    font-size:58px;
    font-weight:700;
    color:#084422;
}

/* KPI CARDS */

[data-testid="metric-container"]{
    background:#ffffff;
    border-radius:24px;
    padding:22px;
    box-shadow:0 8px 25px rgba(0,0,0,0.04);
    border:none;
}

[data-testid="metric-container"] label{
    color:#8a8a8a !important;
    font-size:14px !important;
}

[data-testid="metric-container"] [data-testid="stMetricValue"]{
    color:#084422;
    font-size:34px;
    font-weight:700;
}

/* TABLE */

thead tr th{
    background-color:#084422 !important;
    color:white !important;
}

tbody tr:nth-child(even){
    background-color:#f9f3e9;
}

tbody tr:hover{
    background-color:#eef5ea;
}

</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)

# =====================================================
# HEADER
# =====================================================

col1, col2, col3 = st.columns([2,2,1])

with col1:
    st.title("Afspraken")

with col3:
    st.text(
        f"{datetime.now().strftime('%d %B %Y')}"
    )

# =====================================================
# SHEET
# =====================================================

SHEET_ID = "1ahFKg-OOJaczjYx2dt4USJzx54nCB4olWB-cWDp4yzA"

OPEN_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=0"
)

# =====================================================
# DATA
# =====================================================

@st.cache_data(ttl=30)
def load_data():

    try:
        df = pd.read_csv(OPEN_SHEET_URL)

    except Exception as exc:
        st.error(f"Kan data niet laden: {exc}")
        return pd.DataFrame()

    # ===== KOLOMMEN OPSCHONEN =====

    df.columns = (
        df.columns
        .str.strip()
    )

    # ===== DATUM =====

    df["Datum"] = pd.to_datetime(
        df["Datum"],
        dayfirst=True,
        errors="coerce"
    )

    # ===== ANNULERING =====

    df["Is geannuleerd"] = (
        df["Is geannuleerd"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map({
            "ja": True,
            "nee": False
        })
        .fillna(False)
    )

    return df

df = load_data()

# =====================================================
# KPI DATA
# =====================================================

if not df.empty:

    total = len(df)

    canceled = int(
        df["Is geannuleerd"].sum()
    )

    cancel_rate = (
        round((canceled / total) * 100, 1)
        if total else 0
    )

    # ===== ALLEEN ACTIEVE AFSPRAKEN =====

    df_active = (
        df[df["Is geannuleerd"] == False]
        .copy()
    )

    df_active = (
        df_active[df_active["Datum"].notna()]
    )

    latest_week = 0
    growth = 0

    # =====================================================
    # WEEK DATA
    # =====================================================

    if not df_active.empty:

        df_active["Week_start"] = (
            df_active["Datum"]
            - pd.to_timedelta(
                df_active["Datum"].dt.weekday,
                unit="d"
            )
        )

        weekly = (
            df_active
            .groupby("Week_start")
            .size()
            .reset_index(name="Aantal")
            .sort_values("Week_start")
        )

        weekly["Groei %"] = (
            weekly["Aantal"]
            .pct_change()
            * 100
        )

        weekly["Groei %"] = (
            weekly["Groei %"]
            .fillna(0)
            .round(1)
        )

        # ===== HUIDIGE WEEK =====

        current_week_start = (
            pd.Timestamp.today().normalize()
            - pd.to_timedelta(
                pd.Timestamp.today().weekday(),
                unit="d"
            )
        )

        current_week_data = weekly[
            weekly["Week_start"]
            == current_week_start
        ]

        if not current_week_data.empty:

            latest_week = int(
                current_week_data["Aantal"].iloc[0]
            )

            growth = float(
                current_week_data["Groei %"].iloc[0]
            )

        else:

            latest_week = int(
                weekly["Aantal"].iloc[-1]
            )

            growth = float(
                weekly["Groei %"].iloc[-1]
            )

# =====================================================
# KPI CARDS
# =====================================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Afspraken totaal",
        f"{total:,}".replace(",", ".")
    )

with col2:
    st.metric(
        "Geannuleerd",
        f"{canceled:,}".replace(",", ".")
    )

with col3:
    st.metric(
        "Annuleringsratio",
        f"{cancel_rate}%"
    )

with col4:
    st.metric(
        "Laatste week",
        f"{latest_week:,}".replace(",", "."),
        f"{growth}%"
    )

# =====================================================
# WEEK OVERZICHT
# =====================================================

st.divider()

st.subheader("Week overzicht")

if not df_active.empty:

    weekly_display = weekly.copy()

    weekly_display["Week_label"] = (
        "Week "
        + weekly_display["Week_start"]
        .dt.isocalendar()
        .week.astype(str)
    )

    fig_week = px.bar(
        weekly_display,
        x="Week_label",
        y="Aantal",
        text="Aantal",
    )

    fig_week.update_traces(
        marker_color="#084422",
        textposition="outside",
        hovertemplate=
        "<b>%{x}</b><br>"
        "Afspraken: %{y}<br>"
        "Groei: %{customdata[0]}%<extra></extra>",
        customdata=weekly_display[["Groei %"]]
    )

    fig_week.update_layout(
        height=420,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        showlegend=False,
        xaxis_title="",
        yaxis_title="Aantal afspraken",
        margin=dict(t=30, l=20, r=20, b=20),
    )

    fig_week.update_xaxes(
        showgrid=False
    )

    fig_week.update_yaxes(
        showgrid=True,
        gridcolor="#ececf3"
    )

    st.plotly_chart(
        fig_week,
        use_container_width=True
    )

# =====================================================
# AFDELINGEN DIAGRAM
# =====================================================

st.divider()

st.subheader("Afspraken per afdeling")

if (
    not df_active.empty and
    "Dienst-categorie" in df_active.columns
):

    afdeling_data = (
        df_active
        .groupby("Dienst-categorie")
        .size()
        .reset_index(name="Aantal")
        .sort_values("Aantal", ascending=False)
    )

    fig_afdeling = px.pie(
        afdeling_data,
        names="Dienst-categorie",
        values="Aantal",
        hole=0.45
    )

    fig_afdeling.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=
        "<b>%{label}</b><br>"
        "Afspraken: %{value}<br>"
        "Percentage: %{percent}<extra></extra>"
    )

    fig_afdeling.update_layout(
        height=500,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        showlegend=False,
        margin=dict(t=30, l=20, r=20, b=20),
    )

    st.plotly_chart(
        fig_afdeling,
        use_container_width=True
    )