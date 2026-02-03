#!/usr/bin/env python3
"""
Drop the old event text column from shows table
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "shows.db"

def drop_old_event_column():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("="*80)
    print("REMOVING OLD EVENT COLUMN FROM SHOWS TABLE")
    print("="*80)

    try:
        # SQLite doesn't support DROP COLUMN directly on older versions
        # We need to recreate the table without the event column

        print("\n1. Creating new shows table without event column...")
        cursor.execute("""
            CREATE TABLE shows_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                venue_id INTEGER NOT NULL,
                event_id INTEGER,
                confirmed BOOLEAN DEFAULT 1,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (venue_id) REFERENCES venues(id),
                FOREIGN KEY (event_id) REFERENCES events(id)
            )
        """)
        print("   ✓ New shows table created")

        # Copy data from old table to new table
        print("\n2. Copying data to new table...")
        cursor.execute("""
            INSERT INTO shows_new (id, date, venue_id, event_id, confirmed, notes, created_at)
            SELECT id, date, venue_id, event_id, confirmed, notes, created_at
            FROM shows
        """)
        rows_copied = cursor.rowcount
        print(f"   ✓ Copied {rows_copied} shows")

        # Drop old table
        print("\n3. Dropping old shows table...")
        cursor.execute("DROP TABLE shows")
        print("   ✓ Old table dropped")

        # Rename new table
        print("\n4. Renaming new table to 'shows'...")
        cursor.execute("ALTER TABLE shows_new RENAME TO shows")
        print("   ✓ Table renamed")

        # Recreate indexes
        print("\n5. Recreating indexes...")
        cursor.execute("CREATE INDEX idx_shows_date ON shows(date)")
        cursor.execute("CREATE INDEX idx_shows_venue ON shows(venue_id)")
        print("   ✓ Indexes recreated")

        # Verify
        print("\n6. Verifying schema...")
        cursor.execute("PRAGMA table_info(shows)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"   Columns in shows table: {', '.join(columns)}")

        if 'event' in columns:
            raise Exception("Old 'event' column still exists!")
        if 'event_id' not in columns:
            raise Exception("New 'event_id' column is missing!")

        print("   ✓ Schema verified")

        conn.commit()

        print("\n" + "="*80)
        print("✓ MIGRATION COMPLETE!")
        print("="*80)
        print("\nThe old 'event' text column has been removed.")
        print("All shows now use event_id to reference the events table.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    drop_old_event_column()
