from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Afspraken",
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


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


from sqlalchemy import create_engine

engine = create_engine(
    "mysql+pymysql://avnadmin:AVNS_IOr05TcV_n9lMLmM4do@vdk-dashboard-vdk-marketing.i.aivencloud.com:25406/dashboards",
    connect_args={"ssl": {}}
)

@st.cache_data(ttl=300)
def load_data() -> pd.DataFrame:
    try:

        df = pd.read_sql(
            "SELECT * FROM afspraken",
            engine
        )

        df.columns = df.columns.str.strip()

        df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

        return df

    except Exception as error:
        st.error(f"Kan data niet laden: {error}")
        return pd.DataFrame()


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    required_columns = {"datum", "is_geannuleerd"}

    if not required_columns.issubset(df.columns):
        st.error("De kolommen `datum` en `Is geannuleerd` ontbreken.")
        return pd.DataFrame()

    df = df.copy()

    df["datum"] = pd.to_datetime(
        df["datum"],
        dayfirst=True,
        errors="coerce",
    )

    df["is_geannuleerd"] = (
        df["is_geannuleerd"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(
            {
                "ja": True,
                "nee": False,
                "true": True,
                "false": False,
            }
        )
        .fillna(False)
    )

    return df


def prepare_weekly_data(df: pd.DataFrame) -> pd.DataFrame:
    df_active = (
        df[df["is_geannuleerd"] == False]
        .dropna(subset=["datum"])
        .copy()
    )

    if df_active.empty:
        return pd.DataFrame()

    df_active["Week_start"] = (
        df_active["datum"]
        - pd.to_timedelta(df_active["datum"].dt.weekday, unit="d")
    )

    weekly = (
        df_active
        .groupby("Week_start")
        .size()
        .reset_index(name="Aantal")
        .sort_values("Week_start")
    )

    weekly["Groei %"] = (
        weekly["Aantal"]
        .pct_change()
        .mul(100)
        .fillna(0)
        .round(1)
    )

    weekly["Week_label"] = (
        "Week "
        + weekly["Week_start"].dt.isocalendar().week.astype(str)
    )

    return weekly


def calculate_kpis(df: pd.DataFrame, weekly: pd.DataFrame) -> dict[str, float]:
    total = len(df)
    canceled = int(df["is_geannuleerd"].sum())
    cancel_rate = round((canceled / total) * 100, 1) if total else 0

    if weekly.empty:
        latest_week = 0
        growth = 0
    else:
        current_week_start = (
            pd.Timestamp.today().normalize()
            - pd.to_timedelta(pd.Timestamp.today().weekday(), unit="d")
        )

        current_week_data = weekly[weekly["Week_start"] == current_week_start]

        if current_week_data.empty:
            latest_week = int(weekly["Aantal"].iloc[-1])
            growth = float(weekly["Groei %"].iloc[-1])
        else:
            latest_week = int(current_week_data["Aantal"].iloc[0])
            growth = float(current_week_data["Groei %"].iloc[0])

    return {
        "total": total,
        "canceled": canceled,
        "cancel_rate": cancel_rate,
        "latest_week": latest_week,
        "growth": growth,
    }


def apply_chart_style(fig, height: int = 420):
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

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="#eef0ec",
    )

    return fig


def render_header() -> None:
    col1, _, col3 = st.columns([2, 2, 1])

    with col1:
        st.markdown(
            '<div class="vdk-main-title">Afspraken dashboard</div>',
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d-%m-%Y")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="vdk-divider"></div>', unsafe_allow_html=True)


def render_kpis(kpis: dict[str, float]) -> None:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Afspraken totaal",
        format_number(kpis["total"]),
    )

    col2.metric(
        "Geannuleerd",
        format_number(kpis["canceled"]),
    )

    col3.metric(
        "Annuleringsratio",
        f"{kpis['cancel_rate']:.1f}%",
    )

    col4.metric(
        "Laatste week",
        format_number(kpis["latest_week"]),
        f"{kpis['growth']:.1f}%",
    )


def render_week_chart(weekly: pd.DataFrame) -> None:
    if weekly.empty:
        st.info("Geen weekdata beschikbaar.")
        return

    st.subheader("Week overzicht")

    fig = px.bar(
        weekly,
        x="Week_label",
        y="Aantal",
        text="Aantal",
        color_discrete_sequence=["#084422"],
    )

    fig.update_traces(
        textposition="outside",
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Afspraken: %{y}<br>"
            "Groei: %{customdata[0]}%<extra></extra>"
        ),
        customdata=weekly[["Groei %"]],
    )

    fig.update_layout(
        showlegend=False,
        xaxis_title="",
        yaxis_title="Aantal afspraken",
    )

    st.plotly_chart(
        apply_chart_style(fig),
        use_container_width=True,
    )


def render_department_chart(df: pd.DataFrame) -> None:
    df_active = (
        df[df["is_geannuleerd"] == False]
        .dropna(subset=["datum"])
        .copy()
    )

    if df_active.empty or "dienst_categorie" not in df_active.columns:
        st.info("Geen afdelingsdata beschikbaar.")
        return

    st.subheader("Afspraken per afdeling")

    department_data = (
        df_active
        .groupby("dienst_categorie")
        .size()
        .reset_index(name="Aantal")
        .sort_values("Aantal", ascending=False)
    )

    fig = px.pie(
        department_data,
        names="dienst_categorie",
        values="Aantal",
        hole=0.55,
        color_discrete_sequence=[
            "#084422",
            "#3f6b53",
            "#7d9b88",
            "#b6c5b9",
            "#dfe7df",
        ],
    )

    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Afspraken: %{value}<br>"
            "Percentage: %{percent}<extra></extra>"
        ),
    )

    fig.update_layout(
        showlegend=False,
        margin=dict(t=40, l=30, r=30, b=40),
    )

    st.plotly_chart(
        apply_chart_style(fig, height=500),
        use_container_width=True,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


def main() -> None:
    df = clean_data(load_data())

    if df.empty:
        st.warning("Geen geldige afspraken-data beschikbaar.")
        return

    weekly = prepare_weekly_data(df)
    kpis = calculate_kpis(df, weekly)

    render_header()
    render_kpis(kpis)

    add_space()
    render_week_chart(weekly)

    add_space()
    render_department_chart(df)


if __name__ == "__main__":
    main()
