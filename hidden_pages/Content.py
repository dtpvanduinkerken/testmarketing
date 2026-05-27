import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# =====================================================
# Pagina-configuratie
# =====================================================

st.set_page_config(
    page_title="VDK Content Dashboard",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "social": f"{BASE_URL}/social_media",
    "newsletter": f"{BASE_URL}/nieuwsbrief",
    "landing": f"{BASE_URL}/landing_pages",
}

BRAND_GREEN = "#084422"
BRAND_BEIGE = "#f5f1e8"
BRAND_GOLD = "#c9a646"
BRAND_LIGHT_GREEN = "#8cbe26"
BRAND_BLUE = "#2f80ed"
TEXT_DARK = "#1f2933"

# =====================================================
# Styling
# =====================================================

st.markdown(
    f"""
    <link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

    <style>
    html, body, [data-testid="stAppViewContainer"] {{
        background: {BRAND_BEIGE};
        font-family: 'sofia-pro', sans-serif;
        color: {TEXT_DARK};
    }}

    .block-container {{
        padding: 2rem 2.5rem 3rem 2.5rem;
        max-width: 1500px;
    }}

    h1, h2, h3 {{
        color: {BRAND_GREEN};
        letter-spacing: -0.03em;
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {BRAND_GREEN} 0%, #052c16 100%);
    }}

    [data-testid="stSidebar"] * {{
        color: white;
    }}

    [data-testid="stMetric"] {{
        background: white;
        border: 1px solid rgba(8, 68, 34, 0.12);
        border-radius: 22px;
        padding: 1.15rem 1.25rem;
        box-shadow: 0 14px 35px rgba(8, 68, 34, 0.08);
    }}

    [data-testid="stMetricValue"] {{
        color: {BRAND_GREEN};
        font-weight: 800;
    }}

    .hero-card {{
        background: linear-gradient(135deg, {BRAND_GREEN} 0%, #0d5f31 100%);
        color: white;
        padding: 2rem;
        border-radius: 28px;
        margin-bottom: 1.5rem;
        box-shadow: 0 20px 45px rgba(8, 68, 34, 0.20);
    }}

    .hero-card h1 {{
        color: white;
        margin-bottom: 0.35rem;
    }}

    .hero-card p {{
        color: rgba(255, 255, 255, 0.88);
        margin: 0;
        font-size: 1.05rem;
    }}

    .insight-card {{
        background: white;
        border-left: 6px solid {BRAND_GOLD};
        border-radius: 20px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 12px 28px rgba(8, 68, 34, 0.07);
        min-height: 132px;
    }}

    .insight-card h4 {{
        color: {BRAND_GREEN};
        margin: 0 0 0.45rem 0;
    }}

    .insight-card p {{
        color: #5f6b62;
        margin: 0;
    }}

    .section-note {{
        color: #627067;
        font-size: 0.94rem;
        margin-top: -0.4rem;
        margin-bottom: 1rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# Helpers
# =====================================================


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


def convert_columns_to_numeric(dataframe: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    dataframe = dataframe.copy()

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = parse_numeric(dataframe[column])

    return dataframe


def clean_social(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(
        dataframe,
        ["likes", "comments", "shares", "views", "saves", "engagement"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
        dataframe = dataframe.dropna(subset=["date"])
        dataframe = dataframe.sort_values("date")

    if "engagement" not in dataframe.columns:
        engagement_parts = [
            column for column in ["likes", "comments", "shares", "saves"]
            if column in dataframe.columns
        ]
        if engagement_parts:
            dataframe["engagement"] = dataframe[engagement_parts].sum(axis=1)

    if {"engagement", "views"}.issubset(dataframe.columns):
        dataframe["engagement_rate"] = (
            dataframe["engagement"] / dataframe["views"] * 100
        ).fillna(0)

    return dataframe


def clean_newsletter(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(
        dataframe,
        ["opens", "clicks", "open_rate", "click_rate", "omzet", "revenue"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
        dataframe = dataframe.sort_values("date")

    if "omzet" not in dataframe.columns and "revenue" in dataframe.columns:
        dataframe["omzet"] = dataframe["revenue"]

    return dataframe


def clean_landing(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(
        dataframe,
        ["sessions", "users", "engagedsessions", "conversions", "revenue"],
    )

    if {"conversions", "sessions"}.issubset(dataframe.columns):
        dataframe["conversion_rate"] = (
            dataframe["conversions"] / dataframe["sessions"] * 100
        ).fillna(0)

    return dataframe


def filter_by_period(dataframe: pd.DataFrame, period_label: str) -> pd.DataFrame:
    if "date" not in dataframe.columns or dataframe.empty:
        return dataframe.copy()

    period_days = {
        "Laatste 7 dagen": 7,
        "Laatste 30 dagen": 30,
        "Laatste 90 dagen": 90,
        "Alles": None,
    }[period_label]

    if period_days is None:
        return dataframe.copy()

    latest_date = dataframe["date"].max()
    start_date = latest_date - pd.Timedelta(days=period_days - 1)

    return dataframe[dataframe["date"] >= start_date]


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
        paper_bgcolor="white",
        plot_bgcolor="white",
        font={"family": "Sofia Pro, Arial", "color": TEXT_DARK},
        margin={"l": 20, "r": 20, "t": 55, "b": 25},
        hovermode="x unified",
        legend={"orientation": "h", "y": 1.08, "x": 0},
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(8, 68, 34, 0.08)")
    return fig

# =====================================================
# Data laden
# =====================================================

with st.spinner("Contentdata laden..."):
    social = clean_social(load_sheet(SHEET_URLS["social"]))
    newsletter = clean_newsletter(load_sheet(SHEET_URLS["newsletter"]))
    landing = clean_landing(load_sheet(SHEET_URLS["landing"]))

# =====================================================
# Sidebar
# =====================================================

st.sidebar.markdown("# Van Duinkerken")
st.sidebar.markdown("### Content")
st.sidebar.divider()

period = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

available_platforms = ["Alles"]
if "platform" in social.columns and not social.empty:
    available_platforms += sorted(social["platform"].dropna().astype(str).unique().tolist())

platform_filter = st.sidebar.selectbox("Platform", available_platforms)

ranking_metric = st.sidebar.selectbox(
    "Sorteer content op",
    ["views", "engagement", "engagement_rate", "shares", "saves"],
)

top_n = st.sidebar.slider("Aantal items", min_value=5, max_value=25, value=10)
show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)

filtered_social = filter_by_period(social, period)
filtered_newsletter = filter_by_period(newsletter, period)

if platform_filter != "Alles" and "platform" in filtered_social.columns:
    filtered_social = filtered_social[
        filtered_social["platform"].astype(str).str.lower() == platform_filter.lower()
    ]

if filtered_social.empty and newsletter.empty and landing.empty:
    st.error("Geen contentdata beschikbaar.")
    st.stop()

# =====================================================
# KPI-data
# =====================================================

total_views = filtered_social["views"].sum() if "views" in filtered_social.columns else 0
total_engagement = (
    filtered_social["engagement"].sum()
    if "engagement" in filtered_social.columns
    else 0
)
total_shares = filtered_social["shares"].sum() if "shares" in filtered_social.columns else 0
avg_engagement_rate = (
    filtered_social["engagement_rate"].mean()
    if "engagement_rate" in filtered_social.columns
    else 0
)
avg_open_rate = (
    filtered_newsletter["open_rate"].mean()
    if "open_rate" in filtered_newsletter.columns and not filtered_newsletter.empty
    else 0
)
newsletter_revenue = (
    filtered_newsletter["omzet"].sum()
    if "omzet" in filtered_newsletter.columns
    else 0
)

period_text = period.lower()
if "date" in filtered_social.columns and not filtered_social.empty:
    period_text = f"{filtered_social['date'].min().date()} t/m {filtered_social['date'].max().date()}"

# =====================================================
# Header
# =====================================================

st.markdown(
    f"""
    <div class="hero-card">
        <h1>Content Performance</h1>
        <p>
            Inzicht in social media, nieuwsbrieven, contentpagina's en engagement.<br>
            Periode: <strong>{period_text}</strong> · Platform: <strong>{platform_filter}</strong>.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# =====================================================
# KPI's
# =====================================================

metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    st.metric("Views", format_number(total_views))

with metric_col2:
    st.metric("Engagement", format_number(total_engagement))

with metric_col3:
    st.metric("Shares", format_number(total_shares))

with metric_col4:
    st.metric("Engagement rate", format_percent(avg_engagement_rate))

with metric_col5:
    st.metric("Nieuwsbrief open rate", format_percent(avg_open_rate))

# =====================================================
# Tabs
# =====================================================

tab_overview, tab_social, tab_newsletter, tab_pages, tab_data = st.tabs(
    ["📈 Overzicht", "📱 Social", "✉️ Nieuwsbrief", "📄 Pagina's", "🔎 Data"]
)

with tab_overview:
    chart_col, side_col = st.columns([2, 1])

    with chart_col:
        st.markdown("### Content performance")
        st.markdown(
            "<p class='section-note'>Views en engagement over tijd binnen de geselecteerde periode.</p>",
            unsafe_allow_html=True,
        )

        if {"date", "views", "engagement"}.issubset(filtered_social.columns):
            social_trend = (
                filtered_social
                .groupby("date", as_index=False)[["views", "engagement"]]
                .sum()
            )
            trend_data = social_trend.melt(
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
                title="Bereik en interactie",
                color_discrete_sequence=[BRAND_GREEN, BRAND_GOLD],
            )
            st.plotly_chart(apply_plotly_layout(trend_fig), use_container_width=True)
        else:
            st.info("Geen social trenddata beschikbaar.")

    with side_col:
        st.markdown("### Contentmix")

        if "platform" in filtered_social.columns and not filtered_social.empty:
            platform_data = (
                filtered_social
                .groupby("platform", as_index=False)["views"]
                .sum()
                .sort_values("views", ascending=False)
            )
            platform_fig = px.pie(
                platform_data,
                names="platform",
                values="views",
                hole=0.58,
                title="Views per platform",
                color_discrete_sequence=[BRAND_GREEN, BRAND_GOLD, BRAND_LIGHT_GREEN, BRAND_BLUE],
            )
            platform_fig.update_traces(textinfo="percent+label")
            st.plotly_chart(apply_plotly_layout(platform_fig), use_container_width=True)
        else:
            st.info("Geen platformdata beschikbaar.")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Bereik</h4>
                <p>
                    De content behaalde <strong>{format_number(total_views)}</strong>
                    views in de geselecteerde periode.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Interactie</h4>
                <p>
                    Totale engagement: <strong>{format_number(total_engagement)}</strong>.
                    De gemiddelde engagement rate is <strong>{format_percent(avg_engagement_rate)}</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Nieuwsbrief</h4>
                <p>
                    Gemiddelde open rate: <strong>{format_percent(avg_open_rate)}</strong>.
                    Nieuwsbriefomzet: <strong>{format_euro(newsletter_revenue)}</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_social:
    st.markdown("### Best presterende posts")

    if filtered_social.empty:
        st.warning("Geen social data gevonden voor deze selectie.")
    elif "topic" not in filtered_social.columns:
        st.warning("Social data mist de kolom `topic`.")
    elif ranking_metric not in filtered_social.columns:
        st.warning(f"Social data mist `{ranking_metric}`.")
    else:
        top_posts = (
            filtered_social
            .dropna(subset=[ranking_metric])
            .sort_values(ranking_metric, ascending=False)
            .head(top_n)
        )

        post_fig = px.bar(
            top_posts,
            x=ranking_metric,
            y="topic",
            orientation="h",
            text=ranking_metric,
            title=f"Top {top_n} posts op {ranking_metric}",
            color_discrete_sequence=[BRAND_GREEN],
        )
        post_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        post_fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_plotly_layout(post_fig, height=560), use_container_width=True)

        if {"views", "engagement", "platform"}.issubset(filtered_social.columns):
            scatter_fig = px.scatter(
                filtered_social,
                x="views",
                y="engagement",
                color="platform",
                size="shares" if "shares" in filtered_social.columns else None,
                hover_name="topic",
                title="Views versus engagement",
                color_discrete_sequence=[BRAND_GREEN, BRAND_GOLD, BRAND_LIGHT_GREEN, BRAND_BLUE],
            )
            st.plotly_chart(apply_plotly_layout(scatter_fig, height=500), use_container_width=True)

        social_columns = [
            column for column in [
                "date",
                "platform",
                "topic",
                "views",
                "likes",
                "comments",
                "shares",
                "saves",
                "engagement",
                "engagement_rate",
            ]
            if column in filtered_social.columns
        ]

        st.dataframe(
            filtered_social[social_columns].sort_values(ranking_metric, ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Datum"),
                "platform": st.column_config.TextColumn("Platform"),
                "topic": st.column_config.TextColumn("Topic"),
                "views": st.column_config.NumberColumn("Views", format="%.0f"),
                "likes": st.column_config.NumberColumn("Likes", format="%.0f"),
                "comments": st.column_config.NumberColumn("Comments", format="%.0f"),
                "shares": st.column_config.NumberColumn("Shares", format="%.0f"),
                "saves": st.column_config.NumberColumn("Saves", format="%.0f"),
                "engagement": st.column_config.NumberColumn("Engagement", format="%.0f"),
                "engagement_rate": st.column_config.NumberColumn("Engagement rate", format="%.1f%%"),
            },
        )

with tab_newsletter:
    st.markdown("### Nieuwsbrief prestaties")

    if filtered_newsletter.empty:
        st.warning("Geen nieuwsbriefdata gevonden.")
    elif "campagne" not in filtered_newsletter.columns:
        st.warning("Nieuwsbriefdata mist de kolom `campagne`.")
    else:
        newsletter_col1, newsletter_col2 = st.columns(2)

        with newsletter_col1:
            if "open_rate" in filtered_newsletter.columns:
                open_fig = px.bar(
                    filtered_newsletter.sort_values("open_rate", ascending=False).head(top_n),
                    x="open_rate",
                    y="campagne",
                    orientation="h",
                    title="Top nieuwsbrieven op open rate",
                    color_discrete_sequence=[BRAND_LIGHT_GREEN],
                )
                open_fig.update_xaxes(ticksuffix="%")
                open_fig.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(apply_plotly_layout(open_fig, height=500), use_container_width=True)

        with newsletter_col2:
            if "click_rate" in filtered_newsletter.columns:
                click_fig = px.bar(
                    filtered_newsletter.sort_values("click_rate", ascending=False).head(top_n),
                    x="click_rate",
                    y="campagne",
                    orientation="h",
                    title="Top nieuwsbrieven op click rate",
                    color_discrete_sequence=[BRAND_GOLD],
                )
                click_fig.update_xaxes(ticksuffix="%")
                click_fig.update_layout(yaxis={"categoryorder": "total ascending"})
                st.plotly_chart(apply_plotly_layout(click_fig, height=500), use_container_width=True)

        newsletter_columns = [
            column for column in [
                "date",
                "campagne",
                "opens",
                "clicks",
                "open_rate",
                "click_rate",
                "omzet",
            ]
            if column in filtered_newsletter.columns
        ]

        st.dataframe(
            filtered_newsletter[newsletter_columns],
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": st.column_config.DateColumn("Datum"),
                "campagne": st.column_config.TextColumn("Campagne"),
                "opens": st.column_config.NumberColumn("Opens", format="%.0f"),
                "clicks": st.column_config.NumberColumn("Clicks", format="%.0f"),
                "open_rate": st.column_config.NumberColumn("Open rate", format="%.1f%%"),
                "click_rate": st.column_config.NumberColumn("Click rate", format="%.1f%%"),
                "omzet": st.column_config.NumberColumn("Omzet", format="€ %.0f"),
            },
        )

with tab_pages:
    st.markdown("### Best presterende contentpagina's")

    if landing.empty:
        st.warning("Geen landingpage-data gevonden.")
    elif not {"landingpage", "sessions"}.issubset(landing.columns):
        st.warning("Landingpage-data mist `landingpage` of `sessions`.")
    else:
        top_pages = (
            landing
            .dropna(subset=["sessions"])
            .sort_values("sessions", ascending=False)
            .head(15)
        )

        landing_fig = px.bar(
            top_pages,
            x="sessions",
            y="landingpage",
            orientation="h",
            text="sessions",
            title="Top contentpagina's op sessies",
            color_discrete_sequence=[BRAND_GREEN],
        )
        landing_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        landing_fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_plotly_layout(landing_fig, height=620), use_container_width=True)

        landing_columns = [
            column for column in [
                "landingpage",
                "sessions",
                "users",
                "engagedsessions",
                "conversions",
                "conversion_rate",
                "revenue",
            ]
            if column in landing.columns
        ]

        st.dataframe(
            landing[landing_columns].sort_values("sessions", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "landingpage": st.column_config.TextColumn("Landingpage"),
                "sessions": st.column_config.NumberColumn("Sessies", format="%.0f"),
                "users": st.column_config.NumberColumn("Gebruikers", format="%.0f"),
                "engagedsessions": st.column_config.NumberColumn("Engaged sessies", format="%.0f"),
                "conversions": st.column_config.NumberColumn("Conversies", format="%.0f"),
                "conversion_rate": st.column_config.NumberColumn("Conversie", format="%.1f%%"),
                "revenue": st.column_config.NumberColumn("Omzet", format="€ %.0f"),
            },
        )

with tab_data:
    st.markdown("### Datakwaliteit")

    data_col1, data_col2, data_col3 = st.columns(3)

    with data_col1:
        st.metric("Social posts", len(social))

    with data_col2:
        st.metric("Nieuwsbrieven", len(newsletter))

    with data_col3:
        st.metric("Landingpages", len(landing))

    if show_raw_data:
        st.markdown("#### Social media")
        st.dataframe(social, use_container_width=True, hide_index=True)

        st.markdown("#### Nieuwsbrief")
        st.dataframe(newsletter, use_container_width=True, hide_index=True)

        st.markdown("#### Landingpages")
        st.dataframe(landing, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")

st.markdown("---")
st.caption("Van Duinkerken Content Dashboard · Streamlit · Plotly · Google Sheets")
