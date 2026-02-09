# Shows Attended 🎸

A Streamlit web application for tracking concerts and shows attended, with band grouping, statistics, and cloud database sync.

## Features

- 📅 **Show Tracking**: Browse all 1,125+ shows with search and filters
- 🎤 **Band Grouping**: Group band name variations together (e.g., "Lenny Lashley", "Lenny Lashley & Friends")
- ✏️ **Edit Capabilities**: Edit band names, venue details, and closed status
- 📍 **Venue Management**: Track venues with location and closed status indicators
- 📊 **Statistics**: Charts by year, top bands (with grouping), top venues
- 🎯 **Sorting**: Sort bands and venues by count or alphabetically
- 🔐 **Password Protection**: Optional password authentication with session persistence
- ☁️ **Cloud Database**: Data stored in Turso (libSQL) for access from anywhere
- 🌙 **Dark Theme**: Easy on the eyes

## Live Demo

🚀 [Visit the live app](https://shows-attended.streamlit.app) _(coming soon)_

## Tech Stack

- **Framework**: Streamlit (Python)
- **Database**: Turso (libSQL) - serverless SQLite
- **Deployment**: Streamlit Cloud
- **Authentication**: SHA-256 password hashing with session persistence
- **Testing**: pytest with comprehensive test coverage

## Quick Start

### Local Development

```bash
# Clone the repository
git clone https://github.com/mattfinkel/shows-attended.git
cd shows-attended/streamlit_app

# Install dependencies
pip install -r requirements.txt

# Set up secrets (copy and edit)
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Run the app
streamlit run app.py
```

The app will open at http://localhost:8501

### Required Secrets

Create `.streamlit/secrets.toml`:

```toml
[turso]
database_url = "https://your-database.turso.io"
auth_token = "your-turso-auth-token"

# Optional: Password protection
app_password_hash = "your-sha256-hash"
```

See [PASSWORD_SETUP.md](streamlit_app/PASSWORD_SETUP.md) for password configuration.

## Database Schema

### Tables
- **shows**: Show records with date, venue, and optional event
- **bands**: Band names with optional `primary_band_id` for grouping
- **venues**: Venue names, locations, and closed status
- **events**: Festival/tour event names
- **show_bands**: Many-to-many junction table with band ordering

### Band Grouping
Bands can be grouped together using `primary_band_id`:
- Primary band: `primary_band_id IS NULL`
- Alias band: `primary_band_id` points to primary band
- Stats automatically roll up to primary band

Example: "Dropkick Murphys" (primary) + "[Dropkick Murphys]" (alias) = combined stats

## Project Structure

```
shows-attended/
├── streamlit_app/
│   ├── .streamlit/
│   │   ├── config.toml           # Dark theme
│   │   └── secrets.toml          # Credentials (gitignored)
│   ├── pages/
│   │   ├── 1_Bands.py            # Band stats with grouping
│   │   ├── 2_Venues.py           # Venue stats with editing
│   │   └── 3_Stats.py            # Charts and statistics
│   ├── app.py                    # Main page (shows list)
│   ├── db.py                     # Turso database wrapper
│   ├── auth.py                   # Password authentication
│   ├── test_app.py               # Test suite (30+ tests)
│   ├── requirements.txt
│   ├── PASSWORD_SETUP.md         # Password config guide
│   └── TESTING.md                # Testing guide
├── .gitignore
└── README.md
```

## Features in Detail

### Band Grouping

Group band name variations together:
- Click "⚙️ Manage Groups" on Bands page
- Select primary band and aliases
- Stats automatically combine (e.g., 17 + 11 + 2 = 30 total shows)
- Individual shows still show the actual band name used

### Password Protection

Optional authentication to restrict access:
1. Generate hash: `python generate_password_hash.py "your-password"`
2. Add to secrets: `app_password_hash = "hash"`
3. Users stay logged in per device
4. Logout button in sidebar

### Sorting

Both Bands and Venues pages support sorting:
- **By Count**: Most shows first (default)
- **By Name**: Alphabetical order

### Editing

- **Band names**: Click ✏️ on any band to rename
- **Venue details**: Edit name, location, and closed status
- **Closed venues**: Marked with 🔒 icon

## Deployment

### Streamlit Cloud

1. **Make repository public** (credentials are in secrets, not code)
2. Go to https://share.streamlit.io
3. Click "New app"
4. Configure:
   - Repository: `mattfinkel/shows-attended`
   - Branch: `main`
   - Main file: `streamlit_app/app.py`
5. Add secrets (Advanced settings → Secrets)
6. Deploy!

See deployment guide for full instructions.

### Database Setup (Turso)

```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Login
turso auth login

# Create database
turso db create shows-attended

# Get credentials
turso db show shows-attended
turso db tokens create shows-attended
```

## Testing

Run the comprehensive test suite:

```bash
# Install test dependencies
pip install pytest

# Set your Turso token
export TURSO_TEST_DB_TOKEN="your-token"

# Run all tests
pytest streamlit_app/test_app.py -v
```

See [TESTING.md](streamlit_app/TESTING.md) for details.

### Test Coverage

- ✅ Authentication (password hashing, sessions)
- ✅ Database connectivity
- ✅ Band grouping logic
- ✅ Venue operations
- ✅ Statistics queries
- ✅ Sorting (count and name)

## Current Data

- **1,125 shows** spanning 2006-2026
- **1,363 unique bands** (primary bands only)
- **342 venues**
- **18 events**

## Development History

1. **AppSheet** (2006-2025) - No-code platform, limited customization
2. **FastAPI + Vanilla JS** (Jan 2026) - Custom UI, local SQLite
3. **Streamlit + Turso** (Feb 2026) - Current version with cloud database

## Contributing

This is a personal project tracking my concert history. Feel free to fork and adapt for your own use!

## License

Personal project - not licensed for public use.
