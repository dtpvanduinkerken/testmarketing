import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ==========================================================
# PAGINA CONFIG
# ==========================================================

st.set_page_config(
    page_title="Coupon Dashboard",
    page_icon="🎟️",
    layout="wide",
)

# ==========================================================
# KLEUREN
# ==========================================================

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"

# ==========================================================
# STYLING
# ==========================================================

st.markdown(
    """
    <style>

    .stMetric {
        background-color: white;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #e8e8e8;
    }

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
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
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
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    return normalize_columns(df)


def clean_data(df):

    numeric_cols = [
        "verzonden",
        "openstaand",
        "ingeleverd",
        "verlopen",
        "discount",
        "omzet",
    ]

    for col in numeric_cols:

        if col in df.columns:
            df[col] = parse_numeric(df[col])
        else:
            df[col] = 0

    if "datum" in df.columns:

        df["datum"] = pd.to_datetime(
            df["datum"],
            errors="coerce",
            dayfirst=True,
        )

    return df


# ==========================================================
# DATA LADEN
# ==========================================================

try:

    df = load_data()
    df = clean_data(df)

except Exception as error:

    st.error(
        f"Data kon niet geladen worden: {error}"
    )

    st.stop()

if df.empty:

    st.warning(
        "Geen data gevonden."
    )

    st.stop()

# ==========================================================
# FILTERS
# ==========================================================

st.sidebar.title("🎟️ Coupons")

campagnes = (
    ["Alle campagnes"]
    + sorted(
        df["campagne"]
        .dropna()
        .unique()
        .tolist()
    )
)

selected_campaign = st.sidebar.selectbox(
    "Campagne",
    campagnes,
)

if selected_campaign != "Alle campagnes":

    df = df[
        df["campagne"] == selected_campaign
    ]

coupon_codes = (
    ["Alle coupons"]
    + sorted(
        df["coupon_code"]
        .dropna()
        .unique()
        .tolist()
    )
)

selected_coupon = st.sidebar.selectbox(
    "Coupon",
    coupon_codes,
)

if selected_coupon != "Alle coupons":

    df = df[
        df["coupon_code"] == selected_coupon
    ]

if df["datum"].notna().any():

    min_date = df["datum"].min().date()
    max_date = df["datum"].max().date()

    selected_dates = st.sidebar.date_input(
        "Periode",
        value=(min_date, max_date),
    )

    if len(selected_dates) == 2:

        start_date, end_date = selected_dates

        df = df[
            df["datum"].between(
                pd.Timestamp(start_date),
                pd.Timestamp(end_date),
            )
        ]

# ==========================================================
# SAMENVATTING PER COUPON
# ==========================================================

summary = (
    df.groupby(
        ["coupon_code", "campagne"],
        as_index=False,
    )
    .agg(
        verzonden=("verzonden", "sum"),
        openstaand=("openstaand", "sum"),
        ingeleverd=("ingeleverd", "sum"),
        verlopen=("verlopen", "sum"),
        discount=("discount", "sum"),
        omzet=("omzet", "sum"),
    )
)

summary["conversie"] = (
    summary["ingeleverd"]
    .div(summary["verzonden"].replace(0, pd.NA))
    .mul(100)
).fillna(0)

summary["verloop_percentage"] = (
    summary["verlopen"]
    .div(summary["verzonden"].replace(0, pd.NA))
    .mul(100)
).fillna(0)

summary["roi"] = (
    summary["omzet"]
    .div(summary["discount"].replace(0, pd.NA))
).fillna(0)

# ==========================================================
# KPI'S
# ==========================================================

total_verzonden = summary["verzonden"].sum()
total_openstaand = summary["openstaand"].sum()
total_ingeleverd = summary["ingeleverd"].sum()
total_verlopen = summary["verlopen"].sum()

total_discount = summary["discount"].sum()
total_omzet = summary["omzet"].sum()

conversion_rate = (
    total_ingeleverd / total_verzonden * 100
    if total_verzonden > 0
    else 0
)

expiry_rate = (
    total_verlopen / total_verzonden * 100
    if total_verzonden > 0
    else 0
)

roi_total = (
    total_omzet / total_discount
    if total_discount > 0
    else 0
)

# ==========================================================
# TITEL
# ==========================================================

st.title("🎟️ Coupon Dashboard")

st.caption(
    "Inzicht in couponprestaties, omzet en ROI"
)

# ==========================================================
# KPI CARDS
# ==========================================================

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Verzonden",
        f"{total_verzonden:,.0f}"
    )

with c2:
    st.metric(
        "Ingeleverd",
        f"{total_ingeleverd:,.0f}"
    )

with c3:
    st.metric(
        "Conversie",
        f"{conversion_rate:.1f}%"
    )

with c4:
    st.metric(
        "Omzet",
        f"€ {total_omzet:,.0f}"
    )

c5, c6, c7 = st.columns(3)

with c5:
    st.metric(
        "Openstaand",
        f"{total_openstaand:,.0f}"
    )

with c6:
    st.metric(
        "Verlopen",
        f"{total_verlopen:,.0f}"
    )

with c7:
    st.metric(
        "ROI",
        f"{roi_total:.2f}x"
    )

st.markdown("---")

# ==========================================================
# GRAFIEKEN RIJ 1
# ==========================================================

left, right = st.columns(2)

# ----------------------------------------------------------
# STATUS VERDELING
# ----------------------------------------------------------

with left:

    st.subheader("Status verdeling")

    status_df = pd.DataFrame(
        {
            "Status": [
                "Ingeleverd",
                "Verlopen",
                "Openstaand",
            ],
            "Aantal": [
                total_ingeleverd,
                total_verlopen,
                total_openstaand,
            ],
        }
    )

    fig = px.bar(
        status_df,
        x="Aantal",
        y="Status",
        orientation="h",
        color="Status",
        color_discrete_map={
            "Ingeleverd": "#084422",
            "Verlopen": "#c9654b",
            "Openstaand": "#cfd7d1",
        },
    )

    fig.update_layout(
        height=450,
        showlegend=False,
        plot_bgcolor="white",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ----------------------------------------------------------
# OMZET PER COUPON
# ----------------------------------------------------------

with right:

    st.subheader("Top omzet per coupon")

    omzet_chart = (
        summary
        .sort_values(
            "omzet",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        omzet_chart,
        x="coupon_code",
        y="omzet",
        color="omzet",
        color_continuous_scale=[
            "#dce7e1",
            "#084422",
        ],
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Omzet (€)",
        coloraxis_showscale=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.markdown("---")

# ==========================================================
# GRAFIEKEN RIJ 2
# ==========================================================

left, right = st.columns(2)

# ----------------------------------------------------------
# INGELEVERD OVER TIJD
# ----------------------------------------------------------

with left:

    st.subheader("Ingeleverd over tijd")

    trend_df = (
        df.groupby(
            "datum",
            as_index=False,
        )
        .agg(
            ingeleverd=("ingeleverd", "sum")
        )
        .sort_values("datum")
    )

    fig = px.line(
        trend_df,
        x="datum",
        y="ingeleverd",
    )

    fig.update_traces(
        line_color="#084422",
        line_width=3,
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
# OMZET OVER TIJD
# ----------------------------------------------------------

with right:

    st.subheader("Omzet over tijd")

    omzet_trend = (
        df.groupby(
            "datum",
            as_index=False,
        )
        .agg(
            omzet=("omzet", "sum")
        )
        .sort_values("datum")
    )

    fig = px.line(
        omzet_trend,
        x="datum",
        y="omzet",
    )

    fig.update_traces(
        line_color="#0d6b36",
        line_width=3,
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Omzet (€)",
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.markdown("---")

# ==========================================================
# INSIGHTS
# ==========================================================

st.subheader("📈 Belangrijkste inzichten")

if not summary.empty:

    best_conversion = summary.loc[
        summary["conversie"].idxmax()
    ]

    best_roi = summary.loc[
        summary["roi"].idxmax()
    ]

    highest_revenue = summary.loc[
        summary["omzet"].idxmax()
    ]

    col1, col2, col3 = st.columns(3)

    with col1:

        st.metric(
            "🏆 Hoogste conversie",
            best_conversion["coupon_code"],
            f"{best_conversion['conversie']:.1f}%"
        )

    with col2:

        st.metric(
            "🔥 Hoogste omzet",
            best_revenue["coupon_code"]
            if "best_revenue" in locals()
            else highest_revenue["coupon_code"],
            f"€ {highest_revenue['omzet']:,.0f}"
        )

    with col3:

        st.metric(
            "🚀 Beste ROI",
            best_roi["coupon_code"],
            f"{best_roi['roi']:.2f}x"
        )

st.markdown("---")

# ==========================================================
# TOP CONVERSIE VS VERLOOP
# ==========================================================

left, right = st.columns(2)

with left:

    st.subheader("Top conversie coupons")

    conversion_chart = (
        summary
        .sort_values(
            "conversie",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        conversion_chart,
        x="coupon_code",
        y="conversie",
        color="conversie",
        color_continuous_scale=[
            "#dce7e1",
            "#084422",
        ],
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Conversie %",
        coloraxis_showscale=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

with right:

    st.subheader("Hoogste verloop")

    expiry_chart = (
        summary
        .sort_values(
            "verloop_percentage",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        expiry_chart,
        x="coupon_code",
        y="verloop_percentage",
        color="verloop_percentage",
        color_continuous_scale=[
            "#f5d6d0",
            "#c9654b",
        ],
    )

    fig.update_layout(
        height=450,
        xaxis_title="",
        yaxis_title="Verloop %",
        coloraxis_showscale=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.markdown("---")

# ==========================================================
# COUPON PRESTATIES TABEL
# ==========================================================

st.subheader("📋 Coupon prestaties")

display_df = summary.copy()

display_df = display_df[
    [
        "coupon_code",
        "campagne",
        "verzonden",
        "openstaand",
        "ingeleverd",
        "verlopen",
        "discount",
        "omzet",
        "conversie",
        "roi",
    ]
]

display_df = display_df.rename(
    columns={
        "coupon_code": "Coupon",
        "campagne": "Campagne",
        "verzonden": "Verzonden",
        "openstaand": "Openstaand",
        "ingeleverd": "Ingeleverd",
        "verlopen": "Verlopen",
        "discount": "Korting (€)",
        "omzet": "Omzet (€)",
        "conversie": "Conversie %",
        "roi": "ROI",
    }
)

display_df["Conversie %"] = (
    display_df["Conversie %"]
    .round(1)
)

display_df["ROI"] = (
    display_df["ROI"]
    .round(2)
)

display_df["Korting (€)"] = (
    display_df["Korting (€)"]
    .map(lambda x: f"€ {x:,.2f}")
)

display_df["Omzet (€)"] = (
    display_df["Omzet (€)"]
    .map(lambda x: f"€ {x:,.2f}")
)

display_df = display_df.sort_values(
    "Omzet (€)",
    ascending=False,
)

st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

st.markdown("---")

# ==========================================================
# RUWE DATA
# ==========================================================

with st.expander("🔍 Bekijk ruwe data"):

    st.dataframe(
        df.sort_values(
            "datum",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

# ==========================================================
# DATAKWALITEIT
# ==========================================================

with st.expander("🧪 Datacontrole"):

    check_df = summary.copy()

    check_df["Controle"] = (
        check_df["openstaand"]
        + check_df["ingeleverd"]
        + check_df["verlopen"]
    )

    check_df["Afwijking"] = (
        check_df["verzonden"]
        - check_df["Controle"]
    )

    st.dataframe(
        check_df[
            [
                "coupon_code",
                "verzonden",
                "Controle",
                "Afwijking",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

st.markdown("---")

# ==========================================================
# FOOTER
# ==========================================================

st.caption(
    f"{len(df):,.0f} regels geladen | "
    f"{summary['coupon_code'].nunique():,.0f} coupons | "
    f"{summary['campagne'].nunique():,.0f} campagnes"
)
