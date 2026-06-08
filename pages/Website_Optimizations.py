from __future__ import annotations

import pandas as pd
import plotly.express as px
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
    "funnel": f"{BASE_URL}/checkout_funnel",
}

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_RED = "#c76f6f"

st.markdown(
    f"""
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

#MainMenu, footer, header {{
    visibility: hidden;
}}

section[data-testid="stSidebar"] {{
    background: #ffffff;
    border-right: 1px solid rgba(8, 68, 34, 0.06);
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

.space {{
    height: 34px;
}}
</style>
""",
    unsafe_allow_html=True,
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def parse_numeric(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def ensure_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    for column in columns:
        if column in df.columns:
            df[column] = parse_numeric(df[column])

    return df


def add_missing_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = df.copy()

    for column in columns:
        if column not in df.columns:
            df[column] = 0

    return df


def parse_date_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "datum" in df.columns and "date" not in df.columns:
        df = df.rename(columns={"datum": "date"})

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

    return df


def safe_divide(numerator, denominator, multiplier=1):
    return numerator.div(denominator.replace(0, pd.NA)).fillna(0) * multiplier


def format_euro(value: float) -> str:
    return f"€ {value:,.0f}".replace(",", ".") if not pd.isna(value) else "€ 0"


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".") if not pd.isna(value) else "0"


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",") if not pd.isna(value) else "0,0%"


def apply_plotly_layout(fig, height: int = 430):
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


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()

    if not data:
        return pd.DataFrame()

    if isinstance(data, dict):
        data = [data]

    return normalize_columns(pd.DataFrame(data))


def clean_landing(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(
        columns={
            "landing_page": "landingpage",
            "sessies": "sessions",
            "bezoekers": "users",
            "transacties": "transactions",
            "omzet": "revenue",
            "conversie": "conversion_rate",
        }
    )

    numeric_columns = [
        "sessions",
        "users",
        "transactions",
        "revenue",
        "conversion_rate",
        "bounce_rate",
    ]

    df = ensure_numeric(df, numeric_columns)
    df = add_missing_numeric_columns(df, numeric_columns)
    df = parse_date_column(df)

    if "landingpage" not in df.columns:
        df["landingpage"] = "Onbekend"

    df["landingpage"] = df["landingpage"].fillna("Onbekend").astype(str).str.strip()
    df["landingpage"] = df["landingpage"].replace("", "Onbekend")

    df["bounce_impact_score"] = df["bounce_rate"] * df["sessions"]

    return df


def clean_products(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(
        columns={
            "product": "itemname",
            "views": "itemsviewed",
            "aankopen": "itemspurchased",
            "omzet": "itemrevenue",
            "conversie": "conversion_rate",
        }
    )

    numeric_columns = [
        "itemsviewed",
        "itemrevenue",
        "itemspurchased",
        "conversion_rate",
    ]

    df = ensure_numeric(df, numeric_columns)
    df = add_missing_numeric_columns(df, numeric_columns)
    df = parse_date_column(df)

    if "itemname" not in df.columns:
        df["itemname"] = "Onbekend"

    df["itemname"] = df["itemname"].fillna("Onbekend").astype(str).str.strip()
    df["itemname"] = df["itemname"].replace("", "Onbekend")

    df["revenue_per_view"] = safe_divide(df["itemrevenue"], df["itemsviewed"])

    df["product_opportunity_score"] = (
        df["itemsviewed"] / (df["itemrevenue"] + 1)
    ).fillna(0)

    return df


def clean_search(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(
        columns={
            "zoekterm": "searchterm",
            "zoekopdrachten": "searches",
            "gebruikers": "users",
            "resultaten": "results",
            "conversies": "conversions",
        }
    )

    numeric_columns = ["searches", "users", "results", "conversions"]

    df = ensure_numeric(df, numeric_columns)
    df = add_missing_numeric_columns(df, numeric_columns)
    df = parse_date_column(df)

    if "searchterm" not in df.columns:
        df["searchterm"] = "Onbekend"

    df["searchterm"] = df["searchterm"].fillna("Onbekend").astype(str).str.strip()
    df["searchterm"] = df["searchterm"].replace("", "Onbekend")

    df["results_per_search"] = safe_divide(df["results"], df["searches"])

    df["search_conversion_rate"] = safe_divide(
        df["conversions"],
        df["searches"],
        100,
    )

    return df


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(columns={"pagina": "page"})

    numeric_columns = ["mobile_speed", "desktop_speed"]

    df = ensure_numeric(df, numeric_columns)
    df = add_missing_numeric_columns(df, numeric_columns)
    df = parse_date_column(df)

    if "page" not in df.columns:
        df["page"] = "Onbekend"

    df["page"] = df["page"].fillna("Onbekend").astype(str).str.strip()
    df["page"] = df["page"].replace("", "Onbekend")

    df["speed_score"] = df["mobile_speed"]
    df["speed_risk"] = 100 - df["mobile_speed"]

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(

    columns={
        "stap": "step",
        "aantal": "count",
        "datum": "date",
    }

)

    possible_numeric_columns = [
        "count",
        "view_item",
        "add_to_cart",
        "begin_checkout",
        "purchase",
    ]

    available_numeric_columns = [
        column for column in possible_numeric_columns if column in df.columns
    ]

    df = ensure_numeric(df, available_numeric_columns)
    df = parse_date_column(df)

    if "step" in df.columns:
        df["step"] = df["step"].fillna("Onbekend").astype(str).str.strip()
        df["step"] = df["step"].replace("", "Onbekend")

    return df


def load_all_data() -> dict[str, pd.DataFrame]:
    return {
        "landing": clean_landing(load_sheet(SHEET_URLS["landing"])),
        "products": clean_products(load_sheet(SHEET_URLS["products"])),
        "search": clean_search(load_sheet(SHEET_URLS["search"])),
        "pagespeed": clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"])),
        "funnel": clean_funnel(load_sheet(SHEET_URLS["funnel"])),
    }


def get_selected_period(dataframes: list[pd.DataFrame]) -> tuple:
    date_series = []

    for df in dataframes:
        if not df.empty and "date" in df.columns:
            dates = pd.to_datetime(df["date"], errors="coerce").dropna()

            if not dates.empty:
                date_series.append(dates)

    if not date_series:
        st.sidebar.info("Geen geldige datumkolommen gevonden.")
        return None, None, "alle beschikbare data"

    all_dates = pd.concat(date_series, ignore_index=True)

    min_date = all_dates.min().date()
    max_date = all_dates.max().date()

    period_label = st.sidebar.radio(
        "Periode",
        [
            "Afgelopen 7 dagen",
            "Afgelopen 30 dagen",
            "Afgelopen 90 dagen",
            "Alles",
            "Aangepast",
        ],
        index=1,
    )

    if period_label == "Afgelopen 7 dagen":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=6)).date()
        end_date = max_date
    elif period_label == "Afgelopen 30 dagen":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=29)).date()
        end_date = max_date
    elif period_label == "Afgelopen 90 dagen":
        start_date = (pd.Timestamp(max_date) - pd.Timedelta(days=89)).date()
        end_date = max_date
    elif period_label == "Alles":
        start_date = min_date
        end_date = max_date
    else:
        selected_period = st.sidebar.date_input(
            "Aangepaste periode",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(selected_period, tuple) and len(selected_period) == 2:
            start_date, end_date = selected_period
        else:
            start_date, end_date = min_date, max_date

    return start_date, end_date, f"{start_date} t/m {end_date}"


def filter_by_period(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    if df.empty or "date" not in df.columns or start_date is None or end_date is None:
        return df

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

    if df["date"].notna().sum() == 0:
        return df

    return df[
        df["date"].between(
            pd.Timestamp(start_date),
            pd.Timestamp(end_date),
        )
    ]


def render_sidebar(data: dict[str, pd.DataFrame]) -> dict:
    st.sidebar.markdown("## Van Duinkerken")
    st.sidebar.markdown("Website optimizations")
    st.sidebar.divider()

    start_date, end_date, period_text = get_selected_period(list(data.values()))

    filtered_data = {
        key: filter_by_period(df, start_date, end_date)
        for key, df in data.items()
    }

    settings = {
        "period_text": period_text,
        "minimum_sessions": st.sidebar.slider(
            "Minimale sessies pagina's",
            min_value=0,
            max_value=1000,
            value=0,
            step=50,
        ),
        "minimum_product_views": st.sidebar.slider(
            "Minimale productviews",
            min_value=0,
            max_value=1000,
            value=0,
            step=50,
        ),
        "mobile_speed_threshold": st.sidebar.slider(
            "Mobiele speed score drempel",
            min_value=0,
            max_value=100,
            value=50,
            step=5,
        ),
        "show_raw_data": st.sidebar.toggle(
            "Toon ruwe tabellen",
            value=False,
        ),
    }

    return {"data": filtered_data, "settings": settings}


def create_funnel_data(funnel: pd.DataFrame) -> pd.DataFrame:
    if funnel.empty:
        return pd.DataFrame()

    if {"step", "count"}.issubset(funnel.columns):
        funnel_data = (
            funnel.groupby("step", as_index=False)["count"]
            .sum()
            .rename(columns={"step": "Stap", "count": "Aantal"})
        )
    else:
        funnel_columns = ["view_item", "add_to_cart", "begin_checkout", "purchase"]
        available_columns = [column for column in funnel_columns if column in funnel.columns]

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

    funnel_data = funnel_data[funnel_data["Aantal"] > 0].copy()

    if funnel_data.empty:
        return funnel_data

    funnel_data["Conversie vanaf vorige stap"] = (
        funnel_data["Aantal"].div(funnel_data["Aantal"].shift(1)).fillna(1) * 100
    )

    funnel_data["Uitval vanaf vorige stap"] = (
        100 - funnel_data["Conversie vanaf vorige stap"]
    )

    return funnel_data


def calculate_metrics(
    landing: pd.DataFrame,
    products: pd.DataFrame,
    search: pd.DataFrame,
    pagespeed: pd.DataFrame,
    settings: dict,
) -> dict:
    average_conversion = (
        landing["conversion_rate"].mean()
        if not landing.empty and "conversion_rate" in landing.columns
        else 0
    )

    average_mobile_speed = (
        pagespeed["mobile_speed"].mean()
        if not pagespeed.empty and "mobile_speed" in pagespeed.columns
        else 0
    )

    average_desktop_speed = (
        pagespeed["desktop_speed"].mean()
        if not pagespeed.empty and "desktop_speed" in pagespeed.columns
        else 0
    )

    total_searches = (
        search["searches"].sum()
        if not search.empty and "searches" in search.columns
        else 0
    )

    slow_pages_count = (
        len(pagespeed[pagespeed["mobile_speed"] < settings["mobile_speed_threshold"]])
        if not pagespeed.empty and "mobile_speed" in pagespeed.columns
        else 0
    )

    product_opportunities = (
        len(products[products["itemsviewed"] >= settings["minimum_product_views"]])
        if not products.empty and "itemsviewed" in products.columns
        else 0
    )

    return {
        "average_conversion": average_conversion,
        "average_mobile_speed": average_mobile_speed,
        "average_desktop_speed": average_desktop_speed,
        "total_searches": total_searches,
        "slow_pages_count": slow_pages_count,
        "product_opportunities": product_opportunities,
    }


def render_header(period_text: str) -> None:
    st.markdown(
        f"""
        <div>
            <div class="vdk-main-title">Website optimizations</div>
            <div class="vdk-subtitle">
                Vind pagina's, producten, zoekopdrachten, performanceproblemen
                en funnelstappen met de grootste verbeterkans.
                Periode: <strong>{period_text}</strong>.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def render_metrics(metrics: dict) -> None:
    cols = st.columns(5)

    kpis = [
        ("Gem. conversie", format_percent(metrics["average_conversion"])),
        ("Mobiele speed", f"{metrics['average_mobile_speed']:.0f}/100"),
        ("Desktop speed", f"{metrics['average_desktop_speed']:.0f}/100"),
        ("Zoekopdrachten", format_number(metrics["total_searches"])),
        ("Productkansen", format_number(metrics["product_opportunities"])),
    ]

    for col, (label, value) in zip(cols, kpis):
        col.metric(label, value)


def insight_card(title: str, text: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <h4>{title}</h4>
            <p>{text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_page_sessions_chart(
    landing: pd.DataFrame,
    settings: dict,
    height: int = 620,
) -> None:
    required = {"landingpage", "sessions", "conversion_rate"}

    if landing.empty or not required.issubset(landing.columns):
        st.info("Geen bruikbare landingpage-data beschikbaar.")
        return

    page_data = landing[landing["sessions"] >= settings["minimum_sessions"]].copy()

    if page_data.empty:
        st.info("Geen pagina's boven het ingestelde minimum aantal sessies.")
        return

    page_data = page_data.sort_values(
        ["sessions", "conversion_rate"],
        ascending=[False, True],
    ).head(15)

    fig = px.bar(
        page_data,
        x="sessions",
        y="landingpage",
        orientation="h",
        text="sessions",
        title="Pagina's met meeste sessies en conversiekans",
        color="conversion_rate",
        color_continuous_scale=["#dfe7df", "#7d9b88", BRAND_GREEN],
    )

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(apply_plotly_layout(fig, height=height), use_container_width=True)


def render_funnel_chart(funnel: pd.DataFrame, height: int = 540) -> None:
    funnel_data = create_funnel_data(funnel)

    if funnel_data.empty:
        st.info("Geen bruikbare funneldata gevonden.")
        return

    fig = px.funnel(
        funnel_data,
        x="Aantal",
        y="Stap",
        title="Checkout funnel",
        color_discrete_sequence=[BRAND_GREEN],
    )

    st.plotly_chart(apply_plotly_layout(fig, height=height), use_container_width=True)


def render_overview_tab(
    landing: pd.DataFrame,
    funnel: pd.DataFrame,
    metrics: dict,
    settings: dict,
) -> None:
    col1, col2, col3 = st.columns(3)

    with col1:
        insight_card(
            "Pagina's",
            f"Gemiddelde conversie is <strong>{format_percent(metrics['average_conversion'])}</strong>. "
            "Analyseer pagina's met veel sessies maar weinig transacties.",
        )

    with col2:
        insight_card(
            "Performance",
            f"Gemiddelde mobiele speed score is <strong>{metrics['average_mobile_speed']:.0f}/100</strong>. "
            f"Er zijn <strong>{format_number(metrics['slow_pages_count'])}</strong> pagina's onder de drempel.",
        )

    with col3:
        insight_card(
            "Zoekfunctie",
            f"Er zijn <strong>{format_number(metrics['total_searches'])}</strong> zoekopdrachten. "
            "Populaire zoektermen zijn directe UX- en assortimentssignalen.",
        )

    add_space()

    col1, col2 = st.columns(2)

    with col1:
        render_page_sessions_chart(landing, settings, height=520)

    with col2:
        render_funnel_chart(funnel, height=520)


def render_pages_tab(landing: pd.DataFrame, settings: dict) -> None:
    st.subheader("Pagina's met optimalisatiekansen")

    render_page_sessions_chart(landing, settings)

    if landing.empty:
        return

    page_data = landing[landing["sessions"] >= settings["minimum_sessions"]].copy()

    page_data = page_data.sort_values(
        ["sessions", "conversion_rate"],
        ascending=[False, True],
    )

    columns = [
        "date",
        "landingpage",
        "sessions",
        "users",
        "transactions",
        "revenue",
        "conversion_rate",
        "bounce_rate",
        "bounce_impact_score",
    ]

    st.dataframe(
        page_data[[column for column in columns if column in page_data.columns]],
        use_container_width=True,
        hide_index=True,
    )


def render_products_tab(products: pd.DataFrame, settings: dict) -> None:
    st.subheader("Producten met hoge views maar lage omzet")

    required = {"itemname", "itemsviewed", "itemrevenue"}

    if products.empty or not required.issubset(products.columns):
        st.warning("Geen bruikbare productdata gevonden.")
        return

    product_data = products[
        products["itemsviewed"] >= settings["minimum_product_views"]
    ].copy()

    if product_data.empty:
        st.info("Geen producten boven het ingestelde minimum aantal views.")
        return

    product_data = product_data.sort_values(
        "product_opportunity_score",
        ascending=False,
    )

    fig = px.scatter(
        product_data,
        x="itemsviewed",
        y="itemrevenue",
        size="itemsviewed",
        color="conversion_rate" if "conversion_rate" in product_data.columns else None,
        hover_name="itemname",
        title="Productviews versus omzet",
        color_continuous_scale=["#dfe7df", "#7d9b88", BRAND_GREEN],
    )

    fig.update_yaxes(tickprefix="€ ")

    st.plotly_chart(apply_plotly_layout(fig, height=560), use_container_width=True)

    columns = [
        "date",
        "itemname",
        "itemsviewed",
        "itemspurchased",
        "itemrevenue",
        "conversion_rate",
        "revenue_per_view",
        "product_opportunity_score",
    ]

    st.dataframe(
        product_data[[column for column in columns if column in product_data.columns]],
        use_container_width=True,
        hide_index=True,
    )


def render_search_tab(search: pd.DataFrame) -> None:
    st.subheader("Populaire zoektermen")

    if search.empty or not {"searchterm", "searches"}.issubset(search.columns):
        st.warning("Geen bruikbare site-search data gevonden.")
        return

    search_data = search.copy()
    search_data = search_data[search_data["searchterm"].astype(str).str.len() > 0]
    search_data = search_data.sort_values("searches", ascending=False)

    if search_data.empty:
        st.info("Geen zoektermen beschikbaar.")
        return

    fig = px.bar(
        search_data.head(15),
        x="searches",
        y="searchterm",
        orientation="h",
        text="searches",
        title="Meest gebruikte zoektermen",
        color_discrete_sequence=[BRAND_GREEN],
    )

    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(apply_plotly_layout(fig, height=560), use_container_width=True)

    columns = [
        "date",
        "searchterm",
        "searches",
        "users",
        "results",
        "conversions",
        "results_per_search",
        "search_conversion_rate",
    ]

    st.dataframe(
        search_data[[column for column in columns if column in search_data.columns]],
        use_container_width=True,
        hide_index=True,
    )


def render_speed_tab(pagespeed: pd.DataFrame) -> None:
    st.subheader("Page speed")

    required = {"page", "mobile_speed", "desktop_speed"}

    if pagespeed.empty or not required.issubset(pagespeed.columns):
        st.warning("Geen bruikbare page-speed data gevonden.")
        return

    speed_data = pagespeed.sort_values("mobile_speed", ascending=True).copy()

    speed_long = speed_data.melt(
        id_vars="page",
        value_vars=["mobile_speed", "desktop_speed"],
        var_name="Device",
        value_name="Score",
    )

    fig = px.bar(
        speed_long,
        x="Score",
        y="page",
        color="Device",
        orientation="h",
        barmode="group",
        title="Mobiele en desktop speed score",
        color_discrete_sequence=[SOFT_RED, BRAND_GREEN],
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})

    st.plotly_chart(apply_plotly_layout(fig, height=620), use_container_width=True)

    columns = ["date", "page", "mobile_speed", "desktop_speed", "speed_risk"]

    st.dataframe(
        speed_data[[column for column in columns if column in speed_data.columns]],
        use_container_width=True,
        hide_index=True,
    )


def render_funnel_tab(funnel: pd.DataFrame) -> None:
    st.subheader("Checkout funnel")

    funnel_data = create_funnel_data(funnel)

    if funnel_data.empty:
        st.warning("Geen bruikbare funneldata gevonden.")
        return

    render_funnel_chart(funnel)

    display_df = funnel_data.copy()
    display_df["Aantal"] = display_df["Aantal"].map(format_number)
    display_df["Conversie vanaf vorige stap"] = display_df[
        "Conversie vanaf vorige stap"
    ].map(format_percent)
    display_df["Uitval vanaf vorige stap"] = display_df[
        "Uitval vanaf vorige stap"
    ].map(format_percent)

    st.dataframe(display_df, use_container_width=True, hide_index=True)


def render_tasks_tab(
    search: pd.DataFrame,
    funnel: pd.DataFrame,
    metrics: dict,
    settings: dict,
) -> None:
    st.subheader("Automatische optimalisatietaken")

    tasks = []

    if metrics["average_mobile_speed"] < settings["mobile_speed_threshold"]:
        tasks.append(
            {
                "Prioriteit": "Hoog",
                "Categorie": "Page Speed",
                "Probleem": "Mobiele speed score is laag.",
                "Aanbevolen actie": "Comprimeer afbeeldingen, beperk scripts en verbeter caching.",
                "Impact": "SEO, UX en conversie",
            }
        )

    if metrics["product_opportunities"] > 0:
        tasks.append(
            {
                "Prioriteit": "Middel",
                "Categorie": "Productpagina's",
                "Probleem": "Producten krijgen views maar leveren relatief weinig omzet op.",
                "Aanbevolen actie": "Controleer productfoto's, prijs, voorraad, reviews en koopknoppen.",
                "Impact": "Meer add-to-carts en omzet",
            }
        )

    if not search.empty and metrics["total_searches"] > 0:
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

    if not funnel_data.empty:
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
        st.dataframe(pd.DataFrame(tasks), use_container_width=True, hide_index=True)
    else:
        st.info("Geen automatische taken gevonden op basis van de huidige instellingen.")


def render_data_tab(data: dict[str, pd.DataFrame], show_raw_data: bool) -> None:
    st.subheader("Datakwaliteit")

    cols = st.columns(5)

    labels = [
        ("Landingpages", "landing"),
        ("Producten", "products"),
        ("Zoektermen", "search"),
        ("Speed pages", "pagespeed"),
        ("Funnel-rijen", "funnel"),
    ]

    for col, (label, key) in zip(cols, labels):
        col.metric(label, len(data[key]))

    if not show_raw_data:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")
        return

    add_space()

    for label, key in labels:
        st.subheader(label)
        st.dataframe(data[key], use_container_width=True, hide_index=True)


def main() -> None:
    with st.spinner("Optimalisatiedata laden..."):
        try:
            raw_data = load_all_data()
        except Exception as error:
            st.error(f"Data kon niet worden geladen: {error}")
            return

    sidebar_result = render_sidebar(raw_data)
    data = sidebar_result["data"]
    settings = sidebar_result["settings"]

    landing = data["landing"]
    products = data["products"]
    search = data["search"]
    pagespeed = data["pagespeed"]
    funnel = data["funnel"]

    metrics = calculate_metrics(
        landing,
        products,
        search,
        pagespeed,
        settings,
    )

    render_header(settings["period_text"])
    render_metrics(metrics)

    add_space()

    tabs = st.tabs(
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

    with tabs[0]:
        render_overview_tab(landing, funnel, metrics, settings)

    with tabs[1]:
        render_pages_tab(landing, settings)

    with tabs[2]:
        render_products_tab(products, settings)

    with tabs[3]:
        render_search_tab(search)

    with tabs[4]:
        render_speed_tab(pagespeed)

    with tabs[5]:
        render_funnel_tab(funnel)

    with tabs[6]:
        render_tasks_tab(search, funnel, metrics, settings)

    with tabs[7]:
        render_data_tab(data, settings["show_raw_data"])

    st.caption(
        "Van Duinkerken Website Optimization Dashboard · Streamlit · Plotly · Google Sheets"
    )


if __name__ == "__main__":
    main()
