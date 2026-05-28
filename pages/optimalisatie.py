from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# Config ----------------------------------------------------------------------

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

COLORS = {
    "brand_green": "#084422",
    "background": "#f7f3ec",
    "text_muted": "#6f766f",
    "card_border": "rgba(8, 68, 34, 0.07)",
    "soft_green": "#7d9b88",
    "soft_gold": "#c9a646",
    "soft_red": "#c76f6f",
}

PERIOD_OPTIONS = {
    "Afgelopen 7 dagen": 7,
    "Afgelopen 30 dagen": 30,
    "Afgelopen 90 dagen": 90,
    "Alles": None,
}

KPI_TARGETS = pd.DataFrame(
    {
        "KPI": ["Add-to-cart", "Checkout start", "Aankoopratio"],
        "Doel laag": [4, 35, 45],
        "Doel hoog": [6, 50, 60],
    }
)


# Styling ---------------------------------------------------------------------

def inject_style() -> None:
    st.markdown(
        f"""
        <link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">
        <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background: {COLORS["background"]};
            font-family: 'sofia-pro', sans-serif;
            color: {COLORS["brand_green"]};
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
            color: {COLORS["brand_green"]};
            margin: 0;
        }}

        .vdk-subtitle {{
            color: {COLORS["text_muted"]};
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

        [data-testid="stMetric"],
        .insight-card,
        div[data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"] {{
            background: #ffffff;
            border-radius: 18px !important;
            border: 1px solid {COLORS["card_border"]};
            box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
            overflow: hidden;
        }}

        [data-testid="stMetric"] {{
            padding: 22px;
        }}

        [data-testid="stMetric"] label {{
            color: {COLORS["text_muted"]} !important;
            font-size: 14px !important;
        }}

        [data-testid="stMetricValue"] {{
            color: {COLORS["brand_green"]};
            font-size: 28px;
            font-weight: 700;
        }}

        .insight-card {{
            padding: 22px;
            min-height: 145px;
        }}

        .insight-card h4 {{
            color: {COLORS["brand_green"]};
            margin: 0 0 8px 0;
            font-size: 18px;
        }}

        .insight-card p {{
            color: {COLORS["text_muted"]};
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


# Data helpers ----------------------------------------------------------------

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


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as error:
        st.warning(f"Data kon niet worden geladen: {error}")
        return pd.DataFrame()

    if isinstance(data, dict):
        data = [data]

    return normalize_columns(pd.DataFrame(data))


def clean_numeric_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    df = normalize_columns(df)

    for column in columns:
        if column in df.columns:
            df[column] = parse_number(df[column])

    return df


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = clean_numeric_columns(
        df,
        [
            "add_to_carts",
            "checkout_start",
            "aankopen",
            "conversie",
            "sessies",
            "bezoekers",
            "orders",
            "omzet",
        ],
    )

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    return clean_numeric_columns(
        df,
        ["view_item", "add_to_cart", "begin_checkout", "purchase", "count"],
    )


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = normalize_columns(df).rename(columns={"pagina": "page"})

    return clean_numeric_columns(df, ["mobile_speed", "desktop_speed"])


def safe_sum(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return 0

    return float(df[column].sum())


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0

    return numerator / denominator * 100


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def get_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    days = PERIOD_OPTIONS[label]

    if days is None:
        return df

    max_date = df["date"].max()
    start_date = max_date - pd.Timedelta(days=days - 1)

    return df[df["date"] >= start_date]


def calculate_kpis(overview: pd.DataFrame) -> dict[str, float]:
    sessions = safe_sum(overview, "sessies")
    add_to_carts = safe_sum(overview, "add_to_carts")
    checkout_start = safe_sum(overview, "checkout_start")
    purchases = safe_sum(overview, "aankopen")

    return {
        "sessions": sessions,
        "add_to_carts": add_to_carts,
        "checkout_start": checkout_start,
        "purchases": purchases,
        "add_to_cart_rate": safe_rate(add_to_carts, sessions),
        "checkout_start_rate": safe_rate(checkout_start, add_to_carts),
        "purchase_rate": safe_rate(purchases, checkout_start),
    }


def create_funnel_data(
    overview: pd.DataFrame,
    funnel: pd.DataFrame,
) -> pd.DataFrame:
    funnel_columns = {"view_item", "add_to_cart", "begin_checkout", "purchase"}

    if not funnel.empty and funnel_columns.issubset(funnel.columns):
        data = {
            "Stap": [
                "Product bekeken",
                "Toegevoegd aan winkelwagen",
                "Checkout gestart",
                "Aankoop",
            ],
            "Aantal": [
                safe_sum(funnel, "view_item"),
                safe_sum(funnel, "add_to_cart"),
                safe_sum(funnel, "begin_checkout"),
                safe_sum(funnel, "purchase"),
            ],
        }
    elif {"add_to_carts", "checkout_start", "aankopen"}.issubset(overview.columns):
        data = {
            "Stap": [
                "Sessies",
                "Toegevoegd aan winkelwagen",
                "Checkout gestart",
                "Aankoop",
            ],
            "Aantal": [
                safe_sum(overview, "sessies"),
                safe_sum(overview, "add_to_carts"),
                safe_sum(overview, "checkout_start"),
                safe_sum(overview, "aankopen"),
            ],
        }
    else:
        return pd.DataFrame()

    funnel_data = pd.DataFrame(data)
    previous_step = funnel_data["Aantal"].shift(1)

    funnel_data["Conversie vorige stap"] = [
        100 if pd.isna(previous) else safe_rate(current, previous)
        for current, previous in zip(funnel_data["Aantal"], previous_step)
    ]
    funnel_data["Uitval vorige stap"] = 100 - funnel_data["Conversie vorige stap"]

    return funnel_data


# UI helpers ------------------------------------------------------------------

def apply_plotly_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={
            "family": "Sofia Pro, Arial",
            "color": COLORS["brand_green"],
        },
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
                websitesnelheid en voortgang van de optimalisaties gedurende
                de testmaand.
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


def render_insight_card(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="insight-card">
            <h4>{title}</h4>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_default_tasks() -> pd.DataFrame:
    return pd.DataFrame(
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


# App -------------------------------------------------------------------------

def main() -> None:
    inject_style()

    with st.spinner("Projectdata laden..."):
        overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
        funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))
        pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))

    st.sidebar.markdown("## Van Duinkerken")
    st.sidebar.markdown("Website optimalisatie")
    st.sidebar.divider()

    period = st.sidebar.radio(
        "Meetperiode",
        list(PERIOD_OPTIONS.keys()),
        index=1,
    )

    if st.sidebar.button("Data verversen"):
        st.cache_data.clear()
        st.rerun()

    overview_filtered = get_period_data(overview, period)
    kpis = calculate_kpis(overview_filtered)
    funnel_data = create_funnel_data(overview_filtered, funnel)

    render_header()

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Add-to-cart",
        format_percent(kpis["add_to_cart_rate"]),
        "Doel: 4–6%",
    )
    col2.metric(
        "Checkout start",
        format_percent(kpis["checkout_start_rate"]),
        "Doel: 35–50%",
    )
    col3.metric(
        "Aankoopratio",
        format_percent(kpis["purchase_rate"]),
        "Doel: 45–60%",
    )

    add_space()

    tab_overview, tab_funnel, tab_speed, tab_tasks, tab_results = st.tabs(
        ["Overzicht", "Checkout funnel", "Snelheid", "Taken", "Resultaten"]
    )

    with tab_overview:
        insight_col1, insight_col2, insight_col3 = st.columns(3)

        with insight_col1:
            render_insight_card(
                "Conversiedoel",
                (
                    "De add-to-cart staat nu op "
                    f"<strong>{format_percent(kpis['add_to_cart_rate'])}</strong>. "
                    "De gewenste bandbreedte is <strong>4–6%</strong>."
                ),
            )

        with insight_col2:
            render_insight_card(
                "Checkout optimalisatie",
                (
                    "Checkout start is "
                    f"<strong>{format_percent(kpis['checkout_start_rate'])}</strong>. "
                    "Focus op rust, duidelijkheid en minder afleiding."
                ),
            )

        with insight_col3:
            render_insight_card(
                "Aankoopratio",
                (
                    "De aankoopratio vanaf checkout is "
                    f"<strong>{format_percent(kpis['purchase_rate'])}</strong>. "
                    "Doel is <strong>45–60%</strong>."
                ),
            )

        add_space()

        goal_data = KPI_TARGETS.assign(
            Nu=[
                kpis["add_to_cart_rate"],
                kpis["checkout_start_rate"],
                kpis["purchase_rate"],
            ]
        )

        goal_fig = go.Figure()
        for column, color in {
            "Nu": COLORS["brand_green"],
            "Doel laag": COLORS["soft_green"],
            "Doel hoog": COLORS["soft_gold"],
        }.items():
            goal_fig.add_trace(
                go.Bar(
                    x=goal_data["KPI"],
                    y=goal_data[column],
                    name=column,
                    marker_color=color,
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
                color_discrete_sequence=[COLORS["brand_green"]],
            )

            st.plotly_chart(
                apply_plotly_layout(funnel_fig, height=520),
                use_container_width=True,
            )

            st.dataframe(
                funnel_data.assign(
                    Aantal=funnel_data["Aantal"].map(format_number),
                    **{
                        "Conversie vorige stap": funnel_data[
                            "Conversie vorige stap"
                        ].map(format_percent),
                        "Uitval vorige stap": funnel_data[
                            "Uitval vorige stap"
                        ].map(format_percent),
                    },
                ),
                use_container_width=True,
                hide_index=True,
            )

    with tab_speed:
        st.subheader("Websitesnelheid")

        required_columns = {"page", "mobile_speed", "desktop_speed"}

        if pagespeed.empty or not required_columns.issubset(pagespeed.columns):
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
                color_discrete_sequence=[
                    COLORS["soft_red"],
                    COLORS["brand_green"],
                ],
            )

            speed_fig.update_layout(yaxis={"categoryorder": "total ascending"})

            st.plotly_chart(
                apply_plotly_layout(speed_fig, height=620),
                use_container_width=True,
            )

            st.dataframe(speed_data, use_container_width=True, hide_index=True)

    with tab_tasks:
        st.subheader("To do website optimalisaties")

        if "tasks" not in st.session_state:
            st.session_state.tasks = get_default_tasks()

        selected_status = st.selectbox(
            "Statusfilter",
            ["Alle", "Open", "Bezig", "Afgerond"],
        )

        st.session_state.tasks = st.data_editor(
            st.session_state.tasks,
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

        visible_tasks = st.session_state.tasks.copy()

        if selected_status != "Alle":
            visible_tasks = visible_tasks[visible_tasks["Status"] == selected_status]

        st.dataframe(visible_tasks, use_container_width=True, hide_index=True)

    with tab_results:
        st.subheader("Wekelijkse monitoring")

        required_columns = {
            "date",
            "sessies",
            "add_to_carts",
            "checkout_start",
            "aankopen",
        }

        if overview.empty or not required_columns.issubset(overview.columns):
            st.warning("Geen volledige datumdata beschikbaar.")
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

            weekly["add_to_cart_rate"] = weekly.apply(
                lambda row: safe_rate(row["add_to_carts"], row["sessies"]),
                axis=1,
            )
            weekly["checkout_start_rate"] = weekly.apply(
                lambda row: safe_rate(row["checkout_start"], row["add_to_carts"]),
                axis=1,
            )
            weekly["purchase_rate"] = weekly.apply(
                lambda row: safe_rate(row["aankopen"], row["checkout_start"]),
                axis=1,
            )

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
                color_discrete_sequence=[
                    COLORS["brand_green"],
                    COLORS["soft_green"],
                    COLORS["soft_gold"],
                ],
            )

            st.plotly_chart(
                apply_plotly_layout(fig, height=520),
                use_container_width=True,
            )

            st.dataframe(weekly, use_container_width=True, hide_index=True)

    st.caption("Van Duinkerken · Website optimalisatieplan · Dashboard")


if __name__ == "__main__":
    main()
