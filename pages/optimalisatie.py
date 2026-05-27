import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="Website Optimalisatieplan",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)


SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "funnel": f"{BASE_URL}/funnel",
    "pagespeed": f"{BASE_URL}/page_speed",
}


BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"
SOFT_GREEN = "#7d9b88"
SOFT_GOLD = "#c9a646"
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

#MainMenu, footer, header {{
    visibility: hidden;
}}

.vdk-main-title {{
    font-size: 42px;
    font-weight: 700;
    color: {BRAND_GREEN};
    margin: 0;
}}

.vdk-subtitle {{
    color: {TEXT_MUTED};
    font-size: 15px;
    margin-top: 8px;
    max-width: 950px;
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

.space {{
    height: 34px;
}}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return pd.DataFrame()

    if isinstance(data, dict):
        data = [data]

    return normalize_columns(pd.DataFrame(data))


def parse_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df)

    for col in [
        "add_to_carts",
        "checkout_start",
        "aankopen",
        "conversie",
        "sessies",
        "bezoekers",
        "orders",
        "omzet",
    ]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df)

    for col in ["view_item", "add_to_cart", "begin_checkout", "purchase", "count"]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    return df


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df)
    df = df.rename(columns={"pagina": "page"})

    for col in ["mobile_speed", "desktop_speed"]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    return df


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def get_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    max_date = df["date"].max()

    days = {
        "Afgelopen 7 dagen": 7,
        "Afgelopen 30 dagen": 30,
        "Afgelopen 90 dagen": 90,
        "Alles": None,
    }[label]

    if days is None:
        return df

    start_date = max_date - pd.Timedelta(days=days - 1)

    return df[df["date"] >= start_date]


def create_funnel_data(overview: pd.DataFrame, funnel: pd.DataFrame) -> pd.DataFrame:
    if not funnel.empty and {"view_item", "add_to_cart", "begin_checkout", "purchase"}.issubset(funnel.columns):
        data = {
            "Stap": [
                "Product bekeken",
                "Toegevoegd aan winkelwagen",
                "Checkout gestart",
                "Aankoop",
            ],
            "Aantal": [
                funnel["view_item"].sum(),
                funnel["add_to_cart"].sum(),
                funnel["begin_checkout"].sum(),
                funnel["purchase"].sum(),
            ],
        }
    elif not overview.empty and {"add_to_carts", "checkout_start", "aankopen"}.issubset(overview.columns):
        sessions = overview["sessies"].sum() if "sessies" in overview.columns else 0

        data = {
            "Stap": [
                "Sessies",
                "Toegevoegd aan winkelwagen",
                "Checkout gestart",
                "Aankoop",
            ],
            "Aantal": [
                sessions,
                overview["add_to_carts"].sum(),
                overview["checkout_start"].sum(),
                overview["aankopen"].sum(),
            ],
        }
    else:
        return pd.DataFrame()

    funnel_data = pd.DataFrame(data)

    funnel_data["Conversie vorige stap"] = (
        funnel_data["Aantal"] / funnel_data["Aantal"].shift(1) * 100
    ).fillna(100)

    funnel_data["Uitval vorige stap"] = 100 - funnel_data["Conversie vorige stap"]

    return funnel_data


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
            <div class="vdk-main-title">Website optimalisatieplan</div>
            <div class="vdk-subtitle">
                Dashboard voor het monitoren van conversie, checkout-uitval,
                websitesnelheid en voortgang van de optimalisaties gedurende de testmaand.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


TASKS = pd.DataFrame(
    [
        ["Algemeen", "Controle websitesnelheid uitvoeren", "Open"],
        ["Algemeen", "Pagina’s met trage laadtijden in kaart brengen", "Open"],
        ["Algemeen", "Verbeterpunten voor mobiel analyseren", "Open"],
        ["Productpagina’s", "USP’s toevoegen onder productprijs", "Open"],
        ["Productpagina’s", "Sticky koopknop toevoegen op mobiel", "Open"],
        ["Productpagina’s", "Reviews beter zichtbaar maken", "Open"],
        ["Checkout", "Checkout rustiger vormgeven", "Open"],
        ["Checkout", "Overbodige informatie verwijderen", "Open"],
        ["Checkout", "Mobiele checkout controleren", "Open"],
        ["Categoriepagina’s", "Snelle keuze knoppen toevoegen", "Open"],
        ["Zoek & filter", "Belangrijkste filters prominenter tonen", "Open"],
        ["Zoek & filter", "Zoekresultaten controleren op relevantie", "Open"],
        ["Analyse", "Wekelijkse controle conversie", "Open"],
        ["Analyse", "Wekelijkse controle checkout uitval", "Open"],
        ["Analyse", "Resultaten evalueren na 1 maand", "Open"],
    ],
    columns=["Onderdeel", "Taak", "Status"],
)


with st.spinner("Projectdata laden..."):
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
    funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))
    pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))


st.sidebar.markdown("## Van Duinkerken")
st.sidebar.markdown("Website optimalisatie")
st.sidebar.divider()

period = st.sidebar.radio(
    "Meetperiode",
    ["Afgelopen 7 dagen", "Afgelopen 30 dagen", "Afgelopen 90 dagen", "Alles"],
    index=1,
)

if st.sidebar.button("Data verversen"):
    st.cache_data.clear()
    st.rerun()


overview_filtered = get_period_data(overview, period)


render_header()


funnel_data = create_funnel_data(overview_filtered, funnel)

sessions = overview_filtered["sessies"].sum() if "sessies" in overview_filtered.columns else 0
add_to_carts = overview_filtered["add_to_carts"].sum() if "add_to_carts" in overview_filtered.columns else 0
checkout_start = overview_filtered["checkout_start"].sum() if "checkout_start" in overview_filtered.columns else 0
purchases = overview_filtered["aankopen"].sum() if "aankopen" in overview_filtered.columns else 0

add_to_cart_rate = add_to_carts / sessions * 100 if sessions > 0 else 0
checkout_start_rate = checkout_start / add_to_carts * 100 if add_to_carts > 0 else 0
purchase_rate = purchases / checkout_start * 100 if checkout_start > 0 else 0

col1, col2, col3 = st.columns(3)

col1.metric("Add-to-cart", format_percent(add_to_cart_rate), "Doel: 4–6%")
col2.metric("Checkout start", format_percent(checkout_start_rate), "Doel: 35–50%")
col3.metric("Aankoopratio", format_percent(purchase_rate), "Doel: 45–60%")


add_space()

tab_overview, tab_funnel, tab_speed, tab_tasks, tab_results = st.tabs(
    [
        "Overzicht",
        "Checkout funnel",
        "Snelheid",
        "Taken",
        "Resultaten",
    ]
)


with tab_overview:
    insight_col1, insight_col2, insight_col3 = st.columns(3)

    with insight_col1:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Conversiedoel</h4>
                <p>
                    De add-to-cart staat nu op <strong>{format_percent(add_to_cart_rate)}</strong>.
                    De gewenste bandbreedte is <strong>4–6%</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col2:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Checkout optimalisatie</h4>
                <p>
                    Checkout start is <strong>{format_percent(checkout_start_rate)}</strong>.
                    Focus op rust, duidelijkheid en minder afleiding in de checkout.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with insight_col3:
        st.markdown(
            f"""
            <div class="insight-card">
                <h4>Aankoopratio</h4>
                <p>
                    De aankoopratio vanaf checkout is <strong>{format_percent(purchase_rate)}</strong>.
                    Doel is <strong>45–60%</strong>.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    add_space()

    goal_data = pd.DataFrame(
        {
            "KPI": ["Add-to-cart", "Checkout start", "Aankoopratio"],
            "Nu": [add_to_cart_rate, checkout_start_rate, purchase_rate],
            "Doel laag": [4, 35, 45],
            "Doel hoog": [6, 50, 60],
        }
    )

    goal_fig = go.Figure()

    goal_fig.add_trace(
        go.Bar(
            x=goal_data["KPI"],
            y=goal_data["Nu"],
            name="Nu",
            marker_color=BRAND_GREEN,
        )
    )

    goal_fig.add_trace(
        go.Bar(
            x=goal_data["KPI"],
            y=goal_data["Doel laag"],
            name="Doel ondergrens",
            marker_color=SOFT_GREEN,
        )
    )

    goal_fig.add_trace(
        go.Bar(
            x=goal_data["KPI"],
            y=goal_data["Doel hoog"],
            name="Doel bovengrens",
            marker_color=SOFT_GOLD,
        )
    )

    goal_fig.update_layout(
        title="KPI’s ten opzichte van doelstellingen",
        barmode="group",
        yaxis_title="Percentage",
    )

    st.plotly_chart(
        apply_plotly_layout(goal_fig, height=480),
        use_container_width=True,
    )


with tab_funnel:
    st.subheader("Checkout funnel")

    if funnel_data.empty:
        st.warning("Geen funneldata gevonden.")
    else:
        funnel_fig = px.funnel(
            funnel_data,
            x="Aantal",
            y="Stap",
            title="Van sessie/productview naar aankoop",
            color_discrete_sequence=[BRAND_GREEN],
        )

        st.plotly_chart(
            apply_plotly_layout(funnel_fig, height=520),
            use_container_width=True,
        )

        st.dataframe(
            funnel_data.assign(
                Aantal=funnel_data["Aantal"].map(format_number),
                **{
                    "Conversie vorige stap": funnel_data["Conversie vorige stap"].map(format_percent),
                    "Uitval vorige stap": funnel_data["Uitval vorige stap"].map(format_percent),
                },
            ),
            use_container_width=True,
            hide_index=True,
        )


with tab_speed:
    st.subheader("Websitesnelheid")

    if pagespeed.empty or not {"page", "mobile_speed", "desktop_speed"}.issubset(pagespeed.columns):
        st.warning("Geen page speed data gevonden.")
    else:
        speed_data = pagespeed.sort_values("mobile_speed")

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
            title="Mobiele en desktop snelheid per pagina",
            color_discrete_sequence=[SOFT_RED, BRAND_GREEN],
        )

        speed_fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            apply_plotly_layout(speed_fig, height=620),
            use_container_width=True,
        )

        st.dataframe(
            speed_data,
            use_container_width=True,
            hide_index=True,
        )


with tab_tasks:
    st.subheader("To do website optimalisaties")

    selected_status = st.selectbox(
        "Statusfilter",
        ["Alle", "Open", "Bezig", "Afgerond"],
    )

    tasks = TASKS.copy()

    edited_tasks = st.data_editor(
        tasks,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["Open", "Bezig", "Afgerond"],
            )
        },
    )

    if selected_status != "Alle":
        edited_tasks = edited_tasks[edited_tasks["Status"] == selected_status]

    st.dataframe(
        edited_tasks,
        use_container_width=True,
        hide_index=True,
    )


with tab_results:
    st.subheader("Wekelijkse monitoring")

    if overview.empty or "date" not in overview.columns:
        st.warning("Geen datumdata beschikbaar voor wekelijkse monitoring.")
    else:
        weekly = overview.copy()
        weekly["week"] = weekly["date"].dt.to_period("W").astype(str)

        weekly = (
            weekly
            .groupby("week", as_index=False)
            .agg(
                sessies=("sessies", "sum"),
                add_to_carts=("add_to_carts", "sum"),
                checkout_start=("checkout_start", "sum"),
                aankopen=("aankopen", "sum"),
            )
        )

        weekly["add_to_cart_rate"] = (
            weekly["add_to_carts"] / weekly["sessies"].replace(0, pd.NA) * 100
        ).fillna(0)

        weekly["checkout_start_rate"] = (
            weekly["checkout_start"] / weekly["add_to_carts"].replace(0, pd.NA) * 100
        ).fillna(0)

        weekly["purchase_rate"] = (
            weekly["aankopen"] / weekly["checkout_start"].replace(0, pd.NA) * 100
        ).fillna(0)

        weekly_long = weekly.melt(
            id_vars="week",
            value_vars=[
                "add_to_cart_rate",
                "checkout_start_rate",
                "purchase_rate",
            ],
            var_name="KPI",
            value_name="Percentage",
        )

        fig = px.line(
            weekly_long,
            x="week",
            y="Percentage",
            color="KPI",
            markers=True,
            title="Wekelijkse ontwikkeling van optimalisatie-KPI’s",
            color_discrete_sequence=[BRAND_GREEN, SOFT_GREEN, SOFT_GOLD],
        )

        st.plotly_chart(
            apply_plotly_layout(fig, height=520),
            use_container_width=True,
        )

        st.dataframe(
            weekly,
            use_container_width=True,
            hide_index=True,
        )


st.caption("Van Duinkerken · Website optimalisatieplan · Dashboard")