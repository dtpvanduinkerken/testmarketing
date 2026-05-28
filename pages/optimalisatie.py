from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st


st.set_page_config(
    page_title="Pilotmonitor website optimalisatie",
    page_icon="📈",
    layout="wide",
)

SHEET_ID = "1wiE1a6rjX7bV2dun-R33SdoHsf70XPrdrB957bA8zFo"
BASE_URL = f"https://opensheet.elk.sh/{SHEET_ID}"

SHEET_URLS = {
    "overview": f"{BASE_URL}/overview_kpis",
    "funnel": f"{BASE_URL}/funnel",
    "pagespeed": f"{BASE_URL}/page_speed",
}

COLORS = {
    "green": "#084422",
    "light_green": "#7d9b88",
    "gold": "#c9a646",
    "red": "#c76f6f",
    "background": "#f7f3ec",
    "muted": "#6f766f",
}

PERIOD_OPTIONS = {
    "Afgelopen 7 dagen": 7,
    "Afgelopen 30 dagen": 30,
    "Afgelopen 90 dagen": 90,
    "Alles": None,
}

KPI_TARGETS = {
    "add_to_cart_rate": {
        "label": "Add-to-cart",
        "low": 4,
        "high": 6,
    },
    "checkout_rate": {
        "label": "Checkout start",
        "low": 35,
        "high": 50,
    },
    "purchase_rate": {
        "label": "Aankoopratio",
        "low": 45,
        "high": 60,
    },
}


st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        background: #f7f3ec;
        color: #084422;
    }

    .block-container {
        padding: 40px;
        max-width: 1500px;
    }

    #MainMenu, footer, header {
        visibility: hidden;
    }

    .dashboard-title {
        font-size: 42px;
        font-weight: 800;
        color: #084422;
        margin-bottom: 8px;
    }

    .dashboard-subtitle {
        color: #6f766f;
        font-size: 15px;
        margin-bottom: 28px;
        max-width: 900px;
        line-height: 1.6;
    }

    .summary-card {
        background: #ffffff;
        border-radius: 18px;
        padding: 22px;
        border: 1px solid rgba(8, 68, 34, 0.07);
        box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
        min-height: 132px;
    }

    .summary-card h3 {
        color: #084422;
        font-size: 18px;
        margin: 0 0 8px 0;
    }

    .summary-card p {
        color: #6f766f;
        font-size: 14px;
        line-height: 1.5;
        margin: 0;
    }

    .status-good,
    .status-warning,
    .status-bad {
        display: inline-block;
        padding: 6px 11px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        margin-bottom: 12px;
    }

    .status-good {
        color: #084422;
        background: rgba(125, 155, 136, 0.18);
    }

    .status-warning {
        color: #7a5b00;
        background: rgba(201, 166, 70, 0.22);
    }

    .status-bad {
        color: #8f3030;
        background: rgba(199, 111, 111, 0.18);
    }

    div[data-testid="stMetric"] {
        background: white;
        border-radius: 18px;
        padding: 20px;
        border: 1px solid rgba(8, 68, 34, 0.06);
        box-shadow: 0 6px 18px rgba(8, 68, 34, 0.03);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = (
        df.columns
        .str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def parse_number(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce").fillna(0)


@st.cache_data(ttl=300, show_spinner=False)
def load_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            data = [data]

        return normalize_columns(pd.DataFrame(data))
    except Exception as error:
        st.warning(f"Data kon niet geladen worden: {error}")
        return pd.DataFrame()


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    for col in ["sessies", "add_to_carts", "checkout_start", "aankopen", "omzet"]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"]).sort_values("date")

    return df


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if {"stap", "aantal"}.issubset(df.columns):
        df = df.rename(columns={"stap": "Stap", "aantal": "Aantal"})
        df["Aantal"] = parse_number(df["Aantal"])
        return df[["Stap", "Aantal"]]

    return pd.DataFrame()


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if "pagina" in df.columns:
        df = df.rename(columns={"pagina": "page"})

    for col in ["mobile_speed", "desktop_speed"]:
        if col in df.columns:
            df[col] = parse_number(df[col])

    return df


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


def safe_sum(df: pd.DataFrame, column: str) -> float:
    if df.empty or column not in df.columns:
        return 0.0

    return float(df[column].sum())


def safe_rate(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0

    return numerator / denominator * 100


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    sessions = safe_sum(df, "sessies")
    add_to_carts = safe_sum(df, "add_to_carts")
    checkout_start = safe_sum(df, "checkout_start")
    purchases = safe_sum(df, "aankopen")
    revenue = safe_sum(df, "omzet")

    return {
        "sessions": sessions,
        "add_to_carts": add_to_carts,
        "checkout_start": checkout_start,
        "purchases": purchases,
        "revenue": revenue,
        "add_to_cart_rate": safe_rate(add_to_carts, sessions),
        "checkout_rate": safe_rate(checkout_start, add_to_carts),
        "purchase_rate": safe_rate(purchases, checkout_start),
        "conversion_rate": safe_rate(purchases, sessions),
    }


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float) -> str:
    return f"€ {format_number(value)}"


def format_delta_pp(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f} pp".replace(".", ",")


def get_kpi_status(value: float, low: float, high: float) -> tuple[str, str]:
    if value < low:
        return "Onder doel", "status-bad"
    if value <= high:
        return "Op doel", "status-good"
    return "Boven doel", "status-good"


def get_pilot_status(kpis: dict[str, float]) -> tuple[str, str, str]:
    statuses = []

    for key, config in KPI_TARGETS.items():
        status, _ = get_kpi_status(kpis[key], config["low"], config["high"])
        statuses.append(status)

    on_target = sum(status != "Onder doel" for status in statuses)

    if on_target == 3:
        return "Pilot op koers", "status-good", "Alle kern-KPI’s halen de ondergrens."

    if on_target == 2:
        return "Aandacht nodig", "status-warning", "Twee van de drie kern-KPI’s halen de ondergrens."

    return "Actie nodig", "status-bad", "Meerdere KPI’s liggen onder de gewenste bandbreedte."


def make_funnel_data(funnel: pd.DataFrame, kpis: dict[str, float]) -> pd.DataFrame:
    if not funnel.empty and {"Stap", "Aantal"}.issubset(funnel.columns):
        funnel_df = funnel.copy()
    else:
        funnel_df = pd.DataFrame(
            {
                "Stap": ["Sessies", "Add-to-cart", "Checkout", "Aankoop"],
                "Aantal": [
                    kpis["sessions"],
                    kpis["add_to_carts"],
                    kpis["checkout_start"],
                    kpis["purchases"],
                ],
            }
        )

    previous = funnel_df["Aantal"].shift(1)

    funnel_df["Conversie vorige stap"] = [
        100 if pd.isna(prev) else safe_rate(current, prev)
        for current, prev in zip(funnel_df["Aantal"], previous)
    ]

    funnel_df["Uitval absoluut"] = (previous - funnel_df["Aantal"]).fillna(0)
    funnel_df["Uitval vorige stap"] = 100 - funnel_df["Conversie vorige stap"]

    return funnel_df


def get_biggest_leak(funnel_df: pd.DataFrame) -> str:
    if funnel_df.empty or len(funnel_df) < 2:
        return "Nog onvoldoende funneldata beschikbaar."

    leak_df = funnel_df.iloc[1:].sort_values("Uitval absoluut", ascending=False)
    row = leak_df.iloc[0]

    return (
        f"Grootste uitval zit bij **{row['Stap']}**: "
        f"{format_number(row['Uitval absoluut'])} bezoekers "
        f"({format_percent(row['Uitval vorige stap'])})."
    )


def apply_plotly_layout(fig: go.Figure, height: int = 450) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=30),
        font=dict(color=COLORS["green"]),
        legend=dict(orientation="h", y=1.08, x=0),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(8, 68, 34, 0.08)")
    return fig


def render_card(title: str, body: str, status_class: str | None = None) -> None:
    if status_class is None:
        st.markdown(
            f"""
            <div class="summary-card">
                <h3>{title}</h3>
                <p>{body}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="summary-card">
                <span class="{status_class}">{title}</span>
                <p>{body}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


with st.spinner("Dashboard laden..."):
    overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
    funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))
    pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))


st.sidebar.title("Website optimalisatie")
st.sidebar.caption("Pilotmonitor")

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


overview_filtered = get_period_data(overview, period)
previous_overview = get_previous_period_data(overview, period)

kpis = calculate_kpis(overview_filtered)
previous_kpis = calculate_kpis(previous_overview)
funnel_df = make_funnel_data(funnel, kpis)

pilot_title, pilot_status_class, pilot_text = get_pilot_status(kpis)


st.markdown(
    """
    <div class="dashboard-title">Pilotmonitor website optimalisatie</div>
    <div class="dashboard-subtitle">
        Managementdashboard voor conversie, funnel-uitval, snelheid en acties.
        Focus: snel zien of de pilot op koers ligt en waar actie nodig is.
    </div>
    """,
    unsafe_allow_html=True,
)


summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)

with summary_col1:
    render_card(pilot_title, pilot_text, pilot_status_class)

with summary_col2:
    render_card(
        "Volume",
        (
            f"<strong>{format_number(kpis['sessions'])}</strong> sessies<br>"
            f"<strong>{format_number(kpis['purchases'])}</strong> aankopen"
        ),
    )

with summary_col3:
    render_card(
        "Conversie",
        (
            "Totale conversieratio: "
            f"<strong>{format_percent(kpis['conversion_rate'])}</strong>"
        ),
    )

with summary_col4:
    render_card(
        "Omzet",
        f"Totale omzet in periode: <strong>{format_currency(kpis['revenue'])}</strong>",
    )

st.write("")


metric_col1, metric_col2, metric_col3 = st.columns(3)
metric_cols = [metric_col1, metric_col2, metric_col3]

for col, (key, config) in zip(metric_cols, KPI_TARGETS.items()):
    delta = kpis[key] - previous_kpis.get(key, 0)
    col.metric(
        config["label"],
        format_percent(kpis[key]),
        format_delta_pp(delta),
    )

st.write("")


tab_overview, tab_funnel, tab_speed, tab_actions, tab_effect = st.tabs(
    ["Beslisoverzicht", "Funnel", "Snelheid", "Acties", "Effectmeting"]
)


with tab_overview:
    col_left, col_right = st.columns([2, 1])

    with col_left:
        goal_df = pd.DataFrame(
            {
                "KPI": [item["label"] for item in KPI_TARGETS.values()],
                "Nu": [kpis[key] for key in KPI_TARGETS.keys()],
                "Doel laag": [item["low"] for item in KPI_TARGETS.values()],
                "Doel hoog": [item["high"] for item in KPI_TARGETS.values()],
            }
        )

        fig = go.Figure()

        for column, color in {
            "Nu": COLORS["green"],
            "Doel laag": COLORS["light_green"],
            "Doel hoog": COLORS["gold"],
        }.items():
            fig.add_trace(
                go.Bar(
                    x=goal_df["KPI"],
                    y=goal_df[column],
                    name=column,
                    marker_color=color,
                )
            )

        fig.update_layout(
            title="KPI’s ten opzichte van doelstellingen",
            barmode="group",
            yaxis_title="Percentage",
        )

        st.plotly_chart(
            apply_plotly_layout(fig, 500),
            use_container_width=True,
        )

    with col_right:
        st.markdown("### Grootste aandachtspunt")
        st.info(get_biggest_leak(funnel_df))

        st.markdown("### Aanbevolen focus")

        weakest_kpi = min(
            KPI_TARGETS.keys(),
            key=lambda key: kpis[key] / KPI_TARGETS[key]["low"],
        )

        st.warning(
            f"Prioriteer acties rond **{KPI_TARGETS[weakest_kpi]['label']}**. "
            "Deze KPI ligt relatief het verst van de doelondergrens af."
        )

        st.markdown("### Focuspunten")
        st.markdown(
            """
- Checkout vereenvoudigen
- Mobiele snelheid verbeteren
- Sticky add-to-cart testen
- Reviews prominenter maken
            """
        )


with tab_funnel:
    st.subheader("Conversiefunnel")

    fig = px.funnel(
        funnel_df,
        x="Aantal",
        y="Stap",
        color_discrete_sequence=[COLORS["green"]],
    )

    st.plotly_chart(
        apply_plotly_layout(fig, 520),
        use_container_width=True,
    )

    display_funnel = funnel_df.copy()
    display_funnel["Aantal"] = display_funnel["Aantal"].map(format_number)
    display_funnel["Conversie vorige stap"] = display_funnel[
        "Conversie vorige stap"
    ].map(format_percent)
    display_funnel["Uitval absoluut"] = display_funnel["Uitval absoluut"].map(
        format_number
    )
    display_funnel["Uitval vorige stap"] = display_funnel[
        "Uitval vorige stap"
    ].map(format_percent)

    st.dataframe(
        display_funnel,
        use_container_width=True,
        hide_index=True,
    )


with tab_speed:
    st.subheader("Websitesnelheid")

    required_cols = {"page", "mobile_speed", "desktop_speed"}

    if pagespeed.empty or not required_cols.issubset(pagespeed.columns):
        st.warning("Geen pagespeed data gevonden.")
    else:
        speed_data = pagespeed.sort_values("mobile_speed").copy()

        speed_data["mobiele_status"] = pd.cut(
            speed_data["mobile_speed"],
            bins=[-1, 49, 89, 100],
            labels=["Slecht", "Verbeteren", "Goed"],
        )

        worst_pages = speed_data.head(3)
        speed_cols = st.columns(3)

        for col, (_, row) in zip(speed_cols, worst_pages.iterrows()):
            with col:
                st.metric(
                    str(row["page"]),
                    format_number(row["mobile_speed"]),
                    f"Desktop {format_number(row['desktop_speed'])}",
                )

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
            orientation="h",
            color="Device",
            barmode="group",
            color_discrete_sequence=[COLORS["red"], COLORS["green"]],
        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"})

        st.plotly_chart(
            apply_plotly_layout(fig, 620),
            use_container_width=True,
        )

        st.dataframe(
            speed_data,
            use_container_width=True,
            hide_index=True,
        )


with tab_actions:
    st.subheader("Actieplanning")

    if "tasks" not in st.session_state:
        st.session_state.tasks = pd.DataFrame(
            [
                ["Checkout", "Checkout vereenvoudigen", "Open", "Hoog", "Hoog"],
                ["Snelheid", "Mobiele snelheid verbeteren", "Bezig", "Hoog", "Hoog"],
                ["Productpagina", "Sticky add-to-cart testen", "Open", "Midden", "Hoog"],
                ["Productpagina", "Reviews prominenter maken", "Open", "Midden", "Midden"],
            ],
            columns=["Onderdeel", "Taak", "Status", "Prioriteit", "Impact"],
        )

    status_filter = st.selectbox(
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
            ),
            "Prioriteit": st.column_config.SelectboxColumn(
                "Prioriteit",
                options=["Hoog", "Midden", "Laag"],
            ),
            "Impact": st.column_config.SelectboxColumn(
                "Impact",
                options=["Hoog", "Midden", "Laag"],
            ),
        },
    )

    visible_tasks = st.session_state.tasks.copy()

    if status_filter != "Alle":
        visible_tasks = visible_tasks[visible_tasks["Status"] == status_filter]

    st.dataframe(
        visible_tasks,
        use_container_width=True,
        hide_index=True,
    )


with tab_effect:
    st.subheader("Effectmeting")

    if previous_overview.empty:
        st.info(
            "Kies 7, 30 of 90 dagen om de huidige periode met de vorige periode te vergelijken."
        )
    else:
        effect_df = pd.DataFrame(
            {
                "KPI": [item["label"] for item in KPI_TARGETS.values()],
                "Verschil pp": [
                    kpis[key] - previous_kpis.get(key, 0)
                    for key in KPI_TARGETS.keys()
                ],
            }
        )

        effect_df["Conclusie"] = effect_df["Verschil pp"].apply(
            lambda value: "Verbeterd"
            if value > 0
            else "Gedaald"
            if value < 0
            else "Gelijk"
        )

        fig = px.bar(
            effect_df,
            x="KPI",
            y="Verschil pp",
            color="Conclusie",
            color_discrete_map={
                "Verbeterd": COLORS["light_green"],
                "Gedaald": COLORS["red"],
                "Gelijk": COLORS["gold"],
            },
            title="Huidige periode versus vorige periode",
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="rgba(8,68,34,0.3)",
        )

        st.plotly_chart(
            apply_plotly_layout(fig, 500),
            use_container_width=True,
        )

        display_effect = effect_df.copy()
        display_effect["Verschil pp"] = display_effect["Verschil pp"].map(
            format_delta_pp
        )

        st.dataframe(
            display_effect,
            use_container_width=True,
            hide_index=True,
        )

    if not overview.empty and "date" in overview.columns:
        weekly = overview.copy()
        weekly["week"] = weekly["date"].dt.to_period("W").astype(str)

        weekly = weekly.groupby("week", as_index=False).agg(
            sessies=("sessies", "sum"),
            add_to_carts=("add_to_carts", "sum"),
            checkout_start=("checkout_start", "sum"),
            aankopen=("aankopen", "sum"),
        )

        weekly["add_to_cart_rate"] = weekly.apply(
            lambda row: safe_rate(row["add_to_carts"], row["sessies"]),
            axis=1,
        )

        weekly["checkout_rate"] = weekly.apply(
            lambda row: safe_rate(row["checkout_start"], row["add_to_carts"]),
            axis=1,
        )

        weekly["purchase_rate"] = weekly.apply(
            lambda row: safe_rate(row["aankopen"], row["checkout_start"]),
            axis=1,
        )

        weekly_long = weekly.melt(
            id_vars="week",
            value_vars=["add_to_cart_rate", "checkout_rate", "purchase_rate"],
            var_name="KPI",
            value_name="Percentage",
        )

        fig = px.line(
            weekly_long,
            x="week",
            y="Percentage",
            color="KPI",
            markers=True,
            title="Wekelijkse ontwikkeling",
            color_discrete_sequence=[
                COLORS["green"],
                COLORS["light_green"],
                COLORS["gold"],
            ],
        )

        st.plotly_chart(
            apply_plotly_layout(fig, 520),
            use_container_width=True,
        )


st.caption("Van Duinkerken · Website optimalisatiepilot")
