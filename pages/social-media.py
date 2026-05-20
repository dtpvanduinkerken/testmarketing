import io
from datetime import datetime

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


st.set_page_config(
    page_title="Social media dashboard",
    layout="wide",
)


SHEET_ID = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"

GIDS = {
    "instagram": "0",
    "facebook": "847206611",
    "followers": "730161295",
}

NUMERIC_COLUMNS = ["likes", "views", "comments", "shares", "saves"]
FOLLOWER_COLUMNS = ["instagram_followers", "facebook_followers"]


STYLE = """
<link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #f4efe6;
    font-family: 'sofia-pro', sans-serif;
}

.block-container {
    padding: 35px 40px 40px 40px;
    max-width: 100%;
}

#MainMenu,
footer,
header {
    visibility: hidden;
}

.vdk-main-title {
    font-size: 54px;
    font-weight: 700;
    color: #084422;
    margin: 0;
}

.vdk-date {
    text-align: right;
    color: #084422;
    font-size: 18px;
    margin-top: 14px;
}

.vdk-divider {
    width: 100%;
    height: 1px;
    background: rgba(8, 68, 34, 0.12);
    margin-top: 30px;
    margin-bottom: 50px;
}

.kpi-wrapper {
    background: #ffffff;
    border-radius: 24px;
    padding: 26px;
    box-shadow: 0 10px 25px rgba(8, 68, 34, 0.05);
    min-height: 170px;
}

.kpi-label {
    color: #9b9b9b;
    font-size: 15px;
    margin-bottom: 24px;
}

.kpi-value {
    color: #3d3f4d;
    font-size: 48px;
    font-weight: 700;
    line-height: 1;
}

.kpi-growth {
    margin-top: 16px;
    font-size: 22px;
    font-weight: 700;
}

[data-testid="stDataFrame"],
div[data-testid="stPlotlyChart"] {
    border-radius: 24px !important;
    overflow: hidden;
}

.space {
    height: 50px;
}
</style>
"""


def get_sheet_url(gid: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={gid}"
    )


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


@st.cache_data(ttl=600)
def fetch_sheet(sheet_gid: str) -> pd.DataFrame:
    url = get_sheet_url(sheet_gid)

    response = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv, */*;q=0.1",
        },
        timeout=20,
    )
    response.raise_for_status()
    response.encoding = "utf-8"

    return normalize_columns(pd.read_csv(io.StringIO(response.text)))


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace("%", "", regex=False)
        .str.strip(),
        errors="coerce",
    ).fillna(0)


def calculate_engagement(df: pd.DataFrame) -> pd.Series:
    required_columns = ["likes", "comments", "shares", "saves", "views"]

    if not all(column in df.columns for column in required_columns):
        return pd.Series(0, index=df.index)

    interactions = (
        df["likes"] +
        df["comments"] +
        df["shares"] +
        df["saves"]
    )

    engagement = interactions / df["views"].replace(0, pd.NA) * 100

    return (
        engagement
        .fillna(0)
        .replace([float("inf"), -float("inf")], 0)
        .round(1)
    )


def clean_posts_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for column in NUMERIC_COLUMNS:
        if column in df.columns:
            df[column] = to_number(df[column])

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    df["engagement"] = calculate_engagement(df)

    return df


def clean_followers_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    for column in FOLLOWER_COLUMNS:
        if column in df.columns:
            df[column] = to_number(df[column])

    return (
        df
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )


@st.cache_data(ttl=600)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    instagram_df = fetch_sheet(GIDS["instagram"])
    instagram_df["channel"] = "Instagram"

    facebook_df = fetch_sheet(GIDS["facebook"])
    facebook_df["channel"] = "Facebook"

    followers_df = fetch_sheet(GIDS["followers"])

    posts_df = pd.concat(
        [instagram_df, facebook_df],
        ignore_index=True,
    )

    return clean_posts_data(posts_df), clean_followers_data(followers_df)


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(value):,}".replace(",", ".")


def calculate_growth(current: float, previous: float) -> tuple[str, str]:
    if pd.isna(previous) or previous <= 0:
        return "0,0%", "#58a55c"

    growth = ((current - previous) / previous) * 100
    arrow = "↓" if growth < 0 else "↑"
    color = "#d64545" if growth < 0 else "#58a55c"

    label = f"{arrow} {abs(growth):.1f}%".replace(".", ",")

    return label, color


def get_latest_growth(df: pd.DataFrame, column: str) -> tuple[int, str, str]:
    if column not in df.columns or len(df[column].dropna()) < 2:
        return 0, "0,0%", "#58a55c"

    values = df[column].dropna().astype(float)
    current = values.iloc[-1]
    previous = values.iloc[-2]
    growth, color = calculate_growth(current, previous)

    return int(current), growth, color


def render_header() -> None:
    title_col, _, date_col = st.columns([2, 2, 1])

    with title_col:
        st.markdown(
            '<div class="vdk-main-title">Social Media</div>',
            unsafe_allow_html=True,
        )

    with date_col:
        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d-%m-%Y")}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="vdk-divider"></div>', unsafe_allow_html=True)


def render_metrics(posts_df: pd.DataFrame) -> None:
    col1, col2, col3, col4 = st.columns(4)

    views = posts_df["views"] if "views" in posts_df.columns else pd.Series(dtype=float)
    engagement = (
        posts_df["engagement"]
        if "engagement" in posts_df.columns
        else pd.Series(dtype=float)
    )

    col1.metric("Totaal posts", len(posts_df))
    col2.metric("Gem. views", format_number(views.mean()))
    col3.metric("Gem. engagement", f"{engagement.mean():.1f}%")
    col4.metric("Totale views", format_number(views.sum()))


def render_kpi_card(label: str, value: str, growth: str, color: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-wrapper">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-growth" style="color:{color};">{growth}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis(followers_df: pd.DataFrame, posts_df: pd.DataFrame) -> None:
    insta_followers, insta_growth, insta_color = get_latest_growth(
        followers_df,
        "instagram_followers",
    )

    facebook_followers, facebook_growth, facebook_color = get_latest_growth(
        followers_df,
        "facebook_followers",
    )

    avg_engagement = posts_df["engagement"].mean() if "engagement" in posts_df else 0
    engagement_growth = "0,0%"
    engagement_color = "#58a55c"

    recent_posts = posts_df.dropna(subset=["date"]).sort_values("date")

    if len(recent_posts) >= 2:
        current = recent_posts.iloc[-1]["engagement"]
        previous = recent_posts.iloc[-2]["engagement"]
        engagement_growth, engagement_color = calculate_growth(current, previous)

    col1, col2, col3 = st.columns(3)

    with col1:
        render_kpi_card(
            "Volgers Instagram",
            format_number(insta_followers),
            insta_growth,
            insta_color,
        )

    with col2:
        render_kpi_card(
            "Volgers Facebook",
            format_number(facebook_followers),
            facebook_growth,
            facebook_color,
        )

    with col3:
        render_kpi_card(
            "Engagement",
            f"{avg_engagement:.1f}%".replace(".", ","),
            engagement_growth,
            engagement_color,
        )


def render_category_chart(df: pd.DataFrame) -> None:
    if "categorie" not in df.columns or df.empty:
        return

    category_counts = (
        df
        .groupby("categorie", dropna=False)
        .size()
        .reset_index(name="aantal_posts")
    )

    fig = px.pie(
        category_counts,
        names="categorie",
        values="aantal_posts",
        hole=0.35,
        title="Categorieën overzicht",
    )

    fig.update_layout(height=450)

    st.plotly_chart(fig, use_container_width=True)


def render_trend_chart(df: pd.DataFrame) -> None:
    if not {"date", "channel", "views"}.issubset(df.columns) or df.empty:
        return

    trend = (
        df
        .dropna(subset=["date"])
        .groupby(["date", "channel"], as_index=False)["views"]
        .sum()
    )

    fig = px.line(
        trend,
        x="date",
        y="views",
        color="channel",
        markers=True,
        title="Views trend",
    )

    fig.update_layout(height=350)

    st.plotly_chart(fig, use_container_width=True)


def render_tables(df: pd.DataFrame) -> None:
    columns = ["topic", "likes", "views", "comments", "shares", "saves"]

    instagram = df[df["channel"] == "Instagram"]
    facebook = df[df["channel"] == "Facebook"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Instagram")
        st.dataframe(
            instagram[[column for column in columns if column in instagram.columns]],
            use_container_width=True,
            hide_index=True,
            height=350,
        )

    with col2:
        st.subheader("Facebook")
        st.dataframe(
            facebook[[column for column in columns if column in facebook.columns]],
            use_container_width=True,
            hide_index=True,
            height=350,
        )


def render_sidebar(df: pd.DataFrame) -> list[str]:
    st.sidebar.header("Filters")

    channels = sorted(df["channel"].dropna().unique())

    return st.sidebar.multiselect(
        "Kanalen",
        options=channels,
        default=channels,
    )


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


def main() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)

    try:
        posts_df, followers_df = load_data()
    except requests.RequestException as error:
        st.error(f"Fout bij ophalen van Google Sheets-data: {error}")
        return
    except Exception as error:
        st.error(f"Onverwachte fout bij inladen van data: {error}")
        return

    if posts_df.empty:
        st.warning("Geen data beschikbaar.")
        return

    selected_channels = render_sidebar(posts_df)

    filtered_posts_df = posts_df[
        posts_df["channel"].isin(selected_channels)
    ]

    if filtered_posts_df.empty:
        st.warning("Geen data beschikbaar voor de gekozen filters.")
        return

    render_header()
    render_metrics(filtered_posts_df)

    add_space()
    render_kpis(followers_df, filtered_posts_df)

    add_space()
    render_category_chart(filtered_posts_df)

    add_space()
    render_trend_chart(filtered_posts_df)

    add_space()
    render_tables(filtered_posts_df)

    csv = filtered_posts_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download gefilterde data als CSV",
        data=csv,
        file_name="marketing_data_export.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
