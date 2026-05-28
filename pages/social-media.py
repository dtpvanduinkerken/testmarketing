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

.analysis-wrapper {
    background: #ffffff;
    border-radius: 18px;
    padding: 26px 30px;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}

.analysis-title {
    color: #084422;
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 16px;
}

.analysis-item {
    color: #084422;
    font-size: 16px;
    line-height: 1.55;
    margin-bottom: 10px;
}

.kpi-wrapper {
    background: #ffffff;
    border-radius: 18px;
    padding: 24px;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
    min-height: 145px;
}

.kpi-label {
    color: #6f766f;
    font-size: 14px;
    margin-bottom: 18px;
    font-weight: 500;
}

.kpi-value {
    color: #084422;
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
}

.kpi-growth {
    margin-top: 14px;
    font-size: 15px;
    font-weight: 600;
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

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid rgba(8, 68, 34, 0.06);
}

[data-testid="stSidebar"] * {
    color: #084422 !important;
}

[data-testid="stDataFrame"],
div[data-testid="stPlotlyChart"] {
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
        df["likes"]
        + df["comments"]
        + df["shares"]
        + df["saves"]
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
        df = df.dropna(subset=["date"]).sort_values("date")

    for column in FOLLOWER_COLUMNS:
        if column in df.columns:
            df[column] = to_number(df[column])

    return df.reset_index(drop=True)


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

    return f"{arrow} {abs(growth):.1f}%".replace(".", ","), color


def get_latest_growth(df: pd.DataFrame, column: str) -> tuple[int, str, str]:
    if column not in df.columns:
        return 0, "0,0%", "#58a55c"

    values = df[column].dropna()

    if len(values) < 2:
        current = int(values.iloc[-1]) if len(values) == 1 else 0
        return current, "0,0%", "#58a55c"

    current = values.iloc[-1]
    previous = values.iloc[-2]
    growth, color = calculate_growth(current, previous)

    return int(current), growth, color


def render_header() -> None:
    title_col, _, date_col = st.columns([2, 2, 1])

    with title_col:
        st.markdown(
            '<div class="vdk-main-title">Social media dashboard</div>',
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

    views = (
        posts_df["views"]
        if "views" in posts_df.columns
        else pd.Series(dtype=float)
    )

    engagement = (
        posts_df["engagement"]
        if "engagement" in posts_df.columns
        else pd.Series(dtype=float)
    )

    avg_views = views.mean() if not views.empty else 0
    avg_engagement = engagement.mean() if not engagement.empty else 0
    total_views = views.sum() if not views.empty else 0

    col1.metric("Totaal posts", len(posts_df))
    col2.metric("Gem. views", format_number(avg_views))
    col3.metric("Gem. engagement", f"{avg_engagement:.1f}%")
    col4.metric("Totale views", format_number(total_views))


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


def render_kpis(
    followers_df: pd.DataFrame,
    posts_df: pd.DataFrame,
) -> None:
    insta_followers, insta_growth, insta_color = get_latest_growth(
        followers_df,
        "instagram_followers",
    )

    facebook_followers, facebook_growth, facebook_color = get_latest_growth(
        followers_df,
        "facebook_followers",
    )

    avg_engagement = (
        posts_df["engagement"].mean()
        if "engagement" in posts_df.columns and not posts_df.empty
        else 0
    )

    engagement_growth = "0,0%"
    engagement_color = "#58a55c"

    if "date" in posts_df.columns:
        recent_posts = posts_df.dropna(subset=["date"]).sort_values("date")
    else:
        recent_posts = posts_df.copy()

    if len(recent_posts) >= 2 and "engagement" in recent_posts.columns:
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


def build_analysis_points(
    posts_df: pd.DataFrame,
    followers_df: pd.DataFrame,
) -> list[str]:
    points = []

    if posts_df.empty:
        return ["Er is geen data beschikbaar voor analyse."]

    total_posts = len(posts_df)
    total_views = posts_df["views"].sum() if "views" in posts_df.columns else 0
    avg_engagement = (
        posts_df["engagement"].mean()
        if "engagement" in posts_df.columns
        else 0
    )

    points.append(
        f"Er zijn {format_number(total_posts)} posts geanalyseerd met in totaal "
        f"{format_number(total_views)} views."
    )

    if {"channel", "views"}.issubset(posts_df.columns):
        channel_views = posts_df.groupby("channel")["views"].sum()

        if not channel_views.empty:
            best_channel = channel_views.idxmax()
            best_channel_views = channel_views.max()

            points.append(
                f"{best_channel} levert de meeste views op "
                f"({format_number(best_channel_views)} views)."
            )

    if {"post_type", "views", "engagement"}.issubset(posts_df.columns):
        post_type_stats = (
            posts_df
            .dropna(subset=["post_type"])
            .groupby("post_type")
            .agg(
                gemiddelde_views=("views", "mean"),
                gemiddelde_engagement=("engagement", "mean"),
                totaal_posts=("post_type", "count"),
            )
        )

        if not post_type_stats.empty:
            best_views_type = post_type_stats["gemiddelde_views"].idxmax()
            best_views_value = post_type_stats.loc[
                best_views_type,
                "gemiddelde_views",
            ]

            best_engagement_type = (
                post_type_stats["gemiddelde_engagement"].idxmax()
            )
            best_engagement_value = post_type_stats.loc[
                best_engagement_type,
                "gemiddelde_engagement",
            ]

            points.append(
                f"{best_views_type} werkt het beste voor bereik, met gemiddeld "
                f"{format_number(best_views_value)} views per post."
            )

            points.append(
                f"{best_engagement_type} zorgt voor de hoogste betrokkenheid, "
                f"met gemiddeld {best_engagement_value:.1f}% engagement."
            )

    if {"topic", "views"}.issubset(posts_df.columns):
        top_post = posts_df.sort_values("views", ascending=False).iloc[0]

        points.append(
            f"De best presterende post op views is '{top_post['topic']}' "
            f"met {format_number(top_post['views'])} views."
        )

    if {"topic", "engagement"}.issubset(posts_df.columns):
        top_engagement = posts_df.sort_values(
            "engagement",
            ascending=False,
        ).iloc[0]

        points.append(
            f"De hoogste engagement komt van '{top_engagement['topic']}' "
            f"met {top_engagement['engagement']:.1f}% engagement."
        )

    if "categorie" in posts_df.columns:
        category_counts = posts_df["categorie"].dropna().value_counts()

        if not category_counts.empty:
            top_category = category_counts.idxmax()
            top_category_count = category_counts.max()

            points.append(
                f"De meest gebruikte categorie is '{top_category}' "
                f"met {format_number(top_category_count)} posts."
            )

    points.append(
        f"De gemiddelde engagement over de geselecteerde data is "
        f"{avg_engagement:.1f}%."
    )

    if not followers_df.empty:
        insta_followers, insta_growth, _ = get_latest_growth(
            followers_df,
            "instagram_followers",
        )
        facebook_followers, facebook_growth, _ = get_latest_growth(
            followers_df,
            "facebook_followers",
        )

        points.append(
            f"Instagram heeft momenteel {format_number(insta_followers)} "
            f"volgers ({insta_growth}); Facebook heeft "
            f"{format_number(facebook_followers)} volgers ({facebook_growth})."
        )

    return points


def render_analysis(
    posts_df: pd.DataFrame,
    followers_df: pd.DataFrame,
) -> None:
    analysis_points = build_analysis_points(posts_df, followers_df)

    analysis_html = """
    <div class="analysis-wrapper">
        <div class="analysis-title">Belangrijkste inzichten</div>
    """

    for point in analysis_points:
        analysis_html += f'<div class="analysis-item">• {point}</div>'

    analysis_html += "</div>"

    st.markdown(analysis_html, unsafe_allow_html=True)


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
        hole=0.55,
        title="Categorieën overzicht",
        color_discrete_sequence=[
            "#084422",
            "#3f6b53",
            "#7d9b88",
            "#b6c5b9",
            "#dfe7df",
        ],
    )

    fig.update_layout(
        height=420,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="sofia-pro", color="#084422"),
        title_font_size=20,
    )

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

    if trend.empty:
        return

    fig = px.line(
        trend,
        x="date",
        y="views",
        color="channel",
        markers=True,
        title="Views trend",
        color_discrete_sequence=["#084422", "#7d9b88"],
    )

    fig.update_layout(
        height=350,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="sofia-pro", color="#084422"),
        title_font_size=20,
    )

    st.plotly_chart(fig, use_container_width=True)


def render_post_type_analysis(df: pd.DataFrame) -> None:
    required_columns = {"post_type", "views", "engagement"}

    if not required_columns.issubset(df.columns) or df.empty:
        st.info(
            "Voeg een kolom 'post_type' toe om prestaties per posttype "
            "te analyseren."
        )
        return

    analysis_df = (
        df
        .dropna(subset=["post_type"])
        .groupby("post_type", as_index=False)
        .agg(
            gemiddelde_views=("views", "mean"),
            gemiddelde_engagement=("engagement", "mean"),
            totaal_posts=("post_type", "count"),
        )
        .sort_values("gemiddelde_views", ascending=False)
    )

    if analysis_df.empty:
        return

    fig = px.bar(
        analysis_df,
        x="post_type",
        y="gemiddelde_views",
        color="gemiddelde_engagement",
        text="totaal_posts",
        title="Prestaties per posttype",
        color_continuous_scale=[
            "#dfe7df",
            "#7d9b88",
            "#084422",
        ],
    )

    fig.update_traces(
        texttemplate="%{text} posts",
        textposition="outside",
    )

    fig.update_layout(
        height=430,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="sofia-pro", color="#084422"),
        title_font_size=20,
        coloraxis_colorbar_title="Engagement %",
        xaxis_title="Posttype",
        yaxis_title="Gemiddelde views",
    )

    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        analysis_df.assign(
            gemiddelde_views=analysis_df["gemiddelde_views"].round(0),
            gemiddelde_engagement=analysis_df["gemiddelde_engagement"].round(1),
        ),
        use_container_width=True,
        hide_index=True,
    )


def render_tables(df: pd.DataFrame) -> None:
    columns = [
        "topic",
        "post_type",
        "likes",
        "views",
        "comments",
        "shares",
        "saves",
        "engagement",
    ]

    instagram = df[df["channel"] == "Instagram"]
    facebook = df[df["channel"] == "Facebook"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Instagram")
        st.dataframe(
            instagram[
                [column for column in columns if column in instagram.columns]
            ],
            use_container_width=True,
            hide_index=True,
            height=350,
        )

    with col2:
        st.subheader("Facebook")
        st.dataframe(
            facebook[
                [column for column in columns if column in facebook.columns]
            ],
            use_container_width=True,
            hide_index=True,
            height=350,
        )


def render_sidebar(df: pd.DataFrame) -> list[str]:
    st.sidebar.header("Filters")

    if "channel" not in df.columns:
        return []

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
        st.error(f"Fout bij ophalen van data: {error}")
        return
    except Exception as error:
        st.error(f"Onverwachte fout: {error}")
        return

    if posts_df.empty:
        st.warning("Geen data beschikbaar.")
        return

    selected_channels = render_sidebar(posts_df)

    if selected_channels:
        filtered_posts_df = posts_df[
            posts_df["channel"].isin(selected_channels)
        ]
    else:
        filtered_posts_df = posts_df.copy()

    if filtered_posts_df.empty:
        st.warning("Geen data beschikbaar voor de gekozen filters.")
        return

    render_header()
    render_metrics(filtered_posts_df)

    add_space()
    render_kpis(followers_df, filtered_posts_df)

    add_space()
    render_analysis(filtered_posts_df, followers_df)

    add_space()
    render_category_chart(filtered_posts_df)

    add_space()
    render_trend_chart(filtered_posts_df)

    add_space()
    render_post_type_analysis(filtered_posts_df)

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
