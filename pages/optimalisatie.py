from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# -----------------------------------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------------------------------

st.set_page_config(
    page_title="Pilotmonitor website optimalisatie",
    page_icon="📈",
    layout="wide",
)

# -----------------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------------

SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"

BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "funnel": f"{BASE_URL}/funnel",
    "pagespeed": f"{BASE_URL}/page_speed",
}

COLORS = {
    "green": "#084422",
    "light_green": "#7d9b88",
    "gold": "#c9a646",
    "red": "#c76f6f",
    "background": "#f7f3ec",
    "muted": "#6f766f",
}

PERIOD_OPTIONS = {
    "Afgelopen 7 dagen": 7,
    "Afgelopen 30 dagen": 30,
    "Afgelopen 90 dagen": 90,
    "Alles": None,
}

# -----------------------------------------------------------------------------
# STYLE
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #f7f3ec;
        color: #084422;
    }

    .block-container {
        padding: 40px;
        max-width: 1500px;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    .title {
        font-size: 42px;
        font-weight: 700;
        color: #084422;
        margin-bottom: 10px;
    }

    .subtitle {
        color: #6f766f;
        font-size: 15px;
        margin-bottom: 35px;
    }

    div[data-testid="stMetric"] {
        background: white;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid rgba(8,68,34,0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# HELPERS
# -----------------------------------------------------------------------------

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
    )
    return df


def parse_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    ).fillna(0)


@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            data = [data]

        df = pd.DataFrame(data)

        return normalize_columns(df)

    except Exception as error:
        st.error(f"Data kon niet geladen worden: {error}")
        return pd.DataFrame()


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    cols = [
        "sessies",
        "add_to_carts",
        "checkout_start",
        "aankopen",
        "omzet",
    ]

    for col in cols:
        if col in df.columns:
            df[col] = parse_number(df[col])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "pagina" in df.columns:
        df = df.rename(columns={"pagina": "page"})

    for col in ["mobile_speed", "desktop_speed"]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    return df


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator * 100


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def apply_plotly_layout(fig, height=450):
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(color="#084422"),
    )

    return fig


def get_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    days = PERIOD_OPTIONS[label]

    if days is None:
        return df

    max_date = df["date"].max()

    start_date = max_date - pd.Timedelta(days=days - 1)

    return df[df["date"] >= start_date]


# -----------------------------------------------------------------------------
# LOAD DATA
# -----------------------------------------------------------------------------

with st.spinner("Dashboard laden..."):

    overview = clean_overview(
        load_sheet(SHEET_URLS["overview"])
    )

    funnel = load_sheet(
        SHEET_URLS["funnel"]
    )

    pagespeed = clean_pagespeed(
        load_sheet(SHEET_URLS["pagespeed"])
    )

# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------

st.sidebar.title("Website optimalisatie")

period = st.sidebar.radio(
    "Meetperiode",
    list(PERIOD_OPTIONS.keys()),
    index=1,
)

if st.sidebar.button("Data verversen"):
    st.cache_data.clear()
    st.rerun()

overview_filtered = get_period_data(
    overview,
    period,
)

# -----------------------------------------------------------------------------
# KPI CALCULATIONS
# -----------------------------------------------------------------------------

sessions = overview_filtered["sessies"].sum() if "sessies" in overview_filtered.columns else 0

add_to_carts = overview_filtered["add_to_carts"].sum() if "add_to_carts" in overview_filtered.columns else 0

checkout_start = overview_filtered["checkout_start"].sum() if "checkout_start" in overview_filtered.columns else 0

purchases = overview_filtered["aankopen"].sum() if "aankopen" in overview_filtered.columns else 0

revenue = overview_filtered["omzet"].sum() if "omzet" in overview_filtered.columns else 0

add_to_cart_rate = safe_rate(add_to_carts, sessions)

checkout_rate = safe_rate(checkout_start, add_to_carts)

purchase_rate = safe_rate(purchases, checkout_start)

# -----------------------------------------------------------------------------
# HEADER
# -----------------------------------------------------------------------------

st.markdown(
    """
    <div class="title">
        Pilotmonitor website optimalisatie
    </div>

    <div class="subtitle">
        Dashboard voor monitoring van conversie, funnel, snelheid en optimalisaties.
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# KPI CARDS
# -----------------------------------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Add-to-cart",
    format_percent(add_to_cart_rate),
)

col2.metric(
    "Checkout start",
    format_percent(checkout_rate),
)

col3.metric(
    "Aankoopratio",
    format_percent(purchase_rate),
)

col4.metric(
    "Omzet",
    f"€ {format_number(revenue)}",
)

# -----------------------------------------------------------------------------
# TABS
# -----------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "Overzicht",
        "Funnel",
        "Snelheid",
        "Acties",
    ]
)

# -----------------------------------------------------------------------------
# OVERVIEW TAB
# -----------------------------------------------------------------------------

with tab1:

    goal_df = pd.DataFrame(
        {
            "KPI": [
                "Add-to-cart",
                "Checkout start",
                "Aankoopratio",
            ],
            "Score": [
                add_to_cart_rate,
                checkout_rate,
                purchase_rate,
            ],
        }
    )

    fig = px.bar(
        goal_df,
        x="KPI",
        y="Score",
        text_auto=".1f",
        color="KPI",
    )

    fig.update_traces(
        marker_color=COLORS["green"]
    )

    fig.update_layout(
        title="KPI prestaties",
        showlegend=False,
    )

    st.plotly_chart(
        apply_plotly_layout(fig),
        use_container_width=True,
    )

# -----------------------------------------------------------------------------
# FUNNEL TAB
# -----------------------------------------------------------------------------

with tab2:

    st.subheader("Conversiefunnel")

    if not funnel.empty and {"stap", "aantal"}.issubset(funnel.columns):

        funnel_df = funnel.rename(
            columns={
                "stap": "Stap",
                "aantal": "Aantal",
            }
        )

        funnel_df["Aantal"] = parse_number(
            funnel_df["Aantal"]
        )

    else:

        funnel_df = pd.DataFrame(
            {
                "Stap": [
                    "Sessies",
                    "Add-to-cart",
                    "Checkout",
                    "Aankoop",
                ],
                "Aantal": [
                    sessions,
                    add_to_carts,
                    checkout_start,
                    purchases,
                ],
            }
        )

    fig = px.funnel(
        funnel_df,
        x="Aantal",
        y="Stap",
        color_discrete_sequence=[COLORS["green"]],
    )

    st.plotly_chart(
        apply_plotly_layout(fig, 520),
        use_container_width=True,
    )

    st.dataframe(
        funnel_df,
        use_container_width=True,
        hide_index=True,
    )

# -----------------------------------------------------------------------------
# SPEED TAB
# -----------------------------------------------------------------------------

with tab3:

    required_cols = {
        "page",
        "mobile_speed",
        "desktop_speed",
    }

    if pagespeed.empty or not required_cols.issubset(pagespeed.columns):

        st.warning("Geen pagespeed data gevonden.")

    else:

        speed_long = pagespeed.melt(
            id_vars="page",
            value_vars=[
                "mobile_speed",
                "desktop_speed",
            ],
            var_name="Device",
            value_name="Score",
        )

        fig = px.bar(
            speed_long,
            x="Score",
            y="page",
            orientation="h",
            color="Device",
            barmode="group",
            color_discrete_sequence=[
                COLORS["red"],
                COLORS["green"],
            ],
        )

        st.plotly_chart(
            apply_plotly_layout(fig, 600),
            use_container_width=True,
        )

        st.dataframe(
            pagespeed,
            use_container_width=True,
            hide_index=True,
        )

# -----------------------------------------------------------------------------
# ACTIONS TAB
# -----------------------------------------------------------------------------

with tab4:

    if "tasks" not in st.session_state:

        st.session_state.tasks = pd.DataFrame(
            [
                [
                    "Checkout",
                    "Checkout vereenvoudigen",
                    "Open",
                    "Hoog",
                ],
                [
                    "Snelheid",
                    "Mobiele snelheid verbeteren",
                    "Bezig",
                    "Hoog",
                ],
                [
                    "Productpagina",
                    "Sticky add-to-cart testen",
                    "Open",
                    "Midden",
                ],
            ],
            columns=[
                "Onderdeel",
                "Taak",
                "Status",
                "Prioriteit",
            ],
        )

    st.session_state.tasks = st.data_editor(
        st.session_state.tasks,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
    )

# -----------------------------------------------------------------------------
# FOOTER
# -----------------------------------------------------------------------------

st.caption(
    "Van Duinkerken · Website optimalisatiepilot"
)
