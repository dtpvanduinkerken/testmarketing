import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Coupons Dashboard",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "199ipIJJARO8UjXjMcay33DNXz6mpui-oA2F43SE5Weg"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "coupons": f"{BASE_URL}/coupons",
}


BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_GREEN = "#7d9b88"


STYLE = f"""
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>
html, body, [data-testid="stAppViewContainer"] {{
    background: {BACKGROUND};
    font-family: 'sofia-pro', sans-serif;
    color: {BRAND_GREEN};
}}

.block-container {{
    padding: 42px 56px 56px 56px;
    max-width: 1500px;
}}

#MainMenu,
footer,
header {{
    visibility: hidden;
}}

.vdk-main-title {{
    font-size: 42px;
    font-weight: 700;
    color: {BRAND_GREEN};
    margin: 0;
    line-height: 1.15;
}}

.vdk-subtitle {{
    color: {TEXT_MUTED};
    font-size: 15px;
    margin-top: 8px;
    max-width: 900px;
    line-height: 1.6;
}}

.vdk-divider {{
    width: 100%;
    height: 1px;
    background: rgba(8, 68, 34, 0.08);
    margin-top: 24px;
    margin-bottom: 34px;
}}

[data-testid="stSidebar"] {{
    background: #ffffff;
    border-right: 1px solid rgba(8, 68, 34, 0.06);
}}

[data-testid="stSidebar"] * {{
    color: {BRAND_GREEN} !important;
}}

[data-testid="stMetric"] {{
    background: #ffffff;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid {CARD_BORDER};
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}}

[data-testid="stMetric"] label {{
    color: {TEXT_MUTED} !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}}

[data-testid="stMetricValue"] {{
    color: {BRAND_GREEN};
    font-size: 28px;
    font-weight: 700;
}}

.insight-card,
div[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {{
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid {CARD_BORDER};
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}}

.insight-card {{
    padding: 22px;
    min-height: 145px;
}}

.insight-card h4 {{
    color: {BRAND_GREEN};
    margin: 0 0 8px 0;
    font-size: 18px;
}}

.insight-card p {{
    color: {TEXT_MUTED};
    margin: 0;
    line-height: 1.55;
    font-size: 14px;
}}

[data-baseweb="select"] {{
    max-width: 360px;
}}

h1, h2, h3, h4 {{
    color: {BRAND_GREEN};
}}

h3 {{
    font-size: 20px;
    font-weight: 700;
}}

.space {{
    height: 34px;
}}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


def normalize_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = dataframe.copy()
    dataframe.columns = (
        dataframe.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return dataframe


@st.cache_data(ttl=60, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        st.error(f"Data kon niet worden opgehaald: {error}")
        return pd.DataFrame()
    except ValueError:
        st.error("De databron gaf geen geldige JSON terug.")
        return pd.DataFrame()

    if not data:
        st.error(f"De sheet is leeg of niet bereikbaar via deze URL: {url}")
        return pd.DataFrame()

    if isinstance(data, dict):
        data = [data]

    return normalize_columns(pd.DataFrame(data))


def parse_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series
        .astype(str)
        .str.replace("€", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def clean_coupons(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty:
        return dataframe

    dataframe = normalize_columns(dataframe)

    dataframe = dataframe.rename(
        columns={
            "coupon": "coupon_code",
            "couponcode": "coupon_code",
            "coupon_code": "coupon_code",
            "code": "coupon_code",
            "kortingscode": "coupon_code",
            "omzet": "revenue",
            "revenue": "revenue",
            "orders": "orders",
            "bestellingen": "orders",
            "aantal": "uses",
            "uses": "uses",
            "gebruik": "uses",
            "gebruiken": "uses",
            "datum": "date",
            "date": "date",
        }
    )

    if "coupon_code" not in dataframe.columns:
        st.error("Kolom voor couponcode ontbreekt.")
        st.write("Gevonden kolommen:", dataframe.columns.tolist())
        return pd.DataFrame()

    for column in ["uses", "orders", "revenue", "conversion_rate"]:
        if column in dataframe.columns:
            dataframe[column] = parse_numeric(dataframe[column])

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")

    if "uses" not in dataframe.columns:
        dataframe["uses"] = 0

    if "orders" not in dataframe.columns:
        dataframe["orders"] = dataframe["uses"]

    if "revenue" not in dataframe.columns:
        dataframe["revenue"] = 0

    dataframe["average_revenue_per_use"] = (
        dataframe["revenue"] / dataframe["uses"].replace(0, pd.NA)
    ).fillna(0)

    return dataframe


def format_euro(value: float) -> str:
    if pd.isna(value):
        return "€ 0"

    return f"€ {value:,.0f}".replace(",", ".")


def format_number(value: float) -> str:
    if pd.isna(value):
        return "0"

    return f"{value:,.0f}".replace(",", ".")


def apply_plotly_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Sofia Pro, Arial", "color": BRAND_GREEN},
        margin={"l": 30, "r": 30, "t": 55, "b": 35},
        hovermode="closest",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(8, 68, 34, 0.08)")

    return fig


def render_header() -> None:
    st.markdown(
        """
        <div>
            <div class="vdk-main-title">Coupons dashboard</div>
            <div class="vdk-subtitle">
                Inzicht in coupongebruik, orders en omzet.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("Coupondata laden..."):
    raw_coupons = load_sheet(SHEET_URLS["coupons"])
    coupons = clean_coupons(raw_coupons)


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Coupons")
st.sidebar.divider()

if st.sidebar.button("Data verversen"):
    st.cache_data.clear()
    st.rerun()

show_raw_data = st.sidebar.toggle("Toon ruwe data", value=False)


render_header()

if coupons.empty:
    st.warning("Geen coupondata beschikbaar. Controleer de tab `coupons` en de kolommen.")
    st.stop()


coupon_options = ["Alle coupons"] + sorted(
    coupons["coupon_code"].dropna().astype(str).unique()
)

selected_coupon = st.selectbox(
    "Coupon",
    coupon_options,
)

if selected_coupon != "Alle coupons":
    coupons = coupons[coupons["coupon_code"].astype(str) == selected_coupon]


if coupons.empty:
    st.warning("Geen coupondata beschikbaar voor de geselecteerde coupon.")
    st.stop()


total_uses = coupons["uses"].sum()
total_orders = coupons["orders"].sum()
total_revenue = coupons["revenue"].sum()

average_revenue_per_use = total_revenue / total_uses if total_uses > 0 else 0


add_space()

col1, col2, col3 = st.columns(3)

col1.metric("Coupongebruik", format_number(total_uses))
col2.metric("Orders met coupon", format_number(total_orders))
col3.metric("Omzet via coupons", format_euro(total_revenue))


add_space()

tab_overview, tab_coupons, tab_revenue, tab_data = st.tabs(
    ["Overzicht", "Coupons", "Omzet", "Data"]
)


with tab_overview:
    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Coupongebruik</h4>
                <p>Er zijn <strong>{format_number(total_uses)}</strong> couponacties geregistreerd.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Couponomzet</h4>
                <p>Coupons leverden samen <strong>{format_euro(total_revenue)}</strong> omzet op.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Gem. omzet per gebruik</h4>
                <p>Gemiddeld is dit <strong>{format_euro(average_revenue_per_use)}</strong> per coupongebruik.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

   


with tab_coupons:
    st.subheader("Top coupons")

    coupon_summary = (
        coupons
        .groupby("coupon_code", as_index=False)
        .agg(
            uses=("uses", "sum"),
            orders=("orders", "sum"),
            revenue=("revenue", "sum"),
        )
    )

    coupon_summary["average_revenue_per_use"] = (
        coupon_summary["revenue"] / coupon_summary["uses"].replace(0, pd.NA)
    ).fillna(0)

    fig = px.bar(
        coupon_summary.sort_values("revenue", ascending=False),
        x="revenue",
        y="coupon_code",
        orientation="h",
        text="revenue",
        title="Coupons op omzet",
        color_discrete_sequence=[BRAND_GREEN],
    )

    fig.update_traces(
        texttemplate="€ %{text:,.0f}",
        textposition="outside",
    )

    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
    )

    st.plotly_chart(
        apply_plotly_layout(fig, height=560),
        use_container_width=True,
    )

    st.dataframe(
        coupon_summary.sort_values("revenue", ascending=False),
        use_container_width=True,
        hide_index=True,
    )


with tab_revenue:
    st.subheader("Omzet per coupon")

    coupon_summary = (
        coupons
        .groupby("coupon_code", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            uses=("uses", "sum"),
            orders=("orders", "sum"),
        )
    )

    fig = px.scatter(
        coupon_summary,
        x="uses",
        y="revenue",
        size="orders",
        hover_name="coupon_code",
        title="Coupongebruik versus omzet",
        color_discrete_sequence=[BRAND_GREEN],
    )

    fig.update_yaxes(tickprefix="€ ")

    st.plotly_chart(
        apply_plotly_layout(fig, height=520),
        use_container_width=True,
    )


with tab_data:
    st.subheader("Datakwaliteit")

    col1, col2, col3 = st.columns(3)

    col1.metric("Couponrijen", len(coupons))
    col2.metric("Unieke coupons", coupons["coupon_code"].nunique())
    col3.metric("Beschikbare omzet", format_euro(total_revenue))

    if show_raw_data:
        add_space()
        st.subheader("Ruwe coupondata")
        st.dataframe(coupons, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe data' aan in de sidebar om de brondata te bekijken.")


st.caption("Van Duinkerken Coupons Dashboard · Streamlit · Plotly · Google Sheets")