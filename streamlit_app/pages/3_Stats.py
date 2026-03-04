"""
Statistics Page
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db import get_db
from auth import check_password, show_logout_button
from utils import inject_sidebar_css

st.set_page_config(page_title="Stats", page_icon="📊", layout="wide")

# Check authentication
if not check_password():
    st.stop()

# Show logout button in sidebar
show_logout_button()

inject_sidebar_css()

st.title("📊 Statistics")

@st.cache_data(ttl=300)
def get_stats_overview():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM shows")
    total_shows = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bands WHERE primary_band_id IS NULL")
    total_bands = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM venues")
    total_venues = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM events")
    total_events = cursor.fetchone()[0]
    return total_shows, total_bands, total_venues, total_events

@st.cache_data(ttl=300)
def get_shows_by_year():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT strftime('%Y', date) as year, COUNT(*) as show_count
        FROM shows GROUP BY year ORDER BY year DESC
    """)
    return cursor.fetchall()

@st.cache_data(ttl=300)
def get_top_bands():
    conn = get_db()
    cursor = conn.cursor()
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
    return cursor.fetchall()

@st.cache_data(ttl=300)
def get_top_venues():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT v.name, v.location, COUNT(s.id) as show_count
        FROM venues v JOIN shows s ON v.id = s.venue_id
        GROUP BY v.id ORDER BY show_count DESC LIMIT 20
    """)
    return cursor.fetchall()

@st.cache_data(ttl=300)
def get_events_stats():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT e.name, COUNT(s.id) as show_count
        FROM events e JOIN shows s ON e.id = s.event_id
        GROUP BY e.id ORDER BY show_count DESC
    """)
    return cursor.fetchall()

# Overall stats
st.header("Overview")

total_shows, total_bands, total_venues, total_events = get_stats_overview()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Shows", total_shows)
with col2:
    st.metric("Bands Seen", total_bands)
with col3:
    st.metric("Venues", total_venues)
with col4:
    st.metric("Events", total_events)

st.divider()

# Shows by year
st.header("Shows by Year")

years_data = get_shows_by_year()

if years_data:
    chart_data = {row['year']: row['show_count'] for row in years_data}
    st.bar_chart(chart_data)

    with st.expander("View detailed year breakdown"):
        for row in years_data:
            st.write(f"**{row['year']}**: {row['show_count']} shows")

st.divider()

# Top bands
st.header("Top Bands (All Time)")

top_bands = get_top_bands()

if top_bands:
    chart_data = {row['name']: row['times_seen'] for row in top_bands}

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(chart_data)
    with col2:
        for row in top_bands:
            st.write(f"**{row['name']}**: {row['times_seen']}")

st.divider()

# Top venues
st.header("Top Venues (All Time)")

top_venues = get_top_venues()

if top_venues:
    chart_data = {row['name']: row['show_count'] for row in top_venues}

    col1, col2 = st.columns([2, 1])
    with col1:
        st.bar_chart(chart_data)
    with col2:
        for row in top_venues:
            st.write(f"**{row['name']}**: {row['show_count']}")

st.divider()

# Events stats
st.header("Events")

events_data = get_events_stats()

if events_data:
    for row in events_data:
        st.write(f"**{row['name']}**: {row['show_count']} shows")
else:
    st.info("No events tracked yet")
