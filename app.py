import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="FootLens Pro Analytics", layout="wide", page_icon="⚽")

# --- 10-SECOND INTRO ANIMATION ---
if 'intro_played' not in st.session_state:
    st.session_state['intro_played'] = False

if not st.session_state['intro_played']:
    splash = st.empty()
    with splash.container():
        st.markdown("<h1 style='text-align: center; color: #43A1D5; font-size: 4em;'>FootLens AI Analytics</h1>", unsafe_allow_html=True)
        # Using a highly reliable Tenor GIF link
        st.image("https://media.tenor.com/images/792dbcc1bd1f5a54db52ff758d407675/tenor.gif", use_container_width=True)
        st.markdown("<h3 style='text-align: center;'>Initializing Premier League Datasets...</h3>", unsafe_allow_html=True)
    
    time.sleep(10) 
    st.session_state['intro_played'] = True
    st.rerun()

# --- ADVANCED DATA PROCESSING ENGINE ---
@st.cache_data
def load_and_clean_data():
    df = pd.read_csv("player_injuries_impact.csv", na_values=["N.A.", "N.A", "N/A"])
    
    # 1. Clean Ratings (Strip text, convert to float)
    rating_cols = [c for c in df.columns if 'rating' in c.lower() and c != 'FIFA rating']
    for col in rating_cols:
        df[col] = df[col].astype(str).str.extract(r'(\d+\.?\d*)')[0].astype(float)
        
    # 2. Clean Goal Difference (GD)
    gd_cols = [c for c in df.columns if 'GD' in c]
    for col in gd_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        
    # 3. Advanced Date Handling & Recovery Calculation
    df['Date of Injury'] = pd.to_datetime(df['Date of Injury'], errors='coerce')
    df['Date of return'] = pd.to_datetime(df['Date of return'], errors='coerce')
    df['Injury_Month'] = df['Date of Injury'].dt.month_name()
    df['Recovery_Days'] = (df['Date of return'] - df['Date of Injury']).dt.days
    
    # 4. Feature Engineering for Rubric Requirements
    df['Avg_Rating_Before'] = df[['Match1_before_injury_Player_rating', 'Match2_before_injury_Player_rating', 'Match3_before_injury_Player_rating']].mean(axis=1)
    df['Avg_Rating_After'] = df[['Match1_after_injury_Player_rating', 'Match2_after_injury_Player_rating', 'Match3_after_injury_Player_rating']].mean(axis=1)
    df['Rating_Improvement'] = df['Avg_Rating_After'] - df['Avg_Rating_Before']
    
    df['Avg_GD_Before'] = df[['Match1_before_injury_GD', 'Match2_before_injury_GD', 'Match3_before_injury_GD']].mean(axis=1)
    df['Avg_GD_Missed'] = df[['Match1_missed_match_GD', 'Match2_missed_match_GD', 'Match3_missed_match_GD']].mean(axis=1)
    df['Performance_Drop_Index'] = df['Avg_GD_Before'] - df['Avg_GD_Missed']
    
    return df

df = load_and_clean_data()

# --- SIDEBAR & DYNAMIC FILTERING ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1165/1165183.png", width=100)
st.sidebar.title("Data Filters")

team_list = ["All Teams"] + list(df['Team Name'].dropna().unique())
selected_team = st.sidebar.selectbox("Select Club", team_list)

pos_list = ["All Positions"] + list(df['Position'].dropna().unique())
selected_pos = st.sidebar.selectbox("Select Position", pos_list)

# Apply filters
filtered_df = df.copy()
if selected_team != "All Teams":
    filtered_df = filtered_df[filtered_df['Team Name'] == selected_team]
if selected_pos != "All Positions":
    filtered_df = filtered_df[filtered_df['Position'] == selected_pos]

# --- MAIN DASHBOARD UI ---
st.title("⚽ FootLens Pro: Injury Impact & Squad Analytics")
st.markdown("Discovering data-driven insights to minimize injury risks and boost team success.")

# --- DYNAMIC KPI METRICS ---
st.markdown("### 📈 Key Performance Indicators")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Total Players Analyzed", len(filtered_df['Name'].unique()))
kpi2.metric("Total Injury Incidents", len(filtered_df))
kpi3.metric("Avg. Recovery Time", f"{filtered_df['Recovery_Days'].mean():.1f} Days" if pd.notnull(filtered_df['Recovery_Days'].mean()) else "N/A")

# Find worst injury type by performance drop
if not filtered_df.empty:
    worst_injury = filtered_df.groupby('Injury')['Performance_Drop_Index'].mean().idxmax()
    kpi4.metric("Highest Impact Injury", worst_injury)

st.markdown("---")

# --- TABBED NAVIGATION ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Executive Summary", "🏃‍♂️ Player Analytics", "🎮 FIFA Ultimate Team", "📌 Business Context"])

# TAB 1: EXECUTIVE SUMMARY (Team Impact & Clusters)
with tab1:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("1. Top 10 Injuries Sinking Team Performance")
        injury_drop = filtered_df.groupby('Injury')['Performance_Drop_Index'].mean().reset_index()
        injury_drop = injury_drop.sort_values(by='Performance_Drop_Index', ascending=False).head(10)
        fig1 = px.bar(injury_drop, x='Injury', y='Performance_Drop_Index', 
                      color='Performance_Drop_Index', color_continuous_scale='Reds',
                      labels={'Performance_Drop_Index': 'GD Drop Index'})
        st.plotly_chart(fig1, use_container_width=True)

    with col_b:
        st.subheader("2. Injury Frequency Clusters (Month vs Club)")
        heatmap_data = pd.crosstab(df['Injury_Month'], df['Team Name'])
        fig2 = px.imshow(heatmap_data, text_auto=True, aspect="auto", color_continuous_scale='Blues')
        st.plotly_chart(fig2, use_container_width=True)

# TAB 2: PLAYER ANALYTICS (Timelines, Age, and Comebacks)
with tab2:
    st.subheader("3. Player Recovery Timeline")
    selected_player = st.selectbox("Search Player Database", filtered_df['Name'].dropna().unique())
    player_data = filtered_df[filtered_df['Name'] == selected_player].iloc[0]
    
    timeline_y = [
        player_data['Match3_before_injury_Player_rating'], player_data['Match2_before_injury_Player_rating'], 
        player_data['Match1_before_injury_Player_rating'], player_data['Match1_after_injury_Player_rating'], 
        player_data['Match2_after_injury_Player_rating'], player_data['Match3_after_injury_Player_rating']
    ]
    timeline_x = ['Match -3', 'Match -2', 'Match -1', 'Match +1 (Return)', 'Match +2', 'Match +3']
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=timeline_x, y=timeline_y, mode='lines+markers+text', name='Rating', 
                              line=dict(color='#00FF00', width=4), marker=dict(size=10)))
    fig3.add_vline(x=2.5, line_width=3, line_dash="dash", line_color="#FF0000", annotation_text="INJURY OCCURRED")
    fig3.update_layout(yaxis_title="Match Rating (out of 10)", template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)

    col_c, col_d = st.columns(2)
    with col_c:
        st.subheader("4. Risk Analysis: Age vs Performance Drop")
        fig4 = px.scatter(filtered_df, x='Age', y='Performance_Drop_Index', color='Injury',
                          size='Recovery_Days', hover_data=['Name', 'Team Name'], 
                          title="Bubble Size = Days to Recover")
        st.plotly_chart(fig4, use_container_width=True)
        
    with col_d:
        st.subheader("5. Leaderboard: Ultimate Comeback Players")
        comeback_df = filtered_df.dropna(subset=['Rating_Improvement']).sort_values(by='Rating_Improvement', ascending=False)
        st.dataframe(comeback_df[['Name', 'Team Name', 'Injury', 'Avg_Rating_Before', 'Avg_Rating_After', 'Rating_Improvement']].head(10), use_container_width=True, hide_index=True)

# TAB 3: FIFA ULTIMATE TEAM (Premium UI)
with tab3:
    st.subheader("🔍 Interactive FUT Injury Database")
    card_player = st.selectbox("Select Player to view FUT Status", filtered_df['Name'].dropna().unique(), key="fifa_select")
    card_data = filtered_df[filtered_df['Name'] == card_player].iloc[0]

    # Advanced CSS Card Design
    st.markdown(f"""
    <div style="display: flex; justify-content: center;">
        <div style="background: linear-gradient(135deg, #1f1c2c 0%, #928DAB 100%); padding: 30px; border-radius: 20px; width: 400px; color: #FFF; box-shadow: 0px 10px 30px rgba(0,0,0,0.5); border: 3px solid #FFD700;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h1 style="margin: 0; font-size: 4em; color: #FFD700;">{card_data['FIFA rating']}</h1>
                <h2 style="margin: 0; font-size: 2em; text-transform: uppercase;">{card_data['Position']}</h2>
            </div>
            <h2 style="text-align: center; margin: 20px 0; font-size: 2.2em; text-transform: uppercase; letter-spacing: 2px;">{card_data['Name']}</h2>
            <hr style="border: 1px solid #FFD700; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; font-size: 1.2em;">
                <p><strong>Club:</strong><br>{card_data['Team Name']}</p>
                <p style="text-align: right;"><strong>Age:</strong><br>{card_data['Age']}</p>
            </div>
            <div style="background-color: rgba(255,0,0,0.2); padding: 10px; border-radius: 10px; margin-top: 15px; border: 1px solid #FF0000;">
                <p style="margin: 0; text-align: center; color: #FFA07A;"><strong>⚠️ Last Injury:</strong> {card_data['Injury']}</p>
                <p style="margin: 5px 0 0 0; text-align: center;"><strong>Time Out:</strong> {card_data['Recovery_Days']} Days</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# TAB 4: BUSINESS CONTEXT
with tab4:
    st.header("📌 Project Rationale & Research")
    st.markdown("""
    **Framing the Analytics Scope (Top 5 Business Questions):**
    1. **Which specific injuries trigger the most significant drop in team Goal Difference (GD)?** *(Addressed in Tab 1 Bar Chart)*
    2. **Are there temporal or club-based clusters of frequent injuries that suggest systemic training issues?** *(Addressed in Tab 1 Heatmap)*
    3. **How is a player's individual form affected immediately post-recovery compared to their pre-injury baseline?** *(Addressed in Tab 2 Timeline)*
    4. **Does a player's age positively correlate with a longer recovery time and a harsher drop in team performance during their absence?** *(Addressed in Tab 2 Scatter Plot)*
    5. **Which players demonstrate the strongest psychological and physical resilience by improving their match ratings post-injury?** *(Addressed in Tab 2 Leaderboard)*
    """)
