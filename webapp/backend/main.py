#!/usr/bin/env python3
"""
Shows Attended - FastAPI Backend
Mobile-friendly API for tracking shows and bands
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
import sqlite3
from pathlib import Path

app = FastAPI(title="Shows Attended API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path(__file__).parent.parent / "database" / "shows.db"

# Models
class BandCreate(BaseModel):
    name: str

class VenueCreate(BaseModel):
    name: str
    location: Optional[str] = None

class ShowBandCreate(BaseModel):
    band_name: str
    order: int

class ShowCreate(BaseModel):
    date: date
    venue_name: str
    venue_location: Optional[str] = None
    event_name: Optional[str] = None
    bands: List[ShowBandCreate]

class BandStats(BaseModel):
    id: int
    name: str
    times_seen: int
    first_show: Optional[str] = None
    last_show: Optional[str] = None

class ShowDetail(BaseModel):
    id: int
    date: str
    venue_name: str
    venue_location: Optional[str]
    event: Optional[str]
    bands: List[str]

# Database helpers
def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# API Endpoints

@app.get("/")
async def root():
    """API health check"""
    return {"status": "ok", "message": "Shows Attended API"}

@app.get("/api/stats/summary")
async def get_summary_stats():
    """Get overall statistics"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM shows")
    total_shows = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bands")
    total_bands = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM venues")
    total_venues = cursor.fetchone()[0]

    cursor.execute("SELECT MIN(date), MAX(date) FROM shows")
    date_range = cursor.fetchone()

    conn.close()

    return {
        "total_shows": total_shows,
        "total_bands": total_bands,
        "total_venues": total_venues,
        "first_show": date_range[0],
        "last_show": date_range[1]
    }

@app.get("/api/stats/by-year")
async def get_stats_by_year():
    """Get statistics grouped by year"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            strftime('%Y', date) as year,
            COUNT(*) as show_count
        FROM shows
        GROUP BY year
        ORDER BY year DESC
    """)

    years = []
    for row in cursor.fetchall():
        years.append({
            "year": row["year"],
            "show_count": row["show_count"]
        })

    conn.close()
    return years

@app.get("/api/stats/year/{year}")
async def get_year_stats(year: int):
    """Get detailed statistics for a specific year"""
    conn = get_db()
    cursor = conn.cursor()

    # Total shows in year
    cursor.execute("""
        SELECT COUNT(*) FROM shows
        WHERE strftime('%Y', date) = ?
    """, (str(year),))
    total_shows = cursor.fetchone()[0]

    # Top bands in year
    cursor.execute("""
        SELECT
            b.id,
            b.name,
            COUNT(*) as times_seen
        FROM bands b
        JOIN show_bands sb ON b.id = sb.band_id
        JOIN shows s ON sb.show_id = s.id
        WHERE strftime('%Y', s.date) = ?
        GROUP BY b.id
        ORDER BY times_seen DESC, b.name
        LIMIT 10
    """, (str(year),))

    top_bands = []
    for row in cursor.fetchall():
        top_bands.append({
            "id": row["id"],
            "name": row["name"],
            "times_seen": row["times_seen"]
        })

    # Top venues in year
    cursor.execute("""
        SELECT
            v.id,
            v.name,
            v.location,
            COUNT(*) as show_count
        FROM venues v
        JOIN shows s ON v.id = s.venue_id
        WHERE strftime('%Y', s.date) = ?
        GROUP BY v.id
        ORDER BY show_count DESC, v.name
        LIMIT 10
    """, (str(year),))

    top_venues = []
    for row in cursor.fetchall():
        top_venues.append({
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "show_count": row["show_count"]
        })

    # Unique bands in year
    cursor.execute("""
        SELECT COUNT(DISTINCT sb.band_id)
        FROM show_bands sb
        JOIN shows s ON sb.show_id = s.id
        WHERE strftime('%Y', s.date) = ?
    """, (str(year),))
    unique_bands = cursor.fetchone()[0]

    # Unique venues in year
    cursor.execute("""
        SELECT COUNT(DISTINCT venue_id)
        FROM shows
        WHERE strftime('%Y', date) = ?
    """, (str(year),))
    unique_venues = cursor.fetchone()[0]

    conn.close()

    return {
        "year": year,
        "total_shows": total_shows,
        "unique_bands": unique_bands,
        "unique_venues": unique_venues,
        "top_bands": top_bands,
        "top_venues": top_venues
    }

@app.get("/api/bands/stats")
async def get_band_stats(
    limit: int = 100,
    search: Optional[str] = None,
    min_shows: int = 1
):
    """Get band statistics with optional search"""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            b.id,
            b.name,
            COUNT(sb.id) as times_seen,
            MIN(s.date) as first_show,
            MAX(s.date) as last_show
        FROM bands b
        LEFT JOIN show_bands sb ON b.id = sb.band_id
        LEFT JOIN shows s ON sb.show_id = s.id
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND b.name LIKE ?"
        params.append(f"%{search}%")

    query += """
        GROUP BY b.id
        HAVING times_seen >= ?
        ORDER BY times_seen DESC, b.name
        LIMIT ?
    """
    params.extend([min_shows, limit])

    cursor.execute(query, params)

    bands = []
    for row in cursor.fetchall():
        bands.append({
            "id": row["id"],
            "name": row["name"],
            "times_seen": row["times_seen"],
            "first_show": row["first_show"],
            "last_show": row["last_show"]
        })

    conn.close()
    return bands

@app.get("/api/bands/{band_id}/shows")
async def get_band_shows(band_id: int):
    """Get all shows for a specific band"""
    conn = get_db()
    cursor = conn.cursor()

    # Get band name
    cursor.execute("SELECT name FROM bands WHERE id = ?", (band_id,))
    band_row = cursor.fetchone()
    if not band_row:
        raise HTTPException(status_code=404, detail="Band not found")

    # Get all shows for this band
    cursor.execute("""
        WITH band_shows AS (
            SELECT
                s.id,
                s.date,
                v.name as venue_name,
                v.location as venue_location,
                e.name as event,
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
            WHERE s.id IN (
                SELECT show_id FROM show_bands WHERE band_id = ?
            )
        )
        SELECT
            *,
            (
                SELECT COUNT(*)
                FROM band_shows bs2
                WHERE bs2.date <= band_shows.date
            ) as show_number
        FROM band_shows
        ORDER BY date DESC
    """, (band_id,))

    shows = []
    for row in cursor.fetchall():
        shows.append({
            "id": row["id"],
            "date": row["date"],
            "venue_name": row["venue_name"],
            "venue_location": row["venue_location"],
            "event": row["event"],
            "bands": row["all_bands"].split(", ") if row["all_bands"] else [],
            "show_number": row["show_number"]
        })

    conn.close()

    return {
        "band_name": band_row["name"],
        "times_seen": len(shows),
        "shows": shows
    }

@app.get("/api/shows/{show_id}")
async def get_show(show_id: int):
    """Get a single show by ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            s.id,
            s.date,
            v.id as venue_id,
            v.name as venue_name,
            e.id as event_id,
            e.name as event
        FROM shows s
        JOIN venues v ON s.venue_id = v.id
        LEFT JOIN events e ON s.event_id = e.id
        WHERE s.id = ?
    """, (show_id,))

    show = cursor.fetchone()
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")

    # Get bands for this show
    cursor.execute("""
        SELECT b.id, b.name, sb.band_order
        FROM show_bands sb
        JOIN bands b ON sb.band_id = b.id
        WHERE sb.show_id = ?
        ORDER BY sb.band_order
    """, (show_id,))

    bands = []
    for row in cursor.fetchall():
        bands.append({
            "id": row["id"],
            "name": row["name"],
            "order": row["band_order"]
        })

    conn.close()

    return {
        "id": show["id"],
        "date": show["date"],
        "venue_id": show["venue_id"],
        "venue_name": show["venue_name"],
        "event_id": show["event_id"],
        "event": show["event"],
        "bands": bands
    }

@app.get("/api/shows")
async def get_shows(
    limit: int = 50,
    offset: int = 0,
    band: Optional[str] = None,
    venue: Optional[str] = None,
    event: Optional[str] = None,
    year: Optional[int] = None
):
    """Get shows with optional filters"""
    conn = get_db()
    cursor = conn.cursor()

    # Build WHERE clause for filtering
    where_conditions = ["1=1"]
    params = []

    if band:
        where_conditions.append("""s.id IN (
            SELECT sb2.show_id FROM show_bands sb2
            JOIN bands b2 ON sb2.band_id = b2.id
            WHERE b2.name LIKE ?
        )""")
        params.append(f"%{band}%")

    if venue:
        where_conditions.append("v.name LIKE ?")
        params.append(f"%{venue}%")

    if event:
        where_conditions.append("e.name LIKE ?")
        params.append(f"%{event}%")

    if year:
        where_conditions.append("strftime('%Y', s.date) = ?")
        params.append(str(year))

    where_clause = " AND ".join(where_conditions)

    # Main query with row number calculated within filtered set
    query = f"""
        WITH filtered_shows AS (
            SELECT
                s.id,
                s.date,
                v.name as venue_name,
                v.location as venue_location,
                e.name as event,
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
            WHERE {where_clause}
        )
        SELECT
            *,
            (
                SELECT COUNT(*)
                FROM filtered_shows fs2
                WHERE fs2.date <= filtered_shows.date
            ) as show_number
        FROM filtered_shows
        ORDER BY date DESC
        LIMIT ? OFFSET ?
    """
    params.extend([limit, offset])

    cursor.execute(query, params)

    shows = []
    for row in cursor.fetchall():
        shows.append({
            "id": row["id"],
            "date": row["date"],
            "venue_name": row["venue_name"],
            "venue_location": row["venue_location"],
            "event": row["event"],
            "bands": row["all_bands"].split(", ") if row["all_bands"] else [],
            "show_number": row["show_number"]
        })

    conn.close()
    return shows

@app.get("/api/autocomplete/bands")
async def autocomplete_bands(q: str, limit: int = 10):
    """Autocomplete for band names"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM bands
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
    """, (f"%{q}%", limit))

    results = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
    conn.close()
    return results

@app.get("/api/autocomplete/venues")
async def autocomplete_venues(q: str, limit: int = 10):
    """Autocomplete for venue names"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, location
        FROM venues
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
    """, (f"%{q}%", limit))

    results = [
        {"id": row["id"], "name": row["name"], "location": row["location"]}
        for row in cursor.fetchall()
    ]
    conn.close()
    return results

@app.get("/api/autocomplete/events")
async def autocomplete_events(q: str, limit: int = 10):
    """Autocomplete for event names"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM events
        WHERE name LIKE ?
        ORDER BY name
        LIMIT ?
    """, (f"%{q}%", limit))

    results = [{"id": row["id"], "name": row["name"]} for row in cursor.fetchall()]
    conn.close()
    return results

@app.post("/api/shows")
async def create_show(show: ShowCreate):
    """Create a new show"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Get or create venue
        cursor.execute("SELECT id FROM venues WHERE name = ?", (show.venue_name,))
        venue_row = cursor.fetchone()

        if venue_row:
            venue_id = venue_row["id"]
        else:
            cursor.execute(
                "INSERT INTO venues (name, location) VALUES (?, ?)",
                (show.venue_name, show.venue_location)
            )
            venue_id = cursor.lastrowid

        # Get or create event
        event_id = None
        if show.event_name:
            cursor.execute("SELECT id FROM events WHERE name = ?", (show.event_name,))
            event_row = cursor.fetchone()

            if event_row:
                event_id = event_row["id"]
            else:
                cursor.execute("INSERT INTO events (name) VALUES (?)", (show.event_name,))
                event_id = cursor.lastrowid

        # Create show
        cursor.execute(
            "INSERT INTO shows (date, venue_id, event_id) VALUES (?, ?, ?)",
            (show.date.isoformat(), venue_id, event_id)
        )
        show_id = cursor.lastrowid

        # Create bands and relationships
        for band_info in show.bands:
            # Get or create band
            cursor.execute("SELECT id FROM bands WHERE name = ?", (band_info.band_name,))
            band_row = cursor.fetchone()

            if band_row:
                band_id = band_row["id"]
            else:
                cursor.execute("INSERT INTO bands (name) VALUES (?)", (band_info.band_name,))
                band_id = cursor.lastrowid

            # Create show-band relationship
            cursor.execute(
                "INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                (show_id, band_id, band_info.order)
            )

        conn.commit()
        conn.close()

        return {"id": show_id, "message": "Show created successfully"}

    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/shows/{show_id}")
async def update_show(show_id: int, show: ShowCreate):
    """Update an existing show"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if show exists
        cursor.execute("SELECT id FROM shows WHERE id = ?", (show_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Show not found")

        # Get or create venue
        cursor.execute("SELECT id FROM venues WHERE name = ?", (show.venue_name,))
        venue_row = cursor.fetchone()

        if venue_row:
            venue_id = venue_row["id"]
        else:
            cursor.execute(
                "INSERT INTO venues (name, location) VALUES (?, ?)",
                (show.venue_name, show.venue_location)
            )
            venue_id = cursor.lastrowid

        # Get or create event
        event_id = None
        if show.event_name:
            cursor.execute("SELECT id FROM events WHERE name = ?", (show.event_name,))
            event_row = cursor.fetchone()

            if event_row:
                event_id = event_row["id"]
            else:
                cursor.execute("INSERT INTO events (name) VALUES (?)", (show.event_name,))
                event_id = cursor.lastrowid

        # Update show
        cursor.execute(
            "UPDATE shows SET date = ?, venue_id = ?, event_id = ? WHERE id = ?",
            (show.date.isoformat(), venue_id, event_id, show_id)
        )

        # Delete existing band relationships
        cursor.execute("DELETE FROM show_bands WHERE show_id = ?", (show_id,))

        # Create new band relationships
        for band_info in show.bands:
            # Get or create band
            cursor.execute("SELECT id FROM bands WHERE name = ?", (band_info.band_name,))
            band_row = cursor.fetchone()

            if band_row:
                band_id = band_row["id"]
            else:
                cursor.execute("INSERT INTO bands (name) VALUES (?)", (band_info.band_name,))
                band_id = cursor.lastrowid

            # Create show-band relationship
            cursor.execute(
                "INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                (show_id, band_id, band_info.order)
            )

        conn.commit()
        conn.close()

        return {"id": show_id, "message": "Show updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/api/shows/{show_id}")
async def delete_show(show_id: int):
    """Delete a show"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Enable foreign keys for this connection
        cursor.execute("PRAGMA foreign_keys = ON")

        # Check if show exists
        cursor.execute("SELECT id FROM shows WHERE id = ?", (show_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Show not found")

        # Delete show (cascade should delete show_bands if foreign keys enabled)
        cursor.execute("DELETE FROM shows WHERE id = ?", (show_id,))

        # Clean up any orphaned show_bands entries (in case cascade didn't work)
        cursor.execute("""
            DELETE FROM show_bands
            WHERE show_id NOT IN (SELECT id FROM shows)
        """)

        # Clean up orphaned bands (bands with no shows)
        cursor.execute("""
            DELETE FROM bands
            WHERE id NOT IN (SELECT DISTINCT band_id FROM show_bands)
        """)

        # Clean up orphaned venues (venues with no shows)
        cursor.execute("""
            DELETE FROM venues
            WHERE id NOT IN (SELECT DISTINCT venue_id FROM shows)
        """)

        # Clean up orphaned events (events with no shows)
        cursor.execute("""
            DELETE FROM events
            WHERE id NOT IN (SELECT DISTINCT event_id FROM shows WHERE event_id IS NOT NULL)
        """)

        conn.commit()
        conn.close()

        return {"message": "Show deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/events/stats")
async def get_event_stats(
    limit: int = 100,
    search: Optional[str] = None,
    min_shows: int = 1
):
    """Get event statistics with optional search"""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            e.id,
            e.name,
            COUNT(s.id) as show_count
        FROM events e
        LEFT JOIN shows s ON e.id = s.event_id
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND e.name LIKE ?"
        params.append(f"%{search}%")

    query += """
        GROUP BY e.id
        HAVING show_count >= ?
        ORDER BY show_count DESC, e.name
        LIMIT ?
    """
    params.extend([min_shows, limit])

    cursor.execute(query, params)

    events = []
    for row in cursor.fetchall():
        events.append({
            "id": row["id"],
            "name": row["name"],
            "show_count": row["show_count"]
        })

    conn.close()
    return events

@app.get("/api/events/{event_id}/shows")
async def get_event_shows(event_id: int):
    """Get all shows for a specific event"""
    conn = get_db()
    cursor = conn.cursor()

    # Get event info
    cursor.execute("SELECT name FROM events WHERE id = ?", (event_id,))
    event_row = cursor.fetchone()
    if not event_row:
        raise HTTPException(status_code=404, detail="Event not found")

    # Get all shows for this event
    cursor.execute("""
        WITH event_shows AS (
            SELECT
                s.id,
                s.date,
                v.name as venue_name,
                v.location as venue_location,
                (
                    SELECT GROUP_CONCAT(b2.name, ', ')
                    FROM show_bands sb2
                    JOIN bands b2 ON sb2.band_id = b2.id
                    WHERE sb2.show_id = s.id
                    ORDER BY sb2.band_order
                ) as all_bands
            FROM shows s
            JOIN venues v ON s.venue_id = v.id
            WHERE s.event_id = ?
        )
        SELECT
            *,
            (
                SELECT COUNT(*)
                FROM event_shows es2
                WHERE es2.date <= event_shows.date
            ) as show_number
        FROM event_shows
        ORDER BY date DESC
    """, (event_id,))

    shows = []
    for row in cursor.fetchall():
        shows.append({
            "id": row["id"],
            "date": row["date"],
            "venue_name": row["venue_name"],
            "venue_location": row["venue_location"],
            "bands": row["all_bands"].split(", ") if row["all_bands"] else [],
            "show_number": row["show_number"]
        })

    conn.close()

    return {
        "event_name": event_row["name"],
        "show_count": len(shows),
        "shows": shows
    }

@app.put("/api/bands/{band_id}")
async def update_band(band_id: int, name: str):
    """Update a band name"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if band exists
        cursor.execute("SELECT id FROM bands WHERE id = ?", (band_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Band not found")

        # Update band name
        cursor.execute("UPDATE bands SET name = ? WHERE id = ?", (name.strip(), band_id))

        conn.commit()
        conn.close()

        return {"message": "Band updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/venues/{venue_id}")
async def update_venue(venue_id: int, name: str, location: Optional[str] = None):
    """Update a venue"""
    conn = get_db()
    cursor = conn.cursor()

    try:
        # Check if venue exists
        cursor.execute("SELECT id FROM venues WHERE id = ?", (venue_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Venue not found")

        # Update venue
        cursor.execute(
            "UPDATE venues SET name = ?, location = ? WHERE id = ?",
            (name.strip(), location, venue_id)
        )

        conn.commit()
        conn.close()

        return {"message": "Venue updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        conn.close()
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/venues/stats")
async def get_venue_stats(
    limit: int = 100,
    search: Optional[str] = None,
    min_shows: int = 1
):
    """Get venue statistics with optional search"""
    conn = get_db()
    cursor = conn.cursor()

    query = """
        SELECT
            v.id,
            v.name,
            v.location,
            COUNT(s.id) as show_count
        FROM venues v
        LEFT JOIN shows s ON v.id = s.venue_id
        WHERE 1=1
    """

    params = []

    if search:
        query += " AND v.name LIKE ?"
        params.append(f"%{search}%")

    query += """
        GROUP BY v.id
        HAVING show_count >= ?
        ORDER BY show_count DESC, v.name
        LIMIT ?
    """
    params.extend([min_shows, limit])

    cursor.execute(query, params)

    venues = []
    for row in cursor.fetchall():
        venues.append({
            "id": row["id"],
            "name": row["name"],
            "location": row["location"],
            "show_count": row["show_count"]
        })

    conn.close()
    return venues

@app.get("/api/venues/{venue_id}/shows")
async def get_venue_shows(venue_id: int):
    """Get all shows at a specific venue"""
    conn = get_db()
    cursor = conn.cursor()

    # Get venue info
    cursor.execute("SELECT name, location FROM venues WHERE id = ?", (venue_id,))
    venue_row = cursor.fetchone()
    if not venue_row:
        raise HTTPException(status_code=404, detail="Venue not found")

    # Get all shows at this venue
    cursor.execute("""
        WITH venue_shows AS (
            SELECT
                s.id,
                s.date,
                e.name as event,
                (
                    SELECT GROUP_CONCAT(b2.name, ', ')
                    FROM show_bands sb2
                    JOIN bands b2 ON sb2.band_id = b2.id
                    WHERE sb2.show_id = s.id
                    ORDER BY sb2.band_order
                ) as all_bands
            FROM shows s
            LEFT JOIN events e ON s.event_id = e.id
            WHERE s.venue_id = ?
        )
        SELECT
            *,
            (
                SELECT COUNT(*)
                FROM venue_shows vs2
                WHERE vs2.date <= venue_shows.date
            ) as show_number
        FROM venue_shows
        ORDER BY date DESC
    """, (venue_id,))

    shows = []
    for row in cursor.fetchall():
        shows.append({
            "id": row["id"],
            "date": row["date"],
            "event": row["event"],
            "bands": row["all_bands"].split(", ") if row["all_bands"] else [],
            "show_number": row["show_number"]
        })

    conn.close()

    return {
        "venue_name": venue_row["name"],
        "venue_location": venue_row["location"],
        "show_count": len(shows),
        "shows": shows
    }

# Serve frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/app")
    async def serve_app():
        return FileResponse(frontend_path / "index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
