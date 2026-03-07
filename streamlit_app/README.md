# Shows Attended

Streamlit app for tracking live shows. Uses Turso (libSQL) as a hosted database.

## Features

- 📅 Browse shows with search and year filters
- ➕ Add shows with band autocomplete, venue address lookup, and import from upcoming shows
- ✏️ Edit/delete shows with band reordering
- 🎸 Band statistics with grouping/alias support
- 📍 Venue statistics with closed venue tracking
- 📊 Charts and stats (shows by year, top bands, top venues)
- 🎟️ Upcoming shows page with RSVP support (populated by event_watch)
- 🔐 Optional password protection

## Quick Start

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

Requires `.streamlit/secrets.toml` with Turso credentials:

```toml
[turso]
database_url = "https://your-db.turso.io"
auth_token = "your-token"
```

## Pages

- **Shows** (app.py) — Main page with show list, search, filters, add/edit dialogs
- **Bands** (pages/1_Bands.py) — Band statistics, grouping, show history
- **Venues** (pages/2_Venues.py) — Venue statistics, show history
- **Stats** (pages/3_Stats.py) — Charts and overall statistics
- **Upcoming** (pages/4_Upcoming.py) — Upcoming shows with RSVP

## Database

Uses [Turso](https://turso.tech/) via `libsql-experimental` with an embedded replica for fast local reads and remote sync on writes.

## Deployment

Can be deployed to Streamlit Community Cloud or any platform that supports Streamlit. Set Turso credentials as secrets in your deployment environment.
