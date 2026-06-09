import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st

# ==========================================================
# CONFIG
# ==========================================================

st.set_page_config(
    page_title="Verenigingsdashboard",
    page_icon="📊",
    layout="wide",
)

SHEET_ID = "1v0IVTJkUwkwDUHL2m75dpj0A9WofxJyQ-u0nLHeMyXo"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"

# ==========================================================
# STYLING
# ==========================================================

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

section[data-testid="stSidebar"] {{
    background: white;
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

.vdk-date {{
    text-align: right;
    color: {TEXT_MUTED};
    font-size: 14px;
    margin-top: 16px;
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
    font-size: 30px;
    font-weight: 700;
}}

div[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {{
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid {CARD_BORDER};
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
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

# ==========================================================
# HELPERS
# ==========================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df.columns = df.columns.str.strip()
    return df


def fetch_csv(url: str) -> pd.DataFrame:
    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv, */*;q=0.1",
        },
        timeout=20,
    )
    response.raise_for_status()

    return normalize_columns(pd.read_csv(io.StringIO(response.text)))


@st.cache_data(ttl=3600, show_spinner="Verenigingsdata laden...")
def load_data() -> pd.DataFrame:
    return fetch_csv(CSV_URL)


def parse_number(series: pd.Series) -> pd.Series:
    def parse_value(value):
        if pd.isna(value):
            return 0

        if isinstance(value, (int, float)):
            return float(value)

        value = str(value).strip()
        value = value.replace("€", "").replace(" ", "")

        if value == "":
            return 0

        if "." in value and "," in value:
            value = value.replace(".", "").replace(",", ".")
        elif "," in value:
            value = value.replace(",", ".")

        return pd.to_numeric(value, errors="coerce")

    return series.apply(parse_value).fillna(0)


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:,.0f}".replace(",", ".")


def format_currency(value: float | int) -> str:
    if pd.isna(value):
        return "-"
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def format_decimal(value: float | int) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.2f}".replace(".", ",")


def apply_chart_style(fig, height: int = 400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="sofia-pro",
            color=BRAND_GREEN,
        ),
        margin=dict(l=30, r=30, t=45, b=40),
    )
    return fig


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


# ==========================================================
# DATA CLEANING
# ==========================================================

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    required_columns = {"Datum", "Vereniging", "Members", "Omzet", "Orders"}

    if not required_columns.issubset(df.columns):
        missing = required_columns - set(df.columns)
        st.error(f"Deze kolommen ontbreken in de sheet: {', '.join(missing)}")
        return pd.DataFrame()

    df = df.copy()

    df["Datum"] = pd.to_datetime(df["Datum"], errors="coerce", dayfirst=True)
    df["Vereniging"] = df["Vereniging"].fillna("Onbekend").astype(str).str.strip()
    df["Vereniging"] = df["Vereniging"].replace("", "Onbekend")

    df["Members"] = parse_number(df["Members"])
    df["Omzet"] = parse_number(df["Omzet"])
    df["Orders"] = parse_number(df["Orders"])

    df = df.dropna(subset=["Datum"])
    df = df.sort_values(["Vereniging", "Datum"])

    return df


# ==========================================================
# FILTERS
# ==========================================================

def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.title("📊 Verenigingen")
    st.sidebar.caption("Filter dashboarddata")

    filtered = df.copy()

    verenigingen = sorted(filtered["Vereniging"].dropna().unique().tolist())

    selected_verenigingen = st.sidebar.multiselect(
        "Vereniging",
        options=verenigingen,
        default=verenigingen,
    )

    if selected_verenigingen:
        filtered = filtered[filtered["Vereniging"].isin(selected_verenigingen)]

    if not filtered.empty:
        min_date = filtered["Datum"].min().date()
        max_date = filtered["Datum"].max().date()

        selected_dates = st.sidebar.date_input(
            "Periode",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date,
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates

            filtered = filtered[
                filtered["Datum"].between(
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date),
                )
            ]

    return filtered


# ==========================================================
# PREPARE DATA
# ==========================================================

def prepare_vereniging_summary(df: pd.DataFrame) -> pd.DataFrame:
    summary = (
        df.sort_values(["Vereniging", "Datum"])
        .groupby("Vereniging", as_index=False)
        .tail(1)
        .copy()
        .sort_values("Members", ascending=False)
    )

    summary["Omzet per member"] = summary.apply(
        lambda row: row["Omzet"] / row["Members"] if row["Members"] > 0 else 0,
        axis=1,
    )

    summary["Orders per member"] = summary.apply(
        lambda row: row["Orders"] / row["Members"] if row["Members"] > 0 else 0,
        axis=1,
    )

    return summary


def prepare_monthly_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values(["Vereniging", "Datum"]).copy()
    df["Maand"] = df["Datum"].dt.to_period("M")

    latest_per_vereniging_per_month = (
        df.groupby(["Maand", "Vereniging"], as_index=False)
        .tail(1)
        .copy()
    )

    monthly = (
        latest_per_vereniging_per_month
        .groupby("Maand")
        .agg(
            Members=("Members", "sum"),
            Omzet=("Omzet", "sum"),
            Orders=("Orders", "sum"),
        )
        .reset_index()
    )

    monthly["Datum"] = monthly["Maand"].dt.to_timestamp()
    monthly = monthly.sort_values("Datum")

    return monthly


# ==========================================================
# RENDER
# ==========================================================

def render_header() -> None:
    col1, _, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(
            '<div class="vdk-main-title">Verenigingsdashboard</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d-%m-%Y")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="vdk-divider"></div>', unsafe_allow_html=True)


def render_kpis(summary: pd.DataFrame) -> None:
    total_members = summary["Members"].sum()
    total_omzet = summary["Omzet"].sum()
    total_orders = summary["Orders"].sum()

    omzet_per_member = total_omzet / total_members if total_members > 0 else 0
    orders_per_member = total_orders / total_members if total_members > 0 else 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Members totaal", format_number(total_members))
    col2.metric("Omzet totaal", format_currency(total_omzet))
    col3.metric("Orders totaal", format_number(total_orders))
    col4.metric("Omzet per member", format_currency(omzet_per_member))
    col5.metric("Orders per member", format_decimal(orders_per_member))


def render_members_per_vereniging(summary: pd.DataFrame) -> None:
    st.subheader("Members per vereniging")

    members_df = (
        summary[["Vereniging", "Members"]]
        .copy()
        .sort_values("Members", ascending=False)
    )

    fig = px.bar(
        members_df,
        x="Members",
        y="Vereniging",
        orientation="h",
        text="Members",
        color_discrete_sequence=[BRAND_GREEN],
    )

    fig.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
    )

    fig.update_layout(
        xaxis_title="Aantal members",
        yaxis_title="Vereniging",
        showlegend=False,
        yaxis=dict(autorange="reversed"),
    )

    st.plotly_chart(
        apply_chart_style(fig, height=600),
        use_container_width=True,
    )


def render_monthly_charts(monthly: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Members totaal per maand")

        fig = px.line(
            monthly,
            x="Datum",
            y="Members",
            markers=True,
            color_discrete_sequence=[BRAND_GREEN],
        )

        fig.update_layout(
            xaxis_title="Maand",
            yaxis_title="Members totaal",
            showlegend=False,
        )

        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    with col2:
        st.subheader("Omzet totaal per maand")

        fig = px.bar(
            monthly,
            x="Datum",
            y="Omzet",
            text_auto=".2s",
            color_discrete_sequence=[BRAND_GREEN],
        )

        fig.update_layout(
            xaxis_title="Maand",
            yaxis_title="Omzet totaal (€)",
            showlegend=False,
        )

        st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_vereniging_charts(summary: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Omzet per vereniging")

        omzet_df = summary.sort_values("Omzet", ascending=False)

        fig = px.bar(
            omzet_df,
            x="Vereniging",
            y="Omzet",
            text_auto=".2s",
            color_discrete_sequence=[BRAND_GREEN],
        )

        fig.update_layout(
            xaxis_title="Vereniging",
            yaxis_title="Omzet (€)",
            showlegend=False,
        )

        st.plotly_chart(apply_chart_style(fig, height=450), use_container_width=True)

    with col2:
        st.subheader("Orders per vereniging")

        orders_df = summary.sort_values("Orders", ascending=False)

        fig = px.bar(
            orders_df,
            x="Vereniging",
            y="Orders",
            text_auto=True,
            color_discrete_sequence=["#7d9b88"],
        )

        fig.update_layout(
            xaxis_title="Vereniging",
            yaxis_title="Orders",
            showlegend=False,
        )

        st.plotly_chart(apply_chart_style(fig, height=450), use_container_width=True)


def render_tables(summary: pd.DataFrame, filtered: pd.DataFrame) -> None:
    st.subheader("Overzicht per vereniging")

    display_summary = summary.copy()
    display_summary["Datum"] = display_summary["Datum"].dt.strftime("%d-%m-%Y")
    display_summary["Members"] = display_summary["Members"].map(format_number)
    display_summary["Omzet"] = display_summary["Omzet"].map(format_currency)
    display_summary["Orders"] = display_summary["Orders"].map(format_number)
    display_summary["Omzet per member"] = display_summary["Omzet per member"].map(format_currency)
    display_summary["Orders per member"] = display_summary["Orders per member"].map(format_decimal)

    st.dataframe(
        display_summary[
            [
                "Datum",
                "Vereniging",
                "Members",
                "Omzet",
                "Orders",
                "Omzet per member",
                "Orders per member",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    with st.expander("Bekijk ruwe data"):
        raw_df = filtered.copy()
        raw_df["Datum"] = raw_df["Datum"].dt.strftime("%d-%m-%Y")

        st.dataframe(
            raw_df,
            use_container_width=True,
            hide_index=True,
        )


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    try:
        df = clean_data(load_data())
    except Exception as error:
        st.error(f"Data kon niet geladen worden: {error}")
        return

    if df.empty:
        st.error("Geen geldige data beschikbaar.")
        return

    filtered = apply_filters(df)

    if filtered.empty:
        st.warning("Geen data beschikbaar voor de gekozen filters.")
        return

    vereniging_summary = prepare_vereniging_summary(filtered)
    monthly = prepare_monthly_data(filtered)

    render_header()
    render_kpis(vereniging_summary)

    add_space()
    render_members_per_vereniging(vereniging_summary)

    add_space()
    render_monthly_charts(monthly)

    add_space()
    render_vereniging_charts(vereniging_summary)

    add_space()
    render_tables(vereniging_summary, filtered)

    st.markdown("---")
    st.caption(
        f"{format_number(len(filtered))} records geladen "
        f"· {format_number(vereniging_summary['Vereniging'].nunique())} verenigingen"
    )


if __name__ == "__main__":
    main()
