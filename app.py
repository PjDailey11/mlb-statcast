import datetime
import warnings
import streamlit as st
import pandas as pd
from pybaseball import statcast_batter, statcast_pitcher, chadwick_register  # type: ignore
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

def _inject_css() -> None:
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,300;0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Base ──────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
}
.stApp {
    background: #07090f;
}

/* ── Sidebar ───────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0b0f1a 0%, #07090f 100%) !important;
    border-right: 1px solid #1a2235 !important;
}
[data-testid="stSidebar"] .stMarkdown h3 {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    color: #3b82f6 !important;
    margin-bottom: 0.75rem !important;
}
[data-testid="stSidebar"] hr {
    border-color: #1a2235 !important;
    margin: 1rem 0 !important;
}

/* ── Selectbox & inputs ────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-testid="stTextInput"] > div > div > input {
    background: #0d1117 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    font-size: 0.875rem !important;
    color: #e2e8f0 !important;
    transition: border-color 0.15s ease !important;
}
[data-testid="stSelectbox"] > div > div:focus-within,
[data-testid="stTextInput"] > div > div > input:focus {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}

/* ── Date inputs ───────────────────────────── */
[data-testid="stDateInput"] input {
    background: #0d1117 !important;
    border: 1px solid #1e2d45 !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
}

/* ── Buttons ───────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.825rem !important;
    letter-spacing: 0.03em !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%) !important;
    border: none !important;
    box-shadow: 0 0 24px rgba(59,130,246,0.25) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 32px rgba(59,130,246,0.45) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:disabled {
    opacity: 0.35 !important;
    box-shadow: none !important;
}

/* ── Radio ─────────────────────────────────── */
[data-testid="stRadio"] label {
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    color: #94a3b8 !important;
}

/* ── Section label ─────────────────────────── */
[data-testid="stSidebar"] .stMarkdown h5 {
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
    margin-bottom: 0.5rem !important;
}

/* ── Main panel header ─────────────────────── */
.stApp [data-testid="stVerticalBlock"] > div:first-child h2 {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.04em !important;
    background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 100%);
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    background-clip: text !important;
}

/* ── Metric cards ──────────────────────────── */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0d1521 0%, #0a1018 100%) !important;
    border: 1px solid #1a2235 !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    position: relative !important;
    overflow: hidden !important;
}
[data-testid="stMetric"]::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important; left: 0 !important;
    right: 0 !important; height: 2px !important;
    background: linear-gradient(90deg, #3b82f6, #06b6d4) !important;
    border-radius: 12px 12px 0 0 !important;
}
[data-testid="stMetricLabel"] p {
    font-size: 0.65rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: #475569 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
    font-weight: 700 !important;
    letter-spacing: -0.03em !important;
    color: #f1f5f9 !important;
    font-family: 'Inter', sans-serif !important;
}

/* ── Chart containers ──────────────────────── */
[data-testid="stPlotlyChart"] {
    background: #0d1117 !important;
    border: 1px solid #1a2235 !important;
    border-radius: 12px !important;
    padding: 0.25rem !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stPlotlyChart"]:hover {
    border-color: #1e2d45 !important;
}

/* ── Divider ───────────────────────────────── */
[data-testid="stHorizontalBlock"] + hr,
hr {
    border-color: #1a2235 !important;
}

/* ── Info / warning boxes ──────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-width: 1px !important;
    font-size: 0.875rem !important;
}

/* ── Caption ───────────────────────────────── */
.stApp .stCaption p {
    font-size: 0.75rem !important;
    color: #475569 !important;
    letter-spacing: 0.04em !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* ── Spinner ───────────────────────────────── */
[data-testid="stSpinner"] p {
    font-size: 0.8rem !important;
    color: #475569 !important;
}

/* ── Scrollbar ─────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #07090f; }
::-webkit-scrollbar-thumb { background: #1a2235; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #1e2d45; }
</style>
""", unsafe_allow_html=True)

_inject_css()

SEASONS = list(range(2026, 2014, -1))
SEASON_DATES = {y: (datetime.date(y, 4, 1), datetime.date(y, 10, 1)) for y in SEASONS}

BATTING_COLS = [
    "game_date", "launch_speed", "launch_angle", "events",
    "hc_x", "hc_y", "hit_distance_sc",
    "estimated_woba_using_speedangle", "barrel", "pitch_type",
]
PITCHING_COLS = [
    "game_date", "pitch_type", "release_speed", "release_spin_rate",
    "pfx_x", "pfx_z", "release_pos_x", "release_pos_z", "description",
]


@st.cache_resource
def load_player_registry():
    """Shared singleton — built once, never copied. Returns (options_list, id_map)."""
    df = chadwick_register()
    df = df[
        df["key_mlbam"].notna() &
        (df["key_mlbam"].astype(float) > 0) &
        df["mlb_played_first"].notna() &
        (df["mlb_played_last"].fillna(2026).astype(float) >= 2015)
    ].copy()
    df["key_mlbam"] = df["key_mlbam"].astype(int)
    df["name_first"] = df["name_first"].fillna("").str.strip().str.title()
    df["name_last"] = df["name_last"].fillna("").str.strip().str.title()
    df["display"] = df["name_first"] + " " + df["name_last"]
    df = df.sort_values("display").reset_index(drop=True)
    options = [""] + df["display"].tolist()
    id_map = dict(zip(df["display"], df["key_mlbam"]))
    return options, id_map


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_batting(player_id: int, start: str, end: str) -> pd.DataFrame:
    df = statcast_batter(start, end, player_id)
    if df is not None and not df.empty:
        df = df[[c for c in BATTING_COLS if c in df.columns]]
    return df


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_pitching(player_id: int, start: str, end: str) -> pd.DataFrame:
    df = statcast_pitcher(start, end, player_id)
    if df is not None and not df.empty:
        df = df[[c for c in PITCHING_COLS if c in df.columns]]
    return df


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
    st.markdown("### STATCAST")

    try:
        player_options, player_id_map = load_player_registry()
    except Exception as e:
        st.error(f"Could not load player list: {e}")
        player_options, player_id_map = [""], {}

    player_id = None
    player_name = ""

    chosen = st.selectbox(
        "Search player",
        player_options,
        index=0,
        placeholder="Type a name, e.g. Ohtani…",
        label_visibility="collapsed",
    )

    if chosen:
        player_id = player_id_map.get(chosen)
        player_name = chosen
        st.session_state["player_id"] = player_id
        st.session_state["player_name"] = player_name
    else:
        st.session_state.pop("player_id", None)
        st.session_state.pop("player_name", None)

    st.divider()

    mode = st.radio("Analytics Mode", ["Batting", "Pitching"],
                    horizontal=True, disabled=(st.session_state.get("player_id") is None))

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
        disabled=(st.session_state.get("player_id") is None),
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
    st.markdown("""
<div style="
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    min-height: 60vh; text-align: center; gap: 1.5rem;
">
  <div style="
      font-size: 3rem; font-weight: 800; letter-spacing: -0.05em; line-height: 1.1;
      background: linear-gradient(135deg, #f1f5f9 0%, #3b82f6 60%, #06b6d4 100%);
      -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
  ">MLB Statcast<br>Analytics</div>
  <div style="font-size: 0.9rem; color: #475569; max-width: 340px; line-height: 1.6;">
      Search for any MLB player in the sidebar, choose a season and date range,<br>
      then click <strong style="color: #3b82f6;">⚡ Load Data</strong> to explore their Statcast metrics.
  </div>
  <div style="
      display: flex; gap: 1.5rem; margin-top: 0.5rem;
      font-size: 0.7rem; font-weight: 600; letter-spacing: 0.1em;
      text-transform: uppercase; color: #1e2d45;
  ">
      <span>Exit Velocity</span><span>·</span>
      <span>Spray Charts</span><span>·</span>
      <span>Pitch Movement</span><span>·</span>
      <span>xwOBA Trends</span>
  </div>
</div>
""", unsafe_allow_html=True)
