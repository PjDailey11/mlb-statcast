import pytest
import pandas as pd
import plotly.graph_objects as go
import charts


def test_transform_spray_coords(batting_df):
    result = charts.transform_spray_coords(batting_df)
    assert "spray_x" in result.columns
    assert "spray_y" in result.columns
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
