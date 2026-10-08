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
        # Argentina/Messi themed GIF
        st.image("https://media.giphy.com/media/3o7TKVm9p5cbGkARbO/giphy.gif", use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Loading Premier League Dataset...</h3>", unsafe_allow_html=True)
    
    # Wait 10 seconds while the GIF plays
    time.sleep(10) 
    
    # Mark intro as played and force a page reload to show the dashboard
    st.session_state['intro_played'] = True
    st.rerun()

# --- DATA PROCESSING (Rubric: Data Preprocessing & Cleaning) ---
@st.cache_data
def load_and_clean_data():
    # Load dataset 
    df = pd.read_csv("player_injuries_impact.csv", na_values=["N.A.", "N.A", "N/A"])
    
    # Clean Rating columns: Extract numeric values from strings like '6(S)'
    rating_cols = [c for c in df.columns if 'rating' in c.lower() and c != 'FIFA rating']
    for col in rating_cols:
        # Extract numbers and convert to float
        df[col] = df[col].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
        
    # Clean Goal Difference (GD) columns
    gd_cols = [c for c in df.columns if 'GD' in c]
    for col in gd_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # Convert Dates
    df['Date of Injury'] = pd.to_datetime(df['Date of Injury'], errors='coerce')
    df['Injury_Month'] = df['Date of Injury'].dt.month_name()
    
    # Feature Engineering
    df['Avg_Rating_Before'] = df[['Match1_before_injury_Player_rating', 'Match2_before_injury_Player_rating', 'Match3_before_injury_Player_rating']].mean(axis=1)
    df['Avg_Rating_After'] = df[['Match1_after_injury_Player_rating', 'Match2_after_injury_Player_rating', 'Match3_after_injury_Player_rating']].mean(axis=1)
    df['Rating_Improvement'] = df['Avg_Rating_After'] - df['Avg_Rating_Before']
    
    df['Avg_GD_Before'] = df[['Match1_before_injury_GD', 'Match2_before_injury_GD', 'Match3_before_injury_GD']].mean(axis=1)
    df['Avg_GD_Missed'] = df[['Match1_missed_match_GD', 'Match2_missed_match_GD', 'Match3_missed_match_GD']].mean(axis=1)
    df['Performance_Drop_Index'] = df['Avg_GD_Before'] - df['Avg_GD_Missed']
    
    return df

# Load the data
df = load_and_clean_data()

# --- DASHBOARD UI ---
st.title("⚽ Player Injuries and Team Performance Dashboard")
st.markdown("---")

# Business Questions Section
with st.expander("📌 View the 5 Key Business Questions"):
    st.markdown("""
    1. Which injuries led to the biggest team performance drop?
    2. What was the team's win/loss record during player absence?
    3. How did individual players perform after recovery?
    4. Are there specific months or clubs with frequent injury clusters?
    5. How does a player's age impact their post-injury FIFA rating recovery?
    """)

# Sidebar Filters
st.sidebar.header("Filter Dashboard")
team_list = ["All Teams"] + list(df['Team Name'].dropna().unique())
selected_team = st.sidebar.selectbox("Select Team", team_list)

if selected_team != "All Teams":
    filtered_df = df[df['Team Name'] == selected_team]
else:
    filtered_df = df

# --- VISUALIZATIONS (Rubric: Build Interactive Visualizations) ---

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Top 10 Injuries (Performance Drop)")
    # Group by injury type to see which hurts team GD the most
    injury_drop = filtered_df.groupby('Injury')['Performance_Drop_Index'].mean().reset_index()
    injury_drop = injury_drop.sort_values(by='Performance_Drop_Index', ascending=False).head(10)
    fig1 = px.bar(injury_drop, x='Injury', y='Performance_Drop_Index', 
                  title="Average Team Goal Difference Drop by Injury",
                  color='Performance_Drop_Index', color_continuous_scale='Reds')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("3. Injury Frequency Clusters")
    # Heatmap of Months vs Clubs
    heatmap_data = pd.crosstab(filtered_df['Injury_Month'], filtered_df['Team Name'])
    fig3 = px.imshow(heatmap_data, text_auto=True, aspect="auto", 
                     title="Injury Occurrences: Month vs Club", color_continuous_scale='Blues')
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.subheader("2. Player Performance Timeline")
    selected_player = st.selectbox("Select a Player to View Timeline", filtered_df['Name'].dropna().unique())
    player_data = filtered_df[filtered_df['Name'] == selected_player].iloc[0]
    
    timeline_y = [
        player_data['Match3_before_injury_Player_rating'],
        player_data['Match2_before_injury_Player_rating'],
        player_data['Match1_before_injury_Player_rating'],
        player_data['Match1_after_injury_Player_rating'],
        player_data['Match2_after_injury_Player_rating'],
        player_data['Match3_after_injury_Player_rating']
    ]
    timeline_x = ['Match -3', 'Match -2', 'Match -1', 'Match +1 (Return)', 'Match +2', 'Match +3']
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=timeline_x, y=timeline_y, mode='lines+markers', name='Rating', line=dict(color='green', width=3)))
    # Add a visual line showing exactly when the injury happened
    fig2.add_vline(x=2.5, line_width=2, line_dash="dash", line_color="red", annotation_text="Injury Occurred")
    fig2.update_layout(title=f"{selected_player}'s Rating Timeline (Pre & Post Injury)", yaxis_title="Match Rating")
    st.plotly_chart(fig2, use_container_width=True)

    st.subheader("4. Age vs. Performance Drop Index")
    fig4 = px.scatter(filtered_df, x='Age', y='Performance_Drop_Index', color='Injury',
                      hover_data=['Name', 'Team Name'], title="Does Age Affect Team Impact During Absence?")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.subheader("5. Leaderboard: Best Comeback Players")
# Sort by highest rating improvement
comeback_df = filtered_df.dropna(subset=['Rating_Improvement']).sort_values(by='Rating_Improvement', ascending=False)
st.dataframe(comeback_df[['Name', 'Team Name', 'Injury', 'Avg_Rating_Before', 'Avg_Rating_After', 'Rating_Improvement']].head(10), use_container_width=True)

st.markdown("---")
# --- BONUS: FIFA ULTIMATE TEAM CARD ---
st.subheader("🎮 FIFA Ultimate Team: Injury Profile Card")
card_player = st.selectbox("Select Player for FIFA Profile", filtered_df['Name'].dropna().unique(), key="fifa_select")
card_data = filtered_df[filtered_df['Name'] == card_player].iloc[0]

# Custom HTML/CSS to render a cool looking FIFA card
st.markdown(f"""
<div style="background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); padding: 20px; border-radius: 15px; width: 350px; color: #1a1a1a; box-shadow: 5px 5px 15px rgba(0,0,0,0.3); border: 2px solid #fff;">
    <h1 style="text-align: center; margin: 0; font-size: 3em;">{card_data['FIFA rating']}</h1>
    <h4 style="text-align: center; margin: 0; text-transform: uppercase;">{card_data['Position']}</h4>
    <h2 style="text-align: center; margin: 10px 0;">{card_data['Name']}</h2>
    <hr style="border: 1px solid #1a1a1a;">
    <p style="margin: 5px 0;"><strong>Club:</strong> {card_data['Team Name']}</p>
    <p style="margin: 5px 0;"><strong>Age:</strong> {card_data['Age']}</p>
    <p style="margin: 5px 0;"><strong>Recent Injury:</strong> {card_data['Injury']}</p>
    <p style="margin: 5px 0;"><strong>Form Change:</strong> {round(card_data['Rating_Improvement'], 2) if pd.notnull(card_data['Rating_Improvement']) else 'N/A'}</p>
</div>
""", unsafe_allow_html=True)
