import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# Configure page settings
st.set_page_config(page_title="FootLens Analytics", layout="wide", page_icon="⚽")

# --- 10-SECOND INTRO ANIMATION FIX ---
if 'intro_played' not in st.session_state:
    st.session_state['intro_played'] = False

if not st.session_state['intro_played']:
    splash = st.empty()
    with splash.container():
        st.markdown("<h1 style='text-align: center; color: #43A1D5;'>FootLens Analytics: Injury Impact</h1>", unsafe_allow_html=True)
        st.image("https://media.giphy.com/media/3o7TKVm9p5cbGkARbO/giphy.gif", use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Loading Premier League Dataset...</h3>", unsafe_allow_html=True)
    
    # Wait 10 seconds while the GIF plays
    time.sleep(10) 
    
    # Mark intro as played and force a page reload to show the dashboard
    st.session_state['intro_played'] = True
    st.rerun()

# --- DATA PROCESSING ---
@st.cache_data
def load_and_clean_data():
    # Load dataset (Make sure player_injuries_impact.csv is in your GitHub repo!)
    df = pd.read_csv("player_injuries_impact.csv", na_values=["N.A.", "N.A", "N/A"])
