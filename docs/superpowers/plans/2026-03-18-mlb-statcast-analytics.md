# MLB Statcast Analytics App — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a focused Streamlit analytics dashboard that lets users search any MLB player and view 6 batting or 6 pitching Plotly charts from Statcast data, deployable to Streamlit Cloud.

**Architecture:** `app.py` handles all Streamlit UI, session state, and cached data fetching; `charts.py` contains pure functions (DataFrame → `go.Figure`) for all 12 charts. Tests cover data helpers and chart functions in `tests/`. No shared state between modules beyond function arguments.

**Tech Stack:** Python 3.11+, Streamlit, pybaseball, Plotly (graph_objects + express), pandas, numpy, pytest

---

## File Map

| File | Responsibility |
|------|---------------|
| `app.py` | Streamlit page, sidebar, session state, cached fetch, metric cards, chart grid |
| `charts.py` | All 12 chart functions + shared theme dict + data helpers |
| `requirements.txt` | Pinned dependencies |
| `.streamlit/config.toml` | Dark theme |
| `tests/test_charts.py` | Tests for chart functions and data helpers |
| `tests/conftest.py` | Shared pytest fixtures (sample DataFrames) |

---

## Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `.streamlit/config.toml`
- Create: `app.py` (skeleton)
- Create: `charts.py` (skeleton)
- Create: `tests/conftest.py`
- Create: `tests/test_charts.py` (skeleton)

- [ ] **Step 1: Create requirements.txt**

```
streamlit>=1.32.0
pybaseball>=2.2.7
pandas>=2.0.0
plotly>=5.18.0
numpy>=1.24.0
pytest>=8.0.0
```

- [ ] **Step 2: Create .streamlit/config.toml**

```toml
[theme]
base = "dark"
backgroundColor = "#0d1117"
secondaryBackgroundColor = "#0d1117"
textColor = "#e2e8f0"
primaryColor = "#2563eb"
```

- [ ] **Step 3: Create charts.py skeleton**

```python
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

THEME = {
    "bg": "#0d1117",
    "grid": "#1a2332",
    "axis": "#2d3f52",
    "tick": "#475569",
    "axis_title": "#64748b",
    "subtitle": "#64748b",
    "hr": "#f87171",
    "xbh": "#fb923c",
    "single": "#4ade80",
    "out_fill": "#1e293b",
    "out_border": "#475569",
    "ref_line": "#f97316",
    "pitch_colors": px.colors.qualitative.D3,
}

PITCH_NAMES = {
    "FF": "4-Seam FB", "FT": "2-Seam FB", "SI": "Sinker",
    "FC": "Cutter", "SL": "Slider", "SW": "Sweeper",
    "CU": "Curveball", "KC": "Knuckle-Curve", "CH": "Changeup",
    "FS": "Splitter", "KN": "Knuckleball",
}

OUTCOME_COLORS = {
    "home_run": "#f87171",
    "double": "#fb923c",
    "triple": "#fb923c",
    "single": "#4ade80",
}

def _base_layout(title: str = "", height: int = 340) -> dict:
    """Return shared Plotly layout kwargs."""
    return dict(
        height=height,
        paper_bgcolor=THEME["bg"],
        plot_bgcolor=THEME["bg"],
        font=dict(color=THEME["tick"], family="system-ui"),
        title=dict(text=title, font=dict(size=13, color="#94a3b8"), x=0, xanchor="left"),
        margin=dict(l=60, r=20, t=40, b=50),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=10, color="#94a3b8"),
        ),
        xaxis=dict(
            gridcolor=THEME["grid"],
            linecolor=THEME["axis"],
            tickcolor=THEME["axis"],
            tickfont=dict(size=9, color=THEME["tick"]),
            nticks=3,
        ),
        yaxis=dict(
            gridcolor=THEME["grid"],
            linecolor=THEME["axis"],
            tickcolor=THEME["axis"],
            tickfont=dict(size=9, color=THEME["tick"]),
            nticks=3,
        ),
    )


def _label_pitch_types(series: pd.Series) -> pd.Series:
    return series.map(lambda p: PITCH_NAMES.get(p, p) if pd.notna(p) else p)
```

- [ ] **Step 4: Create app.py skeleton**

```python
import datetime
import streamlit as st
import pandas as pd
import numpy as np
from pybaseball import statcast_batter, statcast_pitcher, playerid_lookup
import charts

st.set_page_config(
    page_title="MLB Statcast Analytics",
    page_icon="⚾",
    layout="wide",
)

SEASONS = list(range(2026, 2014, -1))
SEASON_DATES = {y: (datetime.date(y, 4, 1), datetime.date(y, 10, 1)) for y in SEASONS}
```

- [ ] **Step 5: Create tests/conftest.py**

```python
import pandas as pd
import numpy as np
import pytest

@pytest.fixture
def batting_df():
    n = 80
    rng = np.random.default_rng(42)
    events = rng.choice(
        ["home_run", "double", "triple", "single", "field_out", "strikeout"],
        size=n, p=[0.05, 0.07, 0.01, 0.18, 0.40, 0.29],
    )
    return pd.DataFrame({
        "game_date": pd.date_range("2024-04-01", periods=n, freq="2D"),
        "launch_speed": rng.normal(88, 10, n),
        "launch_angle": rng.normal(12, 18, n),
        "hc_x": rng.uniform(50, 200, n),
        "hc_y": rng.uniform(50, 200, n),
        "hit_distance_sc": rng.normal(220, 80, n),
        "events": events,
        "estimated_woba_using_speedangle": rng.uniform(0.1, 0.8, n),
        "barrel": rng.choice([0, 1], size=n, p=[0.85, 0.15]),
        "pitch_type": rng.choice(["FF", "SL", "CH", "SI", "CU"], size=n),
        "description": rng.choice(
            ["called_strike", "ball", "swinging_strike", "foul", "hit_into_play"],
            size=n,
        ),
    })


@pytest.fixture
def pitching_df():
    n = 100
    rng = np.random.default_rng(7)
    return pd.DataFrame({
        "game_date": pd.date_range("2024-04-01", periods=n, freq="D"),
        "pitch_type": rng.choice(["FF", "SL", "CH", "SI"], size=n),
        "release_speed": rng.normal(95, 3, n),
        "pfx_x": rng.normal(0.5, 0.3, n),
        "pfx_z": rng.normal(1.0, 0.4, n),
        "release_spin_rate": rng.normal(2300, 200, n),
        "release_pos_x": rng.normal(-2, 0.2, n),
        "release_pos_z": rng.normal(6, 0.3, n),
        "description": rng.choice(
            ["called_strike", "ball", "swinging_strike", "foul", "hit_into_play"],
            size=n,
        ),
    })
```

- [ ] **Step 6: Create tests/test_charts.py skeleton**

```python
import pytest
import pandas as pd
import plotly.graph_objects as go
import charts
```

- [ ] **Step 7: Install dependencies and verify import**

```bash
cd C:/Users/pjdai/mlb-statcast
pip install -r requirements.txt
python -c "import streamlit, pybaseball, plotly, pandas, numpy; print('OK')"
```

Expected: `OK`

- [ ] **Step 8: Commit scaffold**

```bash
cd C:/Users/pjdai/mlb-statcast
git init
git add .
git commit -m "feat: project scaffold — app.py, charts.py, requirements, theme"
```

---

## Task 2: Data Helpers + Metrics

**Files:**
- Modify: `charts.py` — add `compute_batting_metrics`, `compute_pitching_metrics`, `transform_spray_coords`, `rolling_xwoba`
- Modify: `tests/test_charts.py` — add helper tests

- [ ] **Step 1: Write failing tests for data helpers**

In `tests/test_charts.py`:

```python
def test_transform_spray_coords(batting_df):
    result = charts.transform_spray_coords(batting_df)
    assert "spray_x" in result.columns
    assert "spray_y" in result.columns
    # Home plate is near origin; values should be centered
    assert result["spray_x"].between(-200, 200).all()
    assert result["spray_y"].between(-50, 420).all()


def test_rolling_xwoba_returns_series(batting_df):
    result = charts.rolling_xwoba(batting_df, window=10)
    assert isinstance(result, pd.Series)
    assert len(result) == len(batting_df.dropna(subset=["estimated_woba_using_speedangle"]))
    assert result.notna().sum() > 0


def test_compute_batting_metrics_keys(batting_df):
    m = charts.compute_batting_metrics(batting_df)
    assert set(m.keys()) == {"avg_ev", "max_ev", "barrel_pct", "xwoba"}


def test_compute_batting_metrics_no_barrel_col():
    df = pd.DataFrame({"launch_speed": [90.0, 95.0], "estimated_woba_using_speedangle": [0.3, 0.5]})
    m = charts.compute_batting_metrics(df)
    assert m["barrel_pct"] is None


def test_compute_pitching_metrics_keys(pitching_df):
    m = charts.compute_pitching_metrics(pitching_df)
    assert set(m.keys()) == {"avg_velo", "max_velo", "avg_spin", "whiff_pct"}


def test_whiff_pct_calculation(pitching_df):
    m = charts.compute_pitching_metrics(pitching_df)
    assert 0.0 <= m["whiff_pct"] <= 100.0
```

- [ ] **Step 2: Run — verify failures**

```bash
cd C:/Users/pjdai/mlb-statcast
pytest tests/test_charts.py -v 2>&1 | head -30
```

Expected: all 6 tests FAIL (`AttributeError: module 'charts' has no attribute ...`)

- [ ] **Step 3: Implement helpers in charts.py**

Add after `_label_pitch_types`:

```python
def transform_spray_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Center spray coords so home plate ≈ origin."""
    out = df.copy()
    out["spray_x"] = df["hc_x"] - 125.42
    out["spray_y"] = 198.27 - df["hc_y"]
    return out


def rolling_xwoba(df: pd.DataFrame, window: int = 30) -> pd.Series:
    """30-PA rolling mean of xwOBA, sorted by game_date."""
    col = "estimated_woba_using_speedangle"
    pa = df[df[col].notna()].copy()
    pa = pa.sort_values("game_date")
    return pa[col].rolling(window, min_periods=5).mean().reset_index(drop=True)


def compute_batting_metrics(df: pd.DataFrame) -> dict:
    ev = df["launch_speed"] if "launch_speed" in df.columns else pd.Series(dtype=float)
    xwoba_col = df["estimated_woba_using_speedangle"] if "estimated_woba_using_speedangle" in df.columns else pd.Series(dtype=float)
    barrel_pct = None
    if "barrel" in df.columns and len(df) > 0:
        barrel_pct = df["barrel"].sum() / len(df) * 100
    return {
        "avg_ev": round(ev.mean(), 1) if not ev.empty else None,
        "max_ev": round(ev.max(), 1) if not ev.empty else None,
        "barrel_pct": round(barrel_pct, 1) if barrel_pct is not None else None,
        "xwoba": round(xwoba_col.mean(), 3) if not xwoba_col.empty else None,
    }


def compute_pitching_metrics(df: pd.DataFrame) -> dict:
    velo = df["release_speed"] if "release_speed" in df.columns else pd.Series(dtype=float)
    spin = df["release_spin_rate"] if "release_spin_rate" in df.columns else pd.Series(dtype=float)
    whiff_pct = None
    if "description" in df.columns:
        desc = df["description"].dropna()
        if len(desc) > 0:
            whiff_pct = round((desc == "swinging_strike").sum() / len(desc) * 100, 1)
    return {
        "avg_velo": round(velo.mean(), 1) if not velo.empty else None,
        "max_velo": round(velo.max(), 1) if not velo.empty else None,
        "avg_spin": round(spin.mean(), 0) if not spin.empty else None,
        "whiff_pct": whiff_pct,
    }
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_charts.py -v
```

Expected: 6 PASSED

- [ ] **Step 5: Commit**

```bash
git add charts.py tests/
git commit -m "feat: data helpers — spray transform, rolling xwOBA, metric calcs"
```

---

## Task 3: Batting Charts 1 & 2 (EV Distribution + Launch Angle Scatter)

**Files:**
- Modify: `charts.py` — add `batting_ev_distribution`, `batting_launch_ev_scatter`
- Modify: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
def test_batting_ev_distribution_returns_figure(batting_df):
    fig = charts.batting_ev_distribution(batting_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1  # at least histogram trace


def test_batting_ev_distribution_empty_df():
    fig = charts.batting_ev_distribution(pd.DataFrame(columns=["launch_speed"]))
    assert isinstance(fig, go.Figure)


def test_batting_launch_ev_scatter_returns_figure(batting_df):
    fig = charts.batting_launch_ev_scatter(batting_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_batting_launch_ev_scatter_has_sweet_spot_shape(batting_df):
    fig = charts.batting_launch_ev_scatter(batting_df)
    # Sweet spot zone is added as a shape
    assert len(fig.layout.shapes) >= 1
```

- [ ] **Step 2: Run — verify failures**

```bash
pytest tests/test_charts.py -k "ev_distribution or launch_ev" -v
```

Expected: 4 FAIL

- [ ] **Step 3: Implement batting_ev_distribution**

```python
def batting_ev_distribution(df: pd.DataFrame) -> go.Figure:
    ev = df["launch_speed"].dropna() if "launch_speed" in df.columns else pd.Series(dtype=float)
    fig = go.Figure()
    if ev.empty:
        return fig.update_layout(**_base_layout("Exit Velocity Distribution"))

    fig.add_trace(go.Histogram(
        x=ev, xbins=dict(size=2),
        marker_color="#2563eb", opacity=0.85,
        hovertemplate="EV: %{x} mph<br>Count: %{y}<extra></extra>",
        name="",
    ))

    avg = ev.mean()
    fig.add_vline(x=avg, line_dash="dash", line_color=THEME["ref_line"], line_width=1.5,
                  annotation_text=f"Avg {avg:.1f}", annotation_position="top right",
                  annotation_font=dict(size=9, color=THEME["ref_line"]))
    fig.add_vline(x=95, line_dash="dot", line_color="#ef4444", line_width=1,
                  annotation_text="95 mph", annotation_position="top left",
                  annotation_font=dict(size=9, color="#ef4444"))

    layout = _base_layout("Exit Velocity Distribution")
    layout["xaxis"]["title"] = dict(text="Exit Velocity (mph)", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Batted Balls", font=dict(size=10, color=THEME["axis_title"]))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 4: Implement batting_launch_ev_scatter**

```python
def batting_launch_ev_scatter(df: pd.DataFrame) -> go.Figure:
    needed = {"launch_angle", "launch_speed"}
    if not needed.issubset(df.columns) or df.empty:
        return go.Figure().update_layout(**_base_layout("Launch Angle vs Exit Velocity"))

    data = df[df["launch_speed"].notna() & df["launch_angle"].notna()].copy()

    def _outcome_color(event):
        if event == "home_run":
            return OUTCOME_COLORS["home_run"]
        if event in ("double", "triple"):
            return OUTCOME_COLORS["double"]
        if event == "single":
            return OUTCOME_COLORS["single"]
        return THEME["out_fill"]

    data["color"] = data["events"].map(_outcome_color).fillna(THEME["out_fill"])

    fig = go.Figure()
    for label, color, marker_size in [
        ("Out",    THEME["out_fill"],          5),
        ("Single", OUTCOME_COLORS["single"],   6),
        ("XBH",    OUTCOME_COLORS["xbh"],      7),
        ("HR",     OUTCOME_COLORS["hr"],        8),
    ]:
        if label == "Out":
            mask = ~data["events"].isin(["home_run", "double", "triple", "single"])
        elif label == "Single":
            mask = data["events"] == "single"
        elif label == "XBH":
            mask = data["events"].isin(["double", "triple"])
        else:
            mask = data["events"] == "home_run"

        subset = data[mask]
        if subset.empty:
            continue

        fig.add_trace(go.Scatter(
            x=subset["launch_angle"], y=subset["launch_speed"],
            mode="markers",
            marker=dict(
                color=color,
                size=marker_size,
                opacity=0.8,
                line=dict(color=THEME["axis"], width=0.5) if label == "Out" else dict(width=0),
            ),
            name=label,
            hovertemplate="LA: %{x:.1f}°<br>EV: %{y:.1f} mph<extra></extra>",
        ))

    # Sweet spot zone
    fig.add_shape(
        type="rect", x0=8, x1=32,
        y0=95, y1=data["launch_speed"].max() + 5,
        fillcolor="rgba(34,197,94,0.05)",
        line=dict(color="rgba(34,197,94,0.28)", width=1, dash="dot"),
    )

    # Callout annotation — placed to the right of the chart
    fig.add_annotation(
        x=32, y=95 + (data["launch_speed"].max() + 5 - 95) / 2,
        xref="x", yref="y",
        text="Sweet Spot<br><span style='font-size:9px;color:rgba(74,222,128,0.5)'>8–32° · ≥95 mph</span>",
        showarrow=True,
        arrowhead=0,
        arrowcolor="rgba(74,222,128,0.35)",
        arrowwidth=1,
        ax=50, ay=0,
        font=dict(size=9, color="rgba(74,222,128,0.75)"),
        align="left",
        xanchor="left",
    )

    layout = _base_layout("Launch Angle vs Exit Velocity")
    layout["xaxis"]["title"] = dict(text="Launch Angle (°)", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Exit Velocity (mph)", font=dict(size=10, color=THEME["axis_title"]))
    layout["xaxis"]["tickvals"] = [-20, 10, 40]
    layout["yaxis"]["tickvals"] = [70, 95, 115]
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 5: Run — verify pass**

```bash
pytest tests/test_charts.py -k "ev_distribution or launch_ev" -v
```

Expected: 4 PASSED

- [ ] **Step 6: Commit**

```bash
git add charts.py tests/test_charts.py
git commit -m "feat: batting charts 1-2 — EV histogram, launch angle scatter"
```

---

## Task 4: Batting Charts 3 & 4 (Spray Chart + Rolling xwOBA)

**Files:**
- Modify: `charts.py` — add `batting_spray_chart`, `batting_xwoba_trend`
- Modify: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
def test_batting_spray_chart_returns_figure(batting_df):
    fig = charts.batting_spray_chart(batting_df)
    assert isinstance(fig, go.Figure)
    # Should have field overlay traces + data traces
    assert len(fig.data) >= 2


def test_batting_spray_chart_has_diamond_shape(batting_df):
    fig = charts.batting_spray_chart(batting_df)
    assert len(fig.layout.shapes) >= 1  # infield diamond


def test_batting_xwoba_trend_returns_figure(batting_df):
    fig = charts.batting_xwoba_trend(batting_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_batting_xwoba_trend_has_ref_line(batting_df):
    fig = charts.batting_xwoba_trend(batting_df)
    # League avg reference line added as hline (shows up in layout.shapes)
    assert any(s.y0 == pytest.approx(0.320) for s in fig.layout.shapes)
```

- [ ] **Step 2: Run — verify failures**

```bash
pytest tests/test_charts.py -k "spray or xwoba" -v
```

Expected: 4 FAIL

- [ ] **Step 3: Implement batting_spray_chart**

```python
def batting_spray_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    # Field overlay — foul lines
    fig.add_trace(go.Scatter(
        x=[-250, 0, 250], y=[350, 0, 350],
        mode="lines", line=dict(color="rgba(100,116,139,0.3)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    # Outfield arc
    import numpy as np
    theta = np.linspace(np.radians(45), np.radians(135), 80)
    r = 370
    fig.add_trace(go.Scatter(
        x=r * np.cos(theta), y=r * np.sin(theta),
        mode="lines", line=dict(color="rgba(100,116,139,0.2)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    # Infield diamond shape
    fig.add_shape(
        type="path",
        path="M 0 0 L -63.5 63.5 L 0 127 L 63.5 63.5 Z",
        fillcolor="rgba(250,204,21,0.04)",
        line=dict(color="rgba(250,204,21,0.38)", width=1.2),
    )

    needed = {"hc_x", "hc_y"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Spray Chart"))

    spray = transform_spray_coords(df[df["hc_x"].notna() & df["hc_y"].notna()].copy())
    if spray.empty:
        return fig.update_layout(**_base_layout("Spray Chart"))

    for label, color, size, events_filter in [
        ("Out",    THEME["out_fill"],  5,  None),
        ("Hit",    OUTCOME_COLORS["single"], 6, ["single", "double", "triple"]),
        ("HR",     OUTCOME_COLORS["hr"],     8, ["home_run"]),
    ]:
        if events_filter is None:
            mask = ~spray["events"].isin(["home_run", "single", "double", "triple"])
        else:
            mask = spray["events"].isin(events_filter)
        sub = spray[mask]
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["spray_x"], y=sub["spray_y"],
            mode="markers",
            marker=dict(
                color=color, size=size, opacity=0.8,
                line=dict(color=THEME["axis"], width=0.5) if label == "Out" else dict(width=0),
            ),
            name=label,
            hovertemplate="x: %{x:.0f}<br>y: %{y:.0f}<extra></extra>",
        ))

    layout = _base_layout("Spray Chart")
    layout["xaxis"].update(range=[-270, 270], showgrid=False, zeroline=False,
                           showticklabels=False, title="← Pull · Center · Oppo →")
    layout["xaxis"]["title"] = dict(text="← Pull · Center · Oppo →", font=dict(size=9, color=THEME["axis_title"]))
    layout["yaxis"].update(range=[-30, 430], showgrid=False, zeroline=False,
                           showticklabels=False, scaleanchor="x")
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 4: Implement batting_xwoba_trend**

```python
def batting_xwoba_trend(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    col = "estimated_woba_using_speedangle"
    if col not in df.columns or df.empty:
        return fig.update_layout(**_base_layout("Rolling xwOBA (30 PA)"))

    pa = df[df[col].notna()].copy().sort_values("game_date")
    if pa.empty:
        return fig.update_layout(**_base_layout("Rolling xwOBA (30 PA)"))

    pa["rolling"] = pa[col].rolling(30, min_periods=5).mean()

    fig.add_trace(go.Scatter(
        x=pa["game_date"], y=pa["rolling"],
        mode="lines",
        line=dict(color="#2563eb", width=2),
        name="Rolling xwOBA",
        hovertemplate="%{x|%b %d}: %{y:.3f}<extra></extra>",
    ))

    # League avg reference line
    fig.add_hline(y=0.320, line_dash="dash", line_color=THEME["ref_line"], line_width=1,
                  annotation_text="Lg Avg (~.320)",
                  annotation_position="bottom right",
                  annotation_font=dict(size=9, color=THEME["ref_line"]))

    layout = _base_layout("Rolling xwOBA (30 PA)")
    layout["xaxis"]["title"] = dict(text="Date", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="xwOBA", font=dict(size=10, color=THEME["axis_title"]))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 5: Run — verify pass**

```bash
pytest tests/test_charts.py -k "spray or xwoba" -v
```

Expected: 4 PASSED

- [ ] **Step 6: Commit**

```bash
git add charts.py tests/test_charts.py
git commit -m "feat: batting charts 3-4 — spray chart, rolling xwOBA trend"
```

---

## Task 5: Batting Charts 5 & 6 (Pitch Types Faced + Hit Distance)

**Files:**
- Modify: `charts.py` — add `batting_pitch_types_faced`, `batting_hit_distance`
- Modify: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
def test_batting_pitch_types_faced_returns_figure(batting_df):
    fig = charts.batting_pitch_types_faced(batting_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_batting_hit_distance_returns_figure(batting_df):
    fig = charts.batting_hit_distance(batting_df)
    assert isinstance(fig, go.Figure)


def test_batting_hit_distance_only_hit_events(batting_df):
    fig = charts.batting_hit_distance(batting_df)
    if fig.data:
        x_vals = set()
        for trace in fig.data:
            if hasattr(trace, "x") and trace.x is not None:
                x_vals.update(trace.x)
        assert x_vals.issubset({"single", "double", "triple", "home_run"})
```

- [ ] **Step 2: Run — verify failures**

```bash
pytest tests/test_charts.py -k "pitch_types_faced or hit_distance" -v
```

Expected: 3 FAIL

- [ ] **Step 3: Implement batting_pitch_types_faced**

```python
def batting_pitch_types_faced(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "pitch_type" not in df.columns or df.empty:
        return fig.update_layout(**_base_layout("Pitch Types Faced"))

    counts = df["pitch_type"].dropna().map(lambda p: PITCH_NAMES.get(p, p)).value_counts()
    if counts.empty:
        return fig.update_layout(**_base_layout("Pitch Types Faced"))

    fig.add_trace(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.4,
        textposition="outside",
        textinfo="label+percent",
        textfont=dict(size=9, color="#94a3b8"),
        marker=dict(colors=THEME["pitch_colors"][:len(counts)]),
        showlegend=False,
    ))

    layout = _base_layout("Pitch Types Faced")
    layout["margin"] = dict(l=40, r=40, t=40, b=40)
    fig.update_layout(**layout)
    return fig


def batting_hit_distance(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"hit_distance_sc", "events"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Hit Distance by Outcome"))

    hit_events = ["single", "double", "triple", "home_run"]
    colors = [OUTCOME_COLORS["single"], THEME["xbh"],
              THEME["xbh"], OUTCOME_COLORS["hr"]]

    data = df[df["events"].isin(hit_events) & df["hit_distance_sc"].notna()]
    if data.empty:
        return fig.update_layout(**_base_layout("Hit Distance by Outcome"))

    for event, color in zip(hit_events, colors):
        sub = data[data["events"] == event]["hit_distance_sc"]
        if sub.empty:
            continue
        fig.add_trace(go.Box(
            y=sub, name=event.replace("_", " ").title(),
            marker_color=color, line_color=color,
            boxmean=True,
            hovertemplate="%{y:.0f} ft<extra></extra>",
        ))

    layout = _base_layout("Hit Distance by Outcome")
    layout["xaxis"]["title"] = dict(text="Hit Type", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Distance (ft)", font=dict(size=10, color=THEME["axis_title"]))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_charts.py -k "pitch_types_faced or hit_distance" -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add charts.py tests/test_charts.py
git commit -m "feat: batting charts 5-6 — pitch types faced, hit distance"
```

---

## Task 6: Pitching Charts 1–3 (Usage, Velocity, Movement)

**Files:**
- Modify: `charts.py` — add `pitching_pitch_usage`, `pitching_velocity_by_type`, `pitching_movement_profile`
- Modify: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
def test_pitching_pitch_usage_returns_figure(pitching_df):
    fig = charts.pitching_pitch_usage(pitching_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_pitching_velocity_by_type_returns_figure(pitching_df):
    fig = charts.pitching_velocity_by_type(pitching_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_pitching_movement_profile_returns_figure(pitching_df):
    fig = charts.pitching_movement_profile(pitching_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_pitching_movement_profile_has_crosshairs(pitching_df):
    fig = charts.pitching_movement_profile(pitching_df)
    # Zero-line crosshairs added as shapes
    assert len(fig.layout.shapes) >= 2
```

- [ ] **Step 2: Run — verify failures**

```bash
pytest tests/test_charts.py -k "pitching_pitch_usage or velocity_by_type or movement_profile" -v
```

Expected: 4 FAIL

- [ ] **Step 3: Implement pitching_pitch_usage**

```python
def pitching_pitch_usage(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if "pitch_type" not in df.columns or df.empty:
        return fig.update_layout(**_base_layout("Pitch Type Usage"))

    counts = df["pitch_type"].dropna().map(lambda p: PITCH_NAMES.get(p, p)).value_counts()
    if counts.empty:
        return fig.update_layout(**_base_layout("Pitch Type Usage"))

    fig.add_trace(go.Pie(
        labels=counts.index.tolist(),
        values=counts.values.tolist(),
        hole=0.4,
        textposition="outside",
        textinfo="label+percent",
        textfont=dict(size=9, color="#94a3b8"),
        marker=dict(colors=THEME["pitch_colors"][:len(counts)]),
        showlegend=False,
    ))

    layout = _base_layout("Pitch Type Usage")
    layout["margin"] = dict(l=40, r=40, t=40, b=40)
    fig.update_layout(**layout)
    return fig


def pitching_velocity_by_type(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"release_speed", "pitch_type"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Velocity by Pitch Type"))

    df2 = df[df["release_speed"].notna() & df["pitch_type"].notna()].copy()
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])

    for i, label in enumerate(df2["pitch_label"].unique()):
        sub = df2[df2["pitch_label"] == label]["release_speed"]
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        fig.add_trace(go.Violin(
            y=sub, name=label,
            box_visible=True,
            meanline_visible=True,
            line_color=color,
            fillcolor=color.replace(")", ",0.15)").replace("rgb", "rgba"),
            opacity=0.8,
        ))

    layout = _base_layout("Velocity by Pitch Type")
    layout["xaxis"]["title"] = dict(text="Pitch Type", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Velocity (mph)", font=dict(size=10, color=THEME["axis_title"]))
    layout["violingap"] = 0.3
    fig.update_layout(**layout)
    return fig


def pitching_movement_profile(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"pfx_x", "pfx_z", "pitch_type"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Movement Profile"))

    df2 = df[df["pfx_x"].notna() & df["pfx_z"].notna()].copy()
    df2["hmov"] = df2["pfx_x"] * 12   # feet → inches
    df2["vmov"] = df2["pfx_z"] * 12
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])

    for i, label in enumerate(df2["pitch_label"].unique()):
        sub = df2[df2["pitch_label"] == label]
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        fig.add_trace(go.Scatter(
            x=sub["hmov"], y=sub["vmov"],
            mode="markers",
            marker=dict(color=color, size=5, opacity=0.65),
            name=label,
            hovertemplate="H: %{x:.1f}\"<br>V: %{y:.1f}\"<extra></extra>",
        ))

    # Zero-line crosshairs
    fig.add_hline(y=0, line_color=THEME["axis"], line_width=1)
    fig.add_vline(x=0, line_color=THEME["axis"], line_width=1)

    layout = _base_layout("Movement Profile (Catcher's POV)")
    layout["xaxis"].update(range=[-24, 24], title=dict(text="Horizontal Break (in)", font=dict(size=10, color=THEME["axis_title"])))
    layout["yaxis"].update(range=[-20, 30], title=dict(text="Vertical Break (in)", font=dict(size=10, color=THEME["axis_title"])))
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 4: Run — verify pass**

```bash
pytest tests/test_charts.py -k "pitching_pitch_usage or velocity_by_type or movement_profile" -v
```

Expected: 4 PASSED

- [ ] **Step 5: Commit**

```bash
git add charts.py tests/test_charts.py
git commit -m "feat: pitching charts 1-3 — usage, velocity, movement profile"
```

---

## Task 7: Pitching Charts 4–6 (Spin Rate, Release Point, Velocity Trend)

**Files:**
- Modify: `charts.py` — add `pitching_spin_rate`, `pitching_release_point`, `pitching_velocity_trend`
- Modify: `tests/test_charts.py`

- [ ] **Step 1: Write failing tests**

```python
def test_pitching_spin_rate_returns_figure(pitching_df):
    fig = charts.pitching_spin_rate(pitching_df)
    assert isinstance(fig, go.Figure)


def test_pitching_release_point_returns_figure(pitching_df):
    fig = charts.pitching_release_point(pitching_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_pitching_velocity_trend_returns_figure(pitching_df):
    fig = charts.pitching_velocity_trend(pitching_df)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1
```

- [ ] **Step 2: Run — verify failures**

```bash
pytest tests/test_charts.py -k "spin_rate or release_point or velocity_trend" -v
```

Expected: 3 FAIL

- [ ] **Step 3: Implement remaining pitching charts**

```python
def pitching_spin_rate(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"release_spin_rate", "pitch_type"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Spin Rate by Pitch Type"))

    df2 = df[df["release_spin_rate"].notna() & df["pitch_type"].notna()].copy()
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])

    for i, label in enumerate(df2["pitch_label"].unique()):
        sub = df2[df2["pitch_label"] == label]["release_spin_rate"]
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        fig.add_trace(go.Box(
            y=sub, name=label,
            marker_color=color, line_color=color,
            boxmean=True,
            hovertemplate="%{y:.0f} rpm<extra></extra>",
        ))

    layout = _base_layout("Spin Rate by Pitch Type")
    layout["xaxis"]["title"] = dict(text="Pitch Type", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Spin Rate (rpm)", font=dict(size=10, color=THEME["axis_title"]))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


def pitching_release_point(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"release_pos_x", "release_pos_z", "pitch_type"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Release Point"))

    df2 = df[df["release_pos_x"].notna() & df["release_pos_z"].notna()].copy()
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])

    for i, label in enumerate(df2["pitch_label"].unique()):
        sub = df2[df2["pitch_label"] == label]
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        fig.add_trace(go.Scatter(
            x=sub["release_pos_x"], y=sub["release_pos_z"],
            mode="markers",
            marker=dict(color=color, size=5, opacity=0.6),
            name=label,
            hovertemplate="H: %{x:.2f} ft<br>V: %{y:.2f} ft<extra></extra>",
        ))

    layout = _base_layout("Release Point")
    layout["xaxis"]["title"] = dict(text="Horizontal Release (ft)", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Vertical Release (ft)", font=dict(size=10, color=THEME["axis_title"]))
    fig.update_layout(**layout)
    return fig


def pitching_velocity_trend(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    needed = {"release_speed", "pitch_type", "game_date"}
    if not needed.issubset(df.columns) or df.empty:
        return fig.update_layout(**_base_layout("Velocity Trend"))

    df2 = df[df["release_speed"].notna() & df["pitch_type"].notna()].copy()
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])
    df2["game_date"] = pd.to_datetime(df2["game_date"])

    daily = (
        df2.groupby(["game_date", "pitch_label"])["release_speed"]
        .mean()
        .reset_index()
    )

    for i, label in enumerate(daily["pitch_label"].unique()):
        sub = daily[daily["pitch_label"] == label].sort_values("game_date")
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        fig.add_trace(go.Scatter(
            x=sub["game_date"], y=sub["release_speed"],
            mode="lines+markers",
            line=dict(color=color, width=1.8),
            marker=dict(color=color, size=4),
            name=label,
            hovertemplate="%{x|%b %d}: %{y:.1f} mph<extra></extra>",
        ))

    layout = _base_layout("Velocity Trend by Pitch Type")
    layout["xaxis"]["title"] = dict(text="Date", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Avg Velocity (mph)", font=dict(size=10, color=THEME["axis_title"]))
    fig.update_layout(**layout)
    return fig
```

- [ ] **Step 4: Run all tests**

```bash
pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 5: Commit**

```bash
git add charts.py tests/test_charts.py
git commit -m "feat: pitching charts 4-6 — spin rate, release point, velocity trend"
```

---

## Task 8: Full app.py — Sidebar, State, Layout

**Files:**
- Modify: `app.py` — complete implementation

No unit tests for Streamlit UI; smoke test manually by running `streamlit run app.py`.

- [ ] **Step 1: Add cached data fetch functions to app.py**

Replace the skeleton with:

```python
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
```

- [ ] **Step 2: Add sidebar**

```python
# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚾ Player Search")

    col_a, col_b = st.columns(2)
    first_input = col_a.text_input("First", value="Shohei", label_visibility="collapsed",
                                    placeholder="First name")
    last_input  = col_b.text_input("Last",  value="Ohtani", label_visibility="collapsed",
                                    placeholder="Last name")
    col_a.caption("First")
    col_b.caption("Last")

    if st.button("Search", type="primary", use_container_width=True):
        with st.spinner("Searching…"):
            try:
                results = search_player(last_input, first_input)
                st.session_state["player_results"] = results
                st.session_state.pop("player_id", None)
            except Exception as e:
                st.error(str(e))

    player_id   = None
    player_name = ""

    if "player_results" in st.session_state:
        res = st.session_state["player_results"]
        valid = res[res["key_mlbam"].notna() & (res["key_mlbam"].astype(float) > 0)] if not res.empty else res
        if valid.empty:
            st.warning("No players found. Check spelling.")
        else:
            options = {
                f"{r['name_first']} {r['name_last']} (born {int(r['mlb_played_first']) if pd.notna(r.get('mlb_played_first')) else '?'}, ID {int(r['key_mlbam'])})": int(r["key_mlbam"])
                for _, r in valid.iterrows()
            }
            chosen = st.selectbox("Select player", list(options.keys()), label_visibility="collapsed")
            player_id   = options[chosen]
            player_name = chosen.split(" (")[0]
            st.session_state["player_id"]   = player_id
            st.session_state["player_name"] = player_name

    st.divider()

    # Mode toggle
    mode = st.radio("Analytics Mode", ["Batting", "Pitching"],
                    horizontal=True, disabled=(player_id is None))

    st.divider()

    # Season + date range
    st.markdown("##### Date Range")
    season = st.selectbox("Season shortcut", ["Custom"] + [str(y) for y in SEASONS])
    if season != "Custom":
        default_start, default_end = SEASON_DATES[int(season)]
    else:
        default_start = datetime.date(2024, 4, 1)
        default_end   = datetime.date(2024, 10, 1)

    col_s, col_e = st.columns(2)
    start_date = col_s.date_input("Start", value=default_start)
    end_date   = col_e.date_input("End",   value=default_end)

    st.divider()

    load = st.button("⚡ Load Data", type="primary",
                     disabled=(player_id is None), use_container_width=True)
```

- [ ] **Step 3: Add metric card helper**

```python
def _metric_card(label: str, value) -> None:
    """Render a single stat card."""
    display = str(value) if value is not None else "N/A"
    st.metric(label=label, value=display)
```

- [ ] **Step 4: Add main panel — batting layout**

```python
def _render_batting(df: pd.DataFrame, player_name: str, start: str, end: str) -> None:
    st.header(f"{player_name} — Batting Analytics")
    st.caption(f"{start}  →  {end}")

    m = charts.compute_batting_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card("Avg Exit Velo", f"{m['avg_ev']} mph" if m['avg_ev'] else None)
    with c2: _metric_card("Max Exit Velo", f"{m['max_ev']} mph" if m['max_ev'] else None)
    with c3: _metric_card("Barrel %",      f"{m['barrel_pct']}%" if m['barrel_pct'] is not None else None)
    with c4: _metric_card("xwOBA",         m['xwoba'])

    st.divider()

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.plotly_chart(charts.batting_ev_distribution(df),    use_container_width=True)
    with r1c2: st.plotly_chart(charts.batting_launch_ev_scatter(df),  use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1: st.plotly_chart(charts.batting_spray_chart(df),        use_container_width=True)
    with r2c2: st.plotly_chart(charts.batting_xwoba_trend(df),        use_container_width=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1: st.plotly_chart(charts.batting_pitch_types_faced(df),  use_container_width=True)
    with r3c2: st.plotly_chart(charts.batting_hit_distance(df),       use_container_width=True)
```

- [ ] **Step 5: Add main panel — pitching layout**

```python
def _render_pitching(df: pd.DataFrame, player_name: str, start: str, end: str) -> None:
    st.header(f"{player_name} — Pitching Analytics")
    st.caption(f"{start}  →  {end}")

    m = charts.compute_pitching_metrics(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1: _metric_card("Avg Velocity",  f"{m['avg_velo']} mph" if m['avg_velo'] else None)
    with c2: _metric_card("Max Velocity",  f"{m['max_velo']} mph" if m['max_velo'] else None)
    with c3: _metric_card("Avg Spin Rate", f"{m['avg_spin']} rpm" if m['avg_spin'] else None)
    with c4: _metric_card("Whiff %",       f"{m['whiff_pct']}%" if m['whiff_pct'] is not None else None)

    st.divider()

    r1c1, r1c2 = st.columns(2)
    with r1c1: st.plotly_chart(charts.pitching_pitch_usage(df),      use_container_width=True)
    with r1c2: st.plotly_chart(charts.pitching_velocity_by_type(df), use_container_width=True)

    r2c1, r2c2 = st.columns(2)
    with r2c1: st.plotly_chart(charts.pitching_movement_profile(df), use_container_width=True)
    with r2c2: st.plotly_chart(charts.pitching_spin_rate(df),        use_container_width=True)

    r3c1, r3c2 = st.columns(2)
    with r3c1: st.plotly_chart(charts.pitching_release_point(df),    use_container_width=True)
    with r3c2: st.plotly_chart(charts.pitching_velocity_trend(df),   use_container_width=True)
```

- [ ] **Step 6: Wire the load button to the main panel**

> **Note:** Charts only render when Load Data is pressed. Changing mode/dates without pressing the button clears the view — this is intentional (avoids stale data being shown with new settings). If persistence across sidebar interactions is desired, store `(df, mode)` in `st.session_state` and render from there instead.

```python
# ── MAIN PANEL ───────────────────────────────────────────────────────────────
if load and player_id:
    start_str = str(start_date)
    end_str   = str(end_date)

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
        st.warning("No data returned. Try a different date range or check the player's role.")
    else:
        if mode == "Batting":
            _render_batting(df, player_name, start_str, end_str)
        else:
            _render_pitching(df, player_name, start_str, end_str)

elif not load:
    st.markdown("## ⚾ MLB Statcast Analytics")
    st.info("Search for a player in the sidebar and click **⚡ Load Data** to begin.")
```

- [ ] **Step 7: Smoke test — run the app**

```bash
cd C:/Users/pjdai/mlb-statcast
streamlit run app.py
```

Open `http://localhost:8501`. Search "Shohei Ohtani", select him, choose 2024, click Load Data in both Batting and Pitching modes. Verify all 6 charts render for each mode with no errors.

- [ ] **Step 8: Commit**

```bash
git add app.py
git commit -m "feat: complete app.py — sidebar, session state, batting and pitching layouts"
```

---

## Task 9: Deployment Files

**Files:**
- Verify: `.streamlit/config.toml` already exists
- Create: `.gitignore`

- [ ] **Step 1: Create .gitignore**

```
__pycache__/
*.pyc
.env
.streamlit/secrets.toml
pybaseball_cache/
.superpowers/
```

- [ ] **Step 2: Run full test suite one final time**

```bash
pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 3: Final commit**

```bash
git add .gitignore
git commit -m "chore: add .gitignore, ready for Streamlit Cloud deploy"
```

- [ ] **Step 4: Push to GitHub and deploy**

```bash
git remote add origin https://github.com/<your-username>/mlb-statcast.git
git push -u origin main
```

Then go to **https://share.streamlit.io**, click "New app", connect the repo, set main file to `app.py`. No secrets needed. Deploy.

---

## Quick Reference — pybaseball API

```python
from pybaseball import playerid_lookup, statcast_batter, statcast_pitcher

# Returns DataFrame with: name_first, name_last, key_mlbam, mlb_played_first
results = playerid_lookup("ohtani", "shohei")

# Returns Statcast DataFrame (one row per pitch/PA)
df = statcast_batter("2024-04-01", "2024-10-01", player_id=660271)
df = statcast_pitcher("2024-04-01", "2024-10-01", player_id=660271)
```

Key Statcast columns used in this app:

| Column | Type | Description |
|--------|------|-------------|
| `launch_speed` | float | Exit velocity (mph) |
| `launch_angle` | float | Launch angle (°) |
| `hc_x`, `hc_y` | float | Hit coordinates (raw pixels) |
| `hit_distance_sc` | float | Estimated hit distance (ft) |
| `events` | str | Outcome (home_run, single, etc.) |
| `estimated_woba_using_speedangle` | float | xwOBA |
| `barrel` | int | 1 = barrel, 0 = not |
| `pitch_type` | str | Pitch code (FF, SL, etc.) |
| `release_speed` | float | Pitch velocity (mph) |
| `pfx_x`, `pfx_z` | float | Pitch movement (ft, catcher's POV) |
| `release_spin_rate` | float | Spin rate (rpm) |
| `release_pos_x/z` | float | Release point coordinates (ft) |
| `description` | str | Pitch outcome (swinging_strike, etc.) |
| `game_date` | str/date | Game date |
