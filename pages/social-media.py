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
    page_title="Social media dashboard",
    page_icon="📱",
    layout="wide",
)

SHEET_ID = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"

GIDS = {
    "instagram": "0",
    "facebook": "847206611",
    "followers": "730161295",
}

BRAND_GREEN = "#084422"
LIGHT_GREEN = "#7d9b88"
BACKGROUND = "#f7f3ec"
TEXT_MUTED = "#6f766f"
RED = "#d64545"
POSITIVE = "#58a55c"

NUMERIC_COLUMNS = ["likes", "views", "comments", "shares", "saves"]
FOLLOWER_COLUMNS = ["instagram_followers", "facebook_followers"]

# ==========================================================
# STYLE
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

#MainMenu, footer, header {{
    visibility: hidden;
}}

section[data-testid="stSidebar"] {{
    background: #ffffff;
    border-right: 1px solid rgba(8, 68, 34, 0.06);
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

.analysis-wrapper,
.kpi-wrapper {{
    background: #ffffff;
    border-radius: 18px;
    border: 1px solid rgba(8, 68, 34, 0.07);
    box-shadow: 0 6px 18px rgba(8, 68, 34, 0.035);
}}

.analysis-wrapper {{
    padding: 26px 30px;
}}

.analysis-title {{
    color: {BRAND_GREEN};
    font-size: 22px;
    font-weight: 700;
    margin-bottom: 16px;
}}

.analysis-item {{
    color: {BRAND_GREEN};
    font-size: 16px;
    line-height: 1.55;
    margin-bottom: 10px;
}}

.kpi-wrapper {{
    padding: 24px;
    min-height: 145px;
}}

.kpi-label {{
    color: {TEXT_MUTED};
    font-size: 14px;
    margin-bottom: 18px;
    font-weight: 500;
}}

.kpi-value {{
    color: {BRAND_GREEN};
    font-size: 36px;
    font-weight: 700;
    line-height: 1;
}}

.kpi-growth {{
    margin-top: 14px;
    font-size: 15px;
    font-weight: 600;
}}

[data-testid="stMetric"] {{
    background: #ffffff;
    padding: 22px;
    border-radius: 18px;
    border: 1px solid rgba(8, 68, 34, 0.07);
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

[data-testid="stDataFrame"],
div[data-testid="stPlotlyChart"] {{
    background: #ffffff;
    border-radius: 18px !important;
    overflow: hidden;
    border: 1px solid rgba(8, 68, 34, 0.07);
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

def get_sheet_url(gid: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
        f"/export?format=csv&gid={gid}"
    )


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
        .str.replace("/", "_", regex=False)
    )
    return df


def to_number(series: pd.Series) -> pd.Series:
    return (
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
        .pipe(pd.to_numeric, errors="coerce")
        .fillna(0)
    )


def format_number(value: float | int) -> str:
    if pd.isna(value):
        return "-"

    return f"{int(round(value)):,}".replace(",", ".")


def format_percent(value: float) -> str:
    return f"{value:.1f}%".replace(".", ",")


def calculate_growth(current: float, previous: float) -> tuple[str, str]:
    if pd.isna(previous) or previous <= 0:
        return "0,0%", POSITIVE

    growth = (current - previous) / previous * 100
    arrow = "↓" if growth < 0 else "↑"
    color = RED if growth < 0 else POSITIVE

    return f"{arrow} {abs(growth):.1f}%".replace(".", ","), color


def apply_chart_style(fig, height: int = 420):
    fig.update_layout(
        height=height,
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        font=dict(family="sofia-pro", color=BRAND_GREEN),
        margin=dict(l=30, r=30, t=50, b=40),
    )
    return fig


def add_space() -> None:
    st.markdown('<div class="space"></div>', unsafe_allow_html=True)


# ==========================================================
# DATA LOADERS
# ==========================================================

@st.cache_data(ttl=600, show_spinner=False)
def fetch_sheet(sheet_gid: str) -> pd.DataFrame:
    response = requests.get(
        get_sheet_url(sheet_gid),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/csv, */*;q=0.1",
        },
        timeout=20,
    )

    response.raise_for_status()
    response.encoding = "utf-8"

    return normalize_columns(pd.read_csv(io.StringIO(response.text)))


@st.cache_data(ttl=600, show_spinner="Social media data laden...")
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


# ==========================================================
# CLEANING
# ==========================================================

def calculate_engagement(df: pd.DataFrame) -> pd.Series:
    required_columns = {"likes", "comments", "shares", "saves", "views"}

    if not required_columns.issubset(df.columns):
        return pd.Series(0, index=df.index)

    interactions = df["likes"] + df["comments"] + df["shares"] + df["saves"]

    engagement = interactions.div(df["views"].replace(0, pd.NA)) * 100

    return engagement.fillna(0).round(1)


def clean_posts_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    for column in NUMERIC_COLUMNS:
        df[column] = to_number(df[column]) if column in df.columns else 0

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    else:
        df["date"] = pd.NaT

    for column in ["topic", "post_type", "categorie", "channel"]:
        if column in df.columns:
            df[column] = df[column].fillna("Onbekend").astype(str).str.strip()
            df[column] = df[column].replace("", "Onbekend")

    df["engagement"] = calculate_engagement(df)

    return df.sort_values("date", na_position="last").reset_index(drop=True)


def clean_followers_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
        df = df.dropna(subset=["date"]).sort_values("date")
    else:
        df["date"] = pd.NaT

    for column in FOLLOWER_COLUMNS:
        df[column] = to_number(df[column]) if column in df.columns else 0

    return df.reset_index(drop=True)


# ==========================================================
# FILTERS
# ==========================================================

def render_sidebar(posts_df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filters")

    filtered_df = posts_df.copy()

    channels = sorted(filtered_df["channel"].dropna().unique().tolist())

    selected_channels = st.sidebar.multiselect(
        "Kanalen",
        options=channels,
        default=channels,
    )

    if selected_channels:
        filtered_df = filtered_df[filtered_df["channel"].isin(selected_channels)]

    if "post_type" in filtered_df.columns:
        post_types = sorted(filtered_df["post_type"].dropna().unique().tolist())

        selected_post_types = st.sidebar.multiselect(
            "Posttypes",
            options=post_types,
            default=post_types,
        )

        if selected_post_types:
            filtered_df = filtered_df[filtered_df["post_type"].isin(selected_post_types)]

    if "categorie" in filtered_df.columns:
        categories = sorted(filtered_df["categorie"].dropna().unique().tolist())

        selected_categories = st.sidebar.multiselect(
            "Categorieën",
            options=categories,
            default=categories,
        )

        if selected_categories:
            filtered_df = filtered_df[filtered_df["categorie"].isin(selected_categories)]

    if filtered_df["date"].notna().any():
        min_date = filtered_df["date"].min().date()
        max_date = filtered_df["date"].max().date()

        selected_dates = st.sidebar.date_input(
            "Periode",
            value=(min_date, max_date),
        )

        if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
            start_date, end_date = selected_dates

            filtered_df = filtered_df[
                filtered_df["date"].between(
                    pd.Timestamp(start_date),
                    pd.Timestamp(end_date),
                )
            ]

    return filtered_df


# ==========================================================
# KPI HELPERS
# ==========================================================

def get_latest_growth(df: pd.DataFrame, column: str) -> tuple[int, str, str]:
    if df.empty or column not in df.columns:
        return 0, "0,0%", POSITIVE

    values = df[column].dropna()

    if len(values) == 0:
        return 0, "0,0%", POSITIVE

    if len(values) == 1:
        return int(values.iloc[-1]), "0,0%", POSITIVE

    current = values.iloc[-1]
    previous = values.iloc[-2]
    growth, color = calculate_growth(current, previous)

    return int(current), growth, color


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


# ==========================================================
# RENDER
# ==========================================================

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
    avg_views = posts_df["views"].mean() if not posts_df.empty else 0
    avg_engagement = posts_df["engagement"].mean() if not posts_df.empty else 0
    total_views = posts_df["views"].sum() if not posts_df.empty else 0
    total_interactions = (
        posts_df[["likes", "comments", "shares", "saves"]].sum().sum()
        if not posts_df.empty
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Totaal posts", format_number(len(posts_df)))
    col2.metric("Gem. views", format_number(avg_views))
    col3.metric("Gem. engagement", format_percent(avg_engagement))
    col4.metric("Interacties", format_number(total_interactions))


def render_kpis(followers_df: pd.DataFrame, posts_df: pd.DataFrame) -> None:
    insta_followers, insta_growth, insta_color = get_latest_growth(
        followers_df,
        "instagram_followers",
    )

    facebook_followers, facebook_growth, facebook_color = get_latest_growth(
        followers_df,
        "facebook_followers",
    )

    avg_engagement = posts_df["engagement"].mean() if not posts_df.empty else 0

    recent_posts = posts_df.dropna(subset=["date"]).sort_values("date")

    if len(recent_posts) >= 2:
        current = recent_posts.iloc[-1]["engagement"]
        previous = recent_posts.iloc[-2]["engagement"]
        engagement_growth, engagement_color = calculate_growth(current, previous)
    else:
        engagement_growth, engagement_color = "0,0%", POSITIVE

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
            format_percent(avg_engagement),
            engagement_growth,
            engagement_color,
        )


def build_analysis_points(
    posts_df: pd.DataFrame,
    followers_df: pd.DataFrame,
) -> list[str]:
    if posts_df.empty:
        return ["Er is geen data beschikbaar voor analyse."]

    points = []

    total_posts = len(posts_df)
    total_views = posts_df["views"].sum()
    avg_engagement = posts_df["engagement"].mean()

    points.append(
        f"Er zijn {format_number(total_posts)} posts geanalyseerd met in totaal "
        f"{format_number(total_views)} views."
    )

    channel_views = posts_df.groupby("channel")["views"].sum().sort_values(ascending=False)

    if not channel_views.empty:
        points.append(
            f"{channel_views.index[0]} levert de meeste views op "
            f"({format_number(channel_views.iloc[0])} views)."
        )

    if {"post_type", "views", "engagement"}.issubset(posts_df.columns):
        post_type_stats = (
            posts_df.groupby("post_type")
            .agg(
                gemiddelde_views=("views", "mean"),
                gemiddelde_engagement=("engagement", "mean"),
                totaal_posts=("post_type", "count"),
            )
            .sort_values("gemiddelde_views", ascending=False)
        )

        if not post_type_stats.empty:
            best_views_type = post_type_stats["gemiddelde_views"].idxmax()
            best_engagement_type = post_type_stats["gemiddelde_engagement"].idxmax()

            points.append(
                f"{best_views_type} werkt het beste voor bereik, met gemiddeld "
                f"{format_number(post_type_stats.loc[best_views_type, 'gemiddelde_views'])} views."
            )

            points.append(
                f"{best_engagement_type} zorgt voor de hoogste betrokkenheid, "
                f"met gemiddeld "
                f"{format_percent(post_type_stats.loc[best_engagement_type, 'gemiddelde_engagement'])}."
            )

    if "topic" in posts_df.columns and not posts_df.empty:
        top_views_post = posts_df.sort_values("views", ascending=False).iloc[0]
        top_engagement_post = posts_df.sort_values("engagement", ascending=False).iloc[0]

        points.append(
            f"De best presterende post op views is '{top_views_post['topic']}' "
            f"met {format_number(top_views_post['views'])} views."
        )

        points.append(
            f"De hoogste engagement komt van '{top_engagement_post['topic']}' "
            f"met {format_percent(top_engagement_post['engagement'])}."
        )

    if "categorie" in posts_df.columns:
        category_counts = posts_df["categorie"].value_counts()

        if not category_counts.empty:
            points.append(
                f"De meest gebruikte categorie is '{category_counts.index[0]}' "
                f"met {format_number(category_counts.iloc[0])} posts."
            )

    points.append(
        f"De gemiddelde engagement over de geselecteerde data is "
        f"{format_percent(avg_engagement)}."
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
            f"Instagram heeft momenteel {format_number(insta_followers)} volgers "
            f"({insta_growth}); Facebook heeft {format_number(facebook_followers)} "
            f"volgers ({facebook_growth})."
        )

    return points


def render_analysis(posts_df: pd.DataFrame, followers_df: pd.DataFrame) -> None:
    points = build_analysis_points(posts_df, followers_df)

    html = """
    <div class="analysis-wrapper">
        <div class="analysis-title">Belangrijkste inzichten</div>
    """

    for point in points:
        html += f'<div class="analysis-item">• {point}</div>'

    html += "</div>"

    st.markdown(html, unsafe_allow_html=True)


def render_category_chart(df: pd.DataFrame) -> None:
    if "categorie" not in df.columns or df.empty:
        st.info("Geen categoriedata beschikbaar.")
        return

    category_counts = (
        df.groupby("categorie", dropna=False)
        .size()
        .reset_index(name="aantal_posts")
        .sort_values("aantal_posts", ascending=False)
    )

    fig = px.pie(
        category_counts,
        names="categorie",
        values="aantal_posts",
        hole=0.55,
        title="Categorieën overzicht",
        color_discrete_sequence=[
            BRAND_GREEN,
            "#3f6b53",
            LIGHT_GREEN,
            "#b6c5b9",
            "#dfe7df",
        ],
    )

    st.plotly_chart(apply_chart_style(fig), use_container_width=True)


def render_trend_chart(df: pd.DataFrame) -> None:
    if not {"date", "channel", "views"}.issubset(df.columns) or df.empty:
        st.info("Geen trenddata beschikbaar.")
        return

    trend = (
        df.dropna(subset=["date"])
        .groupby(["date", "channel"], as_index=False)
        .agg(
            views=("views", "sum"),
            engagement=("engagement", "mean"),
        )
        .sort_values("date")
    )

    if trend.empty:
        st.info("Geen geldige datums beschikbaar voor trendanalyse.")
        return

    metric = st.radio(
        "Trend metric",
        ["views", "engagement"],
        horizontal=True,
        format_func=lambda value: "Views" if value == "views" else "Engagement",
    )

    fig = px.line(
        trend,
        x="date",
        y=metric,
        color="channel",
        markers=True,
        title="Trend per kanaal",
        color_discrete_sequence=[BRAND_GREEN, LIGHT_GREEN],
    )

    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Views" if metric == "views" else "Engagement %",
    )

    st.plotly_chart(apply_chart_style(fig, height=380), use_container_width=True)


def render_post_type_analysis(df: pd.DataFrame) -> None:
    required_columns = {"post_type", "views", "engagement"}

    if not required_columns.issubset(df.columns) or df.empty:
        st.info("Voeg een kolom `post_type` toe om prestaties per posttype te analyseren.")
        return

    analysis_df = (
        df.groupby("post_type", as_index=False)
        .agg(
            gemiddelde_views=("views", "mean"),
            gemiddelde_engagement=("engagement", "mean"),
            totaal_posts=("post_type", "count"),
        )
        .sort_values("gemiddelde_views", ascending=False)
    )

    if analysis_df.empty:
        st.info("Geen posttype-data beschikbaar.")
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
            LIGHT_GREEN,
            BRAND_GREEN,
        ],
    )

    fig.update_traces(
        texttemplate="%{text} posts",
        textposition="outside",
    )

    fig.update_layout(
        coloraxis_colorbar_title="Engagement %",
        xaxis_title="Posttype",
        yaxis_title="Gemiddelde views",
    )

    st.plotly_chart(apply_chart_style(fig, height=430), use_container_width=True)

    display_df = analysis_df.copy()
    display_df["gemiddelde_views"] = display_df["gemiddelde_views"].round(0)
    display_df["gemiddelde_engagement"] = display_df["gemiddelde_engagement"].round(1)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


def render_top_posts(df: pd.DataFrame) -> None:
    if df.empty:
        return

    st.subheader("Top posts")

    col1, col2 = st.columns(2)

    table_columns = [
        "date",
        "channel",
        "topic",
        "post_type",
        "views",
        "engagement",
        "likes",
        "comments",
        "shares",
        "saves",
    ]

    available_columns = [column for column in table_columns if column in df.columns]

    with col1:
        st.write("Meeste views")
        st.dataframe(
            df.sort_values("views", ascending=False)[available_columns].head(10),
            use_container_width=True,
            hide_index=True,
            height=350,
        )

    with col2:
        st.write("Hoogste engagement")
        st.dataframe(
            df.sort_values("engagement", ascending=False)[available_columns].head(10),
            use_container_width=True,
            hide_index=True,
            height=350,
        )


def render_tables(df: pd.DataFrame) -> None:
    columns = [
        "date",
        "topic",
        "post_type",
        "categorie",
        "likes",
        "views",
        "comments",
        "shares",
        "saves",
        "engagement",
    ]

    col1, col2 = st.columns(2)

    for col, channel in zip([col1, col2], ["Instagram", "Facebook"]):
        channel_df = df[df["channel"] == channel]
        available_columns = [column for column in columns if column in channel_df.columns]

        with col:
            st.subheader(channel)

            if channel_df.empty:
                st.info(f"Geen {channel}-data voor de gekozen filters.")
            else:
                st.dataframe(
                    channel_df[available_columns].sort_values(
                        "date",
                        ascending=False,
                        na_position="last",
                    ),
                    use_container_width=True,
                    hide_index=True,
                    height=350,
                )


def render_follower_chart(followers_df: pd.DataFrame) -> None:
    if followers_df.empty or not {"date", *FOLLOWER_COLUMNS}.issubset(followers_df.columns):
        return

    follower_long = followers_df.melt(
        id_vars="date",
        value_vars=FOLLOWER_COLUMNS,
        var_name="Kanaal",
        value_name="Volgers",
    )

    follower_long["Kanaal"] = follower_long["Kanaal"].replace(
        {
            "instagram_followers": "Instagram",
            "facebook_followers": "Facebook",
        }
    )

    fig = px.line(
        follower_long,
        x="date",
        y="Volgers",
        color="Kanaal",
        markers=True,
        title="Volgersontwikkeling",
        color_discrete_sequence=[BRAND_GREEN, LIGHT_GREEN],
    )

    fig.update_layout(
        xaxis_title="Datum",
        yaxis_title="Volgers",
    )

    st.plotly_chart(apply_chart_style(fig, height=380), use_container_width=True)


# ==========================================================
# MAIN
# ==========================================================

def main() -> None:
    try:
        posts_df, followers_df = load_data()
    except requests.RequestException as error:
        st.error(f"Fout bij ophalen van data: {error}")
        return
    except Exception as error:
        st.error(f"Onverwachte fout: {error}")
        return

    if posts_df.empty:
        st.warning("Geen social media data beschikbaar.")
        return

    filtered_posts_df = render_sidebar(posts_df)

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
    render_follower_chart(followers_df)

    add_space()
    render_post_type_analysis(filtered_posts_df)

    add_space()
    render_top_posts(filtered_posts_df)

    add_space()
    render_tables(filtered_posts_df)

    csv = filtered_posts_df.to_csv(index=False).encode("utf-8")

    st.download_button(
        label="Download gefilterde data als CSV",
        data=csv,
        file_name="social_media_export.csv",
        mime="text/csv",
    )

    st.caption(
        f"{format_number(len(filtered_posts_df))} posts geladen · "
        "Social media dashboard"
    )


if __name__ == "__main__":
    main()
