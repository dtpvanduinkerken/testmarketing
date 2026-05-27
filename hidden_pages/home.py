import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Website Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "channels": f"{BASE_URL}/channels",
    "devices": f"{BASE_URL}/devices",
    "funnel": f"{BASE_URL}/funnel",
}

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"


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

[data-testid="stMetricDelta"] {{
    font-size: 13px;
    font-weight: 600;
}}

.section-card,
div[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {{
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid {CARD_BORDER};
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}}

.section-card {{
    padding: 22px;
}}

.small-muted {{
    color: {TEXT_MUTED};
    font-size: 14px;
    margin-bottom: 4px;
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
    dataframe.columns = dataframe.columns.str.strip().str.lower()
    return dataframe


@st.cache_data(ttl=3600, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        st.error(f"Data kon niet worden opgehaald: {error}")
        return pd.DataFrame()
    except ValueError:
        st.error("De Google Sheet gaf geen geldige JSON terug.")
        return pd.DataFrame()

    if isinstance(data, dict):
        data = [data]

    return normalize_columns(pd.DataFrame(data))


def to_numeric(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    dataframe = dataframe.copy()

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = (
                dataframe[column]
                .astype(str)
                .str.replace("€", "", regex=False)
                .str.replace("%", "", regex=False)
                .str.replace(".", "", regex=False)
                .str.replace(",", ".", regex=False)
            )
            dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    return dataframe


def clean_overview(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)

    if "date" not in dataframe.columns:
        return pd.DataFrame()

    numeric_columns = [
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

    dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
    dataframe = dataframe.dropna(subset=["date"])
    dataframe = to_numeric(dataframe, numeric_columns)
    dataframe = dataframe.sort_values("date")

    return dataframe


def format_euro(value: float) -> str:
    if pd.isna(value):
        return "€ 0"

    return f"€ {value:,.0f}".replace(",", ".")


def format_number(value: float) -> str:
    if pd.isna(value):
        return "0"

    return f"{value:,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    if pd.isna(value):
        return "0,0%"

    return f"{value:.1f}%".replace(".", ",")


def calculate_delta(current: float, previous: float) -> float:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return 0.0

    return round(((current - previous) / previous) * 100, 1)


def summarize_metric(
    dataframe: pd.DataFrame,
    column: str,
    method: str = "sum",
) -> float:
    if column not in dataframe.columns:
        return 0.0

    if method == "mean":
        return dataframe[column].mean()

    return dataframe[column].sum()


def get_period_data(
    dataframe: pd.DataFrame,
    days: int | None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    latest_date = dataframe["date"].max()

    if days is None:
        return dataframe.copy(), dataframe.iloc[0:0].copy()

    current_start = latest_date - pd.Timedelta(days=days - 1)
    previous_start = current_start - pd.Timedelta(days=days)
    previous_end = current_start - pd.Timedelta(days=1)

    current = dataframe[dataframe["date"] >= current_start]
    previous = dataframe[
        (dataframe["date"] >= previous_start)
        & (dataframe["date"] <= previous_end)
    ]

    return current, previous


def apply_plotly_layout(fig: go.Figure, height: int = 420) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Sofia Pro, Arial", "color": BRAND_GREEN},
        margin={"l": 30, "r": 30, "t": 50, "b": 35},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(8, 68, 34, 0.08)")

    return fig


def show_metric(label: str, value: str, delta: float) -> None:
    st.metric(
        label=label,
        value=value,
        delta=f"{delta:+.1f}%".replace(".", ","),
    )


def render_header(start_date, end_date) -> None:
    st.markdown(
        f"""
        <div>
            <div class="vdk-main-title">Website dashboard</div>
            <div class="vdk-subtitle">
                Inzicht in omzet, verkeer, kanalen, devices en checkout-performance.
                Periode: <strong>{start_date}</strong> t/m <strong>{end_date}</strong>.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("Dashboarddata laden..."):
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
    channels = load_sheet(SHEET_URLS["channels"])
    devices = load_sheet(SHEET_URLS["devices"])
    funnel = load_sheet(SHEET_URLS["funnel"])


if overview.empty:
    st.error("Geen geldige overview-data gevonden. Controleer de sheetnaam en kolom `date`.")
    st.stop()


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Website dashboard")
st.sidebar.divider()

period_label = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

period_days = {
    "Laatste 7 dagen": 7,
    "Laatste 30 dagen": 30,
    "Laatste 90 dagen": 90,
    "Alles": None,
}[period_label]

selected_metrics = st.sidebar.multiselect(
    "Toon trends",
    ["omzet", "orders", "bezoekers", "sessies", "conversie"],
    default=["omzet", "orders", "bezoekers"],
)

show_raw_data = st.sidebar.toggle("Toon ruwe data", value=False)

current_period, previous_period = get_period_data(overview, period_days)

if current_period.empty:
    st.error("Geen data beschikbaar binnen deze periode.")
    st.stop()

start_date = current_period["date"].min().date()
end_date = current_period["date"].max().date()

render_header(start_date, end_date)


current_revenue = summarize_metric(current_period, "omzet")
previous_revenue = summarize_metric(previous_period, "omzet")

current_orders = summarize_metric(current_period, "orders")
previous_orders = summarize_metric(previous_period, "orders")

current_visitors = summarize_metric(current_period, "bezoekers")
previous_visitors = summarize_metric(previous_period, "bezoekers")

current_sessions = summarize_metric(current_period, "sessies")
previous_sessions = summarize_metric(previous_period, "sessies")

current_conversion = summarize_metric(current_period, "conversie", method="mean")
previous_conversion = summarize_metric(previous_period, "conversie", method="mean")

metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    show_metric(
        "Omzet",
        format_euro(current_revenue),
        calculate_delta(current_revenue, previous_revenue),
    )

with metric_col2:
    show_metric(
        "Orders",
        format_number(current_orders),
        calculate_delta(current_orders, previous_orders),
    )

with metric_col3:
    show_metric(
        "Bezoekers",
        format_number(current_visitors),
        calculate_delta(current_visitors, previous_visitors),
    )

with metric_col4:
    show_metric(
        "Sessies",
        format_number(current_sessions),
        calculate_delta(current_sessions, previous_sessions),
    )

with metric_col5:
    show_metric(
        "Conversie",
        format_percent(current_conversion),
        calculate_delta(current_conversion, previous_conversion),
    )


add_space()

tab_overview, tab_channels, tab_funnel, tab_data = st.tabs(
    ["Overzicht", "Kanalen & devices", "Funnel", "Data"]
)


with tab_overview:
    left_col, right_col = st.columns([2, 1])

    with left_col:
        st.subheader("Omzetontwikkeling")

        revenue_fig = px.area(
            current_period,
            x="date",
            y="omzet",
            markers=True,
            title="Omzet per dag",
        )

        revenue_fig.update_traces(
            line={"color": BRAND_GREEN, "width": 3},
            fillcolor="rgba(8, 68, 34, 0.10)",
        )

        revenue_fig.update_yaxes(tickprefix="€ ")

        st.plotly_chart(
            apply_plotly_layout(revenue_fig),
            use_container_width=True,
        )

    with right_col:
        st.subheader("Samenvatting")

        average_order_value = (
            current_revenue / current_orders
            if current_orders > 0
            else 0
        )

        sessions_per_visitor = (
            current_sessions / current_visitors
            if current_visitors > 0
            else 0
        )

        st.markdown(
            f"""
            <div class="section-card">
                <p class="small-muted">Gemiddelde orderwaarde</p>
                <h2>{format_euro(average_order_value)}</h2>

                <p class="small-muted">Sessies per bezoeker</p>
                <h2>{sessions_per_visitor:.2f}</h2>

                <p class="small-muted">Actieve dagen in selectie</p>
                <h2>{len(current_period)}</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if selected_metrics:
        trend_data = current_period[["date", *selected_metrics]].melt(
            id_vars="date",
            var_name="Metric",
            value_name="Waarde",
        )

        trend_fig = px.line(
            trend_data,
            x="date",
            y="Waarde",
            color="Metric",
            markers=True,
            title="Geselecteerde trends",
            color_discrete_sequence=[
                BRAND_GREEN,
                "#7d9b88",
                "#3f6b53",
                "#b6c5b9",
                "#c76f6f",
            ],
        )

        st.plotly_chart(
            apply_plotly_layout(trend_fig),
            use_container_width=True,
        )


with tab_channels:
    channel_col, device_col = st.columns(2)

    with channel_col:
        st.subheader("Verkeer per kanaal")

        channels = normalize_columns(channels)

        if {"sessiondefaultchannelgroup", "sessions"}.issubset(channels.columns):
            channels = to_numeric(channels, ["sessions"])

            channels_top = (
                channels
                .dropna(subset=["sessions"])
                .sort_values("sessions", ascending=False)
                .head(10)
            )

            channel_fig = px.bar(
                channels_top,
                x="sessions",
                y="sessiondefaultchannelgroup",
                orientation="h",
                text="sessions",
                title="Top 10 kanalen op sessies",
                color_discrete_sequence=[BRAND_GREEN],
            )

            channel_fig.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
            )

            channel_fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
            )

            st.plotly_chart(
                apply_plotly_layout(channel_fig),
                use_container_width=True,
            )
        else:
            st.warning("Kanaaldata mist `sessiondefaultchannelgroup` of `sessions`.")

    with device_col:
        st.subheader("Devices")

        devices = normalize_columns(devices)

        if {"devicetype", "sessions"}.issubset(devices.columns):
            devices = to_numeric(devices, ["sessions"])
            devices = devices.dropna(subset=["sessions"])

            device_fig = px.pie(
                devices,
                names="devicetype",
                values="sessions",
                hole=0.58,
                title="Sessies per device",
                color_discrete_sequence=[
                    BRAND_GREEN,
                    "#7d9b88",
                    "#b6c5b9",
                    "#dfe7df",
                ],
            )

            device_fig.update_traces(textinfo="percent+label")

            st.plotly_chart(
                apply_plotly_layout(device_fig),
                use_container_width=True,
            )
        else:
            st.warning("Devicedata mist `devicetype` of `sessions`.")


with tab_funnel:
    st.subheader("Checkout funnel")

    funnel = normalize_columns(funnel)
    funnel_columns = ["view_item", "add_to_cart", "begin_checkout", "purchase"]
    available_columns = [
        column for column in funnel_columns if column in funnel.columns
    ]

    if available_columns:
        funnel = to_numeric(funnel, available_columns)

        funnel_labels = {
            "view_item": "Product bekeken",
            "add_to_cart": "Toegevoegd aan winkelwagen",
            "begin_checkout": "Checkout gestart",
            "purchase": "Aankoop",
        }

        funnel_data = pd.DataFrame(
            {
                "Stap": [funnel_labels[column] for column in available_columns],
                "Aantal": [funnel[column].sum() for column in available_columns],
            }
        )

        funnel_data["Conversie t.o.v. vorige stap"] = (
            funnel_data["Aantal"] / funnel_data["Aantal"].shift(1) * 100
        ).fillna(100)

        funnel_fig = px.funnel(
            funnel_data,
            x="Aantal",
            y="Stap",
            title="Van productview naar aankoop",
            color_discrete_sequence=[BRAND_GREEN],
        )

        st.plotly_chart(
            apply_plotly_layout(funnel_fig),
            use_container_width=True,
        )

        st.dataframe(
            funnel_data.assign(
                Aantal=funnel_data["Aantal"].map(format_number),
                **{
                    "Conversie t.o.v. vorige stap": funnel_data[
                        "Conversie t.o.v. vorige stap"
                    ].map(format_percent)
                },
            ),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Geen bruikbare funnelkolommen gevonden.")

    add_space()

    st.subheader("Automatische inzichten")

    average_order_value = (
        current_revenue / current_orders
        if current_orders > 0
        else 0
    )

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.info(
            f"Omzet in deze periode: {format_euro(current_revenue)}. "
            f"Dit is {calculate_delta(current_revenue, previous_revenue):+.1f}% "
            "versus de vorige vergelijkbare periode."
        )

    with insight_col2:
        st.info(
            f"Conversie: {format_percent(current_conversion)}. "
            "Controleer vooral de stap tussen winkelwagen en checkout."
        )

    with insight_col3:
        st.info(
            f"Gemiddelde orderwaarde: {format_euro(average_order_value)}. "
            "Gebruik bundels of upsell-campagnes om deze waarde te verhogen."
        )


with tab_data:
    st.subheader("Datakwaliteit")

    quality_col1, quality_col2, quality_col3 = st.columns(3)

    with quality_col1:
        st.metric("Rijen overview", len(overview))

    with quality_col2:
        st.metric("Startdatum", str(overview["date"].min().date()))

    with quality_col3:
        st.metric("Einddatum", str(overview["date"].max().date()))

    if show_raw_data:
        add_space()
        st.subheader("Ruwe overview-data")
        st.dataframe(
            overview,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.caption("Zet 'Toon ruwe data' aan in de sidebar om de brondata te bekijken.")

st.caption("Van Duinkerken Marketing Dashboard · Streamlit, Plotly en Google Sheets")