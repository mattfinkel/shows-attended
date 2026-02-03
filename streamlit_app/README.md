# Shows Attended - Streamlit Version

Streamlit prototype of the Shows Attended app. Uses the same SQLite database as the FastAPI version.

## Features

- 📅 Browse shows with search and filters
- ➕ Add new shows with autocomplete
- 🎸 View band statistics and shows
- 📍 View venue statistics and shows
- 📊 Overall statistics and charts
- ✏️ Edit/delete shows

## Quick Start

```bash
cd streamlit_app
pip install -r requirements.txt
streamlit run app.py
```

The app will open at http://localhost:8501

## Database

This app uses the same database as the FastAPI version at:
`../webapp/database/shows.db`

No database changes needed - they share the same data!

## Deploy to Streamlit Cloud

1. Push to GitHub
2. Go to https://share.streamlit.io
3. Connect your repo
4. Set app path to `streamlit_app/app.py`
5. Deploy!

Note: You'll need to upload the database or connect to a hosted database for production.

## Comparison with FastAPI Version

### Pros
- Much simpler codebase (5 files vs 15+)
- Pure Python (no HTML/CSS/JS)
- Built-in charts and stats
- Easy deployment to Streamlit Cloud

### Cons
- Less mobile-optimized UI
- Sidebar navigation instead of bottom nav
- Expandable sections instead of modals
- Less custom styling control

## Pages

- **Shows** (app.py) - Main page with show list and filters
- **Add Show** - Form to add new shows
- **Edit Show** - Edit/delete existing shows
- **Bands** - Band statistics and show history
- **Venues** - Venue statistics and show history
- **Stats** - Charts and overall statistics
