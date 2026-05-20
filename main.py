import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="VDK Marketing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


SOCIAL_SHEET = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"
MEMBERS_SHEET = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"
NEWSLETTER_SHEET = "1seQjiFaLzEm7PZ2vTDeylSZKEXGqDl6FHe2l1nVPnfg"

FOLLOWERS_GID = "730161295"
MEMBERS_GID = "0"

BRAND_GREEN = "#084422"
BACKGROUND = "#f7f3ec"
CARD_BACKGROUND = "#ffffff"
TEXT_MUTED = "#6f766f"


def apply_styling() -> None:
    st.markdown(
        f"""
        <link rel="stylesheet" href="https://use.typekit.net/nap5xax.css">

        <style>
        html,
        body,
        [data-testid="stAppViewContainer"] {{
            background: {BACKGROUND};
            font-family: 'sofia-pro', sans-serif;
            color: {BRAND_GREEN};
        }}

        #MainMenu,
        footer,
        header {{
            visibility: hidden;
        }}

        .block-container {{
            padding: 42px 56px 56px 56px;
            max-width: 1500px;
        }}

        section[data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid rgba(8, 68, 34, 0.06);
        }}

        section[data-testid="stSidebar"] * {{
            color: {BRAND_GREEN} !important;
        }}

        [data-testid="stSidebarNav"]::before {{
            content: "VDK Marketing";
            display: block;
            font-size: 18px;
            font-weight: 600;
            margin: 12px 0 28px 10px;
            color: {BRAND_GREEN};
        }}

        [data-testid="stSidebarNav"] a {{
            background: transparent !important;
            border-radius: 10px;
            padding: 10px 12px;
            font-weight: 500;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(8, 68, 34, 0.05) !important;
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: rgba(8, 68, 34, 0.08) !important;
            color: {BRAND_GREEN} !important;
            font-weight: 700;
        }}

        .hero {{
            background: {CARD_BACKGROUND};
            padding: 38px 42px;
            border-radius: 22px;
            color: {BRAND_GREEN};
            margin-bottom: 38px;
            border: 1px solid rgba(8, 68, 34, 0.08);
            box-shadow: 0 8px 24px rgba(8, 68, 34, 0.04);
        }}

        .hero h1 {{
            color: {BRAND_GREEN};
            font-size: 42px;
            line-height: 1.15;
            margin: 0 0 10px 0;
            font-weight: 700;
        }}

        .hero p {{
            color: {TEXT_MUTED};
            font-size: 17px;
            max-width: 780px;
            line-height: 1.6;
            margin: 0;
        }}

        .hero .date {{
            margin-top: 22px;
            font-size: 14px;
            color: {TEXT_MUTED};
        }}

        [data-testid="stMetric"] {{
            background: {CARD_BACKGROUND};
            padding: 24px;
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
            font-size: 34px;
            font-weight: 700;
        }}

        [data-testid="stMetricDelta"] {{
            font-size: 14px;
            font-weight: 600;
        }}

        .section-title {{
            font-size: 22px;
            font-weight: 700;
            color: {BRAND_GREEN};
            margin-bottom: 22px;
            border-bottom: none;
            display: block;
        }}

        h1, h2, h3, h4 {{
            color: {BRAND_GREEN};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=600)
def load_csv(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return pd.read_csv(io.StringIO(response.text))
    except requests.RequestException as error:
        st.warning(f"Kon CSV niet laden: {error}")
        return pd.DataFrame()
    except pd.errors.ParserError as error:
        st.warning(f"Kon CSV niet verwerken: {error}")
        return pd.DataFrame()


@st.cache_data(ttl=600)
def load_json_sheet(url: str) -> pd.DataFrame:
    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except requests.RequestException as error:
        st.warning(f"Kon nieuwsbriefdata niet laden: {error}")
        return pd.DataFrame()
    except ValueError as error:
        st.warning(f"Kon JSON niet verwerken: {error}")
        return pd.DataFrame()


def clean_columns(data: pd.DataFrame) -> pd.DataFrame:
    data = data.copy()
    data.columns = data.columns.str.lower().str.strip()
    return data


def calculate_growth(current: float, previous: float) -> float:
    if pd.isna(previous) or previous == 0:
        return 0.0

    return round(((current - previous) / previous) * 100, 1)


def format_number(value: int | float) -> str:
    return f"{value:,.0f}".replace(",", ".")


def get_followers_kpis() -> dict[str, float]:
    url = (
        f"https://docs.google.com/spreadsheets/d/{SOCIAL_SHEET}"
        f"/export?format=csv&gid={FOLLOWERS_GID}"
    )

    followers = load_csv(url)

    default_kpis = {
        "instagram_followers": 0,
        "facebook_followers": 0,
        "instagram_growth": 0.0,
        "facebook_growth": 0.0,
    }

    if followers.empty:
        return default_kpis

    followers = clean_columns(followers)

    required_columns = ["instagram_followers", "facebook_followers"]
    missing_columns = set(required_columns) - set(followers.columns)

    if missing_columns:
        st.warning(f"Ontbrekende kolommen in volgersdata: {missing_columns}")
        return default_kpis

    for column in required_columns:
        followers[column] = pd.to_numeric(followers[column], errors="coerce")

    followers = followers.dropna(subset=required_columns)

    if len(followers) < 2:
        return default_kpis

    current = followers.iloc[-1]
    previous = followers.iloc[-2]

    return {
        "instagram_followers": int(current["instagram_followers"]),
        "facebook_followers": int(current["facebook_followers"]),
        "instagram_growth": calculate_growth(
            current["instagram_followers"],
            previous["instagram_followers"],
        ),
        "facebook_growth": calculate_growth(
            current["facebook_followers"],
            previous["facebook_followers"],
        ),
    }


def get_total_members() -> int:
    url = (
        f"https://docs.google.com/spreadsheets/d/{MEMBERS_SHEET}"
        f"/export?format=csv&gid={MEMBERS_GID}"
    )

    members = load_csv(url)

    if members.empty:
        return 0

    return len(members)


def get_average_open_rate() -> float:
    url = f"https://opensheet.elk.sh/{NEWSLETTER_SHEET}/Sheet1"
    newsletter = load_json_sheet(url)

    if newsletter.empty:
        return 0.0

    newsletter = clean_columns(newsletter)

    if "opens" not in newsletter.columns:
        st.warning("Kolom `opens` ontbreekt in nieuwsbriefdata.")
        return 0.0

    newsletter["opens"] = pd.to_numeric(
        newsletter["opens"],
        errors="coerce",
    )

    return round(newsletter["opens"].mean(skipna=True), 1)


def render_hero() -> None:
    today = datetime.now().strftime("%d-%m-%Y")

    st.markdown(
        f"""
        <div class="hero">
            <h1>VDK Marketing Dashboard</h1>
            <p>Live overzicht van de belangrijkste marketing KPI's.</p>
            <p class="date">Bijgewerkt op {today}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis() -> None:
    follower_kpis = get_followers_kpis()
    total_members = get_total_members()
    average_open_rate = get_average_open_rate()

    st.markdown(
        '<div class="section-title">Snelle statistieken</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Instagram volgers",
        format_number(follower_kpis["instagram_followers"]),
        f"{follower_kpis['instagram_growth']:+.1f}%",
    )

    col2.metric(
        "Facebook volgers",
        format_number(follower_kpis["facebook_followers"]),
        f"{follower_kpis['facebook_growth']:+.1f}%",
    )

    col3.metric(
        "Nieuwe members 2026",
        format_number(total_members),
    )

    col4.metric(
        "Gem. opens",
        f"{average_open_rate:.1f}",
    )


def main() -> None:
    apply_styling()
    render_hero()
    render_kpis()


if __name__ == "__main__":
    main()
