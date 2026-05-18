import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Nieuwsbrief Dashboard",
    layout="wide",
)

STYLE = """
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>

html, body, [data-testid="stAppViewContainer"]{
    background:#f6f1e7;
    font-family:'sofia-pro', sans-serif;
}

.block-container{
    padding-top:30px;
    padding-left:55px;
    padding-right:55px;
    padding-bottom:40px;
    max-width:1700px;
}

/* HEADER */

.dashboard-header{
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding-bottom:25px;
    border-bottom:1px solid #bdb7ab;
    margin-bottom:25px;
}

.dashboard-title{
    font-size:58px;
    font-weight:700;
    color:#084422;
}

.dashboard-center{
    font-size:28px;
    font-weight:600;
    color:#111111;
}

.dashboard-date{
    font-size:18px;
    color:#084422;
    font-weight:600;
}

/* GRAPH BLOCK */

.graph-card{
    background:#ffffff;
    border-radius:30px;
    padding:30px;
    box-shadow:0 8px 25px rgba(0,0,0,0.04);
    margin-top:35px;
}

.stSelectbox label{
    display:none;
}

[data-baseweb="select"]{
    max-width:280px;
}

</style>
"""

# =====================================================
# DATA
# =====================================================

SHEET_ID = "1seQjiFaLzEm7PZ2vTDeylSZKEXGqDl6FHe2l1nVPnfg"

OPEN_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/"
    f"{SHEET_ID}/export?format=csv&gid=0"
)

ALL_CAMPAIGNS_LABEL = "Alle campagnes"

NUMERIC_COLUMNS = [
    "sent",
    "opens",
    "clicks",
    "bounces",
    "unsubscribes",
]

@st.cache_data(ttl=600)
def load_data() -> pd.DataFrame:

    try:
        df = pd.read_csv(OPEN_SHEET_URL)

    except Exception as exc:
        st.error(f"Kan data niet laden: {exc}")
        return pd.DataFrame()

    # ===== KOLOMNAMEN =====

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    # ===== NUMERIEKE KOLOMMEN =====

    for col in NUMERIC_COLUMNS:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace("\u00a0", "", regex=False)
                .str.replace(" ", "", regex=False)
                .str.replace(",", ".", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    # ===== DATUM =====

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            errors="coerce"
        )

    return df


def format_number(value) -> str:

    if pd.isna(value):
        return "0"

    return f"{int(value):,}".replace(",", ".")


def format_rate(value) -> str:

    if value is None or pd.isna(value):
        return "0,0%"

    return f"{value:.1f}%".replace(".", ",")


def render_header() -> None:

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        st.title("Nieuwsbrief")

    with col3:
        st.text(
            f"{datetime.now().strftime('%d %B %Y')}"
        )


def get_campaign_filter(df: pd.DataFrame) -> pd.DataFrame:

    campaigns = [ALL_CAMPAIGNS_LABEL]

    if "campaign" in df.columns:

        campaign_order = (
            df.dropna(subset=["campaign"])
            .sort_values("date", ascending=False)
            .drop_duplicates(subset=["campaign"])
        )

        campaigns.extend(
            campaign_order["campaign"]
            .astype(str)
            .tolist()
        )

    selected_campaign = st.selectbox(
        "Campagne",
        campaigns
    )

    if selected_campaign != ALL_CAMPAIGNS_LABEL:

        return df[
            df["campaign"] == selected_campaign
        ]

    return df


def render_kpis(df: pd.DataFrame) -> None:

    total_sent = int(
        df.get("sent", pd.Series(0)).sum()
    )

    total_opens = int(
        df.get("opens", pd.Series(0)).sum()
    )

    total_clicks = int(
        df.get("clicks", pd.Series(0)).sum()
    )

    total_bounces = int(
        df.get("bounces", pd.Series(0)).sum()
    )

    total_unsubs = int(
        df.get("unsubscribes", pd.Series(0)).sum()
    )

    open_rate = (
        round((total_opens / total_sent) * 100, 1)
        if total_sent else 0
    )

    click_rate = (
        round((total_clicks / total_sent) * 100, 1)
        if total_sent else 0
    )

    bounce_rate = (
        round((total_bounces / total_sent) * 100, 1)
        if total_sent else 0
    )

    click_to_open = (
        round((total_clicks / total_opens) * 100, 1)
        if total_opens else 0
    )

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric(
            "Verzonden mails",
            format_number(total_sent)
        )

    with col2:
        st.metric(
            "Open rate",
            format_rate(open_rate),
            f"{format_number(total_opens)} geopend"
        )

    with col3:
        st.metric(
            "Click rate",
            format_rate(click_rate),
            f"{format_number(total_clicks)} geklikt"
        )

    with col4:
        st.metric(
            "Click-to-open",
            format_rate(click_to_open)
        )

    with col5:
        st.metric(
            "Bounce rate",
            format_rate(bounce_rate),
            f"{format_number(total_bounces)} bounced"
        )

    with col6:
        st.metric(
            "Uitschrijvingen",
            format_number(total_unsubs)
        )


def render_chart(df: pd.DataFrame) -> None:

    if len(df) <= 1:
        return

    st.subheader("Click rate trend")

    chart_data = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .copy()
    )

    chart_data["click_rate"] = (
        chart_data["clicks"]
        .astype(float)
        .div(
            chart_data["sent"]
            .replace(0, pd.NA)
        )
        .fillna(0)
        * 100
    )

    fig = px.line(
        chart_data,
        x="date",
        y="click_rate",
        markers=True,
    )

    fig.update_traces(
        line=dict(
            color="#084422",
            width=4,
            shape="spline"
        )
    )

    fig.update_layout(
        height=350,
        showlegend=False,
        xaxis_title="Datum",
        yaxis_title="Click rate (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#ececf3"
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#ececf3"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


def main() -> None:

    st.markdown(
        STYLE,
        unsafe_allow_html=True
    )

    render_header()

    df = load_data()

    if df.empty:
        st.error("Geen data gevonden.")
        return

    filtered_df = get_campaign_filter(df)

    if filtered_df.empty:
        st.warning(
            "Geen data beschikbaar voor de geselecteerde campagne."
        )
        return

    st.divider()

    render_kpis(filtered_df)

    st.divider()

    render_chart(filtered_df)


if __name__ == "__main__":
    main()