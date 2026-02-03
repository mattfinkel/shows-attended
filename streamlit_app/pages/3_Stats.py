"""
Statistics Page
"""
import streamlit as st
import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db import get_db

st.set_page_config(page_title="Stats", page_icon="📊", layout="wide")

# Rename "app" to "Shows" in sidebar
st.markdown("""
    <style>
    /* Rename "app" to "Shows" in sidebar */
    [data-testid="stSidebarNav"] ul li:first-child a span {
        visibility: hidden;
        position: relative;
        width: auto;
        min-width: 60px;
    }
    [data-testid="stSidebarNav"] ul li:first-child a span::before {
        content: "Shows";
        visibility: visible;
        position: absolute;
        left: 0;
        white-space: nowrap;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Statistics")

conn = get_db()
cursor = conn.cursor()

# Overall stats
st.header("Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    cursor.execute("SELECT COUNT(*) FROM shows")
    total_shows = cursor.fetchone()[0]
    st.metric("Total Shows", total_shows)

with col2:
    cursor.execute("SELECT COUNT(*) FROM bands WHERE primary_band_id IS NULL")
    total_bands = cursor.fetchone()[0]
    st.metric("Bands Seen", total_bands)

with col3:
    cursor.execute("SELECT COUNT(*) FROM venues")
    total_venues = cursor.fetchone()[0]
    st.metric("Venues", total_venues)

with col4:
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    st.metric("Events", total_events)

st.divider()

# Shows by year
st.header("Shows by Year")

cursor.execute("""
    SELECT
        strftime('%Y', date) as year,
        COUNT(*) as show_count
    FROM shows
    GROUP BY year
    ORDER BY year DESC
""")

years_data = cursor.fetchall()

if years_data:
    df_years = pd.DataFrame([
        {"Year": row['year'], "Shows": row['show_count']}
        for row in years_data
    ])

    # Bar chart
    st.bar_chart(df_years.set_index("Year"))

    # Table
    with st.expander("View detailed year breakdown"):
        st.dataframe(df_years, use_container_width=True, hide_index=True)

st.divider()

# Top bands
st.header("Top Bands (All Time)")

cursor.execute("""
    SELECT
        COALESCE(b_primary.name, b.name) as name,
        COUNT(sb.id) as times_seen
    FROM bands b
    LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
    LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
        SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
    ))
    WHERE b.primary_band_id IS NULL
    GROUP BY COALESCE(b_primary.id, b.id)
    ORDER BY times_seen DESC
    LIMIT 20
""")

top_bands = cursor.fetchall()

if top_bands:
    df_bands = pd.DataFrame([
        {"Band": row['name'], "Times Seen": row['times_seen']}
        for row in top_bands
    ])

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(df_bands.set_index("Band"))
    with col2:
        st.dataframe(df_bands, use_container_width=True, hide_index=True)

st.divider()

# Top venues
st.header("Top Venues (All Time)")

cursor.execute("""
    SELECT
        v.name,
        v.location,
        COUNT(s.id) as show_count
    FROM venues v
    JOIN shows s ON v.id = s.venue_id
    GROUP BY v.id
    ORDER BY show_count DESC
    LIMIT 20
""")

top_venues = cursor.fetchall()

if top_venues:
    df_venues = pd.DataFrame([
        {"Venue": row['name'], "Shows": row['show_count']}
        for row in top_venues
    ])

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(df_venues.set_index("Venue"))
    with col2:
        st.dataframe(df_venues, use_container_width=True, hide_index=True)

st.divider()

# Events stats
st.header("Events")

cursor.execute("""
    SELECT
        e.name,
        COUNT(s.id) as show_count
    FROM events e
    JOIN shows s ON e.id = s.event_id
    GROUP BY e.id
    ORDER BY show_count DESC
""")

events_data = cursor.fetchall()

if events_data:
    df_events = pd.DataFrame([
        {"Event": row['name'], "Shows": row['show_count']}
        for row in events_data
    ])

    st.dataframe(df_events, use_container_width=True, hide_index=True)
else:
    st.info("No events tracked yet")
