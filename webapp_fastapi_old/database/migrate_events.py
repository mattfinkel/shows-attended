#!/usr/bin/env python3
"""
Migrate events from text field to separate table
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shows.db"

def migrate_events():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("="*80)
    print("MIGRATING EVENTS TO SEPARATE TABLE")
    print("="*80)

    try:
        # Create events table
        print("\n1. Creating events table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("   ✓ Events table created")

        # Get all unique events from shows
        print("\n2. Extracting unique events from shows...")
        cursor.execute("""
            SELECT DISTINCT event
            FROM shows
            WHERE event IS NOT NULL AND event != ''
        """)
        events = cursor.fetchall()
        print(f"   ✓ Found {len(events)} unique events")

        # Insert events into new table
        print("\n3. Inserting events into events table...")
        event_map = {}
        for event in events:
            event_name = event['event'].strip()
            cursor.execute("INSERT INTO events (name) VALUES (?)", (event_name,))
            event_map[event_name] = cursor.lastrowid
        print(f"   ✓ Inserted {len(event_map)} events")

        # Add event_id column to shows (temporarily nullable)
        print("\n4. Adding event_id column to shows table...")
        cursor.execute("""
            ALTER TABLE shows ADD COLUMN event_id INTEGER
        """)
        print("   ✓ Added event_id column")

        # Populate event_id based on event text
        print("\n5. Populating event_id values...")
        for event_name, event_id in event_map.items():
            cursor.execute(
                "UPDATE shows SET event_id = ? WHERE event = ?",
                (event_id, event_name)
            )
        print(f"   ✓ Updated event_id for all shows")

        # Check results
        cursor.execute("SELECT COUNT(*) FROM shows WHERE event_id IS NOT NULL")
        count = cursor.fetchone()[0]
        print(f"   ✓ {count} shows now have event_id")

        conn.commit()

        print("\n" + "="*80)
        print("✓ MIGRATION COMPLETE!")
        print("="*80)
        print("\nNext steps:")
        print("1. The old 'event' column is still there for safety")
        print("2. Update the backend to use event_id instead of event")
        print("3. Once verified, you can drop the old 'event' column")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_events()
