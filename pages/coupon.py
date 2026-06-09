import pandas as pd
import plotly.express as px
import requests
import streamlit as st
from sqlalchemy import create_engine
import pymysql

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="VDK Coupon Dashboard",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded",
)


BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.08)"

NUMERIC_COLS = [
    "verzonden",
    "openstaand",
    "ingeleverd",
    "verlopen",
    "discount",
    "omzet",
]

# ==========================================================
# STYLING
# ==========================================================

st.markdown(
    f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
    background: {BACKGROUND};
}}

.block-container {{
    padding-top: 2rem;
    max-width: 1500px;
}}

section[data-testid="stSidebar"] {{
    background: white;
}}

.kpi-card, .insight-card {{
    background: white;
    border-radius: 16px;
    padding: 20px;
    border: 1px solid {CARD_BORDER};
    min-height: 110px;
}}

.kpi-label, .insight-title {{
    color: {TEXT_MUTED};
    font-size: 13px;
    margin-bottom: 10px;
}}

.kpi-value {{
    color: {BRAND_GREEN};
    font-size: 32px;
    font-weight: 700;
}}

.insight-value {{
    color: {BRAND_GREEN};
    font-size: 24px;
    font-weight: 600;
    white-space: pre-line;
}}
</style>
""",
    unsafe_allow_html=True,
)

# ==========================================================
# HELPERS
# ==========================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def parse_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def safe_divide(numerator, denominator, multiplier=1):
    return numerator.div(denominator.replace(0, pd.NA)).fillna(0) * multiplier


def format_number(value):
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value):
    return f"€ {format_number(value)}"


def kpi_card(title, value):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{title}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(title, value):
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">{title}</div>
            <div class="insight-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def apply_chart_layout(fig, height=420, x_title=None, y_title=None):
    fig.update_layout(
        height=height,
        plot_bgcolor="white",
        paper_bgcolor=BACKGROUND,
        margin=dict(l=20, r=20, t=20, b=20),
        xaxis_title=x_title,
        yaxis_title=y_title,
        coloraxis_showscale=False,
    )
    return fig


from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://avnadmin:AVNS_IOr05TcV_n9lMLmM4do@vdk-dashboard-vdk-marketing.i.aivencloud.com:25406/dashboards"
)

@st.cache_data(ttl=300)
def load_data():

    query = """
    SELECT
        datum,
        coupon_code,
        campagne,
        verzonden,
        openstaand,
        ingeleverd,
        verlopen,
        discount,
        omzet
    FROM coupons
    """

    df = pd.read_sql(query, engine)

    return normalize_columns(df)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for col in NUMERIC_COLS:
        df[col] = parse_numeric(df[col]) if col in df.columns else 0

    if "coupon_code" not in df.columns:
        st.error("Kolom 'coupon_code' ontbreekt in de data.")
        st.stop()

    df["coupon_code"] = df["coupon_code"].fillna("").astype(str).str.strip()
    df = df[df["coupon_code"] != ""]

    if "campagne" not in df.columns:
        df["campagne"] = ""

    if "datum" in df.columns:
        df["datum"] = pd.to_datetime(df["datum"], errors="coerce")
    else:
        df["datum"] = pd.NaT

    return df


def summarize_coupons(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.sort_values("datum", na_position="last")
        .groupby("coupon_code", as_index=False)
        .agg(
            campagne=("campagne", "last"),
            verzonden=("verzonden", "sum"),
            openstaand=("openstaand", "last"),
            ingeleverd=("ingeleverd", "sum"),
            verlopen=("verlopen", "sum"),
            discount=("discount", "sum"),
            omzet=("omzet", "sum"),
        )
    )

    summary["totaal"] = summary["verzonden"]
    summary["conversie"] = safe_divide(summary["ingeleverd"], summary["verzonden"], 100)
    summary["verloop_percentage"] = safe_divide(summary["verlopen"], summary["verzonden"], 100)
    summary["openstaand_percentage"] = safe_divide(summary["openstaand"], summary["verzonden"], 100)
    summary["roi"] = safe_divide(summary["omzet"], summary["discount"])

    return summary


# ==========================================================
# DATA LADEN
# ==========================================================

try:
    df = clean_data(load_data())
except Exception as error:
    st.error(f"Data kon niet geladen worden: {error}")
    st.stop()

if df.empty:
    st.warning("Geen data gevonden.")
    st.stop()

# ==========================================================
# SIDEBAR
# ==========================================================

st.sidebar.title("🎟️ Coupons")
st.sidebar.caption("Filter op coupon en periode")

coupon_options = ["Alle coupons"] + sorted(df["coupon_code"].unique().tolist())

selected_coupon = st.sidebar.selectbox("Coupon", coupon_options)

if selected_coupon != "Alle coupons":
    df = df[df["coupon_code"] == selected_coupon]

if df["datum"].notna().any():
    min_datum = df["datum"].min().date()
    max_datum = df["datum"].max().date()

    selected_datums = st.sidebar.date_input(
        "Periode",
        value=(min_datum, max_datum),
    )

    if isinstance(selected_datums, tuple) and len(selected_datums) == 2:
        start_datum, end_datum = selected_datums

        df = df[
            df["datum"].between(
                pd.Timestamp(start_datum),
                pd.Timestamp(end_datum),
            )
        ]

if df.empty:
    st.warning("Geen data binnen de gekozen filters.")
    st.stop()

# ==========================================================
# SAMENVATTING
# ==========================================================

summary = summarize_coupons(df)
summary_filtered = summary[summary["totaal"] >= 10].copy()

total_verzonden = summary["verzonden"].sum()
total_openstaand = summary["openstaand"].sum()
total_ingeleverd = summary["ingeleverd"].sum()
total_verlopen = summary["verlopen"].sum()
total_discount = summary["discount"].sum()
total_omzet = summary["omzet"].sum()

conversion_rate = total_ingeleverd / total_verzonden * 100 if total_verzonden else 0

# ==========================================================
# HEADER
# ==========================================================

st.markdown(
    f"""
    <h1 style="color:{BRAND_GREEN}; margin-bottom:0;">
        Coupon Dashboard
    </h1>
    """,
    unsafe_allow_html=True,
)

st.caption("Inzicht in coupongebruik, conversie en verloop")

# ==========================================================
# KPI'S
# ==========================================================

cols = st.columns(7)

kpis = [
    ("Verzonden", format_number(total_verzonden)),
    ("Openstaand", format_number(total_openstaand)),
    ("Ingeleverd", format_number(total_ingeleverd)),
    ("Verlopen", format_number(total_verlopen)),
    ("Conversie", f"{conversion_rate:.1f}%"),
    ("Korting", format_currency(total_discount)),
    ("Omzet", format_currency(total_omzet)),
]

for col, (title, value) in zip(cols, kpis):
    with col:
        kpi_card(title, value)

st.markdown("")

# ==========================================================
# STATUS + TREND
# ==========================================================

left, right = st.columns(2)

with left:
    st.subheader("Status verdeling")

    status_df = pd.DataFrame(
        {
            "Status": ["Gebruikt", "Verlopen", "Openstaand"],
            "Aantal": [total_ingeleverd, total_verlopen, total_openstaand],
        }
    )

    fig = px.bar(
        status_df,
        x="Aantal",
        y="Status",
        orientation="h",
        color="Status",
        color_discrete_map={
            "Gebruikt": BRAND_GREEN,
            "Verlopen": "#c9654b",
            "Openstaand": "#cfd7d1",
        },
    )

    fig.update_layout(showlegend=False)

    st.plotly_chart(
        apply_chart_layout(fig),
        use_container_width=True,
    )

with right:
    st.subheader("Coupongebruik over tijd")

    if df["datum"].notna().any():
        trend = (
            df.groupby("datum", as_index=False)
            .agg(gebruikt=("ingeleverd", "sum"))
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

        st.plotly_chart(
            apply_chart_layout(fig, x_title="", y_title="Gebruikt"),
            use_container_width=True,
        )
    else:
        st.info("Geen geldige datums beschikbaar.")

st.markdown("")

# ==========================================================
# OMZET + VERLOOP / COUPONDETAIL
# ==========================================================

left, right = st.columns(2)

with left:
    if selected_coupon == "Alle coupons":
        st.subheader("Top omzet per coupon")
    else:
        st.subheader("Omzet geselecteerde coupon")

    chart_data = summary_filtered.sort_values("omzet", ascending=False).head(10)

    if chart_data.empty:
        st.info("Geen coupons met minimaal 10 verzonden coupons.")
    else:
        fig = px.bar(
            chart_data,
            x="coupon_code",
            y="omzet",
            color="omzet",
            color_continuous_scale=["#dce7e1", BRAND_GREEN],
        )

        st.plotly_chart(
            apply_chart_layout(fig, height=450, x_title="", y_title="Omzet (€)"),
            use_container_width=True,
        )

with right:
    if selected_coupon == "Alle coupons":
        st.subheader("Coupons met hoogste verloop")

        worst_coupons = (
            summary_filtered
            .sort_values("verloop_percentage", ascending=False)
            .head(10)
        )

        if worst_coupons.empty:
            st.info("Geen coupons met minimaal 10 verzonden coupons.")
        else:
            fig = px.bar(
                worst_coupons,
                y="coupon_code",
                x="verloop_percentage",
                orientation="h",
                color="verloop_percentage",
                color_continuous_scale=["#f5d6d0", "#e8a697", "#c9654b"],
            )

            st.plotly_chart(
                apply_chart_layout(
                    fig,
                    height=450,
                    x_title="Verloop %",
                    y_title="",
                ),
                use_container_width=True,
            )

    else:
        st.subheader("Detail geselecteerde coupon")

        selected_summary = summary.iloc[0]

        detail_df = pd.DataFrame(
            {
                "Status": ["Ingeleverd", "Verlopen", "Openstaand"],
                "Aantal": [
                    selected_summary["ingeleverd"],
                    selected_summary["verlopen"],
                    selected_summary["openstaand"],
                ],
            }
        )

        if detail_df["Aantal"].sum() == 0:
            st.info("Geen statusdata beschikbaar voor deze coupon.")
        else:
            fig = px.pie(
                detail_df,
                names="Status",
                values="Aantal",
                hole=0.55,
                color="Status",
                color_discrete_map={
                    "Ingeleverd": BRAND_GREEN,
                    "Verlopen": "#c9654b",
                    "Openstaand": "#cfd7d1",
                },
            )

            fig.update_layout(
                height=450,
                paper_bgcolor=BACKGROUND,
                margin=dict(l=20, r=20, t=20, b=20),
                showlegend=True,
            )

            st.plotly_chart(fig, use_container_width=True)

st.markdown("")

# ==========================================================
# INZICHTEN
# ==========================================================

st.subheader("Belangrijkste inzichten")

if summary_filtered.empty:
    st.info("Geen inzichten beschikbaar bij de huidige filters.")
else:
    best_coupon = summary_filtered.loc[summary_filtered["conversie"].idxmax()]
    highest_revenue = summary_filtered.loc[summary_filtered["omzet"].idxmax()]
    best_roi = summary_filtered.loc[summary_filtered["roi"].idxmax()]

    col1, col2, col3 = st.columns(3)

    with col1:
        insight_card(
            "🏆 Hoogste conversie",
            f"{best_coupon['coupon_code']}\n{best_coupon['conversie']:.1f}%",
        )

    with col2:
        insight_card(
            "🔥 Hoogste omzet",
            f"{highest_revenue['coupon_code']}\n{format_currency(highest_revenue['omzet'])}",
        )

    with col3:
        insight_card(
            "💡 Beste ROI",
            f"{best_roi['coupon_code']}\n{best_roi['roi']:.2f}",
        )

st.markdown("")

# ==========================================================
# TABEL
# ==========================================================

st.subheader("Coupon prestaties")

table_cols = [
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

display_df = (
    summary_filtered[table_cols]
    .sort_values("omzet", ascending=False)
    .rename(
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
)

display_df["Conversie %"] = display_df["Conversie %"].round(1)
display_df["ROI"] = display_df["ROI"].round(2)
display_df["Korting (€)"] = display_df["Korting (€)"].map(format_currency)
display_df["Omzet (€)"] = display_df["Omzet (€)"].map(format_currency)

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
        df.sort_values("datum", ascending=False),
        use_container_width=True,
        hide_index=True,
    )

# ==========================================================
# FOOTER
# ==========================================================

st.markdown("---")
st.caption(f"{format_number(len(df))} records geladen")
