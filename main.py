import io
from datetime import datetime

import pandas as pd
import requests
import streamlit as st


# Page config -------------------------------------------------------------

st.set_page_config(
    page_title="VDK Marketing Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Constants ---------------------------------------------------------------

SOCIAL_SHEET = "1L-KVqx5Bg5Y18PiqncQLggX3oKpeMHtqmRnsmJ5Qziw"
MEMBERS_SHEET = "1snBY34YPGix5KpgOQ45aq4obQpmHirEt9Pg9I8DrE_0"
NEWSLETTER_SHEET = "1seQjiFaLzEm7PZ2vTDeylSZKEXGqDl6FHe2l1nVPnfg"

FOLLOWERS_GID = "730161295"
MEMBERS_GID = "0"

BRAND_GREEN = "#084422"
BACKGROUND = "#f4efe6"


# Styling -----------------------------------------------------------------

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
        }}

        #MainMenu,
        footer,
        header {{
            visibility: hidden;
        }}

        .block-container {{
            padding: 35px 55px 55px 55px;
            max-width: 1800px;
        }}

        section[data-testid="stSidebar"] {{
            background: white;
            border-right: 1px solid rgba(8, 68, 34, 0.08);
            padding-top: 25px;
        }}

        section[data-testid="stSidebar"] * {{
            color: {BRAND_GREEN} !important;
        }}

        [data-testid="stSidebarNav"] {{
            padding-top: 20px;
        }}

        [data-testid="stSidebarNav"]::before {{
            content: "VDK Marketing";
            display: block;
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 30px;
            padding-left: 10px;
            color: {BRAND_GREEN};
        }}

        [data-testid="stSidebarNav"] a {{
            background: #f8f8f8 !important;
            border: 1px solid rgba(8, 68, 34, 0.08);
            border-radius: 14px;
            padding: 12px 14px;
            transition: 0.2s;
        }}

        [data-testid="stSidebarNav"] a:hover {{
            background: rgba(8, 68, 34, 0.06) !important;
            border: 1px solid rgba(8, 68, 34, 0.15);
        }}

        [data-testid="stSidebarNav"] a[aria-current="page"] {{
            background: {BRAND_GREEN} !important;
            color: white !important;
            font-weight: 700;
        }}

        .hero {{
            background: linear-gradient(135deg, {BRAND_GREEN} 0%, #0f5f33 100%);
            padding: 60px;
            border-radius: 34px;
            color: white;
            margin-bottom: 50px;
            box-shadow: 0 12px 30px rgba(8, 68, 34, 0.15);
        }}

        .hero h1 {{
            color: white;
            font-size: 64px;
            margin: 0 0 16px 0;
        }}

        .hero p {{
            font-size: 20px;
            opacity: 0.95;
            max-width: 900px;
            line-height: 1.8;
        }}

        .hero .date {{
            margin-top: 30px;
            font-size: 16px;
            opacity: 0.85;
        }}

        [data-testid="stMetric"] {{
            background: white;
            padding: 28px;
            border-radius: 24px;
            border: 1px solid rgba(8, 68, 34, 0.05);
            box-shadow: 0 10px 25px rgba(8, 68, 34, 0.05);
            transition: 0.2s;
        }}

        [data-testid="stMetric"]:hover {{
            transform: translateY(-2px);
            box-shadow: 0 15px 35px rgba(8, 68, 34, 0.1);
        }}

        .section-title {{
            font-size: 28px;
            font-weight: 700;
            color: {BRAND_GREEN};
            margin-bottom: 25px;
            padding-bottom: 12px;
            border-bottom: 3px solid {BRAND_GREEN};
            display: inline-block;
        }}

        h1, h2, h3, h4 {{
            color: {BRAND_GREEN};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# Data helpers ------------------------------------------------------------

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


# KPI calculations --------------------------------------------------------

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

    # AANGEPAST VAN open_rate NAAR opens
    if "opens" not in newsletter.columns:
        st.warning("Kolom `opens` ontbreekt in nieuwsbriefdata.")
        return 0.0

    newsletter["opens"] = pd.to_numeric(
        newsletter["opens"],
        errors="coerce",
    )

    return round(newsletter["opens"].mean(skipna=True), 1)


# Layout ------------------------------------------------------------------

def render_hero() -> None:
    today = datetime.now().strftime("%d-%m-%Y")

    st.markdown(
        f"""
        <div class="hero">
            <h1>VDK Marketing Dashboard</h1>
            <p>Live overzicht van de belangrijkste marketing KPI's.</p>
            <p class="date">{today}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpis() -> None:
    follower_kpis = get_followers_kpis()
    total_members = get_total_members()
    average_open_rate = get_average_open_rate()

    st.markdown(
        '<div class="section-title">📈 Snelle statistieken</div>',
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


# App ---------------------------------------------------------------------

def main() -> None:
    apply_styling()
    render_hero()
    render_kpis()


if __name__ == "__main__":
    main()
