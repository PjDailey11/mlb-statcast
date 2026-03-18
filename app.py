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
