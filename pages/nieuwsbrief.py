
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://avnadmin:AVNS_IOr05TcV_n9lMLmM4do@vdk-dashboard-vdk-marketing.i.aivencloud.com:25406/dashboards",
    connect_args={"ssl": {}}
)



st.set_page_config(
    page_title="Nieuwsbrief Dashboard",
    layout="wide",
)


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
    font-size: 28px;
    font-weight: 700;
}

[data-testid="stMetricDelta"] {
    font-size: 13px;
    font-weight: 600;
}

div[data-testid="stPlotlyChart"] {
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}

.stSelectbox label {
    color: #6f766f !important;
    font-size: 14px;
    font-weight: 500;
}

[data-baseweb="select"] {
    max-width: 320px;
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


ALL_CAMPAIGNS_LABEL = "Alle campagnes"

NUMERIC_COLUMNS = [
    "sent",
    "opens",
    "clicks",
    "bounces",
    "unsubscribes",
]


@st.cache_data(ttl=3600)
def load_data():

    query = """
    SELECT *
    FROM nieuwsbrieven
    """

    df = pd.read_sql(query, engine)

    df.columns = df.columns.str.lower()

    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    return df


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "0"

    return f"{int(value):,}".replace(",", ".")


def format_rate(value: float | int) -> str:
    if pd.isna(value):
        return "0,0%"

    return f"{value:.1f}%".replace(".", ",")


def apply_chart_style(fig, height: int = 360):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(
            family="sofia-pro",
            color="#084422",
        ),
        title_font_size=20,
        margin=dict(l=30, r=30, t=40, b=40),
    )

    fig.update_xaxes(
        showgrid=True,
        gridcolor="#eef0ec",
    )

    fig.update_yaxes(
        showgrid=True,
        gridcolor="#eef0ec",
    )

    return fig


def render_header() -> None:
    col1, _, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(
            '<div class="vdk-main-title">Nieuwsbrief dashboard</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d-%m-%Y")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="vdk-divider"></div>', unsafe_allow_html=True)


def get_campaign_filter(df: pd.DataFrame) -> pd.DataFrame:
    campaigns = [ALL_CAMPAIGNS_LABEL]

    if {"campaign", "date"}.issubset(df.columns):
        campaign_order = (
            df.dropna(subset=["campaign"])
            .sort_values("date", ascending=False)
            .drop_duplicates(subset=["campaign"])
        )

        campaigns.extend(campaign_order["campaign"].astype(str).tolist())

    elif "campaign" in df.columns:
        campaigns.extend(sorted(df["campaign"].dropna().astype(str).unique()))

    selected_campaign = st.selectbox(
        "Campagne",
        campaigns,
    )

    if selected_campaign == ALL_CAMPAIGNS_LABEL:
        return df

    return df[df["campaign"].astype(str) == selected_campaign]


def calculate_kpis(df: pd.DataFrame) -> dict[str, float]:
    total_sent = int(df.get("sent", pd.Series(dtype=float)).sum())
    total_opens = int(df.get("opens", pd.Series(dtype=float)).sum())
    total_clicks = int(df.get("clicks", pd.Series(dtype=float)).sum())
    total_bounces = int(df.get("bounces", pd.Series(dtype=float)).sum())
    total_unsubs = int(df.get("unsubscribes", pd.Series(dtype=float)).sum())

    open_rate = round((total_opens / total_sent) * 100, 1) if total_sent else 0
    click_rate = round((total_clicks / total_sent) * 100, 1) if total_sent else 0
    bounce_rate = round((total_bounces / total_sent) * 100, 1) if total_sent else 0

    click_to_open = (
        round((total_clicks / total_opens) * 100, 1)
        if total_opens
        else 0
    )

    return {
        "total_sent": total_sent,
        "total_opens": total_opens,
        "total_clicks": total_clicks,
        "total_bounces": total_bounces,
        "total_unsubs": total_unsubs,
        "open_rate": open_rate,
        "click_rate": click_rate,
        "bounce_rate": bounce_rate,
        "click_to_open": click_to_open,
    }


def render_kpis(df: pd.DataFrame) -> None:
    kpis = calculate_kpis(df)

    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    col1.metric(
        "Verzonden mails",
        format_number(kpis["total_sent"]),
    )

    col2.metric(
        "Open rate",
        format_rate(kpis["open_rate"]),
        f"{format_number(kpis['total_opens'])} geopend",
    )

    col3.metric(
        "Click rate",
        format_rate(kpis["click_rate"]),
        f"{format_number(kpis['total_clicks'])} geklikt",
    )

    col4.metric(
        "Click-to-open",
        format_rate(kpis["click_to_open"]),
    )

    col5.metric(
        "Bounce rate",
        format_rate(kpis["bounce_rate"]),
        f"{format_number(kpis['total_bounces'])} bounced",
    )

    col6.metric(
        "Uitschrijvingen",
        format_number(kpis["total_unsubs"]),
    )


def render_chart(df: pd.DataFrame) -> None:
    required_columns = {"date", "clicks", "sent"}

    if not required_columns.issubset(df.columns) or len(df) <= 1:
        return

    chart_data = (
        df.dropna(subset=["date"])
        .sort_values("date")
        .copy()
    )

    if chart_data.empty:
        return

    chart_data["open_rate"] = (
        chart_data["opens"]
        .div(chart_data["sent"].replace(0, pd.NA))
        .fillna(0)
        * 100
    )

    chart_data["click_rate"] = (
        chart_data["clicks"]
        .div(chart_data["sent"].replace(0, pd.NA))
        .fillna(0)
        * 100
    )

    st.subheader("Click rate trend")

    fig = px.line(
        chart_data,
        x="date",
        y="click_rate",
        markers=True,
        color_discrete_sequence=["#084422"],
    )

    fig.update_traces(
        line=dict(
            width=3,
            shape="spline",
        )
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="Datum",
        yaxis_title="Click rate (%)",
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)

def main():

    st.markdown(STYLE, unsafe_allow_html=True)

    render_header()

    df = load_data()

    if df.empty:
        st.error("Geen data gevonden.")
        return

    filtered_df = get_campaign_filter(df)

    if filtered_df.empty:
        st.warning("Geen data beschikbaar.")
        return

    add_space()
    render_kpis(filtered_df)

    add_space()
    render_chart(filtered_df)


if __name__ == "__main__":
    main()
