from __future__ import annotations

import html

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# -----------------------------------------------------------------------------
# PAGINA CONFIG
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

# PAS DEZE TABNAMEN AAN ALS NODIG
SHEET_URLS = {
    "overview": f"{BASE_URL}/overview",
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
# STYLING
# -----------------------------------------------------------------------------

def inject_style() -> None:
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
            margin-bottom: 8px;
        }

        .subtitle {
            color: #6f766f;
            font-size: 15px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 18px;
            padding: 24px;
            border: 1px solid rgba(8,68,34,0.07);
            box-shadow: 0 6px 18px rgba(8,68,34,0.03);
        }

        .space {
            height: 24px;
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
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


@st.cache_data(ttl=300)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            data = [data]

        return normalize_columns(pd.DataFrame(data))

    except Exception as error:
        st.error(f"Data kon niet geladen worden: {error}")
        return pd.DataFrame()


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    numeric_cols = [
        "sessies",
        "add_to_carts",
        "checkout_start",
        "aankopen",
        "omzet",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = parse_number(df[col])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    numeric_cols = [
        "view_item",
        "add_to_cart",
        "begin_checkout",
        "purchase",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = parse_number(df[col])

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


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator * 100


def get_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    days = PERIOD_OPTIONS[label]

    if days is None:
        return df

    max_date = df["date"].max()

    start_date = max_date - pd.Timedelta(days=days - 1)

    return df[df["date"] >= start_date]


def apply_plotly_layout(fig, height=450):
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(color="#084422"),
        margin=dict(l=20, r=20, t=60, b=20),
    )

    return fig


# -----------------------------------------------------------------------------
# STYLE
# -----------------------------------------------------------------------------

inject_style()

# -----------------------------------------------------------------------------
# DATA LADEN
# -----------------------------------------------------------------------------

with st.spinner("Dashboard laden..."):

    overview = clean_overview(
        load_sheet(SHEET_URLS["overview"])
    )

    funnel = clean_funnel(
        load_sheet(SHEET_URLS["funnel"])
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

overview_filtered = get_period_data(overview, period)

# -----------------------------------------------------------------------------
# KPI BEREKENINGEN
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

st.markdown('<div class="space"></div>', unsafe_allow_html=True)

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
# OVERZICHT
# -----------------------------------------------------------------------------

with tab1:

    col1, col2 = st.columns([2, 1])

    with col1:

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
            color="KPI",
            text_auto=".1f",
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

    with col2:

        st.markdown(
            """
            <div class="card">
                <h3>Focuspunten</h3>

                <ul>
                    <li>Checkout vereenvoudigen</li>
                    <li>Mobiele snelheid verbeteren</li>
                    <li>Sticky add-to-cart testen</li>
                    <li>Reviews prominenter maken</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# -----------------------------------------------------------------------------
# FUNNEL
# -----------------------------------------------------------------------------

with tab2:

    if not funnel.empty:

        funnel_df = pd.DataFrame(
            {
                "Stap": [
                    "Product bekeken",
                    "Add-to-cart",
                    "Checkout",
                    "Aankoop",
                ],
                "Aantal": [
                    funnel["view_item"].sum(),
                    funnel["add_to_cart"].sum(),
                    funnel["begin_checkout"].sum(),
                    funnel["purchase"].sum(),
                ],
            }
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
# SNELHEID
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
            value_vars=["mobile_speed", "desktop_speed"],
            var_name="Device",
            value_name="Score",
        )

        fig = px.bar(
            speed_long,
            x="Score",
            y="page",
            color="Device",
            orientation="h",
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
# ACTIES
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
                    "Mobiele performance verbeteren",
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

st.caption("Van Duinkerken · Website optimalisatiepilot")
