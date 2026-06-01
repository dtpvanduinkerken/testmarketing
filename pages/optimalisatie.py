from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ============================================================
# PAGINA
# ============================================================

st.set_page_config(
    page_title="Pilotmonitor Website Optimalisatie",
    page_icon="📈",
    layout="wide",
)

# ============================================================
# PILOT CONFIG
# ============================================================

PILOT_START = pd.Timestamp("2026-05-28")
PILOT_END = pd.Timestamp("2026-06-28")

TARGETS = {
    "add_to_cart_rate": 6.0,
    "checkout_rate": 50.0,
    "purchase_rate": 60.0,
}

# ============================================================
# GOOGLE SHEETS
# ============================================================

SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "funnel": f"{BASE_URL}/funnel",
    "pagespeed": f"{BASE_URL}/page_speed",
}

# ============================================================
# KLEUREN
# ============================================================

COLORS = {
    "green": "#084422",
    "light_green": "#7d9b88",
    "gold": "#c9a646",
    "red": "#c76f6f",
    "background": "#f7f3ec",
    "muted": "#6f766f",
    "white": "#ffffff",
}

# ============================================================
# KPI DEFINITIES
# ============================================================

KPI_CONFIG = {
    "add_to_cart_rate": {
        "label": "Add-to-cart",
        "target": 6,
    },
    "checkout_rate": {
        "label": "Checkout start",
        "target": 50,
    },
    "purchase_rate": {
        "label": "Aankoopratio",
        "target": 60,
    },
}

# ============================================================
# STYLING
# ============================================================

st.markdown(
    """
<style>

html,
body,
[data-testid="stAppViewContainer"]{
    background:#f7f3ec;
    color:#084422;
}

.block-container{
    max-width:1500px;
    padding:32px 42px;
}

#MainMenu,
footer,
header{
    visibility:hidden;
}

.dashboard-title{
    font-size:42px;
    font-weight:800;
    color:#084422;
    margin-bottom:4px;
}

.dashboard-subtitle{
    color:#6f766f;
    font-size:15px;
    margin-bottom:12px;
}

.summary-card{
    background:white;
    border-radius:18px;
    padding:22px;
    border:1px solid rgba(8,68,34,.08);
    box-shadow:0 6px 18px rgba(8,68,34,.04);
    min-height:135px;
}

.summary-card h3{
    margin:0 0 10px 0;
    font-size:18px;
}

.summary-card p{
    margin:0;
    color:#6f766f;
    line-height:1.5;
}

.status-good{
    background:rgba(125,155,136,.20);
    color:#084422;
    padding:6px 12px;
    border-radius:999px;
    font-size:12px;
    font-weight:700;
}

.status-warning{
    background:rgba(201,166,70,.20);
    color:#7a5b00;
    padding:6px 12px;
    border-radius:999px;
    font-size:12px;
    font-weight:700;
}

.status-bad{
    background:rgba(199,111,111,.18);
    color:#8f3030;
    padding:6px 12px;
    border-radius:999px;
    font-size:12px;
    font-weight:700;
}

div[data-testid="stMetric"]{
    background:white;
    border-radius:18px;
    padding:18px;
    border:1px solid rgba(8,68,34,.08);
    box-shadow:0 6px 18px rgba(8,68,34,.03);
}

</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    return df


def parse_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    return pd.to_numeric(
        cleaned,
        errors="coerce"
    ).fillna(0)


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float) -> str:
    return f"€ {format_number(value)}"


def format_delta_pp(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f} pp".replace(".", ",")

# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:

    try:

        response = requests.get(
            url,
            timeout=20,
        )

        response.raise_for_status()

        data = response.json()

        if isinstance(data, dict):
            data = [data]

        return normalize_columns(
            pd.DataFrame(data)
        )

    except Exception as error:

        st.warning(
            f"Data kon niet geladen worden: {error}"
        )

        return pd.DataFrame()

# ============================================================
# CLEANING
# ============================================================

def clean_overview(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    numeric_cols = [
        "omzet",
        "orders",
        "bezoekers",
        "sessies",
        "conversie",
        "add_to_carts",
        "checkout_start",
        "aankopen",
        "gemiddelde_orderwaarde",
    ]

    for col in numeric_cols:

        if col in df.columns:
            df[col] = parse_number(df[col])

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce",
    )

    df = (
        df.dropna(subset=["date"])
        .sort_values("date")
    )

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    df = df.rename(
        columns={
            "stap": "Stap",
            "aantal": "Aantal",
        }
    )

    df["Aantal"] = parse_number(df["Aantal"])

    return df


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

    df = df.rename(
        columns={
            "pagina": "page"
        }
    )

    for col in [
        "mobile_speed",
        "desktop_speed",
    ]:

        if col in df.columns:
            df[col] = parse_number(df[col])

    return df

# ============================================================
# KPI BEREKENINGEN
# ============================================================

def safe_sum(df: pd.DataFrame, column: str) -> float:

    if column not in df.columns:
        return 0

    return float(df[column].sum())


def safe_rate(
    numerator: float,
    denominator: float,
) -> float:

    if denominator <= 0:
        return 0

    return (
        numerator
        / denominator
        * 100
    )


def calculate_kpis(
    df: pd.DataFrame,
) -> dict[str, float]:

    sessions = safe_sum(df, "sessies")
    add_to_carts = safe_sum(df, "add_to_carts")
    checkout_start = safe_sum(df, "checkout_start")
    purchases = safe_sum(df, "aankopen")
    revenue = safe_sum(df, "omzet")

    return {
        "sessions": sessions,
        "add_to_carts": add_to_carts,
        "checkout_start": checkout_start,
        "purchases": purchases,
        "revenue": revenue,
        "add_to_cart_rate":
            safe_rate(add_to_carts, sessions),
        "checkout_rate":
            safe_rate(checkout_start, add_to_carts),
        "purchase_rate":
            safe_rate(purchases, checkout_start),
        "conversion_rate":
            safe_rate(purchases, sessions),
    }

# ============================================================
# PILOT LOGICA
# ============================================================

def get_pilot_progress() -> float:

    today = min(
        pd.Timestamp.today().normalize(),
        PILOT_END,
    )

    progress = (
        (today - PILOT_START).days
        / (PILOT_END - PILOT_START).days
    )

    return max(
        0,
        min(progress, 1),
    )


def goal_progress(
    baseline: float,
    current: float,
    target: float,
) -> float:

    if target == baseline:
        return 100

    progress = (
        (current - baseline)
        / (target - baseline)
    ) * 100

    return max(
        0,
        min(progress, 100),
    )

# ============================================================
# DATA LADEN
# ============================================================

with st.spinner("Dashboard laden..."):

    overview = clean_overview(
        load_sheet(
            SHEET_URLS["overview"]
        )
    )

    funnel = clean_funnel(
        load_sheet(
            SHEET_URLS["funnel"]
        )
    )

    pagespeed = clean_pagespeed(
        load_sheet(
            SHEET_URLS["pagespeed"]
        )
    )

# ============================================================
# PILOT DATASETS
# ============================================================

baseline_df = overview[
    overview["date"] < PILOT_START
]

pilot_df = overview[
    overview["date"] >= PILOT_START
]

baseline_kpis = calculate_kpis(
    baseline_df
)

pilot_kpis = calculate_kpis(
    pilot_df
)

# ============================================================
# HEADER
# ============================================================

pilot_progress = get_pilot_progress()

today = min(
    pd.Timestamp.today().normalize(),
    PILOT_END,
)

current_day = (
    today - PILOT_START
).days + 1

total_days = (
    PILOT_END - PILOT_START
).days + 1

st.markdown(
    """
    <div class="dashboard-title">
        Pilotmonitor Website Optimalisatie
    </div>

    <div class="dashboard-subtitle">
        Voor pilot → Huidige situatie → Doel 28 juni
    </div>
    """,
    unsafe_allow_html=True,
)

st.progress(pilot_progress)

st.caption(
    f"Pilotperiode: 28 mei 2026 t/m 28 juni 2026 "
    f"• Dag {current_day} van {total_days}"
)

# ============================================================
# STATUS
# ============================================================

achieved = 0

for kpi_key, target in TARGETS.items():

    if pilot_kpis[kpi_key] >= target:
        achieved += 1

if achieved == 3:
    status_title = "🟢 Pilot op koers"
    status_text = (
        "Alle KPI-doelen zijn gehaald."
    )

elif achieved == 2:
    status_title = "🟡 Pilot ontwikkelt positief"
    status_text = (
        "Meerdere KPI's liggen op schema."
    )

else:
    status_title = "🔴 Aandacht nodig"
    status_text = (
        "Meerdere KPI's liggen onder doel."
    )

# ============================================================
# SAMENVATTING
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.markdown(
        f"""
        <div class="summary-card">
            <h3>{status_title}</h3>
            <p>{status_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:

    st.metric(
        "Pilotomzet",
        format_currency(
            pilot_kpis["revenue"]
        )
    )

with col3:

    st.metric(
        "Orders",
        format_number(
            pilot_kpis["purchases"]
        )
    )

with col4:

    aov = (
        pilot_kpis["revenue"]
        / pilot_kpis["purchases"]
        if pilot_kpis["purchases"] > 0
        else 0
    )

    st.metric(
        "Gem. orderwaarde",
        format_currency(aov)
    )

st.divider()

# ============================================================
# KPI KAARTEN
# ============================================================

metric_cols = st.columns(3)

for col, (
    key,
    config,
) in zip(
    metric_cols,
    KPI_CONFIG.items(),
):

    baseline = baseline_kpis[key]
    current = pilot_kpis[key]
    target = config["target"]

    progress = goal_progress(
        baseline,
        current,
        target,
    )

    with col:

        st.metric(
            config["label"],
            format_percent(current),
            format_delta_pp(
                current - baseline
            ),
        )

        st.progress(progress / 100)

        st.caption(
            f"Voor pilot: "
            f"{baseline:.1f}%"
        )

        st.caption(
            f"Doel: "
            f"{target:.1f}%"
        )

st.divider()

# ============================================================
# TABS
# ============================================================

(
    tab_summary,
    tab_impact,
    tab_funnel,
    tab_speed,
    tab_actions,
    tab_trend,
) = st.tabs(
    [
        "Pilot Samenvatting",
        "Pilot Impact",
        "Funnel",
        "Snelheid",
        "Acties",
        "Trend",
    ]
)

# ============================================================
# TAB SAMENVATTING
# ============================================================

with tab_summary:

    comparison_df = pd.DataFrame(
        {
            "KPI": [
                "Add-to-cart",
                "Checkout",
                "Purchase",
            ],
            "Voor pilot": [
                baseline_kpis[
                    "add_to_cart_rate"
                ],
                baseline_kpis[
                    "checkout_rate"
                ],
                baseline_kpis[
                    "purchase_rate"
                ],
            ],
            "Nu": [
                pilot_kpis[
                    "add_to_cart_rate"
                ],
                pilot_kpis[
                    "checkout_rate"
                ],
                pilot_kpis[
                    "purchase_rate"
                ],
            ],
            "Doel": [
                6,
                50,
                60,
            ],
        }
    )

    chart_df = comparison_df.melt(
        id_vars="KPI",
        var_name="Type",
        value_name="Percentage",
    )

    fig = px.bar(
        chart_df,
        x="KPI",
        y="Percentage",
        color="Type",
        barmode="group",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# TAB IMPACT
# ============================================================

with tab_impact:

    impact_df = comparison_df.copy()

    impact_df["Verschil"] = (
        impact_df["Nu"]
        - impact_df["Voor pilot"]
    )

    st.dataframe(
        impact_df,
        use_container_width=True,
        hide_index=True,
    )

# ============================================================
# TAB FUNNEL
# ============================================================

with tab_funnel:

    st.subheader(
        "Conversiefunnel"
    )

    if not funnel.empty:

        fig = px.funnel(
            funnel,
            x="Aantal",
            y="Stap",
            color_discrete_sequence=[
                COLORS["green"]
            ],
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.dataframe(
            funnel,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# TAB SPEED
# ============================================================

with tab_speed:

    st.subheader(
        "Pagespeed"
    )

    if not pagespeed.empty:

        fig = px.bar(
            pagespeed,
            x="mobile_speed",
            y="page",
            orientation="h",
            color="mobile_speed",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.dataframe(
            pagespeed,
            use_container_width=True,
            hide_index=True,
        )

# ============================================================
# TAB ACTIES
# ============================================================

with tab_actions:

    if "tasks" not in st.session_state:

        st.session_state.tasks = (
            pd.DataFrame(
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
                        "Product",
                        "Sticky add-to-cart testen",
                        "Open",
                        "Hoog",
                    ],
                ],
                columns=[
                    "Onderdeel",
                    "Taak",
                    "Status",
                    "Prioriteit",
                ],
            )
        )

    st.session_state.tasks = (
        st.data_editor(
            st.session_state.tasks,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )
    )

# ============================================================
# TAB TREND
# ============================================================

with tab_trend:

    trend_df = (
        overview.copy()
    )

    trend_df[
        "add_to_cart_rate"
    ] = trend_df.apply(
        lambda row:
        safe_rate(
            row["add_to_carts"],
            row["sessies"],
        ),
        axis=1,
    )

    trend_df[
        "checkout_rate"
    ] = trend_df.apply(
        lambda row:
        safe_rate(
            row["checkout_start"],
            row["add_to_carts"],
        ),
        axis=1,
    )

    trend_df[
        "purchase_rate"
    ] = trend_df.apply(
        lambda row:
        safe_rate(
            row["aankopen"],
            row["checkout_start"],
        ),
        axis=1,
    )

    trend_long = trend_df.melt(
        id_vars="date",
        value_vars=[
            "add_to_cart_rate",
            "checkout_rate",
            "purchase_rate",
        ],
        var_name="KPI",
        value_name="Percentage",
    )

    fig = px.line(
        trend_long,
        x="date",
        y="Percentage",
        color="KPI",
        markers=True,
    )

    fig.add_vline(
        x=PILOT_START,
        line_dash="dash",
        line_color="red",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ============================================================
# FOOTER
# ============================================================

st.caption(
    "Van Duinkerken · Website optimalisatiepilot"
)
