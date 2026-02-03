"""
Shows Attended - Streamlit App
Main page: Shows list with search and filters
"""
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime

# Page config
st.set_page_config(
    page_title="Shows Attended",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better mobile experience
st.markdown("""
    <style>
    /* Make it more compact on mobile */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Better card styling */
    .show-card {
        background: #262730;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        border-left: 3px solid #FF6B6B;
        position: relative;
    }

    .show-date {
        color: #B0B0B0;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }

    .show-bands {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #FAFAFA;
    }

    .show-venue {
        color: #B0B0B0;
        font-size: 0.9rem;
    }

    .show-event {
        color: #B0B0B0;
        font-size: 0.85rem;
        font-style: italic;
        margin-top: 0.25rem;
    }

    /* Delete warning box */
    .delete-warning {
        background-color: #3d1a1a;
        padding: 1rem;
        border-radius: 8px;
        border: 2px solid #FF6B6B;
        margin: 0.5rem 0;
    }

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

# Database path
DB_PATH = Path(__file__).parent.parent / "webapp_fastapi_old" / "database" / "shows.db"

@st.cache_resource
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def format_date(date_str):
    """Format date string"""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%b %d, %Y")

def load_shows(search="", year=None):
    """Load shows with filters"""
    conn = get_db()
    cursor = conn.cursor()

    where_conditions = ["1=1"]
    params = []

    if search:
        where_conditions.append("""s.id IN (
            SELECT sb2.show_id FROM show_bands sb2
            JOIN bands b2 ON sb2.band_id = b2.id
            WHERE b2.name LIKE ?
        )""")
        params.append(f"%{search}%")

    if year and year != "All Years":
        where_conditions.append("strftime('%Y', s.date) = ?")
        params.append(str(year))

    where_clause = " AND ".join(where_conditions)

    query = f"""
        SELECT
            s.id,
            s.date,
            v.name as venue_name,
            v.location as venue_location,
            e.name as event,
            (
                SELECT GROUP_CONCAT(b2.name, ', ')
                FROM show_bands sb2
                JOIN bands b2 ON sb2.band_id = b2.id
                WHERE sb2.show_id = s.id
                ORDER BY sb2.band_order
            ) as all_bands
        FROM shows s
        JOIN venues v ON s.venue_id = v.id
        LEFT JOIN events e ON s.event_id = e.id
        WHERE {where_clause}
        ORDER BY s.date DESC
    """

    cursor.execute(query, params)
    return cursor.fetchall()

def load_years():
    """Load available years"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT strftime('%Y', date) as year FROM shows ORDER BY year DESC")
    return [row['year'] for row in cursor.fetchall()]

def delete_show(show_id):
    """Delete a show and cleanup orphans"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Delete show
        cursor.execute("DELETE FROM shows WHERE id = ?", (show_id,))

        # Cleanup orphans
        cursor.execute("DELETE FROM show_bands WHERE show_id NOT IN (SELECT id FROM shows)")
        cursor.execute("DELETE FROM bands WHERE id NOT IN (SELECT DISTINCT band_id FROM show_bands)")
        cursor.execute("DELETE FROM venues WHERE id NOT IN (SELECT DISTINCT venue_id FROM shows)")
        cursor.execute("DELETE FROM events WHERE id NOT IN (SELECT DISTINCT event_id FROM shows WHERE event_id IS NOT NULL)")

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Error deleting show: {e}")
        return False

def get_all_bands():
    """Get all band names for autocomplete"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM bands ORDER BY name")
    return [row['name'] for row in cursor.fetchall()]

def get_all_venues():
    """Get all venue names for autocomplete"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name, location FROM venues ORDER BY name")
    return [(row['name'], row['location']) for row in cursor.fetchall()]

def get_all_events():
    """Get all event names for autocomplete"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM events ORDER BY name")
    return [row['name'] for row in cursor.fetchall()]

def lookup_venue_address(venue_name):
    """Look up venue address using Nominatim (OpenStreetMap)"""
    import urllib.parse
    import urllib.request
    import json
    import time

    try:
        # URL encode the venue name
        query = urllib.parse.quote(venue_name)
        url = f"https://nominatim.openstreetmap.org/search?q={query}&format=json&limit=1"

        # Add user agent (required by Nominatim)
        req = urllib.request.Request(url, headers={'User-Agent': 'ShowsAttendedApp/1.0'})

        # Rate limit: wait 1 second between requests
        time.sleep(1)

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read())

            if data and len(data) > 0:
                return data[0].get('display_name', '')
    except Exception as e:
        st.warning(f"Could not auto-lookup address: {e}")

    return None

# Main app
col1, col2 = st.columns([4, 1])
with col1:
    st.title("🎸 Shows")
with col2:
    st.write("")  # Spacing
    if st.button("➕ Add Show", use_container_width=True, type="primary"):
        st.session_state.adding_show = True

# Sidebar for filters
with st.sidebar:
    st.header("Filters")

    search = st.text_input("🔍 Search bands", placeholder="Type band name...")

    years = ["All Years"] + load_years()
    year = st.selectbox("📅 Year", years)

    st.divider()

    # Quick stats
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM shows")
    total_shows = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM bands")
    total_bands = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM venues")
    total_venues = cursor.fetchone()[0]

    st.metric("Total Shows", total_shows)
    st.metric("Bands Seen", total_bands)
    st.metric("Venues", total_venues)

# Main content
shows = load_shows(search, year)

if not shows:
    st.info("No shows found. Try adjusting your filters.")
else:
    st.subheader(f"Showing {len(shows)} shows")

    # Display shows
    for show in shows:
        # Create a container for each show
        with st.container():
            col1, col2 = st.columns([6, 1])

            with col1:
                # Show content
                bands_html = show['all_bands'] if show['all_bands'] else 'No bands listed'
                event_html = f"<div class='show-event'>{show['event']}</div>" if show['event'] else ""

                st.markdown(f"""
                    <div class='show-card'>
                        <div class='show-date'>{format_date(show['date'])}</div>
                        <div class='show-bands'>{bands_html}</div>
                        <div class='show-venue'>{show['venue_name']}</div>
                        {event_html}
                    </div>
                """, unsafe_allow_html=True)

            with col2:
                # Edit button on the right
                if st.button("Edit", key=f"edit_{show['id']}", use_container_width=True):
                    st.session_state.editing_show_id = show['id']

# Edit dialog
if 'editing_show_id' in st.session_state:
    show_id = st.session_state.editing_show_id

    @st.dialog("Edit Show", width="large")
    def edit_show_dialog(show_id):
        conn = get_db()
        cursor = conn.cursor()

        # Load show data
        cursor.execute("""
            SELECT s.*, v.name as venue_name, v.id as venue_id, e.name as event_name, e.id as event_id
            FROM shows s
            JOIN venues v ON s.venue_id = v.id
            LEFT JOIN events e ON s.event_id = e.id
            WHERE s.id = ?
        """, (show_id,))
        show_data = cursor.fetchone()

        # Load bands
        cursor.execute("""
            SELECT b.id, b.name, sb.band_order
            FROM show_bands sb
            JOIN bands b ON sb.band_id = b.id
            WHERE sb.show_id = ?
            ORDER BY sb.band_order
        """, (show_id,))
        show_bands = [row['name'] for row in cursor.fetchall()]

        # Initialize edit bands in session state
        if f'edit_bands_{show_id}' not in st.session_state:
            st.session_state[f'edit_bands_{show_id}'] = show_bands.copy()

        edit_bands = st.session_state[f'edit_bands_{show_id}']

        # Date
        show_date = st.date_input("Date", value=datetime.strptime(show_data['date'], "%Y-%m-%d").date())

        st.divider()

        # Bands
        st.subheader("Bands (in order)")

        all_bands = get_all_bands()

        col1, col2 = st.columns([5, 1])
        with col1:
            new_band = st.selectbox("Add band", [""] + all_bands, key=f"band_select_{show_id}")
        with col2:
            st.write("")
            st.write("")
            if st.button("Add", key=f"add_band_{show_id}"):
                if new_band and new_band not in edit_bands:
                    edit_bands.append(new_band)
                    st.rerun()

        # Display current bands
        if edit_bands:
            for i, band in enumerate(edit_bands):
                col1, col2, col3 = st.columns([1, 5, 1])
                with col1:
                    st.write(f"**{i+1}.**")
                with col2:
                    st.write(band)
                with col3:
                    if st.button("✕", key=f"remove_band_{show_id}_{i}"):
                        edit_bands.pop(i)
                        st.rerun()
        else:
            st.info("Add at least one band")

        st.divider()

        # Venue
        st.subheader("📍 Venue")

        all_venues = get_all_venues()
        venue_names = [v[0] for v in all_venues]
        venue_options = ["+ New Venue"] + venue_names

        # Adjust index since we added "+ New Venue" at the top
        current_venue_idx = venue_names.index(show_data['venue_name']) + 1 if show_data['venue_name'] in venue_names else 0
        venue = st.selectbox("Venue", venue_options, index=current_venue_idx)

        venue_name = venue
        venue_location = None

        if venue == "+ New Venue":
            # Initialize session state for new venue in edit
            if f'edit_last_venue_lookup_{show_id}' not in st.session_state:
                st.session_state[f'edit_last_venue_lookup_{show_id}'] = ""

            venue_name = st.text_input(
                "Venue name*",
                key=f"edit_venue_name_input_{show_id}",
                placeholder="e.g., The Sinclair Cambridge MA"
            )

            # Auto-lookup when venue name changes and is long enough
            if venue_name and len(venue_name) > 3 and venue_name != st.session_state[f'edit_last_venue_lookup_{show_id}']:
                with st.spinner("Looking up address..."):
                    looked_up = lookup_venue_address(venue_name)
                    if looked_up:
                        st.session_state[f'edit_venue_location_input_{show_id}'] = looked_up
                        st.session_state[f'edit_last_venue_lookup_{show_id}'] = venue_name
                        st.success(f"✓ Found address")
                        st.rerun()

            col1, col2 = st.columns([4, 1])
            with col1:
                venue_location = st.text_input(
                    "Venue address* (required)",
                    key=f"edit_venue_location_input_{show_id}",
                    placeholder="Auto-fills as you type venue name above"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("🔍 Retry", key=f"lookup_btn_{show_id}", help="Re-lookup address"):
                    if venue_name:
                        with st.spinner("Looking up address..."):
                            looked_up = lookup_venue_address(venue_name)
                            if looked_up:
                                st.session_state[f'edit_venue_location_input_{show_id}'] = looked_up
                                st.session_state[f'edit_last_venue_lookup_{show_id}'] = venue_name
                                st.success("Address found!")
                                st.rerun()
                            else:
                                st.warning("Address not found. Please enter manually.")
                    else:
                        st.warning("Enter venue name first")

        elif venue and venue != "":
            # Show existing location
            venue_data = [v for v in all_venues if v[0] == venue]
            if venue_data and venue_data[0][1]:
                st.caption(f"📍 {venue_data[0][1]}")
            else:
                st.caption("⚠️ No address on file")

        st.divider()

        # Event
        st.subheader("🎉 Event (optional)")

        all_events = get_all_events()
        event_options = ["", "+ New Event"] + all_events

        # Adjust index since we added "+ New Event" at position 1
        current_event_idx = 0
        if show_data['event_name'] and show_data['event_name'] in all_events:
            current_event_idx = all_events.index(show_data['event_name']) + 2  # +2 because of "" and "+ New Event"

        event = st.selectbox("Event (optional)", event_options, index=current_event_idx)

        event_name = event if event and event != "+ New Event" and event != "" else None

        if event == "+ New Event":
            event_name = st.text_input("Event name", key=f"new_event_name_{show_id}")

        st.divider()

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("Cancel", use_container_width=True):
                del st.session_state.editing_show_id
                if f'edit_bands_{show_id}' in st.session_state:
                    del st.session_state[f'edit_bands_{show_id}']
                st.rerun()

        with col2:
            if st.button("Save Changes", type="primary", use_container_width=True):
                # Validation
                if not venue_name or not edit_bands:
                    st.error("Please fill in venue and at least one band")
                elif venue == "+ New Venue" and not venue_location:
                    st.error("❌ Please fill in venue address (use 🔍 Lookup button or enter manually)")
                else:
                    try:
                        # Get or create venue
                        cursor.execute("SELECT id FROM venues WHERE name = ?", (venue_name,))
                        venue_row = cursor.fetchone()
                        if venue_row:
                            venue_id = venue_row['id']
                        else:
                            cursor.execute("INSERT INTO venues (name, location) VALUES (?, ?)",
                                         (venue_name, venue_location))
                            venue_id = cursor.lastrowid

                        # Get or create event
                        event_id = None
                        if event_name:
                            cursor.execute("SELECT id FROM events WHERE name = ?", (event_name,))
                            event_row = cursor.fetchone()
                            if event_row:
                                event_id = event_row['id']
                            else:
                                cursor.execute("INSERT INTO events (name) VALUES (?)", (event_name,))
                                event_id = cursor.lastrowid

                        # Update show
                        cursor.execute(
                            "UPDATE shows SET date = ?, venue_id = ?, event_id = ? WHERE id = ?",
                            (show_date.isoformat(), venue_id, event_id, show_id)
                        )

                        # Delete existing band relationships
                        cursor.execute("DELETE FROM show_bands WHERE show_id = ?", (show_id,))

                        # Add new band relationships
                        for order, band_name in enumerate(edit_bands, 1):
                            # Get or create band
                            cursor.execute("SELECT id FROM bands WHERE name = ?", (band_name,))
                            band_row = cursor.fetchone()
                            if band_row:
                                band_id = band_row['id']
                            else:
                                cursor.execute("INSERT INTO bands (name) VALUES (?)", (band_name,))
                                band_id = cursor.lastrowid

                            # Create show-band relationship
                            cursor.execute(
                                "INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                                (show_id, band_id, order)
                            )

                        conn.commit()
                        st.success("Show updated successfully!")
                        del st.session_state.editing_show_id
                        if f'edit_bands_{show_id}' in st.session_state:
                            del st.session_state[f'edit_bands_{show_id}']
                        st.rerun()

                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error updating show: {e}")

        with col3:
            # Delete with confirmation
            if f'confirm_delete_{show_id}' not in st.session_state:
                st.session_state[f'confirm_delete_{show_id}'] = False

            if not st.session_state[f'confirm_delete_{show_id}']:
                if st.button("🗑️ Delete", use_container_width=True):
                    st.session_state[f'confirm_delete_{show_id}'] = True
                    st.rerun()

        # Show confirmation if delete was clicked
        if st.session_state.get(f'confirm_delete_{show_id}', False):
            st.markdown('<div class="delete-warning">', unsafe_allow_html=True)
            st.error("⚠️ **Are you sure you want to delete this show?**")
            st.write("This action cannot be undone.")
            st.markdown('</div>', unsafe_allow_html=True)

            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("✓ Yes, Delete Forever", use_container_width=True, type="primary"):
                    if delete_show(show_id):
                        st.success("Show deleted!")
                        del st.session_state.editing_show_id
                        if f'edit_bands_{show_id}' in st.session_state:
                            del st.session_state[f'edit_bands_{show_id}']
                        if f'confirm_delete_{show_id}' in st.session_state:
                            del st.session_state[f'confirm_delete_{show_id}']
                        st.rerun()
            with col_no:
                if st.button("✗ Cancel", use_container_width=True):
                    st.session_state[f'confirm_delete_{show_id}'] = False
                    st.rerun()

    edit_show_dialog(show_id)

# Add show dialog
if 'adding_show' in st.session_state and st.session_state.adding_show:
    @st.dialog("Add Show", width="large")
    def add_show_dialog():
        from datetime import date

        # Initialize session state for bands
        if 'add_show_bands' not in st.session_state:
            st.session_state.add_show_bands = []

        # Date
        show_date = st.date_input("📅 Date", value=date.today())

        st.divider()

        # Bands
        st.subheader("🎸 Bands (in order)")

        all_bands = get_all_bands()

        col1, col2 = st.columns([5, 1])
        with col1:
            new_band = st.selectbox("Add band", [""] + all_bands, key="add_band_select")
        with col2:
            st.write("")
            st.write("")
            if st.button("Add", key="add_band_btn"):
                if new_band and new_band not in st.session_state.add_show_bands:
                    st.session_state.add_show_bands.append(new_band)
                    st.rerun()

        # Display current bands
        if st.session_state.add_show_bands:
            for i, band in enumerate(st.session_state.add_show_bands):
                col1, col2, col3 = st.columns([1, 5, 1])
                with col1:
                    st.write(f"**{i+1}.**")
                with col2:
                    st.write(band)
                with col3:
                    if st.button("✕", key=f"remove_add_band_{i}"):
                        st.session_state.add_show_bands.pop(i)
                        st.rerun()
        else:
            st.info("Add at least one band")

        st.divider()

        # Venue
        st.subheader("📍 Venue")

        all_venues = get_all_venues()
        venue_names = [v[0] for v in all_venues]

        venue = st.selectbox("Venue", ["", "+ New Venue"] + venue_names)

        venue_name = venue
        venue_location = None

        if venue == "+ New Venue":
            # Initialize session state for new venue
            if 'last_venue_lookup' not in st.session_state:
                st.session_state.last_venue_lookup = ""

            venue_name = st.text_input(
                "Venue name*",
                key="add_venue_name_input",
                placeholder="e.g., The Sinclair Cambridge MA"
            )

            # Auto-lookup when venue name changes and is long enough
            if venue_name and len(venue_name) > 3 and venue_name != st.session_state.last_venue_lookup:
                with st.spinner("Looking up address..."):
                    looked_up = lookup_venue_address(venue_name)
                    if looked_up:
                        st.session_state.add_venue_location_input = looked_up
                        st.session_state.last_venue_lookup = venue_name
                        st.success(f"✓ Found address")
                        st.rerun()

            col1, col2 = st.columns([4, 1])
            with col1:
                venue_location = st.text_input(
                    "Venue address* (required)",
                    key="add_venue_location_input",
                    placeholder="Auto-fills as you type venue name above"
                )
            with col2:
                st.write("")
                st.write("")
                if st.button("🔍 Retry", help="Re-lookup address"):
                    if venue_name:
                        with st.spinner("Looking up address..."):
                            looked_up = lookup_venue_address(venue_name)
                            if looked_up:
                                st.session_state.add_venue_location_input = looked_up
                                st.session_state.last_venue_lookup = venue_name
                                st.success("Address found!")
                                st.rerun()
                            else:
                                st.warning("Address not found. Please enter manually.")
                    else:
                        st.warning("Enter venue name first")

        elif venue and venue != "":
            # Show existing location
            venue_data = [v for v in all_venues if v[0] == venue]
            if venue_data and venue_data[0][1]:
                st.caption(f"📍 {venue_data[0][1]}")
            else:
                st.caption("⚠️ No address on file")

        st.divider()

        # Event
        st.subheader("🎉 Event (optional)")

        all_events = get_all_events()
        event = st.selectbox("Event", ["", "+ New Event"] + all_events)

        event_name = event if event and event != "+ New Event" and event != "" else None

        if event == "+ New Event":
            event_name = st.text_input("Event name")

        st.divider()

        # Action buttons
        col1, col2 = st.columns(2)

        with col1:
            if st.button("Cancel", use_container_width=True):
                st.session_state.adding_show = False
                st.session_state.add_show_bands = []
                # Clear venue state
                if 'add_venue_name_input' in st.session_state:
                    del st.session_state.add_venue_name_input
                if 'add_venue_location_input' in st.session_state:
                    del st.session_state.add_venue_location_input
                if 'last_venue_lookup' in st.session_state:
                    del st.session_state.last_venue_lookup
                st.rerun()

        with col2:
            if st.button("Add Show", type="primary", use_container_width=True):
                # Validation
                if not venue_name or not st.session_state.add_show_bands:
                    st.error("❌ Please fill in venue and at least one band")
                elif venue == "+ New Venue" and not venue_location:
                    st.error("❌ Please fill in venue address (use 🔍 Lookup button or enter manually)")
                else:
                    conn = get_db()
                    cursor = conn.cursor()

                    try:
                        # Get or create venue
                        cursor.execute("SELECT id FROM venues WHERE name = ?", (venue_name,))
                        venue_row = cursor.fetchone()
                        if venue_row:
                            venue_id = venue_row['id']
                        else:
                            cursor.execute("INSERT INTO venues (name, location) VALUES (?, ?)",
                                         (venue_name, venue_location))
                            venue_id = cursor.lastrowid

                        # Get or create event
                        event_id = None
                        if event_name:
                            cursor.execute("SELECT id FROM events WHERE name = ?", (event_name,))
                            event_row = cursor.fetchone()
                            if event_row:
                                event_id = event_row['id']
                            else:
                                cursor.execute("INSERT INTO events (name) VALUES (?)", (event_name,))
                                event_id = cursor.lastrowid

                        # Create show
                        cursor.execute("INSERT INTO shows (date, venue_id, event_id) VALUES (?, ?, ?)",
                                     (show_date.isoformat(), venue_id, event_id))
                        show_id = cursor.lastrowid

                        # Add bands
                        for order, band_name in enumerate(st.session_state.add_show_bands, 1):
                            # Get or create band
                            cursor.execute("SELECT id FROM bands WHERE name = ?", (band_name,))
                            band_row = cursor.fetchone()
                            if band_row:
                                band_id = band_row['id']
                            else:
                                cursor.execute("INSERT INTO bands (name) VALUES (?)", (band_name,))
                                band_id = cursor.lastrowid

                            # Create show-band relationship
                            cursor.execute("INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                                         (show_id, band_id, order))

                        conn.commit()
                        st.success("✅ Show added successfully!")
                        st.session_state.adding_show = False
                        st.session_state.add_show_bands = []
                        # Clear venue state
                        if 'add_venue_name_input' in st.session_state:
                            del st.session_state.add_venue_name_input
                        if 'add_venue_location_input' in st.session_state:
                            del st.session_state.add_venue_location_input
                        if 'last_venue_lookup' in st.session_state:
                            del st.session_state.last_venue_lookup
                        st.rerun()

                    except Exception as e:
                        conn.rollback()
                        st.error(f"❌ Error adding show: {e}")

    add_show_dialog()
