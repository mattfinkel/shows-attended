#!/usr/bin/env python3
"""
Fix the 14 shows missing band relationships
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "shows.db"
DATA_DIR = Path(__file__).parent.parent

def get_or_create_band(cursor, band_name):
    """Get existing band ID or create new band"""
    band_name = band_name.strip()

    # Try to find existing band
    cursor.execute("SELECT id FROM bands WHERE name = ?", (band_name,))
    result = cursor.fetchone()

    if result:
        return result[0]

    # Create new band
    cursor.execute("INSERT INTO bands (name) VALUES (?)", (band_name,))
    return cursor.lastrowid

def fix_missing_bands():
    """Fix the 14 shows without band relationships"""

    # Load AppSheet data
    shows_file = DATA_DIR / "data_shows.json"
    with open(shows_file) as f:
        appsheet_shows = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get shows without bands
    cursor.execute("""
        SELECT s.id, s.date, v.name as venue
        FROM shows s
        JOIN venues v ON s.venue_id = v.id
        WHERE s.id NOT IN (SELECT DISTINCT show_id FROM show_bands)
        ORDER BY s.date
    """)

    shows_to_fix = cursor.fetchall()

    print("="*80)
    print(f"Fixing {len(shows_to_fix)} shows with missing bands")
    print("="*80)

    fixed_count = 0
    bands_added = 0

    for show in shows_to_fix:
        # Convert date to AppSheet format
        db_date = datetime.strptime(show['date'], '%Y-%m-%d')
        appsheet_date = db_date.strftime('%m/%d/%Y')

        # Find matching AppSheet show
        original = next((s for s in appsheet_shows if s.get('Date') == appsheet_date), None)

        if not original or not original.get('Bands'):
            print(f"⚠️  Could not find bands for {show['date']} @ {show['venue']}")
            continue

        bands_str = original['Bands']
        band_names = [b.strip() for b in bands_str.split(',')]

        print(f"\n{show['date']} @ {show['venue']}")
        print(f"  Adding {len(band_names)} bands...")

        # Add each band with order
        for order, band_name in enumerate(band_names, start=1):
            band_id = get_or_create_band(cursor, band_name)

            # Create show-band relationship
            try:
                cursor.execute(
                    "INSERT INTO show_bands (show_id, band_id, band_order) VALUES (?, ?, ?)",
                    (show['id'], band_id, order)
                )
                print(f"    {order}. {band_name}")
                bands_added += 1
            except sqlite3.IntegrityError:
                print(f"    {order}. {band_name} (already exists)")

        fixed_count += 1

    conn.commit()

    # Verify the fix
    cursor.execute("""
        SELECT COUNT(*) FROM shows
        WHERE id NOT IN (SELECT DISTINCT show_id FROM show_bands)
    """)
    remaining = cursor.fetchone()[0]

    print("\n" + "="*80)
    print("RESULTS")
    print("="*80)
    print(f"✓ Fixed {fixed_count} shows")
    print(f"✓ Added {bands_added} band relationships")
    print(f"✓ Shows still missing bands: {remaining}")

    if remaining == 0:
        print("\n🎉 All shows now have band relationships!")

    # Show updated stats
    cursor.execute("SELECT COUNT(*) FROM show_bands")
    total_relationships = cursor.fetchone()[0]
    print(f"\nTotal show-band relationships: {total_relationships}")

    conn.close()

if __name__ == "__main__":
    fix_missing_bands()
