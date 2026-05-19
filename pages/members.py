import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import io
from datetime import datetime

st.set_page_config(page_title="Members", layout="wide")

STYLE = """
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">
<style>
html, body, [data-testid="stAppViewContainer"]{
    background:#f4efe6;
    font-family:'sofia-pro', sans-serif;
}
.block-container{
    padding-top:35px;
    padding-left:40px;
    padding-right:40px;
    padding-bottom:40px;
    max-width:100%;
}
</style>
"""

st.markdown(STYLE, unsafe_allow_html=True)

# =====================================================
# CONFIG
# =====================================================

MONTH_MAP = {
    1: "Jan", 2: "Feb", 3: "Mrt", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Dec"
}

MONTH_ORDER = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

SHEET_ID = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"
MEMBER_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"
DEALS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=MemberDeal"

# =====================================================
# HELPERS
# =====================================================

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:

    if df.empty:
        return df

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

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv, */*;q=0.1",
        }

        response = requests.get(
            url,
            headers=headers,
            timeout=15
        )

        response.raise_for_status()

        df = pd.read_csv(
            io.StringIO(response.text)
        )

        return normalize_columns(df)

    except requests.RequestException as e:

        st.error(f"❌ Kan data niet laden: {e}")
        return pd.DataFrame()

    except Exception as e:

        st.error(f"❌ Onverwachte fout: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_members():
    return fetch_sheet(MEMBER_URL)


@st.cache_data(ttl=3600)
def load_deals():
    return fetch_sheet(DEALS_URL)

# =====================================================
# LOAD DATA
# =====================================================

members = load_members()
deals = load_deals()

if members.empty:
    st.error("❌ Geen members data beschikbaar")
    st.stop()

members = members.dropna(subset=["member_id", "created_at"])

if members.empty:
    st.error("❌ Geen geldige members data na schoonmaken")
    st.stop()

# =====================================================
# PROCESS MEMBERS DATA
# =====================================================

members["week_label"] = members["created_at"].astype(str)
members["year"] = members["week_label"].str.extract(r'(\d{4})')[0].astype(int)
members["week"] = members["week_label"].str.extract(r'week (\d+)')[0].astype(int)

weekly = (
    members
    .groupby(["year", "week", "week_label"])
    .size()
    .reset_index(name="Nieuwe members")
)

weekly = weekly.sort_values(["year", "week"])

weekly["Groei"] = weekly["Nieuwe members"].diff().fillna(0)
weekly["Trend"] = weekly["Nieuwe members"].rolling(3).mean()
weekly["Totaal"] = weekly["Nieuwe members"].cumsum()

# =====================================================
# KPI BEREKENING
# =====================================================

if len(weekly) >= 2:

    vorige_week = int(weekly.iloc[-2]["Nieuwe members"])
    huidige_week = int(weekly.iloc[-1]["Nieuwe members"])

    groei_percentage = (
        ((huidige_week - vorige_week) / vorige_week * 100)
        if vorige_week > 0 else 0
    )

else:

    huidige_week = 0
    groei_percentage = 0

# =====================================================
# HEADER
# =====================================================

col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    st.title("Members")

with col3:
    st.text(f"{datetime.now().strftime('%d %B %Y')}")

st.divider()

# =====================================================
# KPI'S
# =====================================================

total_members = int(weekly["Nieuwe members"].sum())

latest_growth = (
    int(weekly["Groei"].iloc[-1])
    if len(weekly) > 0 else 0
)

total_cumulative = (
    int(weekly["Totaal"].iloc[-1])
    if len(weekly) > 0 else 0
)

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Nieuwe members totaal",
        f"{total_members:,}"
    )

with col2:

    st.metric(
        "Nieuwe members laatste week",
        f"{huidige_week:,}",
        delta=f"{groei_percentage:.1f}%",
        delta_color="normal" if groei_percentage >= 0 else "inverse"
    )

with col3:

    st.metric(
        "Totaal cumulatief",
        f"{total_cumulative:,}"
    )

st.divider()

# =====================================================
# MEMBERS GRAFIEKEN
# =====================================================

col1, col2 = st.columns(2)

with col1:

    st.subheader("Inkomende leden en weektrend")

    fig = px.line(
        weekly,
        x="week_label",
        y=["Nieuwe members", "Trend"],
        markers=True,
    )

    fig.update_layout(
        height=400,
        showlegend=True,
        xaxis_title="Week",
        yaxis_title="Aantal members"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

with col2:

    st.subheader("Wekelijkse groei")

    growth_df = weekly.copy()

    growth_df["kleur"] = growth_df["Groei"].apply(
        lambda x: "Groei" if x >= 0 else "Daling"
    )

    fig = px.bar(
        growth_df,
        x="week_label",
        y="Groei",
        color="kleur",
        color_discrete_map={
            "Groei": "#8cbe26",
            "Daling": "#c0392b"
        }
    )

    fig.add_hline(
        y=0,
        line_dash="dash",
        line_color="#084422"
    )

    fig.update_layout(
        height=400,
        showlegend=False,
        xaxis_title="Week",
        yaxis_title="Groei"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )

st.divider()

# =====================================================
# DEALS DATA
# =====================================================

if not deals.empty:

    deals["datum"] = pd.to_datetime(
        deals["datum"],
        errors="coerce"
    )

    deals["omzet"] = pd.to_numeric(
        deals["omzet"]
        .astype(str)
        .str.replace(",", "."),
        errors="coerce"
    ).fillna(0)

    deals["maand"] = deals["datum"].dt.month.map(MONTH_MAP)
    deals["maand_nummer"] = deals["datum"].dt.month

    # =====================================================
    # OMZET PER MEMBER DEAL
    # =====================================================

    if (
        "member_deal" in deals.columns and
        "omzet" in deals.columns
    ):

        total_per_deal = (
            deals
            .groupby("member_deal")["omzet"]
            .agg(["sum", "count", "mean"])
            .reset_index()
            .rename(columns={
                "sum": "totale_omzet",
                "count": "aantal_transacties",
                "mean": "gemiddelde_omzet"
            })
            .sort_values(
                "totale_omzet",
                ascending=False
            )
        )

        total_per_deal = total_per_deal[
            total_per_deal["totale_omzet"] > 0
        ]

        if not total_per_deal.empty:

            st.subheader("Omzet per member deal")

            fig = px.bar(
                total_per_deal,
                x="member_deal",
                y="totale_omzet",
                text_auto=".2s",
                color="totale_omzet",
                color_continuous_scale="Greens",
            )

            fig.update_layout(
                height=400,
                xaxis_title="Member deal",
                yaxis_title="Totale omzet (€)",
                showlegend=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

            # =====================================================
            # OMZET PER MAAND EN DEAL
            # =====================================================

            monthly_deal_chart = (
                deals
                .groupby([
                    "member_deal",
                    "maand",
                    "maand_nummer"
                ])["omzet"]
                .sum()
                .reset_index()
                .sort_values([
                    "maand_nummer",
                    "member_deal"
                ])
            )

            monthly_deal_chart = monthly_deal_chart[
                monthly_deal_chart["omzet"] > 0
            ]

            if not monthly_deal_chart.empty:

                col1, col2 = st.columns(2)

                with col1:

                    st.subheader("Maandelijke trend per deal")

                    fig = px.line(
                        monthly_deal_chart,
                        x="maand",
                        y="omzet",
                        color="member_deal",
                        markers=True,
                    )

                    fig.update_traces(
                        line=dict(width=2)
                    )

                    fig.update_layout(
                        height=450,
                        xaxis={
                            'categoryorder': 'array',
                            'categoryarray': MONTH_ORDER
                        },
                        yaxis_title="Omzet (€)",
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

                with col2:

                    st.subheader("Gestapelde omzet per deal")

                    pivot_chart = (
                        monthly_deal_chart
                        .pivot(
                            index="maand",
                            columns="member_deal",
                            values="omzet"
                        )
                        .fillna(0)
                    )

                    pivot_chart = pivot_chart.reset_index()

                    pivot_chart["maand_nummer"] = pivot_chart["maand"].map({
                        "Jan": 1,
                        "Feb": 2,
                        "Mrt": 3,
                        "Apr": 4,
                        "Mei": 5,
                        "Jun": 6,
                        "Jul": 7,
                        "Aug": 8,
                        "Sep": 9,
                        "Okt": 10,
                        "Nov": 11,
                        "Dec": 12
                    })

                    pivot_chart = pivot_chart.sort_values(
                        "maand_nummer"
                    )

                    fig = px.bar(
                        pivot_chart,
                        x="maand",
                        y=pivot_chart.columns[1:-1],
                        text_auto=".2s",
                    )

                    fig.update_layout(
                        height=450,
                        barmode="stack",
                        xaxis={
                            'categoryorder': 'array',
                            'categoryarray': MONTH_ORDER
                        },
                        yaxis_title="Omzet (€)",
                    )

                    st.plotly_chart(
                        fig,
                        use_container_width=True
                    )

    # =====================================================
    # OMZET PER CATEGORIE
    # =====================================================

    if (
        "categorie" in deals.columns and
        "omzet" in deals.columns
    ):

        categorie_df = (
            deals
            .groupby("categorie")["omzet"]
            .sum()
            .reset_index()
        )

        if not categorie_df.empty:

            st.divider()

            st.subheader("🎯 Omzetverdeling per categorie")

            fig = px.pie(
                categorie_df,
                names="categorie",
                values="omzet",
                hole=0.45
            )

            fig.update_layout(height=400)

            st.plotly_chart(
                fig,
                use_container_width=True
            )

else:

    st.info("ℹ️ Geen deals data beschikbaar")
