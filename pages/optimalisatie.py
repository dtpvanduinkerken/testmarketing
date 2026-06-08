from __future__ import annotations

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ============================================================
# CONFIG
# ============================================================

st.set_page_config(
    page_title="Pilotmonitor Website Optimalisatie",
    page_icon="📈",
    layout="wide",
)

PILOT_START = pd.Timestamp("2026-05-28")
PILOT_END = pd.Timestamp("2026-06-28")

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
    "white": "#ffffff",
}

KPI_CONFIG = {
    "add_to_cart_rate": {
        "label": "Add-to-cart",
        "target": 6.0,
        "baseline_key": "add_to_cart_rate",
    },
    "checkout_rate": {
        "label": "Checkout start",
        "target": 50.0,
        "baseline_key": "checkout_rate",
    },
    "purchase_rate": {
        "label": "Aankoopratio",
        "target": 60.0,
        "baseline_key": "purchase_rate",
    },
}

NUMERIC_OVERVIEW_COLS = [
    "omzet",
    "orders",
    "bezoekers",
    "sessies",
    "conversie",
    "add_to_carts",
    "checkout_start",
    "aankopen",
    "gemiddelde_orderwaarde",
]

# ============================================================
# STYLE
# ============================================================

st.markdown(
    f"""
<style>
html, body, [data-testid="stAppViewContainer"] {{
    background: {COLORS["background"]};
    color: {COLORS["green"]};
}}

.block-container {{
    max-width: 1500px;
    padding: 32px 42px;
}}

section[data-testid="stSidebar"] {{
    background: white;
}}

#MainMenu, footer, header {{
    visibility: hidden;
}}

.dashboard-title {{
    font-size: 42px;
    font-weight: 800;
    color: {COLORS["green"]};
    margin-bottom: 4px;
}}

.dashboard-subtitle {{
    color: {COLORS["muted"]};
    font-size: 15px;
    margin-bottom: 12px;
}}

.summary-card {{
    background: white;
    border-radius: 18px;
    padding: 22px;
    border: 1px solid rgba(8,68,34,.08);
    box-shadow: 0 6px 18px rgba(8,68,34,.04);
    min-height: 135px;
}}

.summary-card h3 {{
    margin: 0 0 10px 0;
    font-size: 18px;
}}

.summary-card p {{
    margin: 0;
    color: {COLORS["muted"]};
    line-height: 1.5;
}}

div[data-testid="stMetric"] {{
    background: white;
    border-radius: 18px;
    padding: 18px;
    border: 1px solid rgba(8,68,34,.08);
    box-shadow: 0 6px 18px rgba(8,68,34,.03);
}}
</style>
""",
    unsafe_allow_html=True,
)

# ============================================================
# HELPERS
# ============================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df.columns = (
        df.columns.str.lower()
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def parse_number(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def safe_sum(df: pd.DataFrame, column: str) -> float:
    return float(df[column].sum()) if column in df.columns else 0.0


def safe_rate(numerator: float, denominator: float) -> float:
    return numerator / denominator * 100 if denominator > 0 else 0.0


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def format_number(value: float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float) -> str:
    return f"€ {format_number(value)}"


def format_delta_pp(value: float) -> str:
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.1f} pp".replace(".", ",")


def apply_chart_style(fig, height: int = 420):
    fig.update_layout(
        height=height,
        paper_bgcolor=COLORS["white"],
        plot_bgcolor=COLORS["white"],
        font=dict(color=COLORS["green"]),
        margin=dict(l=30, r=30, t=40, b=40),
    )
    return fig


def goal_progress(baseline: float, current: float, target: float) -> float:
    if target == baseline:
        return 100.0 if current >= target else 0.0

    progress = (current - baseline) / (target - baseline) * 100
    return max(0.0, min(progress, 100.0))


def get_pilot_progress() -> float:
    today = min(pd.Timestamp.today().normalize(), PILOT_END)

    if today < PILOT_START:
        return 0.0

    total_days = max((PILOT_END - PILOT_START).days, 1)
    progress = (today - PILOT_START).days / total_days

    return max(0.0, min(progress, 1.0))


# ============================================================
# DATA
# ============================================================

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


def clean_overview(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "date" not in df.columns:
        st.error("Kolom `date` ontbreekt in overview_kpis.")
        return pd.DataFrame()

    for col in NUMERIC_OVERVIEW_COLS:
        df[col] = parse_number(df[col]) if col in df.columns else 0

    df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)

    return df.dropna(subset=["date"]).sort_values("date")


def clean_funnel(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.rename(columns={"stap": "Stap", "aantal": "Aantal"}).copy()

    if not {"Stap", "Aantal"}.issubset(df.columns):
        return pd.DataFrame()

    df["Aantal"] = parse_number(df["Aantal"])

    return df[df["Aantal"] > 0]


def clean_pagespeed(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.rename(columns={"pagina": "page"}).copy()

    for col in ["mobile_speed", "desktop_speed"]:
        df[col] = parse_number(df[col]) if col in df.columns else 0

    if "page" not in df.columns:
        df["page"] = "Onbekend"

    return df


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


def add_rate_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df["add_to_cart_rate"] = df.apply(
        lambda row: safe_rate(row["add_to_carts"], row["sessies"]),
        axis=1,
    )

    df["checkout_rate"] = df.apply(
        lambda row: safe_rate(row["checkout_start"], row["add_to_carts"]),
        axis=1,
    )

    df["purchase_rate"] = df.apply(
        lambda row: safe_rate(row["aankopen"], row["checkout_start"]),
        axis=1,
    )

    return df


def build_comparison_df(
    baseline_kpis: dict[str, float],
    pilot_kpis: dict[str, float],
) -> pd.DataFrame:
    rows = []

    for key, config in KPI_CONFIG.items():
        rows.append(
            {
                "KPI": config["label"],
                "Voor pilot": baseline_kpis[key],
                "Nu": pilot_kpis[key],
                "Doel": config["target"],
                "Verschil": pilot_kpis[key] - baseline_kpis[key],
            }
        )

    return pd.DataFrame(rows)


# ============================================================
# SIDEBAR
# ============================================================

def render_sidebar(overview: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("📈 Pilotmonitor")
    st.sidebar.caption("Filter de meetperiode")

    if overview.empty or "date" not in overview.columns:
        return overview

    min_date = overview["date"].min().date()
    max_date = overview["date"].max().date()

    selected_dates = st.sidebar.date_input(
        "Periode",
        value=(min_date, max_date),
    )

    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates

        overview = overview[
            overview["date"].between(
                pd.Timestamp(start_date),
                pd.Timestamp(end_date),
            )
        ]

    return overview


# ============================================================
# RENDER
# ============================================================

def render_header() -> None:
    pilot_progress = get_pilot_progress()

    today = min(pd.Timestamp.today().normalize(), PILOT_END)
    current_day = max((today - PILOT_START).days + 1, 0)
    total_days = (PILOT_END - PILOT_START).days + 1

    st.markdown(
        """
        <div class="dashboard-title">
            Pilotmonitor Website Optimalisatie
        </div>
        <div class="dashboard-subtitle">
            Voor pilot → Huidige situatie → Doel 28 juni
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.progress(pilot_progress)

    st.caption(
        f"Pilotperiode: 28 mei 2026 t/m 28 juni 2026 "
        f"• Dag {current_day} van {total_days}"
    )


def get_status(pilot_kpis: dict[str, float]) -> tuple[str, str]:
    achieved = sum(
        1
        for key, config in KPI_CONFIG.items()
        if pilot_kpis[key] >= config["target"]
    )

    if achieved == 3:
        return "🟢 Pilot op koers", "Alle KPI-doelen zijn gehaald."

    if achieved == 2:
        return "🟡 Pilot ontwikkelt positief", "Meerdere KPI's liggen op schema."

    return "🔴 Aandacht nodig", "Meerdere KPI's liggen onder doel."


def render_summary_cards(pilot_kpis: dict[str, float]) -> None:
    status_title, status_text = get_status(pilot_kpis)

    aov = (
        pilot_kpis["revenue"] / pilot_kpis["purchases"]
        if pilot_kpis["purchases"] > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="summary-card">
                <h3>{status_title}</h3>
                <p>{status_text}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    col2.metric("Pilotomzet", format_currency(pilot_kpis["revenue"]))
    col3.metric("Orders", format_number(pilot_kpis["purchases"]))
    col4.metric("Gem. orderwaarde", format_currency(aov))


def render_kpi_cards(
    baseline_kpis: dict[str, float],
    pilot_kpis: dict[str, float],
) -> None:
    metric_cols = st.columns(3)

    for col, (key, config) in zip(metric_cols, KPI_CONFIG.items()):
        baseline = baseline_kpis[key]
        current = pilot_kpis[key]
        target = config["target"]
        progress = goal_progress(baseline, current, target)

        with col:
            st.metric(
                config["label"],
                format_percent(current),
                format_delta_pp(current - baseline),
            )

            st.progress(progress / 100)

            st.caption(f"Voor pilot: {format_percent(baseline)}")
            st.caption(f"Doel: {format_percent(target)}")


def render_summary_tab(comparison_df: pd.DataFrame) -> None:
    chart_df = comparison_df.melt(
        id_vars="KPI",
        value_vars=["Voor pilot", "Nu", "Doel"],
        var_name="Type",
        value_name="Percentage",
    )

    fig = px.bar(
        chart_df,
        x="KPI",
        y="Percentage",
        color="Type",
        barmode="group",
        color_discrete_sequence=[
            COLORS["muted"],
            COLORS["green"],
            COLORS["gold"],
        ],
    )

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Percentage",
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    st.dataframe(
        comparison_df[["KPI", "Voor pilot", "Nu", "Doel"]],
        use_container_width=True,
        hide_index=True,
    )


def render_impact_tab(comparison_df: pd.DataFrame) -> None:
    impact_df = comparison_df.copy()
    impact_df["Status"] = impact_df["Verschil"].apply(
        lambda value: "Verbetering" if value >= 0 else "Daling"
    )

    fig = px.bar(
        impact_df,
        x="KPI",
        y="Verschil",
        color="Status",
        color_discrete_map={
            "Verbetering": COLORS["light_green"],
            "Daling": COLORS["red"],
        },
    )

    fig.add_hline(y=0, line_dash="dash", line_color=COLORS["green"])

    fig.update_layout(
        xaxis_title="",
        yaxis_title="Verschil in procentpunten",
        showlegend=False,
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    st.dataframe(
        impact_df,
        use_container_width=True,
        hide_index=True,
    )


def render_funnel_tab(funnel: pd.DataFrame) -> None:
    st.subheader("Conversiefunnel")

    if funnel.empty:
        st.info("Geen funneldata beschikbaar.")
        return

    fig = px.funnel(
        funnel,
        x="Aantal",
        y="Stap",
        color_discrete_sequence=[COLORS["green"]],
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    st.dataframe(
        funnel,
        use_container_width=True,
        hide_index=True,
    )


def render_speed_tab(pagespeed: pd.DataFrame) -> None:
    st.subheader("Pagespeed")

    if pagespeed.empty:
        st.info("Geen pagespeeddata beschikbaar.")
        return

    metric = st.radio(
        "Toon score",
        ["mobile_speed", "desktop_speed"],
        horizontal=True,
        format_func=lambda value: "Mobiel" if value == "mobile_speed" else "Desktop",
    )

    fig = px.bar(
        pagespeed.sort_values(metric),
        x=metric,
        y="page",
        orientation="h",
        color=metric,
        color_continuous_scale=["#c76f6f", "#c9a646", "#7d9b88"],
    )

    fig.update_layout(
        xaxis_title="Score",
        yaxis_title="Pagina",
        coloraxis_showscale=False,
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    st.dataframe(
        pagespeed,
        use_container_width=True,
        hide_index=True,
    )


def render_actions_tab() -> None:
    default_tasks = pd.DataFrame(
        [
            ["Checkout", "Checkout vereenvoudigen", "Open", "Hoog"],
            ["Snelheid", "Mobiele snelheid verbeteren", "Bezig", "Hoog"],
            ["Product", "Sticky add-to-cart testen", "Open", "Hoog"],
        ],
        columns=["Onderdeel", "Taak", "Status", "Prioriteit"],
    )

    if "tasks" not in st.session_state:
        st.session_state.tasks = default_tasks

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
                options=["Laag", "Middel", "Hoog"],
            ),
        },
    )


def render_trend_tab(overview: pd.DataFrame) -> None:
    if overview.empty:
        st.info("Geen trenddata beschikbaar.")
        return

    trend_df = add_rate_columns(overview)

    trend_long = trend_df.melt(
        id_vars="date",
        value_vars=[
            "add_to_cart_rate",
            "checkout_rate",
            "purchase_rate",
        ],
        var_name="KPI",
        value_name="Percentage",
    )

    label_map = {
        "add_to_cart_rate": "Add-to-cart",
        "checkout_rate": "Checkout start",
        "purchase_rate": "Aankoopratio",
    }

    trend_long["KPI"] = trend_long["KPI"].map(label_map)

    fig = px.line(
        trend_long,
        x="date",
        y="Percentage",
        color="KPI",
        markers=True,
        color_discrete_sequence=[
            COLORS["green"],
            COLORS["gold"],
            COLORS["light_green"],
        ],
    )

    fig.add_vline(
        x=PILOT_START,
        line_dash="dash",
        line_color=COLORS["red"],
    )

    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Percentage",
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_raw_data(
    overview: pd.DataFrame,
    funnel: pd.DataFrame,
    pagespeed: pd.DataFrame,
) -> None:
    with st.expander("Bekijk ruwe data"):
        st.write("Overview KPI's")
        st.dataframe(overview, use_container_width=True, hide_index=True)

        st.write("Funnel")
        st.dataframe(funnel, use_container_width=True, hide_index=True)

        st.write("Pagespeed")
        st.dataframe(pagespeed, use_container_width=True, hide_index=True)


# ============================================================
# MAIN
# ============================================================

def main() -> None:
    with st.spinner("Dashboard laden..."):
        try:
            overview = clean_overview(load_sheet(SHEET_URLS["overview"]))
            funnel = clean_funnel(load_sheet(SHEET_URLS["funnel"]))
            pagespeed = clean_pagespeed(load_sheet(SHEET_URLS["pagespeed"]))
        except Exception as error:
            st.error(f"Data kon niet geladen worden: {error}")
            return

    overview = render_sidebar(overview)

    if overview.empty:
        st.error("Geen geldige overview-data beschikbaar.")
        return

    baseline_df = overview[overview["date"] < PILOT_START]
    pilot_df = overview[overview["date"] >= PILOT_START]

    baseline_kpis = calculate_kpis(baseline_df)
    pilot_kpis = calculate_kpis(pilot_df)
    comparison_df = build_comparison_df(baseline_kpis, pilot_kpis)

    render_header()
    render_summary_cards(pilot_kpis)

    st.divider()

    render_kpi_cards(baseline_kpis, pilot_kpis)

    st.divider()

    tab_summary, tab_impact, tab_funnel, tab_speed, tab_actions, tab_trend = st.tabs(
        [
            "Pilot Samenvatting",
            "Pilot Impact",
            "Funnel",
            "Snelheid",
            "Acties",
            "Trend",
        ]
    )

    with tab_summary:
        render_summary_tab(comparison_df)

    with tab_impact:
        render_impact_tab(comparison_df)

    with tab_funnel:
        render_funnel_tab(funnel)

    with tab_speed:
        render_speed_tab(pagespeed)

    with tab_actions:
        render_actions_tab()

    with tab_trend:
        render_trend_tab(overview)

    render_raw_data(overview, funnel, pagespeed)

    st.caption("Van Duinkerken · Website optimalisatiepilot")


if __name__ == "__main__":
    main()
