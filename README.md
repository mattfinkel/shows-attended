# Shows Attended

A Streamlit web application for tracking concerts and shows attended, with full CRUD operations, statistics, and charts.

## Features

- 📅 **Show Tracking**: Record shows with date, bands, venue, and event
- 🎸 **Band Statistics**: See which bands you've seen most, view all shows for each band
- 📍 **Venue Tracking**: Track venues visited with show counts and details
- 🎉 **Event Navigation**: Track events like festivals and tours
- 📊 **Statistics**: Charts and stats by year, top bands, top venues
- ✏️ **Full CRUD**: Add, edit, and delete shows with autocomplete
- 🌙 **Dark Theme**: Easy on the eyes

## Tech Stack

- **Framework**: Streamlit (Pure Python)
- **Database**: SQLite with normalized relational schema
- **Deployment**: Streamlit Cloud, Railway, or any Python host

## Quick Start

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

The app will open at http://localhost:8501

## Database Schema

### Tables
- **shows**: Show records with date, venue, and optional event
- **bands**: Unique band names
- **venues**: Venue names and locations
- **events**: Festival/tour event names
- **show_bands**: Many-to-many junction table with band ordering

### Relationships
- `shows.venue_id` → `venues.id`
- `shows.event_id` → `events.id`
- `show_bands.show_id` → `shows.id` (CASCADE delete)
- `show_bands.band_id` → `bands.id`

## Project Structure

```
shows-attended/
├── streamlit_app/              # Main Streamlit application
│   ├── .streamlit/
│   │   └── config.toml         # Dark theme configuration
│   ├── pages/
│   │   ├── 1_Add_Show.py       # Add new shows
│   │   ├── 2_Edit_Show.py      # Edit/delete shows
│   │   ├── 3_Bands.py          # Band statistics
│   │   ├── 4_Venues.py         # Venue statistics
│   │   └── 5_Stats.py          # Overall statistics
│   ├── app.py                  # Main page (shows list)
│   ├── requirements.txt
│   └── README.md
├── webapp_fastapi_old/         # Legacy FastAPI version (archived)
│   └── database/
│       └── shows.db            # SQLite database (shared)
└── python/                     # Legacy analysis scripts
```

## Pages

- **Shows** (main) - Browse all shows with search and filters
- **Add Show** - Form to add new shows with autocomplete
- **Edit Show** - View and delete shows
- **Bands** - Band statistics with expandable show history
- **Venues** - Venue statistics with expandable show history
- **Stats** - Charts and overall statistics

## Deployment

### Streamlit Cloud (Recommended)

1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect your repository
4. Set main file: `streamlit_app/app.py`
5. Deploy!

**Note**: You'll need to handle the database file. Options:
- Upload `shows.db` to the repo (if < 100MB)
- Use Streamlit secrets for database connection
- Connect to a hosted SQLite/Postgres instance

### Railway / Render

```bash
# Install dependencies
pip install -r streamlit_app/requirements.txt

# Run the app
streamlit run streamlit_app/app.py --server.port=$PORT --server.address=0.0.0.0
```

## Database Location

The database is located at: `webapp_fastapi_old/database/shows.db`

To initialize a fresh database:
```bash
cd webapp_fastapi_old/database
sqlite3 shows.db < schema.sql
```

## Migration from AppSheet

This project was migrated from AppSheet. The original AppSheet data was imported using `webapp_fastapi_old/database/init_db.py`, which:
- Fetched all shows, bands, and venues from AppSheet API
- Normalized the data into relational tables
- Preserved band ordering and all relationships

Current data:
- **1,125 shows** spanning 2006-2025
- **1,369 unique bands**
- **342 venues**
- **18 events**

## Development History

This app went through several iterations:
1. **AppSheet** (2006-2025) - No-code platform, great UX but slow setup
2. **FastAPI + Vanilla JS** (Jan 2026) - Custom mobile-first UI with dark theme
3. **Streamlit** (Feb 2026) - Current version, simpler codebase and deployment

The FastAPI version is archived in `webapp_fastapi_old/` for reference.

## Legacy Scripts

The `python/` directory contains legacy analysis scripts from the AppSheet era:
- `bands_seen.py` - Band frequency analysis
- `duplicates.py` - Find duplicate entries
- `venues.py` - Venue analysis
- `most_by_letter.py` - Letter frequency analysis

## License

Personal project - not licensed for public use.
