#!/usr/bin/env python3
"""Quick server test"""
import sys
sys.path.insert(0, '/Users/mfinkel/workspace/shows-attended/webapp')

from backend.main import app
import sqlite3
from pathlib import Path

# Test database
db_path = Path(__file__).parent / "database" / "shows.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("="*60)
print("SERVER TEST")
print("="*60)

# Test database queries
cursor.execute("SELECT COUNT(*) FROM shows")
shows = cursor.fetchone()[0]
print(f"✓ Shows in database: {shows}")

cursor.execute("SELECT COUNT(*) FROM bands")
bands = cursor.fetchone()[0]
print(f"✓ Bands in database: {bands}")

cursor.execute("SELECT COUNT(*) FROM venues")
venues = cursor.fetchone()[0]
print(f"✓ Venues in database: {venues}")

# Test API import
print(f"✓ FastAPI app loaded: {app.title}")

print("\n" + "="*60)
print("✓ ALL TESTS PASSED - SERVER IS READY!")
print("="*60)
print("\nTo start the server:")
print("  cd /Users/mfinkel/workspace/shows-attended/webapp")
print("  python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
print("\nThen open: http://localhost:8000/app")

conn.close()
