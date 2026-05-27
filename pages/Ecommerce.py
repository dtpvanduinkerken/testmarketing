import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK E-commerce Dashboard",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "products": f"{BASE_URL}/products",
    "categories": f"{BASE_URL}/categories",
    "funnel": f"{BASE_URL}/funnel",
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

    if "date" not in dataframe.columns:
        return pd.DataFrame()

    numeric_columns = [
        "omzet",
        "orders",
        "bezoekers",
        "sessies",
        "conversie",
        "gemiddelde_orderwaarde",
        "add_to_carts",
        "checkout_start",
        "aankopen",
    ]

    dataframe["date"] = pd.to_datetime(dataframe["date"], errors="coerce")
    dataframe = dataframe.dropna(subset=["date"])
    dataframe = convert_columns_to_numeric(dataframe, numeric_columns)
    dataframe = dataframe.sort_values("date")

    return dataframe


def clean_products(dataframe: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = [
        "itemrevenue",
        "itemsviewed",
        "itemsaddedtocart",
        "itemspurchased",
    ]

    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(dataframe, numeric_columns)

    if {"itemsaddedtocart", "itemsviewed"}.issubset(dataframe.columns):
        dataframe["cart_rate"] = (
            dataframe["itemsaddedtocart"]
            / dataframe["itemsviewed"].replace(0, pd.NA)
            * 100
        ).fillna(0)

    if {"itemrevenue", "itemsviewed"}.issubset(dataframe.columns):
        dataframe["revenue_per_view"] = (
            dataframe["itemrevenue"]
            / dataframe["itemsviewed"].replace(0, pd.NA)
        ).fillna(0)

    return dataframe


def clean_categories(dataframe: pd.DataFrame) -> pd.DataFrame:
    numeric_columns = ["itemrevenue", "itemsviewed", "itemsaddedtocart"]
    dataframe = normalize_columns(dataframe)
    dataframe = convert_columns_to_numeric(dataframe, numeric_columns)
    return dataframe


def filter_period(
    dataframe: pd.DataFrame,
    period_label: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
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


def render_header(start_date, end_date) -> None:
    st.markdown(
        f"""
        <div>
            <div class="vdk-main-title">E-commerce performance</div>
            <div class="vdk-subtitle">
                Inzicht in omzet, orders, productprestaties, categorieën
                en checkout-uitval. Periode:
                <strong>{start_date}</strong> t/m <strong>{end_date}</strong>.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


with st.spinner("E-commerce data laden..."):
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
    products = clean_products(load_sheet(SHEET_URLS["products"]))
    categories = clean_categories(load_sheet(SHEET_URLS["categories"]))
    funnel = load_sheet(SHEET_URLS["funnel"])


if overview.empty:
    st.error("Geen geldige overview-data gevonden. Controleer de sheet en kolom `date`.")
    st.stop()


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("E-commerce")
st.sidebar.divider()

period = st.sidebar.radio(
    "Periode",
    ["Laatste 7 dagen", "Laatste 30 dagen", "Laatste 90 dagen", "Alles"],
    index=1,
)

product_sort = st.sidebar.selectbox(
    "Rangschik producten op",
    ["itemrevenue", "itemsviewed", "itemsaddedtocart", "cart_rate"],
)

top_n = st.sidebar.slider(
    "Aantal producten",
    min_value=5,
    max_value=25,
    value=10,
)

show_raw_data = st.sidebar.toggle("Toon ruwe tabellen", value=False)


current_period, previous_period = filter_period(overview, period)

if current_period.empty:
    st.error("Geen data beschikbaar voor deze periode.")
    st.stop()


start_date = current_period["date"].min().date()
end_date = current_period["date"].max().date()


current_revenue = current_period["omzet"].sum()
previous_revenue = previous_period["omzet"].sum()

current_orders = current_period["orders"].sum()
previous_orders = previous_period["orders"].sum()

current_aov = current_revenue / current_orders if current_orders > 0 else 0
previous_aov = previous_revenue / previous_orders if previous_orders > 0 else 0

current_conversion = current_period["conversie"].mean()
previous_conversion = previous_period["conversie"].mean()

current_cart_adds = (
    current_period["add_to_carts"].sum()
    if "add_to_carts" in current_period.columns
    else 0
)

previous_cart_adds = (
    previous_period["add_to_carts"].sum()
    if "add_to_carts" in previous_period.columns
    else 0
)


render_header(start_date, end_date)


metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)

with metric_col1:
    show_metric(
        "Totale omzet",
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
        "Gem. orderwaarde",
        format_euro(current_aov),
        calculate_delta(current_aov, previous_aov),
    )

with metric_col4:
    show_metric(
        "Conversieratio",
        format_percent(current_conversion),
        calculate_delta(current_conversion, previous_conversion),
    )

with metric_col5:
    show_metric(
        "Add to carts",
        format_number(current_cart_adds),
        calculate_delta(current_cart_adds, previous_cart_adds),
    )


add_space()


tab_sales, tab_products, tab_funnel, tab_data = st.tabs(
    ["Sales", "Producten", "Funnel", "Data"]
)


with tab_sales:
    chart_col, side_col = st.columns([2, 1])

    with chart_col:
        st.subheader("Omzetontwikkeling")
        st.markdown(
            """
            <p class="section-note">
                Dagelijkse omzetontwikkeling binnen de geselecteerde periode.
            </p>
            """,
            unsafe_allow_html=True,
        )

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

    with side_col:
        st.subheader("Orders & AOV")

        order_fig = go.Figure()

        order_fig.add_trace(
            go.Bar(
                x=current_period["date"],
                y=current_period["orders"],
                name="Orders",
                marker_color=BRAND_GREEN,
            )
        )

        if "gemiddelde_orderwaarde" in current_period.columns:
            order_fig.add_trace(
                go.Scatter(
                    x=current_period["date"],
                    y=current_period["gemiddelde_orderwaarde"],
                    name="Gem. orderwaarde",
                    mode="lines+markers",
                    yaxis="y2",
                    line={"color": SOFT_GOLD, "width": 3},
                )
            )

            order_fig.update_layout(
                yaxis2={
                    "overlaying": "y",
                    "side": "right",
                    "showgrid": False,
                    "tickprefix": "€ ",
                }
            )

        order_fig.update_layout(title="Orders en orderwaarde")

        st.plotly_chart(
            apply_plotly_layout(order_fig),
            use_container_width=True,
        )

    trend_columns = [
        column
        for column in ["date", "omzet", "orders", "conversie"]
        if column in current_period.columns
    ]

    if len(trend_columns) > 1:
        trend_data = current_period[trend_columns].melt(
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
            title="Commerciële trends",
            color_discrete_sequence=[BRAND_GREEN, SOFT_GOLD, SOFT_BLUE],
        )

        st.plotly_chart(
            apply_plotly_layout(trend_fig),
            use_container_width=True,
        )


with tab_products:
    product_col, category_col = st.columns(2)

    with product_col:
        st.subheader("Top producten")

        if not products.empty and {"itemname", product_sort}.issubset(products.columns):
            top_products = (
                products
                .dropna(subset=[product_sort])
                .sort_values(product_sort, ascending=False)
                .head(top_n)
            )

            product_fig = px.bar(
                top_products,
                x=product_sort,
                y="itemname",
                orientation="h",
                text=product_sort,
                title=f"Top {top_n} producten op {product_sort}",
                color_discrete_sequence=[BRAND_GREEN],
            )

            product_fig.update_traces(
                texttemplate="%{text:,.0f}",
                textposition="outside",
            )

            product_fig.update_layout(
                yaxis={"categoryorder": "total ascending"},
            )

            st.plotly_chart(
                apply_plotly_layout(product_fig, height=520),
                use_container_width=True,
            )
        else:
            st.warning("Productdata mist de vereiste kolommen voor deze analyse.")

    with category_col:
        st.subheader("Top categorieën")

        if not categories.empty and {"itemcategory", "itemsviewed"}.issubset(categories.columns):
            category_data = (
                categories
                .dropna(subset=["itemsviewed"])
                .sort_values("itemsviewed", ascending=False)
                .head(10)
            )

            category_fig = px.pie(
                category_data,
                names="itemcategory",
                values="itemsviewed",
                hole=0.58,
                title="Categorieaandeel op productviews",
                color_discrete_sequence=[
                    BRAND_GREEN,
                    SOFT_GOLD,
                    SOFT_GREEN,
                    "#b6c5b9",
                    SOFT_BLUE,
                ],
            )

            category_fig.update_traces(textinfo="percent+label")

            st.plotly_chart(
                apply_plotly_layout(category_fig, height=520),
                use_container_width=True,
            )
        else:
            st.warning("Categoriedata mist `itemcategory` of `itemsviewed`.")

    add_space()

    st.subheader("Product performance tabel")

    product_table_columns = [
        column
        for column in [
            "itemname",
            "itemrevenue",
            "itemsviewed",
            "itemsaddedtocart",
            "cart_rate",
            "revenue_per_view",
        ]
        if column in products.columns
    ]

    if product_table_columns:
        product_table = products[product_table_columns].copy()

        if "itemrevenue" in product_table.columns:
            product_table = product_table.sort_values(
                "itemrevenue",
                ascending=False,
            )

        st.dataframe(
            product_table,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Geen productkolommen beschikbaar voor de tabel.")


with tab_funnel:
    st.subheader("Checkout funnel")

    funnel = normalize_columns(funnel)
    funnel_columns = ["view_item", "add_to_cart", "begin_checkout", "purchase"]
    available_columns = [
        column for column in funnel_columns if column in funnel.columns
    ]

    if available_columns:
        funnel = convert_columns_to_numeric(funnel, available_columns)

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

        funnel_data["Conversie vanaf vorige stap"] = (
            funnel_data["Aantal"] / funnel_data["Aantal"].shift(1) * 100
        ).fillna(100)

        funnel_data["Uitval vanaf vorige stap"] = (
            100 - funnel_data["Conversie vanaf vorige stap"]
        )

        funnel_fig = px.funnel(
            funnel_data,
            x="Aantal",
            y="Stap",
            title="Van productview naar aankoop",
            color_discrete_sequence=[BRAND_GREEN],
        )

        st.plotly_chart(
            apply_plotly_layout(funnel_fig, height=520),
            use_container_width=True,
        )

        step_col1, step_col2 = st.columns(2)

        with step_col1:
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

        with step_col2:
            highest_drop = funnel_data.iloc[
                funnel_data["Uitval vanaf vorige stap"].idxmax()
            ]

            st.markdown(
                f"""
                <div class="insight-card">
                    <h4>Grootste funnel-uitval</h4>
                    <p>
                        De grootste relatieve uitval zit bij
                        <strong>{highest_drop['Stap']}</strong> met
                        <strong>{format_percent(highest_drop['Uitval vanaf vorige stap'])}</strong>.
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("Geen bruikbare funnelkolommen gevonden.")

    add_space()

    st.subheader("Automatische inzichten")

    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Omzetmomentum</h4>
                <p>
                    De omzet is {format_euro(current_revenue)} in deze periode,
                    met een verandering van
                    {calculate_delta(current_revenue, previous_revenue):+.1f}%.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Orderkwaliteit</h4>
                <p>
                    De gemiddelde orderwaarde is {format_euro(current_aov)}.
                    Optimaliseer bundels, staffelkorting en cross-sells.
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
                    De gemiddelde conversieratio is {format_percent(current_conversion)}.
                    Kijk vooral naar productpagina's met veel views maar lage cart rate.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with tab_data:
    st.subheader("Datakwaliteit")

    data_col1, data_col2, data_col3, data_col4 = st.columns(4)

    with data_col1:
        st.metric("Overview-rijen", len(overview))

    with data_col2:
        st.metric("Producten", len(products))

    with data_col3:
        st.metric("Categorieën", len(categories))

    with data_col4:
        st.metric("Funnel-rijen", len(funnel))

    st.caption(
        "Gebruik deze sectie om snel te controleren of alle Google Sheet-tabs correct worden ingelezen."
    )

    if show_raw_data:
        add_space()

        st.subheader("Overview")
        st.dataframe(overview, use_container_width=True, hide_index=True)

        st.subheader("Products")
        st.dataframe(products, use_container_width=True, hide_index=True)

        st.subheader("Categories")
        st.dataframe(categories, use_container_width=True, hide_index=True)

        st.subheader("Funnel")
        st.dataframe(funnel, use_container_width=True, hide_index=True)
    else:
        st.info("Zet 'Toon ruwe tabellen' aan in de sidebar om de brondata te bekijken.")


st.caption("Van Duinkerken E-commerce Dashboard · Streamlit · Plotly · Google Sheets")