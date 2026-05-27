import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Website Optimizations",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "landing": f"{BASE_URL}/landing_pages",
    "products": f"{BASE_URL}/products",
    "search": f"{BASE_URL}/site_search",
    "pagespeed": f"{BASE_URL}/page_speed",
    "funnel": f"{BASE_URL}/funnel",
}

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_GREEN = "#7d9b88"
SOFT_RED = "#c76f6f"


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
    min-height: 150px;
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


def clean_landing(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = dataframe.rename(
        columns={
            "landing_page": "landingpage",
            "sessies": "sessions",
            "bezoekers": "users",
            "transacties": "transactions",
            "omzet": "revenue",
            "conversie": "conversion_rate",
        }
    )

    dataframe = convert_columns_to_numeric(
        dataframe,
        ["sessions", "users", "transactions", "revenue", "conversion_rate", "bounce_rate"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")

    if "bounce_rate" not in dataframe.columns:
        dataframe["bounce_rate"] = 0

    if "sessions" not in dataframe.columns:
        dataframe["sessions"] = 0

    dataframe["bounce_impact_score"] = dataframe["bounce_rate"] * dataframe["sessions"]

    return dataframe


def clean_products(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = dataframe.rename(
        columns={
            "product": "itemname",
            "views": "itemsviewed",
            "aankopen": "itemspurchased",
            "omzet": "itemrevenue",
            "conversie": "conversion_rate",
        }
    )

    dataframe = convert_columns_to_numeric(
        dataframe,
        ["itemsviewed", "itemrevenue", "itemspurchased", "conversion_rate"],
    )

    if "date" in dataframe.columns:
        dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")

    if "itemsviewed" not in dataframe.columns:
        dataframe["itemsviewed"] = 0

    if "itemrevenue" not in dataframe.columns:
        dataframe["itemrevenue"] = 0

    dataframe["revenue_per_view"] = (
        dataframe["itemrevenue"] / dataframe["itemsviewed"].replace(0, pd.NA)
    ).fillna(0)

    dataframe["product_opportunity_score"] = (
        dataframe["itemsviewed"] / (dataframe["itemrevenue"] + 1)
    ).fillna(0)

    return dataframe


def clean_search(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = dataframe.rename(
        columns={
            "zoekterm": "searchterm",
            "zoekopdrachten": "searches",
            "gebruikers": "users",
            "resultaten": "results",
            "conversies": "conversions",
        }
    )

    dataframe = convert_columns_to_numeric(
        dataframe,
        ["searches", "users", "results", "conversions"],
    )

    for column in ["searches", "results", "conversions"]:
        if column not in dataframe.columns:
            dataframe[column] = 0

    dataframe["results_per_search"] = (
        dataframe["results"] / dataframe["searches"].replace(0, pd.NA)
    ).fillna(0)

    dataframe["search_conversion_rate"] = (
        dataframe["conversions"] / dataframe["searches"].replace(0, pd.NA) * 100
    ).fillna(0)

    return dataframe


def clean_pagespeed(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = dataframe.rename(columns={"pagina": "page"})
    dataframe = convert_columns_to_numeric(
        dataframe,
        ["mobile_speed", "desktop_speed"],
    )

    if "mobile_speed" in dataframe.columns:
        dataframe["speed_score"] = dataframe["mobile_speed"]
        dataframe["speed_risk"] = 100 - dataframe["mobile_speed"]
    else:
        dataframe["speed_score"] = 0
        dataframe["speed_risk"] = 0

    return dataframe


def clean_funnel(dataframe: pd.DataFrame) -> pd.DataFrame:
    dataframe = normalize_columns(dataframe)
    dataframe = dataframe.rename(
        columns={
            "stap": "step",
            "aantal": "count",
        }
    )

    dataframe = convert_columns_to_numeric(dataframe, ["count"])

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


def create_funnel_data(funnel: pd.DataFrame) -> pd.DataFrame:
    if {"step", "count"}.issubset(funnel.columns):
        funnel_data = funnel[["step", "count"]].copy()
        funnel_data = funnel_data.rename(
            columns={
                "step": "Stap",
                "count": "Aantal",
            }
        )
    else:
        funnel_columns = ["view_item", "add_to_cart", "begin_checkout", "purchase"]
        available_columns = [
            column for column in funnel_columns if column in funnel.columns
        ]

        if not available_columns:
            return pd.DataFrame()

        labels = {
            "view_item": "Product bekeken",
            "add_to_cart": "Toegevoegd aan winkelwagen",
            "begin_checkout": "Checkout gestart",
            "purchase": "Aankoop",
        }

        funnel_data = pd.DataFrame(
            {
                "Stap": [labels[column] for column in available_columns],
                "Aantal": [funnel[column].sum() for column in available_columns],
            }
        )

    funnel_data["Conversie vanaf vorige stap"] = (
        funnel_data["Aantal"] / funnel_data["Aantal"].shift(1) * 100
    ).fillna(100)

    funnel_data["Uitval vanaf vorige stap"] = (
        100 - funnel_data["Conversie vanaf vorige stap"]
    )

    return funnel_data


def render_header() -> None:
    st.markdown(
        """
        <div>
            <div class="vdk-main-title">Website optimizations</div>
            <div class="vdk-subtitle">
                Vind pagina's, producten, zoekopdrachten, performanceproblemen
                en funnelstappen met de grootste verbeterkans.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("Optimalisatiedata laden..."):
    landing = clean_landing(load_sheet(SHEET_URLS["landing"]))
    products = clean_products(load_sheet(SHEET_URLS["products"]))
    search = clean_search(load_sheet(SHEET_URLS["search"]))
    pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))
    funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Website optimizations")
st.sidebar.divider()

minimum_sessions = st.sidebar.slider(
    "Minimale sessies pagina's",
    min_value=0,
    max_value=1000,
    value=0,
    step=50,
)

minimum_product_views = st.sidebar.slider(
    "Minimale productviews",
    min_value=0,
    max_value=1000,
    value=0,
    step=50,
)

mobile_speed_threshold = st.sidebar.slider(
    "Mobiele speed score drempel",
    min_value=0,
    max_value=100,
    value=50,
    step=5,
)

show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)


average_conversion = (
    landing["conversion_rate"].mean()
    if "conversion_rate" in landing.columns
    else 0
)

average_mobile_speed = (
    pagespeed["mobile_speed"].mean()
    if "mobile_speed" in pagespeed.columns
    else 0
)

average_desktop_speed = (
    pagespeed["desktop_speed"].mean()
    if "desktop_speed" in pagespeed.columns
    else 0
)

total_searches = (
    search["searches"].sum()
    if "searches" in search.columns
    else 0
)

slow_pages_count = (
    len(pagespeed[pagespeed["mobile_speed"] < mobile_speed_threshold])
    if "mobile_speed" in pagespeed.columns
    else 0
)

product_opportunities = (
    len(products[products["itemsviewed"] >= minimum_product_views])
    if "itemsviewed" in products.columns
    else len(products)
)


render_header()

metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    st.metric("Gem. conversie", format_percent(average_conversion))

with metric_col2:
    st.metric("Mobiele speed", f"{average_mobile_speed:.0f}/100")

with metric_col3:
    st.metric("Desktop speed", f"{average_desktop_speed:.0f}/100")

with metric_col4:
    st.metric("Zoekopdrachten", format_number(total_searches))

with metric_col5:
    st.metric("Productkansen", format_number(product_opportunities))


add_space()

tab_overview, tab_pages, tab_products, tab_search, tab_speed, tab_funnel, tab_tasks, tab_data = st.tabs(
    [
        "Overzicht",
        "Pagina's",
        "Producten",
        "Zoekfunctie",
        "Snelheid",
        "Funnel",
        "Taken",
        "Data",
    ]
)


with tab_overview:
    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Pagina's</h4>
                <p>
                    Gemiddelde conversie is <strong>{format_percent(average_conversion)}</strong>.
                    Analyseer pagina's met veel sessies maar weinig transacties.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Performance</h4>
                <p>
                    Gemiddelde mobiele speed score is
                    <strong>{average_mobile_speed:.0f}/100</strong>.
                    Er zijn <strong>{format_number(slow_pages_count)}</strong>
                    pagina's onder de ingestelde drempel.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Zoekfunctie</h4>
                <p>
                    Er zijn <strong>{format_number(total_searches)}</strong>
                    zoekopdrachten. Populaire zoektermen zijn directe
                    UX- en assortimentssignalen.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    add_space()

    overview_col1, overview_col2 = st.columns(2)

    with overview_col1:
        if {"landingpage", "sessions", "conversion_rate"}.issubset(landing.columns):
            page_data = landing[landing["sessions"] >= minimum_sessions].copy()

            page_data = page_data.sort_values(
                ["sessions", "conversion_rate"],
                ascending=[False, True],
            ).head(10)

            page_fig = px.bar(
                page_data,
                x="sessions",
                y="landingpage",
                orientation="h",
                title="Pagina's met veel sessies",
                color="conversion_rate",
                color_continuous_scale="Greens",
            )

            page_fig.update_layout(yaxis={"categoryorder": "total ascending"})

            st.plotly_chart(
                apply_plotly_layout(page_fig, height=520),
                use_container_width=True,
            )

    with overview_col2:
        funnel_data = create_funnel_data(funnel)

        if not funnel_data.empty:
            funnel_fig = px.funnel(
                funnel_data,
                x="Aantal",
                y="Stap",
                title="Checkout funnel",
                color_discrete_sequence=[BRAND_GREEN],
            )

            st.plotly_chart(
                apply_plotly_layout(funnel_fig, height=520),
                use_container_width=True,
            )


with tab_pages:
    st.subheader("Pagina's met optimalisatiekansen")

    if landing.empty:
        st.warning("Geen landingpage-data gevonden.")
    elif not {"landingpage", "sessions"}.issubset(landing.columns):
        st.warning("Landingpage-data mist `landingpage` of `sessions`.")
    else:
        page_data = landing[landing["sessions"] >= minimum_sessions].copy()

        page_data = page_data.sort_values(
            ["sessions", "conversion_rate"],
            ascending=[False, True],
        )

        page_fig = px.bar(
            page_data.head(15),
            x="sessions",
            y="landingpage",
            orientation="h",
            text="sessions",
            title="Pagina's met meeste sessies en conversiekans",
            color="conversion_rate" if "conversion_rate" in page_data.columns else None,
            color_continuous_scale="Greens",
        )

        page_fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
        )

        page_fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            apply_plotly_layout(page_fig, height=620),
            use_container_width=True,
        )

        page_columns = [
            column
            for column in [
                "date",
                "landingpage",
                "sessions",
                "users",
                "transactions",
                "revenue",
                "conversion_rate",
            ]
            if column in page_data.columns
        ]

        st.dataframe(
            page_data[page_columns],
            use_container_width=True,
            hide_index=True,
        )


with tab_products:
    st.subheader("Producten met hoge views maar lage omzet")

    if products.empty:
        st.warning("Geen productdata gevonden.")
    elif not {"itemname", "itemsviewed", "itemrevenue"}.issubset(products.columns):
        st.warning("Productdata mist `product`, `views` of `omzet`.")
    else:
        product_data = products[
            products["itemsviewed"] >= minimum_product_views
        ].copy()

        product_data = product_data.sort_values(
            "product_opportunity_score",
            ascending=False,
        )

        scatter_fig = px.scatter(
            product_data,
            x="itemsviewed",
            y="itemrevenue",
            size="itemsviewed",
            color="conversion_rate" if "conversion_rate" in product_data.columns else None,
            hover_name="itemname",
            title="Productviews versus omzet",
            color_continuous_scale="Greens",
        )

        scatter_fig.update_yaxes(tickprefix="€ ")

        st.plotly_chart(
            apply_plotly_layout(scatter_fig, height=560),
            use_container_width=True,
        )

        product_columns = [
            column
            for column in [
                "date",
                "itemname",
                "itemsviewed",
                "itemspurchased",
                "itemrevenue",
                "conversion_rate",
                "revenue_per_view",
                "product_opportunity_score",
            ]
            if column in product_data.columns
        ]

        st.dataframe(
            product_data[product_columns],
            use_container_width=True,
            hide_index=True,
        )


with tab_search:
    st.subheader("Populaire zoektermen")

    if search.empty:
        st.warning("Geen site-search data gevonden.")
    elif not {"searchterm", "searches"}.issubset(search.columns):
        st.warning("Search-data mist `zoekterm` of `zoekopdrachten`.")
    else:
        search_data = search.copy()
        search_data = search_data[
            search_data["searchterm"].astype(str).str.len() > 0
        ]
        search_data = search_data.sort_values("searches", ascending=False)

        search_fig = px.bar(
            search_data.head(15),
            x="searches",
            y="searchterm",
            orientation="h",
            text="searches",
            title="Meest gebruikte zoektermen",
            color_discrete_sequence=[BRAND_GREEN],
        )

        search_fig.update_traces(
            texttemplate="%{text:,.0f}",
            textposition="outside",
        )

        search_fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            apply_plotly_layout(search_fig, height=560),
            use_container_width=True,
        )

        search_columns = [
            column
            for column in [
                "searchterm",
                "searches",
                "users",
                "results",
                "conversions",
            ]
            if column in search_data.columns
        ]

        st.dataframe(
            search_data[search_columns],
            use_container_width=True,
            hide_index=True,
        )


with tab_speed:
    st.subheader("Page speed")

    if pagespeed.empty:
        st.warning("Geen page-speed data gevonden.")
    elif not {"page", "mobile_speed", "desktop_speed"}.issubset(pagespeed.columns):
        st.warning("Page-speed data mist `pagina`, `mobile_speed` of `desktop_speed`.")
    else:
        speed_data = pagespeed.sort_values("mobile_speed", ascending=True).copy()

        speed_long = speed_data.melt(
            id_vars="page",
            value_vars=["mobile_speed", "desktop_speed"],
            var_name="Device",
            value_name="Score",
        )

        speed_fig = px.bar(
            speed_long,
            x="Score",
            y="page",
            color="Device",
            orientation="h",
            barmode="group",
            title="Mobiele en desktop speed score",
            color_discrete_sequence=[SOFT_RED, BRAND_GREEN],
        )

        speed_fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            apply_plotly_layout(speed_fig, height=620),
            use_container_width=True,
        )

        st.dataframe(
            speed_data[["page", "mobile_speed", "desktop_speed", "speed_risk"]],
            use_container_width=True,
            hide_index=True,
        )


with tab_funnel:
    st.subheader("Checkout funnel")

    funnel_data = create_funnel_data(funnel)

    if funnel_data.empty:
        st.warning("Geen bruikbare funneldata gevonden.")
    else:
        funnel_fig = px.funnel(
            funnel_data,
            x="Aantal",
            y="Stap",
            title="Van sessie naar aankoop",
            color_discrete_sequence=[BRAND_GREEN],
        )

        st.plotly_chart(
            apply_plotly_layout(funnel_fig, height=540),
            use_container_width=True,
        )

        st.dataframe(
            funnel_data.assign(
                Aantal=funnel_data["Aantal"].map(format_number),
                **{
                    "Conversie vanaf vorige stap": funnel_data[
                        "Conversie vanaf vorige stap"
                    ].map(format_percent),
                    "Uitval vanaf vorige stap": funnel_data[
                        "Uitval vanaf vorige stap"
                    ].map(format_percent),
                },
            ),
            use_container_width=True,
            hide_index=True,
        )


with tab_tasks:
    st.subheader("Automatische optimalisatietaken")

    tasks = []

    if average_mobile_speed < mobile_speed_threshold:
        tasks.append(
            {
                "Prioriteit": "Hoog",
                "Categorie": "Page Speed",
                "Probleem": "Mobiele speed score is laag.",
                "Aanbevolen actie": "Comprimeer afbeeldingen, beperk scripts en verbeter caching.",
                "Impact": "SEO, UX en conversie",
            }
        )

    if product_opportunities > 0:
        tasks.append(
            {
                "Prioriteit": "Middel",
                "Categorie": "Productpagina's",
                "Probleem": "Producten krijgen views maar leveren relatief weinig omzet op.",
                "Aanbevolen actie": "Controleer productfoto's, prijs, voorraad, reviews en koopknoppen.",
                "Impact": "Meer add-to-carts en omzet",
            }
        )

    if total_searches > 0:
        tasks.append(
            {
                "Prioriteit": "Middel",
                "Categorie": "Zoekfunctie",
                "Probleem": "Zoekgedrag laat concrete klantvraag zien.",
                "Aanbevolen actie": "Gebruik populaire zoektermen voor categorieën, synoniemen en content.",
                "Impact": "Betere vindbaarheid en UX",
            }
        )

    funnel_data = create_funnel_data(funnel)

    if not funnel_data.empty and "Uitval vanaf vorige stap" in funnel_data.columns:
        highest_drop = funnel_data.sort_values(
            "Uitval vanaf vorige stap",
            ascending=False,
        ).iloc[0]

        tasks.append(
            {
                "Prioriteit": "Hoog",
                "Categorie": "Checkout funnel",
                "Probleem": f"Grootste uitval bij: {highest_drop['Stap']}.",
                "Aanbevolen actie": "Analyseer mobiele flow, verzendkosten, betaalopties en foutmeldingen.",
                "Impact": "Conversie verhogen",
            }
        )

    if tasks:
        st.dataframe(
            pd.DataFrame(tasks),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Geen automatische taken gevonden op basis van de huidige instellingen.")


with tab_data:
    st.subheader("Datakwaliteit")

    data_col1, data_col2, data_col3, data_col4, data_col5 = st.columns(5)

    with data_col1:
        st.metric("Landingpages", len(landing))

    with data_col2:
        st.metric("Producten", len(products))

    with data_col3:
        st.metric("Zoektermen", len(search))

    with data_col4:
        st.metric("Speed pages", len(pagespeed))

    with data_col5:
        st.metric("Funnel-rijen", len(funnel))

    if show_raw_data:
        add_space()

        st.subheader("Landingpages")
        st.dataframe(landing, use_container_width=True, hide_index=True)

        st.subheader("Products")
        st.dataframe(products, use_container_width=True, hide_index=True)

        st.subheader("Search")
        st.dataframe(search, use_container_width=True, hide_index=True)

        st.subheader("Page speed")
        st.dataframe(pagespeed, use_container_width=True, hide_index=True)

        st.subheader("Funnel")
        st.dataframe(funnel, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")


st.caption("Van Duinkerken Website Optimization Dashboard · Streamlit · Plotly · Google Sheets")