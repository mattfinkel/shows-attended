#!/usr/bin/env python3
"""Test year statistics API"""
import sys
sys.path.insert(0, '/Users/mfinkel/workspace/shows-attended/webapp')

import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "database" / "shows.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("="*80)
print("YEAR STATISTICS TEST")
print("="*80)

# Test by-year query
cursor.execute("""
    SELECT
        strftime('%Y', date) as year,
        COUNT(*) as show_count
    FROM shows
    GROUP BY year
    ORDER BY year DESC
    LIMIT 10
""")

print("\nMost Recent Years:")
for row in cursor.fetchall():
    print(f"  {row['year']}: {row['show_count']} shows")

# Test detailed year stats (2025)
year = 2025
cursor.execute("""
    SELECT COUNT(*) FROM shows
    WHERE strftime('%Y', date) = ?
""", (str(year),))
total_shows = cursor.fetchone()[0]

cursor.execute("""
    SELECT
        b.name,
        COUNT(*) as times_seen
    FROM bands b
    JOIN show_bands sb ON b.id = sb.band_id
    JOIN shows s ON sb.show_id = s.id
    WHERE strftime('%Y', s.date) = ?
    GROUP BY b.id
    ORDER BY times_seen DESC
    LIMIT 5
""", (str(year),))

print(f"\n{year} Stats:")
print(f"  Total Shows: {total_shows}")
print(f"  Top Bands:")
for row in cursor.fetchall():
    print(f"    {row['times_seen']}x - {row['name']}")

conn.close()

print("\n" + "="*80)
print("✓ YEAR STATS TEST PASSED")
print("="*80)
