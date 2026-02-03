"""
Bands Statistics Page
"""
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Bands", page_icon="🎸", layout="wide")

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

def load_bands(search="", min_shows=1, sort_by="count"):
    """Load band statistics with grouping support"""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            COALESCE(b_primary.id, b.id) as id,
            COALESCE(b_primary.name, b.name) as name,
            COUNT(sb.id) as times_seen,
            MIN(s.date) as first_show,
            MAX(s.date) as last_show
        FROM bands b
        LEFT JOIN bands b_primary ON b.primary_band_id = b_primary.id
        LEFT JOIN show_bands sb ON (sb.band_id = b.id OR sb.band_id IN (
            SELECT id FROM bands WHERE primary_band_id = COALESCE(b_primary.id, b.id)
        ))
        LEFT JOIN shows s ON sb.show_id = s.id
        WHERE b.primary_band_id IS NULL
    """

    params = []

    if search:
        query += " AND COALESCE(b_primary.name, b.name) LIKE ?"
        params.append(f"%{search}%")

    query += """
        GROUP BY COALESCE(b_primary.id, b.id)
        HAVING times_seen >= ?
    """
    params.append(min_shows)

    # Add ORDER BY based on sort preference
    if sort_by == "name":
        query += " ORDER BY COALESCE(b_primary.name, b.name)"
    else:  # count
        query += " ORDER BY times_seen DESC, COALESCE(b_primary.name, b.name)"

    cursor.execute(query, params)
    return cursor.fetchall()

def load_band_shows(band_id):
    """Load all shows for a band and its aliases"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id,
            s.date,
            v.name as venue_name,
            v.location as venue_location,
            e.name as event,
            b_actual.name as actual_band_name,
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
        JOIN show_bands sb ON sb.show_id = s.id
        JOIN bands b_actual ON sb.band_id = b_actual.id
        WHERE sb.band_id IN (
            SELECT id FROM bands WHERE id = ? OR primary_band_id = ?
        )
        ORDER BY s.date DESC
    """, (band_id, band_id))

    return cursor.fetchall()

def create_band_group(primary_band_id, alias_band_ids):
    """Create a new band group by setting aliases"""
    conn = get_db()
    cursor = conn.cursor()
    for alias_id in alias_band_ids:
        cursor.execute(
            "UPDATE bands SET primary_band_id = ? WHERE id = ?",
            (primary_band_id, alias_id)
        )
    conn.commit()

def add_alias_to_group(primary_band_id, alias_band_id):
    """Add a single alias to an existing group"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bands SET primary_band_id = ? WHERE id = ?",
        (primary_band_id, alias_band_id)
    )
    conn.commit()

def remove_alias_from_group(alias_band_id):
    """Remove a band from its group (make it standalone)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bands SET primary_band_id = NULL WHERE id = ?",
        (alias_band_id,)
    )
    conn.commit()

def disband_group(primary_band_id):
    """Remove all aliases from a group"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE bands SET primary_band_id = NULL WHERE primary_band_id = ?",
        (primary_band_id,)
    )
    conn.commit()

def load_band_groups():
    """Load all band groupings for display"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            b_primary.id as primary_id,
            b_primary.name as primary_name,
            b_alias.id as alias_id,
            b_alias.name as alias_name,
            COUNT(DISTINCT sb.show_id) as alias_show_count
        FROM bands b_primary
        LEFT JOIN bands b_alias ON b_alias.primary_band_id = b_primary.id
        LEFT JOIN show_bands sb ON sb.band_id = b_alias.id
        WHERE b_alias.id IS NOT NULL
        GROUP BY b_primary.id, b_alias.id
        ORDER BY b_primary.name, b_alias.name
    """)
    return cursor.fetchall()

def get_primary_band_show_count(primary_band_id):
    """Get total show count for a primary band including all aliases"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT sb.show_id) as total_shows
        FROM show_bands sb
        WHERE sb.band_id IN (
            SELECT id FROM bands WHERE id = ? OR primary_band_id = ?
        )
    """, (primary_band_id, primary_band_id))
    result = cursor.fetchone()
    return result['total_shows'] if result else 0

def get_band_show_count(band_id):
    """Get show count for a specific band (not including aliases)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(DISTINCT sb.show_id) as show_count
        FROM show_bands sb
        WHERE sb.band_id = ?
    """, (band_id,))
    result = cursor.fetchone()
    return result['show_count'] if result else 0

def get_standalone_bands():
    """Get all bands that are not part of any group (for dropdowns)"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, name
        FROM bands
        WHERE primary_band_id IS NULL
        ORDER BY name
    """)
    return cursor.fetchall()

def update_band_name(band_id, new_name):
    """Update a band's name"""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE bands SET name = ? WHERE id = ?",
            (new_name, band_id)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Name already exists

@st.dialog("Edit Band Name")
def edit_band_dialog(band_id, current_name):
    """Dialog for editing a band's name"""
    st.write(f"Editing: **{current_name}**")

    new_name = st.text_input("Band Name", value=current_name, key=f"edit_band_name_input_{band_id}")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save", type="primary", use_container_width=True, key=f"save_band_{band_id}"):
            if not new_name.strip():
                st.error("Band name cannot be empty")
            elif new_name == current_name:
                st.info("No changes made")
                st.rerun()
            else:
                if update_band_name(band_id, new_name):
                    st.success(f"Updated to '{new_name}'")
                    st.rerun()
                else:
                    st.error("A band with this name already exists")
    with col2:
        if st.button("Cancel", use_container_width=True, key=f"cancel_band_{band_id}"):
            st.rerun()

@st.dialog("Manage Band Groups")
def manage_band_groups_dialog():
    """Dialog for managing band groupings"""
    st.subheader("Current Groupings")

    groups = load_band_groups()
    if not groups:
        st.info("No band groups created yet")
    else:
        # Organize groups by primary band
        groups_dict = {}
        for row in groups:
            primary_id = row['primary_id']
            if primary_id not in groups_dict:
                groups_dict[primary_id] = {
                    'name': row['primary_name'],
                    'aliases': []
                }
            groups_dict[primary_id]['aliases'].append({
                'id': row['alias_id'],
                'name': row['alias_name'],
                'show_count': row['alias_show_count']
            })

        # Display each group
        for primary_id, group_info in groups_dict.items():
            # Get total show count for primary band
            total_shows = get_primary_band_show_count(primary_id)
            with st.expander(f"📍 {group_info['name']} ({total_shows} shows total)", expanded=True):
                # Display primary band first (without remove button)
                primary_show_count = get_band_show_count(primary_id)
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.write(f"├─ **{group_info['name']}** ({primary_show_count} shows) - Primary")
                with col2:
                    st.write("")  # No remove button for primary

                # Display aliases
                for alias in group_info['aliases']:
                    col1, col2 = st.columns([5, 1])
                    with col1:
                        st.write(f"├─ {alias['name']} ({alias['show_count']} shows)")
                    with col2:
                        if st.button("✕", key=f"remove_{alias['id']}", help="Remove from group"):
                            remove_alias_from_group(alias['id'])
                            st.rerun()

                st.divider()

                # Add alias to existing group
                col1, col2 = st.columns([3, 1])
                with col1:
                    standalone_bands = get_standalone_bands()
                    if standalone_bands:
                        band_options = {band['name']: band['id'] for band in standalone_bands}
                        selected_alias = st.selectbox(
                            "Add alias",
                            options=list(band_options.keys()),
                            index=None,
                            placeholder="Select a band...",
                            key=f"add_alias_{primary_id}"
                        )
                with col2:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if standalone_bands and selected_alias and st.button("Add", key=f"add_button_{primary_id}"):
                        add_alias_to_group(primary_id, band_options[selected_alias])
                        st.rerun()

                # Disband group
                if st.button(f"Disband Group", key=f"disband_{primary_id}", type="secondary"):
                    disband_group(primary_id)
                    st.rerun()

    st.divider()
    st.subheader("Create New Group")

    standalone_bands = get_standalone_bands()
    if len(standalone_bands) < 2:
        st.warning("Need at least 2 standalone bands to create a group")
    else:
        band_options = {band['name']: band['id'] for band in standalone_bands}

        primary_band = st.selectbox(
            "Select Primary Band",
            options=list(band_options.keys()),
            index=None,
            placeholder="Select a band...",
            key="new_primary"
        )

        # Filter out the primary band from alias options
        if primary_band:
            alias_options = {name: id for name, id in band_options.items()
                            if id != band_options[primary_band]}

            if alias_options:
                alias_bands = st.multiselect(
                    "Select Alias Bands",
                    options=list(alias_options.keys()),
                    placeholder="Select one or more bands...",
                    key="new_aliases"
                )

                if st.button("Create Group", type="primary"):
                    if not alias_bands:
                        st.error("Please select at least one alias band")
                    else:
                        alias_ids = [alias_options[name] for name in alias_bands]
                        create_band_group(band_options[primary_band], alias_ids)
                        st.success(f"Created group for {primary_band}")
                        st.rerun()
        else:
            st.info("Select a primary band to continue")

st.title("🎸 Bands")

# Header with manage button
col1, col2 = st.columns([6, 1])
with col1:
    st.write("")  # Spacing
with col2:
    if st.button("⚙️ Manage Groups"):
        manage_band_groups_dialog()

# Filters
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    search = st.text_input("🔍 Search bands", placeholder="Type band name...")
with col2:
    min_shows = st.selectbox("Min shows", [1, 5, 10, 20], index=0)
with col3:
    sort_by = st.selectbox("Sort by", ["Count", "Name"], index=0)

# Load bands
bands = load_bands(search, min_shows, sort_by.lower())

if not bands:
    st.info("No bands found")
else:
    st.subheader(f"Found {len(bands)} bands")

    # Display as cards or table
    view_mode = st.radio("View", ["Cards", "Table"], horizontal=True)

    if view_mode == "Table":
        # Table view
        df_data = []
        for band in bands:
            df_data.append({
                "Band": band['name'],
                "Times Seen": band['times_seen'],
                "First Show": format_date(band['first_show']) if band['first_show'] else "N/A",
                "Last Show": format_date(band['last_show']) if band['last_show'] else "N/A"
            })
        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        # Card view with expandable shows
        for band in bands:
            with st.expander(f"**{band['name']}** - Seen {band['times_seen']} time{'s' if band['times_seen'] != 1 else ''}"):
                # Edit button
                col1, col2 = st.columns([6, 1])
                with col1:
                    if band['first_show']:
                        st.write(f"First show: {format_date(band['first_show'])}")
                    if band['last_show']:
                        st.write(f"Last show: {format_date(band['last_show'])}")
                with col2:
                    if st.button("✏️", key=f"edit_band_{band['id']}", help="Edit band name"):
                        edit_band_dialog(band['id'], band['name'])

                st.divider()

                # Load and display shows
                shows = load_band_shows(band['id'])

                if shows:
                    st.write(f"**All {len(shows)} shows:**")
                    for show in shows:
                        col1, col2 = st.columns([4, 2])
                        with col1:
                            # Show actual band name if different from primary
                            band_display = show['actual_band_name']
                            if band_display != band['name']:
                                band_display = f"{band_display} (as)"
                            st.write(f"**{format_date(show['date'])}** - {show['all_bands']}")
                            if band_display != band['name']:
                                st.caption(f"Performed as: {show['actual_band_name']}")
                            st.caption(f"{show['venue_name']}")
                            if show['event']:
                                st.caption(f"_Event: {show['event']}_")
                        with col2:
                            st.caption(f"Show #{show['id']}")
