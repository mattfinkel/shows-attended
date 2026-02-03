# Deployment Guide

## Quick Deploy to Railway (Recommended - Free)

Railway is the easiest way to deploy this app for free.

### Step 1: Create a Railway Account

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub (recommended)

### Step 2: Deploy from GitHub

**Option A: Deploy from GitHub (Recommended)**

1. Push your webapp folder to GitHub:
   ```bash
   cd webapp
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/shows-attended.git
   git push -u origin main
   ```

2. In Railway:
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Select your repository
   - Railway will auto-detect and deploy!

**Option B: Deploy from CLI**

1. Install Railway CLI:
   ```bash
   npm install -g @railway/cli
   # or on Mac:
   brew install railway
   ```

2. Login and deploy:
   ```bash
   cd webapp
   railway login
   railway init
   railway up
   ```

### Step 3: Done!

Railway will give you a URL like: `https://your-app.railway.app`

Your app is now live and accessible from any device!

## Alternative: Fly.io (Also Free)

### Step 1: Install Fly CLI

```bash
# Mac/Linux:
curl -L https://fly.io/install.sh | sh

# Or with Homebrew:
brew install flyctl
```

### Step 2: Sign Up & Deploy

```bash
cd webapp
flyctl auth signup    # Or: flyctl auth login
flyctl launch        # Follow prompts
flyctl deploy        # Deploy!
```

### Step 3: Done!

Your app will be at: `https://your-app.fly.dev`

## Cost Comparison

| Platform | Free Tier | Limits |
|----------|-----------|--------|
| **Railway** | $5/month credit | ~500 hours/month |
| **Fly.io** | Free tier | 3 VMs, 256MB each |
| **Render** | Free tier | Spins down after 15min |

**Recommendation**: Railway is the easiest and most generous for this use case.

## Post-Deployment

### Updating Your App

**Railway:**
- Just push to GitHub, Railway auto-deploys
- Or run `railway up` from CLI

**Fly.io:**
```bash
flyctl deploy
```

### Accessing Your Data

The SQLite database is embedded in your deployment. To back it up:

**Railway:**
```bash
railway run python3 -c "import sqlite3; import json; con=sqlite3.connect('database/shows.db'); ..."
```

Or use Railway's file browser in the dashboard.

**Fly.io:**
```bash
flyctl ssh console
# Then copy database file
```

### Custom Domain (Optional)

Both Railway and Fly.io support custom domains for free:

**Railway:**
1. Go to project settings
2. Click "Domains"
3. Add your domain and follow DNS instructions

**Fly.io:**
```bash
flyctl certs add yourdomain.com
```

## Troubleshooting

### Deployment Fails

**Error: Missing dependencies**
- Make sure `requirements.txt` is in the webapp directory
- Check that all files are committed

**Error: Database not found**
- The database is created during migration
- Make sure `database/shows.db` exists locally first

### App Won't Start

Check logs:

**Railway:**
- View in dashboard under "Deployments" → "Logs"

**Fly.io:**
```bash
flyctl logs
```

### Database Reset

If you need to reset your data:

1. Delete the deployment
2. Recreate with fresh database
3. Or SSH in and delete `database/shows.db`

## Security Notes

- The SQLite database is stored in the deployment
- Anyone with the URL can access the app
- To add authentication, consider adding a simple password check

## Performance

With your current data (~1,100 shows):
- **Load time**: < 1 second
- **API response**: < 100ms
- **Database size**: < 5MB

The free tiers can easily handle this.

## Monitoring

**Railway:**
- Built-in metrics in dashboard
- Shows CPU, memory, bandwidth

**Fly.io:**
```bash
flyctl status
flyctl metrics
```

## Backup Strategy

Since the database is embedded:

1. **Periodic Export**: Use the API to export data as JSON
2. **Git Backup**: Commit database periodically (not recommended for production)
3. **External Backup**: Set up scheduled backup to cloud storage

Example backup script:
```bash
#!/bin/bash
curl https://your-app.railway.app/api/shows > backup-$(date +%Y%m%d).json
```

## Questions?

- Railway: https://railway.app/help
- Fly.io: https://fly.io/docs
