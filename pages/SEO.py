import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# =====================================================
# Pagina-configuratie
# =====================================================

st.set_page_config(
    page_title="VDK SEO Dashboard",
    page_icon="🔎",
    layout="wide",
    initial_sidebar_state="expanded",
)

SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "seo": f"{BASE_URL}/seo",
    "landing": f"{BASE_URL}/landing_pages",
}

BRAND_GREEN = "#084422"
BRAND_BEIGE = "#f5f1e8"
BRAND_GOLD = "#c9a646"
BRAND_LIGHT_GREEN = "#8cbe26"
BRAND_BLUE = "#2f80ed"
BRAND_RED = "#b54747"
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

    [data-testid="stMetricLabel"] {{
        color: #657267;
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


def convert_columns_to_numeric(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    dataframe = dataframe.copy()

    for column in columns:
        if column in dataframe.columns:
            dataframe[column] = parse_numeric(dataframe[column])

    return dataframe


def clean_seo(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(
        dataframe,
        ["clicks", "impressions", "ctr", "position"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
        dataframe = dataframe.dropna(subset=["date"])
        dataframe = dataframe.sort_values("date")

    if {"clicks", "impressions"}.issubset(dataframe.columns):
        dataframe["calculated_ctr"] = (
            dataframe["clicks"] / dataframe["impressions"] * 100
        ).fillna(0)

    if "ctr" not in dataframe.columns and "calculated_ctr" in dataframe.columns:
        dataframe["ctr"] = dataframe["calculated_ctr"]

    return dataframe


def clean_landing_pages(dataframe: pd.DataFrame) -> pd.DataFrame:
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
        (dataframe["date"] >= previous_start) &
        (dataframe["date"] <= previous_end)
    ]

    return current, previous


def calculate_delta(current: float, previous: float, inverse: bool = False) -> float:
    if pd.isna(current) or pd.isna(previous) or previous == 0:
        return 0.0

    delta = round(((current - previous) / previous) * 100, 1)

    if inverse:
        return delta * -1

    return delta


def weighted_average(
    dataframe: pd.DataFrame,
    value_column: str,
    weight_column: str,
) -> float:
    if not {value_column, weight_column}.issubset(dataframe.columns):
        return 0.0

    valid_data = dataframe.dropna(subset=[value_column, weight_column])
    total_weight = valid_data[weight_column].sum()

    if total_weight == 0:
        return 0.0

    return (valid_data[value_column] * valid_data[weight_column]).sum() / total_weight


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


def show_metric(
    label: str,
    value: str,
    delta: float | None = None,
) -> None:
    if delta is None:
        st.metric(label=label, value=value)
        return

    st.metric(
        label=label,
        value=value,
        delta=f"{delta:+.1f}%".replace(".", ","),
    )

# =====================================================
# Data laden
# =====================================================

with st.spinner("SEO-data laden..."):
    seo = clean_seo(load_sheet(SHEET_URLS["seo"]))
    landing = clean_landing_pages(load_sheet(SHEET_URLS["landing"]))

if seo.empty:
    st.error("Geen geldige SEO-data gevonden. Controleer de sheet `seo`.")
    st.stop()

required_columns = {"clicks", "impressions", "ctr", "position"}
missing_columns = required_columns.difference(seo.columns)

if missing_columns:
    st.error(f"De SEO-sheet mist deze kolommen: {', '.join(sorted(missing_columns))}.")
    st.stop()

# =====================================================
# Sidebar
# =====================================================

st.sidebar.markdown("# Van Duinkerken")
st.sidebar.markdown("### SEO")
st.sidebar.divider()

period = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

minimum_impressions = st.sidebar.slider(
    "Minimale impressies voor kansen",
    min_value=50,
    max_value=1000,
    value=100,
    step=50,
)

position_range = st.sidebar.slider(
    "Positierange voor optimalisatie",
    min_value=1,
    max_value=50,
    value=(5, 20),
)

show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)

filtered_seo, previous_seo = filter_period(seo, period)

if filtered_seo.empty:
    st.error("Geen SEO-data beschikbaar voor deze periode.")
    st.stop()

if "date" in filtered_seo.columns:
    start_date = filtered_seo["date"].min().date()
    end_date = filtered_seo["date"].max().date()
    period_text = f"{start_date} t/m {end_date}"
else:
    period_text = period.lower()

# =====================================================
# KPI-data
# =====================================================

current_clicks = filtered_seo["clicks"].sum()
previous_clicks = previous_seo["clicks"].sum()

current_impressions = filtered_seo["impressions"].sum()
previous_impressions = previous_seo["impressions"].sum()

current_ctr = (
    current_clicks / current_impressions * 100
    if current_impressions > 0
    else 0
)
previous_ctr = (
    previous_clicks / previous_impressions * 100
    if previous_impressions > 0
    else 0
)

current_position = weighted_average(filtered_seo, "position", "impressions")
previous_position = weighted_average(previous_seo, "position", "impressions")

current_queries = (
    filtered_seo["query"].nunique()
    if "query" in filtered_seo.columns
    else 0
)
previous_queries = (
    previous_seo["query"].nunique()
    if "query" in previous_seo.columns
    else 0
)

# =====================================================
# Header
# =====================================================

st.markdown(
    f"""
    <div class="hero-card">
        <h1>SEO Performance</h1>
        <p>
            Inzicht in organische groei, zoekwoorden, rankings, CTR en landingpage-kansen.<br>
            Periode: <strong>{period_text}</strong>.
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
    show_metric(
        "Organische clicks",
        format_number(current_clicks),
        calculate_delta(current_clicks, previous_clicks),
    )

with metric_col2:
    show_metric(
        "Impressies",
        format_number(current_impressions),
        calculate_delta(current_impressions, previous_impressions),
    )

with metric_col3:
    show_metric(
        "CTR",
        format_percent(current_ctr),
        calculate_delta(current_ctr, previous_ctr),
    )

with metric_col4:
    show_metric(
        "Gem. positie",
        f"{current_position:.1f}".replace(".", ","),
        calculate_delta(current_position, previous_position, inverse=True),
    )

with metric_col5:
    show_metric(
        "Actieve queries",
        format_number(current_queries),
        calculate_delta(current_queries, previous_queries),
    )

# =====================================================
# Tabs
# =====================================================

tab_overview, tab_keywords, tab_pages, tab_opportunities, tab_data = st.tabs(
    ["📈 Overzicht", "🔤 Zoekwoorden", "📄 Landingpages", "🚀 Kansen", "🔎 Data"]
)

with tab_overview:
    chart_col, side_col = st.columns([2, 1])

    with chart_col:
        st.markdown("### SEO ontwikkeling")
        st.markdown(
            "<p class='section-note'>Clicks en impressies over tijd binnen de geselecteerde periode.</p>",
            unsafe_allow_html=True,
        )

        if "date" in filtered_seo.columns:
            trend = (
                filtered_seo
                .groupby("date", as_index=False)[["clicks", "impressions"]]
                .sum()
            )

            trend_data = trend.melt(
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
                title="Organische zichtbaarheid",
                color_discrete_sequence=[BRAND_GREEN, BRAND_GOLD],
            )
            st.plotly_chart(apply_plotly_layout(trend_fig), use_container_width=True)
        else:
            st.info("Geen datumkolom beschikbaar voor trendanalyse.")

    with side_col:
        st.markdown("### CTR & positie")

        if "date" in filtered_seo.columns:
            ctr_position = (
                filtered_seo
                .groupby("date", as_index=False)
                .apply(
                    lambda group: pd.Series(
                        {
                            "ctr": (
                                group["clicks"].sum() /
                                group["impressions"].sum() * 100
                                if group["impressions"].sum() > 0
                                else 0
                            ),
                            "position": weighted_average(
                                group,
                                "position",
                                "impressions",
                            ),
                        }
                    )
                )
                .reset_index(drop=True)
            )

            ctr_fig = go.Figure()
            ctr_fig.add_trace(
                go.Scatter(
                    x=ctr_position["date"],
                    y=ctr_position["ctr"],
                    name="CTR",
                    mode="lines+markers",
                    line={"color": BRAND_GREEN, "width": 3},
                )
            )
            ctr_fig.add_trace(
                go.Scatter(
                    x=ctr_position["date"],
                    y=ctr_position["position"],
                    name="Gem. positie",
                    mode="lines+markers",
                    yaxis="y2",
                    line={"color": BRAND_GOLD, "width": 3},
                )
            )
            ctr_fig.update_layout(
                title="CTR versus gemiddelde positie",
                yaxis={"ticksuffix": "%"},
                yaxis2={
                    "overlaying": "y",
                    "side": "right",
                    "showgrid": False,
                    "autorange": "reversed",
                },
            )
            st.plotly_chart(apply_plotly_layout(ctr_fig), use_container_width=True)

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>SEO-groei</h4>
                <p>
                    Organische clicks: <strong>{format_number(current_clicks)}</strong>.
                    Groei versus vorige periode:
                    <strong>{calculate_delta(current_clicks, previous_clicks):+.1f}%</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Zichtbaarheid</h4>
                <p>
                    De site kreeg <strong>{format_number(current_impressions)}</strong>
                    impressies. Hogere impressies met lage CTR zijn directe optimalisatiekansen.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Rankingkwaliteit</h4>
                <p>
                    De gewogen gemiddelde positie is
                    <strong>{current_position:.1f}</strong>. Queries tussen positie
                    {position_range[0]} en {position_range[1]} zijn vaak quick wins.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with tab_keywords:
    keyword_col, scatter_col = st.columns(2)

    if "query" not in filtered_seo.columns:
        st.warning("De SEO-sheet mist de kolom `query`.")
    else:
        keyword_summary = (
            filtered_seo
            .groupby("query", as_index=False)
            .agg(
                clicks=("clicks", "sum"),
                impressions=("impressions", "sum"),
                position=("position", "mean"),
            )
        )
        keyword_summary["ctr"] = (
            keyword_summary["clicks"] / keyword_summary["impressions"] * 100
        ).fillna(0)

        with keyword_col:
            st.markdown("### Top zoekwoorden")

            top_keywords = (
                keyword_summary
                .sort_values("clicks", ascending=False)
                .head(15)
            )

            keyword_fig = px.bar(
                top_keywords,
                x="clicks",
                y="query",
                orientation="h",
                text="clicks",
                title="Top 15 zoekwoorden op clicks",
                color_discrete_sequence=[BRAND_GREEN],
            )
            keyword_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
            keyword_fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(apply_plotly_layout(keyword_fig, height=560), use_container_width=True)

        with scatter_col:
            st.markdown("### CTR versus positie")

            scatter_data = keyword_summary[
                keyword_summary["impressions"] >= minimum_impressions
            ].copy()

            scatter_fig = px.scatter(
                scatter_data,
                x="position",
                y="ctr",
                size="impressions",
                color="clicks",
                hover_name="query",
                title="Zoekwoordkansen op basis van ranking en CTR",
                color_continuous_scale="Greens",
            )
            scatter_fig.update_xaxes(autorange="reversed", title="Gem. positie")
            scatter_fig.update_yaxes(title="CTR (%)")
            st.plotly_chart(apply_plotly_layout(scatter_fig, height=560), use_container_width=True)

        st.markdown("### Zoekwoordtabel")
        st.dataframe(
            keyword_summary.sort_values("clicks", ascending=False),
            use_container_width=True,
            hide_index=True,
            column_config={
                "query": st.column_config.TextColumn("Zoekwoord"),
                "clicks": st.column_config.NumberColumn("Clicks", format="%.0f"),
                "impressions": st.column_config.NumberColumn("Impressies", format="%.0f"),
                "ctr": st.column_config.NumberColumn("CTR", format="%.1f%%"),
                "position": st.column_config.NumberColumn("Positie", format="%.1f"),
            },
        )

with tab_pages:
    st.markdown("### Beste SEO landingpages")

    if landing.empty:
        st.warning("Geen landingpage-data gevonden.")
    elif {"landingpage", "sessions"}.issubset(landing.columns):
        top_pages = (
            landing
            .dropna(subset=["sessions"])
            .sort_values("sessions", ascending=False)
            .head(15)
        )

        page_fig = px.bar(
            top_pages,
            x="sessions",
            y="landingpage",
            orientation="h",
            text="sessions",
            title="Top 15 landingpages op organische sessies",
            color_discrete_sequence=[BRAND_LIGHT_GREEN],
        )
        page_fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        page_fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(apply_plotly_layout(page_fig, height=620), use_container_width=True)

        table_columns = [
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
            landing[table_columns].sort_values("sessions", ascending=False),
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
    else:
        st.warning("Landingpage-data mist `landingpage` of `sessions`.")

with tab_opportunities:
    st.markdown("### SEO kansen")
    st.markdown(
        "<p class='section-note'>Queries met veel impressies, lage CTR of posities net buiten de top 3.</p>",
        unsafe_allow_html=True,
    )

    if "query" not in filtered_seo.columns:
        st.warning("De SEO-sheet mist de kolom `query`.")
    else:
        opportunities = (
            filtered_seo
            .groupby("query", as_index=False)
            .agg(
                clicks=("clicks", "sum"),
                impressions=("impressions", "sum"),
                position=("position", "mean"),
            )
        )
        opportunities["ctr"] = (
            opportunities["clicks"] / opportunities["impressions"] * 100
        ).fillna(0)

        opportunities = opportunities[
            (opportunities["impressions"] >= minimum_impressions) &
            (opportunities["position"] >= position_range[0]) &
            (opportunities["position"] <= position_range[1])
        ].copy()

        opportunities["opportunity_score"] = (
            opportunities["impressions"] *
            (1 / opportunities["position"].clip(lower=1)) *
            (1 / (opportunities["ctr"] + 1))
        )

        opportunities = opportunities.sort_values(
            "opportunity_score",
            ascending=False,
        )

        opp_col1, opp_col2, opp_col3 = st.columns(3)

        with opp_col1:
            st.metric("Aantal kansen", format_number(len(opportunities)))

        with opp_col2:
            st.metric(
                "Gem. impressies per kans",
                format_number(opportunities["impressions"].mean()),
            )

        with opp_col3:
            st.metric(
                "Gem. CTR kansen",
                format_percent(opportunities["ctr"].mean()),
            )

        if not opportunities.empty:
            opportunity_fig = px.bar(
                opportunities.head(15),
                x="opportunity_score",
                y="query",
                orientation="h",
                title="Top SEO optimalisatiekansen",
                color="impressions",
                color_continuous_scale="Greens",
            )
            opportunity_fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(apply_plotly_layout(opportunity_fig, height=560), use_container_width=True)

            st.dataframe(
                opportunities[
                    [
                        "query",
                        "clicks",
                        "impressions",
                        "ctr",
                        "position",
                        "opportunity_score",
                    ]
                ],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "query": st.column_config.TextColumn("Zoekwoord"),
                    "clicks": st.column_config.NumberColumn("Clicks", format="%.0f"),
                    "impressions": st.column_config.NumberColumn("Impressies", format="%.0f"),
                    "ctr": st.column_config.NumberColumn("CTR", format="%.1f%%"),
                    "position": st.column_config.NumberColumn("Positie", format="%.1f"),
                    "opportunity_score": st.column_config.NumberColumn("Kansscore", format="%.1f"),
                },
            )
        else:
            st.info("Geen kansen gevonden met de huidige filters. Verlaag de minimale impressies of verruim de positierange.")

with tab_data:
    st.markdown("### Datakwaliteit")

    data_col1, data_col2, data_col3, data_col4 = st.columns(4)

    with data_col1:
        st.metric("SEO-rijen", len(seo))

    with data_col2:
        st.metric("Landingpages", len(landing))

    with data_col3:
        st.metric("Queries", format_number(current_queries))

    with data_col4:
        st.metric("Kolommen", len(seo.columns))

    if show_raw_data:
        st.markdown("#### SEO-data")
        st.dataframe(seo, use_container_width=True, hide_index=True)

        st.markdown("#### Landingpage-data")
        st.dataframe(landing, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")

st.markdown("---")
st.caption("Van Duinkerken SEO Dashboard · Streamlit · Plotly · Google Sheets")
