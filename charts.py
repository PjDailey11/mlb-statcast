import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

THEME = {
    "bg": "#0d1117",
    "grid": "#111827",
    "axis": "#1e2d45",
    "tick": "#334155",
    "axis_title": "#475569",
    "subtitle": "#475569",
    "hr": "#f87171",
    "xbh": "#fb923c",
    "single": "#4ade80",
    "out_fill": "#0f172a",
    "out_border": "#334155",
    "ref_line": "#3b82f6",
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
        font=dict(color=THEME["tick"], family="Inter, system-ui, sans-serif"),
        title=dict(
            text=title,
            font=dict(size=12, color="#64748b", family="Inter, system-ui, sans-serif"),
            x=0, xanchor="left",
        ),
        margin=dict(l=56, r=16, t=36, b=44),
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            borderwidth=0,
            font=dict(size=10, color="#64748b", family="Inter, system-ui, sans-serif"),
        ),
        xaxis=dict(
            gridcolor=THEME["grid"],
            linecolor=THEME["axis"],
            tickcolor=THEME["axis"],
            tickfont=dict(size=9, color=THEME["tick"], family="JetBrains Mono, monospace"),
            nticks=3,
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor=THEME["grid"],
            linecolor="rgba(0,0,0,0)",
            tickcolor=THEME["axis"],
            tickfont=dict(size=9, color=THEME["tick"], family="JetBrains Mono, monospace"),
            nticks=3,
            showgrid=True,
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


def compute_batting_metrics(df: pd.DataFrame) -> dict:
    ev = df["launch_speed"].dropna() if "launch_speed" in df.columns else pd.Series(dtype=float)
    xwoba_col = df["estimated_woba_using_speedangle"].dropna() if "estimated_woba_using_speedangle" in df.columns else pd.Series(dtype=float)
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
    velo = df["release_speed"].dropna() if "release_speed" in df.columns else pd.Series(dtype=float)
    spin = df["release_spin_rate"].dropna() if "release_spin_rate" in df.columns else pd.Series(dtype=float)
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


def batting_launch_ev_scatter(df: pd.DataFrame) -> go.Figure:
    needed = {"launch_angle", "launch_speed"}
    if not needed.issubset(df.columns) or df.empty:
        return go.Figure().update_layout(**_base_layout("Launch Angle vs Exit Velocity"))

    data = df[df["launch_speed"].notna() & df["launch_angle"].notna()].copy()
    if data.empty:
        return go.Figure().update_layout(**_base_layout("Launch Angle vs Exit Velocity"))
    if len(data) > 800:
        data = data.sample(800, random_state=42)

    fig = go.Figure()
    for label, events_list, marker_size in [
        ("Out",    None,                              5),
        ("Single", ["single"],                        6),
        ("XBH",    ["double", "triple"],              7),
        ("HR",     ["home_run"],                      8),
    ]:
        if events_list is None:
            mask = ~data["events"].isin(["home_run", "double", "triple", "single"])
        else:
            mask = data["events"].isin(events_list)

        color = (THEME["out_fill"] if label == "Out"
                 else OUTCOME_COLORS["single"] if label == "Single"
                 else THEME["xbh"] if label == "XBH"
                 else OUTCOME_COLORS["home_run"])

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

    fig.add_shape(
        type="rect", x0=8, x1=32,
        y0=95, y1=data["launch_speed"].max() + 5,
        fillcolor="rgba(34,197,94,0.05)",
        line=dict(color="rgba(34,197,94,0.28)", width=1, dash="dot"),
    )

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


def batting_spray_chart(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=[-250, 0, 250], y=[350, 0, 350],
        mode="lines", line=dict(color="rgba(100,116,139,0.3)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

    theta = np.linspace(np.radians(45), np.radians(135), 80)
    r = 370
    fig.add_trace(go.Scatter(
        x=r * np.cos(theta), y=r * np.sin(theta),
        mode="lines", line=dict(color="rgba(100,116,139,0.2)", width=1),
        showlegend=False, hoverinfo="skip",
    ))

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
    if len(spray) > 800:
        spray = spray.sample(800, random_state=42)

    for label, color, size, events_filter in [
        ("Out",  THEME["out_fill"],         5, None),
        ("Hit",  OUTCOME_COLORS["single"],  6, ["single", "double", "triple"]),
        ("HR",   OUTCOME_COLORS["home_run"],  8, ["home_run"]),
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
                           showticklabels=False)
    layout["xaxis"]["title"] = dict(text="← Pull · Center · Oppo →",
                                    font=dict(size=9, color=THEME["axis_title"]))
    layout["yaxis"].update(range=[-30, 430], showgrid=False, zeroline=False,
                           showticklabels=False, scaleanchor="x")
    fig.update_layout(**layout)
    return fig


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
    colors = [
        OUTCOME_COLORS["single"],
        THEME["xbh"],
        THEME["xbh"],
        OUTCOME_COLORS["home_run"],
    ]

    data = df[df["events"].isin(hit_events) & df["hit_distance_sc"].notna()]
    if data.empty:
        return fig.update_layout(**_base_layout("Hit Distance by Outcome"))

    for event, color in zip(hit_events, colors):
        sub = data[data["events"] == event]["hit_distance_sc"]
        if sub.empty:
            continue
        fig.add_trace(go.Box(
            y=sub,
            name=event.replace("_", " ").title(),
            marker_color=color,
            line_color=color,
            boxmean=True,
            hovertemplate="%{y:.0f} ft<extra></extra>",
        ))

    layout = _base_layout("Hit Distance by Outcome")
    layout["xaxis"]["title"] = dict(text="Hit Type", font=dict(size=10, color=THEME["axis_title"]))
    layout["yaxis"]["title"] = dict(text="Distance (ft)", font=dict(size=10, color=THEME["axis_title"]))
    layout["showlegend"] = False
    fig.update_layout(**layout)
    return fig


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
    if len(df2) > 1000:
        df2 = df2.sample(1000, random_state=42)
    df2["pitch_label"] = _label_pitch_types(df2["pitch_type"])

    for i, label in enumerate(df2["pitch_label"].unique()):
        sub = df2[df2["pitch_label"] == label]["release_speed"]
        color = THEME["pitch_colors"][i % len(THEME["pitch_colors"])]
        if color.startswith("rgb("):
            fill = color.replace("rgb(", "rgba(").replace(")", ", 0.15)")
        else:
            fill = color
        fig.add_trace(go.Violin(
            y=sub, name=label,
            box_visible=True,
            meanline_visible=True,
            line_color=color,
            fillcolor=fill,
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
    df2["hmov"] = df2["pfx_x"] * 12
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

    fig.add_hline(y=0, line_color=THEME["axis"], line_width=1)
    fig.add_vline(x=0, line_color=THEME["axis"], line_width=1)

    layout = _base_layout("Movement Profile (Catcher's POV)")
    layout["xaxis"].update(
        range=[-24, 24],
        title=dict(text="Horizontal Break (in)", font=dict(size=10, color=THEME["axis_title"]))
    )
    layout["yaxis"].update(
        range=[-20, 30],
        title=dict(text="Vertical Break (in)", font=dict(size=10, color=THEME["axis_title"]))
    )
    fig.update_layout(**layout)
    return fig


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
