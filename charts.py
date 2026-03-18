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


def transform_spray_coords(df: pd.DataFrame) -> pd.DataFrame:
    """Center Statcast hit coordinates so home plate is near the origin.

    Statcast hc_x / hc_y are raw pixel coordinates from a 250x250 field image.
    125.42 and 198.27 are the empirically-derived home-plate pixel offsets.
    After transformation: negative spray_x = pull side, positive = oppo; spray_y
    increases toward the outfield.
    """
    out = df.copy()
    out["spray_x"] = df["hc_x"] - 125.42
    out["spray_y"] = 198.27 - df["hc_y"]
    return out


def rolling_xwoba(df: pd.DataFrame, window: int = 30) -> pd.Series:
    col = "estimated_woba_using_speedangle"
    pa = df[df[col].notna()].copy()
    pa = pa.sort_values("game_date")
    return pa[col].rolling(window, min_periods=5).mean().reset_index(drop=True)


def compute_batting_metrics(df: pd.DataFrame) -> dict:
    ev = df["launch_speed"] if "launch_speed" in df.columns else pd.Series(dtype=float)
    xwoba_col = df["estimated_woba_using_speedangle"] if "estimated_woba_using_speedangle" in df.columns else pd.Series(dtype=float)
    barrel_pct = None
    if "barrel" in df.columns:
        valid_barrels = df["barrel"].dropna()
        if len(valid_barrels) > 0:
            barrel_pct = valid_barrels.sum() / len(valid_barrels) * 100
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
