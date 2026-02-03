# Shows Attended Web App

A mobile-friendly web application for tracking concerts and shows with powerful band statistics and search capabilities.

## Features

- 📱 **Mobile-First Design** - Optimized for mobile browsers with touch-friendly interface
- 🎸 **Band Statistics** - See how many times you've seen each band, with full show history
- 🔍 **Advanced Search** - Filter shows by band, venue, year, or event
- ➕ **Quick Entry** - Add new shows with autocomplete for bands and venues
- 📊 **Analytics** - View top bands, venues, and overall statistics

## Quick Start

### Local Development

1. **Start the server:**
   ```bash
   ./start.sh
   ```

2. **Open in browser:**
   ```
   http://localhost:8000/app
   ```

That's it! The start script handles:
- Creating virtual environment
- Installing dependencies
- Starting the FastAPI server

### Manual Setup

If you prefer manual setup:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (first time only)
python3 database/init_db.py

# Start server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

## Deployment

### Deploy to Railway (Free)

1. **Install Railway CLI:**
   ```bash
   npm install -g @railway/cli
   # or
   brew install railway
   ```

2. **Login and deploy:**
   ```bash
   cd webapp
   railway login
   railway init
   railway up
   ```

3. **Your app is live!** Railway will provide a URL.

### Deploy to Fly.io (Free)

1. **Install Fly CLI:**
   ```bash
   brew install flyctl
   ```

2. **Create app:**
   ```bash
   cd webapp
   flyctl launch
   ```

3. **Deploy:**
   ```bash
   flyctl deploy
   ```

### Environment Variables

No environment variables needed! The app uses SQLite which is embedded in the deployment.

## Project Structure

```
webapp/
├── backend/
│   └── main.py           # FastAPI backend with all API endpoints
├── frontend/
│   ├── index.html        # Main HTML structure
│   ├── style.css         # Mobile-first CSS
│   └── app.js            # Frontend JavaScript
├── database/
│   ├── schema.sql        # Database schema
│   ├── init_db.py        # Migration script from AppSheet
│   └── shows.db          # SQLite database (created after migration)
├── requirements.txt      # Python dependencies
├── Procfile             # For Railway/Heroku deployment
├── railway.json         # Railway configuration
└── start.sh            # Local development startup script
```

## API Endpoints

The backend provides a REST API:

- `GET /api/stats/summary` - Overall statistics
- `GET /api/shows` - List shows with filters (band, venue, year, event)
- `GET /api/bands/stats` - Band statistics with search
- `GET /api/bands/{id}/shows` - All shows for a specific band
- `GET /api/venues/stats` - Venue statistics
- `GET /api/autocomplete/bands` - Band name autocomplete
- `GET /api/autocomplete/venues` - Venue name autocomplete
- `POST /api/shows` - Create a new show

Full API documentation at: `http://localhost:8000/docs`

## Database

The app uses SQLite for simplicity and portability:

- **Bands** - Individual band records
- **Venues** - Venue information with location
- **Shows** - Show details (date, venue, event)
- **ShowBands** - Junction table linking shows to bands with order preservation

### Data Migration

Your AppSheet data has been migrated:
- ✅ 1,125 shows
- ✅ 1,357 bands
- ✅ 342 venues
- ✅ 3,272 show-band relationships

## Mobile Features

- **Bottom Navigation** - Easy thumb access to main sections
- **Touch-Optimized** - Large tap targets, swipe-friendly
- **Autocomplete** - Quick band/venue entry on mobile keyboards
- **Responsive** - Works on all screen sizes

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: Vanilla JavaScript (no framework bloat)
- **Styling**: Custom CSS (mobile-first)

## Development

### Adding New Features

The codebase is intentionally simple - all backend logic is in `backend/main.py`, all frontend in three files. Just edit and the changes take effect immediately with `--reload`.

### Database Queries

To query the database directly:

```bash
sqlite3 database/shows.db
```

Example queries:
```sql
-- Most seen bands
SELECT b.name, COUNT(*) as times
FROM bands b
JOIN show_bands sb ON b.id = sb.band_id
GROUP BY b.id
ORDER BY times DESC
LIMIT 10;

-- Shows by year
SELECT strftime('%Y', date) as year, COUNT(*) as shows
FROM shows
GROUP BY year
ORDER BY year DESC;
```

## Troubleshooting

**Port already in use:**
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill
```

**Database not found:**
```bash
# Re-run migration
python3 database/init_db.py
```

**Modules not found:**
```bash
# Ensure you're in venv
source venv/bin/activate
pip install -r requirements.txt
```

## Future Ideas

- Export shows to CSV/JSON
- Band statistics charts
- Venue map view
- Show photos upload
- Share show lists with friends
- Import from setlist.fm

## License

Personal use only.
