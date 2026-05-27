import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Marketing Dashboard",
    page_icon="📣",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "channels": f"{BASE_URL}/channels",
    "campaigns": f"{BASE_URL}/campaigns",
    "overview": f"{BASE_URL}/overview_kpis",
}

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_GREEN = "#7d9b88"
SOFT_GOLD = "#c9a646"
SOFT_BLUE = "#8faecf"


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

[data-testid="stMetricDelta"] {{
    font-size: 13px;
    font-weight: 600;
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

.section-note {{
    color: {TEXT_MUTED};
    font-size: 14px;
    margin-top: -6px;
    margin-bottom: 16px;
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
        st.error("De databron gaf geen geldige JSON terug.")
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
        .str.replace(",", ".", regex=False),
        errors="coerce",
    )


def convert_columns_to_numeric(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = parse_numeric(dataframe[column])

    return dataframe


def clean_overview(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)

    dataframe = convert_columns_to_numeric(
        dataframe,
        ["omzet", "sessies", "bezoekers", "orders", "conversie"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
        dataframe = dataframe.dropna(subset=["date"])
        dataframe = dataframe.sort_values("date")

    return dataframe


def clean_channels(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)

    protected_columns = {"sessiondefaultchannelgroup", "date"}
    numeric_columns = [
        column for column in dataframe.columns
        if column not in protected_columns
    ]

    dataframe = convert_columns_to_numeric(dataframe, numeric_columns)

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")

    if {"totalrevenue", "sessions"}.issubset(dataframe.columns):
        dataframe["revenue_per_session"] = (
            dataframe["totalrevenue"]
            / dataframe["sessions"].replace(0, pd.NA)
        ).fillna(0)

    if {"transactions", "sessions"}.issubset(dataframe.columns):
        dataframe["conversion_rate"] = (
            dataframe["transactions"]
            / dataframe["sessions"].replace(0, pd.NA)
            * 100
        ).fillna(0)

    return dataframe


def clean_campaigns(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)

    protected_columns = {"campaignname", "date"}
    numeric_columns = [
        column for column in dataframe.columns
        if column not in protected_columns
    ]

    dataframe = convert_columns_to_numeric(dataframe, numeric_columns)

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")

    if {"totalrevenue", "sessions"}.issubset(dataframe.columns):
        dataframe["revenue_per_session"] = (
            dataframe["totalrevenue"]
            / dataframe["sessions"].replace(0, pd.NA)
        ).fillna(0)

    if {"transactions", "sessions"}.issubset(dataframe.columns):
        dataframe["conversion_rate"] = (
            dataframe["transactions"]
            / dataframe["sessions"].replace(0, pd.NA)
            * 100
        ).fillna(0)

    return dataframe


def filter_period(
    dataframe: pd.DataFrame,
    period_label: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if "date" not in dataframe.columns:
        return dataframe.copy(), dataframe.iloc[0:0].copy()

    latest_date = dataframe["date"].max()

    period_days = {
        "Laatste 7 dagen": 7,
        "Laatste 30 dagen": 30,
        "Laatste 90 dagen": 90,
        "Alles": None,
    }[period_label]

    if period_days is None:
        return dataframe.copy(), dataframe.iloc[0:0].copy()

    current_start = latest_date - pd.Timedelta(days=period_days - 1)
    previous_start = current_start - pd.Timedelta(days=period_days)
    previous_end = current_start - pd.Timedelta(days=1)

    current = dataframe[dataframe["date"] >= current_start]
    previous = dataframe[
        (dataframe["date"] >= previous_start)
        & (dataframe["date"] <= previous_end)
    ]

    return current, previous


def calculate_delta(current: float, previous: float) -> float:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return 0.0

    return round(((current - previous) / previous) * 100, 1)


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


def apply_plotly_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Sofia Pro, Arial", "color": BRAND_GREEN},
        margin={"l": 30, "r": 30, "t": 55, "b": 35},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(8, 68, 34, 0.08)")

    return fig


def show_metric(label: str, value: str, delta: float | None = None) -> None:
    if delta is None:
        st.metric(label=label, value=value)
        return

    st.metric(
        label=label,
        value=value,
        delta=f"{delta:+.1f}%".replace(".", ","),
    )


def render_header(period_text: str) -> None:
    st.markdown(
        f"""
        <div>
            <div class="vdk-main-title">Marketing performance</div>
            <div class="vdk-subtitle">
                Inzicht in kanaalprestaties, campagnes, omzetbijdrage
                en marketinggroei. Periode: <strong>{period_text}</strong>.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("Marketingdata laden..."):
    channels = clean_channels(load_sheet(SHEET_URLS["channels"]))
    campaigns = clean_campaigns(load_sheet(SHEET_URLS["campaigns"]))
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))


if overview.empty:
    st.error("Geen geldige overview-data gevonden. Controleer de sheet `overview_kpis`.")
    st.stop()


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Marketing")
st.sidebar.divider()

period = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

channel_metric = st.sidebar.selectbox(
    "Kanaalranking op",
    ["sessions", "totalrevenue", "transactions", "conversion_rate"],
)

campaign_metric = st.sidebar.selectbox(
    "Campagneranking op",
    ["sessions", "totalrevenue", "transactions", "revenue_per_session"],
)

top_n = st.sidebar.slider(
    "Aantal items",
    min_value=5,
    max_value=25,
    value=10,
)

show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)


filtered_overview, previous_overview = filter_period(overview, period)

if filtered_overview.empty:
    st.error("Geen data beschikbaar voor deze periode.")
    st.stop()


if "date" in filtered_overview.columns:
    start_date = filtered_overview["date"].min().date()
    end_date = filtered_overview["date"].max().date()
    period_text = f"{start_date} t/m {end_date}"
else:
    period_text = period.lower()


current_sessions = filtered_overview["sessies"].sum()
previous_sessions = previous_overview["sessies"].sum()

current_users = filtered_overview["bezoekers"].sum()
previous_users = previous_overview["bezoekers"].sum()

current_revenue = filtered_overview["omzet"].sum()
previous_revenue = previous_overview["omzet"].sum()

current_orders = filtered_overview["orders"].sum()
previous_orders = previous_overview["orders"].sum()

current_conversion = filtered_overview["conversie"].mean()
previous_conversion = previous_overview["conversie"].mean()

revenue_per_session = (
    current_revenue / current_sessions
    if current_sessions > 0
    else 0
)

previous_revenue_per_session = (
    previous_revenue / previous_sessions
    if previous_sessions > 0
    else 0
)


render_header(period_text)


metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    show_metric(
        "Sessies",
        format_number(current_sessions),
        calculate_delta(current_sessions, previous_sessions),
    )

with metric_col2:
    show_metric(
        "Bezoekers",
        format_number(current_users),
        calculate_delta(current_users, previous_users),
    )

with metric_col3:
    show_metric(
        "Omzet",
        format_euro(current_revenue),
        calculate_delta(current_revenue, previous_revenue),
    )

with metric_col4:
    show_metric(
        "Conversieratio",
        format_percent(current_conversion),
        calculate_delta(current_conversion, previous_conversion),
    )

with metric_col5:
    show_metric(
        "Omzet per sessie",
        format_euro(revenue_per_session),
        calculate_delta(revenue_per_session, previous_revenue_per_session),
    )


add_space()


tab_overview, tab_channels, tab_campaigns, tab_revenue, tab_data = st.tabs(
    ["Overzicht", "Kanalen", "Campagnes", "Omzet", "Data"]
)


with tab_overview:
    chart_col, side_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Verkeerontwikkeling")
        st.markdown(
            """
            <p class="section-note">
                Sessies en bezoekers binnen de geselecteerde periode.
            </p>
            """,
            unsafe_allow_html=True,
        )

        if "date" in filtered_overview.columns:
            trend = (
                filtered_overview
                .groupby("date", as_index=False)[["sessies", "bezoekers"]]
                .sum()
            )

            trend_data = trend.melt(
                id_vars="date",
                var_name="Metric",
                value_name="Waarde",
            )

            traffic_fig = px.line(
                trend_data,
                x="date",
                y="Waarde",
                color="Metric",
                markers=True,
                title="Marketingverkeer over tijd",
                color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD],
            )

            st.plotly_chart(
                apply_plotly_layout(traffic_fig),
                use_container_width=True,
            )
        else:
            st.info("Geen datumkolom beschikbaar voor trendanalyse.")

    with side_col:
        st.subheader("Omzet & conversie")

        if "date" in filtered_overview.columns:
            revenue_trend = (
                filtered_overview
                .groupby("date", as_index=False)
                .agg(
                    omzet=("omzet", "sum"),
                    conversie=("conversie", "mean"),
                )
            )

            revenue_fig = go.Figure()

            revenue_fig.add_trace(
                go.Bar(
                    x=revenue_trend["date"],
                    y=revenue_trend["omzet"],
                    name="Omzet",
                    marker_color=BRAND_GREEN,
                )
            )

            revenue_fig.add_trace(
                go.Scatter(
                    x=revenue_trend["date"],
                    y=revenue_trend["conversie"],
                    name="Conversie",
                    yaxis="y2",
                    mode="lines+markers",
                    line={"color": SOFT_GOLD, "width": 3},
                )
            )

            revenue_fig.update_layout(
                title="Omzet en conversieratio",
                yaxis={"tickprefix": "€ "},
                yaxis2={
                    "overlaying": "y",
                    "side": "right",
                    "showgrid": False,
                    "ticksuffix": "%",
                },
            )

            st.plotly_chart(
                apply_plotly_layout(revenue_fig),
                use_container_width=True,
            )

    add_space()

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Bereik</h4>
                <p>
                    De marketingkanalen leverden
                    <strong>{format_number(current_sessions)}</strong>
                    sessies op in deze periode.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Commerciële waarde</h4>
                <p>
                    De totale omzet is
                    <strong>{format_euro(current_revenue)}</strong>,
                    oftewel <strong>{format_euro(revenue_per_session)}</strong>
                    per sessie.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Conversie</h4>
                <p>
                    De gemiddelde conversieratio is
                    <strong>{format_percent(current_conversion)}</strong>.
                    Vergelijk kanalen op kwaliteit, niet alleen volume.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab_channels:
    st.subheader("Kanaalprestaties")

    if channels.empty:
        st.warning("Geen kanaaldata gevonden.")
    elif "sessiondefaultchannelgroup" not in channels.columns:
        st.warning("Kanaaldata mist `sessiondefaultchannelgroup`.")
    elif channel_metric not in channels.columns:
        st.warning(f"Kanaaldata mist `{channel_metric}`.")
    else:
        channel_summary = (
            channels
            .groupby("sessiondefaultchannelgroup", as_index=False)
            .sum(numeric_only=True)
        )

        if {"totalrevenue", "sessions"}.issubset(channel_summary.columns):
            channel_summary["revenue_per_session"] = (
                channel_summary["totalrevenue"]
                / channel_summary["sessions"].replace(0, pd.NA)
            ).fillna(0)

        if {"transactions", "sessions"}.issubset(channel_summary.columns):
            channel_summary["conversion_rate"] = (
                channel_summary["transactions"]
                / channel_summary["sessions"].replace(0, pd.NA)
                * 100
            ).fillna(0)

        top_channels = (
            channel_summary
            .dropna(subset=[channel_metric])
            .sort_values(channel_metric, ascending=False)
            .head(top_n)
        )

        channel_fig = px.bar(
            top_channels,
            x=channel_metric,
            y="sessiondefaultchannelgroup",
            orientation="h",
            text=channel_metric,
            title=f"Top {top_n} kanalen op {channel_metric}",
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
            apply_plotly_layout(channel_fig, height=560),
            use_container_width=True,
        )

        st.dataframe(
            channel_summary.sort_values(channel_metric, ascending=False),
            use_container_width=True,
            hide_index=True,
        )


with tab_campaigns:
    st.subheader("Campagneprestaties")

    if campaigns.empty:
        st.warning("Geen campagnedata gevonden.")
    elif "campaignname" not in campaigns.columns:
        st.warning("Campagnedata mist `campaignname`.")
    elif campaign_metric not in campaigns.columns:
        st.warning(f"Campagnedata mist `{campaign_metric}`.")
    else:
        campaign_summary = (
            campaigns
            .groupby("campaignname", as_index=False)
            .sum(numeric_only=True)
        )

        if {"totalrevenue", "sessions"}.issubset(campaign_summary.columns):
            campaign_summary["revenue_per_session"] = (
                campaign_summary["totalrevenue"]
                / campaign_summary["sessions"].replace(0, pd.NA)
            ).fillna(0)

        if {"transactions", "sessions"}.issubset(campaign_summary.columns):
            campaign_summary["conversion_rate"] = (
                campaign_summary["transactions"]
                / campaign_summary["sessions"].replace(0, pd.NA)
                * 100
            ).fillna(0)

        top_campaigns = (
            campaign_summary
            .dropna(subset=[campaign_metric])
            .sort_values(campaign_metric, ascending=False)
            .head(top_n)
        )

        campaign_fig = px.bar(
            top_campaigns,
            x=campaign_metric,
            y="campaignname",
            orientation="h",
            text=campaign_metric,
            title=f"Top {top_n} campagnes op {campaign_metric}",
            color_discrete_sequence=[SOFT_GREEN],
        )

        campaign_fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
        )

        campaign_fig.update_layout(
            yaxis={"categoryorder": "total ascending"},
        )

        st.plotly_chart(
            apply_plotly_layout(campaign_fig, height=560),
            use_container_width=True,
        )

        st.dataframe(
            campaign_summary.sort_values(campaign_metric, ascending=False),
            use_container_width=True,
            hide_index=True,
        )


with tab_revenue:
    st.subheader("Omzetverdeling per kanaal")

    if channels.empty or not {
        "sessiondefaultchannelgroup",
        "totalrevenue",
    }.issubset(channels.columns):
        st.warning("Kanaaldata mist omzetinformatie voor deze analyse.")
    else:
        revenue_by_channel = (
            channels
            .groupby("sessiondefaultchannelgroup", as_index=False)["totalrevenue"]
            .sum()
            .sort_values("totalrevenue", ascending=False)
        )

        revenue_col1, revenue_col2 = st.columns(2)

        with revenue_col1:
            revenue_donut = px.pie(
                revenue_by_channel,
                names="sessiondefaultchannelgroup",
                values="totalrevenue",
                hole=0.58,
                title="Omzetaandeel per kanaal",
                color_discrete_sequence=[
                    BRAND_GREEN,
                    SOFT_GOLD,
                    SOFT_GREEN,
                    SOFT_BLUE,
                    "#b6c5b9",
                ],
            )

            revenue_donut.update_traces(textinfo="percent+label")

            st.plotly_chart(
                apply_plotly_layout(revenue_donut, height=520),
                use_container_width=True,
            )

        with revenue_col2:
            revenue_bar = px.bar(
                revenue_by_channel.head(top_n),
                x="totalrevenue",
                y="sessiondefaultchannelgroup",
                orientation="h",
                title="Omzet per kanaal",
                color_discrete_sequence=[BRAND_GREEN],
            )

            revenue_bar.update_xaxes(tickprefix="€ ")
            revenue_bar.update_layout(
                yaxis={"categoryorder": "total ascending"},
            )

            st.plotly_chart(
                apply_plotly_layout(revenue_bar, height=520),
                use_container_width=True,
            )

    add_space()

    st.subheader("Marketingkansen")

    if not channels.empty and {
        "sessiondefaultchannelgroup",
        "sessions",
        "totalrevenue",
    }.issubset(channels.columns):
        opportunity_data = (
            channels
            .groupby("sessiondefaultchannelgroup", as_index=False)
            .sum(numeric_only=True)
        )

        opportunity_data["revenue_per_session"] = (
            opportunity_data["totalrevenue"]
            / opportunity_data["sessions"].replace(0, pd.NA)
        ).fillna(0)

        opportunity_data["traffic_share"] = (
            opportunity_data["sessions"]
            / opportunity_data["sessions"].sum()
            * 100
        ).fillna(0)

        opportunity_data["revenue_share"] = (
            opportunity_data["totalrevenue"]
            / opportunity_data["totalrevenue"].sum()
            * 100
        ).fillna(0)

        opportunity_data["diagnose"] = opportunity_data.apply(
            lambda row: (
                "Veel verkeer, lage omzet"
                if row["traffic_share"] > row["revenue_share"]
                else "Sterke omzetkwaliteit"
            ),
            axis=1,
        )

        st.dataframe(
            opportunity_data.sort_values("revenue_per_session", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


with tab_data:
    st.subheader("Datakwaliteit")

    data_col1, data_col2, data_col3 = st.columns(3)

    with data_col1:
        st.metric("Overview-rijen", len(overview))

    with data_col2:
        st.metric("Kanalen", len(channels))

    with data_col3:
        st.metric("Campagnes", len(campaigns))

    if show_raw_data:
        add_space()

        st.subheader("Overview")
        st.dataframe(overview, use_container_width=True, hide_index=True)

        st.subheader("Channels")
        st.dataframe(channels, use_container_width=True, hide_index=True)

        st.subheader("Campaigns")
        st.dataframe(campaigns, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")


st.caption("Van Duinkerken Marketing Dashboard · Streamlit · Plotly · Google Sheets")