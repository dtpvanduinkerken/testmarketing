import io
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

st.set_page_config(
    page_title="Social media dashboard",
    layout="wide",
)

# =========================
# GOOGLE SHEETS
# =========================

SHEET_ID = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"

INSTAGRAM_GID = "0"
FACEBOOK_GID = "847206611"
FOLLOWERS_GID = "730161295"


def get_sheet_url(gid: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/"
        f"{SHEET_ID}/export?format=csv&gid={gid}"
    )


# =========================
# STYLING
# =========================

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

#MainMenu,
footer,
header{
    visibility:hidden;
}

.vdk-main-title{
    font-size:54px;
    font-weight:700;
    color:#084422;
    margin:0;
}

.vdk-date{
    text-align:right;
    color:#084422;
    font-size:18px;
    margin-top:14px;
}

.vdk-divider{
    width:100%;
    height:1px;
    background:rgba(8,68,34,0.12);
    margin-top:30px;
    margin-bottom:50px;
}

.kpi-wrapper{
    background:#ffffff;
    border-radius:24px;
    padding:26px;
    box-shadow:0 10px 25px rgba(8,68,34,0.05);
    min-height:170px;
}

.kpi-label{
    color:#9b9b9b;
    font-size:15px;
    margin-bottom:24px;
}

.kpi-value{
    color:#3d3f4d;
    font-size:48px;
    font-weight:700;
    line-height:1;
}

.kpi-growth{
    margin-top:16px;
    font-size:22px;
    font-weight:700;
}

[data-testid="stDataFrame"]{
    border-radius:24px !important;
    overflow:hidden;
}

div[data-testid="stPlotlyChart"]{
    border-radius:24px !important;
    overflow:hidden;
}

.space{
    height:50px;
}

</style>
"""

# =========================
# HELPERS
# =========================

NUMERIC_COLUMNS = [
    "likes",
    "views",
    "comments",
    "shares",
    "saves",
]

FOLLOWER_COLUMNS = [
    "instagram_followers",
    "facebook_followers",
]


def normalize_columns(df):

    df = df.copy()

    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )

    return df


def calculate_engagement_from_columns(df):

    if all(col in df.columns for col in [
        "likes",
        "comments",
        "shares",
        "saves",
        "views"
    ]):

        engagement = (
            (
                df["likes"]
                + df["comments"]
                + df["shares"]
                + df["saves"]
            )
            / df["views"].replace(0, pd.NA)
        ) * 100

        return (
            engagement
            .fillna(0)
            .replace([float("inf"), -float("inf")], 0)
            .round(1)
        )

    return pd.Series(0, index=df.index)


def fetch_sheet(sheet_gid):

    url = get_sheet_url(sheet_gid)

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/csv, */*;q=0.1",
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    response.encoding = "utf-8"

    df = pd.read_csv(io.StringIO(response.text))

    return normalize_columns(df)


# =========================
# CLEAN POSTS
# =========================

def clean_posts_data(df):

    if df.empty:
        return df

    df = df.copy()

    for col in NUMERIC_COLUMNS:

        if col in df.columns:

            df[col] = (
                df[col]
                .astype(str)
                .str.replace(",", ".", regex=False)
                .str.replace("%", "", regex=False)
                .str.strip()
            )

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y-%m-%d",
            errors="coerce"
        )

    df["engagement"] = calculate_engagement_from_columns(df)

    return df


# =========================
# CLEAN FOLLOWERS
# =========================

def clean_followers_data(df):

    if df.empty:
        return df

    df = df.copy()

    if "date" in df.columns:

        df["date"] = pd.to_datetime(
            df["date"],
            format="%Y-%m-%d",
            errors="coerce"
        )

    for col in FOLLOWER_COLUMNS:

        if col in df.columns:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            ).fillna(0)

    df = (
        df
        .dropna(subset=["date"])
        .sort_values("date")
        .reset_index(drop=True)
    )

    return df


# =========================
# FORMATTERS
# =========================

def format_number(value):

    if pd.isna(value):
        return "-"

    try:
        return f"{int(value):,}".replace(",", ".")
    except Exception:
        return str(value)


# =========================
# LOAD DATA
# =========================

@st.cache_data(ttl=0)
def load_data():

    try:

        instagram_df = fetch_sheet(INSTAGRAM_GID)
        instagram_df["channel"] = "Instagram"

        facebook_df = fetch_sheet(FACEBOOK_GID)
        facebook_df["channel"] = "Facebook"

        followers_df = fetch_sheet(FOLLOWERS_GID)

        combined_posts = pd.concat(
            [instagram_df, facebook_df],
            ignore_index=True
        )

        return (
            clean_posts_data(combined_posts),
            clean_followers_data(followers_df)
        )

    except Exception as exc:

        st.error(f"Fout bij inladen van data: {exc}")

        return pd.DataFrame(), pd.DataFrame()


# =========================
# HEADER
# =========================

def render_header():

    h1, h2, h3 = st.columns([2, 2, 1])

    with h1:

        st.markdown(
            '<div class="vdk-main-title">Social Media</div>',
            unsafe_allow_html=True
        )

    with h3:

        st.markdown(
            f'<div class="vdk-date">{datetime.now().strftime("%d %B %Y")}</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        '<div class="vdk-divider"></div>',
        unsafe_allow_html=True
    )


# =========================
# KPI'S
# =========================

def render_kpis(followers_df, posts_df):

    # =========================
    # INSTAGRAM
    # =========================

    insta_followers = 0
    insta_growth = "0,0%"
    insta_color = "#58a55c"
    insta_arrow = "↑"

    if (
        "instagram_followers" in followers_df.columns
        and len(followers_df) >= 2
    ):

        insta_values = (
            followers_df["instagram_followers"]
            .dropna()
            .astype(int)
        )

        current = insta_values.iloc[-1]
        previous = insta_values.iloc[-2]

        insta_followers = current

        if previous > 0:

            growth = (
                (current - previous)
                / previous
            ) * 100

            if growth < 0:
                insta_color = "#d64545"
                insta_arrow = "↓"

            insta_growth = (
                f"{insta_arrow} "
                f"{abs(growth):.1f}%"
            ).replace(".", ",")

    # =========================
    # FACEBOOK
    # =========================

    facebook_followers = 0
    facebook_growth = "0,0%"
    facebook_color = "#58a55c"
    facebook_arrow = "↑"

    if (
        "facebook_followers" in followers_df.columns
        and len(followers_df) >= 2
    ):

        facebook_values = (
            followers_df["facebook_followers"]
            .dropna()
            .astype(int)
        )

        current = facebook_values.iloc[-1]
        previous = facebook_values.iloc[-2]

        facebook_followers = current

        if previous > 0:

            growth = (
                (current - previous)
                / previous
            ) * 100

            if growth < 0:
                facebook_color = "#d64545"
                facebook_arrow = "↓"

            facebook_growth = (
                f"{facebook_arrow} "
                f"{abs(growth):.1f}%"
            ).replace(".", ",")

    # =========================
    # ENGAGEMENT
    # =========================

    engagement_color = "#58a55c"
    engagement_arrow = "↑"
    engagement_growth = "0,0%"

    avg_engagement = round(
        posts_df["engagement"].mean(),
        1
    )

    recent_posts = posts_df.sort_values("date")

    if len(recent_posts) >= 2:

        current_engagement = (
            recent_posts.iloc[-1]["engagement"]
        )

        previous_engagement = (
            recent_posts.iloc[-2]["engagement"]
        )

        if previous_engagement > 0:

            growth = (
                (
                    current_engagement
                    - previous_engagement
                )
                / previous_engagement
            ) * 100

            if growth < 0:
                engagement_color = "#d64545"
                engagement_arrow = "↓"

            engagement_growth = (
                f"{engagement_arrow} "
                f"{abs(growth):.1f}%"
            ).replace(".", ",")

    # =========================
    # KPI BLOKKEN
    # =========================

    k1, k2, k3 = st.columns(3)

    with k1:

        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-label">Volgers Instagram</div>
            <div class="kpi-value">{format_number(insta_followers)}</div>
            <div class="kpi-growth" style="color:{insta_color};">
                {insta_growth}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k2:

        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-label">Volgers Facebook</div>
            <div class="kpi-value">{format_number(facebook_followers)}</div>
            <div class="kpi-growth" style="color:{facebook_color};">
                {facebook_growth}
            </div>
        </div>
        """, unsafe_allow_html=True)

    with k3:

        st.markdown(f"""
        <div class="kpi-wrapper">
            <div class="kpi-label">Engagement</div>
            <div class="kpi-value">
                {str(avg_engagement).replace('.', ',')}%
            </div>
            <div class="kpi-growth" style="color:{engagement_color};">
                {engagement_growth}
            </div>
        </div>
        """, unsafe_allow_html=True)


# =========================
# METRICS
# =========================

def render_metrics(posts_df):

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "Totaal posts",
            len(posts_df)
        )

    with col2:

        st.metric(
            "Gem. views",
            format_number(posts_df["views"].mean())
        )

    with col3:

        st.metric(
            "Gem. engagement",
            f"{posts_df['engagement'].mean():.1f}%"
        )

    with col4:

        st.metric(
            "Totale views",
            format_number(posts_df["views"].sum())
        )


# =========================
# CATEGORY CHART
# =========================

def render_category_chart(df):

    if "categorie" not in df.columns:
        return

    category_counts = (
        df.groupby("categorie")
        .size()
        .reset_index(name="Aantal posts")
    )

    fig = px.pie(
        category_counts,
        names="categorie",
        values="Aantal posts",
        hole=0.35,
        title="Categorieën overzicht"
    )

    fig.update_layout(height=450)

    st.plotly_chart(fig, width="stretch")


# =========================
# TREND CHART
# =========================

def render_trend_chart(df):

    if "date" not in df.columns:
        return

    trend = (
        df.groupby(["date", "channel"])["views"]
        .sum()
        .reset_index()
    )

    fig = px.line(
        trend,
        x="date",
        y="views",
        color="channel",
        markers=True,
        title="Views trend"
    )

    fig.update_layout(height=350)

    st.plotly_chart(fig, width="stretch")


# =========================
# TABLES
# =========================

def render_tables(df):

    instagram = df[df["channel"] == "Instagram"]
    facebook = df[df["channel"] == "Facebook"]

    cols = [
        "topic",
        "likes",
        "views",
        "comments",
        "shares",
        "saves"
    ]

    t1, t2 = st.columns(2)

    with t1:

        st.write("Instagram")

        st.dataframe(
            instagram[[c for c in cols if c in instagram.columns]],
            width="stretch",
            hide_index=True,
            height=350
        )

    with t2:

        st.write("Facebook")

        st.dataframe(
            facebook[[c for c in cols if c in facebook.columns]],
            width="stretch",
            hide_index=True,
            height=350
        )


# =========================
# SIDEBAR
# =========================

def render_sidebar(df):

    st.sidebar.header("Filters")

    channels = sorted(df["channel"].dropna().unique())

    selected_channels = st.sidebar.multiselect(
        "Kanalen",
        options=channels,
        default=channels
    )

    return selected_channels


# =========================
# FILTER
# =========================

def filter_data(df, selected_channels):

    if selected_channels:

        df = df[
            df["channel"].isin(selected_channels)
        ]

    return df


# =========================
# MAIN
# =========================

def main():

    st.markdown(STYLE, unsafe_allow_html=True)

    posts_df, followers_df = load_data()

    if posts_df.empty:

        st.warning("Geen data beschikbaar.")
        return

    selected_channels = render_sidebar(posts_df)

    filtered_posts_df = filter_data(
        posts_df,
        selected_channels
    )

    render_header()

    render_metrics(filtered_posts_df)

    st.markdown(
        '<div class="space"></div>',
        unsafe_allow_html=True
    )

    render_kpis(
        followers_df,
        filtered_posts_df
    )

    st.markdown(
        '<div class="space"></div>',
        unsafe_allow_html=True
    )

    render_category_chart(filtered_posts_df)

    st.markdown(
        '<div class="space"></div>',
        unsafe_allow_html=True
    )

    render_trend_chart(filtered_posts_df)

    st.markdown(
        '<div class="space"></div>',
        unsafe_allow_html=True
    )

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