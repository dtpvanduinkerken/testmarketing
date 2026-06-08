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
    page_title="Members dashboard",
    page_icon="👥",
    layout="wide",
)

SHEET_ID = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"

MEMBER_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=Sheet1"
)

DEALS_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=MemberDeal"
)

MEMBER_STATUS_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=members"
)

SLEEPING_DAYS = 365

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
CARD_BORDER = "rgba(8, 68, 34, 0.07)"

MONTH_MAP = {
    1: "Jan",
    2: "Feb",
    3: "Mrt",
    4: "Apr",
    5: "Mei",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Okt",
    11: "Nov",
    12: "Dec",
}

MONTH_ORDER = list(MONTH_MAP.values())

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
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("/", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )
    return df


def fetch_sheet(url: str) -> pd.DataFrame:
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


@st.cache_data(ttl=3600, show_spinner="Members data laden...")
def load_members() -> pd.DataFrame:
    return fetch_sheet(MEMBER_URL)


@st.cache_data(ttl=3600, show_spinner="Deals data laden...")
def load_deals() -> pd.DataFrame:
    return fetch_sheet(DEALS_URL)


@st.cache_data(ttl=3600, show_spinner="Actieve en slapende members laden...")
def load_member_status() -> pd.DataFrame:
    return fetch_sheet(MEMBER_STATUS_URL)


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


def format_currency(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"€ {value:,.0f}".replace(",", ".")


def parse_currency(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def apply_chart_style(fig, height: int = 400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="sofia-pro",
            color=BRAND_GREEN,
        ),
        margin=dict(l=30, r=30, t=40, b=40),
    )

    return fig


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


# ==========================================================
# DATA CLEANING
# ==========================================================

def clean_members(members: pd.DataFrame) -> pd.DataFrame:
    if members.empty:
        return members

    required_columns = {"member_id", "created_at"}

    if not required_columns.issubset(members.columns):
        st.error("De kolommen `member_id` en `created_at` ontbreken.")
        return pd.DataFrame()

    members = members.dropna(subset=["member_id", "created_at"]).copy()

    members["member_id"] = members["member_id"].astype(str).str.strip()
    members = members[members["member_id"] != ""]

    members["week_label"] = members["created_at"].astype(str).str.strip()

    members["year"] = (
        members["week_label"]
        .str.extract(r"(\d{4})")[0]
        .pipe(pd.to_numeric, errors="coerce")
    )

    members["week"] = (
        members["week_label"]
        .str.extract(r"week\s*(\d+)", flags=0)[0]
        .pipe(pd.to_numeric, errors="coerce")
    )

    members = members.dropna(subset=["year", "week"])
    members["year"] = members["year"].astype(int)
    members["week"] = members["week"].astype(int)

    members = members[
        (members["week"] >= 1)
        & (members["week"] <= 53)
    ]

    members["sort_key"] = members["year"] * 100 + members["week"]

    return members


def clean_deals(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty:
        return deals

    deals = deals.copy()

    if "datum" in deals.columns:
        deals["datum"] = pd.to_datetime(deals["datum"], errors="coerce", dayfirst=True)
        deals["maand"] = deals["datum"].dt.month.map(MONTH_MAP)
        deals["maand_nummer"] = deals["datum"].dt.month
        deals["jaar"] = deals["datum"].dt.year

    if "omzet" in deals.columns:
        deals["omzet"] = parse_currency(deals["omzet"])
    else:
        deals["omzet"] = 0

    for column in ["member_deal", "categorie"]:
        if column in deals.columns:
            deals[column] = deals[column].fillna("Onbekend").astype(str).str.strip()
            deals[column] = deals[column].replace("", "Onbekend")

    return deals


def clean_member_status(member_status: pd.DataFrame) -> pd.DataFrame:
    if member_status.empty:
        return member_status

    required_columns = {"member_id", "eerste_aankoop", "laatste_aankoop"}

    if not required_columns.issubset(member_status.columns):
        st.error(
            "De kolommen `member_ID`, `eerste_aankoop` en `laatste_aankoop` ontbreken "
            "in het tabblad `members`."
        )
        return pd.DataFrame()

    member_status = member_status.copy()

    member_status["member_id"] = member_status["member_id"].astype(str).str.strip()
    member_status = member_status[member_status["member_id"] != ""]
    member_status["eerste_aankoop"] = pd.to_datetime(
        member_status["eerste_aankoop"],
        errors="coerce",
        dayfirst=True,
    )

    member_status["laatste_aankoop"] = pd.to_datetime(
        member_status["laatste_aankoop"],
        errors="coerce",
        dayfirst=True,
    )

    today = pd.Timestamp.today().normalize()

    member_status["dagen_sinds_laatste_aankoop"] = (
        today - member_status["laatste_aankoop"]
    ).dt.days

    member_status["member_status"] = "Actief"

    member_status.loc[
        (
            member_status["eerste_aankoop"].isna()
            | member_status["laatste_aankoop"].isna()
            | (
                member_status["dagen_sinds_laatste_aankoop"]
                > SLEEPING_DAYS
            )
        ),
        "member_status",
    ] = "Slapend"

    return member_status
# ==========================================================
# SIDEBAR
# ==========================================================

def apply_filters(members: pd.DataFrame, deals: pd.DataFrame, member_status: pd.DataFrame):
    st.sidebar.title("👥 Members")
    st.sidebar.caption("Filter dashboarddata")

    if not members.empty:
        years = sorted(members["year"].dropna().unique().tolist())

        selected_years = st.sidebar.multiselect(
            "Jaar members",
            years,
            default=years,
        )

        if selected_years:
            members = members[members["year"].isin(selected_years)]

    if not deals.empty and "member_deal" in deals.columns:
        deal_options = sorted(deals["member_deal"].dropna().unique().tolist())

        selected_deals = st.sidebar.multiselect(
            "Member deals",
            deal_options,
            default=deal_options,
        )

        if selected_deals:
            deals = deals[deals["member_deal"].isin(selected_deals)]

    if not deals.empty and "datum" in deals.columns and deals["datum"].notna().any():
        min_date = deals["datum"].min().date()
        max_date = deals["datum"].max().date()

        selected_dates = st.sidebar.date_input(
            "Periode deals",
            value=(min_date, max_date),
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates

            deals = deals[
                deals["datum"].between(
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date),
                )
            ]

    if not member_status.empty and "member_status" in member_status.columns:
        status_options = sorted(member_status["member_status"].dropna().unique().tolist())

        selected_status = st.sidebar.multiselect(
            "Member status",
            status_options,
            default=status_options,
        )

        if selected_status:
            member_status = member_status[
                member_status["member_status"].isin(selected_status)
            ]

    return members, deals, member_status


# ==========================================================
# RENDER
# ==========================================================

def render_header() -> None:
    col1, _, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(
            '<div class="vdk-main-title">Members dashboard</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d-%m-%Y")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="vdk-divider"></div>', unsafe_allow_html=True)


def render_kpis(weekly: pd.DataFrame, deals: pd.DataFrame, member_status: pd.DataFrame) -> None:
    total_members = int(weekly["Nieuwe members"].sum())
    total_cumulative = int(weekly["Totaal"].iloc[-1])
    current_week = int(weekly.iloc[-1]["Nieuwe members"])

    if len(weekly) >= 2:
        previous_week = int(weekly.iloc[-2]["Nieuwe members"])
        growth_percentage = (
            (current_week - previous_week) / previous_week * 100
            if previous_week > 0
            else 0
        )
    else:
        growth_percentage = 0

    total_revenue = deals["omzet"].sum() if not deals.empty and "omzet" in deals.columns else 0

    active_members = 0
    sleeping_members = 0

    if not member_status.empty and "member_status" in member_status.columns:
        active_members = int((member_status["member_status"] == "Actief").sum())
        sleeping_members = int((member_status["member_status"] == "Slapend").sum())

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    col1.metric("Nieuwe members totaal", format_number(total_members))
    col2.metric(
        "Nieuwe members laatste week",
        format_number(current_week),
        delta=f"{growth_percentage:.1f}%",
    )
    col3.metric("Totaal cumulatief", format_number(total_cumulative))
    col4.metric("Omzet member deals", format_currency(total_revenue))
    col5.metric("Actieve members", format_number(active_members))
    col6.metric("Slapende members", format_number(sleeping_members))


def render_member_charts(weekly: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Inkomende leden en weektrend")

        fig = px.line(
            weekly,
            x="week_label",
            y=["Nieuwe members", "Trend"],
            markers=True,
            color_discrete_sequence=[BRAND_GREEN, "#7d9b88"],
        )

        fig.update_layout(
            showlegend=True,
            xaxis_title="Week",
            yaxis_title="Aantal members",
        )

        st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    with col2:
        st.subheader("Wekelijkse groei")

        growth_df = weekly.copy()
        growth_df["Status"] = growth_df["Groei"].apply(
            lambda value: "Groei" if value >= 0 else "Daling"
        )

        fig = px.bar(
            growth_df,
            x="week_label",
            y="Groei",
            color="Status",
            color_discrete_map={
                "Groei": "#7d9b88",
                "Daling": "#c76f6f",
            },
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color=BRAND_GREEN,
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="Week",
            yaxis_title="Groei",
        )

        st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_member_status(member_status: pd.DataFrame) -> None:
    if member_status.empty:
        st.info("Geen data beschikbaar voor actieve en slapende members.")
        return

    if "member_status" not in member_status.columns:
        st.info("Geen member status beschikbaar.")
        return

    st.subheader("Actieve vs slapende members")

    status_summary = (
        member_status.groupby("member_status")
        .size()
        .reset_index(name="Aantal members")
        .sort_values("Aantal members", ascending=False)
    )

    fig = px.bar(
        status_summary,
        x="member_status",
        y="Aantal members",
        text_auto=True,
        color="member_status",
        color_discrete_map={
            "Actief": "#7d9b88",
            "Slapend": "#c76f6f",
        },
    )

    fig.update_layout(
        xaxis_title="Status",
        yaxis_title="Aantal members",
        showlegend=False,
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)

    with st.expander("Bekijk actieve en slapende members"):
        display_df = member_status.copy()

        display_df["eerste_aankoop"] = display_df["eerste_aankoop"].dt.strftime("%d-%m-%Y")
        display_df["laatste_aankoop"] = display_df["laatste_aankoop"].dt.strftime("%d-%m-%Y")

        display_df = display_df.rename(
            columns={
                "member_id": "member_ID",
                "member_status": "status",
            }
        )

        st.dataframe(
            display_df[
                [
                    "member_ID",
                    "eerste_aankoop",
                    "laatste_aankoop",
                    "dagen_sinds_laatste_aankoop",
                    "status",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )


def render_deal_revenue(deals: pd.DataFrame) -> None:
    if not {"member_deal", "omzet"}.issubset(deals.columns):
        st.info("Geen kolommen `member_deal` en `omzet` gevonden.")
        return

    total_per_deal = (
        deals.groupby("member_deal")["omzet"]
        .agg(
            totale_omzet="sum",
            aantal_transacties="count",
            gemiddelde_omzet="mean",
        )
        .reset_index()
        .sort_values("totale_omzet", ascending=False)
    )

    total_per_deal = total_per_deal[total_per_deal["totale_omzet"] > 0]

    if total_per_deal.empty:
        st.info("Geen omzetdata beschikbaar voor de gekozen filters.")
        return

    st.subheader("Omzet per member deal")

    fig = px.bar(
        total_per_deal,
        x="member_deal",
        y="totale_omzet",
        text_auto=".2s",
        color_discrete_sequence=[BRAND_GREEN],
    )

    fig.update_layout(
        xaxis_title="Member deal",
        yaxis_title="Totale omzet (€)",
        showlegend=False,
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_monthly_deals(deals: pd.DataFrame) -> None:
    required_columns = {"member_deal", "maand", "maand_nummer", "omzet"}

    if not required_columns.issubset(deals.columns):
        st.info("Geen maandelijkse dealdata beschikbaar.")
        return

    monthly_deal_chart = (
        deals.dropna(subset=["maand_nummer"])
        .groupby(["member_deal", "maand", "maand_nummer"])["omzet"]
        .sum()
        .reset_index()
        .sort_values(["maand_nummer", "member_deal"])
    )

    monthly_deal_chart = monthly_deal_chart[monthly_deal_chart["omzet"] > 0]

    if monthly_deal_chart.empty:
        st.info("Geen maandelijkse omzet beschikbaar voor de gekozen filters.")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Maandelijkse trend per deal")

        fig = px.line(
            monthly_deal_chart,
            x="maand",
            y="omzet",
            color="member_deal",
            markers=True,
        )

        fig.update_layout(
            xaxis={
                "categoryorder": "array",
                "categoryarray": MONTH_ORDER,
            },
            xaxis_title="Maand",
            yaxis_title="Omzet (€)",
        )

        st.plotly_chart(apply_chart_style(fig, height=450), use_container_width=True)

    with col2:
        st.subheader("Gestapelde omzet per deal")

        fig = px.bar(
            monthly_deal_chart,
            x="maand",
            y="omzet",
            color="member_deal",
            text_auto=".2s",
        )

        fig.update_layout(
            barmode="stack",
            xaxis={
                "categoryorder": "array",
                "categoryarray": MONTH_ORDER,
            },
            xaxis_title="Maand",
            yaxis_title="Omzet (€)",
        )

        st.plotly_chart(apply_chart_style(fig, height=450), use_container_width=True)


def render_category_revenue(deals: pd.DataFrame) -> None:
    if not {"categorie", "omzet"}.issubset(deals.columns):
        return

    categorie_df = (
        deals.groupby("categorie")["omzet"]
        .sum()
        .reset_index()
        .sort_values("omzet", ascending=False)
    )

    categorie_df = categorie_df[categorie_df["omzet"] > 0]

    if categorie_df.empty:
        return

    st.subheader("Omzetverdeling per categorie")

    fig = px.pie(
        categorie_df,
        names="categorie",
        values="omzet",
        hole=0.55,
        color_discrete_sequence=[
            BRAND_GREEN,
            "#3f6b53",
            "#7d9b88",
            "#b6c5b9",
            "#dfe7df",
        ],
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_tables(weekly: pd.DataFrame, deals: pd.DataFrame) -> None:
    with st.expander("Bekijk weekdata"):
        st.dataframe(
            weekly.drop(columns=["sort_key"], errors="ignore"),
            use_container_width=True,
            hide_index=True,
        )

    if not deals.empty:
        with st.expander("Bekijk deals data"):
            st.dataframe(
                deals,
                use_container_width=True,
                hide_index=True,
            )


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    try:
        members = clean_members(load_members())
        deals = clean_deals(load_deals())
        member_status = clean_member_status(load_member_status())
    except Exception as error:
        st.error(f"Data kon niet geladen worden: {error}")
        return

    members, deals, member_status = apply_filters(members, deals, member_status)

    if members.empty:
        st.error("Geen geldige members data beschikbaar voor de gekozen filters.")
        return

    weekly = prepare_weekly_members(members)

    if weekly.empty:
        st.error("Geen weekdata beschikbaar.")
        return

    render_header()
    render_kpis(weekly, deals, member_status)

    add_space()
    render_member_charts(weekly)

    add_space()
    render_member_status(member_status)

    add_space()

    if deals.empty:
        st.info("Geen deals data beschikbaar voor de gekozen filters.")
    else:
        render_deal_revenue(deals)

        add_space()
        render_monthly_deals(deals)

        add_space()
        render_category_revenue(deals)

    add_space()
    render_tables(weekly, deals)

    st.markdown("---")
    st.caption(
        f"{format_number(len(members))} members records geladen"
        + (
            f" · {format_number(len(deals))} deals records geladen"
            if not deals.empty
            else ""
        )
        + (
            f" · {format_number(len(member_status))} member status records geladen"
            if not member_status.empty
            else ""
        )
    )


if __name__ == "__main__":
    main()
