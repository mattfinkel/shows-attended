#!/usr/bin/env python3
"""
Initialize the SQLite database and migrate data from AppSheet exports
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "shows.db"
SCHEMA_PATH = Path(__file__).parent / "schema.sql"
DATA_DIR = Path(__file__).parent.parent.parent

def init_database():
    """Create the database and tables"""
    print("Initializing database...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Read and execute schema
    with open(SCHEMA_PATH) as f:
        schema = f.read()
        cursor.executescript(schema)

    conn.commit()
    print(f"✓ Database created at {DB_PATH}")
    return conn

def parse_appsheet_date(date_str):
    """Parse AppSheet date format (MM/DD/YYYY) to SQLite format (YYYY-MM-DD)"""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except:
        return None

def migrate_venues(conn):
    """Migrate venues from AppSheet export"""
    print("\nMigrating venues...")

    venues_file = DATA_DIR / "data_venues.json"
    with open(venues_file) as f:
        venues_data = json.load(f)

    cursor = conn.cursor()
    venue_id_map = {}  # Map AppSheet Row ID to new SQLite ID

    for venue in venues_data:
        appsheet_id = venue.get("Row ID")
        name = venue.get("Name", "").strip()
        location = venue.get("Location", "").strip()
        closed = venue.get("Closed", "").upper() == "Y"

        if not name:
            continue

        cursor.execute(
            "INSERT INTO venues (name, location, closed) VALUES (?, ?, ?)",
            (name, location, closed)
        )
        venue_id_map[appsheet_id] = cursor.lastrowid

    conn.commit()
    print(f"✓ Migrated {len(venue_id_map)} venues")
    return venue_id_map

def migrate_bands(conn):
    """Migrate bands from AppSheet export"""
    print("\nMigrating bands...")

    bands_file = DATA_DIR / "data_bands.json"
    with open(bands_file) as f:
        bands_data = json.load(f)

    cursor = conn.cursor()
    band_id_map = {}  # Map AppSheet Row ID to new SQLite ID

    for band in bands_data:
        appsheet_id = band.get("Row ID")
        name = band.get("BandName", "").strip()

        if not name:
            continue

        try:
            cursor.execute("INSERT INTO bands (name) VALUES (?)", (name,))
            band_id_map[appsheet_id] = cursor.lastrowid
        except sqlite3.IntegrityError:
            # Band name already exists, get the existing ID
            cursor.execute("SELECT id FROM bands WHERE name = ?", (name,))
            existing_id = cursor.fetchone()[0]
            band_id_map[appsheet_id] = existing_id

    conn.commit()
    print(f"✓ Migrated {len(band_id_map)} bands")
    return band_id_map

def migrate_shows(conn, venue_id_map):
    """Migrate shows from AppSheet export"""
    print("\nMigrating shows...")

    shows_file = DATA_DIR / "data_shows.json"
    with open(shows_file) as f:
        shows_data = json.load(f)

    cursor = conn.cursor()
    show_id_map = {}  # Map AppSheet Row ID to new SQLite ID

    for show in shows_data:
        appsheet_id = show.get("Row ID")
        date = parse_appsheet_date(show.get("Date"))
        venue_appsheet_id = show.get("venues-shows")
        event = show.get("Event", "").strip() or None
        confirmed = show.get("Confirmed", "").upper() != "N"

        if not date or not venue_appsheet_id:
            continue

        venue_id = venue_id_map.get(venue_appsheet_id)
        if not venue_id:
            continue

        cursor.execute(
            "INSERT INTO shows (date, venue_id, event, confirmed) VALUES (?, ?, ?, ?)",
            (date, venue_id, event, confirmed)
        )
        show_id_map[appsheet_id] = cursor.lastrowid

    conn.commit()
    print(f"✓ Migrated {len(show_id_map)} shows")
    return show_id_map

def migrate_show_bands(conn, show_id_map, band_id_map):
    """Migrate show-band relationships from AppSheet export"""
    print("\nMigrating show-band relationships...")

    showbands_file = DATA_DIR / "data_showbands.json"
    with open(showbands_file) as f:
        showbands_data = json.load(f)

    cursor = conn.cursor()
    migrated = 0
    skipped = 0

    for sb in showbands_data:
        show_appsheet_id = sb.get("Show")
        band_appsheet_id = sb.get("Band")
        order = sb.get("Order")

        if not show_appsheet_id or not band_appsheet_id:
            skipped += 1
            continue

        show_id = show_id_map.get(show_appsheet_id)
        band_id = band_id_map.get(band_appsheet_id)

        if not show_id or not band_id:
            skipped += 1
            continue

        try:
            cursor.execute(
                "INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                (show_id, band_id, order or 0)
            )
            migrated += 1
        except sqlite3.IntegrityError:
            # Duplicate relationship, skip
            skipped += 1

    conn.commit()
    print(f"✓ Migrated {migrated} show-band relationships")
    if skipped > 0:
        print(f"  (Skipped {skipped} invalid/duplicate entries)")

def print_statistics(conn):
    """Print database statistics"""
    cursor = conn.cursor()

    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)

    cursor.execute("SELECT COUNT(*) FROM venues")
    print(f"Venues: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM bands")
    print(f"Bands: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM shows")
    print(f"Shows: {cursor.fetchone()[0]}")

    cursor.execute("SELECT COUNT(*) FROM show_bands")
    print(f"Show-Band relationships: {cursor.fetchone()[0]}")

    # Sample queries
    print("\n" + "="*60)
    print("SAMPLE QUERIES")
    print("="*60)

    # Most seen bands
    cursor.execute("""
        SELECT b.name, COUNT(*) as times_seen
        FROM bands b
        JOIN show_bands sb ON b.id = sb.band_id
        GROUP BY b.id
        ORDER BY times_seen DESC
        LIMIT 10
    """)
    print("\nTop 10 most seen bands:")
    for name, count in cursor.fetchall():
        print(f"  {count:3d}x - {name}")

    # Recent shows
    cursor.execute("""
        SELECT s.date, v.name,
               GROUP_CONCAT(b.name, ', ') as bands
        FROM shows s
        JOIN venues v ON s.venue_id = v.id
        LEFT JOIN show_bands sb ON s.id = sb.show_id
        LEFT JOIN bands b ON sb.band_id = b.id
        GROUP BY s.id
        ORDER BY s.date DESC
        LIMIT 5
    """)
    print("\nMost recent shows:")
    for date, venue, bands in cursor.fetchall():
        print(f"  {date} @ {venue}")
        print(f"    {bands or 'No bands'}")

def main():
    """Main migration process"""
    print("="*60)
    print("SHOWS ATTENDED - DATABASE MIGRATION")
    print("="*60)

    # Check if data files exist
    required_files = ["data_venues.json", "data_bands.json", "data_shows.json", "data_showbands.json"]
    for filename in required_files:
        filepath = DATA_DIR / filename
        if not filepath.exists():
            print(f"✗ Error: {filename} not found in {DATA_DIR}")
            print("\nPlease run the AppSheet export script first.")
            return

    # Initialize database
    conn = init_database()

    # Migrate data
    try:
        venue_id_map = migrate_venues(conn)
        band_id_map = migrate_bands(conn)
        show_id_map = migrate_shows(conn, venue_id_map)
        migrate_show_bands(conn, show_id_map, band_id_map)

        # Print statistics
        print_statistics(conn)

        print("\n" + "="*60)
        print("✓ MIGRATION COMPLETE!")
        print("="*60)
        print(f"\nDatabase location: {DB_PATH}")

    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main()
