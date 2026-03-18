# MLB Statcast Analytics

A single-player MLB Statcast analytics dashboard built with Python, Streamlit, and Plotly. Search any MLB player, select a season or custom date range, and explore 6 curated batting or pitching charts powered by real Statcast data.

**Live app:** [share.streamlit.io](https://share.streamlit.io) *(deploy instructions below)*

---

## Features

### Player Search
- **Live autocomplete** — type any part of a player's name and matching MLB players appear instantly, filtered from a registry of 4,000+ Statcast-era players
- **Two-way player support** — both Batting and Pitching modes are always available for any player (e.g. Shohei Ohtani); the app fetches whichever dataset the mode toggle selects

### Batting Mode — 6 Charts
| Chart | Description |
|-------|-------------|
| Exit Velocity Distribution | Histogram with mean EV and 95 mph threshold markers |
| Launch Angle vs Exit Velocity | Scatter plot colored by outcome (HR / XBH / Single / Out) with sweet spot zone overlay |
| Spray Chart | Field overlay showing batted ball locations, colored by outcome |
| Rolling xwOBA Trend | 30-PA rolling mean with MLB average reference line |
| Pitch Types Faced | Donut chart of pitch mix seen |
| Hit Distance by Outcome | Box plot of hit distance grouped by single / double / triple / HR |

### Pitching Mode — 6 Charts
| Chart | Description |
|-------|-------------|
| Pitch Type Usage | Donut chart of pitch mix thrown |
| Velocity by Pitch Type | Violin + box plot of release speed per pitch type |
| Movement Profile | Horizontal vs vertical break scatter, colored by pitch type |
| Spin Rate by Pitch Type | Box plot of spin rate per pitch type |
| Release Point | Horizontal vs vertical release position scatter |
| Velocity Trend | Daily mean velocity per pitch type over the selected date range |

### Metric Cards
- **Batting:** Avg Exit Velocity · Max Exit Velocity · Barrel % · xwOBA
- **Pitching:** Avg Velocity · Max Velocity · Avg Spin Rate · Whiff %

### Date Range Controls
- Season shortcut dropdown (2015–2026) pre-fills April 1 → October 1
- Manual start/end date override — season dropdown and date inputs are fully independent

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| UI / App framework | [Streamlit](https://streamlit.io) ≥ 1.32 |
| Data source | [pybaseball](https://github.com/jldbc/pybaseball) ≥ 2.2.7 (Baseball Savant / Statcast) |
| Charts | [Plotly](https://plotly.com/python/) ≥ 5.18 |
| Data processing | [pandas](https://pandas.pydata.org/) ≥ 2.0, [NumPy](https://numpy.org/) ≥ 1.24 |
| Testing | [pytest](https://pytest.org/) ≥ 8.0 |
| Deployment | [Streamlit Cloud](https://streamlit.io/cloud) |

---

## Project Structure

```
mlb-statcast/
├── app.py              # UI, session state, data fetching, sidebar, layout
├── charts.py           # All Plotly chart functions (pure: DataFrame → Figure)
├── requirements.txt
├── .streamlit/
│   └── config.toml     # Dark theme configuration
└── tests/
    ├── conftest.py     # Shared pytest fixtures (batting_df, pitching_df)
    └── test_charts.py  # 23 tests covering all chart and metric functions
```

**Architecture principle:** `app.py` owns everything Streamlit; `charts.py` owns every chart — no Streamlit imports in `charts.py`. Chart functions are pure: they take a DataFrame and return a `go.Figure`.

---

## Local Setup

### Prerequisites
- Python 3.9+
- pip

### Install

```bash
git clone https://github.com/PjDailey11/mlb-statcast.git
cd mlb-statcast
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

On first launch, pybaseball downloads and caches the MLB player registry (~10 MB). Subsequent launches are instant.

---

## Usage

1. **Search for a player** — type a last name (e.g. `Ohtani`) or full name (e.g. `Shohei Ohtani`) in the sidebar search box. Matching MLB players appear in the dropdown below.
2. **Select Analytics Mode** — choose Batting or Pitching. Both modes are always available regardless of player position.
3. **Set a date range** — pick a season from the shortcut dropdown, or set custom start/end dates.
4. **Click ⚡ Load Data** — the app fetches Statcast data and renders all 6 charts and 4 metric cards.
5. **Adjust and reload** — change dates or switch modes, then click Load Data again. Each unique `(player, start, end)` combination is cached for 1 hour.

---

## Caching Strategy

| Cache | TTL | What |
|-------|-----|------|
| `@st.cache_resource` | Permanent (per server process) | MLB player registry from `chadwick_register()` — shared singleton, never copied |
| `@st.cache_data(ttl=3600)` | 1 hour | Statcast batting/pitching DataFrames per `(player_id, start, end)` |
| pybaseball local cache | Persistent on disk | Raw CSV responses from Baseball Savant |

---

## Performance Notes

- Fetched DataFrames are immediately trimmed from ~90 columns to the ~10 columns each mode actually uses — reducing memory, cache size, and chart render time.
- Scatter plots (Launch Angle vs EV, Spray Chart) and violin plots (Velocity by Pitch Type) are sampled to ≤ 1,000 points. A full season can contain 2,000+ pitches; the visual difference at 1,000 points is imperceptible.
- The player registry is loaded once per server process via `@st.cache_resource` — zero copy overhead on every subsequent rerun.

---

## Running Tests

```bash
pytest tests/ -v
```

23 tests cover:
- All 12 chart functions (batting + pitching)
- All 4 metric computation helpers (`compute_batting_metrics`, `compute_pitching_metrics`)
- Data helpers (`transform_spray_coords`)
- Edge cases: empty DataFrames, missing columns, all-NaN columns

Tests use seeded synthetic fixtures (`batting_df`, `pitching_df`) in `tests/conftest.py` — no network calls required.

---

## Deploying to Streamlit Cloud

1. Fork or push this repo to GitHub (already done: `github.com/PjDailey11/mlb-statcast`)
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select the `mlb-statcast` repo → set main file path to `app.py`
4. Click **Deploy**

No secrets or environment variables are required. pybaseball fetches public MLB Statcast data directly from Baseball Savant.

---

## Data Source

All data is sourced from **MLB Statcast** via [Baseball Savant](https://baseballsavant.mlb.com), accessed through the [pybaseball](https://github.com/jldbc/pybaseball) library. Statcast data is available from the **2015 season** onward.

Key columns used:

| Column | Description |
|--------|-------------|
| `launch_speed` | Exit velocity (mph) |
| `launch_angle` | Launch angle (degrees) |
| `estimated_woba_using_speedangle` | Expected wOBA (xwOBA) |
| `barrel` | Barrel indicator (1 = barrel) |
| `hc_x`, `hc_y` | Hit coordinate pixels (spray chart) |
| `hit_distance_sc` | Projected hit distance (ft) |
| `release_speed` | Pitch velocity (mph) |
| `release_spin_rate` | Spin rate (RPM) |
| `pfx_x`, `pfx_z` | Pitch movement — horizontal/vertical break (ft, converted to inches) |
| `release_pos_x`, `release_pos_z` | Release point coordinates (ft) |
| `pitch_type` | Pitch type code (FF, SL, CH, etc.) |
| `description` | Pitch outcome (e.g. `swinging_strike`) |

---

## Limitations & Out of Scope

- **Single player only** — no side-by-side player comparison
- **No percentile rankings** — raw stats only, no league-relative context
- **No pitch-by-pitch data table** — charts only
- **No authentication** — public app, no user accounts
- **Statcast era only** — data begins 2015; pre-2015 queries return empty

---

## License

MIT
