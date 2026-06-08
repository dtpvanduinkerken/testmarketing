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
    initial_sidebar_state="expanded",
)

# ==========================================================
# KLEUREN
# ==========================================================

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.08)"

# ==========================================================
# STYLING
# ==========================================================

st.markdown(
    f"""
<style>

html,
body,
[data-testid="stAppViewContainer"] {{
    background:{BACKGROUND};
}}

.block-container {{
    padding-top:2rem;
    max-width:1500px;
}}

section[data-testid="stSidebar"] {{
    background:white;
}}

.chart-card {{
    background:white;
    border-radius:16px;
    padding:16px;
    border:1px solid {CARD_BORDER};
}}

.kpi-card {{
    background:white;
    border-radius:16px;
    padding:20px;
    border:1px solid {CARD_BORDER};
    min-height:110px;
}}

.kpi-label {{
    color:{TEXT_MUTED};
    font-size:13px;
    margin-bottom:10px;
}}

.kpi-value {{
    color:{BRAND_GREEN};
    font-size:32px;
    font-weight:700;
}}

.insight-card {{
    background:white;
    border-radius:16px;
    padding:20px;
    border:1px solid {CARD_BORDER};
}}

.insight-title {{
    color:{TEXT_MUTED};
    font-size:12px;
}}

.insight-value {{
    color:{BRAND_GREEN};
    font-size:24px;
    font-weight:600;
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


def kpi_card(title, value):

    st.markdown(
        f"""
        <div class="kpi-card">

            <div class="kpi-label">
                {title}
            </div>

            <div class="kpi-value">
                {value}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title, value):

    st.markdown(
        f"""
        <div class="insight-card">

            <div class="insight-title">
                {title}
            </div>

            <div class="insight-value">
                {value}
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# DATA LADEN
# ==========================================================

@st.cache_data(ttl=300)
def load_data():

    response = requests.get(
        COUPON_URL,
        timeout=20,
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

    if "coupon_code" in df.columns:

        df["coupon_code"] = (
            df["coupon_code"]
            .fillna("")
            .astype(str)
            .str.strip()
        )

        df = df[
            df["coupon_code"] != ""
        ]

    if "datum" in df.columns:

        df["datum"] = pd.to_datetime(
            df["datum"],
            errors="coerce",
        )

    return df


# ==========================================================
# DATA
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

    st.warning("Geen data gevonden.")

    st.stop()

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title("🎟️ Coupons")

st.sidebar.caption(
    "Filter op coupon en periode"
)

coupon_options = (
    ["Alle coupons"]
    + sorted(
        df["coupon_code"]
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
    "datum" in df.columns
    and df["datum"].notna().any()
):

    min_datum = df["datum"].min().date()
    max_datum = df["datum"].max().date()

    selected_datums = st.sidebar.date_input(
        "Periode",
        value=(min_datum, max_datum),
    )

    if len(selected_datums) == 2:

        start_datum, end_datum = selected_datums

        df = df[
            df["datum"].between(
                pd.Timestamp(start_datum),
                pd.Timestamp(end_datum),
            )
        ]

# ==========================================================
# KPI'S
# ==========================================================

total_openstaand = df["openstaand"].sum()
total_ingeleverd = df["ingeleverd"].sum()
total_verlopen = df["verlopen"].sum()

total_verzonden = df["verzonden"].sum()
total_openstaand = df["openstaand"].sum()
total_ingeleverd = df["ingeleverd"].sum()
total_verlopen = df["verlopen"].sum()

total_discount = df["discount"].sum()
total_omzet = df["omzet"].sum()

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

open_rate = (
    total_openstaand / total_verzonden * 100
    if total_verzonden > 0
    else 0
)

# ==========================================================
# TITEL
# ==========================================================

st.markdown(
    """
    <h1 style="
        color:#084422;
        margin-bottom:0;
    ">
        Coupon Dashboard
    </h1>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "Inzicht in coupongebruik, conversie en verloop"
)

# ==========================================================
# KPI CARDS
# ==========================================================

c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

with c1:
    kpi_card("Verzonden", f"{total_verzonden:,.0f}")

with c2:
    kpi_card("Openstaand", f"{total_openstaand:,.0f}")

with c3:
    kpi_card("Ingeleverd", f"{total_ingeleverd:,.0f}")

with c4:
    kpi_card("Verlopen", f"{total_verlopen:,.0f}")

with c5:
    kpi_card("Conversie", f"{conversion_rate:.1f}%")

with c6:
    kpi_card("Korting", f"€ {total_discount:,.0f}")

with c7:
    kpi_card("Omzet", f"€ {total_omzet:,.0f}")

# ==========================================================
# STATUS VERDELING
# ==========================================================

left, right = st.columns([1, 1])

with left:

    st.subheader("Status verdeling")

    status_df = pd.DataFrame(
        {
            "Status": [
                "Gebruikt",
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
            "Gebruikt": "#084422",
            "Verlopen": "#c9654b",
            "Openstaand": "#cfd7d1",
        },
    )

    fig.update_layout(
        height=420,
        showlegend=False,
        plot_bgcolor="white",
        paper_bgcolor=BACKGROUND,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ==========================================================
# GEBRUIK OVER TIJD
# ==========================================================

with right:

    st.subheader("Coupongebruik over tijd")

    if (
        "datum" in df.columns
        and df["datum"].notna().any()
    ):

        trend = (
            df.groupby(
                "datum",
                as_index=False,
            )
            .agg(
                gebruikt=(
                    "ingeleverd",
                    "sum",
                )
            )
            .sort_values("datum")
        )

        fig = px.line(
            trend,
            x="datum",
            y="gebruikt",
        )

        fig.update_traces(
            line_color=BRAND_GREEN,
            line_width=3,
        )

        fig.update_layout(
            height=420,
            plot_bgcolor="white",
            paper_bgcolor=BACKGROUND,
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================
# SAMENVATTING PER COUPON
# ==========================================================

def summarize_coupons(df):
    agg = {
        "verzonden": "sum",
        "ingeleverd": "sum",
        "verlopen": "sum",
        "discount": "sum",
        "omzet": "sum",
    }

    if "openstaand" in df.columns:
        agg["openstaand"] = "last"

    if "campagne" in df.columns:
        agg["campagne"] = "last"

    return (
        df.sort_values("datum", na_position="last")
          .groupby("coupon_code", as_index=False)
          .agg(agg)
    )


summary = summarize_coupons(df)
summary["totaal"] = summary["verzonden"]

summary["conversie"] = (
    summary["ingeleverd"]
    / summary["verzonden"]
    * 100
).fillna(0)

summary["verloop_percentage"] = (
    summary["verlopen"]
    / summary["verzonden"]
    * 100
).fillna(0)

summary["roi"] = (
    summary["omzet"]
    .div(summary["discount"].replace(0, pd.NA))
).fillna(0)

summary["openstaand_percentage"] = (
    summary["openstaand"]
    / summary["verzonden"]
    * 100
).fillna(0)

# Alleen coupons met voldoende volume
summary_filtered = summary[
    summary["totaal"] >= 10
].copy()

# ==========================================================
# GEBRUIK VS VERLOOP
# ==========================================================

left, right = st.columns([1, 1])

with left:

    st.subheader("Top omzet per coupon")

    chart_data = (
        summary_filtered
        .sort_values("omzet", ascending=False)
        .head(10)
    )

    fig = px.bar(
        chart_data,
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
        plot_bgcolor="white",
        paper_bgcolor=BACKGROUND,
        xaxis_title="",
        yaxis_title="Omzet (€)",
        coloraxis_showscale=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

# ==========================================================
# HOOGSTE VERLOOP
# ==========================================================

with right:

    st.subheader("Coupons met hoogste verloop")

    worst_coupons = (
        summary_filtered
        .sort_values(
            "verloop_percentage",
            ascending=False,
        )
        .head(10)
    )

    fig = px.bar(
        worst_coupons,
        y="coupon_code",
        x="verloop_percentage",
        orientation="h",
        color="verloop_percentage",
        color_continuous_scale=[
            "#f5d6d0",
            "#e8a697",
            "#c9654b",
        ],
    )

    fig.update_layout(
        height=450,
        plot_bgcolor="white",
        paper_bgcolor=BACKGROUND,
        yaxis_title="",
        xaxis_title="Verloop %",
        coloraxis_showscale=False,
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================
# INSIGHTS
# ==========================================================

st.subheader("Belangrijkste inzichten")

if not summary_filtered.empty:

    best_coupon = summary_filtered.loc[
        summary_filtered["conversie"].idxmax()
    ]

    highest_expiry = summary_filtered.loc[
        summary_filtered["verloop_percentage"].idxmax()
    ]

    most_used = summary_filtered.loc[
        summary_filtered["ingeleverd"].idxmax()
    ]

    col1, col2, col3 = st.columns(3)

    with col1:

        insight_card(
            "🏆 Hoogste conversie",
            f"{best_coupon['coupon_code']}<br><span style='font-size:16px'>{best_coupon['conversie']:.1f}%</span>",
        )

    with col2:

        insight_card(
            "🔥 Hoogste omzet",
            f"{highest_revenue['coupon_code']}<br><span style='font-size:16px'>€ {highest_revenue['omzet']:,.0f}</span>",
        )

    with col3:

        insight_card(
            "💡 Beste ROI",
            f"{best_roi['coupon_code']}<br><span style='font-size:16px'>{best_roi['roi']:.2f}</span>",
        )

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================================
# TOP COUPONS TABEL
# ==========================================================

st.subheader("Coupon prestaties")

display_df = (
    summary_filtered[
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
    .sort_values(
        "omzet",
        ascending=False,
    )
)

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
        "roi": "ROI"
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
    .map(lambda x: f"€ {x:,.0f}")
)

display_df["Omzet (€)"] = (
    display_df["Omzet (€)"]
    .map(lambda x: f"€ {x:,.0f}")
)
st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True,
)

# ==========================================================
# RUWE DATA
# ==========================================================

with st.expander("Bekijk ruwe data"):

    st.dataframe(
        df.sort_values(
            "datum",
            ascending=False,
        ),
        use_container_width=True,
        hide_index=True,
    )

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")

st.caption(
    f"{len(df):,.0f} records geladen"
)
