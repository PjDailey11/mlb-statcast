# MLB Statcast Analytics App — Design Spec
**Date:** 2026-03-18
**Status:** Approved (v2 — post spec review)

---

## Overview

A focused, single-player MLB Statcast analytics dashboard built with Python Streamlit and Plotly. Users search for any player by name, select a season and/or date range, toggle between batting and pitching modes (with two-way player support), and view 6 curated charts per mode. Deployable to Streamlit Cloud with no backend beyond pybaseball.

---

## Architecture

Two files:

```
mlb-statcast/
├── app.py          # UI, session state, data fetching, layout
├── charts.py       # All Plotly chart-building functions (pure, no Streamlit)
├── requirements.txt
└── .streamlit/
    └── config.toml # Dark theme
```

`app.py` owns the Streamlit page, sidebar controls, caching, and chart orchestration.
`charts.py` owns every chart function — takes a DataFrame, returns a `go.Figure`. No Streamlit imports in `charts.py`.

---

## Sidebar (`app.py`)

### Player Search
- First + last name text inputs
- "Search" button → calls `pybaseball.playerid_lookup(last, first)`
- Results stored in `st.session_state["player_results"]`
- Selectbox renders each result as `"{first} {last} (born {mlb_played_first}, ID: {key_mlbam})"` to disambiguate players with identical names
- Only rows where `key_mlbam` is a valid positive integer are shown

### Analytics Mode
- `st.radio(["Batting", "Pitching"])`, always visible once a player is selected
- Defaults to **Batting** on initial player load
- Two-way player support: both modes are always available for any player — the app fetches whichever dataset the toggle selects; no pre-checking of which modes have data. If data comes back empty, the empty-state warning handles it.

### Date Range
- **Season dropdown** (2015–2026): selecting a season sets `start_date = April 1, <year>` and `end_date = October 1, <year>` in session state
- **Start / End date inputs**: pre-filled by season selection; user may override freely at any time
- No coupling between the two — changing dates after selecting a season is valid and takes precedence; the season dropdown does not reset
- The last-set values of start/end are always what gets passed to the fetch function

### Load Data Button
- Disabled until a player is selected (`player_id` in session state)
- **Pressing it is always required to trigger a fetch** — changing season/dates does not auto-reload
- On press: calls the appropriate cached fetch function with current `(player_id, start_date, end_date)`
- Subsequent presses with different dates produce independent cache entries (cache keyed on all three arguments automatically by `@st.cache_data`)

---

## Data Fetching (`app.py`)

```python
@st.cache_data(ttl=3600)
def fetch_batting(player_id: int, start: str, end: str) -> pd.DataFrame:
    return statcast_batter(start, end, player_id)

@st.cache_data(ttl=3600)
def fetch_pitching(player_id: int, start: str, end: str) -> pd.DataFrame:
    return statcast_pitcher(start, end, player_id)
```

`@st.cache_data` keys on all function arguments by default — `(player_id, start, end)` is the full cache key. No manual key management needed.

---

## Main Panel (`app.py`)

- Header: `"{player_name} — {mode} Analytics"`
- Subtitle: `"{start_date} to {end_date}"`
- 4 metric stat cards (top row)
- Chart grid: 2 columns × 2 rows (4 charts) + 2 columns × 1 row (2 charts) = **6 charts**

---

## Error Handling

| Condition | Behaviour |
|-----------|-----------|
| `playerid_lookup` raises exception | `st.error(str(e))` |
| No players found | `st.warning("No players found. Check spelling.")` |
| `statcast_batter/pitcher` raises exception | `st.error(str(e))` |
| Returned DataFrame is `None` or empty | `st.warning("No data for this player and date range. Try widening the date range.")` — charts skipped entirely |
| Specific column missing (e.g. `barrel`) | That metric card shows `"N/A"`; chart renders without that feature (e.g. no barrel zone overlay) |

---

## Charts — Batting Mode (`charts.py`)

All charts use: background `#0d1117`, 3 axis ticks max, legend rendered outside plot area, subtitle line above each chart.

### Metric Cards
| Metric | Column | Fallback |
|--------|--------|---------|
| Avg Exit Velocity | `launch_speed` mean | N/A |
| Max Exit Velocity | `launch_speed` max | N/A |
| Barrel % | `barrel` sum / batted balls count × 100 | N/A if column absent |
| xwOBA | `estimated_woba_using_speedangle` mean | N/A |

### Chart 1 — Exit Velocity Distribution
- Histogram of `launch_speed`, bin width 2 mph
- Vertical dashed line: mean EV (orange, labelled)
- Vertical dotted line: 95 mph threshold (red, labelled)
- X-axis: "Exit Velocity (mph)", Y-axis: "Batted Balls"

### Chart 2 — Launch Angle vs Exit Velocity
- Scatter: `launch_angle` (x) vs `launch_speed` (y)
- Color by `events`: HR `#f87171`, XBH (double/triple) `#fb923c`, Single `#4ade80`, Out `#1e293b` with `#475569` border
- Sweet spot zone: dashed rect at 8°–32° x-axis, ≥95 mph y-axis, fill `rgba(34,197,94,0.05)`
- Zone label: sits to the **right of the chart area** at the zone's midpoint height, connected by a short dashed callout line — not inside the plot
- X ticks: −20°, 10°, 40°. Y ticks: 70, 95, 115

### Chart 3 — Spray Chart
- Transform: `hc_x_centered = hc_x - 125.42`, `hc_y_centered = 198.27 - hc_y`
- Field overlay drawn with Plotly `add_shape` / `add_trace` (no external asset):
  - Foul lines: two diagonal lines from origin
  - Outfield arc: scatter trace following a quarter-circle at ~380 ft radius
  - Infield diamond: polygon shape
- Dot colors: HR `#f87171`, Hit (single/double/triple) `#4ade80`, Out `#475569`
- HR marker glow: `marker=dict(line=dict(color="#f87171", width=3))` with larger size
- Legend outside plot, bottom

### Chart 4 — Rolling xwOBA Trend
- Filter to rows where `estimated_woba_using_speedangle` is not null (these are plate appearance rows)
- Sort by `game_date`; compute 30-PA rolling mean
- Reference line: `y=0.320`, labelled `"Lg Avg (~.320)"` (hardcoded constant; represents approximate MLB average xwOBA across Statcast era)
- X-axis: dates, Y-axis: "xwOBA"

### Chart 5 — Pitch Types Faced
- Donut chart of `pitch_type` value counts
- Map pitch codes to human names: `FF→4-Seam FB`, `SL→Slider`, `CH→Changeup`, `SI→Sinker`, `CU→Curveball`, `FC→Cutter`, `FS→Splitter`, others shown as-is
- Labels outside the donut

### Chart 6 — Hit Distance by Outcome
- Box plot: `hit_distance_sc` grouped by `events`
- Filter to `events` in `[single, double, triple, home_run]` only
- X categories in that order; color matches outcome color scheme above

---

## Charts — Pitching Mode (`charts.py`)

### Metric Cards
| Metric | Column | Formula | Fallback |
|--------|--------|---------|---------|
| Avg Velocity | `release_speed` | mean | N/A |
| Max Velocity | `release_speed` | max | N/A |
| Avg Spin Rate | `release_spin_rate` | mean | N/A |
| Whiff % | `description` | `swinging_strike` rows / all non-null rows × 100 | N/A |

### Chart 1 — Pitch Type Usage
- Donut chart of `pitch_type` value counts, same label mapping as batting Chart 5

### Chart 2 — Velocity by Pitch Type
- Violin + embedded box: `release_speed` (y) by pitch type label (x)
- One color per pitch type (Plotly qualitative D3 palette)

### Chart 3 — Movement Profile
- Scatter: `pfx_x * 12` (horizontal, inches) vs `pfx_z * 12` (vertical, inches)
- Color by pitch type
- Zero-line crosshairs: `add_hline(y=0)` + `add_vline(x=0)`, both `#334155`
- Axis ranges: x −24 to 24 in, y −20 to 30 in
- Label: "Horizontal Break (in, catcher's POV)" / "Vertical Break (in)"

### Chart 4 — Spin Rate by Pitch Type
- Box plot: `release_spin_rate` by pitch type label
- Same color palette as Chart 2

### Chart 5 — Release Point
- Scatter: `release_pos_x` (x) vs `release_pos_z` (y), color by pitch type
- Label: "Horizontal Release (ft)" / "Vertical Release (ft)"

### Chart 6 — Velocity Trend
- Group by `game_date` + pitch type → daily mean `release_speed`
- Multi-line chart, one line per pitch type
- X-axis: dates, Y-axis: "Avg Velocity (mph)"

---

## Aesthetic System

- Background: `#0d1117`
- Plot background: `#0d1117`
- Grid lines: `#1a2332` (barely visible), horizontal only where possible
- Axis lines/ticks: `#2d3f52` / `#475569`
- Tick label color: `#475569`
- Axis title color: `#64748b`
- Outcome colors: HR `#f87171` · XBH `#fb923c` · Single `#4ade80` · Out `#1e293b` + `#475569` border
- Pitch-type colors: Plotly `px.colors.qualitative.D3`
- Font: system-ui / monospace for tick values
- All annotation text placed **outside** the data area; callout lines used where a label must point into the plot

---

## Deployment — Streamlit Cloud

1. Create a GitHub repo and push all files
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo
3. Set main file to `app.py`
4. No secrets or environment variables required — pybaseball fetches public MLB Statcast data
5. `.streamlit/config.toml` dark theme is committed to the repo and picked up automatically

---

## Out of Scope

- Player comparison (two players side-by-side)
- Percentile rankings vs league
- Pitch-by-pitch data tables
- Authentication or user accounts
