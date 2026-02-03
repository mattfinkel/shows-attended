# 🎸 Shows Attended - Quick Start

Your concert tracking app is ready to use!

## Try It Locally (2 Steps)

```bash
cd shows-attended/webapp
./start.sh
```

Then open in your browser: **http://localhost:8000/app**

That's it! The app is now running on your machine.

## What You Can Do

### 📱 Browse Shows
- View all 1,125 shows you've attended
- Filter by year, venue, or band
- Search for specific shows

### 🎸 Band Statistics
- See all 1,357 bands you've seen
- Click any band to see every show you saw them at
- Your top band: **Bouncing Souls** (59 times!)

### ➕ Add New Shows
- Quick mobile-friendly form
- Autocomplete for bands and venues
- Automatic band ordering

### 📊 View Stats
- Total shows, bands, venues
- Date range (2006-2026!)
- Top 10 bands and venues

## Deploy It (Free!)

To access from your phone anywhere:

```bash
# Install Railway CLI
brew install railway

# Login & deploy
cd shows-attended/webapp
railway login
railway init
railway up
```

You'll get a URL like `https://your-app.railway.app` - save it to your phone's home screen!

## What's Different from AppSheet?

### ✅ Better
- **Statistics**: See exactly how many times you've seen each band
- **Search**: Fast, powerful filtering
- **Speed**: Instant load times
- **Control**: Change anything by editing code (no clicking through UI)

### = Same
- **Mobile-friendly**: Works great on phone
- **All your data**: 1,125 shows migrated perfectly
- **Easy entry**: Quick forms with autocomplete

### ⚠️ Missing (but can add)
- No offline mode (yet)
- No photo uploads (yet)
- No sharing features (yet)

All of these are easy to add since you control the code!

## Files Overview

```
webapp/
├── start.sh              ← Run this to start
├── backend/main.py       ← All API code (one file!)
├── frontend/
│   ├── index.html        ← UI structure
│   ├── style.css         ← Mobile styling
│   └── app.js            ← Frontend logic
├── database/
│   └── shows.db          ← Your data (SQLite)
└── README.md             ← Full documentation
```

## Common Tasks

### Add a Feature

Just edit the relevant file:
- Backend logic → `backend/main.py`
- UI changes → `frontend/index.html` or `style.css`
- Frontend behavior → `frontend/app.js`

The server auto-reloads when you save!

### Backup Your Data

```bash
cp database/shows.db database/shows-backup-$(date +%Y%m%d).db
```

### Export to CSV

Use the SQLite CLI:
```bash
sqlite3 database/shows.db
.headers on
.mode csv
.output shows.csv
SELECT * FROM shows;
.quit
```

## Next Steps

1. **Try it locally**: `./start.sh`
2. **Test on your phone**: Connect to your laptop's IP (e.g., `http://192.168.1.100:8000/app`)
3. **Deploy to Railway**: Follow DEPLOY.md for free hosting
4. **Customize**: Edit the code to add features you want

## Questions?

Check out:
- **README.md** - Full documentation
- **DEPLOY.md** - Deployment guide
- **backend/main.py** - Comments explain all API endpoints

Enjoy your new app! 🎸
