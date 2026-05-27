import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Customers Dashboard",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "channels": f"{BASE_URL}/channels",
    "campaigns": f"{BASE_URL}/campaigns",
}

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_GREEN = "#7d9b88"
SOFT_GOLD = "#c9a646"


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
        ["bezoekers", "sessies", "orders", "omzet", "conversie"],
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

    if {"transactions", "users"}.issubset(dataframe.columns):
        dataframe["user_conversion_rate"] = (
            dataframe["transactions"] / dataframe["users"].replace(0, pd.NA) * 100
        ).fillna(0)

    if {"totalrevenue", "users"}.issubset(dataframe.columns):
        dataframe["revenue_per_user"] = (
            dataframe["totalrevenue"] / dataframe["users"].replace(0, pd.NA)
        ).fillna(0)

    if {"sessions", "users"}.issubset(dataframe.columns):
        dataframe["sessions_per_user"] = (
            dataframe["sessions"] / dataframe["users"].replace(0, pd.NA)
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
            <div class="vdk-main-title">Customer performance</div>
            <div class="vdk-subtitle">
                Inzicht in klantgroei, loyaliteit, returning users, members
                en kanaalkwaliteit. Periode: <strong>{period_text}</strong>.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("Klantdata laden..."):
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
    channels = clean_channels(load_sheet(SHEET_URLS["channels"]))
    campaigns = clean_campaigns(load_sheet(SHEET_URLS["campaigns"]))


if overview.empty:
    st.error("Geen geldige klantdata gevonden. Controleer de sheet `overview_kpis`.")
    st.stop()


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Customers")
st.sidebar.divider()

period = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

returning_share = st.sidebar.slider(
    "Aandeel returning users",
    min_value=0,
    max_value=100,
    value=38,
    help="Gebruik dit alleen als returning-user data nog niet apart in de sheet staat.",
)

member_share = st.sidebar.slider(
    "Aandeel members",
    min_value=0,
    max_value=100,
    value=44,
    help="Gebruik dit alleen als memberdata nog niet apart beschikbaar is.",
)

show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)


filtered_overview, previous_overview = filter_period(overview, period)

if filtered_overview.empty:
    st.error("Geen klantdata beschikbaar voor deze periode.")
    st.stop()


if "date" in filtered_overview.columns:
    start_date = filtered_overview["date"].min().date()
    end_date = filtered_overview["date"].max().date()
    period_text = f"{start_date} t/m {end_date}"
else:
    period_text = period.lower()


current_users = filtered_overview["bezoekers"].sum()
previous_users = previous_overview["bezoekers"].sum()

current_sessions = filtered_overview["sessies"].sum()
previous_sessions = previous_overview["sessies"].sum()

current_orders = filtered_overview["orders"].sum()
previous_orders = previous_overview["orders"].sum()

current_revenue = filtered_overview["omzet"].sum()
previous_revenue = previous_overview["omzet"].sum()

current_conversion = filtered_overview["conversie"].mean()
previous_conversion = previous_overview["conversie"].mean()

sessions_per_user = current_sessions / current_users if current_users > 0 else 0
previous_sessions_per_user = (
    previous_sessions / previous_users
    if previous_users > 0
    else 0
)

revenue_per_user = current_revenue / current_users if current_users > 0 else 0
previous_revenue_per_user = (
    previous_revenue / previous_users
    if previous_users > 0
    else 0
)

returning_users = int(current_users * returning_share / 100)
new_users = int(current_users - returning_users)

member_users = int(current_users * member_share / 100)
non_member_users = int(current_users - member_users)

member_revenue = current_revenue * 0.58
non_member_revenue = current_revenue - member_revenue


render_header(period_text)


metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    show_metric(
        "Bezoekers",
        format_number(current_users),
        calculate_delta(current_users, previous_users),
    )

with metric_col2:
    show_metric(
        "Returning users",
        format_number(returning_users),
    )

with metric_col3:
    show_metric(
        "Orders",
        format_number(current_orders),
        calculate_delta(current_orders, previous_orders),
    )

with metric_col4:
    show_metric(
        "Conversieratio",
        format_percent(current_conversion),
        calculate_delta(current_conversion, previous_conversion),
    )

with metric_col5:
    show_metric(
        "Omzet per bezoeker",
        format_euro(revenue_per_user),
        calculate_delta(revenue_per_user, previous_revenue_per_user),
    )


add_space()


tab_overview, tab_segments, tab_channels, tab_loyalty, tab_data = st.tabs(
    ["Overzicht", "Segmenten", "Kanalen", "Loyaliteit", "Data"]
)


with tab_overview:
    chart_col, side_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Bezoekersontwikkeling")
        st.markdown(
            """
            <p class="section-note">
                Bezoekers en orders over tijd binnen de geselecteerde periode.
            </p>
            """,
            unsafe_allow_html=True,
        )

        if "date" in filtered_overview.columns:
            trend = (
                filtered_overview
                .groupby("date", as_index=False)[["bezoekers", "orders"]]
                .sum()
            )

            trend_data = trend.melt(
                id_vars="date",
                var_name="Metric",
                value_name="Waarde",
            )

            visitor_fig = px.line(
                trend_data,
                x="date",
                y="Waarde",
                color="Metric",
                markers=True,
                title="Klantgroei en orders",
                color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD],
            )

            st.plotly_chart(
                apply_plotly_layout(visitor_fig),
                use_container_width=True,
            )
        else:
            st.info("Geen datumkolom beschikbaar voor trendanalyse.")

    with side_col:
        st.subheader("Klantwaarde")

        value_data = pd.DataFrame(
            {
                "Metric": ["Sessies per bezoeker", "Omzet per bezoeker"],
                "Waarde": [sessions_per_user, revenue_per_user],
            }
        )

        value_fig = px.bar(
            value_data,
            x="Metric",
            y="Waarde",
            title="Klantkwaliteit",
            color="Metric",
            color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD],
        )

        st.plotly_chart(
            apply_plotly_layout(value_fig),
            use_container_width=True,
        )

    add_space()

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Klantbereik</h4>
                <p>
                    Deze periode trok <strong>{format_number(current_users)}</strong>
                    bezoekers en <strong>{format_number(current_sessions)}</strong>
                    sessies.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Klantwaarde</h4>
                <p>
                    De omzet per bezoeker is
                    <strong>{format_euro(revenue_per_user)}</strong>.
                    Dit beoordeelt kanaalkwaliteit beter dan alleen volume.
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
                    Focus op returning users en members voor hogere waarde.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab_segments:
    segment_col1, segment_col2 = st.columns(2)

    with segment_col1:
        st.subheader("Nieuwe vs returning users")

        returning_data = pd.DataFrame(
            {
                "Type": ["Nieuwe gebruikers", "Returning users"],
                "Aantal": [new_users, returning_users],
            }
        )

        returning_fig = px.pie(
            returning_data,
            names="Type",
            values="Aantal",
            hole=0.58,
            title="Verdeling gebruikers",
            color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD],
        )

        returning_fig.update_traces(textinfo="percent+label")

        st.plotly_chart(
            apply_plotly_layout(returning_fig, height=500),
            use_container_width=True,
        )

    with segment_col2:
        st.subheader("Members vs non-members")

        member_data = pd.DataFrame(
            {
                "Type": ["Members", "Non-members"],
                "Gebruikers": [member_users, non_member_users],
                "Omzet": [member_revenue, non_member_revenue],
            }
        )

        member_long = member_data.melt(
            id_vars="Type",
            var_name="Metric",
            value_name="Waarde",
        )

        member_fig = px.bar(
            member_long,
            x="Type",
            y="Waarde",
            color="Metric",
            barmode="group",
            title="Memberwaarde versus non-members",
            color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD],
        )

        st.plotly_chart(
            apply_plotly_layout(member_fig, height=500),
            use_container_width=True,
        )

    st.info(
        "Returning-user en membersegmenten zijn instelbare aannames zolang "
        "deze segmenten niet als aparte kolommen in de databron staan."
    )


with tab_channels:
    st.subheader("Beste kanalen voor klanten")

    if channels.empty:
        st.warning("Geen kanaaldata gevonden.")
    elif "sessiondefaultchannelgroup" not in channels.columns:
        st.warning("Kanaaldata mist `sessiondefaultchannelgroup`.")
    elif "users" not in channels.columns:
        st.warning("Kanaaldata mist `users`.")
    else:
        channel_summary = (
            channels
            .groupby("sessiondefaultchannelgroup", as_index=False)
            .sum(numeric_only=True)
        )

        if {"transactions", "users"}.issubset(channel_summary.columns):
            channel_summary["user_conversion_rate"] = (
                channel_summary["transactions"]
                / channel_summary["users"].replace(0, pd.NA)
                * 100
            ).fillna(0)

        if {"totalrevenue", "users"}.issubset(channel_summary.columns):
            channel_summary["revenue_per_user"] = (
                channel_summary["totalrevenue"]
                / channel_summary["users"].replace(0, pd.NA)
            ).fillna(0)

        channel_fig = px.bar(
            channel_summary.sort_values("users", ascending=False).head(12),
            x="users",
            y="sessiondefaultchannelgroup",
            orientation="h",
            text="users",
            title="Top kanalen op gebruikers",
            color_discrete_sequence=[SOFT_GREEN],
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
            channel_summary.sort_values("users", ascending=False),
            use_container_width=True,
            hide_index=True,
        )


with tab_loyalty:
    st.subheader("Loyaliteit en klantkwaliteit")

    loyalty_data = pd.DataFrame(
        {
            "Metric": [
                "Returning aandeel",
                "Member aandeel",
                "Sessies per bezoeker",
                "Conversieratio",
            ],
            "Waarde": [
                returning_share,
                member_share,
                sessions_per_user,
                current_conversion,
            ],
        }
    )

    loyalty_fig = px.bar(
        loyalty_data,
        x="Metric",
        y="Waarde",
        title="Loyaliteitsindicatoren",
        color="Metric",
        color_discrete_sequence=[
            BRAND_GREEN,
            SOFT_GOLD,
            SOFT_GREEN,
            "#b6c5b9",
        ],
    )

    st.plotly_chart(
        apply_plotly_layout(loyalty_fig, height=500),
        use_container_width=True,
    )

    loyalty_col1, loyalty_col2, loyalty_col3 = st.columns(3)

    with loyalty_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Returning users</h4>
                <p>
                    Geschat aandeel returning users:
                    <strong>{returning_share}%</strong>.
                    Verhoog dit met e-mail, remarketing en persoonlijke aanbevelingen.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with loyalty_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Members</h4>
                <p>
                    Geschat memberaandeel:
                    <strong>{member_share}%</strong>.
                    Maak membervoordelen zichtbaar op product- en checkoutpagina's.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with loyalty_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Herhaalgedrag</h4>
                <p>
                    Gemiddeld zijn er
                    <strong>{sessions_per_user:.2f}</strong>
                    sessies per bezoeker.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab_data:
    st.subheader("Datakwaliteit")

    data_col1, data_col2, data_col3 = st.columns(3)

    with data_col1:
        st.metric("Overview-rijen", len(overview))

    with data_col2:
        st.metric("Kanaalrijen", len(channels))

    with data_col3:
        st.metric("Campagnerijen", len(campaigns))

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


st.caption("Van Duinkerken Customers Dashboard · Streamlit · Plotly · Google Sheets")