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
