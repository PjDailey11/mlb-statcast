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
