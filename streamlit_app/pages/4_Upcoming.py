"""
Upcoming Shows Page
Displays upcoming shows discovered by event_watch with RSVP support
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from db import get_db
from auth import check_password, show_logout_button
from utils import inject_sidebar_css
from datetime import datetime
from urllib.parse import quote

st.set_page_config(page_title="Upcoming", page_icon="🎟️", layout="wide")

if not check_password():
    st.stop()

show_logout_button()

inject_sidebar_css()

RSVP_COLORS = {
    "yes": "#4CAF50",
    "maybe": "#FFA726",
    "no": "#EF5350",
    None: "#666666",
}

RSVP_LABELS = {
    "yes": "Going",
    "maybe": "Maybe",
    "no": "Not going",
    None: "",
}

st.markdown("""
    <style>
    .upcoming-card {
        background: #262730;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        position: relative;
    }
    .upcoming-date {
        color: #B0B0B0;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
    }
    .upcoming-event {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        color: #FAFAFA;
    }
    .upcoming-venue {
        color: #B0B0B0;
        font-size: 0.9rem;
    }
    .upcoming-match {
        color: #4CAF50;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    .upcoming-price {
        color: #FFD700;
        font-size: 0.85rem;
        margin-top: 0.25rem;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🎟️ Upcoming Shows")


def table_exists():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='upcoming_shows'"
    )
    return cursor.fetchone() is not None


def ensure_rsvp_column():
    """Add rsvp column if it doesn't exist yet."""
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE upcoming_shows ADD COLUMN rsvp TEXT")
        conn.commit()
    except Exception:
        pass


def load_upcoming_shows(show_hidden=False):
    conn = get_db()
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    if show_hidden:
        cursor.execute(
            """SELECT id, event_name, date, venue, matched_artist, price, url, discovered_at, rsvp
               FROM upcoming_shows
               WHERE date >= ?
               ORDER BY date ASC""",
            [today],
        )
    else:
        cursor.execute(
            """SELECT id, event_name, date, venue, matched_artist, price, url, discovered_at, rsvp
               FROM upcoming_shows
               WHERE date >= ? AND (rsvp IS NULL OR rsvp != 'hidden')
               ORDER BY date ASC""",
            [today],
        )
    return cursor.fetchall()


def update_rsvp(show_id, rsvp_value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE upcoming_shows SET rsvp = ? WHERE id = ?", [rsvp_value, show_id])
    conn.commit()


if not table_exists():
    st.info("No upcoming shows data yet. Run event_watch with --save-to-db to populate.")
    st.stop()

ensure_rsvp_column()

# Sidebar filters
with st.sidebar:
    st.header("Filters")
    rsvp_filter = st.selectbox("RSVP Status", ["All", "Going", "Maybe", "Not going", "No response"])
    hide_no_rsvp = st.checkbox("Hide 'Not going'", value=True)
    only_new = st.checkbox("Only new listings")
    show_hidden = st.checkbox("Show hidden")

shows = load_upcoming_shows(show_hidden=show_hidden)

# Apply RSVP filter
if rsvp_filter != "All":
    filter_map = {"Going": "yes", "Maybe": "maybe", "Not going": "no", "No response": None}
    filter_val = filter_map[rsvp_filter]
    shows = [s for s in shows if s["rsvp"] == filter_val]

# Hide "Not going" by default
if hide_no_rsvp:
    shows = [s for s in shows if s["rsvp"] != "no"]

# Only show listings with no RSVP yet
if only_new:
    shows = [s for s in shows if s["rsvp"] is None]

if not shows:
    st.info("No upcoming shows found matching your filters.")
    st.stop()

st.subheader(f"{len(shows)} upcoming shows")

current_month = None

for show in shows:
    try:
        dt = datetime.strptime(show["date"], "%Y-%m-%d")
        month_label = dt.strftime("%B %Y")
        date_display = dt.strftime("%a, %b %d")
    except ValueError:
        month_label = "Unknown"
        date_display = show["date"]

    if month_label != current_month:
        current_month = month_label
        st.markdown(f"### {month_label}")

    rsvp = show["rsvp"]
    border_color = RSVP_COLORS.get(rsvp, RSVP_COLORS[None])

    price_html = f"<div class='upcoming-price'>{show['price']}</div>" if show["price"] else ""
    url = show["url"] or ""
    event_name = show["event_name"]
    if url:
        event_html = f"<a href='{url}' target='_blank' style='color: #FAFAFA; text-decoration: none;'>{event_name}</a>"
    else:
        event_html = event_name

    rsvp_html = ""
    if rsvp and rsvp != "hidden":
        label = RSVP_LABELS.get(rsvp, "")
        rsvp_html = f"<div style='margin-top:0.25rem'><span style='font-size:0.8rem;font-weight:600;padding:2px 8px;border-radius:4px;background:{border_color};color:#fff'>{label}</span></div>"

    # Google Calendar link (all-day event)
    gcal_title = quote(event_name)
    gcal_date = show["date"].replace("-", "")
    gcal_location = quote(show["venue"])
    gcal_details = quote(url) if url else ""
    gcal_url = f"https://calendar.google.com/calendar/render?action=TEMPLATE&text={gcal_title}&dates={gcal_date}/{gcal_date}&location={gcal_location}&details={gcal_details}"
    gcal_html = f"<div style='margin-top:0.25rem'><a href='{gcal_url}' target='_blank' style='color:#8AB4F8;font-size:0.8rem;text-decoration:none'>+ Google Calendar</a></div>"

    with st.container():
        col_card, col_btns = st.columns([5, 2])

        with col_card:
            card_html = f"<div class='upcoming-card' style='border-left: 3px solid {border_color}'><div class='upcoming-date'>{date_display}</div><div class='upcoming-event'>{event_html}</div><div class='upcoming-venue'>{show['venue']}</div><div class='upcoming-match'>Matched: {show['matched_artist']}</div>{price_html}{rsvp_html}{gcal_html}</div>"
            st.markdown(card_html, unsafe_allow_html=True)

        with col_btns:
            sid = show["id"]
            bc1, bc2, bc3, bc4 = st.columns(4)
            with bc1:
                if st.button("Yes" if rsvp != "yes" else "**Yes**", key=f"rsvp_yes_{sid}", help="Going", disabled=rsvp == "yes"):
                    update_rsvp(sid, "yes")
                    st.rerun()
            with bc2:
                if st.button("Maybe" if rsvp != "maybe" else "**Maybe**", key=f"rsvp_maybe_{sid}", help="Maybe", disabled=rsvp == "maybe"):
                    update_rsvp(sid, "maybe")
                    st.rerun()
            with bc3:
                if st.button("No" if rsvp != "no" else "**No**", key=f"rsvp_no_{sid}", help="Not going", disabled=rsvp == "no"):
                    update_rsvp(sid, "no")
                    st.rerun()
            with bc4:
                if st.button("Hide", key=f"rsvp_hide_{sid}", help="Hide this show"):
                    update_rsvp(sid, "hidden")
                    st.rerun()
