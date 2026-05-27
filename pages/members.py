import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(page_title="Members", layout="wide")


STYLE = """
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #f7f3ec;
    font-family: 'sofia-pro', sans-serif;
    color: #084422;
}

.block-container {
    padding: 42px 56px 56px 56px;
    max-width: 1500px;
}

#MainMenu,
footer,
header {
    visibility: hidden;
}

.vdk-main-title {
    font-size: 42px;
    font-weight: 700;
    color: #084422;
    margin: 0;
    line-height: 1.15;
}

.vdk-date {
    text-align: right;
    color: #6f766f;
    font-size: 14px;
    margin-top: 16px;
}

.vdk-divider {
    width: 100%;
    height: 1px;
    background: rgba(8, 68, 34, 0.08);
    margin-top: 24px;
    margin-bottom: 34px;
}

[data-testid="stMetric"] {
    background: #ffffff;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}

[data-testid="stMetric"] label {
    color: #6f766f !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}

[data-testid="stMetricValue"] {
    color: #084422;
    font-size: 30px;
    font-weight: 700;
}

[data-testid="stMetricDelta"] {
    font-size: 14px;
    font-weight: 600;
}

div[data-testid="stPlotlyChart"],
[data-testid="stDataFrame"] {
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}

h1, h2, h3, h4 {
    color: #084422;
}

h3 {
    font-size: 20px;
    font-weight: 700;
}

.space {
    height: 34px;
}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)


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

MONTH_ORDER = [
    "Jan",
    "Feb",
    "Mrt",
    "Apr",
    "Mei",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Okt",
    "Nov",
    "Dec",
]

SHEET_ID = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"

MEMBER_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=Sheet1"
)

DEALS_URL = (
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
    "/gviz/tq?tqx=out:csv&sheet=MemberDeal"
)


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )

    return df


def fetch_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "text/csv, */*;q=0.1",
            },
            timeout=15,
        )

        response.raise_for_status()

        return normalize_columns(
            pd.read_csv(io.StringIO(response.text))
        )

    except requests.RequestException as error:
        st.error(f"Kan data niet laden: {error}")
        return pd.DataFrame()

    except Exception as error:
        st.error(f"Onverwachte fout: {error}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_members() -> pd.DataFrame:
    return fetch_sheet(MEMBER_URL)


@st.cache_data(ttl=3600)
def load_deals() -> pd.DataFrame:
    return fetch_sheet(DEALS_URL)


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


def clean_members(members: pd.DataFrame) -> pd.DataFrame:
    if members.empty:
        return members

    required_columns = {"member_id", "created_at"}

    if not required_columns.issubset(members.columns):
        st.error("De kolommen `member_id` en `created_at` ontbreken.")
        return pd.DataFrame()

    members = members.dropna(subset=["member_id", "created_at"]).copy()

    members["week_label"] = members["created_at"].astype(str)
    members["year"] = (
        members["week_label"]
        .str.extract(r"(\d{4})")[0]
        .astype(float)
    )

    members["week"] = (
        members["week_label"]
        .str.extract(r"week (\d+)")[0]
        .astype(float)
    )

    members = members.dropna(subset=["year", "week"])

    members["year"] = members["year"].astype(int)
    members["week"] = members["week"].astype(int)

    return members


def prepare_weekly_members(members: pd.DataFrame) -> pd.DataFrame:
    weekly = (
        members
        .groupby(["year", "week", "week_label"])
        .size()
        .reset_index(name="Nieuwe members")
        .sort_values(["year", "week"])
    )

    weekly["Groei"] = weekly["Nieuwe members"].diff().fillna(0)
    weekly["Trend"] = weekly["Nieuwe members"].rolling(3).mean()
    weekly["Totaal"] = weekly["Nieuwe members"].cumsum()

    return weekly


def clean_deals(deals: pd.DataFrame) -> pd.DataFrame:
    if deals.empty:
        return deals

    deals = deals.copy()

    if "datum" in deals.columns:
        deals["datum"] = pd.to_datetime(deals["datum"], errors="coerce")
        deals["maand"] = deals["datum"].dt.month.map(MONTH_MAP)
        deals["maand_nummer"] = deals["datum"].dt.month

    if "omzet" in deals.columns:
        deals["omzet"] = pd.to_numeric(
            deals["omzet"].astype(str).str.replace(",", ".", regex=False),
            errors="coerce",
        ).fillna(0)

    return deals


def apply_chart_style(fig, height: int = 400):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="sofia-pro",
            color="#084422",
        ),
        title_font_size=20,
        margin=dict(l=30, r=30, t=60, b=40),
    )

    return fig


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


def render_kpis(weekly: pd.DataFrame) -> None:
    total_members = int(weekly["Nieuwe members"].sum())
    total_cumulative = int(weekly["Totaal"].iloc[-1])

    if len(weekly) >= 2:
        previous_week = int(weekly.iloc[-2]["Nieuwe members"])
        current_week = int(weekly.iloc[-1]["Nieuwe members"])

        growth_percentage = (
            ((current_week - previous_week) / previous_week * 100)
            if previous_week > 0
            else 0
        )
    else:
        current_week = int(weekly.iloc[-1]["Nieuwe members"])
        growth_percentage = 0

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Nieuwe members totaal",
        format_number(total_members),
    )

    col2.metric(
        "Nieuwe members laatste week",
        format_number(current_week),
        delta=f"{growth_percentage:.1f}%",
        delta_color="normal" if growth_percentage >= 0 else "inverse",
    )

    col3.metric(
        "Totaal cumulatief",
        format_number(total_cumulative),
    )


def render_member_charts(weekly: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Inkomende leden en weektrend")

        fig = px.line(
            weekly,
            x="week_label",
            y=["Nieuwe members", "Trend"],
            markers=True,
            color_discrete_sequence=["#084422", "#7d9b88"],
        )

        fig.update_layout(
            showlegend=True,
            xaxis_title="Week",
            yaxis_title="Aantal members",
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True,
        )

    with col2:
        st.subheader("Wekelijkse groei")

        growth_df = weekly.copy()
        growth_df["kleur"] = growth_df["Groei"].apply(
            lambda value: "Groei" if value >= 0 else "Daling"
        )

        fig = px.bar(
            growth_df,
            x="week_label",
            y="Groei",
            color="kleur",
            color_discrete_map={
                "Groei": "#7d9b88",
                "Daling": "#c76f6f",
            },
        )

        fig.add_hline(
            y=0,
            line_dash="dash",
            line_color="#084422",
        )

        fig.update_layout(
            showlegend=False,
            xaxis_title="Week",
            yaxis_title="Groei",
        )

        st.plotly_chart(
            apply_chart_style(fig),
            use_container_width=True,
        )


def render_deal_revenue(deals: pd.DataFrame) -> None:
    if not {"member_deal", "omzet"}.issubset(deals.columns):
        return

    total_per_deal = (
        deals
        .groupby("member_deal")["omzet"]
        .agg(["sum", "count", "mean"])
        .reset_index()
        .rename(
            columns={
                "sum": "totale_omzet",
                "count": "aantal_transacties",
                "mean": "gemiddelde_omzet",
            }
        )
        .sort_values("totale_omzet", ascending=False)
    )

    total_per_deal = total_per_deal[
        total_per_deal["totale_omzet"] > 0
    ]

    if total_per_deal.empty:
        return

    st.subheader("Omzet per member deal")

    fig = px.bar(
        total_per_deal,
        x="member_deal",
        y="totale_omzet",
        text_auto=".2s",
        color_discrete_sequence=["#084422"],
    )

    fig.update_layout(
        xaxis_title="Member deal",
        yaxis_title="Totale omzet (€)",
        showlegend=False,
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True,
    )


def render_monthly_deals(deals: pd.DataFrame) -> None:
    required_columns = {
        "member_deal",
        "maand",
        "maand_nummer",
        "omzet",
    }

    if not required_columns.issubset(deals.columns):
        return

    monthly_deal_chart = (
        deals
        .groupby(["member_deal", "maand", "maand_nummer"])["omzet"]
        .sum()
        .reset_index()
        .sort_values(["maand_nummer", "member_deal"])
    )

    monthly_deal_chart = monthly_deal_chart[
        monthly_deal_chart["omzet"] > 0
    ]

    if monthly_deal_chart.empty:
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
            yaxis_title="Omzet (€)",
        )

        st.plotly_chart(
            apply_chart_style(fig, height=450),
            use_container_width=True,
        )

    with col2:
        st.subheader("Gestapelde omzet per deal")

        pivot_chart = (
            monthly_deal_chart
            .pivot(
                index="maand",
                columns="member_deal",
                values="omzet",
            )
            .fillna(0)
            .reset_index()
        )

        pivot_chart["maand_nummer"] = pivot_chart["maand"].map(
            {month: number for number, month in MONTH_MAP.items()}
        )

        pivot_chart = pivot_chart.sort_values("maand_nummer")

        value_columns = [
            column
            for column in pivot_chart.columns
            if column not in ["maand", "maand_nummer"]
        ]

        fig = px.bar(
            pivot_chart,
            x="maand",
            y=value_columns,
            text_auto=".2s",
        )

        fig.update_layout(
            barmode="stack",
            xaxis={
                "categoryorder": "array",
                "categoryarray": MONTH_ORDER,
            },
            yaxis_title="Omzet (€)",
        )

        st.plotly_chart(
            apply_chart_style(fig, height=450),
            use_container_width=True,
        )


def render_category_revenue(deals: pd.DataFrame) -> None:
    if not {"categorie", "omzet"}.issubset(deals.columns):
        return

    categorie_df = (
        deals
        .groupby("categorie")["omzet"]
        .sum()
        .reset_index()
    )

    if categorie_df.empty:
        return

    st.subheader("Omzetverdeling per categorie")

    fig = px.pie(
        categorie_df,
        names="categorie",
        values="omzet",
        hole=0.55,
        color_discrete_sequence=[
            "#084422",
            "#3f6b53",
            "#7d9b88",
            "#b6c5b9",
            "#dfe7df",
        ],
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


def main() -> None:
    members = clean_members(load_members())
    deals = clean_deals(load_deals())

    if members.empty:
        st.error("Geen geldige members data beschikbaar.")
        return

    weekly = prepare_weekly_members(members)

    if weekly.empty:
        st.error("Geen weekdata beschikbaar.")
        return

    render_header()
    render_kpis(weekly)

    add_space()
    render_member_charts(weekly)

    if deals.empty:
        st.info("Geen deals data beschikbaar.")
        return

    add_space()
    render_deal_revenue(deals)

    add_space()
    render_monthly_deals(deals)

    add_space()
    render_category_revenue(deals)


if __name__ == "__main__":
    main()
