# Shows Attended

A web application for tracking concerts and shows attended, with full CRUD operations, statistics, and mobile-friendly interface.

## Features

- 📅 **Show Tracking**: Record shows with date, bands, venue, and event
- 🎸 **Band Statistics**: See which bands you've seen most, view all shows for each band
- 📍 **Venue Tracking**: Track venues visited with show counts and details
- 🎉 **Event Navigation**: Filter by events like festivals and tours
- 📊 **Statistics**: View stats by year, top bands, top venues
- 📱 **Mobile-First Design**: Responsive dark-themed interface optimized for mobile
- ✏️ **Full CRUD**: Add, edit, and delete shows with autocomplete

## Project Structure

```
shows-attended/
├── webapp/                    # Main web application
│   ├── backend/              # FastAPI backend
│   │   └── main.py           # API endpoints
│   ├── database/             # SQLite database and migrations
│   │   ├── schema.sql        # Database schema
│   │   ├── init_db.py        # Initial data import from AppSheet
│   │   ├── migrate_events.py # Events table migration
│   │   └── shows.db          # SQLite database
│   ├── frontend/             # HTML/CSS/JS frontend
│   │   ├── index.html
│   │   ├── app.js
│   │   └── style.css
│   └── server.log            # Server logs
├── python/                    # Legacy analysis scripts
│   ├── appsheet_import.py    # Original AppSheet import
│   ├── bands_seen.py         # Band analysis
│   ├── duplicates.py         # Find duplicates
│   ├── venues.py             # Venue analysis
│   └── most_by_letter.py     # Letter frequency analysis
└── README.md
```

## Tech Stack

- **Backend**: Python FastAPI
- **Database**: SQLite with normalized relational schema
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Deployment**: Self-hosted or any Python-capable host

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

## Setup

### Prerequisites
- Python 3.7+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone <your-repo-url>
   cd shows-attended
   ```

2. Install Python dependencies:
   ```bash
   pip install fastapi uvicorn
   ```

3. Initialize the database (if starting fresh):
   ```bash
   cd webapp/database
   sqlite3 shows.db < schema.sql
   ```

4. Start the server:
   ```bash
   cd webapp
   python3 backend/main.py
   ```

5. Open your browser to:
   ```
   http://localhost:8000/app
   ```

## Usage

### Adding Shows
1. Click the **Add** tab in the bottom navigation
2. Enter date, bands (in order), venue, and optional event
3. Use autocomplete for existing bands/venues/events
4. Submit to save

### Viewing Statistics
- **Shows Tab**: Browse all shows with search and year filters
- **Bands Tab**: See bands sorted by times seen, with search
- **Venues Tab**: View venues with show counts
- **Stats Tab**: Overall statistics and year-by-year breakdowns

### Navigation
- Click any band name to see all shows for that band
- Click any venue to see all shows at that venue
- Click any event to see all shows for that event
- Click the **Edit** button on any show to modify or delete it

## API Endpoints

### Shows
- `GET /api/shows` - List shows with filters
- `GET /api/shows/{id}` - Get single show
- `POST /api/shows` - Create show
- `PUT /api/shows/{id}` - Update show
- `DELETE /api/shows/{id}` - Delete show

### Bands
- `GET /api/bands/stats` - Band statistics
- `GET /api/bands/{id}/shows` - Shows for band

### Venues
- `GET /api/venues/stats` - Venue statistics
- `GET /api/venues/{id}/shows` - Shows at venue

### Events
- `GET /api/events/stats` - Event statistics
- `GET /api/events/{id}/shows` - Shows for event

### Stats
- `GET /api/stats/summary` - Overall summary
- `GET /api/stats/by-year` - Shows by year
- `GET /api/stats/year/{year}` - Year details

### Autocomplete
- `GET /api/autocomplete/bands?q={query}`
- `GET /api/autocomplete/venues?q={query}`
- `GET /api/autocomplete/events?q={query}`

## Development

### Running in Development Mode
```bash
cd webapp
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations
Migration scripts are in `webapp/database/`:
- `init_db.py` - Initial import from AppSheet
- `migrate_events.py` - Migrate events to separate table
- `drop_old_event_column.py` - Clean up old event column

## Migration from AppSheet

This project was migrated from AppSheet. The original AppSheet data was imported using `webapp/database/init_db.py`, which:
- Fetched all shows, bands, and venues from AppSheet API
- Normalized the data into relational tables
- Preserved band ordering and all relationships

Legacy scripts in `python/` directory were used for the migration and analysis.

## License

Personal project - not licensed for public use.
