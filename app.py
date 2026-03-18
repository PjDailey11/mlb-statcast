import datetime
import warnings
import streamlit as st
import pandas as pd
import numpy as np
from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup
import charts

warnings.filterwarnings("ignore")

try:
    from pybaseball import cache as _pyball_cache
    _pyball_cache.enable()
except Exception:
    pass

st.set_page_config(
    page_title="MLB Statcast Analytics",
    page_icon="⚾",
    layout="wide",
)

SEASONS = list(range(2026, 2014, -1))
SEASON_DATES = {y: (datetime.date(y, 4, 1), datetime.date(y, 10, 1)) for y in SEASONS}


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batting(player_id: int, start: str, end: str) -> pd.DataFrame:
    return statcast_batter(start, end, player_id)


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_pitching(player_id: int, start: str, end: str) -> pd.DataFrame:
    return statcast_pitcher(start, end, player_id)


@st.cache_data(ttl=86400, show_spinner=False)
def search_player(last: str, first: str) -> pd.DataFrame:
    return playerid_lookup(last.strip(), first.strip())


def _metric_card(label: str, value) -> None:
    st.metric(label=label, value=str(value) if value is not None else "N/A")


def _render_batting(df: pd.DataFrame, player_name: str, start: str, end: str) -> None:
    st.header(f"{player_name} — Batting Analytics")
    st.caption(f"{start}  →  {end}")

    m = charts.compute_batting_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Avg Exit Velo", f"{m['avg_ev']} mph" if m["avg_ev"] else None)
    with c2:
        _metric_card("Max Exit Velo", f"{m['max_ev']} mph" if m["max_ev"] else None)
    with c3:
        _metric_card("Barrel %", f"{m['barrel_pct']}%" if m["barrel_pct"] is not None else None)
    with c4:
        _metric_card("xwOBA", m["xwoba"])

    st.divider()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.plotly_chart(charts.batting_ev_distribution(df), use_container_width=True)
    with r1c2:
        st.plotly_chart(charts.batting_launch_ev_scatter(df), use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.plotly_chart(charts.batting_spray_chart(df), use_container_width=True)
    with r2c2:
        st.plotly_chart(charts.batting_xwoba_trend(df), use_container_width=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.plotly_chart(charts.batting_pitch_types_faced(df), use_container_width=True)
    with r3c2:
        st.plotly_chart(charts.batting_hit_distance(df), use_container_width=True)


def _render_pitching(df: pd.DataFrame, player_name: str, start: str, end: str) -> None:
    st.header(f"{player_name} — Pitching Analytics")
    st.caption(f"{start}  →  {end}")

    m = charts.compute_pitching_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        _metric_card("Avg Velocity", f"{m['avg_velo']} mph" if m["avg_velo"] else None)
    with c2:
        _metric_card("Max Velocity", f"{m['max_velo']} mph" if m["max_velo"] else None)
    with c3:
        _metric_card("Avg Spin Rate", f"{m['avg_spin']} rpm" if m["avg_spin"] else None)
    with c4:
        _metric_card("Whiff %", f"{m['whiff_pct']}%" if m["whiff_pct"] is not None else None)

    st.divider()

    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.plotly_chart(charts.pitching_pitch_usage(df), use_container_width=True)
    with r1c2:
        st.plotly_chart(charts.pitching_velocity_by_type(df), use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.plotly_chart(charts.pitching_movement_profile(df), use_container_width=True)
    with r2c2:
        st.plotly_chart(charts.pitching_spin_rate(df), use_container_width=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.plotly_chart(charts.pitching_release_point(df), use_container_width=True)
    with r3c2:
        st.plotly_chart(charts.pitching_velocity_trend(df), use_container_width=True)


# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚾ Player Search")

    col_a, col_b = st.columns(2)
    first_input = col_a.text_input("First name", value="Shohei", placeholder="First name")
    last_input = col_b.text_input("Last name", value="Ohtani", placeholder="Last name")

    if st.button("Search", type="primary", use_container_width=True):
        with st.spinner("Searching…"):
            try:
                results = search_player(last_input, first_input)
                st.session_state["player_results"] = results
                st.session_state.pop("player_id", None)
            except Exception as e:
                st.error(str(e))

    player_id = None
    player_name = ""

    if "player_results" in st.session_state:
        res = st.session_state["player_results"]
        if res is not None and not res.empty:
            valid = res[res["key_mlbam"].notna() & (res["key_mlbam"].astype(float) > 0)]
            if valid.empty:
                st.warning("No players found. Check spelling.")
            else:
                options = {}
                for _, r in valid.iterrows():
                    born = int(r["mlb_played_first"]) if pd.notna(r.get("mlb_played_first")) else "?"
                    label = f"{r['name_first']} {r['name_last']} (born {born}, ID {int(r['key_mlbam'])})"
                    options[label] = int(r["key_mlbam"])
                chosen = st.selectbox("Select player", list(options.keys()), label_visibility="collapsed")
                player_id = options[chosen]
                player_name = chosen.split(" (")[0]
                st.session_state["player_id"] = player_id
                st.session_state["player_name"] = player_name
        else:
            st.warning("No players found. Check spelling.")

    st.divider()

    mode = st.radio("Analytics Mode", ["Batting", "Pitching"],
                    horizontal=True, disabled=(player_id is None))

    st.divider()

    st.markdown("##### Date Range")
    season_options = ["Custom"] + [str(y) for y in SEASONS]
    season = st.selectbox("Season shortcut", season_options)

    if season != "Custom":
        default_start, default_end = SEASON_DATES[int(season)]
    else:
        default_start = datetime.date(2024, 4, 1)
        default_end = datetime.date(2024, 10, 1)

    col_s, col_e = st.columns(2)
    start_date = col_s.date_input("Start", value=default_start)
    end_date = col_e.date_input("End", value=default_end)

    st.divider()

    load = st.button(
        "⚡ Load Data",
        type="primary",
        disabled=(player_id is None),
        use_container_width=True,
    )

# ── MAIN PANEL ───────────────────────────────────────────────────────────────
if load and player_id:
    start_str = str(start_date)
    end_str = str(end_date)

    with st.spinner(f"Fetching {mode.lower()} data…"):
        try:
            if mode == "Batting":
                df = fetch_batting(player_id, start_str, end_str)
            else:
                df = fetch_pitching(player_id, start_str, end_str)
        except Exception as e:
            st.error(f"Error fetching data: {e}")
            df = pd.DataFrame()

    if df is None or df.empty:
        st.warning(
            "No data returned. Try a different date range or check the player's role."
        )
    else:
        if mode == "Batting":
            _render_batting(df, player_name, start_str, end_str)
        else:
            _render_pitching(df, player_name, start_str, end_str)

elif not load:
    st.markdown("## ⚾ MLB Statcast Analytics")
    st.info("Search for a player in the sidebar and click **⚡ Load Data** to begin.")
