import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# ==========================================================
# PAGINA CONFIG
# ==========================================================

st.set_page_config(
    page_title="VDK Coupon Dashboard",
    page_icon="🎟️",
    layout="wide",
)

# ==========================================================
# STYLING
# ==========================================================

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"

st.markdown(
    f"""
<style>

.stApp {{
    background-color: {BACKGROUND};
}}

[data-testid="metric-container"] {{
    background: white;
    border-radius: 12px;
    padding: 15px;
}}

</style>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# DATA BRON
# ==========================================================

SHEET_ID = "199ipIJJARO8UjXjMcay33DNXz6mpui-oA2F43SE5Weg"

COUPON_URL = (
    f"https://opensheet.elk.sh/{SHEET_ID}/coupons"
)

# ==========================================================
# HELPERS
# ==========================================================


def normalize_columns(df):
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    return df


def parse_numeric(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False),
        errors="coerce",
    ).fillna(0)


@st.cache_data(ttl=300)
def load_data():

    response = requests.get(
        COUPON_URL,
        timeout=20,
    )

    response.raise_for_status()

    df = pd.DataFrame(
        response.json()
    )

    return normalize_columns(df)


def clean_data(df):

    numeric_cols = [
        "openstaand",
        "ingeleverd",
        "verlopen",
        "orders",
        "revenue",
    ]

    for col in numeric_cols:

        if col in df.columns:
            df[col] = parse_numeric(df[col])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce",
        )

    return df


# ==========================================================
# DATA
# ==========================================================

try:

    df = load_data()
    df = clean_data(df)

except Exception as e:

    st.error(
        f"Data kon niet geladen worden: {e}"
    )

    st.stop()

# ==========================================================
# FILTERS
# ==========================================================

st.sidebar.header("Filters")

coupon_options = (
    ["Alle coupons"]
    + sorted(
        df["coupon_code"]
        .fillna("")
        .astype(str)
        .str.strip()
        .loc[lambda x: x != ""]
        .unique()
        .tolist()
    )
)

selected_coupon = st.sidebar.selectbox(
    "Coupon",
    coupon_options,
)

if selected_coupon != "Alle coupons":

    df = df[
        df["coupon_code"] == selected_coupon
    ]

if (
    "date" in df.columns
    and df["date"].notna().any()
):

    start_date = df["date"].min().date()
    end_date = df["date"].max().date()

    selected_dates = st.sidebar.date_input(
        "Periode",
        value=(start_date, end_date),
    )

    if len(selected_dates) == 2:

        start, end = selected_dates

        df = df[
            df["date"].between(
                pd.Timestamp(start),
                pd.Timestamp(end),
            )
        ]

# ==========================================================
# KPI'S
# ==========================================================

total_openstaand = df["openstaand"].sum()
total_ingeleverd = df["ingeleverd"].sum()
total_verlopen = df["verlopen"].sum()

total_coupons = (
    total_openstaand
    + total_ingeleverd
    + total_verlopen
)

conversion_rate = (
    (total_ingeleverd / total_coupons) * 100
    if total_coupons > 0
    else 0
)

expiry_rate = (
    (total_verlopen / total_coupons) * 100
    if total_coupons > 0
    else 0
)

# ==========================================================
# TITEL
# ==========================================================

st.title("🎟️ Coupon Dashboard")

st.caption(
    "Inzicht in coupongebruik, conversie en verloop"
)

# ==========================================================
# KPI RIJ
# ==========================================================

c1, c2, c3, c4, c5 = st.columns(5)

c1.metric(
    "Openstaand",
    f"{total_openstaand:,.0f}"
)

c2.metric(
    "Gebruikt",
    f"{total_ingeleverd:,.0f}"
)

c3.metric(
    "Verlopen",
    f"{total_verlopen:,.0f}"
)

c4.metric(
    "Conversie",
    f"{conversion_rate:.1f}%"
)

c5.metric(
    "Verloop",
    f"{expiry_rate:.1f}%"
)

# ==========================================================
# RIJ 1
# ==========================================================

left, right = st.columns([1, 1])

# ----------------------------------------------------------
# FUNNEL
# ----------------------------------------------------------

with left:

    st.subheader("Coupon Funnel")

    funnel = go.Figure(
        go.Funnel(
            y=[
                "Openstaand",
                "Gebruikt",
                "Verlopen",
            ],
            x=[
                total_openstaand,
                total_ingeleverd,
                total_verlopen,
            ],
            marker=dict(
                color=[
                    "#6c757d",
                    "#198754",
                    "#dc3545",
                ]
            ),
        )
    )

    funnel.update_layout(
        height=400,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    st.plotly_chart(
        funnel,
        use_container_width=True,
    )

# ----------------------------------------------------------
# TREND
# ----------------------------------------------------------

with right:

    st.subheader(
        "Gebruikte coupons over tijd"
    )

    if (
        "date" in df.columns
        and df["date"].notna().any()
    ):

        trend = (
            df.groupby(
                "date",
                as_index=False,
            )
            .agg(
                ingeleverd=(
                    "ingeleverd",
                    "sum",
                )
            )
            .sort_values("date")
        )

        fig = px.line(
            trend,
            x="date",
            y="ingeleverd",
        )

        fig.update_traces(
            line_color=BRAND_GREEN,
            line_width=3,
        )

        fig.update_layout(
            height=400,
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

# ==========================================================
# RIJ 2
# ==========================================================

left, right = st.columns([1, 1])

summary = (
    df.groupby(
        "coupon_code",
        as_index=False,
    )
    .agg(
        openstaand=(
            "openstaand",
            "sum",
        ),
        ingeleverd=(
            "ingeleverd",
            "sum",
        ),
        verlopen=(
            "verlopen",
            "sum",
        ),
    )
)

summary["conversie"] = (
    summary["ingeleverd"]
    /
    (
        summary["openstaand"]
        + summary["ingeleverd"]
        + summary["verlopen"]
    )
    * 100
)

# ----------------------------------------------------------
# GEBRUIKT VS VERLOPEN
# ----------------------------------------------------------

with left:

    st.subheader(
        "Gebruik vs verloop"
    )

    chart_data = (
        summary.sort_values(
            "ingeleverd",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        chart_data,
        x="coupon_code",
        y=[
            "ingeleverd",
            "verlopen",
        ],
        barmode="stack",
        color_discrete_sequence=[
            "#198754",
            "#dc3545",
        ],
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Aantal",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ----------------------------------------------------------
# CONVERSIE PER COUPON
# ----------------------------------------------------------

with right:

    st.subheader(
        "Beste coupons"
    )

    top_conversion = (
        summary.sort_values(
            "conversie",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        top_conversion,
        y="coupon_code",
        x="conversie",
        orientation="h",
        color="conversie",
        color_continuous_scale="Greens",
    )

    fig.update_layout(
        height=450,
        yaxis_title="",
        xaxis_title="Conversie %",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ==========================================================
# INSIGHTS
# ==========================================================

st.subheader("Belangrijkste inzichten")

col1, col2, col3 = st.columns(3)

best_coupon = summary.loc[
    summary["conversie"].idxmax()
]

worst_coupon = summary.loc[
    summary["conversie"].idxmin()
]

most_used = summary.loc[
    summary["ingeleverd"].idxmax()
]

with col1:

    st.success(
        f"""
🏆 Beste coupon

{best_coupon['coupon_code']}

Conversie:
{best_coupon['conversie']:.1f}%
"""
    )

with col2:

    st.warning(
        f"""
⚠ Laagste conversie

{worst_coupon['coupon_code']}

Conversie:
{worst_coupon['conversie']:.1f}%
"""
    )

with col3:

    st.info(
        f"""
🔥 Meest gebruikt

{most_used['coupon_code']}

Gebruikt:
{most_used['ingeleverd']:,.0f}
"""
    )

# ==========================================================
# DATA
# ==========================================================

with st.expander("Bekijk ruwe data"):

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
    )
