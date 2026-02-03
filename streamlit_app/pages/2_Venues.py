"""
Venues Statistics Page
"""
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Venues", page_icon="📍", layout="wide")

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

DB_PATH = Path(__file__).parent.parent.parent / "webapp_fastapi_old" / "database" / "shows.db"

@st.cache_resource
def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def format_date(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")

def load_venues(search="", min_shows=1, sort_by="count"):
    """Load venue statistics"""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            v.id,
            v.name,
            v.location,
            v.closed,
            COUNT(s.id) as show_count
        FROM venues v
        LEFT JOIN shows s ON v.id = s.venue_id
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND v.name LIKE ?"
        params.append(f"%{search}%")

    query += """
        GROUP BY v.id
        HAVING show_count >= ?
    """
    params.append(min_shows)

    # Add ORDER BY based on sort preference
    if sort_by == "name":
        query += " ORDER BY v.name"
    else:  # count
        query += " ORDER BY show_count DESC, v.name"

    cursor.execute(query, params)
    return cursor.fetchall()

def load_venue_shows(venue_id):
    """Load all shows at a venue"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id,
            s.date,
            e.name as event,
            (
                SELECT GROUP_CONCAT(b2.name, ', ')
                FROM show_bands sb2
                JOIN bands b2 ON sb2.band_id = b2.id
                WHERE sb2.show_id = s.id
                ORDER BY sb2.band_order
            ) as all_bands
        FROM shows s
        LEFT JOIN events e ON s.event_id = e.id
        WHERE s.venue_id = ?
        ORDER BY s.date DESC
    """, (venue_id,))

    return cursor.fetchall()

def update_venue(venue_id, name, location, closed):
    """Update a venue's name, location, and closed status"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE venues SET name = ?, location = ?, closed = ? WHERE id = ?",
            (name, location, closed, venue_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Name already exists

@st.dialog("Edit Venue")
def edit_venue_dialog(venue_id, current_name, current_location, current_closed):
    """Dialog for editing a venue's details"""
    st.write(f"Editing: **{current_name}**")

    new_name = st.text_input("Venue Name", value=current_name, key=f"edit_venue_name_input_{venue_id}")
    new_location = st.text_input("Location", value=current_location or "", key=f"edit_venue_location_input_{venue_id}")
    new_closed = st.checkbox("Venue is closed", value=bool(current_closed), key=f"edit_venue_closed_input_{venue_id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True, key=f"save_venue_{venue_id}"):
            if not new_name.strip():
                st.error("Venue name cannot be empty")
            elif new_name == current_name and new_location == (current_location or "") and new_closed == bool(current_closed):
                st.info("No changes made")
                st.rerun()
            else:
                if update_venue(venue_id, new_name, new_location or None, new_closed):
                    st.success(f"Updated venue")
                    st.rerun()
                else:
                    st.error("A venue with this name already exists")
    with col2:
        if st.button("Cancel", use_container_width=True, key=f"cancel_venue_{venue_id}"):
            st.rerun()

st.title("📍 Venues")

# Filters
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search = st.text_input("🔍 Search venues", placeholder="Type venue name...")
with col2:
    min_shows = st.selectbox("Min shows", [1, 5, 10, 20], index=0)
with col3:
    sort_by = st.selectbox("Sort by", ["Count", "Name"], index=0)

# Load venues
venues = load_venues(search, min_shows, sort_by.lower())

if not venues:
    st.info("No venues found")
else:
    st.subheader(f"Found {len(venues)} venues")

    # Display as cards or table
    view_mode = st.radio("View", ["Cards", "Table"], horizontal=True)

    if view_mode == "Table":
        # Table view
        df_data = []
        for venue in venues:
            venue_name = venue['name']
            if venue['closed']:
                venue_name = f"🔒 {venue_name}"
            df_data.append({
                "Venue": venue_name,
                "Location": venue['location'] or "N/A",
                "Shows": venue['show_count']
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Card view with expandable shows
        for venue in venues:
            venue_display = venue['name']
            if venue['closed']:
                venue_display = f"🔒 {venue_display}"
            with st.expander(f"**{venue_display}** - {venue['show_count']} show{'s' if venue['show_count'] != 1 else ''}"):
                # Edit button and location/status
                col1, col2 = st.columns([6, 1])
                with col1:
                    if venue['location']:
                        st.write(f"📍 {venue['location']}")
                    if venue['closed']:
                        st.caption("🔒 Venue is closed")
                with col2:
                    if st.button("✏️", key=f"edit_venue_{venue['id']}", help="Edit venue"):
                        edit_venue_dialog(venue['id'], venue['name'], venue['location'], venue['closed'])

                st.divider()

                # Load and display shows
                shows = load_venue_shows(venue['id'])

                if shows:
                    st.write(f"**All {len(shows)} shows:**")
                    for show in shows:
                        col1, col2 = st.columns([4, 2])
                        with col1:
                            st.write(f"**{format_date(show['date'])}** - {show['all_bands']}")
                            if show['event']:
                                st.caption(f"_Event: {show['event']}_")
                        with col2:
                            st.caption(f"Show #{show['id']}")
