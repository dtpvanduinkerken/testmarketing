from __future__ import annotations

import html
from dataclasses import dataclass

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


# Config ----------------------------------------------------------------------

st.set_page_config(
    page_title="Pilotmonitor website optimalisatie",
    page_icon="📈",
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
    "white": "#ffffff",
}

PERIOD_OPTIONS = {
    "Afgelopen 7 dagen": 7,
    "Afgelopen 30 dagen": 30,
    "Afgelopen 90 dagen": 90,
    "Alles": None,
}

KPI_CONFIG = {
    "add_to_cart_rate": {
        "label": "Add-to-cart",
        "low": 4,
        "high": 6,
        "description": "Aandeel sessies dat leidt tot winkelwagenactie.",
    },
    "checkout_start_rate": {
        "label": "Checkout start",
        "low": 35,
        "high": 50,
        "description": "Aandeel winkelwagens dat doorgaat naar checkout.",
    },
    "purchase_rate": {
        "label": "Aankoopratio",
        "low": 45,
        "high": 60,
        "description": "Aandeel checkouts dat eindigt in aankoop.",
    },
}

TASK_COLUMNS = [
    "Onderdeel",
    "Taak",
    "Status",
    "Prioriteit",
    "Impact",
    "Eigenaar",
    "Deadline",
    "KPI",
]


@dataclass(frozen=True)
class PilotPeriod:
    start_date: pd.Timestamp | None
    end_date: pd.Timestamp | None
    days_total: int
    days_elapsed: int
    days_remaining: int


# Styling ---------------------------------------------------------------------

def inject_style() -> None:
    st.markdown(
        f"""
        <link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">
        <style>
        html, body, [data-testid="stAppViewContainer"] {{
            background: {COLORS["background"]};
            font-family: 'sofia-pro', Arial, sans-serif;
            color: {COLORS["brand_green"]};
        }}

        .block-container {{
            padding: 42px 56px 56px 56px;
            max-width: 1500px;
        }}

        #MainMenu, footer, header {{
            visibility: hidden;
        }}

        .vdk-title {{
            font-size: 42px;
            font-weight: 750;
            color: {COLORS["brand_green"]};
            margin: 0;
            letter-spacing: -0.02em;
        }}

        .vdk-subtitle {{
            color: {COLORS["text_muted"]};
            font-size: 15px;
            margin-top: 8px;
            max-width: 980px;
            line-height: 1.6;
        }}

        .vdk-divider {{
            width: 100%;
            height: 1px;
            background: rgba(8, 68, 34, 0.08);
            margin-top: 24px;
            margin-bottom: 28px;
        }}

        [data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid rgba(8, 68, 34, 0.06);
        }}

        [data-testid="stMetric"],
        .vdk-card,
        div[data-testid="stPlotlyChart"],
        [data-testid="stDataFrame"] {{
            background: #ffffff;
            border-radius: 18px !important;
            border: 1px solid {COLORS["card_border"]};
            box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
            overflow: hidden;
        }}

        [data-testid="stMetric"] {{
            padding: 20px;
        }}

        [data-testid="stMetric"] label {{
            color: {COLORS["text_muted"]} !important;
            font-size: 14px !important;
        }}

        [data-testid="stMetricValue"] {{
            color: {COLORS["brand_green"]};
            font-size: 28px;
            font-weight: 750;
        }}

        .vdk-card {{
            padding: 22px;
            min-height: 132px;
        }}

        .vdk-card h4 {{
            color: {COLORS["brand_green"]};
            margin: 0 0 8px 0;
            font-size: 17px;
        }}

        .vdk-card p {{
            color: {COLORS["text_muted"]};
            margin: 0;
            line-height: 1.55;
            font-size: 14px;
        }}

        .status-pill {{
            display: inline-block;
            padding: 6px 11px;
            border-radius: 999px;
            font-weight: 700;
            font-size: 12px;
            margin-bottom: 12px;
        }}

        .status-good {{
            background: rgba(125, 155, 136, 0.18);
            color: {COLORS["brand_green"]};
        }}

        .status-warning {{
            background: rgba(201, 166, 70, 0.20);
            color: #7a5b00;
        }}

        .status-bad {{
            background: rgba(199, 111, 111, 0.18);
            color: #8f3030;
        }}

        .space {{
            height: 30px;
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
    except ValueError:
        st.warning("De databron gaf geen geldige JSON terug.")
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
        return 0.0

    return float(df[column].sum())


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator * 100


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float) -> str:
    return "€ " + f"{value:,.0f}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_delta_pp(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f} pp".replace(".", ",")


def get_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns:
        return df

    days = PERIOD_OPTIONS[label]

    if days is None:
        return df

    max_date = df["date"].max()
    start_date = max_date - pd.Timedelta(days=days - 1)

    return df[df["date"] >= start_date]


def get_previous_period_data(df: pd.DataFrame, label: str) -> pd.DataFrame:
    if df.empty or "date" not in df.columns or PERIOD_OPTIONS[label] is None:
        return pd.DataFrame()

    days = PERIOD_OPTIONS[label]
    max_date = df["date"].max()
    current_start = max_date - pd.Timedelta(days=days - 1)
    previous_start = current_start - pd.Timedelta(days=days)

    return df[(df["date"] >= previous_start) & (df["date"] < current_start)]


def calculate_kpis(overview: pd.DataFrame) -> dict[str, float]:
    sessions = safe_sum(overview, "sessies")
    add_to_carts = safe_sum(overview, "add_to_carts")
    checkout_start = safe_sum(overview, "checkout_start")
    purchases = safe_sum(overview, "aankopen")
    revenue = safe_sum(overview, "omzet")

    return {
        "sessions": sessions,
        "add_to_carts": add_to_carts,
        "checkout_start": checkout_start,
        "purchases": purchases,
        "revenue": revenue,
        "add_to_cart_rate": safe_rate(add_to_carts, sessions),
        "checkout_start_rate": safe_rate(checkout_start, add_to_carts),
        "purchase_rate": safe_rate(purchases, checkout_start),
        "conversion_rate": safe_rate(purchases, sessions),
    }


def get_kpi_status(value: float, low: float, high: float) -> tuple[str, str]:
    if value < low:
        return "Onder doel", "status-bad"
    if value <= high:
        return "Op doel", "status-good"
    return "Boven doel", "status-good"


def get_pilot_health(kpis: dict[str, float]) -> tuple[str, str, str]:
    statuses = [
        get_kpi_status(kpis[key], config["low"], config["high"])[0]
        for key, config in KPI_CONFIG.items()
    ]
    on_target = sum(status != "Onder doel" for status in statuses)

    if on_target == 3:
        return "Pilot ligt op koers", "status-good", "Alle kern-KPI’s halen de ondergrens."
    if on_target == 2:
        return "Pilot vraagt aandacht", "status-warning", "Twee van de drie kern-KPI’s liggen op of boven doel."
    return "Pilot heeft actie nodig", "status-bad", "Meerdere kern-KPI’s liggen onder de gewenste bandbreedte."


def create_pilot_period(df: pd.DataFrame) -> PilotPeriod:
    if df.empty or "date" not in df.columns:
        return PilotPeriod(None, None, 0, 0, 0)

    start_date = df["date"].min()
    end_date = df["date"].max()
    days_total = max((end_date - start_date).days + 1, 1)
    days_elapsed = days_total

    return PilotPeriod(
        start_date=start_date,
        end_date=end_date,
        days_total=days_total,
        days_elapsed=days_elapsed,
        days_remaining=0,
    )


def create_funnel_data(overview: pd.DataFrame, funnel: pd.DataFrame) -> pd.DataFrame:
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
    funnel_data["Uitval absoluut"] = (previous_step - funnel_data["Aantal"]).fillna(0)

    return funnel_data


def find_biggest_funnel_leak(funnel_data: pd.DataFrame) -> dict[str, str | float]:
    if funnel_data.empty or len(funnel_data) <= 1:
        return {
            "title": "Geen funnel-lek bepaald",
            "description": "Er is nog onvoldoende funneldata beschikbaar.",
        }

    leak_data = funnel_data.iloc[1:].copy()
    biggest = leak_data.sort_values("Uitval absoluut", ascending=False).iloc[0]

    return {
        "title": f"Grootste lek: {biggest['Stap']}",
        "description": (
            f"Hier vallen ongeveer {format_number(biggest['Uitval absoluut'])} "
            f"gebruikers uit ten opzichte van de vorige stap "
            f"({format_percent(biggest['Uitval vorige stap'])})."
        ),
    }


def create_weekly_data(overview: pd.DataFrame) -> pd.DataFrame:
    required_columns = {
        "date",
        "sessies",
        "add_to_carts",
        "checkout_start",
        "aankopen",
    }

    if overview.empty or not required_columns.issubset(overview.columns):
        return pd.DataFrame()

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
            omzet=("omzet", "sum") if "omzet" in weekly.columns else ("aankopen", "sum"),
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

    return weekly


def create_effect_data(current_kpis: dict[str, float], previous_kpis: dict[str, float]) -> pd.DataFrame:
    rows = []

    for key, config in KPI_CONFIG.items():
        current = current_kpis[key]
        previous = previous_kpis.get(key, 0)
        delta = current - previous

        rows.append(
            {
                "KPI": config["label"],
                "Vorige periode": previous,
                "Huidige periode": current,
                "Verschil pp": delta,
                "Conclusie": "Verbeterd" if delta > 0 else "Gedaald" if delta < 0 else "Gelijk",
            }
        )

    return pd.DataFrame(rows)


# UI helpers ------------------------------------------------------------------

def apply_plotly_layout(fig: go.Figure, height: int = 430) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font={"family": "Sofia Pro, Arial", "color": COLORS["brand_green"]},
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
            <div class="vdk-title">Pilotmonitor website optimalisatie</div>
            <div class="vdk-subtitle">
                Eén dashboard voor besluitvorming: ligt de pilot op koers,
                waar zit de grootste conversielekkage en welke optimalisatie
                verdient nu prioriteit?
            </div>
        </div>
        <div class="vdk-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


def render_card(title: str, body: str, status_class: str | None = None) -> None:
    status = f'<span class="status-pill {status_class}">{title}</span>' if status_class else ""
    heading = "" if status_class else f"<h4>{html.escape(title)}</h4>"

    st.markdown(
        f"""
        <div class="vdk-card">
            {status}
            {heading}
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(
    overview: pd.DataFrame,
    funnel: pd.DataFrame,
    pagespeed: pd.DataFrame,
) -> str:
    st.sidebar.markdown("## Van Duinkerken")
    st.sidebar.markdown("Website optimalisatiepilot")
    st.sidebar.divider()

    period = st.sidebar.radio(
        "Meetperiode",
        list(PERIOD_OPTIONS.keys()),
        index=1,
    )

    if st.sidebar.button("Data verversen"):
        st.cache_data.clear()
        st.rerun()

    st.sidebar.divider()
    st.sidebar.markdown("### Datakwaliteit")

    latest_date = "Onbekend"
    if not overview.empty and "date" in overview.columns:
        latest_date = overview["date"].max().strftime("%d-%m-%Y")

    st.sidebar.caption(f"Laatste datum: {latest_date}")
    st.sidebar.caption(f"Overview-rijen: {len(overview)}")
    st.sidebar.caption(f"Funnel-rijen: {len(funnel)}")
    st.sidebar.caption(f"Pagespeed-rijen: {len(pagespeed)}")

    return period


def render_kpi_metrics(kpis: dict[str, float], previous_kpis: dict[str, float]) -> None:
    columns = st.columns(3)

    for column, (key, config) in zip(columns, KPI_CONFIG.items()):
        delta = kpis[key] - previous_kpis.get(key, 0)
        column.metric(
            config["label"],
            format_percent(kpis[key]),
            format_delta_pp(delta),
        )


def render_goal_chart(kpis: dict[str, float]) -> None:
    goal_data = pd.DataFrame(
        {
            "KPI": [config["label"] for config in KPI_CONFIG.values()],
            "Nu": [kpis[key] for key in KPI_CONFIG.keys()],
            "Doel laag": [config["low"] for config in KPI_CONFIG.values()],
            "Doel hoog": [config["high"] for config in KPI_CONFIG.values()],
        }
    )

    fig = go.Figure()
    for column, color in {
        "Nu": COLORS["brand_green"],
        "Doel laag": COLORS["soft_green"],
        "Doel hoog": COLORS["soft_gold"],
    }.items():
        fig.add_trace(
            go.Bar(
                x=goal_data["KPI"],
                y=goal_data[column],
                name=column,
                marker_color=color,
            )
        )

    fig.update_layout(
        title="KPI’s ten opzichte van doelstellingen",
        barmode="group",
        yaxis_title="Percentage",
    )

    st.plotly_chart(apply_plotly_layout(fig, height=470), use_container_width=True)


def get_default_tasks() -> pd.DataFrame:
    return pd.DataFrame(
        [
            ["Checkout", "Checkout rustiger vormgeven", "Open", "Hoog", "Hoog", "", pd.NaT, "Aankoopratio"],
            ["Checkout", "Overbodige informatie verwijderen", "Open", "Hoog", "Hoog", "", pd.NaT, "Checkout start"],
            ["Productpagina’s", "Sticky koopknop toevoegen op mobiel", "Open", "Hoog", "Hoog", "", pd.NaT, "Add-to-cart"],
            ["Productpagina’s", "USP’s toevoegen onder productprijs", "Open", "Midden", "Hoog", "", pd.NaT, "Add-to-cart"],
            ["Productpagina’s", "Reviews beter zichtbaar maken", "Open", "Midden", "Midden", "", pd.NaT, "Add-to-cart"],
            ["Snelheid", "Pagina’s met trage laadtijden verbeteren", "Open", "Hoog", "Hoog", "", pd.NaT, "Add-to-cart"],
            ["Snelheid", "Mobiele performance controleren", "Open", "Hoog", "Midden", "", pd.NaT, "Aankoopratio"],
            ["Categoriepagina’s", "Snelle keuze knoppen toevoegen", "Open", "Laag", "Midden", "", pd.NaT, "Add-to-cart"],
            ["Zoek & filter", "Belangrijkste filters prominenter tonen", "Open", "Midden", "Midden", "", pd.NaT, "Add-to-cart"],
            ["Analyse", "Wekelijkse controle conversie", "Bezig", "Hoog", "Midden", "", pd.NaT, "Alle KPI’s"],
            ["Analyse", "Resultaten evalueren na 1 maand", "Open", "Hoog", "Hoog", "", pd.NaT, "Alle KPI’s"],
        ],
        columns=TASK_COLUMNS,
    )
    tasks["Deadline"] = pd.to_datetime(tasks["Deadline"], errors="coerce")

    return tasks


# Main app --------------------------------------------------------------------

def main() -> None:
    inject_style()

    with st.spinner("Projectdata laden..."):
        overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
        funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))
        pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))

    period = render_sidebar(overview, funnel, pagespeed)
    overview_filtered = get_period_data(overview, period)
    previous_overview = get_previous_period_data(overview, period)

    kpis = calculate_kpis(overview_filtered)
    previous_kpis = calculate_kpis(previous_overview)
    pilot_period = create_pilot_period(overview)
    funnel_data = create_funnel_data(overview_filtered, funnel)
    biggest_leak = find_biggest_funnel_leak(funnel_data)
    pilot_status, pilot_status_class, pilot_status_text = get_pilot_health(kpis)

    render_header()

    summary_cols = st.columns(4)
    with summary_cols[0]:
        render_card(pilot_status, pilot_status_text, pilot_status_class)
    with summary_cols[1]:
        body = (
            f"Van <strong>{pilot_period.start_date.strftime('%d-%m-%Y')}</strong> "
            f"tot <strong>{pilot_period.end_date.strftime('%d-%m-%Y')}</strong>."
            if pilot_period.start_date is not None and pilot_period.end_date is not None
            else "Nog geen geldige datumdata beschikbaar."
        )
        render_card("Pilotperiode", body)
    with summary_cols[2]:
        render_card(
            "Volume",
            (
                f"<strong>{format_number(kpis['sessions'])}</strong> sessies, "
                f"<strong>{format_number(kpis['purchases'])}</strong> aankopen."
            ),
        )
    with summary_cols[3]:
        render_card(
            "Omzet",
            f"Totale omzet in periode: <strong>{format_currency(kpis['revenue'])}</strong>.",
        )

    add_space()
    render_kpi_metrics(kpis, previous_kpis)
    add_space()

    tab_overview, tab_funnel, tab_speed, tab_actions, tab_effect = st.tabs(
        ["Beslisoverzicht", "Funnel", "Snelheid", "Acties", "Effectmeting"]
    )

    with tab_overview:
        cols = st.columns(3)
        for col, (key, config) in zip(cols, KPI_CONFIG.items()):
            status, status_class = get_kpi_status(
                kpis[key],
                config["low"],
                config["high"],
            )
            with col:
                render_card(
                    status,
                    (
                        f"<strong>{config['label']}</strong>: "
                        f"{format_percent(kpis[key])}. Doelbandbreedte: "
                        f"{format_percent(config['low'])}–{format_percent(config['high'])}. "
                        f"{config['description']}"
                    ),
                    status_class,
                )

        add_space()

        cols = st.columns([2, 1])
        with cols[0]:
            render_goal_chart(kpis)
        with cols[1]:
            render_card(
                biggest_leak["title"],
                biggest_leak["description"],
                "status-warning",
            )
            add_space()
            lowest_kpi = min(
                KPI_CONFIG.keys(),
                key=lambda key: kpis[key] / KPI_CONFIG[key]["low"] if KPI_CONFIG[key]["low"] else 0,
            )
            render_card(
                "Aanbevolen focus",
                (
                    f"Prioriteer optimalisaties rond <strong>{KPI_CONFIG[lowest_kpi]['label']}</strong>. "
                    "Deze KPI ligt relatief het verst van de ondergrens af."
                ),
            )

    with tab_funnel:
        st.subheader("Conversiefunnel")

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

            display_funnel = funnel_data.assign(
                Aantal=funnel_data["Aantal"].map(format_number),
                **{
                    "Conversie vorige stap": funnel_data["Conversie vorige stap"].map(format_percent),
                    "Uitval vorige stap": funnel_data["Uitval vorige stap"].map(format_percent),
                    "Uitval absoluut": funnel_data["Uitval absoluut"].map(format_number),
                },
            )
            st.dataframe(display_funnel, use_container_width=True, hide_index=True)

    with tab_speed:
        st.subheader("Websitesnelheid")
        required_columns = {"page", "mobile_speed", "desktop_speed"}

        if pagespeed.empty or not required_columns.issubset(pagespeed.columns):
            st.warning("Geen page speed data gevonden.")
        else:
            speed_data = pagespeed.sort_values("mobile_speed").copy()
            speed_data["mobiele_status"] = pd.cut(
                speed_data["mobile_speed"],
                bins=[-1, 49, 89, 100],
                labels=["Slecht", "Verbeteren", "Goed"],
            )

            worst_pages = speed_data.head(3)
            cols = st.columns(3)
            for col, (_, row) in zip(cols, worst_pages.iterrows()):
                with col:
                    render_card(
                        "Mobiele aandachtspagina",
                        (
                            f"<strong>{html.escape(str(row['page']))}</strong><br>"
                            f"Mobiel: {format_number(row['mobile_speed'])}, "
                            f"desktop: {format_number(row['desktop_speed'])}."
                        ),
                        "status-warning" if row["mobile_speed"] >= 50 else "status-bad",
                    )

            add_space()

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
                color_discrete_sequence=[COLORS["soft_red"], COLORS["brand_green"]],
            )
            speed_fig.update_layout(yaxis={"categoryorder": "total ascending"})

            st.plotly_chart(
                apply_plotly_layout(speed_fig, height=620),
                use_container_width=True,
            )
            st.dataframe(speed_data, use_container_width=True, hide_index=True)

    with tab_actions:
        st.subheader("Actieplanning")

        if "tasks" not in st.session_state:
            st.session_state.tasks = get_default_tasks()
        else:
            st.session_state.tasks["Deadline"] = pd.to_datetime(
                st.session_state.tasks["Deadline"],
                errors="coerce",
            )

        selected_status = st.selectbox(
            "Statusfilter",
            ["Alle", "Open", "Bezig", "Afgerond"],
        )
        selected_priority = st.selectbox(
            "Prioriteitsfilter",
            ["Alle", "Hoog", "Midden", "Laag"],
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
                ),
                "Prioriteit": st.column_config.SelectboxColumn(
                    "Prioriteit",
                    options=["Hoog", "Midden", "Laag"],
                ),
                "Impact": st.column_config.SelectboxColumn(
                    "Impact",
                    options=["Hoog", "Midden", "Laag"],
                ),
                "Deadline": st.column_config.DateColumn("Deadline"),
            },
        )

        visible_tasks = st.session_state.tasks.copy()
        if selected_status != "Alle":
            visible_tasks = visible_tasks[visible_tasks["Status"] == selected_status]
        if selected_priority != "Alle":
            visible_tasks = visible_tasks[visible_tasks["Prioriteit"] == selected_priority]

        st.dataframe(visible_tasks, use_container_width=True, hide_index=True)

    with tab_effect:
        st.subheader("Effectmeting")

        if previous_overview.empty:
            st.info("Voor effectmeting is een vorige periode nodig. Kies bijvoorbeeld 7, 30 of 90 dagen.")
        else:
            effect_data = create_effect_data(kpis, previous_kpis)

            effect_fig = px.bar(
                effect_data,
                x="KPI",
                y="Verschil pp",
                color="Conclusie",
                title="Verschil huidige periode versus vorige periode",
                color_discrete_map={
                    "Verbeterd": COLORS["soft_green"],
                    "Gedaald": COLORS["soft_red"],
                    "Gelijk": COLORS["soft_gold"],
                },
            )
            effect_fig.add_hline(y=0, line_dash="dash", line_color="rgba(8, 68, 34, 0.25)")

            st.plotly_chart(
                apply_plotly_layout(effect_fig, height=480),
                use_container_width=True,
            )

            display_effect = effect_data.assign(
                **{
                    "Vorige periode": effect_data["Vorige periode"].map(format_percent),
                    "Huidige periode": effect_data["Huidige periode"].map(format_percent),
                    "Verschil pp": effect_data["Verschil pp"].map(format_delta_pp),
                }
            )
            st.dataframe(display_effect, use_container_width=True, hide_index=True)

        weekly = create_weekly_data(overview)
        if not weekly.empty:
            add_space()
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

            weekly_fig = px.line(
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
                apply_plotly_layout(weekly_fig, height=520),
                use_container_width=True,
            )
            st.dataframe(weekly, use_container_width=True, hide_index=True)

    st.caption("Van Duinkerken · Pilotmonitor website optimalisatie")


if __name__ == "__main__":
    main()
